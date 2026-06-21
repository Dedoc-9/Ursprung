<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Phase 5 — Provenance-Preserving Learning

> **Representation is free; epistemic status is conserved.**

Phase 4 showed the provenance contract *survives* a learned representation. Phase 5 makes the consequence the
object: a `Representation` is not its latent vector — it is the latent **plus** the developer's declared choices
(a *creator manifest*) **plus** a provenance-qualified *claim*, and the claim, not the latent, is its identity.
The goal is explicitly **not** "find the truth"; it is *find representations whose claims remain inspectable
after learning*, so the developer stays a **named component** of the object rather than a hidden author later
mistaken for a discovering machine (the re-anthropomorphism failure).

The provenance-qualified claim is reused verbatim from Phase 3: it is the `graph_digest`. The latent coordinates
do not appear in it.

## Run

```bash
PYTHONHASHSEED=0 python3 experiments/latent_phase5/run.py     # needs numpy; seeded → replayable
```

## The four properties (+ the closed gauge)

| Test | Question | Result |
|---|---|---|
| creator visibility | can we trace which declared choices produced the latent? | manifest digest changes when a choice changes |
| intervention honesty | does the claim distinguish grounded mechanism from correlation? | declared access flips edges grounded↔assumed |
| assumption locality | does every strong claim name the assumption that enabled it? | every assumption edge carries its assumption (Phase-3 invariant) |
| **representation humility** | two encoders, different latents, same claim → equivalent? | `rep_a` and `rep_b` differ in coordinates, share claim `a0939…` → equivalent |
| scale gauge closed | can magnitude artifacts manufacture coherence? | per-column rescaling of `X` leaves the claim unchanged |

A degenerate encoder (`k=1`) that cannot recover the factors yields `INCOMPLETE:c` — it is **not** equivalent;
a representation that cannot support the claims cannot make them.

## The measured result (seed 0)

```
rep_a  per-dim identity [0.28, 0.96, 0.95]  claim a0939bb7984a
rep_b  per-dim identity [0.95, 0.71, 0.81]  claim a0939bb7984a    ← different latent, same claim
rep_deg (k=1)               claim INCOMPLETE:c                     ← cannot support the claim
rep_scaled (X rescaled)     claim a0939bb7984a                     ← scale gauge closed
rep_no_access               claim 631aa50776db                     ← declared access changes the claim
```

## Honest bounds

Phase 5 conserves epistemic status across a *change of representation*; the interventions are still ground-truth
`do()` on a known synthetic world (`do()` without a known graph remains the open frontier). The scale-gauge
result is the Phase-4 numerical-stability fix understood correctly: standardization **closes an unintended
scale gauge** so that coherence cannot be manufactured by magnitude. `created coherence ≠ discovered
coherence`; `latent ≠ truth`; the latent is the coordinate system through which a provenance-bearing claim is
expressed — not the discovery. The developer is legible *in the object*: not "the model found X," but "under
this observation map, this intervention access, this model family, and these assumptions, this structure
survived."
