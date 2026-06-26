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
| `kernel_check.py` | BFS explicit-state checker over `WorldSim`; invariants + transition law; shortest ghost trace; `replay_path` witness check | IMPLEMENTED (pending local test run) |
| `test_kernel_check.py` | 8 validity-not-outcome proofs | WRITTEN (run to confirm) |

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
cd "C:\Users\dillb_lzxy763\Claude\Projects\Ursprung\weltwerk\verify"; python kernel_check.py; python test_kernel_check.py
```

`kernel_check.py` prints a CLOSED proof over the demo world, then demonstrates a **ghost**: it checks a
deliberately-false invariant ("nothing is ever destroyed"), finds the one-event counterexample, and shows
the trace replays faithfully on a fresh world (`trace ≠ truth until it replays`). `test_kernel_check.py`
should report **8/8**.

> Note: tests were authored but not executed in-session — the sandbox mount served a truncated view of an
> unrelated authoring file, so verification is deferred to the PowerShell run above.

## Why this was the first merge chosen

Of the NASA-derived candidates, this one (a) has the **most novel use** — model-checking authored causal
worlds is not a thing that exists; (b) is **legally cleanest** — reimplemented from the literature, so it
stays own-copyright and preserves the dual-license option (no NOSA exposure, no Java↔Python vendoring);
and (c) **raises the central claim**: it lets Weltwerk *prove* invariants it previously only spot-tested.
The differentiating IP is the mapping to `Potential ⊇ Actual`, not the textbook search.

## Next candidates (same folder)

- An **IKOS-style abstract-interpretation** pass: a sound over-approximation that scales past the explicit
  bound (complements this exact-but-bounded checker). Reimplement from Cousot & Cousot — NOSA, no source.
- **Livingstone-style diagnosis**: turn a ghost trace into "which mediator/SPOF is responsible," reusing
  the existing divergence classifier.
