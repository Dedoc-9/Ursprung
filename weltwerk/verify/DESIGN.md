<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# verify/ — verification interface design (forward-looking)

**Status: VISION / PLANNED, with Phase A.2 Step 1 landed.** This is a design contract for the *next*
verify stages (symbolic checking → abstract interpretation → counterfactuals → repair), not a description
of shipped code. Where a principle is already realized in `kernel_check.py` / `diagnose.py` /
`interfaces.py`, the map below says so honestly. `designed ≠ implemented`; `interface-sketch ≠ guarantee`.

**Phase A.2 progress:** Steps 1–2 done. Step 1 — stable `ReachabilityResult` / `VerificationResult`
contract (`interfaces.py`, 8/8). Step 2 — transition relation `T(s,a,s')` (`transition.py`,
`test_transition.py` 8/8), differential-tested to match the reference engine; `kernel_check.py` still
untouched. Remaining: Step 3 engine abstraction (`ExplicitStateEngine` consumes `T`; `check()` rewired
behind it), Step 4 stable artifacts (fills `certificate`, predecessor relation), Step 5 prototype symbolic
backend (gated on the z3-vs-pure-Python decision), Step 6 differential testing (explicit vs symbolic agree
on every world).

## The one idea

Make the **symbolic checker produce artifacts every later phase can reuse**, rather than treating it as
"just a faster BFS." The verification *engine* (explicit-state BFS, BDD, SAT, SMT, or a future hybrid)
should sit behind a **stable interface** so diagnosis, abstract interpretation, counterfactuals, and
repair depend on the *artifacts*, not the algorithm. `engine ≠ interface`.

```
ReachabilityResult
├── reachable(state)        -> bool
├── witness(target)         -> Trace | symbolic model
├── predecessor_set(state)  -> set | symbolic set
├── successor_set(state)    -> set | symbolic set
├── frontier()              -> set | symbolic set
└── proof_certificate()     -> certificate | None
```

## Ten design choices (and where we stand today)

| # | Principle | Why it pays off later | Current state |
|---|---|---|---|
| 1 | **Explicit transition relation** `T(s, a, s')` instead of baking transitions into the search | one relation reused by symbolic reachability, abstract interpretation, counterfactual search, repair planning | **DONE (Step 2)** — `transition.py`: `TransitionRelation.successors/step/actions` over frozen `State`/`Transition`; differential-tested to match the reference engine exactly. `check()` rewired to consume it in Step 3 |
| 2 | **Stable state IDs**: every discovered witness carries `StateID, ParentID, GeneratingAction, Depth` | replay, diagnosis, repair, visualization all get easier | PARTIAL — `_sig(state)` is a canonical id; `parent[sig] = (parent_sig, action)` gives ParentID+action; depth tracked in BFS but not stored on the state |
| 3 | **Predecessor information** (`predecessors(state)`, or computable) not just a single `parent` | enables minimal repair, causal slicing, "what could have led here?", reverse reachability | NOT YET — only a single BFS `parent` is stored |
| 4 | **Invariants as first-class objects**: `Invariant(name, predicate, explanation, severity)` | every phase reuses them — diagnosis reports `violated: <name>`, repair asks "restore `<name>`", counterfactuals ask "when did `<name>` first break?" | PARTIAL — invariants are a `name -> predicate` dict; no `explanation` / `severity` yet |
| 5 | **Preserve symbolic witnesses** (don't immediately flatten a BDD/SAT model); keep both the symbolic witness *and* a concrete replay trace | concrete replay is for humans; symbolic witness is for repair optimization | PLANNED — explicit-state only produces concrete traces today |
| 6 | **Unsat-core support early** (for SMT): report "impossible because constraints A, D, F conflict", not just "impossible" | diagnosis ranks the conflicting constraints; repair targets only them; counterfactuals ask which to change | PLANNED — no SMT engine yet |
| 7 | **Actions as symbolic objects**: `Action(name, preconditions, effects, category)` | supports abstraction, planning, repair synthesis, explanation without redesign | **PARTIAL (Step 2)** — `transition.Action` is a frozen value type (kind/target/amount/faction/dtype); preconditions/effects/category are the documented next extension; `kernel_check` still uses tuples until Step 3 |
| 8 | **Immutable traces** — no phase may mutate a trace | diagnosis, counterfactuals, repair, visualization all reference the same permanent artifact safely | NOT YET — traces are plain `list`s; should become a frozen `Trace` |
| 9 | **Separate search from policy**: `SearchEngine` + `StoppingPolicy` + `Property`, not "BFS knows when to stop" | bounded / complete / symbolic / heuristic search all reuse one engine | NOT YET — `check()` hardcodes BFS + depth bound + `stop_on_first` |
| 10 | **Proof objects, not `PASS`** — return a `VerificationResult` every phase consumes | diagnosis/counterfactuals/repair consume the witness; abstract interpretation compares its approximation to the exact result; visualization renders it | **DONE (Step 1)** — `interfaces.py` defines frozen `ReachabilityResult` + `VerificationResult` (status, witness, explored_states, frontier_exhausted, engine, violations) with a `verify()` entry point over the reference engine; `certificate` is a deliberate placeholder for Step 4 |

## Target proof object

```
VerificationResult(
    status,             # CLOSED | BOUNDED | VIOLATED   (the epistemic outcome, never just PASS/FAIL)
    explored_states,
    frontier,           # 0 ⇒ exhaustive over the induced reachable graph
    witness,            # Trace (concrete) and/or symbolic model, on VIOLATED; None on CLOSED
    certificate,        # proof artifact on CLOSED (e.g. the closed reachable set / BDD); None otherwise
    invariants,         # the Invariant objects checked
)
```

`CheckResult` in `kernel_check.py` is the embryo of this. The migration is additive: add `certificate`
and a `witness` accessor, promote invariants and actions to objects, freeze traces — without changing the
CLOSED/BOUNDED/VIOLATED semantics already proven by the test suite.

## Consumption map (who reads what)

- **Diagnosis** ← `witness` (the ghost trace), `Invariant` (the violated name), predecessor sets.
- **Abstract interpretation** ← the exact `VerificationResult` to *compare its over-approximation against*
  (`over-approx ⊇ exact`); the `Invariant` objects to abstract.
- **Counterfactuals** ← immutable `Trace` + predecessor sets ("if action X had not occurred…").
- **Repair** ← `Invariant` to restore + unsat core (the constraints to target) + `Action` effects to plan.
- **Visualization** ← state IDs, transitions, the `VerificationResult`.

## Migration discipline (non-negotiable)

Per the workbench philosophy: make these changes **small and reversible**, behind the existing tests.
Do not refactor `kernel_check.py` speculatively in one pass — each promotion (Invariant objects, frozen
Trace, search/policy split, `certificate` field) is its own change with its own tests, and must keep the
current 8/8 green. A symbolic engine is added *behind* `ReachabilityResult`, never by rewriting the
explicit-state checker's semantics. `refactor ≠ rewrite`; `new-engine ≠ new-semantics`.
