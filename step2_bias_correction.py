# SPDX-License-Identifier: AGPL-3.0-only
"""step2_bias_correction.py — Phase 2: does a PRINCIPLED bias correction move Witness B's coverage?

The measured Phase-1 failure: plug-in min-entropy leak is biased LOW (V_prior = max_s p_hat(s) is biased
HIGH over many near-equal cells), so a firewall would UNDER-report danger. Fix attempted here = bootstrap
bias correction + reverse-percentile (basic) CI (Efron & Tibshirani 1993 — already cited in the MM estimator),
NOT a multiplicative fudge (that cancels in the log-ratio) and NOT CI-widening to a threshold (metric-gaming).
Grade emerges from measured coverage. estimate != capacity; tested != safe.
"""
from __future__ import annotations
import os, sys, math
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "tests"), os.path.join(ROOT, "weltwerk", "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from channel_profiler.messages import ChannelEstimate                       # reuse shipped dataclass
from claim_ledger import Claim, audit_ledger                                # honest grading
from step1_dual_witness_baseline import (smith_counterexample_channel, sample_channel,
                                          shannon_mi_exact, compute_min_entropy_ground_truth,
                                          MinEntropyPluginEstimator, _covered)


class MinEntropyCorrectedEstimator(MinEntropyPluginEstimator):
    """Witness B v2 = bootstrap-bias-corrected plug-in min-entropy leak + reverse-percentile CI."""
    def estimate(self) -> ChannelEstimate:
        sa, oa = np.array(self._s), np.array(self._o); n = sa.size
        _, sc = np.unique(sa, return_inverse=True); _, oc = np.unique(oa, return_inverse=True)
        ms, mo = int(sc.max()) + 1, int(oc.max()) + 1
        m_so = np.unique(sc * mo + oc).size
        if n < self.tau * m_so:
            return ChannelEstimate(None, None, None, "min_entropy_bc", n, ms, mo, "UNDERDETERMINED")
        def leak(idx):
            vp = np.bincount(sc[idx], minlength=ms).max() / n
            pair = np.bincount(sc[idx] * mo + oc[idx], minlength=ms * mo).reshape(ms, mo)
            return max(0.0, math.log2((pair.max(0).sum() / n) / vp))
        point = leak(np.arange(n))
        boots = np.array([leak(self._rng.integers(0, n, n)) for _ in range(self.bootstrap)])
        point_bc = max(0.0, 2 * point - boots.mean())                       # Efron bias correction
        lo = max(0.0, 2 * point - np.percentile(boots, 97.5))              # reverse-percentile (basic) CI
        hi = 2 * point - np.percentile(boots, 2.5)
        return ChannelEstimate(point_bc, lo, hi, "min_entropy_bc", n, ms, mo, "ESTIMATED")


def coverage_run(n_draw=6000, repeats=10, seed=0):
    channels, _ = smith_counterexample_channel(k=100)
    rng = np.random.default_rng(seed)
    out = {}
    for name, J in channels.items():
        _, _, gt = compute_min_entropy_ground_truth(J)
        cov_pl = cov_bc = 0; e_pl = e_bc = None
        for t in range(repeats):
            smp = sample_channel(J, n_draw, rng)
            ep = MinEntropyPluginEstimator(bootstrap=150, seed=t); [ep.ingest(m) for m in smp]; e_pl = ep.estimate()
            ec = MinEntropyCorrectedEstimator(bootstrap=150, seed=t); [ec.ingest(m) for m in smp]; e_bc = ec.estimate()
            cov_pl += _covered(e_pl, gt); cov_bc += _covered(e_bc, gt)
        out[name] = (gt, cov_pl, cov_bc, e_pl.mi_estimate, e_bc.mi_estimate, repeats)
        print(f"[{name}]  min-ent GT={gt:.3f}b")
        print(f"   plug-in   : est={e_pl.mi_estimate:.3f}  coverage={cov_pl}/{repeats}")
        print(f"   corrected : est={e_bc.mi_estimate:.3f}  coverage={cov_bc}/{repeats}  (CI=[{e_bc.ci_lower:.2f},{e_bc.ci_upper:.2f}])")
    return out


def falsifier_sweep(seed=0):
    """Vary n on the dangerous channel: does the bias shrink with n, and does correction help?"""
    channels, _ = smith_counterexample_channel(k=100)
    J = channels["P1_dangerous"]; _, _, gt = compute_min_entropy_ground_truth(J)
    rng = np.random.default_rng(seed)
    print(f"\nFalsifier sweep on P1_dangerous (min-ent GT={gt:.3f}b): bias = est - GT")
    for n in (1000, 3000, 10000, 30000):
        smp = sample_channel(J, n, rng)
        ep = MinEntropyPluginEstimator(bootstrap=120, seed=1); [ep.ingest(m) for m in smp]; ap = ep.estimate()
        ec = MinEntropyCorrectedEstimator(bootstrap=120, seed=1); [ec.ingest(m) for m in smp]; ac = ec.estimate()
        bp = (ap.mi_estimate - gt) if ap.mi_estimate is not None else float("nan")
        bc = (ac.mi_estimate - gt) if ac.mi_estimate is not None else float("nan")
        print(f"   n={n:>6}: plug-in bias={bp:+.3f}  corrected bias={bc:+.3f}  [{ap.verdict}/{ac.verdict}]")


def grade_from(out) -> Claim:
    bc_ok = all(cbc >= 0.85 * r for _, _, cbc, _, _, r in out.values())
    bc_any = any(cbc > 0 for _, _, cbc, _, _, _ in out.values())
    improved = any(out[n][2] > out[n][1] for n in out)
    g = "UNDERDETERMINED" if bc_ok else ("SPECULATIVE" if bc_any or improved else "NOT_MEASURED")
    return Claim(
        id="DW2",
        statement="Bootstrap bias correction lifts plug-in min-entropy coverage toward usable on the Smith channel.",
        grade=g,
        mechanism="reverse-percentile bootstrap bias correction of plug-in min-entropy leak; coverage vs exact ground truth, i.i.d.",
        does_not_show="autocorrelated streams; adversarial (non-empirical) priors; that correction reaches 0.95 — only what coverage shows.",
        falsifier="the n-sweep: if plug-in bias does not shrink with n, the error is systematic; if corrected coverage stays <0.85, bootstrap correction is insufficient and an analytic (Chothia-Kawamoto) term is required.",
    )


def main():
    print("Phase 2 — bias-corrected Witness B (bootstrap bias correction + reverse-percentile CI)\n")
    out = coverage_run()
    falsifier_sweep()
    c = grade_from(out)
    audit = audit_ledger((c,))
    print("\n=== REGISTERED CLAIM ===")
    print(f"  [{c.grade}] {c.statement}")
    print(f"  falsifier: {c.falsifier}")
    print(f"  ledger honest={audit['honest']}  counts={audit['counts']}")


if __name__ == "__main__":
    main()
