<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Live / Latent Provenance — provenance-preserving compression under runtime constraints

Not a new layer trying to explain reality — a **stress test of the existing invariant** at a new
pressure. The earlier phases asked whether a claim keeps its floor, a coordinate its status, an
edge its support, a latent its claim, an inference its price, an edit its source, ignorance its
diagnosis. This asks the same question under a frame budget:

> Can a runtime keep provenance when it is forced to **compress**?

The invariant, stated for the runtime:

```
Provenance identity survives representation change.
```

which is exactly the Phase-5 recursion at a different layer:

```
Phase 5:   latent coordinate can change      Runtime:   execution representation can change
           claim identity cannot                        provenance identity cannot
```

## The split (where "4.13 ms" actually lives — not in the renderer)

```
frame(t):     execute        — the hot path carries only {state, transform, provenance_digest}
background:   preserve why    — the latent store resolves a digest to the full lineage on demand
```

The hot loop never asks *"why is this object true?"*. It asks *"what is the **identity** of the
explanation attached to this object?"* — one digest, O(1) to carry, independent of lineage depth.
A high-performance reality stack does not need every frame to carry the universe of explanation; it
needs the frame to carry an address, and the background to keep the thing it addresses.

```
LiveObject { state, transform, provenance_digest }      # hot path
ProvenanceStore: digest ──► origin · edit lineage · assumptions
                                  · survival tests · failures · verification status   # latent
```

## Run

```bash
python3 experiments/live_latent_provenance/run.py     # stdlib only; deterministic; 9/9
```

## The severance test (the sharp one)

A real system **must** compress — so compression has to be allowed. The danger is not latency; it
is an optimization that silently converts `why this exists` into `it exists`. So nulling the digest
must **not** degrade to `unknown`. The structure remains (gravity is still `0.5`); the *history* was
destroyed. That is a different category, and the runtime names it:

```
resolve(a81f92…)  → developer edit → gameplay_constraint → world_v12     (resolved)
resolve(NULL)     → PROVENANCE_SEVERED      (not `unknown`; structure remains, history lost)
```

A missing digest is a **runtime failure mode, not a silent fallback.** It connects back to the
failure taxonomy as a fourth, runtime-level mode — kept crisply distinct from the other three:

```
UNACCOUNTED          never recorded                 (no digest ever assigned — the silent gap)
PROVENANCE_SEVERED   recorded identity lost          (digest nulled or dangling; structure remains)
resource_limit       observer insufficient
assumption_limit     admissibility insufficient
```

## Calibration — `PROVENANCE_SEVERED` is not the epistemic `severance`

The failure-taxonomy `severance` means a signal is **absent in the world** (`I(X;O)=0`),
observer-independent and absolute. Runtime `PROVENANCE_SEVERED` means the world still has the
structure but the **runtime threw away its record of why**. Same word, different objects: the
runtime mode is class-relative and repairable in principle (re-commit the lineage); the epistemic
one is not. The code keeps them separate on purpose; do not conflate them.

## What it earns (9 checks)

```
hot path carries only a digest                 (full provenance ≠ hot-path representation)
the digest resolves to the full provenance     (compression conserves the lineage)
representation change keeps provenance identity (re-encode state/transform → same provenance)
severance is a distinct failure, not `unknown`  (PROVENANCE_SEVERED; structure remains)
severed ≠ unaccounted                           (lost-after-recording ≠ never-recorded)
a dangling digest is severed too                (pointing nowhere is the same failure)
optimization may compress, not sever            (compress → traceable; sever → caught)
the frame admits the traceable, refuses the severed   (the contract boundary enforces it)
```

Earned separators: **`full provenance ≠ hot-path representation`** and **`compression ≠ severance`**.

## Honest bounds — the narrow claim

The claim is **provenance-preserving compression under runtime constraints**, *not*
"provenance-bearing reality at 4.13 ms" — the latter implies silicon validation this bench does not
have. There is no GPU, no real frame timing, no real-time rendering here; those remain the un-faked
frontier (every constructed millisecond expires on real silicon). What is shown is the architectural
property that *licenses* such a stack: execution can be compressed to a digest, the full lineage
stays recoverable, and an optimization that severs provenance is a caught failure rather than a
silent collapse. The contract this hands the future renderer/world-model/agent stack:

> The world may become faster, smaller, learned, generated, distributed, or optimized.
> It may **not** become untraceable.
