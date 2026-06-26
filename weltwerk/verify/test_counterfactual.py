# SPDX-License-Identifier: AGPL-3.0-only
"""
test_counterfactual.py — Phase C proofs (validity-not-outcome): trace-level counterfactual ablation is sound
and honest. Pure-stdlib (no solver).

  1. single_event_critical    — a length-1 ghost's only event is critical
  2. overdetermined_no_single — two independent sufficient causes ⇒ NO single critical event (both redundant)
  3. mixed_critical_redundant — a trace with one critical + one redundant event is split correctly
  4. critical_removal_prevents— every event flagged critical, when removed, truly yields no violation
  5. clean_trace_flagged      — a non-violating trace is reported as nothing-to-explain (not a false ghost)
  6. from_result_consumes_artifact — analyzing a VIOLATED VerificationResult (any engine) finds the cause
  7. determinism              — two analyses agree
  8. records_frozen           — Counterfactual / CounterfactualReport are immutable

Run:  python3 test_counterfactual.py
"""
from __future__ import annotations

import dataclasses

from counterfactual import analyze, from_result, Counterfactual, CounterfactualReport
from engine import build_model, VerificationOptions, ExplicitStateBFSEngine
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

# hub→leaf plus an independent 'decoy' that does not affect leaf
MIXED = """
world "M"
entity fa:
  position 0 0 0
  controls hub
entity hub:
  position 1 0 0
  health 10
  powers leaf
entity leaf:
  position 2 0 0
  health 10
entity decoy:
  position 3 0 0
  health 10
"""

NEVER = {"nothing_ever_destroyed": (lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime))}
LEAF_OK = {"leaf_ok": (lambda sim: sim.runtime["leaf"]["alive"] and sim.runtime["leaf"]["status"] == "ok")}


def chk(name, ok, detail):
    return (name, ok, detail)


def test_single_event_critical():
    g = check(SMALL, max_depth=3, invariants=NEVER).ghost
    rep = analyze(SMALL, g.path, NEVER)
    ok = len(rep.critical) == 1 and len(rep.redundant) == 0 and rep.input_violates
    return chk("single_event_critical", ok, f"critical={list(rep.critical)} redundant={list(rep.redundant)}")


def test_overdetermined_no_single():
    # both destroys independently violate "nothing destroyed" ⇒ neither alone is critical
    rep = analyze(SMALL, [("destroy", "hub"), ("destroy", "leaf")], NEVER)
    ok = rep.input_violates and len(rep.critical) == 0 and len(rep.redundant) == 2
    return chk("overdetermined_no_single", ok, f"critical={list(rep.critical)} redundant={len(rep.redundant)}")


def test_mixed_critical_redundant():
    rep = analyze(MIXED, [("destroy", "decoy"), ("destroy", "hub")], LEAF_OK)
    ok = (rep.input_violates and rep.critical == (("destroy", "hub"),)
          and rep.redundant == (("destroy", "decoy"),))
    return chk("mixed_critical_redundant", ok, f"critical={list(rep.critical)} redundant={list(rep.redundant)}")


def test_critical_removal_prevents():
    from counterfactual import _trajectory_violates
    from artifacts import normalize_invariants
    rep = analyze(MIXED, [("destroy", "decoy"), ("destroy", "hub")], LEAF_OK)
    invs = normalize_invariants(LEAF_OK)
    ok = True
    for crit in rep.critical:
        reduced = [e for e in rep.ghost_trace if e != crit]
        if _trajectory_violates(MIXED, reduced, invs):     # removing a 'critical' event must clear it
            ok = False
    return chk("critical_removal_prevents", ok, f"each critical event's removal clears the violation: {ok}")


def test_clean_trace_flagged():
    rep = analyze(SMALL, [("repair", "hub")], NEVER)        # no destroy ⇒ never_destroyed holds
    ok = (not rep.input_violates) and rep.critical == () and "no violation" in (rep.note or "")
    return chk("clean_trace_flagged", ok, f"input_violates={rep.input_violates} note={rep.note!r}")


def test_from_result_consumes_artifact():
    vr = ExplicitStateBFSEngine().verify(build_model(SMALL, invariants=NEVER), VerificationOptions(depth_bound=3))
    rep = from_result(SMALL, vr, NEVER)
    ok = vr.status == "VIOLATED" and len(rep.critical) >= 1
    return chk("from_result_consumes_artifact", ok, f"status={vr.status} critical={list(rep.critical)}")


def test_determinism():
    a = analyze(MIXED, [("destroy", "decoy"), ("destroy", "hub")], LEAF_OK)
    b = analyze(MIXED, [("destroy", "decoy"), ("destroy", "hub")], LEAF_OK)
    ok = (a.critical, a.redundant) == (b.critical, b.redundant)
    return chk("determinism", ok, f"identical split: {ok}")


def test_records_frozen():
    rep = analyze(SMALL, [("destroy", "hub")], NEVER)
    frozen = 0
    for obj, fld, val in [(rep, "critical", ()), (rep.analyses[0], "index", 9)]:
        try:
            setattr(obj, fld, val)
        except dataclasses.FrozenInstanceError:
            frozen += 1
    return chk("records_frozen", frozen == 2, f"report + Counterfactual immutable: {frozen == 2}")


def main():
    results = [
        test_single_event_critical(),
        test_overdetermined_no_single(),
        test_mixed_critical_redundant(),
        test_critical_removal_prevents(),
        test_clean_trace_flagged(),
        test_from_result_consumes_artifact(),
        test_determinism(),
        test_records_frozen(),
    ]
    print("test_counterfactual — Phase C: critical events in ghost traces (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a sole cause is found critical, an "
          f"overdetermined\n  ghost honestly yields NO single critical event, mixed traces split correctly, "
          f"removing a critical\n  event truly clears the violation, clean traces are flagged, and the report "
          f"is immutable.\n  prevents-this-ghost ≠ makes-world-safe.")
    assert passed == total, f"{total - passed} check(s) failed — counterfactual ablation is not sound"


if __name__ == "__main__":
    main()
