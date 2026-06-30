<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# v0.2.1 Canonical Reference — Temporal-Correlation-Corrected MI

**Status: canonical.** Commit `70d0aaf`. This document is the mathematical record of what v0.2.1 established:
the exact validated numbers, the precise claim, and the declared limits. It exists so a future contributor (or
reviewer, or the author in six months) can know what v0.2.1 proved without re-deriving it from code or commits.
`committed ≠ canonical` until this record matches a reproducing run; that condition is met (see §4).

It also fixes the boundary v0.2 builds on: **v0.2 inherits a verified foundation, not an assumption.** No KSG
work begins until this is banked. `written ≠ true`; the trajectory records what occurred, not what was hoped.

---

## 0. Scope correction (read first)

This banking record corrects a framing that appeared while scoping it, because a canonical reference that
misstated its own ground truth would be the exact failure the document exists to prevent:

- **The ground truth is a discrete Markov chain, not a continuous AR(1).** v0.2.1 was validated against a
  **symmetric K-state Markov chain** (stay-probability `p`, uniform stationary distribution) with the **identity
  channel `O=S`**, so the true mutual information is exactly `I(S;O) = H(S) = log₂(K)` bits *regardless of `p`*,
  while the autocorrelation grows with `p`. This is the **discrete analog** of an AR(1) process. There is no
  correlation coefficient ρ in it. Continuous AR(1) (Gaussian, with ρ and closed-form `I = −½·log₂(1−ρ²)`) is
  the **v0.2 / KSG anchor** — an obligation v0.2 must clear, *not* a result v0.2.1 produced. `analog ≠ identical`.
- **The numbers come from three different setups, not one.** They are recorded per-check in §1 with their exact
  parameters. There was no single "ρ=0.95, 4000-sample" experiment; that conflation is corrected here.

---

## 1. The reference case (exact numbers, reproducible)

All from `tests/test_block_bootstrap.py` at `70d0aaf`. `K = 4`, identity channel `O = S`, truth `= log₂(4) =
2.0` bits. Three independent checks, each with its own parameters:

### 1a. Coverage (the crux)
Setup: stay-probability `p = 0.85`, `n = 2000` nominal samples, 40 trials, 200 bootstrap resamples per estimate.
A trial "covers" if its 95% CI contains the known 2.0 bits.

| estimator | CI method | point (bias) correction | coverage |
|---|---|---|---|
| `MillerMadowEstimator` (v0.1) | i.i.d. bootstrap | Miller–Madow at **nominal** `n` | **0.23** |
| *(intermediate, not shipped)* | stationary bootstrap | Miller–Madow at **nominal** `n` | **0.33** |
| `BlockBootstrapEstimator` (v0.2.1) | stationary bootstrap | Miller–Madow at **effective** `n` | **0.95** |

The intermediate row is the load-bearing evidence for the two-part claim (§2): fixing the CI alone moves
coverage only 0.23 → 0.33. The i.i.d. estimator's CI is wrong **77% of the time** under this autocorrelation.

### 1b. Effective-sample-size detection
Setup: `n = 4000`.

- Autocorrelated (`p = 0.9`): `τ = 16.4`, `eff_n = 244` of 4000 — the dependence destroys **~94%** of the
  nominal sample information.
- Memoryless (`p = 1/K = 0.25`, i.e. i.i.d.): `τ = 1.0`, `eff_n = 4000` — the estimator correctly identifies
  independence when it exists, with no spurious discount.

### 1c. Gate refusal
Setup: a **deterministic, non-uniform** block stream `([0]×40 + [1]×30 + [2]×20 + [3]×10) × 2`, `n = 200`,
identity channel. (Deterministic and non-uniform by design — see Limit A in §3.) Result: `eff_n = 9`.

- Nominal-`n` gate (v0.1): `n = 200 ≥ 5·joint_support = 20` → **ESTIMATED**.
- Effective-`n` gate (v0.2.1): `eff_n = 9 < 20` → **UNDERDETERMINED** (correct refusal).

**If these numbers do not reproduce on a clean checkout, v0.2.1 is not canonical.**

---

## 2. The precise mathematical achievement

**Temporal dependence corrupts both moments of the MI estimator, and both require the effective-`n`
correction.** Two corrections, both necessary, neither sufficient alone:

**Correction 1 — Stationary bootstrap (Politis & Romano 1994).** Replace i.i.d. resampling of `(s,o)` pairs with
resampling of geometric-length, wrap-around blocks whose expected length is tied to the autocorrelation time `τ`.
This preserves the temporal dependence structure during resampling, so the bootstrap CI reflects the true
sampling distribution under dependence rather than the artificially narrow i.i.d. approximation. **Alone:
0.23 → 0.33** — it widens the interval but leaves its center biased.

**Correction 2 — Effective-`n`-scaled Miller–Madow.** The Miller–Madow bias term `(m−1)/(2·n·ln2)` (per entropy;
`m` = observed non-zero bins) uses nominal `n` in its denominator. Under autocorrelation the bias is governed by
the **effective** number of independent observations `eff_n = n/τ`, not `n`. Scaling the correction to use
`eff_n` aligns the point estimate's systematic bias with the actual information content of the sample. **Alone:
corrects the center without widening the interval.**

**Combined: 0.95.** The precise claim is therefore *not* "block bootstrap fixes it" but: **under temporal
dependence the variance (CI width) and the mean (point estimate) are each wrong, and each must be corrected by
the effective sample count.** Correcting one without the other yields an interval that is either centered wrong
(stationary bootstrap alone) or sized wrong (effective-`n` MM with an i.i.d. CI).

`τ` is estimated as the integrated autocorrelation time of the **pointwise-MI series** (whose mean *is* the MI,
so its autocorrelation governs both the bias and the variance of the MI estimate), truncated at the first
non-positive lag (initial-positive-sequence rule).

---

## 3. Declared sensitivity limits (limitations, not defects)

**Limit A — the ESS proxy is unreliable under uniform marginals.** `τ` is read *through* the pointwise-MI
series. For a symmetric, uniform channel the pointwise MI is near-constant (every symbol carries equal
surprisal), so there is little per-sample structure to expose the dependence; `τ` then tends toward 1
(declaring independence) even when dependence exists through higher-order structure. **Consequence:** v0.2.1's
correction is reliable when the marginal carries structure (real game loops, trajectories, AR-like processes)
and unreliable for near-deterministic uniform channels — *which is exactly the v0.1 toy scene*. Running
v0.2.1's corrected CIs on the toy scene and trusting them would be **circular**: the proxy cannot measure
dependence it cannot see. This is why §1c uses a deterministic *non-uniform* stream, and why the toy scene's
i.i.d. validation (which is valid there, because the i.i.d. assumption holds) is **not** the anchor for
v0.2.1. `uniform-marginal ⇒ pmi-series ≈ const ⇒ τ-proxy blind`.

**Limit B — single-channel, univariate ESS.** The estimator treats the `(S,O)` pair as one univariate series
(the scalar pointwise-MI contribution). Multivariate autocorrelation — where `S` and `O` each carry dependence
that does not factor through the scalar MI — is not captured. **Scope:** a v0.2.2 refinement (spectral density
at zero, or a batch-means / multivariate effective-sample-size estimator from the MCMC output-analysis
literature). Method named, citation deferred until verified — *documented, not built*.

**Limit C — gate interaction changes the user-facing performance profile.** The effective-`n` gate (refuse if
`eff_n < 5·joint_support`) is strictly more conservative than the nominal-`n` gate; it refuses where the
nominal gate accepts (§1c). On a real loop with moderate autocorrelation (`τ ≈ 5 ⇒ eff_n ≈ n/5`),
`UNDERDETERMINED` is reached at roughly **5× the nominal sample count** a v0.1-calibrated user would expect.
This is honest behavior, not a regression — but it is a behavioral change and is recorded as such.

---

## 4. Canonical completeness declaration

v0.2.1 is **canonically complete** when, and is hereby recorded as having met:

- **(a) The reference numbers reproduce on a clean checkout.** Met: at `70d0aaf`, `python
  tests/test_estimator.py` → 5/5 and `python tests/test_block_bootstrap.py` → 4/4, emitting the §1 figures
  (coverage 0.23→0.95, τ=16.4/eff_n=244 vs τ=1.0/eff_n=4000, gate eff_n=9/200).
- **(b) The two-part correction is documented with the precise claim** (both moments corrupted; both corrected
  by effective `n`). Met: §2, including the 0.33 intermediate that isolates the necessity of each part.
- **(c) The three sensitivity limits are declared.** Met: §3 (uniform-marginal ESS blindness; univariate-only
  ESS; gate-interaction profile change).
- **(d) The canonical ground truth is named correctly.** Met: §0 — v0.2.1's anchor is the **discrete
  Markov-chain** ground truth in `tests/test_block_bootstrap.py`; the **continuous AR(1) + KSG** anchor (ρ,
  `I=−½log₂(1−ρ²)`) is the **v0.2** obligation, not a v0.2.1 result.

Until all four held, v0.2 would have built on sand. They hold. v0.2 may begin from a banked foundation — and
inherits one explicit obligation from this record: **the effective-`n` correction must be carried onto the KSG
estimator and re-validated against the continuous AR(1) anchor**, because nearest-neighbour MI inherits the
dependence problem twice (in the input correlation *and* in the neighbour geometry), and a continuous estimator
with i.i.d.-only CIs is still wrong on a real loop. `necessary ≠ sufficient`.

---

## References (verified)

- Politis & Romano, "The Stationary Bootstrap," *JASA* 1994 — the dependent-data resampling method (Correction 1).
- Miller, "Note on the Bias of Information Estimates," 1955 — the bias correction scaled here by effective `n`.

*(Multivariate / spectral ESS methods referenced in Limit B are described by method only; no author-year is
asserted until verified. `a citation is a claim`.)*
