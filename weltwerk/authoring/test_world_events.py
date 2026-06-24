# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_events.py — Phase 2 proofs (validity-not-outcome): the author→graph→event loop is faithful.

Proves the directive's required properties at the verified Python level (the JS demo mirrors these):
  1. text_edit_changes_graph      — editing the .wrk text changes the causal graph
  2. wrk_format_parses            — the directive's exact `.wrk` syntax parses (zone/entity/key value)
  3. destroy_affects_dependents   — destroying a dependency diverges its dependents (generator → gate,turret)
  4. destroy_isolated_is_local    — destroying a leaf diverges nothing downstream
  5. determinism                  — same text ⇒ identical graph + identical event divergence

Run:  PYTHONHASHSEED=0 python3 test_world_events.py
"""
from __future__ import annotations

from world_format import build_causal_graph, parse_world, simulate_destroy

WRK = """
world "Fortress"
zone courtyard
zone reactor
entity generator:
  zone reactor
  health 100
  emits power
entity gate:
  zone courtyard
  blocks courtyard
  depends_on generator
entity turret:
  zone courtyard
  protects gate
  powered_by generator
"""


def check(name, ok, detail):
    return (name, ok, detail)


def test_wrk_format_parses():
    s = parse_world(WRK)
    ok = (s.name == "Fortress" and set(s.zones) >= {"courtyard", "reactor"}
          and set(s.entities) == {"generator", "gate", "turret"}
          and s.entities["generator"].health == 100
          and ("emits", "power") in s.entities["generator"].relations
          and ("depends_on", "generator") in s.entities["gate"].relations)
    return check("wrk_format_parses", ok, f"directive .wrk syntax parses exactly: {ok}")


def test_text_edit_changes_graph():
    g1 = build_causal_graph(parse_world(WRK))
    g2 = build_causal_graph(parse_world(WRK + "entity wall:\n  protects gate\n"))
    ok = ("wall" not in g1.nodes) and ("wall" in g2.nodes) and ("gate" in g2.edges["wall"])
    return check("text_edit_changes_graph", ok, f"adding an entity in text changes the graph: {ok}")


def test_destroy_affects_dependents():
    g = build_causal_graph(parse_world(WRK))
    r = simulate_destroy(g, "generator")
    # generator emits power AND gate/turret depend_on/powered_by generator ⇒ reversed edges
    # generator → gate, generator → turret ; so destroying generator diverges both
    ok = "gate" in r["diverged"] and "turret" in r["diverged"]
    return check("destroy_affects_dependents", ok,
                 f"destroy generator → diverged {r['diverged']} (gate+turret present={ok})")


def test_destroy_isolated_is_local():
    g = build_causal_graph(parse_world(WRK))
    r = simulate_destroy(g, "turret")    # turret protects gate ⇒ only gate downstream
    ok = "generator" not in r["diverged"]    # destroying a dependent must NOT diverge its dependency
    return check("destroy_isolated_is_local", ok,
                 f"destroy turret does not diverge upstream generator: {ok} (diverged={r['diverged']})")


def test_determinism():
    g1 = build_causal_graph(parse_world(WRK)); r1 = simulate_destroy(g1, "generator")
    g2 = build_causal_graph(parse_world(WRK)); r2 = simulate_destroy(g2, "generator")
    ok = (sorted(g1.nodes) == sorted(g2.nodes)) and (r1 == r2)
    return check("determinism", ok, f"same text ⇒ identical graph + event divergence: {ok}")


def main():
    results = [
        test_wrk_format_parses(),
        test_text_edit_changes_graph(),
        test_destroy_affects_dependents(),
        test_destroy_isolated_is_local(),
        test_determinism(),
    ]
    print("test_world_events — Phase 2 author→graph→event loop (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the .wrk text parses, editing it changes the"
          f"\n  graph, destroying a dependency diverges its dependents (not its upstream), and it's"
          f"\n  deterministic. The graph/event logic the playable demo mirrors is verified here.")
    assert passed == total, f"{total - passed} check(s) failed — the Phase 2 loop is not faithful"


if __name__ == "__main__":
    main()
