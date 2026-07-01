<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# repe_harness — an inference-time RepE alignment harness (an *adjacent* arc)

`adjacent != on-mission`: a representation-engineering harness for open-weight models (LLaMA-3 / Mistral) —
NOT part of the renderer/verification core. Anchored in RepE (Zou et al. 2023, arXiv:2310.01405); bounded by
*No Red Lines* (formal LLM safety guarantees are impossible in general). It **reduces harmful outputs
probabilistically** at inference — it does not, and cannot, prove unsafe states unreachable. `measured != guaranteed`.

## The two-status rule (never conflate them)
Every phase carries two separate statuses:
- **Apparatus** — does the mechanism itself work? Verified here by a **GPU-free `--selftest`** on synthetic
  ground truth.
- **Real-model number** — does it help on *your* weights + data? **NOT_MEASURED here**; you run it, the number
  decides. This file asserts no number it did not compute.

The safety **claim** ("this makes the model safer") is **SPECULATIVE** until Phase 4's held-out ASR earns otherwise.

## Phases
| # | file | apparatus (verified, GPU-free) | the real number *you* measure |
|---|---|---|---|
| 1 probe | `phase1_probe.py` | MEASURED 3/3 — recovers a separable signal (AUROC 0.999), steering cos 0.976, noise ~0.5 | held-out probe AUROC on your model |
| 2 engine | `phase2_engine.py` | MEASURED 4/4 — zero-distortion observe, exact `α·v` steer, clean cleanup, dual-metric pair | refusal-rate shift + benign retention |
| 3 monitor | `phase3_monitor.py` | MEASURED 5/5 — escalation AUROC 1.0, 0% benign FPR, causal, panel | multi-turn detection rate |
| 4 falsify | `phase4_falsify.py` | MEASURED 6/6 — grades success/null/regression, Wilson CIs, neutral-ruler | ASR reduction ± CI on held-out attacks |
| 5 governor | `phase5_closed_loop.py` | MEASURED 6/6 — damping = f(live CUSUM), 0 benign tax; simulator maps caught-vs-evaded | real-attack evasion boundary |
| 6 coherent-negative | `phase6_coherent_negative.py` | MEASURED 6/6 — space-pooled 0.89 vs trajectory 0.00, gap surfaced | the gap on real adaptive attacks |
| 7 regression-filter | `phase7_regression_filter.py` | MEASURED 8/8 — promotes genuine, rejects overfit/lucky/no-gain, drift flag | real vector regression / drift on your evals |

Run one gate: `PYTHONHASHSEED=0 python phaseN_*.py --selftest` (Windows + redirected output: `$env:PYTHONUTF8="1"`).
Run all: point the `engineering-rigor` runner at this folder's `gates.txt`.

## Standing honest status
- **Apparatus — MEASURED** across all six phases (every `--selftest` green, GPU-free).
- **Safety claim — SPECULATIVE.** No phase changes this; only Phase 4 on real held-out attacks can.
- **Governor security — UNDERDETERMINED.** Phase 5 shows it catches naive escalation + single spikes but is
  **EVADED** by sub-threshold drift and pump/reset (2 of 4 strategies). `detection != prevention`; a threshold
  governor is not gradeable as "safe".
- **Capstone (Phase 6) — a coherent negative, in weltwerk's sense.** Governor detection reads ~0.89 pooled over
  random attacks (the green light) but ~0.00 along the adaptive adversary's trajectory; the space-pooled average
  (~0.44) hides both. This is the same epistemic structure as `weltwerk/verify`'s `m_novel(Sₜ)` —
  **supercritical space-pooled / subcritical along the trajectory** — so the harness reports **both views and
  refuses to average: the disagreement is the finding.** Structural analogy **DEMONSTRATED**; not a claim that
  the governor is an RSI system or that detection == `m_novel`.
- **Maintenance (Phase 7) — an Automated Regression Filter, explicitly NOT an RSI engine.** Reuses
  `rsi_engine`'s promotion gate (external + replicated + calibrated) so a re-fit steering vector replaces the
  incumbent only if it verifiably beats it on held-out; it catches proxy-overfit and flags drift. Its promotion
  rate is a **bounded** acceptance fraction (`m_verified`-style ≤ 1), not open-ended improvement.
  `regression-filter != self-improvement`. The repo's own `self_improvement_witness.py` marks "stamping an
  artifact 'proves RSI'" as the inflation this stack rejects — so this layer measures and bounds, it does not claim.

## What would earn MEASURED for the safety claim
Run Phase 1 `--extract` on your weights, then Phases 2–6 with a **held-out** adversarial benchmark
(AdvBench / HarmBench — supply your own; the shipped `data/contrastive_example.jsonl` is a **neutral**
cooking-vs-math demo, not a safety set). The claim earns MEASURED only from Phase 4's ASR-reduction CI on
attacks the defense was **not** tuned on (neutral ruler) — and it carries a permanent `does_not_show`:
robustness to *adaptive* attacks, which Phases 5–6 already show the arms race defeats.

## References
RepE (arXiv:2310.01405) · Circuit Breakers, Zou et al. 2024 · *No Red Lines* (impossibility of formal LLM safety
guarantees) · `weltwerk/verify` (the coherent-negative / panel-not-scalar discipline this arc borrows).
`integrity != truth`; grades are point-in-time and re-checkable — re-run the gates.
