# SPDX-License-Identifier: AGPL-3.0-only
"""step4_ck_interval.py — the REAL Chothia-Kawamoto deliverable (Theorem 3), not the nonexistent bias term.

The 2014 C-K paper leaves point-bias correction as an OPEN problem ("currently investigating..."). What it
proves is a guaranteed >=95% confidence interval via Hoeffding/Bernstein bounds (Sec 4.3, Theorem 3, estimated
prior). So coverage is guaranteed by construction; the only honest question is WIDTH. We measure width per
channel: a guaranteed interval is useless if it is vacuous. tested != safe; bound != usable.

eps allocation here is a conservative union bound over the paper's eps1/eps2/eps3 (the paper does a joint
numeric solve); that only makes our intervals WIDER, never narrower, so a 'usable' verdict stays honest.
"""
from __future__ import annotations
import os, sys, math
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "tests"), os.path.join(ROOT, "weltwerk", "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from claim_ledger import Claim, audit_ledger
from step1_dual_witness_baseline import smith_counterexample_channel, sample_channel, compute_min_entropy_ground_truth


def ck_interval(secrets, obs, conf=0.95):
    """C-K Theorem 3 interval for min-entropy leakage (estimated prior). Returns (point, lo, hi)."""
    s = np.asarray(secrets); o = np.asarray(obs); L = s.size
    _, sc = np.unique(s, return_inverse=True); ms = int(sc.max()) + 1
    V_prior = np.bincount(sc, minlength=ms).max() / L
    _, oc = np.unique(o, return_inverse=True); mo = int(oc.max()) + 1
    Ly = np.bincount(oc, minlength=mo); PY = Ly / L
    pair = np.bincount(sc * mo + oc, minlength=ms * mo).reshape(ms, mo)
    maxcond = pair.max(0) / np.maximum(Ly, 1)                   # max_x P(x|y)
    m = int((Ly > 0).sum()); minLy = int(Ly[Ly > 0].min()); a = 1.0 - conf
    eps3 = math.sqrt(2 * math.log(6.0 / a) / L)                 # prior max (Prop 1, global L)
    eps1 = math.sqrt(2 * math.log(6.0 * m / a) / minLy)         # conditional max (Prop 1, per-obs Ly)
    eps2 = math.sqrt(math.log(6.0 * m / a) / (2 * L))           # P_Y (Prop 2, small-eps Bernstein)
    post_hat = float(np.sum(maxcond * PY))
    post_up = min(1.0, float(np.sum((maxcond + eps1) * (PY + eps2))))    # V(X|Y) <= 1 always
    post_lw = float(np.sum(np.maximum(0.0, maxcond - eps1) * np.maximum(0.0, PY - eps2)))  # product of lower bounds
    point = max(0.0, -math.log2(V_prior) + math.log2(post_hat))
    hi = min(math.log2(ms), -math.log2(max(1e-12, V_prior - eps3)) + math.log2(post_up))
    lo = max(0.0, -math.log2(V_prior + eps3) + math.log2(post_lw)) if post_lw > 0 else 0.0
    return point, lo, hi


def _arrays(J, n, rng):
    smp = sample_channel(J, n, rng)
    return [m.secret_tags["s"] for m in smp], [m.observation_tags["o"] for m in smp]


def coverage_and_width(n=6000, repeats=30, seed=0):
    channels, _ = smith_counterexample_channel(k=100)
    rng = np.random.default_rng(seed); out = {}
    for name, J in channels.items():
        _, _, gt = compute_min_entropy_ground_truth(J)
        cov = 0; widths = []
        for t in range(repeats):
            s, o = _arrays(J, n, rng)
            _, lo, hi = ck_interval(s, o)
            cov += (lo <= gt <= hi); widths.append(hi - lo)
        mw = float(np.median(widths)); usable = mw < 2.0
        out[name] = (gt, cov, repeats, mw, usable)
        print(f"[{name}]  GT={gt:.3f}b  coverage={cov}/{repeats}  median CI width={mw:.3f}b  "
              f"{'USABLE' if usable else 'VACUOUS'} (range 0..{math.log2(800):.1f}b)")
    return out


def width_sweep(seed=0):
    channels, _ = smith_counterexample_channel(k=100)
    J = channels["P1_dangerous"]; _, _, gt = compute_min_entropy_ground_truth(J); rng = np.random.default_rng(seed)
    print(f"\nWidth sweep on P1_dangerous (GT={gt:.3f}b): does the guaranteed interval ever get tight?")
    for n in (6000, 30000, 100000, 300000):
        s, o = _arrays(J, n, rng)
        _, lo, hi = ck_interval(s, o)
        # samples landing on the rarest (leak) observation drive the bound
        import collections
        per_obs_min = min(collections.Counter(o).values())
        print(f"   n={n:>7}: CI=[{lo:.2f},{hi:.2f}]  width={hi-lo:.2f}b  min samples/observation={per_obs_min}")


def grade_from(out) -> Claim:
    all_cover = all(c >= 0.95 * r for _, c, r, _, _ in out.values())
    any_usable = any(u for *_x, u in out.values())
    all_usable = all(u for *_x, u in out.values())
    g = "MEASURED" if (all_cover and all_usable) else ("UNDERDETERMINED" if all_cover and any_usable else "SPECULATIVE")
    return Claim(
        id="DW4",
        statement="C-K Theorem 3 gives guaranteed-coverage min-entropy bounds, but their WIDTH is usable only when every critical observation is well-sampled.",
        grade=g,
        mechanism="Hoeffding/Bernstein concentration interval (estimated prior), coverage AND median width vs exact ground truth on Smith channels.",
        does_not_show="point-estimate de-biasing (C-K leave it open); tight gating on rare-leak channels; non-i.i.d. streams.",
        falsifier="the width sweep: if the dangerous-channel interval never tightens as n grows because min-samples-per-observation stays tiny, real-time min-entropy certification of rare leaks is infeasible, not merely unrefined.",
    )


def main():
    print("Phase 3 / step4 — Chothia-Kawamoto Theorem 3 interval (guaranteed coverage; measuring WIDTH)\n")
    out = coverage_and_width()
    width_sweep()
    c = grade_from(out); au = audit_ledger((c,))
    print("\n=== REGISTERED CLAIM ===")
    print(f"  [{c.grade}] {c.statement}")
    print(f"  does_not_show: {c.does_not_show}")
    print(f"  falsifier:     {c.falsifier}")
    print(f"  ledger honest={au['honest']}  counts={au['counts']}")


if __name__ == "__main__":
    main()
