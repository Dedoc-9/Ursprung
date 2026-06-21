<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Phase 4 — Representation Learning Under Provenance Constraints

The transition from the symbolic phases into ML — but with the question deliberately inverted. **Not** "can a
neural network discover causes?" but **"can a learned latent produce objects that satisfy the contract the
earlier phases already built?"** The hand-written factors (`g`, `m`, `c`) are replaced by *learned* latent
coordinates while every discipline object — claim, ledger, edge, graph — is left **unchanged**. If they stop
being meaningful, the contract was too symbolic. If they survive, the contract survived ML.

The test reuses **Phase-2 topology** and the **Phase-3 provenance contract** *as imported code, unedited*. That
reuse is the experiment.

## Run

```bash
PYTHONHASHSEED=0 python3 experiments/latent_phase4/run.py     # needs numpy; seeded → replayable
```

## Files

```
world.py        synthetic SCM (g→m→y chain + confounder c), ground-truth do()
encoder.py      learned representation families (AE / linear-AE / MLP-AE) — the latent 𝓕
intervene.py    gauge-invariant recoverability + do()->outcome sensitivity
topology.py     recover the intervention graph over learned factors (Phase-2 logic)
provenance.py   imports the Phase-3 CausalEdge / ProvenanceGraph UNCHANGED and wraps recovered edges
robustness.py   ⋂ over encoder families
run.py          the tiered benchmark + self-check
```

## The benchmark hierarchy

```
Tier 0  reconstruction        admission ticket only — good reconstruction ≠ recovered generator
Tier 1  intervention          changing a latent factor changes the outcome? (relevance, over learned factors)
Tier 2  latent topology       where in the intervention graph (Phase-2 logic, learned factors)
Tier 3  representation robust  which relations survive a change of encoder family (⋂ over 𝓕)
Tier 4  provenance-preserving  can the learned system emit edge + support + assumption + digest, never bypassing the contract?
```

## The measured result (seed 0)

```
Tier 0  reconstruction:  AE_pca 1.000  AE_linear ~0.65  AE_mlp ~0.95
Tier 1  g and c BOTH recoverable from the learned latent (≥0.98); do(g)->outcome=1.00, do(c)->outcome=0.00
Tier 2  roles: g=root, m=mediator, y=sink, c=isolated
Tier 3  robust recoverability(g) ≥ 0.98 across all encoder families
Tier 4  graph over learned-factor nodes (z::g→z::m→y intervention_grounded; z::c→y assumption_load_bearing);
        the Phase-3 constructor REFUSES an assumption edge without a declared assumption
```

`g` and `c` are both recoverable and reconstruct — only intervention separates them — and the discipline objects
accept learned-factor node labels (`z::g`, `z::c`) without modification.

## Success criterion (intentionally narrow)

> **A learned latent factor may be unknown. Its provenance may not be.**

The latent's per-dimension identity is gauge-ambiguous (per-dim correlation with `g` changes under a latent
rotation, e.g. `0.67/0.75 → 0.39/0.92`), yet the edge `z::g→z::m` keeps a fixed `intervention_grounded`
provenance and the graph's recoverability is gauge-invariant. We may not be able to name what the latent factor
*is*; we can still say, immutably, **how its edges were supported.**

## Honest bounds

Phase 4 learns the **representation**; the interventions are still ground-truth `do()` on a known synthetic
world. So this tests "does provenance survive learning," **not** "do() without a known graph" — that remains the
Phase-3+ frontier. No LLMs, no large datasets, no score-chasing: the only question is whether identity still
includes provenance once the representation is learned. It does. `latent ≠ truth`; `recovered topology ≠
discovered ontology`; `chosen ≠ derived`.
