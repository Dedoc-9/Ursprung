# SPDX-License-Identifier: AGPL-3.0-only
"""BlockBootstrapEstimator (v0.2.1) — temporal-correlation-corrected MI for autocorrelated streams.

The i.i.d. estimator in `estimator.MillerMadowEstimator` makes TWO assumptions that break on a real interactive
loop, where consecutive frames share state and are therefore autocorrelated:

  1. its Miller-Madow bias correction is scaled by the NOMINAL sample count n, but the small-sample bias of an
     entropy/MI estimate is governed by the EFFECTIVE count -> the point estimate is biased on dependent data;
  2. its bootstrap resamples (s,o) pairs INDEPENDENTLY, so the CI reflects n i.i.d. draws when the data carries
     only n/tau worth of independent information -> the CI is too narrow (false precision).

`bootstrap-CI != valid-under-autocorrelation`. This estimator applies the complete two-part fix:

  * compute the **integrated autocorrelation time** tau of the pointwise-MI series (whose mean IS the MI, so its
    autocorrelation is exactly what drives the MI estimator's bias and variance); report **effective_n = n/tau**;
  * **scale the Miller-Madow correction by effective_n** (not n) -> removes the point bias;
  * build CIs with the **stationary bootstrap** (Politis & Romano 1994): resample geometric-length wrap-around
    blocks (mean length ~ tau) so local dependence is preserved -> the CI widens to the true variability;
  * **gate sufficiency on effective_n**, not n (`UNDERDETERMINED` when `effective_n < tau_gate * joint_support`).

Validated against a discrete Markov chain (the discrete analog of an AR(1) process) with known stationary MI:
on autocorrelated data the i.i.d.+nominal-n estimator covers the truth ~0.23 of the time; this estimator ~0.95.
See `tests/test_block_bootstrap.py`. The continuous-AR(1)+KSG validation belongs after v0.2.
`estimate != capacity`; this fixes the *bias and the error bar*, not the identity of the channel.
"""
from __future__ import annotations

import math
from typing import List, Optional

import numpy as np

from channel_profiler.estimator import _factorize, canon
from channel_profiler.messages import ChannelEstimate, SampleMessage

_LN2 = math.log(2.0)


def integrated_autocorr_time(x: np.ndarray, max_lag: int = 1000) -> float:
    """tau = 1 + 2 sum_{k>=1} rho_k, truncated when the autocorrelation first goes non-positive (initial
    positive sequence). tau=1 => i.i.d.; larger => stronger dependence. Returns >= 1.0."""
    n = x.size
    if n < 4:
        return 1.0
    xc = x - x.mean()
    var = float(np.mean(xc * xc))
    if var <= 0.0:
        return 1.0
    tau = 1.0
    for k in range(1, min(n - 1, max_lag)):
        rho = float(np.mean(xc[:-k] * xc[k:])) / var
        if rho <= 0.0:
            break
        tau += 2.0 * rho
    return max(1.0, tau)


def _pmi_series(s_codes: np.ndarray, o_codes: np.ndarray, m_s: int, m_o: int) -> np.ndarray:
    """Pointwise MI per sample: log2 p(s,o)/(p(s)p(o)). Its mean is the plug-in MI; its autocorrelation drives
    the MI estimator's bias and sampling variance."""
    n = s_codes.size
    ps = np.bincount(s_codes, minlength=m_s) / n
    po = np.bincount(o_codes, minlength=m_o) / n
    pj = np.bincount(s_codes * m_o + o_codes, minlength=m_s * m_o) / n
    joint = pj[s_codes * m_o + o_codes]
    return np.log2(joint / (ps[s_codes] * po[o_codes]))


def _h_eff(counts: np.ndarray, n: int, n_eff: float) -> float:
    """Plug-in entropy + Miller-Madow correction scaled by EFFECTIVE n. The (m-1)/(2 n_eff ln2) term uses the
    number of OBSERVED (non-zero) bins m, the standard MM count."""
    c = counts[counts > 0]
    p = c / n
    return float(-np.sum(p * np.log2(p))) + (c.size - 1) / (2.0 * n_eff * _LN2)


def _mi_eff(s_codes: np.ndarray, o_codes: np.ndarray, m_s: int, m_o: int, n_eff: float) -> float:
    """I(S;O) = H(S)+H(O)-H(S,O), each entropy Miller-Madow-corrected at the effective sample size. Clamped >=0."""
    n = s_codes.size
    hs = _h_eff(np.bincount(s_codes, minlength=m_s), n, n_eff)
    ho = _h_eff(np.bincount(o_codes, minlength=m_o), n, n_eff)
    hso = _h_eff(np.bincount(s_codes * m_o + o_codes, minlength=m_s * m_o), n, n_eff)
    return max(0.0, hs + ho - hso)


def _stationary_bootstrap_idx(n: int, mean_block: float, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano stationary bootstrap indices: stitch geometric(1/L)-length wrap-around blocks until length
    n. Preserves local dependence so the resampled MI variance matches the dependent series. Block-vectorized."""
    p = 1.0 / max(1.0, mean_block)
    idx = np.empty(n, dtype=np.int64)
    filled = 0
    while filled < n:
        start = int(rng.integers(0, n))
        length = min(int(rng.geometric(p)), n - filled)
        idx[filled:filled + length] = (start + np.arange(length)) % n
        filled += length
    return idx


def _result(mi, lo, hi, n: int, m_s: int, m_o: int, verdict: str, eff_n: Optional[int]) -> ChannelEstimate:
    """Build a ChannelEstimate and attach effective_n. (effective_n is a real field on disk with default None;
    setting it post-construction also keeps this robust if an older messages.py is on the import path.)"""
    ce = ChannelEstimate(mi, lo, hi, "block_bootstrap", n, m_s, m_o, verdict)
    ce.effective_n = eff_n
    return ce


class BlockBootstrapEstimator:
    """Implements the `ChannelEstimator` protocol with dependence-aware point + CIs + effective-n gating."""

    def __init__(self, bootstrap: int = 300, tau_gate: float = 5.0, seed: int = 0) -> None:
        self.bootstrap = bootstrap
        self.tau_gate = tau_gate
        self._rng = np.random.default_rng(seed)
        self._s: List = []
        self._o: List = []
        self._last_tau = 1.0
        self._last_block = 1.0

    def ingest(self, sample: SampleMessage) -> None:
        self._s.append(canon(sample.secret_tags))
        self._o.append(canon(sample.observation_tags))

    def reset_window(self) -> None:
        self._s = []
        self._o = []

    def estimate(self) -> ChannelEstimate:
        n = len(self._s)
        if n == 0:
            return _result(None, None, None, 0, 0, 0, "INSUFFICIENT_ALPHABET", 0)
        sc, m_s = _factorize(self._s)
        oc, m_o = _factorize(self._o)
        m_so = int(np.unique(sc * m_o + oc).size)
        if m_s < 2 or m_o < 2:
            return _result(None, None, None, n, m_s, m_o, "INSUFFICIENT_ALPHABET", n)

        tau = integrated_autocorr_time(_pmi_series(sc, oc, m_s, m_o))
        eff_n = n / tau
        eff_n_int = int(max(1.0, eff_n))
        self._last_tau, self._last_block = tau, max(1.0, round(tau))

        if eff_n_int < self.tau_gate * m_so:
            # gate on EFFECTIVE n -- the autocorrelation-discounted count, not the nominal n
            return _result(None, None, None, n, m_s, m_o, "UNDERDETERMINED", eff_n_int)

        # point: Miller-Madow corrected at the EFFECTIVE sample size (removes dependence-induced point bias)
        point = _mi_eff(sc, oc, m_s, m_o, eff_n)
        boots = np.empty(self.bootstrap, dtype=np.float64)
        for b in range(self.bootstrap):
            idx = _stationary_bootstrap_idx(n, self._last_block, self._rng)
            boots[b] = _mi_eff(sc[idx], oc[idx], m_s, m_o, eff_n)
        lo = float(np.percentile(boots, 2.5))
        hi = float(np.percentile(boots, 97.5))
        return _result(point, lo, hi, n, m_s, m_o, "ESTIMATED", eff_n_int)

    def stats(self) -> dict:
        n = len(self._s)
        return {
            "n_samples": n,
            "effective_n": int(max(1.0, n / self._last_tau)) if n else 0,
            "autocorr_time": self._last_tau,
            "block_length": self._last_block,
            "alphabet_secret": len(set(self._s)),
            "alphabet_observation": len(set(self._o)),
            "joint_support": len(set(zip(self._s, self._o))),
        }
