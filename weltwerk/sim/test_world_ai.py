# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_ai.py — Phase 9 proofs (validity-not-outcome): the AI authority is correct, and gameplay
death routes through Weltwerk's causal event system.

   1. los_blocked            — a wall between bot and player ⇒ no line of sight (bot cannot fire)
   2. los_clear              — open ground ⇒ line of sight
   3. no_omniscience_range   — beyond view range ⇒ not visible even with clear LOS
   4. patrol_to_attack       — PATROL + sees player in range ⇒ ATTACK
   5. attack_to_search       — ATTACK + lost sight ⇒ SEARCH
   6. chase_to_search        — CHASE + lost sight ⇒ SEARCH
   7. squad_alert            — a spotter alerts a nearby ally ⇒ ally (no LOS) ⇒ INVESTIGATE
   8. astar_around_wall      — A* paths AROUND a wall (never through a blocked cell), reaches the goal
   9. destroy_generator_cascade — destroy(generator) disables turret/door/light by CAUSAL propagation (world_sim)
  10. determinism            — same inputs ⇒ identical path and identical bot step

Run:  PYTHONHASHSEED=0 python3 test_world_ai.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_ai import (ATTACK, CHASE, INVESTIGATE, PATROL, SEARCH, Bot, Grid, Percept, astar,
                      line_of_sight, perceive, squad_broadcast, step_bot, transition, visible)


def check(name, ok, detail):
    return (name, ok, detail)


def test_los_blocked():
    g = Grid(6, 3, {(3, 1)})
    ok = not line_of_sight(g, (0, 1), (5, 1))
    return check("los_blocked", ok, f"wall at (3,1) between (0,1)-(5,1): LOS={not ok and 'clear' or 'blocked'}")


def test_los_clear():
    g = Grid(6, 3, set())
    ok = line_of_sight(g, (0, 1), (5, 1))
    return check("los_clear", ok, f"open ground (0,1)-(5,1): LOS={'clear' if ok else 'blocked'}")


def test_no_omniscience_range():
    g = Grid(40, 3, set())
    far = visible(g, (0, 1), (30, 1), view_range=14.0)   # clear LOS but out of range
    return check("no_omniscience_range", not far, f"player 30 away, view 14 ⇒ visible={far}")


def test_patrol_to_attack():
    s = transition(PATROL, Percept(can_see_player=True, in_range=True))
    return check("patrol_to_attack", s == ATTACK, f"PATROL+see+range → {s}")


def test_attack_to_search():
    s = transition(ATTACK, Percept(can_see_player=False))
    return check("attack_to_search", s == SEARCH, f"ATTACK+lost-sight → {s}")


def test_chase_to_search():
    s = transition(CHASE, Percept(can_see_player=False))
    return check("chase_to_search", s == SEARCH, f"CHASE+lost-sight → {s}")


def test_squad_alert():
    g = Grid(12, 8, {(6, y) for y in range(0, 5)})       # wall hides the player from the ally
    spotter = Bot(id="b1", pos=(1, 6), team="red", state=ATTACK)
    ally = Bot(id="b2", pos=(3, 6), team="red", state=PATROL, target=(3, 1))
    enemy = Bot(id="b3", pos=(2, 6), team="blue", state=PATROL)
    player = (10, 6)
    alerted = squad_broadcast([spotter, ally, enemy], spotter, player)
    rec = step_bot(g, ally, (10, 1))                     # ally has NO LOS (wall) but heard the alert
    ok = ("b2" in alerted and "b3" not in alerted and rec["state"] == INVESTIGATE)
    return check("squad_alert", ok, f"alerted={alerted}, ally(no LOS) → {rec['state']}")


def test_astar_around_wall():
    g = Grid(5, 3, {(2, 0), (2, 1)})                     # wall blocks the straight y=1 route
    path = astar(g, (0, 1), (4, 1))
    direct_blocked = not line_of_sight(g, (0, 1), (4, 1))
    ok = (path is not None and path[0] == (0, 1) and path[-1] == (4, 1)
          and (2, 1) not in path and (2, 0) not in path and direct_blocked)
    return check("astar_around_wall", ok, f"path len={len(path) if path else None}, avoids wall={ (2,1) not in (path or []) }")


def test_destroy_generator_cascade():
    # gameplay death routes through world_sim; consequences propagate by causality, not script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from world_sim import WorldSim
    world = """
world "Base"
entity generator:
  powers turret
  powers door
  powers light
entity turret:
  health 100
entity door:
  health 100
entity light:
  health 100
"""
    w = WorldSim(world)
    rep = w.apply_event("destroy", "generator")
    disabled = {e for e in ("turret", "door", "light") if w.runtime[e]["status"] == "disabled"}
    ok = disabled == {"turret", "door", "light"} and set(rep["affected"]) >= {"generator", "turret", "door", "light"}
    return check("destroy_generator_cascade", ok, f"disabled by cascade={sorted(disabled)}")


def test_determinism():
    g = Grid(12, 8, {(6, y) for y in range(0, 5)})
    p1 = astar(g, (1, 6), (10, 6)); p2 = astar(g, (1, 6), (10, 6))
    b1 = Bot(id="x", pos=(1, 6), team="red", state=PATROL, target=(1, 1))
    b2 = Bot(id="x", pos=(1, 6), team="red", state=PATROL, target=(1, 1))
    r1 = step_bot(g, b1, (10, 6)); r2 = step_bot(g, b2, (10, 6))
    ok = (p1 == p2 and r1 == r2)
    return check("determinism", ok, f"path stable={p1==p2}, step stable={r1==r2}")


def main():
    results = [
        test_los_blocked(),
        test_los_clear(),
        test_no_omniscience_range(),
        test_patrol_to_attack(),
        test_attack_to_search(),
        test_chase_to_search(),
        test_squad_alert(),
        test_astar_around_wall(),
        test_destroy_generator_cascade(),
        test_determinism(),
    ]
    print("test_world_ai — Phase 9: combat-AI authority (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: bots see by LOS (a wall blocks sight and"
          f"\n  therefore fire), see only within range (no omniscience), transition through an explicit state"
          f"\n  machine, alert squadmates, path AROUND walls, and death cascades through the causal event system."
          f"\n  All deterministic.")
    assert passed == total, f"{total - passed} check(s) failed — the AI authority or its causal integration leaks"


if __name__ == "__main__":
    main()
