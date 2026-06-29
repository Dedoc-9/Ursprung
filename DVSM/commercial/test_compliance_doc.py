# SPDX-License-Identifier: AGPL-3.0-only
"""
test_compliance_doc.py — the compliance doc is a gate-bound, no-drift derivative of COMMERCIAL_CLAIMS:
it generates only from an honest ledger, references no claim absent from the ledger, lists the boundary
non-warranties, and carries the disclaimer + placeholders. Validity-not-outcome.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "verify"))

from compliance_doc import generate, claim_tags, LedgerNotHonest
from commercial_obligations import COMMERCIAL_CLAIMS, CommercialClaim
from claim_ledger import SUPPORTED


def chk(name, ok, detail):
    return (name, ok, detail)


def test_generates_from_honest_ledger():
    doc = generate()
    ok = isinstance(doc, str) and "Warranted scope" in doc and len(doc) > 500
    return chk("generates_from_honest_ledger", ok, f"{len(doc)} bytes")


def test_no_drift_only_ledger_claims():
    ids = {c.id for c in COMMERCIAL_CLAIMS}
    tags = claim_tags(generate())
    ok = tags and tags.issubset(ids)
    return chk("no_drift_only_ledger_claims", ok, f"doc tags ⊆ ledger ids = {tags.issubset(ids)} ({len(tags)} tags)")


def test_all_claims_present():
    doc = generate()
    missing = [c.id for c in COMMERCIAL_CLAIMS if f"[{c.id}]" not in doc]
    return chk("all_claims_present", not missing, f"missing: {missing or 'none'}")


def test_refuses_dishonest_ledger():
    bad = COMMERCIAL_CLAIMS + (CommercialClaim(
        "XS", "The kernel is proven stable.", "ESTABLISHED", "kernel.boundedness", "n/a", "n/a"),)
    raised = False
    try:
        generate(bad)
    except LedgerNotHonest:
        raised = True
    return chk("refuses_dishonest_ledger", raised, f"raised={raised}")


def test_disclaimer_and_placeholders():
    doc = generate()
    ok = "NOT LEGAL ADVICE" in doc and "[PLACEHOLDER" in doc and "AS IS" in doc
    return chk("disclaimer_and_placeholders", ok, "banner + placeholders + AS-IS present")


def test_boundaries_listed_as_nonwarranty():
    doc = generate()
    boundary = [c.id for c in COMMERCIAL_CLAIMS if c.grade not in SUPPORTED]
    # boundary ids must appear under the explicit non-warranties section
    section = doc.split("Explicit non-warranties", 1)[-1]
    ok = bool(boundary) and all(f"[{bid}]" in section for bid in boundary)
    return chk("boundaries_listed_as_nonwarranty", ok, f"boundary ids={boundary}")


def main():
    results = [
        test_generates_from_honest_ledger(),
        test_no_drift_only_ledger_claims(),
        test_all_claims_present(),
        test_refuses_dishonest_ledger(),
        test_disclaimer_and_placeholders(),
        test_boundaries_listed_as_nonwarranty(),
    ]
    print("test_compliance_doc — gate-bound, no-drift compliance generator\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. compliance doc derived from the gated ledger; claim ≠ proof; "
          f"generated ≠ executed.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
