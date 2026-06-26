<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# verify/ — verification interface design (forward-looking)

**Status: VISION / PLANNED, with Phase A.2 Steps 1–6 landed (symbolic backend = approach A, optional z3).** This is a design contract for the *next*
verify stages (symbolic checking → abstract interpretation → counterfactuals → repair), not a description
of shipped code. Where a principle is already realized in `kernel_check.py` / `diagnose.py` /
`interfaces.py`, the map below says so honestly. `designed ≠ implemented`; `interface-sketch ≠ guarantee`.

**Phase A.2 progress:** Steps 1–6 done. Step 1 — stable contract (`interfaces.py`). Step 2 — transition
relation `T(s,a,s')` (`transition.py`). Step 3 — engine abstraction (`engine.py`); BFS left `kernel_check.py`
(shim). Step 4 — durable artifacts (`artifacts.py`). Step 5 — **second engine** (`symbolic_engine.py`,
approach A: SMT/BMC over the *extracted* relation; z3 confined to `solver_adapter.py`, **optional** —
`pip install z3-solver`; core stays pure-stdlib). Step 6 — differential harness (`differential.py`,
`test_differential.py`): explicit vs symbolic agree on every model. *The solver is an engine dependency,
not an architecture dependency.* Next artifacts: predecessor relation (#3) and a symbolic `ConstraintCertificate`
with unsat cores (#5/#6) — "bounded contradiction explanation", never "proof of impossibility". Scaling
(approach B: SMT re-encoding of `apply_event`) is a later, separately-gated step, now safe because the
differential harness will catch encoding drift.

**Milestone reached.** The project crossed a line: from *"Weltwerk has a model checker"* to *"Weltwerk has
a verification kernel with interchangeable proof engines producing auditable artifacts."* Symbolic BMC is
one engine; abstract interpretation will be another; diagnosis/counterfactuals/repair consume the artifacts.
A new engine must pass `differential.py` (equivalence with the explicit reference) before becoming a
supported backend — that harness, not any single algorithm, is now the load-bearing verification tool.

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
| 4 | **Invariants as first-class objects**: `Invariant(name, predicate, explanation, severity)` | every phase reuses them — diagnosis reports `violated: <name>`, repair asks "restore `<name>`", counterfactuals ask "when did `<name>` first break?" | **DONE (Step 4)** — `artifacts.Invariant` (name/predicate/explanation/severity); `DEFAULT_INVARIANTS` promoted; engine uses `.predicate` ONLY (`label ≠ control`); `Violation` carries the metadata |
| 5 | **Preserve symbolic witnesses** (don't immediately flatten a BDD/SAT model); keep both the symbolic witness *and* a concrete replay trace | concrete replay is for humans; symbolic witness is for repair optimization | **PARTIAL (Step 5)** — concrete witness extraction done: SMT model → action sequence → relation replay → `Trace`. Preserving the raw *symbolic* model (and unsat cores) is the next symbolic artifact |
| 6 | **Unsat-core support early** (for SMT): report "impossible because constraints A, D, F conflict", not just "impossible" | diagnosis ranks the conflicting constraints; repair targets only them; counterfactuals ask which to change | PLANNED — no SMT engine yet |
| 7 | **Actions as symbolic objects**: `Action(name, preconditions, effects, category)` | supports abstraction, planning, repair synthesis, explanation without redesign | **PARTIAL (Step 2)** — `transition.Action` is a frozen value type (kind/target/amount/faction/dtype); preconditions/effects/category are the documented next extension; `kernel_check` still uses tuples until Step 3 |
| 8 | **Immutable traces** — no phase may mutate a trace | diagnosis, counterfactuals, repair, visualization all reference the same permanent artifact safely | **DONE (Step 4)** — `artifacts.Trace` (frozen; `events`/`states`/`length`/`terminal_state`; enforces `len(events)==length-1`); on the result as `trace` for VIOLATED. (Raw `path` list remains as a back-compat view.) |
| 9 | **Separate search from policy**: `SearchEngine` + `StoppingPolicy` + `Property`, not "BFS knows when to stop" | bounded / complete / symbolic / heuristic search all reuse one engine | **DONE (Step 3)** — `engine.py`: `VerificationEngine` protocol + `ExplicitStateBFSEngine` (the only impl); search lives here, options in `VerificationOptions`, the world in `WorldModel`; `kernel_check.check()` is now a shim with no algorithm |
| 10 | **Proof objects, not `PASS`** — return a `VerificationResult` every phase consumes | diagnosis/counterfactuals/repair consume the witness; abstract interpretation compares its approximation to the exact result; visualization renders it | **DONE (Steps 1+4)** — frozen `ReachabilityResult`/`VerificationResult` (status, witness, explored_states, frontier_exhausted, engine, violations, **trace**, **certificate**); `certificate` is now a re-derivable `ReachabilityCertificate` on CLOSED (was placeholder) |

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
