# SPDX-License-Identifier: AGPL-3.0-only
"""
flow.py — the Halvorsen attractor as an Ursprung "world": an authoritative flow whose EXACT invariants form
the DEMONSTRATED floor before any numerical statistic is measured.

Cyclically-symmetric flow (a ≈ 1.4):
    ẋ = -a·x - 4y - 4z - y²
    ẏ = -a·y - 4z - 4x - z²
    ż = -a·z - 4x - 4y - x²

EXACT invariants (provable, no integration — the DEMONSTRATED floor):
  • DISSIPATIVITY: ∇·f = ∂ẋ/∂x + ∂ẏ/∂y + ∂ż/∂z = -a - a - a = -3a, a CONSTANT. Phase volume contracts as
    e^{-3a·t} ⇒ the attractor has zero volume. `divergence(a) == -3a` exactly.
  • C₃ CYCLIC EQUIVARIANCE: under the cyclic permutation P:(x,y,z)→(y,z,x), f(P·s) = P·f(s). The attractor's
    symmetry is a property of the LAW, not coordination among coordinates. `symmetry = shared law ≠ signal`.

INTEGRATORS are the PROJECTION layer (RK4, Euler): a numerical trajectory is a rendering of the true flow.
`simulation truth ≠ rendered trajectory`; `integrator ≠ flow`; `trajectory ≠ attractor`. Because the system is
chaotic, two correct integrators DIVERGE pointwise — so trajectories must never be compared pointwise across
integrators; only INVARIANT MEASURES may be (see invariant_audit.py). Everything numerical here is MEASURED,
audited for integrator-robustness, never asserted as truth. `integrity ≠ truth`.
"""
from __future__ import annotations

A = 1.4


# ---- vector helpers -----------------------------------------------------------------------------
def add(u, v):
    return (u[0] + v[0], u[1] + v[1], u[2] + v[2])


def sub(u, v):
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])


def scale(u, c):
    return (u[0] * c, u[1] * c, u[2] * c)


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def norm(u):
    return dot(u, u) ** 0.5


def dist(u, v):
    return norm(sub(u, v))


# ---- the authoritative flow ---------------------------------------------------------------------
def field(s, a: float = A):
    x, y, z = s
    return (-a * x - 4 * y - 4 * z - y * y,
            -a * y - 4 * z - 4 * x - z * z,
            -a * z - 4 * x - 4 * y - x * x)


# ---- exact invariant 1: dissipativity ------------------------------------------------------------
def divergence(a: float = A) -> float:
    """∇·f = -3a, exactly and everywhere (the trace of the Jacobian is constant)."""
    return -3.0 * a


def jacobian_trace_numeric(s, a: float = A, h: float = 1e-6) -> float:
    """Numerical ∂ẋ/∂x + ∂ẏ/∂y + ∂ż/∂z at s — should reproduce -3a to ~h (a validity check of `divergence`)."""
    tr = 0.0
    for i in range(3):
        sp = list(s); sm = list(s)
        sp[i] += h; sm[i] -= h
        tr += (field(tuple(sp), a)[i] - field(tuple(sm), a)[i]) / (2 * h)
    return tr


# ---- exact invariant 2: C₃ cyclic equivariance ---------------------------------------------------
def cyclic_perm(s):
    x, y, z = s
    return (y, z, x)


def equivariance_error(s, a: float = A) -> float:
    """max |f(P·s) − P·f(s)| — zero up to floating-point round-off iff the field is C₃-equivariant."""
    f_Ps = field(cyclic_perm(s), a)
    P_fs = cyclic_perm(field(s, a))
    return max(abs(p - q) for p, q in zip(f_Ps, P_fs))


# ---- integrators (the projection layer) ----------------------------------------------------------
def rk4_step(s, dt: float, a: float = A):
    k1 = field(s, a)
    k2 = field(add(s, scale(k1, dt / 2)), a)
    k3 = field(add(s, scale(k2, dt / 2)), a)
    k4 = field(add(s, scale(k3, dt)), a)
    return add(s, scale(add(add(k1, scale(k2, 2)), add(scale(k3, 2), k4)), dt / 6))


def euler_step(s, dt: float, a: float = A):
    return add(s, scale(field(s, a), dt))


def integrate(s0, dt: float, n: int, a: float = A, step=rk4_step, transient: int = 0):
    """Return the trajectory (list of states) after discarding `transient` steps. The committed trajectory is
    the only record of what the integration did — the Weltlinie of this world."""
    s = s0
    for _ in range(transient):
        s = step(s, dt, a)
    out = [s]
    for _ in range(n):
        s = step(s, dt, a)
        out.append(s)
    return out


def bounding_box(traj):
    xs = [p[0] for p in traj]; ys = [p[1] for p in traj]; zs = [p[2] for p in traj]
    return ((min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)))


def main():
    print("flow.py — Halvorsen attractor: exact invariants (the DEMONSTRATED floor)\n")
    print(f"  divergence ∇·f = -3a = {divergence():.4f} (exact, constant)  numeric@(1,2,3)="
          f"{jacobian_trace_numeric((1.0, 2.0, 3.0)):.5f}")
    err = max(equivariance_error(s) for s in [(1.0, 2.0, 3.0), (-2.0, 0.5, 1.0), (3.0, -1.0, -4.0)])
    print(f"  C₃ equivariance max error over samples: {err:.2e} (≈ round-off ⇒ f(P·s)=P·f(s))")
    traj = integrate((-5.0, 0.0, 0.0), dt=0.01, n=20000, transient=3000)
    print(f"  RK4 trajectory bounded in box: {tuple(tuple(round(v,1) for v in ax) for ax in bounding_box(traj))}")
    print("\n  exact invariants are DEMONSTRATED; the integrated trajectory is a projection (MEASURED).")
    print("  integrator ≠ flow; trajectory ≠ attractor; integrity ≠ truth.")


if __name__ == "__main__":
    main()
