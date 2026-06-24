# SPDX-License-Identifier: AGPL-3.0-only
"""
amplify_bench.py — the verdict: does the sparsity that powered every cheap result survive amplifying
dynamics, or is it an artifact of dissipative toy physics?

Sweeps the CML gain r from stable to chaotic and reports sparsity = peak_actual / N. The whole arc's
economic thesis (divergence-aware allocation / replication is cheap) rides on sparsity ≪ 1. This bench
finds where — and whether — it dies.

  sparsity ≪ 1 across all r  → sparsity is STRUCTURAL: the win survives even amplification. (Strong.)
  sparsity → 1 as r → chaos  → sparsity is a property of DISSIPATIVE dynamics: the economic thesis FAILS
                                in amplifying regimes (markets, near-critical gameplay). Correctness is
                                untouched. This is the honest boundary on the whole vision.
"""
from __future__ import annotations

from amplify import measure

N, EPS, C, DELTA, TAU, H = 200, 0.25, 100, 1e-3, 1e-6, 60
RS = (2.6, 2.9, 3.2, 3.45, 3.57, 3.7, 3.83, 4.0)


def main():
    print("amplify_bench — is sparse divergence structural, or just dissipative toy physics?")
    print(f"  CML ring N={N} eps={EPS} perturb δ={DELTA}@{C} tol τ={TAU} horizon={H}\n")
    print(f"  {'gain r':>7} {'regime':>12} {'peakActual':>11} {'sparsity':>9} {'within_cone':>12}")
    print("  " + "-" * 56)
    rows = []
    for r in RS:
        m = measure(N, r, EPS, C, DELTA, TAU, H)
        rows.append(m)
        print(f"  {r:>7} {m['regime']:>12} {m['peak_actual']:>11} "
              f"{m['sparsity_vs_world']:>9.2f} {str(m['within_cone']):>12}")
    print()
    lo = min(m["sparsity_vs_world"] for m in rows[:2])      # deep dissipative regime
    hi = max(m["sparsity_vs_world"] for m in rows[-2:])     # deep chaotic regime
    print(f"  dissipative regime sparsity ≈ {lo:.2f}   |   chaotic regime sparsity ≈ {hi:.2f}")
    print()
    if hi < 0.5:
        verdict = ("SPARSE even under chaos — sparsity looks STRUCTURAL, not merely dissipative. The "
                   "economic thesis would survive amplifying dynamics. (Surprising; scrutinise τ and H.)")
    elif lo < 0.5 <= hi:
        verdict = ("TRANSITION measured — sparse in the dissipative regime, DENSE in the chaotic one. "
                   "Sparsity is a property of the DYNAMICAL REGIME, not of causal structure. The cheap-"
                   "counterfactual / causal-allocation economics SURVIVE dissipative worlds and FAIL "
                   "amplifying ones (markets, near-critical gameplay). Correctness untouched. SCOPE: "
                   "'sparsity persists under amplifying dynamics' resolves to a measured NO.")
    else:
        verdict = ("DENSE throughout — even the stable regime is not sparse here; re-examine τ/δ/H before "
                   "drawing conclusions.")
    print(f"  VERDICT: {verdict}")


if __name__ == "__main__":
    main()
