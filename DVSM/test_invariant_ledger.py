# SPDX-License-Identifier: AGPL-3.0-only
"""
test_invariant_ledger.py — the manifest obligations are checked, graded honestly, and CATCH the real ghosts
(κ not skew, energy-law not a discrete proof) rather than rubber-stamping them. Validity-not-outcome.

  1. kappa_ghost_caught     — κ skew-symmetry obligation is VIOLATED with a witness pair (the comment is false).
  2. energy_law_rejected    — the energy law is REJECTED_AS_PROOF for the discrete kernel (not CLOSED).
  3. containment_bounded    — a clean trace ⇒ containment obligation BOUNDED (empirical, not CLOSED).
  4. lambda_separates       — clean ⇒ λ-constant CLOSED; a ν→λ trace ⇒ VIOLATED.
  5. observability_separates— clean ⇒ separation CLOSED; an Ω→V trace ⇒ VIOLATED.
  6. determinism_closed     — replay-hash determinism obligation is CLOSED.
  7. obligations_emit_analysis — every obligation projects to an honest AnalysisResult.
  8. ledger_honest          — obligation claims form an honest claim_ledger.

Sound iff 8/8: the ledger neither hides the ghosts nor over-certifies (no VIOLATED dressed as CLOSED).
`integrity ≠ truth`; `REJECTED_AS_PROOF ≠ FALSE`.
"""
from __future__ import annotations

from invariant_ledger import (evaluate, obl_kappa_skew, obl_energy_law, obl_lambda_constant,
                              obl_observability_separation, obl_determinism)
from dvsm_reference import gen_clean, gen_contaminated
from artifacts import AnalysisResult, Limitation
from claim_ledger import audit_ledger

N = 6000


def chk(name, ok, detail):
    return (name, ok, detail)


def test_kappa_ghost_caught():
    o = obl_kappa_skew()
    return chk("kappa_ghost_caught", o.status == "VIOLATED", f"status={o.status} witness={o.witness}")


def test_energy_law_rejected():
    o = obl_energy_law(gen_clean(2000))
    return chk("energy_law_rejected", o.status == "REJECTED_AS_PROOF", f"status={o.status}")


def test_containment_bounded():
    o = [x for x in evaluate(gen_clean(3000)) if x.id == "containment_boundedness"][0]
    return chk("containment_bounded", o.status == "BOUNDED", f"status={o.status} witness={o.witness}")


def test_lambda_separates():
    clean = obl_lambda_constant(gen_clean(N, seed=1)).status
    dirty = obl_lambda_constant(gen_contaminated("novelty_to_lambda", N, seed=2)).status
    ok = clean == "CLOSED" and dirty == "VIOLATED"
    return chk("lambda_separates", ok, f"clean={clean} contaminated={dirty}")


def test_observability_separates():
    clean = obl_observability_separation(gen_clean(N, seed=1)).status
    dirty = obl_observability_separation(gen_contaminated("omega_to_v", N, seed=2)).status
    ok = clean == "CLOSED" and dirty == "VIOLATED"
    return chk("observability_separates", ok, f"clean={clean} contaminated={dirty}")


def test_determinism_closed():
    o = obl_determinism()
    return chk("determinism_closed", o.status == "CLOSED", f"status={o.status}")


def test_obligations_emit_analysis():
    obs = evaluate(gen_clean(2000))
    bad = [o.id for o in obs if not (isinstance(o.as_analysis(), AnalysisResult)
           and o.as_analysis().scope and len(o.as_analysis().limitations) >= 1
           and all(isinstance(l, Limitation) for l in o.as_analysis().limitations))]
    return chk("obligations_emit_analysis", not bad, f"non-honest: {bad or 'none'}")


def test_ledger_honest():
    ledger = [o.as_claim() for o in evaluate(gen_clean(2000))]
    ok = audit_ledger(ledger)["honest"]
    return chk("ledger_honest", ok, f"claim ledger honest={ok}")


def main():
    results = [
        test_kappa_ghost_caught(),
        test_energy_law_rejected(),
        test_containment_bounded(),
        test_lambda_separates(),
        test_observability_separates(),
        test_determinism_closed(),
        test_obligations_emit_analysis(),
        test_ledger_honest(),
    ]
    print("test_invariant_ledger — manifest obligations catch the ghosts, grade honestly\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. integrity ≠ truth; REJECTED_AS_PROOF ≠ FALSE; "
          f"empirical-boundedness ≠ certified.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
