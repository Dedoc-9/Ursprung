<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Min-entropy dual-witness study — a reproduction, not a discovery

A graded record of a six-step investigation into estimating **worst-case (min-entropy) leakage** alongside
average (Shannon) leakage in a side-channel firewall. It is held to the same discipline as the rest of the
repo: every claim carries a grade, a mechanism, a `does_not_show`, and a falsifier. **This study claims no new
theory.** Its results were *already known* to the literature; the contribution is a small, reproducible,
claim-ledger-graded *characterization* on ground-truth channels. `reproduced ≠ discovered`; `measured ≠
guaranteed`; `better-estimator ≠ certifier`.

Scripts: [`step1`](../step1_dual_witness_baseline.py) … [`step6`](../step6_threshold_sweep.py) at the repo root;
the architectural side-thread is [`experiments/live_world_kernel/repo_audit.py`](../experiments/live_world_kernel/repo_audit.py).

## 1. The question

A leakage gate that watches only **Shannon mutual information** measures *average* bits learned and is blind to
*one-shot* guessing risk: a channel can leak little on average yet hand an adversary the secret in a single
guess (Smith 2009). The principled fix is a **dual witness** — report Shannon MI *and* **min-entropy leakage**
side by side, never fused into a scalar. The question this study answers empirically: *can the min-entropy
witness actually be estimated well enough, from finite samples, to gate on?*

## 2. What was already known (so we do not re-claim it)

- **Min-entropy leakage is much harder to estimate than MI.** Stated explicitly by Chothia & Kawamoto (2014):
  min-entropy estimation "requires many more trial runs than that of mutual information." Their paper provides a
  **confidence interval** (χ² and Bernstein/Hoeffding bounds) and leaves point-bias correction *open*.
- **Estimating a small probability `p` needs ~`1/p²` samples** for a useful additive bound — standard
  rare-event statistics.
- **Frequentist/plug-in leakage estimation does not scale to large output spaces.** F-BLEAU (Cherubin,
  Chatzikokolakis, Palamidessi — IEEE S&P 2019) identifies exactly this and *solves* it with nearest-neighbour
  (NN) / ML estimators that exploit **output-space geometry** ("nearby outputs → same secret").

A literature check (recorded mid-study) confirmed all three. The earlier internal framing of a novel "1/p²
wall" was therefore **withdrawn**: it is a known consequence of rare-event estimation, and F-BLEAU already
characterises and partially overcomes the plug-in's failure. `written ≠ true` — we checked before claiming.

## 3. The harness

- **Ground-truth channels.** (a) A *symbolic* Smith counterexample (disjoint observation alphabet: masks in
  `[0,n)`, exact leaks in `[n,2n)`) where exact Shannon MI and min-entropy leakage are computed by enumeration;
  (b) a *metric* Gaussian channel (`observation = secret + N(0,σ)`) with exact leakage by numerical integration.
- **Estimators.** Miller–Madow plug-in MI (shipped `channel_profiler`); plug-in min-entropy; bootstrap
  bias-corrected min-entropy (reverse-percentile, Efron); the C–K Theorem-3 interval; and an F-BLEAU-style
  1-D NN estimator (`k≈√n`).
- **Controls & grading.** A **metric-scramble** control (same channel information, output order destroyed)
  isolates whether an estimator's gain is *geometric*. Every step registers a `Claim` via
  [`weltwerk/verify/claim_ledger.py`](../weltwerk/verify/claim_ledger.py); grades emerge from measured
  coverage/bias, never from intent.

## 4. Results — graded

| Step | What it measured | Result | Grade |
|---|---|---|---|
| 1 | Dual-witness ground truth (Smith) | Shannon `1.37 b` vs min-entropy `6.66 b` — the gap a Shannon-only gate misses is **real**; but finite-sample plug-in **under-covers** (0/12 on the dangerous channel) | SPECULATIVE |
| 2 | Bootstrap bias correction | Reduces bias ~30%, **insufficient** for coverage at n ≤ 30k; bias shrinks with n (systematic, not variance) | SPECULATIVE |
| 3 | Temporal / effective-n correction | **Not the lever** — bias dominates even at zero autocorrelation; block-bootstrap widens the CI correctly but cannot move a biased centre | SPECULATIVE (hypothesis eliminated) |
| 4 | C–K Theorem-3 guaranteed interval | Coverage guaranteed by construction, but **vacuous** `[0, log₂\|S\|]` on rare-leak channels: lower-bounding each rare leak's probability needs `ε₂ < p_leak`, i.e. `n ∝ 1/p²` (~3 M here) | SPECULATIVE |
| 5 | NN vs plug-in (structure test) | NN **beats** plug-in *iff* the output space is large **and** metric: at K=64 it **halves** the bias (`-0.26` vs `-0.56`); scramble control confirms the gain is geometric; no gain at K=8 | **MEASURED** |
| 6 | Threshold sweep over K | NN bias-reduction is **monotone** in output size: `~0%@K=8 → 30%@K≈32 → 69%@K=128` (figure `nn_threshold_sweep.png`); geometric at every K | **MEASURED** |

## 5. Discussion

**The one durable, positive claim (MEASURED).** Nearest-neighbour min-entropy estimation removes a growing
fraction of the plug-in's bias as the output alphabet grows, and the advantage is **geometric** — it vanishes
when the output metric is scrambled. *Practical guidance:* prefer an NN/F-BLEAU-style estimator when the
observation space is **large and metric-valued** (which real timing/power side channels are); the plug-in is
adequate for small, well-sampled alphabets.

**What it does not show.**
- *Not a certifier.* NN is a **better estimator, not an unbiased one** — residual bias is still ~6% at K=128.
  No grade above MEASURED is claimed, and the dual-witness min-entropy *gate* remains **SPECULATIVE**.
- *The threshold is setup-relative.* `K≈32` depends on `(n, σ, plug-in bin count)`; the robust statement is the
  **scaling** (plug-in degrades with K faster than NN), not the exact crossing.
- *The rare-leak wall is estimator-independent.* On **symbolic / structure-less** channels (the Smith
  worst case) no estimator helps, because there is no output metric to exploit — consistent with the
  rare-event `1/p²` floor.
- *Scope.* 1-D continuous metric, i.i.d. sampling. Higher-dimensional metrics and non-stationary streams are
  untested.

## 6. Conclusion

The dual-witness *concept* is sound and its ground-truth gap is real; the min-entropy *witness* is feasible and
efficient **only where the output space carries exploitable geometry**, and even then yields a better estimate
rather than a guarantee. None of the underlying limits are new — they restate C–K, rare-event estimation, and
F-BLEAU — so this is a reproducible characterization with explicit boundaries, not a breakthrough. The honest
one-liner: *single-metric leakage gates miss worst-case risk; the worst-case witness is estimable in proportion
to the output space's geometry, and unestimable without it.*

**Reproduce:** `PYTHONHASHSEED=0 python3 step1_dual_witness_baseline.py` … `step6_threshold_sweep.py`
(Windows: set `$env:PYTHONUTF8="1"` if redirecting output — see `AGENTS.md`).

## References

- G. Smith. *On the Foundations of Quantitative Information Flow.* FOSSACS 2009.
- M. Alvim, K. Chatzikokolakis, C. Palamidessi, G. Smith. *Measuring Information Leakage using Generalized Gain
  Functions (g-leakage).* CSF 2012.
- T. Chothia, Y. Kawamoto. *Statistical Estimation of Min-Entropy Leakage.* 2014 (leakiEst).
- G. Cherubin, K. Chatzikokolakis, C. Palamidessi. *F-BLEAU: Fast Black-box Leakage Estimation.* IEEE S&P 2019.
- D. Politis, J. Romano. *The Stationary Bootstrap.* JASA 1994.
- G. Miller. *Note on the bias of information estimates.* 1955 (Miller–Madow).

*Grades are point-in-time and re-checkable: re-run the step scripts. `integrity ≠ truth`.*
