# SPDX-License-Identifier: AGPL-3.0-only
"""
test_claim_ledger.py — the domain-agnostic honesty-enforced claim ledger is sound (validity-not-outcome).

  1. claim_as_analysis_honest    — a Claim projects to an AnalysisResult with scope + ≥1 limitation.
  2. audit_passes_honest_ledger  — a well-formed ledger (graded, falsifiable, bounded) passes audit_ledger.
  3. audit_catches_off_ladder    — a claim with an invalid grade is flagged; honest=False.
  4. audit_catches_missing       — a claim with an empty falsifier or empty boundary is flagged; honest=False.
  5. grades_ladder_consistent    — SUPPORTED ⊆ GRADES; ladder is a fixed, non-empty tuple.
  6. grade_counts_sum            — the per-grade counts sum to the ledger size.

Sound iff 6/6: the template forces every claim to carry grade + mechanism + boundary + falsifier and projects
to the honesty contract, and the ledger audit refuses ungraded/unfalsifiable/boundary-free claims. `integrity ≠ truth`.

Run:  python3 test_claim_ledger.py
"""
from __future__ import annotations

from claim_ledger import Claim, GRADES, SUPPORTED, grade_counts, audit_ledger
from artifacts import AnalysisResult, Limitation

GOOD = (
    Claim("A", "Effect E reproduces.", "ESTABLISHED", "mechanism M", "the magnitude under C", "a failed replication"),
    Claim("B", "H explains the residual.", "SPECULATIVE", "no established mechanism", "anything", "an isolating test"),
)


def chk(name, ok, detail):
    return (name, ok, detail)


def test_claim_as_analysis_honest():
    a = GOOD[0].as_analysis()
    ok = (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
          and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations))
    return chk("claim_as_analysis_honest", ok, f"scope={a.scope!r} limitations={len(a.limitations)}")


def test_audit_passes_honest_ledger():
    a = audit_ledger(GOOD)
    return chk("audit_passes_honest_ledger", a["honest"], f"honest={a['honest']} counts={a['counts']}")


def test_audit_catches_off_ladder():
    bad = GOOD + (Claim("X", "ungraded claim", "AMAZING", "m", "b", "f"),)
    a = audit_ledger(bad)
    ok = (not a["honest"]) and "X" in a["off_ladder"]
    return chk("audit_catches_off_ladder", ok, f"off_ladder={a['off_ladder']} honest={a['honest']}")


def test_audit_catches_missing():
    bad = GOOD + (Claim("Y", "no falsifier", "MEASURED", "m", "boundary", "   "),)
    a = audit_ledger(bad)
    ok = (not a["honest"]) and "Y" in a["missing_falsifier_or_boundary"]
    return chk("audit_catches_missing", ok, f"missing={a['missing_falsifier_or_boundary']} honest={a['honest']}")


def test_grades_ladder_consistent():
    ok = bool(GRADES) and SUPPORTED <= set(GRADES)
    return chk("grades_ladder_consistent", ok, f"GRADES={GRADES}; SUPPORTED⊆GRADES={SUPPORTED <= set(GRADES)}")


def test_grade_counts_sum():
    c = grade_counts(GOOD)
    ok = sum(c.values()) == len(GOOD)
    return chk("grade_counts_sum", ok, f"counts={c} sum={sum(c.values())}=={len(GOOD)}")


def main():
    results = [
        test_claim_as_analysis_honest(),
        test_audit_passes_honest_ledger(),
        test_audit_catches_off_ladder(),
        test_audit_catches_missing(),
        test_grades_ladder_consistent(),
        test_grade_counts_sum(),
    ]
    print("test_claim_ledger — domain-agnostic honesty-enforced claim ledger\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: every claim carries grade+mechanism+boundary+"
          f"falsifier and\n  projects to the honesty contract; the audit refuses ungraded/unfalsifiable/"
          f"boundary-free claims. integrity ≠ truth.")
    assert passed == total, f"{total - passed} check(s) failed — claim ledger not sound"


if __name__ == "__main__":
    main()
