<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Causal allocation — the measured boundary map

This is the single, whole statement of what the GPU benchmark established about **causal fidelity
allocation** — the Causal Continuity hypothesis (*allocate fidelity by expected future causal loss, dropping
present-perception `S`*). The individual milestones are recorded in
[`experiments/bench_gpu_real/README.md`](../experiments/bench_gpu_real/README.md),
[`docs/GENEALOGY.md`](GENEALOGY.md), and [`ursprung/causal_continuity.py`](../ursprung/causal_continuity.py);
this file exists because the **boundary map is the artifact worth preserving**, more than any one result.

All results below were measured on real silicon — an **ASUS ROG Xbox Ally X** (Radeon 890M, RDNA 3.5, Vulkan).
Every comparison used a **sealed observer** (the policy's type signature cannot read the ruler it is scored on,
so "optimize the metric" is structurally impossible), **equal measured budget**, and **ε-dominance** (a
difference counts only if it exceeds the reproducibility floor measured from the data). No scalar winners; no
claim exceeds a runnable bench.

## The thesis

The benchmark did **not** find that "causal allocation works" or "fails." It found that causal allocation's
value is a **function of the structure of the world being measured**, and it *measured where the boundaries
fall*. The same unbiased apparatus moved the same hypothesis in opposite directions depending on that
structure — which is the strongest evidence the instrument, not the hypothesis, is the durable asset.

## The map

| Regime | Result | Why | Earned by |
|---|---|---|---|
| **Spatial** (one frame) | **Conditional-negative.** The strong claim "causal weighting generally beats uniform at equal budget" is **falsified**. A conditional claim survives: causal helps only with *informative priors* **and** the *variance-optimal exponent* (∝ difficulty^(2/3), not difficulty^1). | At a near-converged budget, weighting samples ∝ difficulty **over-concentrates**; uniform is hard to beat, and a mis-aligned prior measurably hurts. | M6a (perceptual ruler) → M6b (sealed gate: uniform ε-dominates causal) → M6c (alignment × budget × exponent sweep) |
| **Temporal — present predicts future** (monotone reveal) | **Conditional-positive, reaches the ceiling.** Sealed future-causal allocation ε-dominates *both* uniform (≈21× ε) and present-difficulty (≈5× ε) on future error. | The temporal lever is real: *feed the freshly-revealed deficit, waste nothing on content that will be reset.* Beating present-difficulty (which also avoids waste) shows the win is the genuine future-causal signal, not mere culling. | T1 (temporal apparatus, world through the kernel) → T2 (temporal ruler) → T3 (sealed gate + prophet) |
| **Temporal — future hidden** (stable content, hidden importance) | **Recoverable only above a precursor threshold; a weak signal is *harmful*.** The prophet (oracle) separates by ~32× ε when the future is hidden; the sealed policy closes the gap only as a present *precursor* appears, reaching the oracle when the precursor fully signals importance. Below ρ≈0.5, acting on the noisy precursor is **worse than uniform**. | A sealed observer cannot exceed the information available to it. Worse: acting on *unreliable* foresight reshapes the allocation geometry and **starves genuinely important regions** — ignorance is safer than bad knowledge. | T4 (hidden-future importance scene + precursor sweep ρ; `gap(ρ)` = the value of inaccessible information) |

## The recurring principle

Across three independent measurements, the project found the same law in different costumes:
**acting on unreliable information is not neutral — it is negative value.**

- a **circular metric** blesses a policy that a neutral one rejects (M6b: `attestation ≠ authority`);
- **spatial over-concentration** on a difficulty signal loses to spreading (M6c);
- an **unreliable future hint** (ρ < threshold) starves what matters and loses to uniform (T4).

The recurrence is evidence the boundary map carves the problem at real joints, not artifacts of one setup.

## Honest scope — what is *not* established

- **One device, synthetic scenes.** RDNA 3.5 / Vulkan; SSAA as the quality proxy; tile-grid worlds.
  `benchmark gain ≠ universal`, and neither does a benchmark loss.
- **One coupling, held fixed.** Every temporal result is *under a declared TAA-style history accumulation +
  explicit disocclusion-invalidation model* — a chosen convention, not "the temporal law" (`declared ≠
  verified`). Varying the reuse law (partial retention, decay, re-occlusion) is a **different axis**, worth
  moving only to ask *"which reuse laws preserve these boundaries?"* — not as a reflex rung.
- **Conditions, not laws.** Each cell is *supported/falsified under its stated conditions*. The hypothesis
  status is `conditional_on_neutral_ruler` (spatial), with a conditional-positive temporal counterpart.

## The durable artifact

The benchmark is five rulers — **timing** (M1–M5), **perceptual** (M6a), **temporal apparatus** (T1),
**temporal ruler** (T2), **importance-weighted temporal ruler** (T4) — each proven *fair before any hypothesis
passed through it*. That ordering (instrument before verdict) is what let the apparatus reject a favored
hypothesis spatially and support it temporally with equal credibility. The map above is what the instrument
measured; the instrument is what makes the map trustworthy.

> A trustworthy system exposes where its competence ends, where its assumptions begin, and where further
> investigation is required. This map is that exposure for causal fidelity allocation.
