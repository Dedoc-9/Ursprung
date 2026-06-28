# SPDX-License-Identifier: AGPL-3.0-only
"""
test_telemetry_audit.py — the telemetry engine separates the three cases (validity-not-outcome). Pure-stdlib.

  1. healthy_is_healthy        — control-confounded coupling only ⇒ HEALTHY (I(X;Y|Z) ≈ null).
  2. fault_is_fault            — a real X→Y channel survives conditioning on (Z,W) ⇒ FAULT.
  3. misspec_not_fault         — a MISSING confounder W is NOT flagged as a fault: I(X;Y|Z) elevated but
                                I(X;Y|Z,W) ≈ null ⇒ SENSOR_MISSPEC. This is the hard, decisive case.
  4. correlation_is_not_fault  — I(X;Y) is large in every case (control-driven); it alone never decides.
  5. as_analysis_honest        — the result projects to an AnalysisResult with scope + ≥1 limitation.
  6. determinism               — repeated diagnosis agrees.

Sound iff 6/6: the engine flags a fault only when residual dependence survives conditioning on the complete
MODELED state, and refuses to call a missing-confounder a fault. `residual-CMI ≠ fault`;
`proves-the-procedure ≠ proves-the-fault`.

Run:  python3 test_telemetry_audit.py
"""
from __future__ import annotations

from telemetry_audit import diagnose, gen_healthy, gen_fault, gen_sensor_misspec
from artifacts import AnalysisResult, Limitation


def chk(name, ok, detail):
    return (name, ok, detail)


_H = diagnose(gen_healthy())
_F = diagnose(gen_fault())
_M = diagnose(gen_sensor_misspec())


def test_healthy_is_healthy():
    ok = _H.decision == "HEALTHY"
    return chk("healthy_is_healthy", ok, f"{_H.decision}  I(X;Y|Z)={_H.cmi_Z:.4f}≈null {_H.null_Z:.4f}")


def test_fault_is_fault():
    ok = _F.decision == "FAULT" and _F.cmi_ZW > _F.null_ZW + 0.03
    return chk("fault_is_fault", ok, f"{_F.decision}  I(X;Y|Z,W)={_F.cmi_ZW:.4f} (survives conditioning)")


def test_misspec_not_fault():
    ok = _M.decision == "SENSOR_MISSPEC" and _M.cmi_Z > _M.null_Z + 0.03 and _M.cmi_ZW < _M.null_ZW + 0.03
    return chk("misspec_not_fault", ok,
               f"{_M.decision}  I(X;Y|Z)={_M.cmi_Z:.3f} elevated, I(X;Y|Z,W)={_M.cmi_ZW:.4f} dissolved")


def test_correlation_is_not_fault():
    ok = _H.mi > 0.05 and _M.mi > 0.05 and _H.decision == "HEALTHY"   # big I(X;Y) yet healthy ⇒ MI alone ≠ fault
    return chk("correlation_is_not_fault", ok, f"healthy I(X;Y)={_H.mi:.3f}>0 yet decision={_H.decision}")


def test_as_analysis_honest():
    a = _F.as_analysis()
    ok = (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
          and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations))
    return chk("as_analysis_honest", ok, f"scope={a.scope!r} limitations={len(a.limitations)}")


def test_determinism():
    ok = diagnose(gen_fault()).decision == _F.decision
    return chk("determinism", ok, f"repeated diagnosis agrees: {ok}")


def main():
    results = [test_healthy_is_healthy(), test_fault_is_fault(), test_misspec_not_fault(),
              test_correlation_is_not_fault(), test_as_analysis_honest(), test_determinism()]
    print("test_telemetry_audit — fault vs sensor-misspec vs healthy\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a fault is flagged only when residual "
          f"dependence survives\n  conditioning on the complete MODELED (Z,W); a missing confounder is NOT called "
          f"a fault; correlation\n  alone never decides. residual-CMI ≠ fault; proves-the-procedure ≠ proves-the-fault.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
