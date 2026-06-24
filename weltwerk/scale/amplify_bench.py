# SPDX-License-Identifier: AGPL-3.0-only
"""
amplify_bench — is sparse divergence structural, or just dissipative toy physics?

CORRECTED MEASUREMENT. A first pass used horizon H=60 on N=200 and the world-relative denominator. That
was confounded: coupling speed is 1 chunk/tick, so at H=60 the reachability cone had only reached ~121
of 200 chunks — divergence *could not* exceed ~60% regardless of dynamics, and the world-relative
sparsity understated the regime gap. Two fixes here:
  (1) horizon H ≥ N (cone fully SATURATES the ring — measure no longer bounded by the light cone);
  (2) report `actual / cone` — the economically honest denominator (the pruned allocator competes
      against the conservative CONE, not the whole world). Once the cone saturates, cone = N.

  sparsity_vs_cone ≪ 1 across all r  → STRUCTURAL: the win survives amplification. (Strong, surprising.)
  sparsity_vs_cone → 1 as r → chaos  → sparsity is a property of the DYNAMICAL REGIME: cheap counterfactual
                                        / causal-allocation economics SURVIVE dissipative worlds, FAIL
                                        amplifying ones. Correctness untouched.
"""
from __future__ import annotations

from amplify import measure

N, EPS, C, DELTA, TAU, H = 200, 0.25, 100, 1e-3, 1e-6, 220   # H>N ⇒ cone saturates the ring
RS = (2.6, 2.9, 3.2, 3.45, 3.57, 3.7, 3.83, 4.0)


def main():
    print("amplify_bench — structural sparsity, or dissipative artifact? (corrected: saturated cone)")
    print(f"  CML ring N={N} eps={EPS} perturb δ={DELTA}@{C} tol τ={TAU} horizon={H} (cone saturates)\n")
    print(f"  {'gain r':>7} {'regime':>12} {'peakActual':>11} {'/cone':>7} {'/world':>7} {'coneSat':>8}")
    print("  " + "-" * 58)
    rows = []
    for r in RS:
        m = measure(N, r, EPS, C, DELTA, TAU, H)
        rows.append(m)
        sat = m["peak_cone"] >= N
        print(f"  {r:>7} {m['regime']:>12} {m['peak_actual']:>11} "
              f"{m['sparsity_vs_cone']:>7.2f} {m['sparsity_vs_world']:>7.2f} {str(sat):>8}")
    print()
    lo = min(m["sparsity_vs_cone"] for m in rows[:2])      # deep dissipative regime
    hi = max(m["sparsity_vs_cone"] for m in rows[-2:])     # deep chaotic regime
    print(f"  dissipative regime sparsity_vs_cone ≈ {lo:.2f}   |   chaotic regime ≈ {hi:.2f}")
    print()
    if hi < 0.5:
        verdict = ("SPARSE even under chaos with a SATURATED cone — sparsity looks STRUCTURAL. The economic "
                   "thesis would survive amplifying dynamics. (Believe it only after checking τ/δ sensitivity.)")
    elif lo < 0.5 <= hi:
        verdict = ("TRANSITION — sparse in the dissipative regime, DENSE in the chaotic one (cone saturated, "
                   "so this is not a horizon artifact). Sparsity is a property of the DYNAMICAL REGIME, not "
                   "of causal structure. Cheap counterfactual / causal-allocation economics SURVIVE "
                   "dissipative worlds and FAIL amplifying ones (markets, near-critical gameplay). "
                   "Correctness untouched. SCOPE: 'sparsity persists under amplifying dynamics' → measured NO.")
    else:
        verdict = ("DENSE throughout — re-examine τ/δ; even the stable regime is not sparse, which is itself "
                   "suspicious.")
    print(f"  VERDICT: {verdict}")


if __name__ == "__main__":
    main()
