# SPDX-License-Identifier: AGPL-3.0-only
"""
test_repair.py — Phase C.2 proofs (validity-not-outcome): repair candidates are honest, seeded only from
evidence, and never overstate. Uses the explicit engine (pure-stdlib).

  1. critical_produces_candidate — a ghost's critical event yields a REMOVE_EVENT candidate
  2. trace_restoration           — the candidate's restores_trace holds (reduced replay is clean)
  3. non_critical_rejected       — removing a redundant event gives restores_trace=False; propose excludes it
  4. restores_world_proven       — forbidding the sole-cause action ⇒ RESTORED_PROVEN (CLOSED, no violation)
  5. still_violated_overdetermined — forbidding one of several sufficient causes ⇒ STILL_VIOLATED
  6. bounded_honesty             — restores_world is an enum carrying (engine, bound); never a bare bool, no fixed/safe
  7. as_analysis_contract        — candidate projects to AnalysisResult with ≥1 limitation incl. "candidate, not a fix"
  8. records_frozen              — RepairCandidate / RepairChange / WorldRepairEvidence are immutable

Run:  python3 test_repair.py
"""
from __future__ import annotations

import dataclasses

from repair import propose, evaluate_removal, RepairCandidate, RepairChange, WorldRepairEvidence
from counterfactual import _trajectory_violates
from artifacts import normalize_invariants, AnalysisResult, Limitation
from kernel_check import check

SMALL = """
world "T"
entity faction_a:
  position 0 0 0
  controls hub
entity hub:
  position 1 0 0
  health 10
  powers leaf
entity leaf:
  position 2 0 0
  health 10
"""

# a → b ; destroying a DISABLES b (cascade). Only destroy(a) can disable b.
ONELINK = """
world "L"
entity fa:
  position 0 0 0
  controls a
entity a:
  position 1 0 0
  health 10
  powers b
entity b:
  position 2 0 0
  health 10
"""

NEVER = {"nothing_ever_destroyed": (lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime))}
B_NOT_DISABLED = {"b_not_disabled": (lambda sim: sim.runtime["b"]["status"] != "disabled")}


def chk(name, ok, detail):
    return (name, ok, detail)


def test_critical_produces_candidate():
    g = check(ONELINK, max_depth=3, invariants=B_NOT_DISABLED).ghost
    cands = propose(ONELINK, g.path, B_NOT_DISABLED, check_world=False)
    ok = (len(cands) == 1 and cands[0].change.kind == "REMOVE_EVENT"
          and cands[0].change.target == ("destroy", "a") and cands[0].restores_trace)
    return chk("critical_produces_candidate", ok, f"candidates={[c.change.target for c in cands]}")


def test_trace_restoration():
    g = check(ONELINK, max_depth=3, invariants=B_NOT_DISABLED).ghost
    cand = propose(ONELINK, g.path, B_NOT_DISABLED, check_world=False)[0]
    reduced = tuple(e for e in g.path if tuple(e) != cand.change.target)
    ok = cand.restores_trace and not _trajectory_violates(ONELINK, reduced, normalize_invariants(B_NOT_DISABLED))
    return chk("trace_restoration", ok, f"restores_trace={cand.restores_trace}, reduced clean={ok}")


def test_non_critical_rejected():
    trace = [("destroy", "a"), ("destroy", "b")]            # destroy b is redundant for b_not_disabled
    cand_b = evaluate_removal(ONELINK, trace, ("destroy", "b"), B_NOT_DISABLED, check_world=False)
    proposed = [c.change.target for c in propose(ONELINK, trace, B_NOT_DISABLED, check_world=False)]
    ok = (cand_b.restores_trace is False) and (("destroy", "b") not in proposed)
    return chk("non_critical_rejected", ok, f"removing destroy-b restores_trace={cand_b.restores_trace}; proposed={proposed}")


def test_restores_world_proven():
    g = check(ONELINK, max_depth=3, invariants=B_NOT_DISABLED).ghost
    cand = propose(ONELINK, g.path, B_NOT_DISABLED, bound=8)[0]
    ok = cand.restores_world == "RESTORED_PROVEN" and cand.world_evidence.status == "CLOSED"
    return chk("restores_world_proven", ok, f"restores_world={cand.restores_world} status={cand.world_evidence.status}")


def test_still_violated_overdetermined():
    g = check(SMALL, max_depth=3, invariants=NEVER).ghost     # ghost: destroy hub; but destroy leaf also violates
    cand = propose(SMALL, g.path, NEVER, bound=4)[0]
    ok = cand.restores_world == "STILL_VIOLATED" and cand.restores_trace
    return chk("still_violated_overdetermined", ok,
               f"restores_trace={cand.restores_trace} restores_world={cand.restores_world}")


def test_bounded_honesty():
    g = check(ONELINK, max_depth=3, invariants=B_NOT_DISABLED).ghost
    cand = propose(ONELINK, g.path, B_NOT_DISABLED, bound=8)[0]
    enum_ok = cand.restores_world in {"RESTORED_PROVEN", "RESTORED_WITHIN_BOUND", "STILL_VIOLATED", "NOT_CHECKED"}
    carries = isinstance(cand.world_evidence, WorldRepairEvidence) and bool(cand.world_evidence.engine) and cand.world_evidence.bound == 8
    no_overclaim = not any(hasattr(cand, a) for a in ("fixed", "safe", "correct", "world_safe"))
    ok = enum_ok and carries and no_overclaim
    return chk("bounded_honesty", ok, f"restores_world={cand.restores_world} engine={cand.world_evidence.engine} bound={cand.world_evidence.bound} no_overclaim={no_overclaim}")


def test_as_analysis_contract():
    g = check(ONELINK, max_depth=3, invariants=B_NOT_DISABLED).ghost
    a = propose(ONELINK, g.path, B_NOT_DISABLED, bound=8)[0].as_analysis()
    ok = (isinstance(a, AnalysisResult) and len(a.limitations) >= 1
          and any("candidate" in l.claim and "not a fix" in l.claim for l in a.limitations))
    return chk("as_analysis_contract", ok, f"limitations={[l.claim for l in a.limitations]}")


def test_records_frozen():
    g = check(ONELINK, max_depth=3, invariants=B_NOT_DISABLED).ghost
    cand = propose(ONELINK, g.path, B_NOT_DISABLED, bound=8)[0]
    frozen = 0
    for obj, fld, val in [(cand, "restores_trace", False), (cand.change, "kind", "X"),
                          (cand.world_evidence, "bound", 1)]:
        try:
            setattr(obj, fld, val)
        except dataclasses.FrozenInstanceError:
            frozen += 1
    return chk("records_frozen", frozen == 3, f"RepairCandidate/Change/Evidence immutable: {frozen == 3}")


def main():
    results = [
        test_critical_produces_candidate(),
        test_trace_restoration(),
        test_non_critical_rejected(),
        test_restores_world_proven(),
        test_still_violated_overdetermined(),
        test_bounded_honesty(),
        test_as_analysis_contract(),
        test_records_frozen(),
    ]
    print("test_repair — Phase C.2: repair candidates (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: candidates are seeded only from critical "
          f"events,\n  restores_trace is honest (non-critical ⇒ False), restores_world is an enum carrying "
          f"(engine, bound)\n  with RESTORED_PROVEN vs STILL_VIOLATED distinguished, no fixed/safe overclaim, "
          f"and records are frozen.\n  candidate ≠ repair; restores-under-(M,E,K) ≠ world-safe.")
    assert passed == total, f"{total - passed} check(s) failed — repair candidates are not honest"


if __name__ == "__main__":
    main()
