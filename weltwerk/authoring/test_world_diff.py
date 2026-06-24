# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_diff.py — Phase 8 proofs (validity-not-outcome): the consequence diff is correct and honest.

  1. identical_is_empty        — comparing a world to itself ⇒ no change, verdict 'unchanged'
  2. redundancy_removes_spof   — adding a path around a mediator removes a SPOF ⇒ resilience 'increased'
  3. added_coupling_is_riskier — giving one node more reach raises peak blast ⇒ resilience 'decreased'
  4. conflicting_signals_mixed — SPOF falls but peak blast rises ⇒ verdict 'mixed' (NOT a forced binary)
  5. loops_created_detected    — adding a back-edge creates a feedback loop ⇒ loops_created non-empty
  6. relations_diff_symmetry   — added(A→B) == removed(B→A) for relations and entities
  7. determinism              — same inputs ⇒ identical diff

Run:  PYTHONHASHSEED=0 python3 test_world_diff.py
"""
from __future__ import annotations

from world_diff import compare_worlds

CHAIN = """
world "Chain"
entity reactor:
  feeds power
entity power:
  feeds gate
entity gate:
  health 1
"""
CHAIN_REDUNDANT = """
world "ChainR"
entity reactor:
  feeds power
  feeds gate
entity power:
  feeds gate
entity gate:
  health 1
"""
SPARSE = """
world "Sparse"
entity hub:
  feeds a
entity a:
  health 1
entity b:
  health 1
entity c:
  health 1
"""
COUPLED = """
world "Coupled"
entity hub:
  feeds a
  feeds b
  feeds c
entity a:
  health 1
entity b:
  health 1
entity c:
  health 1
"""
# SPOF falls (redundant path around `power`) while a separate hub `x` gains reach (peak blast rises).
MIXED_OLD = """
world "MixedOld"
entity reactor:
  feeds power
entity power:
  feeds gate
entity gate:
  health 1
entity x:
  health 1
entity y:
  health 1
"""
MIXED_NEW = """
world "MixedNew"
entity reactor:
  feeds power
  feeds gate
entity power:
  feeds gate
entity gate:
  health 1
entity x:
  feeds y
  feeds gate
  feeds power
entity y:
  health 1
"""
DAG = """
world "Dag"
entity a:
  feeds b
entity b:
  feeds c
entity c:
  health 1
"""
CYCLE = """
world "Cyc"
entity a:
  feeds b
entity b:
  feeds c
entity c:
  feeds a
"""


def check(name, ok, detail):
    return (name, ok, detail)


def test_identical_is_empty():
    d = compare_worlds(CHAIN, CHAIN)
    ok = (not d["entities_added"] and not d["entities_removed"] and not d["relations_added"]
          and not d["relations_removed"] and d["verdict"]["resilience"] == "unchanged")
    return check("identical_is_empty", ok, f"verdict={d['verdict']['resilience']}, rels±={len(d['relations_added'])}/{len(d['relations_removed'])}")


def test_redundancy_removes_spof():
    d = compare_worlds(CHAIN, CHAIN_REDUNDANT)
    ok = ("power" in d["spofs_before"] and d["spofs_after"] == []
          and ("reactor", "feeds", "gate") in d["relations_added"]
          and d["verdict"]["resilience"] == "increased")
    return check("redundancy_removes_spof", ok,
                 f"SPOFs {d['spofs_before']}→{d['spofs_after']}, verdict={d['verdict']['resilience']}")


def test_added_coupling_is_riskier():
    d = compare_worlds(SPARSE, COUPLED)
    ok = d["coupling_delta"] > 0 and d["verdict"]["resilience"] == "decreased"
    return check("added_coupling_is_riskier", ok,
                 f"peak {d['peak_blast_before']}→{d['peak_blast_after']}, verdict={d['verdict']['resilience']}")


def test_conflicting_signals_mixed():
    d = compare_worlds(MIXED_OLD, MIXED_NEW)
    ok = (d["spof_count_delta"] < 0 and d["coupling_delta"] > 0
          and d["verdict"]["resilience"] == "mixed")
    return check("conflicting_signals_mixed", ok,
                 f"spofΔ={d['spof_count_delta']}, peakΔ={d['coupling_delta']}, verdict={d['verdict']['resilience']}")


def test_loops_created_detected():
    d = compare_worlds(DAG, CYCLE)
    created = d["loops_created"]
    ok = len(created) == 1 and set(created[0]) == {"a", "b", "c"}
    return check("loops_created_detected", ok, f"loops_created={created}")


def test_relations_diff_symmetry():
    ab = compare_worlds(CHAIN, CHAIN_REDUNDANT)
    ba = compare_worlds(CHAIN_REDUNDANT, CHAIN)
    ok = (ab["relations_added"] == ba["relations_removed"]
          and ab["relations_removed"] == ba["relations_added"]
          and ab["entities_added"] == ba["entities_removed"])
    return check("relations_diff_symmetry", ok, f"added(A→B)==removed(B→A): {ab['relations_added']==ba['relations_removed']}")


def test_determinism():
    a = compare_worlds(MIXED_OLD, MIXED_NEW)
    b = compare_worlds(MIXED_OLD, MIXED_NEW)
    return check("determinism", a == b, f"same inputs ⇒ identical diff: {a == b}")


def main():
    results = [
        test_identical_is_empty(),
        test_redundancy_removes_spof(),
        test_added_coupling_is_riskier(),
        test_conflicting_signals_mixed(),
        test_loops_created_detected(),
        test_relations_diff_symmetry(),
        test_determinism(),
    ]
    print("test_world_diff — Phase 8: the consequence diff (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: identical worlds diff to nothing,"
          f"\n  redundancy removes a SPOF (resilience up), added coupling raises peak blast (down), conflicting"
          f"\n  signals stay 'mixed' rather than forced, new loops are detected, the diff is symmetric and deterministic.")
    assert passed == total, f"{total - passed} check(s) failed — the consequence diff is not sound"


if __name__ == "__main__":
    main()
