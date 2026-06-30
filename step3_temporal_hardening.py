# SPDX-License-Identifier: AGPL-3.0-only
"""step3_temporal_hardening.py — Option 3, the version that is NOT a predetermined null.

Effective-n / temporal correction fixes CI-width UNDER AUTOCORRELATION; it does nothing for the i.i.d.
point-bias that blocks the Smith channel (Phase 1-2). So this tests the one temporal regime we never ran:
min-entropy leak on an AUTOCORRELATED stream, i.i.d.-bootstrap CI vs stationary-block-bootstrap CI
(Politis & Romano 1994 — the method the repo already cites). markov_run gives exact GT = log2(K) and known tau.
This is ORTHOGONAL to the Smith bias failure; it cannot lift that grade. tested != safe.
"""
from __future__ import annotations
import os, sys, math
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (ROOT, os.path.join(ROOT, "tests"), os.path.join(ROOT, "weltwerk", "verify")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from claim_ledger import Claim, audit_ledger
from test_block_bootstrap import markov_run, K, TRUTH      # K=4, TRUTH=log2(K)=GT for the identity channel


def _leak(sc, oc, ms, n):
    vp = np.bincount(sc, minlength=ms).max() / n
    pair = np.bincount(sc * ms + oc, minlength=ms * ms).reshape(ms, ms)
    return max(0.0, math.log2((pair.max(0).sum() / n) / vp))


def _lag1(x):
    x = x.astype(float) - x.mean(); d = float(np.sum(x * x))
    return float(np.sum(x[1:] * x[:-1]) / d) if d > 0 else 0.0


def _stationary_idx(n, L, rng):
    """Politis-Romano stationary bootstrap: geometric-length wrap-around blocks (mean length L)."""
    idx = np.empty(n, np.int64); t = 0
    while t < n:
        start = int(rng.integers(0, n)); ln = min(int(rng.geometric(1.0 / L)), n - t)
        idx[t:t + ln] = (start + np.arange(ln)) % n; t += ln
    return idx


def estimate(secrets, method, bootstrap, rng):
    sc = np.asarray(secrets, np.int64); oc = sc            # identity channel: o = s
    n = sc.size; ms = int(sc.max()) + 1
    point = _leak(sc, oc, ms, n)
    if method == "block":
        rho = _lag1(sc); L = max(2.0, (1 + rho) / (1 - rho)) if rho < 0.98 else n / 10.0
        idxs = (_stationary_idx(n, L, rng) for _ in range(bootstrap))
    else:
        idxs = (rng.integers(0, n, n) for _ in range(bootstrap))
    boots = np.array([_leak(sc[i], oc[i], ms, n) for i in idxs])
    return point, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def run(n=3000, repeats=15, bootstrap=150, seed=0):
    gt = TRUTH
    print(f"Identity channel on markov_run (K={K})  GT min-ent leak = log2(K) = {gt:.3f}b   "
          f"n={n} repeats={repeats} bootstrap={bootstrap}\n")
    rng = np.random.default_rng(seed)
    table = {}
    for p in (0.0, 0.5, 0.9):
        cov = {"iid": 0, "block": 0}; w = {"iid": [], "block": []}
        for t in range(repeats):
            s = markov_run(n, p, seed=1000 + t)
            for m in ("iid", "block"):
                pt, lo, hi = estimate(s, m, bootstrap, rng)
                cov[m] += (lo <= gt <= hi); w[m].append(hi - lo)
        table[p] = (cov["iid"], cov["block"], repeats)
        print(f"p={p:>3}  rho-driven dependence | "
              f"iid-CI coverage={cov['iid']:>2}/{repeats} (mean CIw={np.mean(w['iid']):.3f})   "
              f"block-CI coverage={cov['block']:>2}/{repeats} (mean CIw={np.mean(w['block']):.3f})")
    return table


def grade_from(table) -> Claim:
    # the temporal failure: at high p, does block-bootstrap restore coverage that i.i.d.-bootstrap loses?
    iid0, blk0, r0 = table[0.0]; iid9, blk9, r9 = table[0.9]
    iid_breaks = iid9 < 0.7 * r9                       # i.i.d. CI under-covers under strong dependence
    block_restores = blk9 >= 0.85 * r9                 # block CI restores coverage
    if iid_breaks and block_restores:
        g = "MEASURED"
    elif block_restores or blk9 > iid9:
        g = "UNDERDETERMINED"
    else:
        g = "SPECULATIVE"
    return Claim(
        id="DW3",
        statement="Stationary-block bootstrap restores min-entropy CI coverage under autocorrelation where the i.i.d. bootstrap under-covers.",
        grade=g,
        mechanism="identity channel on markov_run (exact GT=log2 K), i.i.d. vs Politis-Romano stationary bootstrap, coverage across stay-probability p.",
        does_not_show="the Smith i.i.d. POINT-BIAS failure (orthogonal; needs the analytic correction) — temporal-CI != bias; small K=4 alphabet; lag-1 tau proxy.",
        falsifier="if block coverage does not exceed i.i.d. coverage as p rises, temporal correction is not the lever and the failure is purely bias.",
    )


def main():
    table = run()
    c = grade_from(table); a = audit_ledger((c,))
    print("\n=== REGISTERED CLAIM ===")
    print(f"  [{c.grade}] {c.statement}")
    print(f"  does_not_show: {c.does_not_show}")
    print(f"  falsifier:     {c.falsifier}")
    print(f"  ledger honest={a['honest']}  counts={a['counts']}")
    print("\nNote: this is the TEMPORAL/CI failure mode. The Smith deployment blocker is i.i.d. point-bias,")
    print("which this does not address — a green result here does NOT lift the Smith SPECULATIVE grade.")


if __name__ == "__main__":
    main()
