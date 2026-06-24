# SPDX-License-Identifier: AGPL-3.0-only
"""
geometry_boundary.py — Phase 5: CausalWorld → GeometryAdapter → Renderer. World logic survives graphics.

Proves the visual world is a REPLACEABLE PROJECTION, not a hidden simulation. The authority (CausalWorld)
mutates only through apply_event; renderers receive an IMMUTABLE snapshot and produce geometry. The crux
invariant (test): rendering does not change the authority — `observation ≠ authority`, machine-checked.

    CausalWorld  (authority: entities, relations, positions, state, events, dependency queries)
        │  snapshot()  → frozen, read-only
        ▼
    GeometryAdapter  (translate snapshot → render primitives; may colour/place/overlay)
        ▼                                   may NOT: mutate runtime, create relations, invent state
    Renderer (VoxelAdapter / TopologyAdapter / … swappable)

Acceptance: delete any renderer and the world still exists (the authority holds no renderer reference).
NOT claimed: UE5 integration, MMO scale, latency, player count. The geometry is pure projection.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from hashlib import blake2b

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
from world_format import build_causal_graph, parse_world, simulate_destroy   # noqa: E402


@dataclass(frozen=True)
class EntityView:
    """A renderer-facing, IMMUTABLE view of one entity. Frozen ⇒ a renderer physically cannot mutate it."""
    id: str
    pos: tuple
    state: str
    alive: bool
    blast: int
    in_scc: bool


@dataclass(frozen=True)
class Snapshot:
    """Everything a renderer is allowed to see — read-only. No back-reference to the authority."""
    entities: tuple        # tuple[EntityView]
    relations: tuple       # tuple[(src, rel, dst)]
    events: tuple          # tuple[str]  (history)
    world_size: int


def _sccs(edges):
    def reach(s):
        seen, st = set(), list(edges.get(s, set()))
        while st:
            n = st.pop()
            if n not in seen:
                seen.add(n); st.extend(edges.get(n, set()))
        return seen
    seen, members = set(), set()
    for n in edges:
        if n in seen:
            continue
        comp = {n} | {m for m in reach(n) if n in reach(m)}
        seen |= comp
        if len(comp) > 1:
            members |= comp
    return members


class CausalWorld:
    """The authority. Mutation happens ONLY through apply_event. Renderers get snapshot() and nothing else."""
    def __init__(self, world_text: str):
        self.spec = parse_world(world_text)
        self.cg = build_causal_graph(self.spec)
        self.runtime = {n: {"alive": True, "state": "ok"} for n in self.cg.nodes}
        self.events: list = []

    # --- the ONLY mutation path (authority) -----------------------------------------------------
    def apply_event(self, kind: str, target: str) -> None:
        if kind == "destroy" and target in self.cg.nodes:
            diverged = simulate_destroy(self.cg, target)["diverged"]
            self.runtime[target] = {"alive": False, "state": "destroyed"}
            for d in diverged:
                self.runtime[d] = {"alive": self.runtime[d]["alive"], "state": "disabled"}
            self.events.append(f"{kind} {target}")

    # --- read-only queries (no mutation) --------------------------------------------------------
    def reachable(self, eid: str) -> frozenset:
        return frozenset(self.cg.reach_ge1(eid)) if eid in self.cg.nodes else frozenset()

    def authority_hash(self) -> str:
        h = blake2b(digest_size=16)
        for k in sorted(self.runtime):
            r = self.runtime[k]
            h.update(f"|{k}:{int(r['alive'])}:{r['state']}".encode())
        for s in sorted(self.cg.edges):
            for d in sorted(self.cg.edges[s]):
                h.update(f"|E{s}>{d}".encode())
        for e in self.events:
            h.update(("|EV" + e).encode())
        return h.hexdigest()

    def snapshot(self) -> Snapshot:
        scc = _sccs(self.cg.edges)
        ents = tuple(EntityView(
            id=n,
            pos=tuple(self.spec.entities[n].pos) if n in self.spec.entities else (0.0, 0.0, 0.0),
            state=self.runtime[n]["state"], alive=self.runtime[n]["alive"],
            blast=len(self.cg.reach_ge1(n)), in_scc=n in scc,
        ) for n in sorted(self.cg.nodes))
        rels = tuple((s, self.cg.labels[(s, d)], d)
                     for s in sorted(self.cg.edges) for d in sorted(self.cg.edges[s]))
        return Snapshot(entities=ents, relations=rels, events=tuple(self.events),
                        world_size=len(self.cg.nodes))


class GeometryAdapter:
    """Translate a Snapshot into render primitives. Pure read: receives ONLY a Snapshot, returns geometry,
    never touches a CausalWorld. Subclasses implement adapt(); they may colour/place, never mutate."""
    name = "adapter"

    def adapt(self, snap: Snapshot) -> tuple:
        raise NotImplementedError


class VoxelAdapter(GeometryAdapter):
    """Renderer A: a block per alive entity at its position, coloured by state."""
    name = "voxel"
    COLORS = {"ok": "#8b949e", "destroyed": "#5a5f66", "disabled": "#da3633"}

    def adapt(self, snap: Snapshot) -> tuple:
        return tuple({"kind": "block", "id": e.id, "pos": e.pos, "color": self.COLORS.get(e.state, "#888")}
                     for e in snap.entities if e.alive)


class TopologyAdapter(GeometryAdapter):
    """Renderer B: nodes + directed edges, coloured by SCC / blast — same Snapshot, different projection."""
    name = "topology"

    def adapt(self, snap: Snapshot) -> tuple:
        prims = []
        for e in snap.entities:
            color = "#e3742f" if e.in_scc else ("#2ea043" if e.blast > 0 else "#1f6feb")
            prims.append({"kind": "node", "id": e.id, "blast": e.blast, "color": color})
        for (s, _rel, d) in snap.relations:
            prims.append({"kind": "edge", "src": s, "dst": d})
        return tuple(prims)


def main():
    import textwrap
    WORLD = textwrap.dedent("""
    world "Frontier"
    entity generator:
      position 0 0 -8
      emits power
    entity turret:
      position 0 0 0
      powered_by generator
    entity door:
      position 4 0 0
      depends_on generator
    entity tree:
      position -10 0 6
      health 30
    """)
    w = CausalWorld(WORLD)
    w.apply_event("destroy", "generator")
    before = w.authority_hash()
    voxel = VoxelAdapter().adapt(w.snapshot())
    topo = TopologyAdapter().adapt(w.snapshot())
    after = w.authority_hash()
    print("geometry_boundary.py — Phase 5: world logic survives graphics\n")
    print(f"  authority hash unchanged by rendering: {before == after}")
    print(f"  Renderer A (voxel):    {len(voxel)} block primitives")
    print(f"  Renderer B (topology): {len(topo)} node/edge primitives")
    print(f"  both consume the SAME snapshot; neither holds authority — delete either, the world remains.")
    print(f"  events on the authority (the committed trajectory): {list(w.events)}")
    print("\n  geometry is a projection; the causal world is the authority. No UE5/MMO/latency claim.")


if __name__ == "__main__":
    main()
