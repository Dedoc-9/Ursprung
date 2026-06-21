<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Phase 1 — the latent benchmark (real-ML, the first non-illustrative numbers)

This is the first step of the [`LATENT_SPACETIME`](../../docs/LATENT_SPACETIME.md) pivot, built in the order the
project's discipline demands: **the benchmark first, the autoencoder second.** The benchmark embodies the
epistemology; an autoencoder is just one candidate explanation fed into it. If the autoencoder came first,
reconstruction accuracy would quietly start acting as truth again — the failure the rest of the project exists
to prevent.

It is deliberately **outside** the `ursprung/` package and the 495-check stdlib suite: it needs `numpy`, and the
verified deterministic core stays dependency-free. This layer is the experimental frontier, where numbers are
*measured*, not constructed — and where they are allowed to fail.

## Run

```bash
PYTHONHASHSEED=0 python3 experiments/latent_phase1/run.py     # needs numpy; fully seeded → replayable
```

## What it does

- `world.py` — a small causal world: generator `g`, confounder `c = 0.6·g + noise` (correlated with `g`, so it
  *looks* predictive), observable `X = [g,c]·Aᵀ + ε`, outcome `y = g` (depends on `g` only). Plus `do()`.
- `benchmark.py` — the encoder-agnostic harness, four gates + `GeneratorScore`. All recoverability is measured
  with a **gauge-invariant** statistic (R² from the latent's column space), never a single dimension.
- `encoders.py` — the model class `𝓕 = {E1 PCA, E2 linear-AE, E3 MLP-AE}`, the latent analogue of the symbolic
  `F1,F2,F3`. Candidates, not authorities.
- `run.py` — runs the report and self-checks the discipline result.

## The four gates

| Gate | Question | Failure mode caught |
|---|---|---|
| 1 reconstruction | can the latent reproduce the observable? | underfit latents (entry gate — passes almost everything) |
| 2 intervention | does `do(factor)` move the outcome? | confounders masquerading as causes |
| 3 model-class robustness | does the factor survive a change of encoder? | encoder-specific artifacts |
| 4 gauge invariance | does the metric survive latent rotations? | coordinate-system illusions |

`GeneratorScore = intervention · robustness · gauge_invariance` — the learned analogue of
`generator = invariant ∧ necessary ∧ model-robust`.

## The measured result (seed 0)

```
reconstruction R²:   E1_pca 1.000   E2_linear_ae 0.649   E3_mlp_ae 0.956
recoverability:      g recovered ≥0.987 and c recovered ≥0.985 by EVERY encoder
intervention:        do(g) → outcome moves 1.00 ;  do(c) → outcome moves 0.00
GeneratorScore:      g = 0.987      c = 0.000
```

Reconstruction, recoverability, robustness, gauge-invariance, **and** correlation-with-outcome all fail to
separate `g` from `c`. Only the **intervention gate** does. `c` is the textbook trap: it reconstructs, is fully
recoverable across the whole model class, is gauge-invariant, and correlates with the outcome at ≈0.6 — yet
`GeneratorScore(c) = 0` because `do(c)` does not move the outcome. **`good reconstruction ≠ recovered
generator`.**

## Honest bounds

A toy: linear-Gaussian world, three small numpy encoders, a single seed. The intervention here coincides with a
clean ground-truth `do()` because the world is known; a real system has neither a known causal graph nor a free
`do()` operator, and recovering the generator there is the open problem. What transfers is the **procedure and
the ordering** — score on Gates 2–4, never on Gate 1 alone — not these specific numbers, which expire on real
data. `latent ≠ truth`.
