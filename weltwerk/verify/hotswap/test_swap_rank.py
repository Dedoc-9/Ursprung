# SPDX-License-Identifier: AGPL-3.0-only
"""
test_swap_rank.py — PO-12 proofs (validity-not-outcome). Pure-stdlib.

  1. learned_beats_canonical  — at EQUAL budget, the learned plan-ordering reaches a successful swap with less
                                verified work and dominates the canonical ordering at every budget. (PO-6.)
  2. minimal_success_is_both  — the minimal successful plan is exactly {MBB, ALIGN} (overdetermined target).
  3. useful_guards_correct    — the two real guards are flagged useful; the decoys are not.
  4. no_false_restore         — success ⟺ the FROZEN checker is CLOSED ∧ migrated AND the oracle agrees; a
                                naive one-guard plan is NOT a success. The policy cannot declare a swap done.
  5. as_analysis_honest       — a plan's projection is an AnalysisResult with scope + ≥1 limitation + findings.
  6. determinism              — repeated equal-budget runs agree.

Sound iff 6/6: the improvement is ORDERING (which plans to try), the criterion is the frozen verdict, and a
plan is never "restored" except by CLOSED ∧ migrated. `improved_map ≠ changed_criterion`; `candidate ≠ deployed-swap`.

Run:  python3 test_swap_rank.py
"""
from __future__ import annotations

from swap_rank import (equal_budget, useful_guards, success, as_analysis, candidate_plans)
from swap_relation import swap_oracle, SwapModelChecker
from artifacts import AnalysisResult, Limitation

CHK = SwapModelChecker()
_R = equal_budget()


def chk(name, ok, detail):
    return (name, ok, detail)


def test_learned_beats_canonical():
    ok = (_R["work_learned"] < _R["work_canonical"] and _R["anytime_dominance"] and _R["strict_gain"])
    return chk("learned_beats_canonical", ok,
               f"work learned={_R['work_learned']} < canonical={_R['work_canonical']}; "
               f"anytime={_R['anytime_dominance']} strict={_R['strict_gain']}")


def test_minimal_success_is_both():
    ok = _R["minimal_success"] == ["ALIGN", "MBB"]
    return chk("minimal_success_is_both", ok, f"minimal successful plan = {_R['minimal_success']}")


def test_useful_guards_correct():
    u = useful_guards()
    ok = u == {"MBB", "ALIGN"}
    return chk("useful_guards_correct", ok, f"useful guards = {sorted(u)} (decoys excluded)")


def test_no_false_restore():
    bad = []
    for p in candidate_plans():
        s = success(p)
        v = CHK.run(p, 8)
        o = swap_oracle(p)
        frozen_ok = (v.status == "CLOSED" and v.goal_reachable and o["status"] == "CLOSED" and o["goal"])
        if s != frozen_ok:
            bad.append(sorted(p))
    naive_not_success = not success(frozenset({"MBB"})) and not success(frozenset({"ALIGN"}))
    ok = not bad and naive_not_success
    return chk("no_false_restore", ok,
               f"success⟺frozen CLOSED∧goal (mismatches: {bad or 'none'}); naive-guard-not-success={naive_not_success}")


def test_as_analysis_honest():
    a = as_analysis(frozenset({"MBB", "ALIGN"}))
    ok = (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
          and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations)
          and len(a.findings) >= 1)
    return chk("as_analysis_honest", ok,
               f"AnalysisResult scope={a.scope!r} limitations={len(a.limitations)} findings={len(a.findings)}")


def test_determinism():
    ok = equal_budget() == _R
    return chk("determinism", ok, f"repeated equal-budget run agrees: {ok}")


def main():
    results = [
        test_learned_beats_canonical(),
        test_minimal_success_is_both(),
        test_useful_guards_correct(),
        test_no_false_restore(),
        test_as_analysis_honest(),
        test_determinism(),
    ]
    print("test_swap_rank — PO-12: swap planning as ordering under the frozen verifier\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the learned ordering wins at equal budget, "
          f"the safe\n  plan is overdetermined ({{MBB,ALIGN}}), and success is the FROZEN CLOSED∧migrated verdict — "
          f"never the\n  policy's claim. improved_map ≠ changed_criterion; candidate ≠ deployed-swap.")
    assert passed == total, f"{total - passed} check(s) failed — PO-12 ordering/criterion separation not established"


if __name__ == "__main__":
    main()
