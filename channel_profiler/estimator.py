# SPDX-License-Identifier: AGPL-3.0-only
"""MillerMadowEstimator — the MI estimator, the part where the thesis lives or dies (spec §4).

It estimates I(secret; observation) in bits over the current window, and never emits a bare point estimate:

* **Per-entropy Miller–Madow bias correction.** `Î = Ĥ_mm(S) + Ĥ_mm(O) − Ĥ_mm(S,O)`, each
  `Ĥ_mm(X) = Ĥ_plugin(X) + (m_X − 1)/(2 n ln2)` over the OBSERVED support `m_X`. Composing the three corrected
  entropies gets the sign right for any channel (the spec's "add (|S|−1)(|O|−1)/(2n ln2)" is the full-support
  special case AND the wrong sign for the positively-biased general MI; this form avoids both). Miller (1955).
* **Bootstrap confidence intervals.** B=500 resamples of the (s,o) pairs, 2.5/97.5 percentiles. Efron &
  Tibshirani (1993). Vectorized via integer-coded `bincount` so coverage studies stay cheap.
* **Sufficiency gate on the JOINT support.** `UNDERDETERMINED` (not a number) when `n < τ·m_so`, τ=5, where
  `m_so` is the observed JOINT support — NOT `|S|·|O|`. For a near-deterministic channel the joint is far
  sparser than the product of marginals; gating on the product would falsely declare everything insufficient.
  The n≫(support) regime is Paninski (2003).
* **Shuffle-null** (`shuffle_null`): a COMPLEMENTARY check kept from `residual_channel` — permute O to break the
  S–O tie; a real signal sits well above the null. It does not replace the CI.

MI is provably ≥ 0; finite-sample correction can dip slightly negative, so the point estimate and CI bounds are
floored at 0. `estimate ≠ capacity`; the class + n + alphabet sizes travel with every number.
"""
from __future__ import annotations

import math
import statistics
from typing import Dict, List, Tuple

import numpy as np

from channel_profiler.messages import ChannelEstimate, SampleMessage

LN2 = math.log(2.0)


def _freeze(v):
    if isinstance(v, (list, tuple)):
        return tuple(_freeze(x) for x in v)
    if isinstance(v, dict):
        return tuple(sorted((k, _freeze(x)) for k, x in v.items()))
    return v


def canon(tags: Dict) -> tuple:
    """Canonicalize a tag dict into a hashable symbol (order-independent, list→tuple)."""
    return tuple(sorted((k, _freeze(v)) for k, v in tags.items()))


def _factorize(seq: List) -> Tuple[np.ndarray, int]:
    d: Dict = {}
    codes = np.empty(len(seq), dtype=np.int64)
    for i, x in enumerate(seq):
        j = d.get(x)
        if j is None:
            j = len(d)
            d[x] = j
        codes[i] = j
    return codes, len(d)


def _H_mm_from_counts(counts: np.ndarray, n: int) -> float:
    c = counts[counts > 0]
    p = c / n
    h = float(-np.sum(p * np.log2(p)))
    m = int(c.size)
    return h + (m - 1) / (2.0 * n * LN2)


def _H_plugin_from_counts(counts: np.ndarray, n: int) -> float:
    c = counts[counts > 0]
    p = c / n
    return float(-np.sum(p * np.log2(p)))


def _mi_coded(s_codes: np.ndarray, o_codes: np.ndarray, m_s: int, m_o: int, corrected: bool) -> float:
    n = s_codes.size
    cs = np.bincount(s_codes, minlength=m_s)
    co = np.bincount(o_codes, minlength=m_o)
    cso = np.bincount(s_codes * m_o + o_codes, minlength=m_s * m_o)
    H = _H_mm_from_counts if corrected else _H_plugin_from_counts
    return H(cs, n) + H(co, n) - H(cso, n)


def mi_miller_madow(secrets: List, observations: List) -> float:
    """Bias-corrected MI (bits) over paired symbol lists. Floored at 0."""
    sc, ms = _factorize(secrets)
    oc, mo = _factorize(observations)
    return max(0.0, _mi_coded(sc, oc, ms, mo, corrected=True))


def mi_plugin(secrets: List, observations: List) -> float:
    """Raw plug-in MI (bits), no correction — for the bias-comparison test. Floored at 0."""
    sc, ms = _factorize(secrets)
    oc, mo = _factorize(observations)
    return max(0.0, _mi_coded(sc, oc, ms, mo, corrected=False))


class MillerMadowEstimator:
    """Implements the `ChannelEstimator` protocol."""

    def __init__(self, bootstrap: int = 500, tau: float = 5.0, seed: int = 0) -> None:
        self.bootstrap = bootstrap
        self.tau = tau
        self._rng = np.random.default_rng(seed)
        self._s: List = []
        self._o: List = []

    # ---- ChannelEstimator protocol ----------------------------------------------------------------
    def ingest(self, sample: SampleMessage) -> None:
        self._s.append(canon(sample.secret_tags))
        self._o.append(canon(sample.observation_tags))

    def reset_window(self) -> None:
        self._s = []
        self._o = []

    def estimate(self) -> ChannelEstimate:
        n = len(self._s)
        if n == 0:
            return ChannelEstimate(None, None, None, "miller_madow", 0, 0, 0, "INSUFFICIENT_ALPHABET")
        sc, m_s = _factorize(self._s)
        oc, m_o = _factorize(self._o)
        m_so = int(np.unique(sc * m_o + oc).size)

        if m_s < 2 or m_o < 2:
            # a constant secret or observation cannot carry a channel
            return ChannelEstimate(None, None, None, "miller_madow", n, m_s, m_o, "INSUFFICIENT_ALPHABET")
        if n < self.tau * m_so:
            # Paninski regime: too few samples relative to the JOINT support being estimated
            return ChannelEstimate(None, None, None, "miller_madow", n, m_s, m_o, "UNDERDETERMINED")

        point = max(0.0, _mi_coded(sc, oc, m_s, m_o, corrected=True))
        boots = np.empty(self.bootstrap, dtype=np.float64)
        for b in range(self.bootstrap):
            r = self._rng.integers(0, n, n)
            boots[b] = max(0.0, _mi_coded(sc[r], oc[r], m_s, m_o, corrected=True))
        lo = float(np.percentile(boots, 2.5))
        hi = float(np.percentile(boots, 97.5))
        return ChannelEstimate(point, lo, hi, "miller_madow", n, m_s, m_o, "ESTIMATED")

    def stats(self) -> dict:
        n = len(self._s)
        return {
            "n_samples": n,
            "alphabet_secret": len(set(self._s)),
            "alphabet_observation": len(set(self._o)),
            "joint_support": len(set(zip(self._s, self._o))),
        }

    # ---- complementary shuffle-null (NOT a replacement for the CI) --------------------------------
    def shuffle_null(self, reps: int = 200) -> dict:
        """Permute O to break the S–O association; a genuine channel's MI sits well above this null mean."""
        n = len(self._s)
        if n == 0:
            return {"observed": 0.0, "null_mean": 0.0, "reps": 0}
        sc, m_s = _factorize(self._s)
        oc, m_o = _factorize(self._o)
        observed = max(0.0, _mi_coded(sc, oc, m_s, m_o, corrected=True))
        nulls = []
        for _ in range(reps):
            perm = self._rng.permutation(n)
            nulls.append(max(0.0, _mi_coded(sc, oc[perm], m_s, m_o, corrected=True)))
        return {"observed": observed, "null_mean": statistics.fmean(nulls), "reps": reps}
