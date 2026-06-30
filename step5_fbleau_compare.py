# SPDX-License-Identifier: AGPL-3.0-only
"""step5_fbleau_compare.py — does F-BLEAU-style nearest-neighbor estimation beat binned plug-in?

F-BLEAU (Cherubin et al., S&P 2019) converges faster ONLY when the OBSERVATION space has a metric
('nearby outputs -> same secret'). The step1/step4 channels are symbolic (arbitrary labels) -> NN is
meaningless there. So we test on a channel that HAS geometry: observation = secret + Gaussian noise.
Then we DESTROY the metric (random relabel, same information) and show the NN advantage vanishes — isolating
that the gain is geometry, not magic. Exact GT by numerical integration. Standalone (numpy only).
verdict: grade emerges from bias vs ground truth. estimate != capacity; structure != magic.
"""
from __future__ import annotations
import math
import numpy as np

SQRT2PI = math.sqrt(2 * math.pi)


def gt_leak(K: int, sigma: float) -> float:
    """Exact min-entropy leakage of the Gaussian channel (uniform prior), by fine numerical integration.
    leak = log2( V(S|O) / V(S) ),  V(S)=1/K,  V(S|O)=∫ max_s (1/K)·N(o; s,sigma) do."""
    grid = np.linspace(-6 * sigma, (K - 1) + 6 * sigma, 40000)
    dx = grid[1] - grid[0]
    dens = np.stack([np.exp(-0.5 * ((grid - s) / sigma) ** 2) / (sigma * SQRT2PI) for s in range(K)])
    v_post = (1.0 / K) * float(np.max(dens, axis=0).sum()) * dx
    return math.log2(v_post / (1.0 / K))


def sample(K: int, sigma: float, n: int, rng) -> tuple:
    s = rng.integers(0, K, n)
    o = s + rng.normal(0.0, sigma, n)        # continuous observation WITH metric structure
    return s, o


def plugin_leak(s: np.ndarray, o: np.ndarray, bins: int = 40) -> float:
    edges = np.linspace(o.min(), o.max(), bins + 1)
    ob = np.clip(np.digitize(o, edges) - 1, 0, bins - 1)
    n = s.size; K = int(s.max()) + 1
    v_prior = np.bincount(s, minlength=K).max() / n
    pair = np.bincount(s * bins + ob, minlength=K * bins).reshape(K, bins)
    return max(0.0, math.log2((pair.max(0).sum() / n) / v_prior))


def nn_leak(s: np.ndarray, o: np.ndarray, k=None) -> float:
    """1-D leave-one-out kNN: classifier accuracy estimates V(S|O)=P(correct guess) (Bayes vulnerability).
    k=None -> adaptive k≈sqrt(n) (capped), the consistency-respecting choice (k->inf, k/n->0)."""
    K = int(s.max()) + 1; n = s.size
    if k is None:
        k = max(5, min(60, int(round(n ** 0.5))))
    order = np.argsort(o, kind="mergesort"); so = s[order]
    correct = 0
    for i in range(n):
        a, b = max(0, i - k), min(n, i + k + 1)
        win = np.concatenate((so[a:i], so[i + 1:b]))     # ~2k nearest in the sorted order
        if win.size and np.bincount(win, minlength=K).argmax() == so[i]:
            correct += 1
    v_prior = np.bincount(s, minlength=K).max() / n
    return max(0.0, math.log2((correct / n) / v_prior))


def metric_destroyed(o: np.ndarray, rng, bins: int = 40) -> np.ndarray:
    """Same channel information (fine bins preserved) but the ORDER/metric scrambled: NN can't exploit it."""
    edges = np.linspace(o.min(), o.max(), bins + 1)
    ob = np.clip(np.digitize(o, edges) - 1, 0, bins - 1)
    relabel = rng.permutation(bins) * 1000.0          # arbitrary, spread-out, order-meaningless labels
    return relabel[ob].astype(float)


def run(K=8, sigma=0.6, repeats=6, seed=0):
    gt = gt_leak(K, sigma)
    print(f"Gaussian channel  K={K}  sigma={sigma}  GT min-ent leak = {gt:.3f} b  (max log2 K = {math.log2(K):.3f})\n")
    print(f"{'n':>7}  {'plugin bias±sd':>20}  {'NN bias±sd':>20}  {'NN-scrambled bias±sd':>22}")
    rng = np.random.default_rng(seed)
    summary = {}
    for n in (300, 1000, 3000, 10000):
        pg, nn, sc = [], [], []
        for _ in range(repeats):
            s, o = sample(K, sigma, n, rng)
            pg.append(plugin_leak(s, o) - gt)
            nn.append(nn_leak(s, o) - gt)
            sc.append(nn_leak(s, metric_destroyed(o, rng)) - gt)
        f = lambda a: (float(np.mean(a)), float(np.std(a)))
        (pb, ps), (nb, ns), (cb, cs) = f(pg), f(nn), f(sc)
        summary[n] = (pb, nb, cb)
        print(f"{n:>7}  {pb:>+9.3f} ± {ps:5.3f}   {nb:>+9.3f} ± {ns:5.3f}   {cb:>+11.3f} ± {cs:5.3f}")
    return gt, summary


def verdict(summary):
    pb, nb, cb = summary[10000]                      # largest-n bias for each estimator
    nn_beats_plugin = abs(nb) < abs(pb) - 0.05
    metric_matters = abs(cb) > abs(nb) + 0.10        # scrambling the metric hurts NN
    if nn_beats_plugin and metric_matters:
        g = "MEASURED"
    elif nn_beats_plugin or metric_matters:
        g = "UNDERDETERMINED"
    else:
        g = "SPECULATIVE"
    print("\n=== GRADED VERDICT (Claim-shaped) ===")
    print(f"  [{g}] NN min-entropy estimation beats binned plug-in IFF the observation space carries a usable metric.")
    print(f"  mechanism : 1-D kNN accuracy estimates Bayes vulnerability on a Gaussian channel; metric destroyed = control.")
    print(f"  does_not_show: helps the step1/step4 SYMBOLIC channels (no metric) — there the rare-leak wall is estimator-independent.")
    print(f"  falsifier : if NN bias is not below plug-in at large n, or scrambling does NOT hurt NN, the gain is not geometric.")
    print(f"  numbers   : @n=10k  plugin_bias={pb:+.3f}  NN_bias={nb:+.3f}  NN_scrambled_bias={cb:+.3f}")


def main():
    for K, sigma in ((8, 0.6), (64, 0.6)):     # small/easy-binning  vs  large output space (F-BLEAU regime)
        print("=" * 78)
        _, summary = run(K=K, sigma=sigma)
        verdict(summary)
        print()


if __name__ == "__main__":
    main()
