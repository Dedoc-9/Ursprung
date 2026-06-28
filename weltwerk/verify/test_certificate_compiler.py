# SPDX-License-Identifier: AGPL-3.0-only
"""
test_certificate_compiler.py — the inductive-implication gate matrix (validity-not-outcome). Pure-stdlib.

The three implication gates (C1 initiation, C2 consecution, C3 safety) and the independent cross-check, each
exercised on a transparent domain, positive and negative:

  1. valid_chain                — a correct inductive invariant on a chain: C1∧C2∧C3 ⇒ valid; cross-check agrees.
  2. valid_branching            — a correct invariant on a branching (diamond) domain (closed under fan-out).
  3. c1_catches_bad_init        — Init ⊄ Inv ⇒ C1 fails with the offending initial state.
  4. c2_catches_non_inductive   — Inv not closed under T ⇒ C2 fails with the escaping edge (s, s′).
  5. c3_catches_unsafe_invariant— Inv admits an unsafe state ⇒ C3 fails with that state (no false proof).
  6. cross_check_catches_incomplete — an Inv that excludes a reachable state is caught by the independent
                                    reachable ⊆ Inv oracle (defense beyond the local pass).
  7. minimal_reason_determinism — the unsat-core-style reason is correct and deterministic.

Sound iff 7/7: a certificate is accepted ONLY when all three local conditions hold (so reachable ⊆ Inv ⊆ Safe),
each failure is reported with a witness, and an incomplete/unsound invariant is independently caught. The
checker verifies a GIVEN invariant; it does not derive one (PLAUSIBLE-UNVERIFIED), and size-independence is the
z3 path. `verify ≠ prove`; `checking ≠ finding`.

Run:  python3 test_certificate_compiler.py
"""
from __future__ import annotations

from certificate_compiler import (ConstraintCertificate, check_certificate, bfs_reachable, cross_check,
                                  minimal_reason, chain)


def _diamond():
    init = [0]
    universe = [0, 1, 2, 3]
    succ = lambda i: {0: [1, 2], 1: [3], 2: [3], 3: []}[i]
    return init, succ, universe


def chk(name, ok, detail):
    return (name, ok, detail)


def test_valid_chain():
    init, succ, uni = chain(6)
    cert = ConstraintCertificate("in_range", lambda i: 0 <= i <= 6, lambda i: True)
    r = check_certificate(init, succ, uni, cert)
    xc = cross_check(init, succ, cert)
    ok = r.valid and r.c1_initiation and r.c2_consecution and r.c3_safety and xc["reachable_subset_of_inv"]
    return chk("valid_chain", ok, f"valid={r.valid} cross_check_subset={xc['reachable_subset_of_inv']}")


def test_valid_branching():
    init, succ, uni = _diamond()
    cert = ConstraintCertificate("all", lambda s: s in (0, 1, 2, 3), lambda s: True)
    r = check_certificate(init, succ, uni, cert)
    ok = r.valid and cross_check(init, succ, cert)["reachable_subset_of_inv"]
    return chk("valid_branching", ok, f"valid={r.valid} (closed under fan-out)")


def test_c1_catches_bad_init():
    init, succ, uni = chain(6)
    cert = ConstraintCertificate("ge1", lambda i: i >= 1, lambda i: True)   # init 0 ∉ Inv
    r = check_certificate(init, succ, uni, cert)
    ok = (not r.valid) and r.failing_condition == "C1_init_not_in_inv" and r.witness == 0
    return chk("c1_catches_bad_init", ok, f"{r.failing_condition} witness={r.witness}")


def test_c2_catches_non_inductive():
    init, succ, uni = chain(6)
    cert = ConstraintCertificate("le2", lambda i: i <= 2, lambda i: True)   # 2→3 escapes Inv
    r = check_certificate(init, succ, uni, cert)
    ok = (not r.valid) and r.failing_condition == "C2_not_closed" and r.witness == (2, 3)
    return chk("c2_catches_non_inductive", ok, f"{r.failing_condition} witness={r.witness}")


def test_c3_catches_unsafe_invariant():
    init, succ, uni = chain(6)
    cert = ConstraintCertificate("in_range", lambda i: 0 <= i <= 6, lambda i: i != 3)  # 3 reachable & unsafe
    r = check_certificate(init, succ, uni, cert)
    ok = (not r.valid) and r.failing_condition == "C3_inv_not_safe" and r.witness == 3
    return chk("c3_catches_unsafe_invariant", ok, f"{r.failing_condition} witness={r.witness}")


def test_cross_check_catches_incomplete():
    init, succ, uni = chain(6)
    cert = ConstraintCertificate("le2", lambda i: i <= 2, lambda i: True)   # excludes reachable 3..6
    xc = cross_check(init, succ, cert)
    ok = not xc["reachable_subset_of_inv"]
    return chk("cross_check_catches_incomplete", ok, f"reachable⊆Inv={xc['reachable_subset_of_inv']} (caught)")


def test_minimal_reason_determinism():
    init, succ, uni = chain(6)
    good = ConstraintCertificate("ok", lambda i: 0 <= i <= 6, lambda i: True)
    bad = ConstraintCertificate("le2", lambda i: i <= 2, lambda i: True)
    rg, rb = check_certificate(init, succ, uni, good), check_certificate(init, succ, uni, bad)
    again = check_certificate(init, succ, uni, bad)
    ok = ("valid" in minimal_reason(rg) and "C2 fails" in minimal_reason(rb)
          and (rb.failing_condition, rb.witness) == (again.failing_condition, again.witness))
    return chk("minimal_reason_determinism", ok, f"good='{minimal_reason(rg)[:24]}…' bad='{minimal_reason(rb)[:24]}…'")


def main():
    results = [
        test_valid_chain(),
        test_valid_branching(),
        test_c1_catches_bad_init(),
        test_c2_catches_non_inductive(),
        test_c3_catches_unsafe_invariant(),
        test_cross_check_catches_incomplete(),
        test_minimal_reason_determinism(),
    ]
    print("test_certificate_compiler — 1-step inductive ConstraintCertificate gates\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a certificate is accepted only when "
          f"Init⊆Inv ∧ Inv-closed-under-T\n  ∧ Inv⊆Safe (⇒ reachable ⊆ Safe, no search), each failure carries a "
          f"witness, and an incomplete/unsound\n  invariant is independently caught. verify ≠ prove; checking ≠ finding.")
    assert passed == total, f"{total - passed} check(s) failed — inductive gate not sound"


if __name__ == "__main__":
    main()
