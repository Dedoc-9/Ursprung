# SPDX-License-Identifier: AGPL-3.0-only
"""
test_times_square.py — Phase 12 proofs (validity-not-outcome): the Times Square CITY is the GRAPH.

Every light/screen/turret/territory in the projection derives from the .wrk authority. These tests prove
the scenario behaves causally, so the renderer can mirror it without owning any truth.

   1. loads_and_factions    — the .wrk world loads; blue + red factions are detected
   2. initial_territory     — blue owns its grid, red owns its grid, data_center + central_square contested
   3. power_station_cascade — destroying the blue power_station disables its whole media/surveillance grid
   4. territory_flips       — data_center + central_square flip blue-contested → red when blue's path dies
   5. blue_loses_power      — faction_power(blue) collapses after its root is destroyed
   6. renderer_invariant    — building geometry from a snapshot never changes the authority hash
   7. inspector_determinism — explain() gives identical answers for identical state
   8. determinism           — replaying the same event ⇒ identical authority hash

Run:  PYTHONHASHSEED=0 python3 test_times_square.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render"))
from world_sim import WorldSim, render_primitives
from world_edit import explain

WRK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worlds", "times_square.wrk")
with open(WRK, encoding="utf-8") as fh:
    WORLD = fh.read()


def check(name, ok, detail):
    return (name, ok, detail)


def test_loads_and_factions():
    w = WorldSim(WORLD)
    return check("loads_and_factions", set(w.factions) == {"faction_blue", "faction_red"},
                 f"factions={sorted(w.factions)}, entities={len(w.cg.nodes)}")


def test_initial_territory():
    w = WorldSim(WORLD)
    ok = (w.controller("media_tower") == "faction_blue" and w.controller("turret_blue") == "faction_blue"
          and w.controller("market") == "faction_red" and w.controller("turret_red") == "faction_red"
          and w.controller("data_center") == "contested" and w.controller("central_square") == "contested")
    return check("initial_territory", ok,
                 f"media_tower={w.controller('media_tower')}, market={w.controller('market')}, "
                 f"data_center={w.controller('data_center')}, central_square={w.controller('central_square')}")


def test_power_station_cascade():
    w = WorldSim(WORLD)
    w.apply_event("destroy", "power_station")
    grid = ["media_tower", "surveillance_net", "billboard_north", "billboard_central", "turret_blue", "drone_cam"]
    disabled = {e for e in grid if w.runtime[e]["status"] == "disabled"}
    return check("power_station_cascade", disabled == set(grid),
                 f"disabled by cascade: {sorted(disabled)}")


def test_territory_flips():
    w = WorldSim(WORLD)
    dc_before, sq_before = w.controller("data_center"), w.controller("central_square")
    w.apply_event("destroy", "power_station")
    dc_after, sq_after = w.controller("data_center"), w.controller("central_square")
    ok = (dc_before == "contested" and dc_after == "faction_red"
          and sq_before == "contested" and sq_after == "faction_red")
    return check("territory_flips", ok,
                 f"data_center {dc_before}→{dc_after}; central_square {sq_before}→{sq_after}")


def test_blue_loses_power():
    w = WorldSim(WORLD)
    before = w.faction_power("faction_blue")
    w.apply_event("destroy", "power_station")
    after = w.faction_power("faction_blue")
    return check("blue_loses_power", before > 0 and after == 0, f"blue power {before}→{after}")


def test_renderer_invariant():
    w = WorldSim(WORLD)
    w.apply_event("destroy", "power_station")
    h0 = w.authority_hash()
    prims = render_primitives(w.snapshot())          # build geometry — a pure read
    h1 = w.authority_hash()
    return check("renderer_invariant", h0 == h1 and len(prims) > 0,
                 f"hash unchanged={h0 == h1}, {len(prims)} primitives")


def test_inspector_determinism():
    w = WorldSim(WORLD); w.apply_event("destroy", "power_station")
    a = explain(w, "central_square"); b = explain(w, "central_square")
    return check("inspector_determinism", a == b and a["controller"] == "faction_red",
                 f"central_square why: {a['why_controller'][:48]}…")


def test_determinism():
    def run():
        w = WorldSim(WORLD); w.apply_event("destroy", "power_station"); return w.authority_hash()
    return check("determinism", run() == run(), f"same event ⇒ identical hash: {run() == run()}")


def main():
    results = [
        test_loads_and_factions(),
        test_initial_territory(),
        test_power_station_cascade(),
        test_territory_flips(),
        test_blue_loses_power(),
        test_renderer_invariant(),
        test_inspector_determinism(),
        test_determinism(),
    ]
    print("test_times_square — Phase 12: the city is the graph (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the Times Square map's lighting, screens,"
          f"\n  turrets, and territory all derive from the .wrk graph — destroying the blue power_station"
          f"\n  cascades through its grid and flips the contested centre to red, and the renderer that mirrors"
          f"\n  this never owns any of it.")
    assert passed == total, f"{total - passed} check(s) failed — the Times Square scenario is not sound"


if __name__ == "__main__":
    main()
