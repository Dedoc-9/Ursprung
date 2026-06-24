# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_edit.py — Phase 11 proofs (validity-not-outcome): live edit = NEW authority, done honestly.

  1. edit_updates_graph         — a topology edit yields a new graph (new reachability)
  2. edit_updates_power_path    — the new power path is reachable in the rebuilt authority
  3. edit_removes_spof          — adding a redundant path removes a SPOF (consequences report it)
  4. edit_updates_factions      — an ownership edit flips control/territory (re-derived, not spliced)
  5. camera_inventory_preserved — player state (carry) passes through an edit untouched
  6. invalid_edit_rejected      — an edit that fails the pre-play gate is REJECTED, not silently rebuilt
  7. parse_error_rejected       — unparseable text is rejected; old authority stands
  8. diff_deterministic         — same edit ⇒ identical consequences
  9. explain_runtime            — runtime 'why' answers come from the alive-graph authority

Run:  PYTHONHASHSEED=0 python3 test_world_edit.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
from world_edit import DEMO_NEW, DEMO_OLD, apply_edit, explain
from world_sim import WorldSim

TERR_OLD = """
world "T"
entity faction_red:
  controls reactor
entity faction_blue:
  controls market
entity reactor:
  feeds zone_a
entity market:
  feeds zone_b
entity zone_a:
  health 1
entity zone_b:
  health 1
"""
TERR_NEW = """
world "T"
entity faction_red:
  controls market
entity faction_blue:
  controls reactor
entity reactor:
  feeds zone_a
entity market:
  feeds zone_b
entity zone_a:
  health 1
entity zone_b:
  health 1
"""
CYCLE = """
world "C"
entity a:
  depends_on b
entity b:
  depends_on a
"""


def check(name, ok, detail):
    return (name, ok, detail)


def test_edit_updates_graph():
    r = apply_edit(DEMO_OLD, DEMO_NEW)
    ok = r["ok"] and "gate" in r["sim"].cg.reach_ge1("reactor")
    return check("edit_updates_graph", ok, f"ok={r['ok']}, reactor now reaches gate directly={'gate' in r['sim'].cg.reach_ge1('reactor')}")


def test_edit_updates_power_path():
    r = apply_edit(DEMO_OLD, DEMO_NEW)
    added = ("reactor", "feeds", "gate") in r["consequences"]["what_changed"]["relations_added"]
    return check("edit_updates_power_path", r["ok"] and added, f"relation (reactor,feeds,gate) added={added}")


def test_edit_removes_spof():
    r = apply_edit(DEMO_OLD, DEMO_NEW)
    c = r["consequences"]
    ok = "power" in c["spofs_removed"] and c["resilience"] == "increased"
    return check("edit_removes_spof", ok, f"spofs_removed={c['spofs_removed']}, resilience={c['resilience']}")


def test_edit_updates_factions():
    r = apply_edit(TERR_OLD, TERR_NEW)
    tc = {t["entity"]: (t["from"], t["to"]) for t in r["consequences"]["territory_changes"]}
    ok = r["ok"] and tc.get("zone_a") == ("faction_red", "faction_blue")
    return check("edit_updates_factions", ok, f"zone_a control {tc.get('zone_a')}")


def test_camera_inventory_preserved():
    carry = {"camera": [1, 2, 3], "health": 73, "inventory": ["rifle", "shotgun"]}
    r = apply_edit(DEMO_OLD, DEMO_NEW, carry=carry)
    return check("camera_inventory_preserved", r["carry"] == carry, f"carry preserved={r['carry']==carry}")


def test_invalid_edit_rejected():
    r = apply_edit(DEMO_OLD, CYCLE, carry={"health": 50})
    ok = (not r["ok"]) and r["sim"] is None and r["reason"].startswith("invalid") and r["carry"] == {"health": 50}
    return check("invalid_edit_rejected", ok, f"ok={r['ok']}, reason='{r['reason']}', old authority stands")


def test_parse_error_rejected():
    r = apply_edit(DEMO_OLD, "this is not a valid world at all")
    ok = (not r["ok"]) and r["sim"] is None and r["reason"].startswith("parse error")
    return check("parse_error_rejected", ok, f"ok={r['ok']}, reason='{r['reason'][:32]}...'")


def test_diff_deterministic():
    a = apply_edit(DEMO_OLD, DEMO_NEW)["consequences"]
    b = apply_edit(DEMO_OLD, DEMO_NEW)["consequences"]
    return check("diff_deterministic", a == b, f"identical consequences={a == b}")


def test_explain_runtime():
    w = WorldSim(DEMO_OLD)
    w.apply_event("destroy", "reactor")         # cut the power source
    e = explain(w, "gate")                       # gate now unreachable from any faction
    ok = e["controller"] == "neutral" and "alive graph" in e["why_controller"] and e["status"] == "disabled"
    return check("explain_runtime", ok, f"gate controller={e['controller']} ({e['status']}); why mentions alive graph")


def main():
    results = [
        test_edit_updates_graph(),
        test_edit_updates_power_path(),
        test_edit_removes_spof(),
        test_edit_updates_factions(),
        test_camera_inventory_preserved(),
        test_invalid_edit_rejected(),
        test_parse_error_rejected(),
        test_diff_deterministic(),
        test_explain_runtime(),
    ]
    print("test_world_edit — Phase 11: live edit = new authority (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a topology edit re-derives graph/power/"
          f"factions,\n  reports its consequences (SPOF removed, resilience), preserves player state, REJECTS"
          f" invalid\n  or unparseable edits (old authority stands), is deterministic, and explains 'why' from the alive graph.")
    assert passed == total, f"{total - passed} check(s) failed — live-edit authority leaks"


if __name__ == "__main__":
    main()
