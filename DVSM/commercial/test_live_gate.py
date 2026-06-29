# SPDX-License-Identifier: AGPL-3.0-only
"""
test_live_gate.py — Obligation B: the LIVE execution binding of the commercial gate. Validity-not-outcome:
asserts the gate's behaviour (a fresh all-pass receipt ⇒ honest; a failed/missing backing suite ⇒ caught;
no receipt ⇒ the static audit is unchanged; a stale receipt file ⇒ ignored). `receipt ≠ proof`; `tested ≠ safe`.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commercial_obligations import (COMMERCIAL_CLAIMS, OBLIGATION_SUITE, SUPPORTED,  # noqa: E402
                                     audit_commercial_ledger, load_live_receipts)


def chk(name, ok, detail):
    return (name, ok, detail)


def _all_pass_receipt():
    """A receipt where every SUPPORTED claim's backing suite reads PASS."""
    return {OBLIGATION_SUITE[c.rests_on]: "PASS"
            for c in COMMERCIAL_CLAIMS if c.grade in SUPPORTED and c.rests_on in OBLIGATION_SUITE}


def _first_supported_suite():
    for c in COMMERCIAL_CLAIMS:
        if c.grade in SUPPORTED and c.rests_on in OBLIGATION_SUITE:
            return OBLIGATION_SUITE[c.rests_on]
    raise AssertionError("no supported claim with a backing suite")


def test_all_pass_is_live_honest():
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS, live_receipts=_all_pass_receipt())
    ok = a["honest"] and not a["unverified_live"]
    return chk("all_pass_is_live_honest", ok, f"honest={a['honest']} unverified={a['unverified_live']}")


def test_failed_backing_suite_caught():
    r = _all_pass_receipt()
    r[_first_supported_suite()] = "FAIL"
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS, live_receipts=r)
    ok = (not a["honest"]) and len(a["unverified_live"]) >= 1
    return chk("failed_backing_suite_caught", ok, f"unverified_live={a['unverified_live']}")


def test_missing_backing_suite_caught():
    r = _all_pass_receipt()
    del r[_first_supported_suite()]  # a backing suite that simply didn't run this build
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS, live_receipts=r)
    ok = (not a["honest"]) and len(a["unverified_live"]) >= 1
    return chk("missing_backing_suite_caught", ok, f"unverified_live={a['unverified_live']}")


def test_static_audit_unchanged_without_receipt():
    # default (no receipt) ⇒ pure static audit: shipped ledger honest, unverified_live empty
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS)
    ok = a["honest"] and a["unverified_live"] == []
    return chk("static_audit_unchanged_without_receipt", ok, f"honest={a['honest']}")


def test_receipt_freshness_window():
    p = os.path.join(tempfile.gettempdir(), "_dvsm_test_receipt.tsv")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# suite\tstatus\trun_id\ntest_x\tPASS\tr1\n")
    fresh = load_live_receipts(p, max_age_seconds=600)
    stale = load_live_receipts(p, max_age_seconds=-1)  # force the freshness check to reject
    ok = fresh.get("test_x") == "PASS" and stale == {}
    try:
        os.remove(p)
    except OSError:
        pass
    return chk("receipt_freshness_window", ok, f"fresh={fresh.get('test_x')} stale_empty={stale == {}}")


def main():
    results = [
        test_all_pass_is_live_honest(),
        test_failed_backing_suite_caught(),
        test_missing_backing_suite_caught(),
        test_static_audit_unchanged_without_receipt(),
        test_receipt_freshness_window(),
    ]
    print("test_live_gate — live execution binding (static-check ≠ live-execution)\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:38s} {detail}")
    print(f"\n  {passed}/{len(results)} checks. receipt ≠ proof; tested ≠ safe; a missing/failed suite fails closed.")
    assert passed == len(results), f"{len(results) - passed} check(s) failed"


if __name__ == "__main__":
    main()
