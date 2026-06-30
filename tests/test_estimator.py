# SPDX-License-Identifier: AGPL-3.0-only
"""Validation of the Channel Profiler estimator against the toy scene's ANALYTIC ground truth.

Each test cites the result it checks. Run: `python tests/test_estimator.py` (also pytest-compatible).
"""
from __future__ import annotations

import os
import random
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOY = os.path.join(_ROOT, "experiments", "toy_scene")
for _p in (_ROOT, _TOY):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from analytic_mi import analytic_mi, coarsen, observation_entropy  # noqa: E402
from channel_profiler.estimator import MillerMadowEstimator, mi_miller_madow, mi_plugin  # noqa: E402
from channel_profiler.messages import SampleMessage, SessionConfig  # noqa: E402
from channel_profiler.window_manager import WindowManager  # noqa: E402
from scene import ToyGridScene  # noqa: E402

TRUTH_R2 = analytic_mi(10, 10, (4, 4), 2)  # ≈ 1.9722 bits (I(S;O)=H(O), deterministic coarsening)


def test_mi_recovers_ground_truth():
    """Paninski (2003) / Miller (1955): with n >> joint support, the MM estimate's 95% CI covers analytic MI."""
    sc = ToyGridScene(seed=7, radius=2)
    est = MillerMadowEstimator(bootstrap=500, seed=0)
    for _ in range(5000):
        est.ingest(sc.sample_iid())
    e = est.estimate()
    assert e.verdict == "ESTIMATED", e.verdict
    assert e.ci_lower - 1e-9 <= TRUTH_R2 <= e.ci_upper + 1e-9, (e.ci_lower, TRUTH_R2, e.ci_upper, e.mi_estimate)


def test_ci_coverage():
    """Efron & Tibshirani (1993) bootstrap percentile CIs; under-coverage caveat Hall (1986). Expect ~95%."""
    trials, hits = 100, 0
    for t in range(trials):
        sc = ToyGridScene(seed=1000 + t, radius=2)
        est = MillerMadowEstimator(bootstrap=300, seed=t)
        for _ in range(3000):
            est.ingest(sc.sample_iid())
        e = est.estimate()
        if e.verdict == "ESTIMATED" and e.ci_lower - 1e-9 <= TRUTH_R2 <= e.ci_upper + 1e-9:
            hits += 1
    cov = hits / trials
    print(f"  CI coverage = {cov:.2f} over {trials} trials (nominal 0.95)")
    assert cov >= 0.85, cov


def test_underdetermined_at_low_n():
    """Paninski (2003): below sample sufficiency (n < 5 * joint-support), refuse a number."""
    sc = ToyGridScene(seed=3, radius=2)
    est = MillerMadowEstimator(seed=0)
    for _ in range(20):
        est.ingest(sc.sample_iid())
    e = est.estimate()
    assert e.verdict == "UNDERDETERMINED", (e.verdict, est.stats())


def test_miller_madow_reduces_bias():
    """Miller (1955): the MM correction reduces the systematic (negative) finite-sample BIAS of plug-in MI.

    Bias is a property of the estimator's MEAN, so we compare |E[estimate] - truth| (averaged over seeds),
    which isolates the bias MM removes from the per-trial variance it does not.
    """
    truth = observation_entropy(10, 10, (4, 4), 2)
    seeds, n = 40, 500
    plug_vals, mm_vals = [], []
    for s in range(seeds):
        rng = random.Random(s)
        secrets, obs = [], []
        for _ in range(n):
            pos = (rng.randrange(10), rng.randrange(10))
            secrets.append(pos)
            obs.append(coarsen(pos, (4, 4), 2))
        plug_vals.append(mi_plugin(secrets, obs))
        mm_vals.append(mi_miller_madow(secrets, obs))
    plug_bias = abs(sum(plug_vals) / seeds - truth)
    mm_bias = abs(sum(mm_vals) / seeds - truth)
    print(f"  |bias(plugin)|={plug_bias:.4f}  |bias(mm)|={mm_bias:.4f}  truth={truth:.4f}")
    assert mm_bias < plug_bias, (mm_bias, plug_bias)


def test_window_reset_on_fidelity_change():
    """Architecture Decision #4: a fidelity change is a channel change -> the window clears."""
    cfg = SessionConfig(session_id="t", budget_bits_per_step=2.0, window_size=1000)
    wm = WindowManager(cfg)

    def msg(fid: float) -> SampleMessage:
        return SampleMessage("t", 0, {"npc_pos": (0, 0)}, {"view": ("FAR",)}, fid)

    for _ in range(5):
        wm.push(msg(2.0))
    assert len(wm) == 5 and not wm.reset_signal
    triggered = wm.push(msg(3.0))  # fidelity changed
    assert wm.reset_signal and len(wm) == 1 and not triggered


if __name__ == "__main__":
    tests = [
        test_window_reset_on_fidelity_change,
        test_underdetermined_at_low_n,
        test_miller_madow_reduces_bias,
        test_mi_recovers_ground_truth,
        test_ci_coverage,
    ]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} checks passed.  (analytic I(S;O)@r=2 = {TRUTH_R2:.4f} bits)")
