# SPDX-License-Identifier: AGPL-3.0-only
"""
world_format.py — Phase 1: the text-first world format (the highest-priority foundation).

A world is AUTHORED AS TEXT; geometry is a projection of the causal graph, never the authority. This
parses a structured world spec into the four-stage pipeline the rest of the system consumes:

    WorldSpec   (parsed declarations: zones, entities, attributes, relations)
        ↓
    CausalGraph (typed relations → directed "can-affect" edges)  — reuses the VERIFIED world_spec +
        ↓        world_lint (reachability / SCC / bottleneck), so the analysis is checked, not re-asserted
    SpatialGraph (positions + influence radius → "can physically reach" adjacency)
        ↓
    RuntimeWorld (entities with state {id, zone, pos, health, alive}) — ready for the deterministic
                 runtime / fork in weltwerk/world.py + scale/.

FORMAT (indentation-based):
    world "Frontier_Test"
    zones: fortress market reactor
    entities:
      turret:
        zone: fortress
        position: 2 0 -3
        health: 100
        protects: gate
        depends_on: power
      gate:
        zone: fortress
        blocks: courtyard
      economy_node:
        zone: market
        feeds: faction

CAUSAL DIRECTION (honest): an edge src→dst means "editing/destroying src can affect dst".
  forward relations  (protects, blocks, feeds, supplies, defends, contains, ...):  entity → target
  REVERSED relations (depends_on, powered_by, fed_by, sustained_by):                target → entity
A developer edits factions/economies/doors/power/territory as relations — without touching code.

This file is engine-independent (Rule 6): no rendering. Meshes are generated downstream FROM the graph.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_spec import CausalGraph                      # noqa: E402
from world_lint import lint, report                     # noqa: E402

ATTR_KEYS = {"zone", "position", "health"}
REVERSED = {"depends_on", "powered_by", "fed_by", "sustained_by", "needs"}   # target affects entity


@dataclass
class Entity:
    name: str
    zone: str = ""
    pos: tuple = (0.0, 0.0, 0.0)
    health: int = 100
    relations: list = field(default_factory=list)       # list of (relation, target)


@dataclass
class WorldSpec:
    name: str = "world"
    zones: list = field(default_factory=list)
    entities: dict = field(default_factory=dict)        # name -> Entity


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _kv(s: str):
    """Split an attribute line into (key, rest), accepting both 'key: vals' and 'key vals'."""
    if ":" in s:
        k, v = s.split(":", 1)
        return k.strip(), v.strip()
    parts = s.split(None, 1)
    return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def parse_world(text: str) -> WorldSpec:
    """Lenient text-first parser. Accepts the .wrk form (`zone X`, `entity NAME:`, `key value`) and the
    earlier form (`zones: a b`, `NAME:`, `key: value`) — both produce the same WorldSpec."""
    spec = WorldSpec()
    cur = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        ind = _indent(line)
        s = line.strip()
        if ind == 0:
            cur = None
            toks = s.split()
            if toks[0] == "world":
                spec.name = s[5:].strip().strip('"') or "world"
            elif toks[0] == "zones:":
                spec.zones += s[len("zones:"):].split()
            elif toks[0] == "zone":                       # .wrk: one zone per line
                for z in toks[1:]:
                    if z not in spec.zones:
                        spec.zones.append(z)
            elif s == "entities:":
                pass
            elif toks[0] == "entity":                     # .wrk: `entity NAME:` or `entity NAME`
                name = toks[1].rstrip(":")
                cur = Entity(name=name); spec.entities[name] = cur
            elif s.endswith(":"):                          # earlier: `NAME:`
                name = s[:-1].strip()
                cur = Entity(name=name); spec.entities[name] = cur
            else:
                raise ValueError(f"unexpected top-level line: {raw!r}")
        elif s.endswith(":") and len(s.split()) == 1:      # indented `  name:` — earlier-format entity decl
            name = s[:-1].strip()
            cur = Entity(name=name)
            spec.entities[name] = cur
        else:                                              # attribute / relation of current entity
            if cur is None:
                raise ValueError(f"attribute outside an entity: {raw!r}")
            key, val = _kv(s)
            if key == "zone":
                cur.zone = val
            elif key == "position":
                p = [float(x) for x in val.split()]
                cur.pos = tuple((p + [0, 0, 0])[:3])
            elif key == "health":
                cur.health = int(val)
            else:                                          # a relation: key target [target2 ...]
                for tgt in val.split():
                    cur.relations.append((key, tgt))
    return spec


def simulate_destroy(cg: CausalGraph, target: str) -> dict:
    """Event propagation (Phase 2): destroying `target` diverges every entity reachable FROM it in the
    can-affect graph (its downstream dependents). This is the discrete-model ACTUAL divergence of the
    event — graph propagation; a continuous model would need dynamics. `event ≠ measured-dynamics`."""
    diverged = cg.reach_ge1(target) if target in cg.nodes else set()
    return {"destroyed": target, "diverged": sorted(diverged), "blast_radius": len(diverged)}


def build_causal_graph(spec: WorldSpec) -> CausalGraph:
    """Typed relations → directed can-affect edges (honest direction; depends_on et al. reversed)."""
    g = CausalGraph()
    for e in spec.entities.values():
        g.add_node(e.name)
    for e in spec.entities.values():
        for rel, tgt in e.relations:
            if rel in REVERSED:
                g.add_edge(tgt, rel, e.name)             # target affects entity
            else:
                g.add_edge(e.name, rel, tgt)             # entity affects target
    return g


def build_spatial_graph(spec: WorldSpec, radius: float = 4.0) -> dict:
    """Positions + influence radius → 'can physically reach' adjacency (the spatial neighbourhood)."""
    ents = list(spec.entities.values())
    adj = {e.name: set() for e in ents}
    for i, a in enumerate(ents):
        for b in ents[i + 1:]:
            d = sum((x - y) ** 2 for x, y in zip(a.pos, b.pos)) ** 0.5
            if d <= radius:
                adj[a.name].add(b.name)
                adj[b.name].add(a.name)
    return {k: sorted(v) for k, v in adj.items()}


def build_runtime(spec: WorldSpec) -> list:
    """RuntimeWorld: deterministic entity state, ready for world.py / fork. No geometry."""
    return [{"id": e.name, "zone": e.zone, "pos": list(e.pos), "health": e.health, "alive": True}
            for e in spec.entities.values()]


def compile_world(text: str, radius: float = 4.0) -> dict:
    spec = parse_world(text)
    cg = build_causal_graph(spec)
    return {"spec": spec, "causal": cg, "spatial": build_spatial_graph(spec, radius),
            "runtime": build_runtime(spec)}


def export_json(text: str, radius: float = 4.0) -> dict:
    """Engine-independent export the wireframe VIEW / FPS shell can project into geometry."""
    w = compile_world(text, radius)
    spec, cg = w["spec"], w["causal"]
    return {
        "world": spec.name, "zones": spec.zones,
        "entities": [{"id": e.name, "zone": e.zone, "pos": list(e.pos), "health": e.health,
                      "relations": [[r, t] for r, t in e.relations]} for e in spec.entities.values()],
        "causal_edges": [[s, cg.labels[(s, d)], d] for s in sorted(cg.edges) for d in sorted(cg.edges[s])],
        "spatial_adj": w["spatial"],
        "lint": [{"severity": x.severity, "kind": x.kind, "subject": x.subject} for x in lint(cg)],
    }


DEMO_WORLD = """
world "Frontier_Test"
zones: fortress market reactor

entities:
  turret:
    zone: fortress
    position: -3 0 -8
    health: 100
    protects: gate
    depends_on: power
  gate:
    zone: fortress
    position: 0 0 2
    health: 150
    blocks: courtyard
  courtyard:
    zone: fortress
    position: 0 0 -4
    feeds: market
  power:
    zone: reactor
    position: 14 0 -6
    health: 200
    feeds: turret
  market:
    zone: market
    position: 8 0 -2
    supplies: garrison
  garrison:
    zone: market
    position: 10 0 -6
    health: 120
    defends: gate
    consumes: supply
  supply:
    zone: market
    position: 12 0 -3
    health: 40
    sustains: garrison
"""


def main():
    w = compile_world(DEMO_WORLD)
    spec = w["spec"]
    print("world_format.py — Phase 1: text-first world → WorldSpec → CausalGraph → SpatialGraph → RuntimeWorld\n")
    print(f"  world '{spec.name}'  zones={spec.zones}  entities={len(spec.entities)}\n")
    print("  CAUSAL ANALYSIS (verified world_lint over the derived graph):")
    print(report(w["causal"]))
    print("\n  SPATIAL adjacency (radius 4):")
    for k, v in w["spatial"].items():
        if v:
            print(f"    {k}: {v}")
    print(f"\n  RUNTIME entities: {[e['id'] for e in w['runtime']]}")
    print("\n  geometry is a PROJECTION of this graph (Rule: graph is authority). export_json() feeds the VIEW.")


if __name__ == "__main__":
    main()
