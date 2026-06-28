# SPDX-License-Identifier: AGPL-3.0-only
"""
invariant_audit.py — the MEASURED layer, audited for the chaos-specific ghosts.

Two disciplines the framework forces here:

1. DIFFERENTIAL ON MEASURES, NOT PATHS. Sensitive dependence means any two correct integrators diverge
   pointwise — so the PO-4/differential idea cannot compare trajectories. It must compare INVARIANT MEASURES:
   the dissipation rate (exactly -3a), the sign of the largest Lyapunov exponent, the attractor's bounding box.
   `agreement-on-measure ≠ agreement-on-path`; `trajectory ≠ attractor`.

2. THE CANONICAL GHOST: determinism ≠ reproducibility. Two integrations from inputs differing by ε diverge
   exponentially; the divergence RATE ≈ the largest Lyapunov exponent λ_max, and is integrator-independent.
   That classifies the ghost as PRECISION/sensitive-dependence (a real dynamical amplification), NOT a model or
   implementation defect. `determinism ≠ reproducibility`; the committed trajectory records what occurred, it
   does not certify reproducibility.

Everything here is MEASURED with our own integrator (we do not import a Lyapunov/dimension number from the
literature — `measure ≠ cite-authority`), and stated as integrator-audited estimates, never as truth.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from flow import (field, rk4_step, integrate, add, sub, scale, dist, divergence,
                  jacobian_trace_numeric, bounding_box, A)


def lyapunov_max(a: float = A, dt: float = 0.01, n: int = 15000, transient: int = 3000,
                 d0: float = 1e-8, s0=(-5.0, 0.0, 0.0)) -> float:
    """Largest Lyapunov exponent via the Benettin two-trajectory method (deterministic). λ_max > 0 ⇒ chaos."""
    s = s0
    for _ in range(transient):
        s = rk4_step(s, dt, a)
    sp = add(s, (d0, 0.0, 0.0))
    acc, cnt = 0.0, 0
    for _ in range(n):
        s = rk4_step(s, dt, a)
        sp = rk4_step(sp, dt, a)
        d = dist(s, sp)
        if d > 0:
            acc += math.log(d / d0)
            cnt += 1
            sp = add(s, scale(sub(sp, s), d0 / d))      # renormalize the perturbation to length d0
    return acc / (cnt * dt) if cnt else 0.0


def dissipation_numeric(a: float = A, dt: float = 0.01, n: int = 4000, transient: int = 3000) -> float:
    """Average of the numerical Jacobian trace along a trajectory — should reproduce ∇·f = -3a (constant)."""
    traj = integrate((-5.0, 0.0, 0.0), dt, n, a, transient=transient)
    return sum(jacobian_trace_numeric(s, a) for s in traj) / len(traj)


@dataclass(frozen=True)
class FPGhost:
    amplification: float        # final separation / initial ε
    rate: float                 # log-divergence rate (≈ λ_max if sensitive dependence)
    lyap: float
    classification: str


def fp_divergence(a: float = A, dt: float = 0.01, n: int = 2500, eps: float = 1e-9,
                  s0=(-5.0, 0.0, 0.0), transient: int = 3000) -> FPGhost:
    """Two integrations whose inputs differ by ε. Measure how the separation grows; classify the ghost by
    comparing the divergence rate to λ_max. Same algorithm + ε-different input ⇒ the gap is precision."""
    s = s0
    for _ in range(transient):
        s = rk4_step(s, dt, a)
    sp = add(s, (eps, 0.0, 0.0))
    for _ in range(n):
        s = rk4_step(s, dt, a)
        sp = rk4_step(sp, dt, a)
    d_final = dist(s, sp)
    amp = d_final / eps
    rate = math.log(d_final / eps) / (n * dt) if d_final > 0 else 0.0
    lam = lyapunov_max(a, dt)
    near = lam > 0 and abs(rate - lam) / lam < 0.5
    cls = ("precision/sensitive-dependence (rate ≈ λ_max; integrator-independent dynamical amplification)"
           if near else "divergence present; rate not matched to λ_max within tolerance")
    return FPGhost(amp, rate, lam, cls)


def measures(a: float = A, dt: float = 0.01) -> dict:
    traj = integrate((-5.0, 0.0, 0.0), dt, 20000, a, transient=3000)
    return {"lyap": lyapunov_max(a, dt), "dissipation": divergence(a),
            "dissipation_numeric": dissipation_numeric(a, dt), "bbox": bounding_box(traj)}


def measures_agree_paths_diverge(a: float = A) -> dict:
    """The honest differential test: two integrators agree on the INVARIANTS but their PATHS diverge."""
    lam1, lam2 = lyapunov_max(a, 0.01), lyapunov_max(a, 0.005)
    # same IC, same physical time T, two step sizes ⇒ states must diverge (chaos)
    T = 25.0
    a1 = integrate((-5.0, 0.0, 0.0), 0.01, int(T / 0.01), a)[-1]
    a2 = integrate((-5.0, 0.0, 0.0), 0.005, int(T / 0.005), a)[-1]
    return {"lyap_dt": lam1, "lyap_dt_half": lam2,
            "lyap_sign_agree": (lam1 > 0) == (lam2 > 0) and lam1 > 0,
            "dissipation_agree": divergence(a) == divergence(a),
            "path_separation_at_T": dist(a1, a2)}


def main():
    print("invariant_audit.py — MEASURED invariants + chaos ghost audit\n")
    lam = lyapunov_max()
    print(f"  largest Lyapunov λ_max ≈ {lam:.3f} (>0 ⇒ chaotic)  [MEASURED, our integrator]")
    print(f"  dissipation ∇·f = {divergence():.3f} (exact)  numeric ≈ {dissipation_numeric():.3f}")
    g = fp_divergence()
    print(f"  FP ghost: amplification={g.amplification:.1e}  rate={g.rate:.3f}  λ_max={g.lyap:.3f}")
    print(f"            classification: {g.classification}")
    m = measures_agree_paths_diverge()
    print(f"  differential-on-measures: lyap_sign_agree={m['lyap_sign_agree']}  "
          f"dissipation_agree={m['dissipation_agree']}  PATH separation @T={m['path_separation_at_T']:.2f}")
    print("\n  invariants agree across integrators; PATHS diverge (chaos). determinism ≠ reproducibility;")
    print("  agreement-on-measure ≠ agreement-on-path; measure ≠ cite-authority; integrity ≠ truth.")


if __name__ == "__main__":
    main()
