<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# weltwerk/verify — bounded model checking of the causal kernel

The first NASA-merge subsystem. It reimplements, clean-room, the **explicit-state model-checking**
discipline that NASA's Java Pathfinder embodies — *systematically explore every reachable state and
return a shortest counterexample* — and applies it to something JPF never targeted: an **authored
causal world**. No JPF source is used (JPF checks Java bytecode; this checks `WorldSim`). License +
provenance: this is original AGPL-3.0 code, recorded in
[`../../docs/LICENSE_DECISIONS.md`](../../docs/LICENSE_DECISIONS.md) and
[`../../docs/PROVENANCE.md`](../../docs/PROVENANCE.md).

## The idea, in Weltwerk's own terms

| Model checking | Weltwerk |
|---|---|
| set of reachable states under the action alphabet | **Actual** (what the world can actually become) |
| all action sequences up to the depth bound | **Potential** (the combinatorial upper bound) |
| a state that violates an invariant | a **ghost** — returned as the *shortest, replayable* event trace |
| exhaustive (frontier emptied) search | a **proof** of the invariants over the reachable set |

`Actual ⊆ Potential` is not just the law the checker *tests* on every transition (`actual ⊆ potential`);
it is also the shape of the search itself — the explored state set is almost always far smaller than the
combinatorial bound, which is the project's sparsity thesis showing up in verification.

## Files

| File | Role | Grade |
|---|---|---|
| `kernel_check.py` | BFS explicit-state checker over `WorldSim`; invariants + transition law; shortest ghost trace; `replay_path` witness check | MEASURED (8/8) |
| `test_kernel_check.py` | 8 validity-not-outcome proofs | MEASURED (8/8) |
| `diagnose.py` | model-based diagnosis (the inverse): observed state → minimal fault hypotheses, ranked, with a discriminating observation; consumes `kernel_check` ghosts | IMPLEMENTED (pending local test run) |
| `test_diagnose.py` | 8 validity-not-outcome proofs | WRITTEN (run to confirm) |

## Diagnosis (the inverse of the checker)

`kernel_check` answers *"this invariant failed / these states diverge"* (forward). `diagnose` answers the
human's next question — *"why?"* (inverse). Given an **observed** world state, it returns the minimal
**fault hypotheses** (entity losses) whose simulated cascade reproduces the observation, ranked, each with
a single **suggested observation** that would best distinguish the surviving rivals. It consumes the
checker's ghost traces directly (`from_ghost`). Pipeline: counterexample → symptoms → candidate causes
(consistency by simulation) → ranking → ghost report.

**`confidence` is a ranking weight, not a probability.** It is a transparent, normalized score
(parsimony of faults × parsimony of effects) used to *allocate investigation*. It does **not** estimate
the probability that a hypothesis is true. `consistency ≠ causation`; `minimal ≠ correct`;
`weight ≠ P(true)`. Competing explanations are preserved (`underdetermined`), never collapsed.

Fault model = **entity loss** only (not damage amounts, captures, or timing). Minimal-cardinality search
(singles, then pairs). Consistency is judged over observed entities only — which is why *partial*
observation produces genuine, honestly-reported ambiguity. `unobserved ≠ ok`; `not-explained ≠ no-cause`.

## Honest grading of a result (the epistemic states)

- **CLOSED** — the frontier emptied before the depth bound: the explored set is the *complete* reachable
  set for this alphabet, so the invariants are **PROVEN** over it. `state-space-closed = proof`.
- **BOUNDED** — the depth bound cut off real frontier: invariants hold on what was explored; the rest is
  **UNDERDETERMINED**. `depth-limited ≠ proof`.
- **VIOLATED** — an invariant fails; the shortest ghost trace is attached and is verified replayable.

## What it does NOT claim (Arbitrary-Boundary Law)

- It proves invariants only over its **action alphabet** (default `{destroy, repair}`; `damage(amount)`
  is excluded because unbounded amounts make the space infinite). `alphabet ≠ all-edits`.
- State identity excludes the event log, so `path ≠ state` (this is what makes closure finite).
- Passing the chosen invariants is `consistent-with-our-invariants`, not `correct`. `holds-here ≠ true`.
- It says nothing about gameplay, performance, or continuous dynamics. `event ≠ measured-dynamics`.

## Run (PowerShell, folder-directed)

```powershell
cd "weltwerk\verify"; python kernel_check.py; python test_kernel_check.py
```

```powershell
cd "weltwerk\verify"; python diagnose.py; python test_diagnose.py
```

`kernel_check.py` prints a CLOSED proof over the demo world, then demonstrates a **ghost** (verified
8/8). `diagnose.py` pins a single cause from a full observation, then shows an *underdetermined* case
under partial observation and the observation that would discriminate. `test_diagnose.py` should report
**8/8**.

> Note: the `diagnose` tests were authored but not executed in-session — the sandbox mount served a
> truncated view of an unrelated authoring file, so verification is deferred to the PowerShell run above.
> `kernel_check` is confirmed 8/8 from the prior run.

## Why this was the first merge chosen

Of the NASA-derived candidates, this one (a) has the **most novel use** — model-checking authored causal
worlds is not a thing that exists; (b) is **legally cleanest** — reimplemented from the literature, so it
stays own-copyright and preserves the dual-license option (no NOSA exposure, no Java↔Python vendoring);
and (c) **raises the central claim**: it lets Weltwerk *prove* invariants it previously only spot-tested.
The differentiating IP is the mapping to `Potential ⊇ Actual`, not the textbook search.

## Roadmap (each stage consumes the previous one's artifacts)

1. ✅ Transition system (`../sim/world_sim.py`)
2. ✅ Explicit-state model checker (`kernel_check.py`) — produces ghosts + traces
3. ✅ Diagnosis engine (`diagnose.py`) — turns ghosts into ranked fault hypotheses + a probe to run next
4. **IKOS-style abstract interpretation** (next) — a sound over-approximation that scales past the
   bounded checker; feeds `world_lint`. Reimplement from Cousot & Cousot — NOSA, no source.
5. **Counterfactual explanations** — "if event X had not occurred…" over the trace.
6. **Automated repair suggestions** — from a diagnosis, the minimal edit that restores invariants.
