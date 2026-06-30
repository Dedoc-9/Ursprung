# SPDX-License-Identifier: AGPL-3.0-only
"""Validation for the v0.2.1 BlockBootstrapEstimator against a discrete Markov-chain ground truth.

A symmetric K-state Markov chain (stay-probability p) has uniform stationary distribution, so with the identity
channel O=S the true MI is exactly H(S) = log2(K) bits regardless of p — but the *autocorrelation* of the stream
grows with p. That isolates the temporal effect: same truth, tunable dependence. This is the discrete analog of
an AR(1) process; the continuous-AR(1)+KSG validation belongs after v0.2.

The crux test is COVERAGE: on autocorrelated data the v0.1 i.i.d.+nominal-n estimator covers the known MI far
below 95% (false precision), while the block estimator (stationary bootstrap + effective-n Miller-Madow)
restores ~95% coverage. `bootstrap-CI != valid-under-autocorrelation`.

Run: python tests/test_block_bootstrap.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from channel_profiler.block_bootstrap import BlockBootstrapEstimator  # noqa: E402
from channel_profiler.estimator import MillerMadowEstimator  # noqa: E402
from channel_profiler.messages import SampleMessage  # noqa: E402

K = 4
TRUTH = float(np.log2(K))  # = 2.0 bits, identity channel, uniform stationary distribution


def markov_run(n: int, p: float, seed: int) -> np.ndarray:
    """Symmetric K-state chain: stay with prob p, else jump to a uniformly-random DIFFERENT state. Stationary
    distribution uniform; autocorrelation increases with p."""
    rng = np.random.default_rng(seed)
    s = np.empty(n, dtype=np.int64)
    cur = int(rng.integers(0, K))
    for i in range(n):
        s[i] = cur
        if rng.random() >= p:
            cur = (cur + 1 + int(rng.integers(0, K - 1))) % K
    return s


def _feed(est, s: np.ndarray, o: np.ndarray):
    for ss, oo in zip(s, o):
        est.ingest(SampleMessage("t", 0, {"s": int(ss)}, {"o": int(oo)}, 0.0))


def _covered(e, truth: float) -> bool:
    return e.verdict == "ESTIMATED" and e.ci_lower is not None and e.ci_lower <= truth <= e.ci_upper


def test_coverage_contrast():
    """The crux: block bootstrap restores ~95% coverage on autocorrelated data; the i.i.d. estimator under-covers."""
    trials, n, p = 40, 2000, 0.85
    naive_hits = block_hits = 0
    for t in range(trials):
        s = markov_run(n, p, 1000 + t)
        o = s.copy()  # identity channel: I(S;O) = H(S) = TRUTH
        ne = MillerMadowEstimator(bootstrap=200, seed=t)
        _feed(ne, s, o)
        naive_hits += _covered(ne.estimate(), TRUTH)
        be = BlockBootstrapEstimator(bootstrap=200, seed=t)
        _feed(be, s, o)
        block_hits += _covered(be.estimate(), TRUTH)
    naive_cov, block_cov = naive_hits / trials, block_hits / trials
    print(f"  coverage: naive(i.i.d.,nominal-n)={naive_cov:.2f}  block(stationary,eff-n)={block_cov:.2f}  (truth={TRUTH})")
    assert block_cov > naive_cov + 0.2, f"block must clearly out-cover naive ({block_cov} vs {naive_cov})"
    assert block_cov >= 0.80, f"block coverage should approach nominal 0.95, got {block_cov}"
    assert naive_cov <= 0.70, f"naive should visibly under-cover under autocorrelation, got {naive_cov}"


def test_effective_n_detects_dependence():
    """effective_n collapses under autocorrelation and is ~n under i.i.d. sampling."""
    be = BlockBootstrapEstimator(seed=0)
    s = markov_run(4000, 0.9, 7)
    _feed(be, s, s)
    e = be.estimate()
    print(f"  autocorr p=0.9: tau={be.stats()['autocorr_time']:.1f}  eff_n={e.effective_n} of {e.n_samples}")
    assert e.effective_n is not None and e.effective_n < 0.5 * e.n_samples

    be2 = BlockBootstrapEstimator(seed=0)
    s2 = markov_run(4000, 1.0 / K, 7)  # p=1/K -> memoryless (i.i.d.)
    _feed(be2, s2, s2)
    e2 = be2.estimate()
    print(f"  i.i.d.  p=1/K: tau={be2.stats()['autocorr_time']:.1f}  eff_n={e2.effective_n} of {e2.n_samples}")
    assert e2.effective_n > 0.8 * e2.n_samples


def test_gate_uses_effective_n():
    """A strongly-autocorrelated stream: nominal n passes the v0.1 gate, but effective n does not — the block
    estimator correctly refuses (UNDERDETERMINED) where the i.i.d. estimator over-claims ESTIMATED.

    A *deterministic* non-uniform block stream is used (not a random Markov chain): the pointwise-MI series'
    autocorrelation — and hence the estimated tau — is reliable only when the marginal is non-uniform (a
    symmetric identity channel has near-constant pmi, so tau is read off finite-sample noise). Long, unequal
    blocks make tau large and reliably measured. This is itself a documented limit of the pmi-series tau proxy."""
    s = np.array(([0] * 40 + [1] * 30 + [2] * 20 + [3] * 10) * 2)  # n=200, marginal [.4,.3,.2,.1], tau~20
    o = s.copy()
    ne = MillerMadowEstimator(seed=0)
    _feed(ne, s, o)
    be = BlockBootstrapEstimator(seed=0)
    _feed(be, s, o)
    nv, bv = ne.estimate().verdict, be.estimate()
    print(f"  block-structured: naive={nv}  block={bv.verdict}  block_eff_n={bv.effective_n} of {bv.n_samples}")
    assert nv == "ESTIMATED", "nominal-n gate passes this n"
    assert bv.verdict == "UNDERDETERMINED", "effective-n gate must refuse"
    assert bv.effective_n < bv.n_samples


def test_effective_n_field_invariant():
    """effective_n is always present and never exceeds n_samples."""
    be = BlockBootstrapEstimator(seed=1)
    s = markov_run(1500, 0.8, 11)
    _feed(be, s, s)
    e = be.estimate()
    assert e.effective_n is not None and e.effective_n <= e.n_samples


if __name__ == "__main__":
    tests = [
        ("coverage contrast (the crux)", test_coverage_contrast),
        ("effective_n detects dependence", test_effective_n_detects_dependence),
        ("gate uses effective_n", test_gate_uses_effective_n),
        ("effective_n field invariant", test_effective_n_field_invariant),
    ]
    failed = 0
    for name, fn in tests:
        try:
            print(f"[ RUN ] {name}")
            fn()
            print(f"[ OK  ] {name}\n")
        except AssertionError as ex:
            failed += 1
            print(f"[FAIL ] {name}: {ex}\n")
    total = len(tests)
    print(f"{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)
