# SPDX-License-Identifier: AGPL-3.0-only
"""
test_attractor_ledger.py — the Halvorsen claim ledger is honest (validity-not-outcome). Pure-stdlib.

  1. ledger_honest         — every claim is graded, falsifiable, and bounded (audit_ledger honest=True).
  2. demonstrated_floor    — the algebraic claims (H1 dissipativity, H2 symmetry) are ESTABLISHED.
  3. speculation_flagged   — the 'hidden structure' claim (H6) is SPECULATIVE, not laundered into support.
  4. grades_on_ladder      — every grade is a valid ladder value.
  5. quantity_matches_flow — H1's quantity (-3a = -4.2) matches flow.divergence (the ledger isn't free-floating).

Sound iff 5/5: the ledger states what each claim rests on, what it does NOT show, and how to falsify it; the
DEMONSTRATED floor is algebraic; speculation is graded as such. `integrity ≠ truth`.

Run:  python3 test_attractor_ledger.py
"""
from __future__ import annotations

import os
import sys

from attractor_ledger import LEDGER, GRADES, SUPPORTED, audit_ledger
from flow import divergence, A

BY_ID = {c.id: c for c in LEDGER}


def chk(name, ok, detail):
    return (name, ok, detail)


def test_ledger_honest():
    a = audit_ledger(LEDGER)
    return chk("ledger_honest", a["honest"], f"honest={a['honest']} counts={a['counts']}")


def test_demonstrated_floor():
    ok = BY_ID["H1"].grade == "ESTABLISHED" and BY_ID["H2"].grade == "ESTABLISHED"
    return chk("demonstrated_floor", ok, f"H1={BY_ID['H1'].grade}, H2={BY_ID['H2'].grade} (algebraic floor)")


def test_speculation_flagged():
    ok = BY_ID["H6"].grade == "SPECULATIVE" and BY_ID["H6"].grade not in SUPPORTED
    return chk("speculation_flagged", ok, f"H6={BY_ID['H6'].grade} (not laundered into support)")


def test_grades_on_ladder():
    bad = [c.id for c in LEDGER if c.grade not in GRADES]
    return chk("grades_on_ladder", not bad, f"off-ladder: {bad or 'none'}")


def test_quantity_matches_flow():
    ok = ("-3a" in BY_ID["H1"].quantity or "-4.2" in BY_ID["H1"].quantity) and abs(divergence(A) - (-4.2)) < 1e-12
    return chk("quantity_matches_flow", ok, f"H1 quantity='{BY_ID['H1'].quantity}'; divergence={divergence(A)}")


def main():
    results = [test_ledger_honest(), test_demonstrated_floor(), test_speculation_flagged(),
              test_grades_on_ladder(), test_quantity_matches_flow()]
    print("test_attractor_ledger — Halvorsen claims graded honestly\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: claims graded + falsifiable + bounded; "
          f"algebraic floor ESTABLISHED;\n  speculation flagged; the ledger is tied to the flow's exact invariant. "
          f"integrity ≠ truth.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
