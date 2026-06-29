# SPDX-License-Identifier: AGPL-3.0-only
"""
test_commercial_obligations.py — no commercial claim exceeds a discharged proof, and the gate BITES on a bad
sales draft. Validity-not-outcome. Pure-stdlib.

  1. shipped_ledger_honest       — the shipped COMMERCIAL_CLAIMS pass audit_commercial_ledger.
  2. supported_claims_discharged — every SUPPORTED claim rests on a DISCHARGED obligation.
  3. boundary_claims_downgraded  — claims resting on OPEN/REJECTED obligations are NOT at a supported grade.
  4. overclaim_caught            — a draft claiming kernel boundedness as ESTABLISHED is rejected.
  5. hype_caught                 — a SUPPORTED claim containing hype ("100% unhackable, guaranteed") is flagged.
  6. unknown_obligation_caught   — a claim resting on an unknown obligation key is flagged.
  7. every_claim_has_boundary    — every claim carries a does_not_show AND a falsifier.
  8. claims_emit_analysis        — each claim projects to an AnalysisResult.

Sound iff 8/8: the shipped ledger is honest AND the gate rejects overclaim/hype/unknown drafts.
`consider those proofs`; `claim ≠ proof`; `grade ≠ truth`.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "verify"))

from commercial_obligations import (CommercialClaim, COMMERCIAL_CLAIMS, DISCHARGED, OPEN_OR_REJECTED,
                                    audit_commercial_ledger)
from claim_ledger import SUPPORTED
from artifacts import AnalysisResult


def chk(name, ok, detail):
    return (name, ok, detail)


def test_shipped_ledger_honest():
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS)
    return chk("shipped_ledger_honest", a["honest"],
               f"honest={a['honest']} exceeds={a['exceeds_proof']} hype={a['hype']}")


def test_supported_claims_discharged():
    bad = [c.id for c in COMMERCIAL_CLAIMS if c.grade in SUPPORTED and c.rests_on not in DISCHARGED]
    return chk("supported_claims_discharged", not bad, f"supported-but-undischarged: {bad or 'none'}")


def test_boundary_claims_downgraded():
    bad = [c.id for c in COMMERCIAL_CLAIMS if c.rests_on in OPEN_OR_REJECTED and c.grade in SUPPORTED]
    return chk("boundary_claims_downgraded", not bad, f"over-graded boundary claims: {bad or 'none'}")


def test_overclaim_caught():
    bad = COMMERCIAL_CLAIMS + (CommercialClaim(
        "X1", "Guarantees your kernel stays numerically bounded.", "ESTABLISHED", "kernel.boundedness",
        "n/a", "n/a"),)
    a = audit_commercial_ledger(bad)
    ok = (not a["honest"]) and "X1" in a["exceeds_proof"]
    return chk("overclaim_caught", ok, f"honest={a['honest']} exceeds={a['exceeds_proof']}")


def test_hype_caught():
    bad = COMMERCIAL_CLAIMS + (CommercialClaim(
        "X2", "100% unhackable leak detection, guaranteed.", "MEASURED", "coupling.detect_identifiable",
        "n/a", "n/a"),)
    a = audit_commercial_ledger(bad)
    ok = (not a["honest"]) and "X2" in a["hype"]
    return chk("hype_caught", ok, f"hype={a['hype']}")


def test_unknown_obligation_caught():
    bad = COMMERCIAL_CLAIMS + (CommercialClaim(
        "X3", "Does something useful.", "MEASURED", "nonexistent.obligation", "n/a", "n/a"),)
    a = audit_commercial_ledger(bad)
    ok = (not a["honest"]) and "X3" in a["unknown_obligation"]
    return chk("unknown_obligation_caught", ok, f"unknown={a['unknown_obligation']}")


def test_every_claim_has_boundary():
    bad = [c.id for c in COMMERCIAL_CLAIMS if not c.does_not_show or not c.falsifier]
    return chk("every_claim_has_boundary", not bad, f"missing does_not_show/falsifier: {bad or 'none'}")


def test_claims_emit_analysis():
    bad = [c.id for c in COMMERCIAL_CLAIMS if not isinstance(c.to_claim().as_analysis(), AnalysisResult)]
    return chk("claims_emit_analysis", not bad, f"non-analysis: {bad or 'none'}")


def test_scoped_certificate_and_kappa_claims():
    by_id = {c.id: c for c in COMMERCIAL_CLAIMS}
    c7, c8 = by_id.get("C7"), by_id.get("C8")
    scoped = (c7 is not None and c8 is not None
              and c7.grade in SUPPORTED and c7.rests_on in DISCHARGED
              and "not a global stability proof" in c7.does_not_show.lower()  # scoped, not overclaimed
              and c8.grade in SUPPORTED and c8.rests_on in DISCHARGED)
    # the gate must still reject a "the kernel is stable" claim resting on the OPEN boundedness obligation
    overclaim = COMMERCIAL_CLAIMS + (CommercialClaim(
        "XS", "The kernel is stable.", "ESTABLISHED", "kernel.boundedness", "n/a", "n/a"),)
    rejected = "XS" in audit_commercial_ledger(overclaim)["exceeds_proof"]
    return chk("scoped_certificate_and_kappa", scoped and rejected,
               f"C7/C8 scoped={scoped}  stability-overclaim-rejected={rejected}")


def main():
    results = [
        test_shipped_ledger_honest(),
        test_supported_claims_discharged(),
        test_boundary_claims_downgraded(),
        test_overclaim_caught(),
        test_hype_caught(),
        test_unknown_obligation_caught(),
        test_every_claim_has_boundary(),
        test_claims_emit_analysis(),
        test_scoped_certificate_and_kappa_claims(),
    ]
    print("test_commercial_obligations — no commercial claim exceeds discharged proof\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. marketing cannot exceed evidence; consider those proofs.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
