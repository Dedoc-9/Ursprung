# SPDX-License-Identifier: AGPL-3.0-only
"""
test_quantum_ledger.py — proofs that the quantum-design ledger is HONEST (validity-not-outcome). Pure-stdlib.

These assert the ledger's discipline, not any physics outcome:

  1. no_speculative_as_supported  — no SPECULATIVE/NOT_MEASURED claim is graded ESTABLISHED/MEASURED; the
                                    macroscopic-coherence claim (C5) is graded SPECULATIVE.
  2. every_claim_has_falsifier    — every claim carries a non-empty falsifier AND a 'does_not_show' boundary.
  3. grades_on_the_ladder         — every grade is a valid ladder value (no ad-hoc grades).
  4. as_analysis_honest           — each claim projects to an AnalysisResult with scope + ≥1 limitation (PO-9).
  5. quantities_grounded          — the cited numbers match the researched values (Pauling ≈ R·ln(3/2) ≈ 3.37
                                    J/mol/K; D₂O−H₂O melt ≈ +3.8 K) — a regression guard against drift.
  6. molecular_link_supported     — the molecular quantum claims (C1, C4) are supported; the macro-coherence
                                    claim (C5) is not. The legitimate link is bounded, not inflated.

Sound iff 6/6: the ledger states what each quantum claim rests on, what it does NOT show, and how to falsify
it, and never presents speculation as settled. `integrity ≠ truth`; `possibility ≠ actuality`.

Run:  python3 test_quantum_ledger.py
"""
from __future__ import annotations

import math

from quantum_ledger import LEDGER, GRADES, _SUPPORTED
from artifacts import AnalysisResult, Limitation

BY_ID = {c.id: c for c in LEDGER}
R = 8.314


def chk(name, ok, detail):
    return (name, ok, detail)


def test_no_speculative_as_supported():
    ok = BY_ID["C5"].grade == "SPECULATIVE" and all(
        not (c.grade in _SUPPORTED and "no established mechanism" in c.mechanism) for c in LEDGER)
    return chk("no_speculative_as_supported", ok, f"C5 grade={BY_ID['C5'].grade} (not laundered into support)")


def test_every_claim_has_falsifier():
    bad = [c.id for c in LEDGER if not (c.falsifier.strip() and c.does_not_show.strip())]
    return chk("every_claim_has_falsifier", not bad, f"claims missing falsifier/boundary: {bad or 'none'}")


def test_grades_on_the_ladder():
    bad = [c.id for c in LEDGER if c.grade not in GRADES]
    return chk("grades_on_the_ladder", not bad, f"off-ladder grades: {bad or 'none'}")


def test_as_analysis_honest():
    bad = []
    for c in LEDGER:
        a = c.as_analysis()
        if not (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
                and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations)
                and len(a.findings) >= 1):
            bad.append(c.id)
    return chk("as_analysis_honest", not bad, f"non-honest projections: {bad or 'none'}")


def test_quantities_grounded():
    pauling = R * math.log(1.5)                       # ≈ 3.37 J/mol/K
    ok_pauling = "3.37" in BY_ID["C4"].quantity and abs(pauling - 3.37) < 0.05
    ok_isotope = "3.8" in BY_ID["C3"].quantity
    return chk("quantities_grounded", ok_pauling and ok_isotope,
               f"R·ln(3/2)={pauling:.2f} J/mol/K matches C4; D₂O isotope ≈+3.8 K matches C3")


def test_molecular_link_supported():
    ok = (BY_ID["C1"].grade in _SUPPORTED and BY_ID["C4"].grade in _SUPPORTED
          and BY_ID["C5"].grade not in _SUPPORTED)
    return chk("molecular_link_supported", ok,
               f"C1={BY_ID['C1'].grade}, C4={BY_ID['C4'].grade} supported; C5={BY_ID['C5'].grade} not")


def main():
    results = [
        test_no_speculative_as_supported(),
        test_every_claim_has_falsifier(),
        test_grades_on_the_ladder(),
        test_as_analysis_honest(),
        test_quantities_grounded(),
        test_molecular_link_supported(),
    ]
    print("test_quantum_ledger — quantum→snow-crystal claims graded honestly\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: every claim has a mechanism, a stated "
          f"boundary, and a\n  falsifier; the molecular quantum link is supported and bounded; macroscopic "
          f"'quantum design' is\n  graded SPECULATIVE, never settled. integrity ≠ truth; possibility ≠ actuality.")
    assert passed == total, f"{total - passed} check(s) failed — ledger not honest"


if __name__ == "__main__":
    main()
