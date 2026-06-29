# SPDX-License-Identifier: AGPL-3.0-only
"""
test_kernel_auditor.py — the product makes both chokepoints inescapable and works on arbitrary customer
telemetry. Validity-not-outcome. Pure-stdlib (~a minute).

  1. clean_certifies         — a clean window ⇒ omega_to_v certifiable ⇒ certify() runs.
  2. contaminated_refused    — an Ω→V window ⇒ certify() raises UngroundedError (atomic refusal).
  3. posture_no_scalar       — posture() is a dict of explicit states; WindowAudit has no score/health field.
  4. windows_emit_analysis   — every probe answer is an AnalysisResult (scope + ≥1 limitation).
  5. blind_declared          — an unidentifiable probe is reported under posture['blind'], not cleared.
  6. custom_probe            — a customer-defined probe over arbitrary columns detects a planted leak.
  7. determinism             — re-auditing the same telemetry agrees.
  8. ledger_honest           — the per-probe claim ledger is honest.

Sound iff 8/8. `observation ≠ authority`; `undetected ≠ absent`; `integrity ≠ truth`.
"""
from __future__ import annotations

import os
import random
import sys
from dataclasses import fields

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "verify"))

from kernel_auditor import KernelAuditor, CouplingProbe, WindowAudit, rows_from_reference, WINDOW
from dvsm_reference import gen_clean, gen_contaminated
from epistemic_types import UngroundedError
from artifacts import AnalysisResult, Limitation
from claim_ledger import audit_ledger

N = WINDOW


def chk(name, ok, detail):
    return (name, ok, detail)


def _clean():
    a = KernelAuditor(window=N)
    return a, a.audit(rows_from_reference(gen_clean(N, 1)))[0]


def _dirty():
    a = KernelAuditor(window=N)
    return a, a.audit(rows_from_reference(gen_contaminated("omega_to_v", N, 2)))[0]


def test_clean_certifies():
    a, wa = _clean()
    log = []
    ran = False
    try:
        a.certify(wa, "omega_to_v", lambda w: log.append(w.index)); ran = True
    except UngroundedError:
        ran = False
    ok = "omega_to_v" in wa.posture()["certifiable"] and ran and log == [0]
    return chk("clean_certifies", ok, f"certified={ran}")


def test_contaminated_refused():
    a, wa = _dirty()
    raised = False
    try:
        a.certify(wa, "omega_to_v", lambda w: w)
    except UngroundedError:
        raised = True
    ok = "omega_to_v" in wa.posture()["contaminated"] and raised
    return chk("contaminated_refused", ok, f"refused={raised}")


def test_posture_no_scalar():
    _a, wa = _clean()
    names = {f.name for f in fields(WindowAudit)}
    p = wa.posture()
    ok = isinstance(p, dict) and not (names & {"score", "confidence", "health", "fused"})
    return chk("posture_no_scalar", ok, f"posture keys={list(p)}")


def test_windows_emit_analysis():
    _a, wa = _clean()
    bad = [an for an in wa.analyses if not (isinstance(an, AnalysisResult) and an.scope
           and len(an.limitations) >= 1 and all(isinstance(l, Limitation) for l in an.limitations))]
    return chk("windows_emit_analysis", not bad, f"non-honest: {len(bad)}")


def test_blind_declared():
    _a, wa = _clean()
    ok = "stiffness_to_z" in wa.posture()["blind"]
    return chk("blind_declared", ok, f"blind={wa.posture()['blind']}")


def test_custom_probe():
    rng = random.Random(7)
    rows = []
    for _ in range(N):
        legit = rng.randrange(3)
        diag = rng.gauss(0.0, 1.0)
        ynext = float(legit) + 1.6 * diag       # ynext leaks from the diagnostic beyond the legit driver
        rows.append({"diag": diag, "ynext": ynext, "legit": float(legit), "cand": float(rng.randrange(3))})
    probe = CouplingProbe("my_leak", "customer probe", "diag", "ynext", ("legit",), ("cand",), True)
    wa = KernelAuditor(probes=(probe,), window=N).audit(rows)[0]
    ok = "my_leak" in wa.posture()["contaminated"]
    return chk("custom_probe", ok, f"posture={wa.posture()}")


def test_determinism():
    _a1, wa1 = _dirty()
    _a2, wa2 = _dirty()
    ok = wa1.posture() == wa2.posture()
    return chk("determinism", ok, f"posture repeats: {ok}")


def test_ledger_honest():
    a, _wa = _clean()
    ok = audit_ledger(a.ledger())["honest"]
    return chk("ledger_honest", ok, f"honest={ok}")


def main():
    results = [
        test_clean_certifies(),
        test_contaminated_refused(),
        test_posture_no_scalar(),
        test_windows_emit_analysis(),
        test_blind_declared(),
        test_custom_probe(),
        test_determinism(),
        test_ledger_honest(),
    ]
    print("test_kernel_auditor — product API (chokepoints + domain-agnostic custom probe)\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. observation ≠ authority; undetected ≠ absent; integrity ≠ truth.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
