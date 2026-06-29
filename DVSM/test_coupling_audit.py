# SPDX-License-Identifier: AGPL-3.0-only
"""
test_coupling_audit.py — the forbidden-coupling firewall separates an air-gapped trace from a contaminated
one, reports honestly, and states where it is blind. Validity-not-outcome. Pure-stdlib (~tens of seconds).

  1. clean_air_gap          — a clean trace ⇒ every IDENTIFIABLE coupling reads AIR_GAP_HELD.
  2. omega_detected         — planting Ω→V ⇒ OBSERVER_CONTAMINATION.
  3. novelty_detected       — planting ν→λ ⇒ OBSERVER_CONTAMINATION.
  4. results_emit_analysis  — every CouplingResult.as_analysis() is an AnalysisResult (scope + ≥1 limitation).
  5. claims_honest          — per-coupling claims form an honest claim_ledger (graded + falsifiable).
  6. unidentifiable_flagged — stiffness→z stays UNIDENTIFIABLE even when planted (no false positive).
  7. panel_no_scalar        — audit_all returns one witness per coupling; no fused confidence/score field.
  8. determinism            — re-auditing a trace agrees.

Sound iff 8/8: leaks are caught, the air-gap reads clean, blindness is declared, the panel stays plural.
`borrow-checker-clean ≠ air-gap-sound`; `residual-CMI ≠ channel`; `undetected ≠ absent`.
"""
from __future__ import annotations

from dataclasses import fields

from coupling_audit import (audit_coupling, audit_all, COUPLINGS, _BY_NAME, CouplingResult)
from dvsm_reference import gen_clean, gen_contaminated
from artifacts import AnalysisResult, Limitation
from claim_ledger import audit_ledger

N = 6000


def chk(name, ok, detail):
    return (name, ok, detail)


def test_clean_air_gap():
    trace = gen_clean(N, seed=1)
    res = [audit_coupling(trace, c, seed=11) for c in COUPLINGS if c.identifiable]
    ok = all(r.verdict == "AIR_GAP_HELD" for r in res)
    return chk("clean_air_gap", ok, f"verdicts={[r.verdict for r in res]}")


def test_omega_detected():
    r = audit_coupling(gen_contaminated("omega_to_v", N, seed=2), _BY_NAME["omega_to_v"], seed=22)
    return chk("omega_detected", r.verdict == "OBSERVER_CONTAMINATION", f"verdict={r.verdict} cmi={r.result.cmi:.3f}")


def test_novelty_detected():
    r = audit_coupling(gen_contaminated("novelty_to_lambda", N, seed=2), _BY_NAME["novelty_to_lambda"], seed=22)
    return chk("novelty_detected", r.verdict == "OBSERVER_CONTAMINATION", f"verdict={r.verdict} cmi={r.result.cmi:.3f}")


def test_results_emit_analysis():
    res = audit_all(gen_clean(N, seed=1), seed=11)
    bad = [r.name for r in res if not (isinstance(r.as_analysis(), AnalysisResult)
           and r.as_analysis().scope and len(r.as_analysis().limitations) >= 1
           and all(isinstance(l, Limitation) for l in r.as_analysis().limitations))]
    return chk("results_emit_analysis", not bad, f"non-honest: {bad or 'none'}")


def test_claims_honest():
    res = audit_all(gen_clean(N, seed=1), seed=11)
    ledger = [r.as_claim() for r in res]
    ok = audit_ledger(ledger)["honest"]
    return chk("claims_honest", ok, f"claim ledger honest={ok}")


def test_unidentifiable_flagged():
    spec = _BY_NAME["stiffness_to_z"]
    # even with the coupling PLANTED, the firewall declines to rule (UNIDENTIFIABLE), not a false positive
    r = audit_coupling(gen_contaminated("stiffness_to_z", N, seed=2), spec, seed=22)
    has_lim = any(l.scope == "identifiability" for l in r.as_analysis().limitations)
    ok = (not spec.identifiable) and has_lim and r.verdict == "UNIDENTIFIABLE"
    return chk("unidentifiable_flagged", ok, f"verdict={r.verdict} limitation_present={has_lim}")


def test_panel_no_scalar():
    res = audit_all(gen_clean(N, seed=1), seed=11)
    names = {f.name for f in fields(CouplingResult)}
    ok = isinstance(res, list) and len(res) == len(COUPLINGS) and not (names & {"score", "confidence", "fused"})
    return chk("panel_no_scalar", ok, f"{len(res)} witnesses; no scalar field={not (names & {'score','confidence','fused'})}")


def test_determinism():
    trace = gen_contaminated("novelty_to_lambda", N, seed=2)
    a = audit_coupling(trace, _BY_NAME["novelty_to_lambda"], seed=22).verdict
    b = audit_coupling(trace, _BY_NAME["novelty_to_lambda"], seed=22).verdict
    return chk("determinism", a == b, f"repeated verdict agrees: {a == b}")


def main():
    results = [
        test_clean_air_gap(),
        test_omega_detected(),
        test_novelty_detected(),
        test_results_emit_analysis(),
        test_claims_honest(),
        test_unidentifiable_flagged(),
        test_panel_no_scalar(),
        test_determinism(),
    ]
    print("test_coupling_audit — forbidden-coupling firewall (both directions, plural panel)\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. borrow-checker-clean ≠ air-gap-sound; residual-CMI ≠ channel; "
          f"undetected ≠ absent.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
