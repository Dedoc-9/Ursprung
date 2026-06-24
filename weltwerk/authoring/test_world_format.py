# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_format.py — validity-not-outcome for the Phase 1 text-first world format.

Proves the four-stage pipeline is faithful to the declared text; it does not assert any world is "good".
Load-bearing checks: causal edge DIRECTION is honest (depends_on reverses), and the derived causal graph
feeds the verified lint (SCC found on a world with a feedback loop).

  1. parse_spec          — world name, zones, entities, attributes parsed exactly
  2. causal_direction    — forward relations entity→target; REVERSED (depends_on) target→entity
  3. spatial_adjacency   — entities within radius are adjacent; far ones are not
  4. runtime_state       — RuntimeWorld carries id/zone/pos/health/alive
  5. lint_runs           — the derived CausalGraph drives world_lint; the demo's supply loop is found
  6. determinism         — same text ⇒ identical compiled world

Run:  PYTHONHASHSEED=0 python3 test_world_format.py
"""
from __future__ import annotations

from world_format import (DEMO_WORLD, build_causal_graph, build_runtime, build_spatial_graph,
                          compile_world, export_json, parse_world, serialize_world)
from world_lint import sccs

SAMPLE = """
world "T"
zones: a b
entities:
  turret:
    zone: a
    position: 0 0 0
    health: 100
    protects: gate
    depends_on: power
  gate:
    zone: a
    position: 1 0 0
  power:
    zone: b
    position: 50 0 0
"""


def check(name, ok, detail):
    return (name, ok, detail)


def test_parse_spec():
    s = parse_world(SAMPLE)
    e = s.entities
    ok = (s.name == "T" and s.zones == ["a", "b"] and set(e) == {"turret", "gate", "power"}
          and e["turret"].zone == "a" and e["turret"].health == 100 and e["turret"].pos == (0.0, 0.0, 0.0))
    return check("parse_spec", ok, f"name/zones/entities/attrs parsed: {ok}")


def test_causal_direction():
    g = build_causal_graph(parse_world(SAMPLE))
    forward = "gate" in g.edges["turret"]          # protects: turret → gate
    reversed_ok = "turret" in g.edges["power"]      # depends_on: power → turret (reversed)
    not_wrong = "power" not in g.edges["turret"]    # turret does NOT point to power
    return check("causal_direction", forward and reversed_ok and not_wrong,
                 f"protects forward={forward}; depends_on reversed={reversed_ok}; no wrong edge={not_wrong}")


def test_spatial_adjacency():
    s = parse_world(SAMPLE)
    adj = build_spatial_graph(s, radius=4.0)
    near = "gate" in adj["turret"]                  # turret(0) & gate(1) within 4
    far = "power" not in adj["turret"]              # power at x=50 is far
    return check("spatial_adjacency", near and far, f"near adjacent={near}; far not adjacent={far}")


def test_runtime_state():
    rt = build_runtime(parse_world(SAMPLE))
    t = next(e for e in rt if e["id"] == "turret")
    ok = t["zone"] == "a" and t["health"] == 100 and t["alive"] is True and len(t["pos"]) == 3
    return check("runtime_state", ok, f"runtime carries id/zone/pos/health/alive: {ok}")


def test_lint_runs():
    g = build_causal_graph(parse_world(DEMO_WORLD))
    fb = [c for c in sccs(g) if len(c) > 1]
    found = any("garrison" in c and "supply" in c for c in fb)
    return check("lint_runs", len(fb) >= 1 and found,
                 f"derived graph drives lint; supply↔garrison loop found={found}")


def test_determinism():
    a = export_json(DEMO_WORLD)
    b = export_json(DEMO_WORLD)
    return check("determinism", a == b, f"same text ⇒ identical compiled world: {a == b}")


def test_roundtrip_serialization():
    # the designer's invariant: edit → serialize → reload gives the SAME spec (text is the authority)
    s1 = parse_world(DEMO_WORLD)
    s2 = parse_world(serialize_world(s1))
    same = (s1.name == s2.name and s1.zones == s2.zones and set(s1.entities) == set(s2.entities)
            and all(s1.entities[k].zone == s2.entities[k].zone
                    and s1.entities[k].health == s2.entities[k].health
                    and s1.entities[k].relations == s2.entities[k].relations
                    and tuple(s1.entities[k].pos) == tuple(s2.entities[k].pos) for k in s1.entities))
    idempotent = serialize_world(s1) == serialize_world(s2)
    return check("roundtrip_serialization", same and idempotent,
                 f"parse(serialize(spec)) == spec={same}; serialization idempotent={idempotent}")


def main():
    results = [
        test_roundtrip_serialization(),
        test_parse_spec(),
        test_causal_direction(),
        test_spatial_adjacency(),
        test_runtime_state(),
        test_lint_runs(),
        test_determinism(),
    ]
    print("test_world_format — the text→pipeline is faithful (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:20s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the text parses exactly, causal edge"
          f"\n  direction is honest (depends_on reverses), spatial adjacency follows positions, runtime state"
          f"\n  is carried, and the derived graph drives the verified lint. Text + graph are the authority.")
    assert passed == total, f"{total - passed} check(s) failed — the world format is not faithful"


if __name__ == "__main__":
    main()
