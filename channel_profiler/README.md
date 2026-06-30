<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Ursprung Channel Profiler (v0.1)

**What your observer learns — in bits, with error bars.** A standalone, pure-Python wedge that turns an
interactive system into a QIF-measured channel: it measures the mutual information `I(secret; observation)` an
observer gains per step, reports it with a confidence interval (or refuses with `UNDERDETERMINED`), and — if the
host opts in — drives an advisory closed loop that reduces fidelity until leakage falls under a declared budget.

It is **OBSERVER-class**: it measures and reports; it never controls the host loop. `telemetry ≠ control`;
`estimate ≠ capacity`; `measured ≠ guaranteed`.

## Run the demo

```bash
pip install -r channel_profiler/requirements.txt

# 1. Validation: 5 checks against the toy scene's ANALYTIC ground truth
python tests/test_estimator.py
#   -> CI coverage ~0.95; the MM estimate's CI covers analytic I(S;O)=1.9722 bits at r=2;
#      UNDERDETERMINED fires at n=20; Miller-Madow reduces the plug-in bias.

# 2. The closed loop: measure -> over budget -> shrink fidelity -> re-measure -> converge
python demo_closed_loop.py
#   writes demo_metrics.jsonl + demo_convergence.png
```

Reference convergence (budget = 2.5 bits/step; analytic anchor in parentheses):

```
  win  radius   MI (bits)   95% CI          verdict
    0      4      5.810   [5.72,5.85]      ABOVE_BUDGET    (analytic 5.84)
    1      3      3.697   [3.58,3.80]      ABOVE_BUDGET    (analytic 3.75)
    2      2      1.916   [1.81,2.03]      BELOW_BUDGET    (analytic 1.97)  -> CONVERGED
```

## What's here

| File | Role |
|---|---|
| `experiments/toy_scene/analytic_mi.py` | the **validation anchor** — exact `I(S;O)=H(O)` for the coarsening channel |
| `experiments/toy_scene/scene.py` | `ToyGridScene` (a `Client`): trajectory `step()` + i.i.d. `sample_iid()` |
| `experiments/toy_scene/run_trajectory.py` | emit a sample stream as JSONL |
| `channel_profiler/messages.py` | `SampleMessage` / `CapacityReport` / `SessionConfig` / `ChannelEstimate` (wire-shaped, `protocol_version=1`) |
| `channel_profiler/protocols.py` | `ChannelEstimator` / `Client` interfaces (a future Rust port mirrors these) |
| `channel_profiler/window_manager.py` | the trigger policy (window full; fidelity-change reset) |
| `channel_profiler/estimator.py` | `MillerMadowEstimator` — bias-corrected MI + bootstrap CIs + sufficiency gate |
| `tests/test_estimator.py` | validation against the analytic anchor |
| `demo_closed_loop.py` | the closed loop |

## Honest boundaries (`does_not_show`)

- **The estimate is not the capacity.** Every number carries a 95% bootstrap CI and the estimator/`n`/alphabet
  it was made under; below sample sufficiency (`n < 5·joint-support`, Paninski regime) it returns
  `UNDERDETERMINED`, never a fabricated bit-count.
- **Validation uses i.i.d. sampling** (matches the analytic prior). A pure greedy *trajectory* NPC parks at a
  wall, collapsing its channel entropy to ~0 — so the demo uses a stochastic (i.i.d.) environment where the
  channel has stationary, measurable leakage. `analytic ≠ trajectory`; `trajectory-parks ≠ stationary-channel`.
- **Class-relative.** Leakage is measured against a discrete-binning estimator and the modeled secret/observation
  tags; a richer observer sees more (`secure-against-this-observer ≠ secure`). Continuous/high-dimensional
  channels need a continuous estimator (KSG/neural) — a v0.2 concern.
- **Standalone, not coupled to the renderer.** It lives in its own package (not under `ursprung/`, whose
  `__init__` eagerly imports the sealed-workbench renderer). No Rust, no gateway schemas in v0.1.

## References (verified)

- Goguen & Meseguer, "Security Policies and Security Models," **IEEE S&P 1982** (noninterference — the structural foundation).
- Mestel, "Quantifying information flow in interactive systems," **CSF 2019** (the log/linear capacity dichotomy).
- Miller, "Note on the Bias of Information Estimates," **1955** (the bias correction).
- Paninski, "Estimation of Entropy and Mutual Information," **Neural Computation 2003** (small-sample bias / the sufficiency regime).
- Kraskov, Stögbauer & Grassberger, "Estimating Mutual Information," **Phys. Rev. E 2004** (continuous-estimator path, v0.2).
- Efron & Tibshirani, *An Introduction to the Bootstrap*, **1993** (the CI method).

## License

AGPL-3.0-only (inherits the repository license for v0.1).
