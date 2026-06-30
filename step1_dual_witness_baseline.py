# SPDX-License-Identifier: AGPL-3.0-only
"""step1_dual_witness_baseline.py — falsifier-first QIF baseline (ground truth BEFORE estimators).

Net-new = the two things the repo does NOT already ship: an EXACT (by-enumeration) min-entropy
ground truth and a plug-in min-entropy estimator to benchmark against it. Everything else is imported.
The grade is MEASURED only if measured coverage earns it; nothing is asserted. estimate != capacity.
"""
from __future__ import annotations
import os, sys, math
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "tests"), os.path.join(ROOT, "weltwerk", "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from channel_profiler.estimator import MillerMadowEstimator             # Witness A (Shannon MI), shipped+validated
from channel_profiler.block_bootstrap import BlockBootstrapEstimator    # Witness A under dependence (anchor)
from channel_profiler.messages import SampleMessage, ChannelEstimate    # reuse the shipped result dataclass
from claim_ledger import Claim, audit_ledger                            # honesty-graded result, not a scalar
from test_block_bootstrap import markov_run, _covered, K, TRUTH         # the validated autocorrelation harness


def shannon_mi_exact(joint: np.ndarray) -> float:
    """I(S;O) = H(S)+H(O)-H(S,O), exact over the joint. bits."""
    def H(p):
        p = p[p > 0]
        return float(-np.sum(p * np.log2(p)))
    j = joint[joint > 0]
    return H(joint.sum(1)) + H(joint.sum(0)) - float(-np.sum(j * np.log2(j)))


def compute_min_entropy_ground_truth(joint: np.ndarray):
    """V_prior = max_s p(s);  V_post = Σ_o max_s p(s,o)  (EXPECTATION over o, not max_o);
    leak = log2(V_post / V_prior) >= 0  (the sign the original scaffold inverted)."""
    v_prior = float(joint.sum(1).max())
    v_post = float(joint.max(0).sum())          # column maxima summed = Σ_o max_s p(s,o)
    return v_prior, v_post, math.log2(v_post / v_prior)


def smith_counterexample_channel(k: int = 100):
    """Disjoint obs: masks in [0,n), exact leaks in [n,2n). P1 hides most, reveals the divisible-by-8
    secrets uniquely (low Shannon, high one-guess); P2 is a coarse block partition (no hidden danger)."""
    n = 8 * k
    def joint_for(dangerous: bool) -> np.ndarray:
        J = np.zeros((n, 2 * n))
        for s in range(n):
            if dangerous and s % 8 == 0:
                J[s, n + s] = 1.0 / n           # unique exact leak in [n,2n)
            elif dangerous:
                J[s, 0] = 1.0 / n               # single mask: hides the rest, in [0,n)
            else:
                J[s, s // 8] = 1.0 / n          # safe: coarse block id, in [0,n)
        return J
    return {"P1_dangerous": joint_for(True), "P2_safe": joint_for(False)}, n


def sample_channel(joint: np.ndarray, n_draw: int, rng) -> list:
    obs = joint.argmax(1)                       # deterministic channel: one observation per secret
    return [SampleMessage("t", 0, {"s": int(s)}, {"o": int(obs[s])}, 0.0)
            for s in rng.integers(0, joint.shape[0], n_draw)]


class MinEntropyPluginEstimator:
    """Plug-in min-entropy leak with bootstrap CIs. Plug-in path ONLY — bias correction is Phase 2."""
    def __init__(self, bootstrap: int = 200, tau: float = 5.0, seed: int = 0):
        self.bootstrap, self.tau, self._rng = bootstrap, tau, np.random.default_rng(seed)
        self._s, self._o = [], []

    def ingest(self, m: SampleMessage):
        self._s.append(m.secret_tags["s"]); self._o.append(m.observation_tags["o"])

    def estimate(self) -> ChannelEstimate:
        sa, oa = np.array(self._s), np.array(self._o)
        n = sa.size
        _, sc = np.unique(sa, return_inverse=True); _, oc = np.unique(oa, return_inverse=True)
        ms, mo = int(sc.max()) + 1, int(oc.max()) + 1
        m_so = np.unique(sc * mo + oc).size
        if n < self.tau * m_so:
            return ChannelEstimate(None, None, None, "min_entropy_plugin", n, ms, mo, "UNDERDETERMINED")
        def leak(idx):
            v_prior = np.bincount(sc[idx], minlength=ms).max() / n
            pair = np.bincount(sc[idx] * mo + oc[idx], minlength=ms * mo).reshape(ms, mo)
            return max(0.0, math.log2((pair.max(0).sum() / n) / v_prior))
        pt = leak(np.arange(n))
        boots = np.array([leak(self._rng.integers(0, n, n)) for _ in range(self.bootstrap)])
        return ChannelEstimate(pt, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)),
                               "min_entropy_plugin", n, ms, mo, "ESTIMATED")


def dual_witness_firewall_test(k=100, n_draw=6000, repeats=12, seed=0):
    channels, n = smith_counterexample_channel(k)
    rng = np.random.default_rng(seed)
    print(f"Smith counterexample  k={k}  |S|={n}  obs in [0,{2*n})  n_draw={n_draw}  repeats={repeats}\n")
    rows = []
    for name, J in channels.items():
        gt_sh = shannon_mi_exact(J)
        _, _, gt_me = compute_min_entropy_ground_truth(J)
        cov_a = cov_b = 0; A = B = None
        for t in range(repeats):
            smp = sample_channel(J, n_draw, rng)
            ea = MillerMadowEstimator(bootstrap=200, seed=t); [ea.ingest(m) for m in smp]; A = ea.estimate()
            eb = MinEntropyPluginEstimator(bootstrap=200, seed=t); [eb.ingest(m) for m in smp]; B = eb.estimate()
            cov_a += _covered(A, gt_sh); cov_b += _covered(B, gt_me)
        wa = (A.ci_upper - A.ci_lower) if A.ci_lower is not None else float("nan")
        wb = (B.ci_upper - B.ci_lower) if B.ci_lower is not None else float("nan")
        be = B.mi_estimate if B.mi_estimate is not None else float("nan")
        print(f"[{name}]  Shannon GT={gt_sh:.3f}b   min-entropy GT={gt_me:.3f}b   (gap={gt_me-gt_sh:+.3f}b)")
        print(f"   Witness A shannon_mi : est={A.mi_estimate:.3f}  CIw={wa:.3f}  coverage={cov_a}/{repeats}  [{A.verdict}]")
        print(f"   Witness B min_entropy: est={be:.3f}  CIw={wb:.3f}  coverage={cov_b}/{repeats}  [{B.verdict}]")
        rows.append((cov_a, cov_b, repeats))
    return rows


def grade_from_coverage(rows) -> Claim:
    a_ok = all(ca >= 0.95 * r for ca, _, r in rows)
    b_ok = all(cb >= 0.95 * r for _, cb, r in rows)
    g = "MEASURED" if (a_ok and b_ok) else ("UNDERDETERMINED" if a_ok and any(cb for _, cb, _ in rows) else "SPECULATIVE")
    return Claim(
        id="DW1",
        statement="Dual-witness (Shannon MI + plug-in min-entropy) recovers the Smith Shannon<>min-entropy gap from finite i.i.d. samples.",
        grade=g,
        mechanism="Miller-Madow MI vs plug-in min-entropy leak, bootstrap CIs, coverage vs exact-enumeration ground truth on the Smith channel.",
        does_not_show="i.i.d. only (no autocorrelation); plug-in min-entropy is uncorrected so its CI may undercover; says nothing about real systems.",
        falsifier="raising n_draw lifts min-entropy coverage toward 0.95 (bias was the cause), or it stays low (bias correction in Phase 2 is mandatory).",
    )


def main():
    rows = dual_witness_firewall_test()
    s = markov_run(4000, 0.9, 7); be = BlockBootstrapEstimator(seed=0)
    for x in s:
        be.ingest(SampleMessage("t", 0, {"s": int(x)}, {"o": int(x)}, 0.0))
    anc = be.estimate()
    print(f"\n[anchor] markov_run(p=0.9, K={K}) identity channel: GT={TRUTH:.3f}b  est={anc.mi_estimate:.3f}  "
          f"covered={_covered(anc, TRUTH)}  [{anc.verdict}]   (validated Witness-A harness, under dependence)")
    c = grade_from_coverage(rows)
    audit = audit_ledger((c,))
    print("\n=== REGISTERED CLAIM ===")
    print(f"  [{c.grade}] {c.statement}")
    print(f"  does_not_show: {c.does_not_show}")
    print(f"  falsifier:     {c.falsifier}")
    print(f"  ledger honest={audit['honest']}  counts={audit['counts']}")


if __name__ == "__main__":
    main()
