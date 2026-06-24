# SPDX-License-Identifier: AGPL-3.0-only
"""
amplify.py — THE economic gate: is sparse divergence a property of causal structure, or a side effect
of dissipative toy physics?

Every cheap result so far lived in a DISSIPATIVE world (perturbation → decay): diffusion attenuates, the
ecology renormalises, transport re-converges. That is *why* divergence stayed sparse. The hard case the
scope doc keeps returning to is AMPLIFICATION (perturbation → growth) — a market where price moves beget
more trading, or any dynamics near instability. If divergence grows instead of damping, `|Actualₜ| ≈
|Potentialₜ|`, the pruned allocator's advantage disappears, and the "causality as the primary resource
primitive" vision does not transfer to that regime. Correctness is untouched either way; only the
economics are at stake.

MODEL: a coupled map lattice (CML) on a ring — the canonical dissipative-vs-chaotic testbed.
    xᵢ(t+1) = (1-ε)·f(xᵢ) + (ε/2)·(f(xᵢ₋₁) + f(xᵢ₊₁)),   f(x) = r·x·(1-x)   (logistic)
The gain `r` tunes the regime: r≲3 stable fixed point (decay), 3≲r≲3.57 periodic, r≳3.57 CHAOS
(sensitive dependence — perturbations grow). ε is nearest-neighbour coupling (info speed 1 chunk/tick).

MEASUREMENT (the bench sweeps r and delivers the verdict; this file just computes):
  perturb one chunk by δ at t=0; a chunk is DIVERGED at t if |x_B − x_A| > τ (a tolerance — the lossy
  Δ(out|Δp)<ε notion: a perturbation that decays below τ is effectively gone).
  sparsity = peak |diverged| / N.  ≪1 ⇒ sparse (win survives the regime); ≈1 ⇒ dense (win dies).

This is a TOLERANCE (lossy) measurement by necessity: under chaos exact float differences spread to all
bits instantly (that itself is the point — exact lossless pruning gives no win in chaos). τ measures
*meaningful* divergence. `dissipative-sparse ≠ structural-sparse`; `correctness ≠ economics`.
"""
from __future__ import annotations

PHI = 0.6180339887498949


def initial(n: int) -> list:
    """A fixed, deterministic spread of initial states in (0,1) — no RNG; a CML is deterministic."""
    return [min(0.999999, max(1e-6, (i * PHI + 0.1) % 1.0)) for i in range(n)]


def _f(x: float, r: float) -> float:
    return r * x * (1.0 - x)


def step(state: list, r: float, eps: float) -> list:
    n = len(state)
    fx = [_f(state[i], r) for i in range(n)]
    return [(1.0 - eps) * fx[i] + 0.5 * eps * (fx[(i - 1) % n] + fx[(i + 1) % n]) for i in range(n)]


def run(state: list, r: float, eps: float, horizon: int) -> list:
    traj = [list(state)]
    s = list(state)
    for _ in range(horizon):
        s = step(s, r, eps)
        traj.append(s)
    return traj


def perturb(state: list, c: int, delta: float) -> list:
    s = list(state)
    s[c] = min(0.999999, max(1e-6, s[c] + delta))
    return s


def diverged(a: list, b: list, tau: float) -> frozenset:
    """Chunks whose state meaningfully differs (|Δ| > τ) — the tolerance/actual divergence set."""
    return frozenset(i for i in range(len(a)) if abs(a[i] - b[i]) > tau)


def cone(c: int, n: int, t: int) -> set:
    """Reachability ball radius t on the ring — coupling info-speed is 1 chunk/tick (the potential)."""
    if 2 * t + 1 >= n:
        return set(range(n))
    return {(c + k) % n for k in range(-t, t + 1)}


def measure(n: int, r: float, eps: float, c: int, delta: float, tau: float, horizon: int) -> dict:
    s0 = initial(n)
    a = run(s0, r, eps, horizon)
    b = run(perturb(s0, c, delta), r, eps, horizon)
    actual = [len(diverged(a[t], b[t], tau)) for t in range(horizon + 1)]
    within_cone = all(diverged(a[t], b[t], tau) <= cone(c, n, t) for t in range(horizon + 1))
    peak_actual = max(actual)
    peak_cone = len(cone(c, n, horizon))
    return {
        "r": r, "peak_actual": peak_actual, "peak_cone": peak_cone, "n": n,
        "sparsity_vs_world": peak_actual / n,
        "sparsity_vs_cone": (peak_actual / peak_cone) if peak_cone else 0.0,
        "within_cone": within_cone, "actual": actual,
        "regime": "chaotic" if r >= 3.57 else ("periodic" if r >= 3.0 else "fixed-point"),
    }


if __name__ == "__main__":
    N, EPS, C, DELTA, TAU, H = 200, 0.25, 100, 1e-3, 1e-6, 220   # H>N ⇒ saturated cone (unconfounded)
    print("amplify.py — does divergence stay sparse when dynamics AMPLIFY?\n")
    print(f"  CML ring N={N} eps={EPS} perturb δ={DELTA}@{C} tol τ={TAU} horizon={H} (cone saturates)\n")
    for r in (2.8, 3.3, 3.5, 3.7, 3.9, 4.0):
        m = measure(N, r, EPS, C, DELTA, TAU, H)
        print(f"  r={r:<4} {m['regime']:<12} peak_actual={m['peak_actual']:>4}/{N}  "
              f"sparsity/cone={m['sparsity_vs_cone']:.2f}  within_cone={m['within_cone']}")
