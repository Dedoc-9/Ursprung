# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_sim.py — Phase 7 proofs (validity-not-outcome): the world is alive AND the boundary holds.

  1. world_loads                     — a .wrk world builds; factions are detected; a node reached by two
                                        factions is 'contested'
  2. event_changes_runtime           — destroy mutates the authority (target dies, hash changes)
  3. render_does_not_mutate_authority— hash identical before/after render_primitives; snapshot is frozen  ← boundary
  4. faction_event_propagates        — destroy the reactor ⇒ faction_red power drops AND its territory
                                        flips away (graph-derived consequence, not scripted)             ← liveness
  5. deterministic_replay            — same events ⇒ identical authority hash (replay reproduces state)
  6. potential_superset_actual       — every event's actual set ⊆ its potential set (Potential ⊇ Actual)
  7. capture_flips_control           — capture overrides reach: a contested node becomes a faction's

Run:  PYTHONHASHSEED=0 python3 test_world_sim.py
"""
from __future__ import annotations

import dataclasses

from world_sim import DEMO_WORLD, WorldSim, render_primitives, replay

SMALL = """
world "Small"
entity faction_a:
  controls reactor
entity reactor:
  health 100
  powers turret
entity turret:
  health 50
  protects gate
entity gate:
  health 50
"""


def check(name, ok, detail):
    return (name, ok, detail)


def test_world_loads():
    w = WorldSim(DEMO_WORLD)
    facs = set(w.factions)
    contested = w.controller("resource_node") == "contested"
    ok = facs == {"faction_red", "faction_blue"} and contested
    return check("world_loads", ok, f"factions={sorted(facs)}, resource_node={w.controller('resource_node')}")


def test_event_changes_runtime():
    w = WorldSim(SMALL)
    h0 = w.authority_hash()
    w.apply_event("destroy", "reactor")
    ok = (not w.runtime["reactor"]["alive"]) and w.authority_hash() != h0
    return check("event_changes_runtime", ok,
                 f"reactor alive={w.runtime['reactor']['alive']}, hash changed={w.authority_hash() != h0}")


def test_render_does_not_mutate_authority():
    w = WorldSim(DEMO_WORLD)
    w.apply_event("destroy", "reactor")
    before = w.authority_hash()
    prims = render_primitives(w.snapshot())
    after = w.authority_hash()
    frozen = False
    try:
        w.snapshot().entities[0].status = "hacked"
    except dataclasses.FrozenInstanceError:
        frozen = True
    except Exception:
        frozen = True
    ok = before == after and len(prims) > 0 and frozen
    return check("render_does_not_mutate_authority", ok,
                 f"hash unchanged={before == after}, {len(prims)} prims, snapshot frozen={frozen}")


def test_faction_event_propagates():
    w = WorldSim(DEMO_WORLD)
    p_before = w.faction_power("faction_red")
    terr_before = w.controller("north_territory")
    w.apply_event("destroy", "reactor")
    p_after = w.faction_power("faction_red")
    terr_after = w.controller("north_territory")
    ok = (p_after < p_before) and (terr_before == "faction_red") and (terr_after != "faction_red")
    return check("faction_event_propagates", ok,
                 f"red power {p_before}->{p_after}; north_territory {terr_before}->{terr_after}; "
                 f"defense_grid={w.runtime['defense_grid']['status']}")


def test_deterministic_replay():
    evs = [("damage", "reactor", 30), ("capture", "resource_node", 0, "faction_red"),
           ("destroy", "garrison"), ("repair", "reactor", 10)]
    a = replay(DEMO_WORLD, evs)
    b = replay(DEMO_WORLD, evs)
    return check("deterministic_replay", a == b, f"same events ⇒ identical hash: {a == b}")


def test_potential_superset_actual():
    w = WorldSim(DEMO_WORLD)
    ok = True
    detail = ""
    for kind, tgt in [("destroy", "reactor"), ("damage", "market"), ("destroy", "resource_node")]:
        rep = w.apply_event(kind, tgt, 40 if kind == "damage" else 0)
        sub = set(rep["actual"]) <= set(rep["potential"])
        ok = ok and sub
        detail = f"{rep['event']}: actual⊆potential={sub} ({rep['n_actual']}/{rep['n_potential']})"
    return check("potential_superset_actual", ok, detail)


def test_capture_flips_control():
    w = WorldSim(DEMO_WORLD)
    before = w.controller("resource_node")          # contested
    w.apply_event("capture", "resource_node", faction="faction_blue")
    after = w.controller("resource_node")
    ok = before == "contested" and after == "faction_blue"
    return check("capture_flips_control", ok, f"resource_node {before} -> {after}")


def test_repair_revives_dead():
    w = WorldSim(DEMO_WORLD)
    w.apply_event("destroy", "reactor")
    dead = not w.runtime["reactor"]["alive"]
    w.apply_event("repair", "reactor")              # reactor's only upstream is faction_red (alive) ⇒ revive
    revived = w.runtime["reactor"]["alive"]
    return check("repair_revives_dead", dead and revived, f"reactor dead={dead} -> revived={revived}")


STATION_WORLD = """
world "Base"
entity generator:
  powers repair_station
entity repair_station:
  health 100
"""
ARMOR_WORLD = """
world "A"
entity tank:
  health 100
"""


def test_station_powered_then_disabled():
    w = WorldSim(STATION_WORLD)
    before = w.station_active("repair_station")
    w.apply_event("destroy", "generator")            # cut power → cascade disables the station
    after = w.station_active("repair_station")
    return check("station_powered_then_disabled", before and not after,
                 f"repair_station active {before}→{after} after generator destroyed (causal, not scripted)")


def test_armor_reduces_damage():
    armored = WorldSim(ARMOR_WORLD); armored.armor["tank"] = {"kinetic": 20}
    bare = WorldSim(ARMOR_WORLD)
    armored.apply_event("damage", "tank", 30, dtype="kinetic")   # 30 − 20 armor = 10
    bare.apply_event("damage", "tank", 30, dtype="kinetic")      # no armor map → 30
    ok = armored.runtime["tank"]["health"] == 90 and bare.runtime["tank"]["health"] == 70
    return check("armor_reduces_damage", ok,
                 f"armored hp={armored.runtime['tank']['health']} > bare hp={bare.runtime['tank']['health']}")


def test_damage_type_specific():
    w = WorldSim(ARMOR_WORLD); w.armor["tank"] = {"kinetic": 20}
    w.apply_event("damage", "tank", 30, dtype="energy")          # kinetic armor must NOT absorb energy
    return check("damage_type_specific", w.runtime["tank"]["health"] == 70,
                 f"energy ignores kinetic armor: hp={w.runtime['tank']['health']}")


def main():
    results = [
        test_world_loads(),
        test_event_changes_runtime(),
        test_render_does_not_mutate_authority(),
        test_faction_event_propagates(),
        test_deterministic_replay(),
        test_potential_superset_actual(),
        test_capture_flips_control(),
        test_repair_revives_dead(),
        test_station_powered_then_disabled(),
        test_armor_reduces_damage(),
        test_damage_type_specific(),
    ]
    print("test_world_sim — Phase 7: the smallest living world (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:34s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: worlds load with graph-derived factions,"
          f"\n  events mutate the authority and propagate causally (reactor death drops a faction and flips its"
          f"\n  territory), rendering never mutates the authority, capture overrides reach, replay is"
          f"\n  deterministic, and Potential ⊇ Actual on every event.")
    assert passed == total, f"{total - passed} check(s) failed — the living world or its boundary leaks"


if __name__ == "__main__":
    main()
