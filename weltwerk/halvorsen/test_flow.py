# SPDX-License-Identifier: AGPL-3.0-only
"""
test_flow.py — the exact invariants + integrator behaviour (validity-not-outcome). Pure-stdlib.

  1. divergence_exact      — ∇·f = -3a exactly; the numerical Jacobian trace reproduces it.
  2. cyclic_equivariance   — f(P·s) = P·f(s) up to round-off (C₃ symmetry of the law).
  3. rk4_bounded           — a long RK4 orbit stays in a finite box (boundedness is MEASURED).
  4. sensitive_dependence  — two RK4 orbits from ε-close inputs diverge (chaos ⇒ no pointwise comparison).
  5. determinism           — identical inputs ⇒ identical trajectory.

Sound iff 5/5: the algebraic invariants hold exactly (DEMONSTRATED floor), the orbit is empirically bounded,
and sensitive dependence is present. `integrator ≠ flow`; `trajectory ≠ attractor`.

Run:  python3 test_flow.py
"""
from __future__ import annotations

from flow import (divergence, jacobian_trace_numeric, equivariance_error, integrate,
                  rk4_step, dist, bounding_box, A)


def chk(name, ok, detail):
    return (name, ok, detail)


def test_divergence_exact():
    ok = abs(divergence(A) - (-4.2)) < 1e-12 and abs(jacobian_trace_numeric((1.0, 2.0, 3.0)) - (-4.2)) < 1e-3
    return chk("divergence_exact", ok, f"∇·f={divergence(A)} (=-3a); numeric≈{jacobian_trace_numeric((1.,2.,3.)):.4f}")


def test_cyclic_equivariance():
    err = max(equivariance_error(s) for s in [(1., 2., 3.), (-2., .5, 1.), (3., -1., -4.), (0.1, -0.2, 0.3)])
    return chk("cyclic_equivariance", err < 1e-9, f"max |f(P·s)−P·f(s)| = {err:.2e}")


def test_rk4_bounded():
    traj = integrate((-5.0, 0.0, 0.0), 0.01, 20000, A, transient=3000)
    mx = max(max(abs(v) for v in p) for p in traj)
    return chk("rk4_bounded", mx < 100.0, f"max|coord| over orbit = {mx:.1f} (< 100 ⇒ bounded)")


def test_sensitive_dependence():
    a = integrate((-5.0, 0.0, 0.0), 0.01, 2500, A)[-1]
    b = integrate((-5.0 + 1e-6, 0.0, 0.0), 0.01, 2500, A)[-1]
    d = dist(a, b)
    return chk("sensitive_dependence", d > 0.5, f"ε=1e-6 inputs diverge to dist={d:.2f} (chaos)")


def test_determinism():
    a = integrate((-5.0, 0.0, 0.0), 0.01, 1000, A)
    b = integrate((-5.0, 0.0, 0.0), 0.01, 1000, A)
    return chk("determinism", a == b, f"identical trajectory: {a == b}")


def main():
    results = [test_divergence_exact(), test_cyclic_equivariance(), test_rk4_bounded(),
              test_sensitive_dependence(), test_determinism()]
    print("test_flow — Halvorsen exact invariants + integrator behaviour\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: exact invariants hold (DEMONSTRATED), the orbit "
          f"is bounded\n  (MEASURED), and sensitive dependence is present. integrator ≠ flow; trajectory ≠ attractor.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
