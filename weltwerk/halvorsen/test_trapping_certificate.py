# SPDX-License-Identifier: AGPL-3.0-only
"""
test_trapping_certificate.py — the boundedness certificate is honest (validity-not-outcome). Pure-stdlib.

  1. halvorsen_quadratic_rejected — V=‖s‖² does NOT certify a Halvorsen trapping ball; a witness with ‖s‖>R and
                                    dV/dt ≥ 0 is returned (the cubic term breaks it). The checker refuses.
  2. contracting_toy_certified    — V=‖s‖² DOES certify the contracting toy field (max dV/dt < 0, no witness).
  3. dVdt_matches_finite_diff     — dV/dt = 2⟨s,f⟩ matches the finite-difference of V along the field.
  4. determinism                  — the certify scan is deterministic.

Sound iff 4/4: the certificate is accepted only when dV/dt < 0 outside R (positive case shown on the toy), and
is REJECTED with a witness for Halvorsen — so empirical boundedness is NOT laundered into a proof.
`empirical-boundedness ≠ certified-boundedness`; `integrity ≠ truth`.

Run:  python3 test_trapping_certificate.py
"""
from __future__ import annotations

from trapping_certificate import certify_ball, contracting_field, dVdt_quadratic
from flow import field, norm, add, scale, dot, A


def chk(name, ok, detail):
    return (name, ok, detail)


def test_halvorsen_quadratic_rejected():
    r = certify_ball(field, A, R=8.0)
    ok = (not r.certified) and r.witness is not None and norm(r.witness) > 8.0 and r.max_dVdt >= 0
    return chk("halvorsen_quadratic_rejected", ok,
               f"certified={r.certified} max_dVdt={r.max_dVdt:.1f} witness‖s‖={norm(r.witness):.1f}")


def test_contracting_toy_certified():
    r = certify_ball(contracting_field, A, R=1.0)
    ok = r.certified and r.witness is None and r.max_dVdt < 0
    return chk("contracting_toy_certified", ok, f"certified={r.certified} max_dVdt={r.max_dVdt:.2f}")


def test_dVdt_matches_finite_diff():
    s = (1.0, 2.0, -1.0)
    h = 1e-5
    f = field(s, A)
    v0 = dot(s, s)
    v1 = dot(add(s, scale(f, h)), add(s, scale(f, h)))
    fd = (v1 - v0) / h
    ok = abs(fd - dVdt_quadratic(s, field, A)) < 1e-2
    return chk("dVdt_matches_finite_diff", ok, f"finite-diff={fd:.4f} vs dV/dt={dVdt_quadratic(s, field, A):.4f}")


def test_determinism():
    a = certify_ball(field, A, R=8.0)
    b = certify_ball(field, A, R=8.0)
    ok = (a.certified, a.max_dVdt) == (b.certified, b.max_dVdt)
    return chk("determinism", ok, f"repeated certify agrees: {ok}")


def main():
    results = [test_halvorsen_quadratic_rejected(), test_contracting_toy_certified(),
              test_dVdt_matches_finite_diff(), test_determinism()]
    print("test_trapping_certificate — boundedness certificate (honest rejection)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the quadratic-V ball is certified for a "
          f"contracting field but\n  REJECTED (with a witness) for Halvorsen — empirical boundedness is not "
          f"laundered into a proof.\n  empirical-boundedness ≠ certified-boundedness; integrity ≠ truth.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
