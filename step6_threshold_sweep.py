# SPDX-License-Identifier: AGPL-3.0-only
"""step6_threshold_sweep.py — where does the NN (F-BLEAU-style) min-entropy advantage activate?

Sweeps output-alphabet size K on the Gaussian channel (observation = secret + noise) and measures how much
of the binned plug-in's bias the nearest-neighbor estimator removes. Result is monotone: ~0% at K=8, crosses
30% near K~=32, ~69% at K=128 — because plug-in bias explodes with K (fixed bins can't cover the alphabet)
while NN's grows slowly (it exploits the output metric). A metric-scramble control confirms the gain is
geometric at every K. Standalone (numpy + matplotlib). Saves nn_threshold_sweep.png next to this file.

HONEST BOUNDS: the crossing K is RELATIVE to (n, sigma, plug-in bin count) — not a universal constant; NN is a
better estimator, NOT an unbiased certifier (residual bias remains); 1-D continuous metric only. estimate != capacity.
"""
from __future__ import annotations
import math, os
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

SQRT2PI = math.sqrt(2 * math.pi)


def gt_leak(K, sigma):
    g = np.linspace(-6 * sigma, (K - 1) + 6 * sigma, 40000); dx = g[1] - g[0]
    d = np.stack([np.exp(-0.5 * ((g - s) / sigma) ** 2) / (sigma * SQRT2PI) for s in range(K)])
    return math.log2(((1.0 / K) * float(np.max(d, 0).sum()) * dx) / (1.0 / K))


def sample(K, sigma, n, rng):
    s = rng.integers(0, K, n); return s, s + rng.normal(0, sigma, n)


def plugin_leak(s, o, bins=40):
    e = np.linspace(o.min(), o.max(), bins + 1); ob = np.clip(np.digitize(o, e) - 1, 0, bins - 1)
    n = s.size; K = int(s.max()) + 1; vp = np.bincount(s, minlength=K).max() / n
    pair = np.bincount(s * bins + ob, minlength=K * bins).reshape(K, bins)
    return max(0.0, math.log2((pair.max(0).sum() / n) / vp))


def nn_leak(s, o, k=None):
    K = int(s.max()) + 1; n = s.size
    if k is None: k = max(5, min(60, int(round(n ** 0.5))))
    so = s[np.argsort(o, kind="mergesort")]; oh = np.eye(K)[so]
    pref = np.vstack([np.zeros(K), np.cumsum(oh, 0)]); i = np.arange(n)
    win = pref[np.minimum(n, i + k + 1)] - pref[np.maximum(0, i - k)] - oh
    vp = np.bincount(s, minlength=K).max() / n
    return max(0.0, math.log2(((win.argmax(1) == so).mean()) / vp))


def scramble(o, rng, bins=40):
    e = np.linspace(o.min(), o.max(), bins + 1); ob = np.clip(np.digitize(o, e) - 1, 0, bins - 1)
    return (rng.permutation(bins) * 1000.0)[ob].astype(float)


def main(Ks=(8, 16, 32, 64, 128), n=10000, reps=8, sigma=0.6, seed=0):
    rng = np.random.default_rng(seed); rm, rs = [], []
    print("%4s %8s %9s %9s %11s %16s" % ("K", "GT", "|plugin|", "|NN|", "|NN-scram|", "NN_bias_redux"))
    for K in Ks:
        gt = gt_leak(K, sigma); reds, P, N, C = [], [], [], []
        for _ in range(reps):
            s, o = sample(K, sigma, n, rng)
            pb = abs(plugin_leak(s, o) - gt); nb = abs(nn_leak(s, o) - gt); cb = abs(nn_leak(s, scramble(o, rng)) - gt)
            reds.append(1 - nb / pb if pb > 0 else 0.0); P.append(pb); N.append(nb); C.append(cb)
        m, sd = float(np.mean(reds)), float(np.std(reds)); rm.append(m * 100); rs.append(sd * 100)
        print("%4d %8.3f %9.3f %9.3f %11.3f %10.1f%% +-%.0f%%" % (K, gt, np.mean(P), np.mean(N), np.mean(C), m * 100, sd * 100))
    plt.figure(figsize=(7, 4.5))
    plt.errorbar(Ks, rm, yerr=rs, marker="o", capsize=4, lw=2, label="NN bias reduction vs plug-in")
    plt.axhline(30, ls="--", color="gray", label="30% threshold"); plt.axhline(0, ls=":", color="k")
    plt.xscale("log", base=2); plt.xticks(Ks, [str(k) for k in Ks])
    plt.xlabel("output alphabet size K"); plt.ylabel("plug-in bias removed by NN (%)")
    plt.title("Min-entropy: NN advantage activates with output-space size\n(n=%dk, sigma=%.1f, adaptive k)" % (n // 1000, sigma))
    plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nn_threshold_sweep.png")
    plt.savefig(out, dpi=110); print("saved:", out)


if __name__ == "__main__":
    main()
