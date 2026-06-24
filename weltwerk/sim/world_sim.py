# SPDX-License-Identifier: AGPL-3.0-only
"""
world_sim.py — Phase 7: the smallest living world. A simulation AUTHORITY over the verified causal graph.

This is the layer that makes a world "feel alive" before any graphics exist. It reuses the proven
pipeline (world_format.parse_world / build_causal_graph, world_design.regime) and adds three things the
renderer-boundary work did not need:

  1. richer runtime state per entity   — alive, health, status, plus a DERIVED faction controller;
  2. an event vocabulary               — destroy / damage / capture / transfer / repair, each returning
                                          the honest report {potential, actual, affected, unchanged};
  3. graph-derived factions            — a faction is just an ENTITY (no new format); "control" is
                                          causal reach over the CURRENTLY-ALIVE graph.

THE BOUNDARY HOLDS (Phase 5 carried forward): the simulation knows nothing about meshes. Mutation happens
ONLY through apply_event. snapshot() is frozen; render_primitives() is a pure read. `observation ≠ authority`.

MODEL BOUNDARIES (Arbitrary-Boundary Law — stated, not hidden):
  • "control(entity) = the faction that reaches it in the alive can-affect graph" is a MODEL construct.
    A real game would layer ownership/visibility rules on top; this is the smallest honest definition that
    makes capture/territory-flip observable. contested = reachable by >1 faction; neutral = by none.
  • "faction power = count of alive entities controlled" is a STRUCTURAL count, not a balance/HP number.
    It measures reach in the alive graph, not combat strength. `measured-reach ≠ game-balance`.
  • The discrete event model's divergence is graph propagation, not continuous dynamics.
    `event ≠ measured-dynamics`.

NOT claimed: MMO scale, UE5, networking performance, AI. This is a causal world substrate that can later
project INTO those engines without moving the authority out of the .wrk text + graph.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from hashlib import blake2b

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
from world_format import build_causal_graph, parse_world   # noqa: E402
from world_design import regime                            # noqa: E402

# A faction is an entity that SOURCES one of these relations. No new format — just relation semantics.
CONTROL_RELS = {"controls", "owns", "commands", "holds", "governs", "claims"}
# Relations that mark a contested grab (used only for narration / demo authoring; still ordinary edges).
CONTEST_RELS = {"attacks", "raids", "contests"}

RECORD_BYTES = 16   # nominal full-state record (id+pos+health+status+owner) — matches causal_net
EVENT_BYTES = 8     # nominal causal event id


@dataclass(frozen=True)
class EntityView:
    """Immutable, renderer-facing view of one entity. Frozen ⇒ a renderer physically cannot mutate it."""
    id: str
    pos: tuple
    alive: bool
    status: str
    health: int
    controller: str        # faction id, "contested", or "neutral"
    is_faction: bool
    blast: int             # downstream reach in the FULL graph (potential)
    in_scc: bool


@dataclass(frozen=True)
class Snapshot:
    """Everything a renderer may see — read-only, no back-reference to the authority."""
    entities: tuple        # tuple[EntityView]
    relations: tuple       # tuple[(src, rel, dst)]
    factions: tuple        # tuple[(faction_id, power)]
    events: tuple          # tuple[str] history
    world_size: int


def _sccs(edges):
    """Tarjan-free SCC membership (small graphs): n is in a cycle iff it reaches some m that reaches n."""
    def reach(s):
        seen, st = set(), list(edges.get(s, set()))
        while st:
            x = st.pop()
            if x not in seen:
                seen.add(x); st.extend(edges.get(x, set()))
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


class WorldSim:
    """The authority. RuntimeWorld + causal graph + event log. The ONLY mutation path is apply_event."""

    def __init__(self, world_text: str):
        self.spec = parse_world(world_text)
        self.cg = build_causal_graph(self.spec)
        # runtime state per node
        self.runtime = {}
        for n in self.cg.nodes:
            h = self.spec.entities[n].health if n in self.spec.entities else 100
            self.runtime[n] = {"alive": True, "status": "ok", "health": h, "max": h}
        self.captured = {}       # entity -> faction (explicit ownership override from capture/transfer)
        self.events = []         # committed trajectory (the only record of what occurred)
        self._scc = _sccs(self.cg.edges)
        self.factions = self._find_factions()

    # ---- structure (static) --------------------------------------------------------------------
    def _find_factions(self) -> list:
        facs = set()
        for (s, d), rel in self.cg.labels.items():
            if rel in CONTROL_RELS:
                facs.add(s)
        return sorted(facs)

    def _pos(self, n) -> tuple:
        return tuple(self.spec.entities[n].pos) if n in self.spec.entities else (0.0, 0.0, 0.0)

    # ---- derived (recomputed from runtime; never stored as a second authority) -----------------
    def alive_reach(self, start: str) -> set:
        """Entities reachable from `start` through ALIVE nodes only. A dead node blocks propagation."""
        if start not in self.runtime or not self.runtime[start]["alive"]:
            return set()
        seen, st = set(), [start]
        while st:
            x = st.pop()
            for d in self.cg.edges.get(x, ()):
                if d not in seen and self.runtime[d]["alive"]:
                    seen.add(d); st.append(d)
        return seen

    def controller(self, e: str) -> str:
        """Faction controlling `e` = the faction that reaches it in the alive graph (model boundary).
        Explicit capture overrides reach. Faction controls itself. >1 ⇒ contested; 0 ⇒ neutral."""
        if e in self.factions:
            return e
        if not self.runtime[e]["alive"]:
            return "neutral"
        if e in self.captured and self.runtime.get(self.captured[e], {}).get("alive", False):
            return self.captured[e]
        reaching = [f for f in self.factions if e in self.alive_reach(f)]
        if len(reaching) == 1:
            return reaching[0]
        if len(reaching) > 1:
            return "contested"
        return "neutral"

    def faction_power(self, f: str) -> int:
        """STRUCTURAL count: alive non-faction entities this faction currently controls. Not game-balance."""
        return sum(1 for e in self.cg.nodes
                   if e not in self.factions and self.runtime[e]["alive"] and self.controller(e) == f)

    def _state_vector(self) -> dict:
        """Per-entity observable state used to diff what an event actually changed (incl. derived control)."""
        return {e: (self.runtime[e]["alive"], self.runtime[e]["status"],
                    self.runtime[e]["health"], self.controller(e)) for e in self.cg.nodes}

    # ---- the ONLY mutation path ----------------------------------------------------------------
    def apply_event(self, kind: str, target: str, amount: int = 0, faction: str = "") -> dict:
        """Apply one event; return the honest report {potential, actual, affected, unchanged}.
        potential = entities the event COULD touch (downstream reach ∪ target). actual/affected = what
        DID change (state-vector diff, including derived control flips). unchanged = the rest. Potential ⊇ Actual."""
        if target not in self.cg.nodes:
            raise KeyError(f"no such entity: {target}")
        before = self._state_vector()
        potential = ({target} | self.cg.reach_ge1(target))

        if kind == "destroy":
            self._kill(target)
        elif kind == "damage":
            r = self.runtime[target]
            if r["alive"]:
                r["health"] = max(0, r["health"] - max(0, amount))
                if r["health"] == 0:
                    self._kill(target)
                elif r["status"] == "ok":
                    r["status"] = "damaged"
        elif kind == "repair":
            r = self.runtime[target]
            if r["alive"]:
                r["health"] = min(r["max"], r["health"] + max(0, amount))
                # status recovers to ok only if every node it depends on upstream is alive (no dead source)
                r["status"] = "ok" if self._upstream_alive(target) else r["status"]
            elif self._upstream_alive(target):                       # revive a destroyed entity if its sources are alive
                self.runtime[target] = {**r, "alive": True, "status": "ok", "health": r["max"]}
        elif kind in ("capture", "transfer"):
            if not faction:
                raise ValueError(f"{kind} requires a faction")
            self.captured[target] = faction
        else:
            raise ValueError(f"unknown event kind: {kind!r}")

        after = self._state_vector()
        affected = sorted(e for e in self.cg.nodes if before[e] != after[e])
        self.events.append(f"{kind} {target}" + (f" {amount}" if amount else "") + (f" -> {faction}" if faction else ""))
        n = len(self.cg.nodes)
        return {
            "event": self.events[-1],
            "potential": sorted(potential),
            "actual": affected,
            "affected": affected,
            "unchanged": sorted(set(self.cg.nodes) - set(affected)),
            "n_potential": len(potential),
            "n_actual": len(affected),
            "n_unchanged": n - len(affected),
        }

    def _kill(self, target: str) -> None:
        self.runtime[target] = {**self.runtime[target], "alive": False, "status": "destroyed", "health": 0}
        for d in self.cg.reach_ge1(target):
            if self.runtime[d]["alive"] and self.runtime[d]["status"] == "ok":
                self.runtime[d] = {**self.runtime[d], "status": "disabled"}

    def _upstream_alive(self, e: str) -> bool:
        """True if no node that can reach `e` (its upstream sources) is dead."""
        for s in self.cg.nodes:
            if s != e and e in self.cg.reach_ge1(s) and not self.runtime[s]["alive"]:
                return False
        return True

    # ---- read-only --------------------------------------------------------------------------
    def authority_hash(self) -> str:
        h = blake2b(digest_size=16)
        for k in sorted(self.runtime):
            r = self.runtime[k]
            h.update(f"|{k}:{int(r['alive'])}:{r['status']}:{r['health']}:{self.controller(k)}".encode())
        for e in self.events:
            h.update(("|EV" + e).encode())
        return h.hexdigest()

    def snapshot(self) -> Snapshot:
        ents = tuple(EntityView(
            id=n, pos=self._pos(n), alive=self.runtime[n]["alive"], status=self.runtime[n]["status"],
            health=self.runtime[n]["health"], controller=self.controller(n),
            is_faction=n in self.factions, blast=len(self.cg.reach_ge1(n)), in_scc=n in self._scc,
        ) for n in sorted(self.cg.nodes))
        rels = tuple((s, self.cg.labels[(s, d)], d)
                     for s in sorted(self.cg.edges) for d in sorted(self.cg.edges[s]))
        facs = tuple((f, self.faction_power(f)) for f in self.factions)
        return Snapshot(entities=ents, relations=rels, factions=facs,
                        events=tuple(self.events), world_size=len(self.cg.nodes))

    def inspect(self, e: str) -> dict:
        """What a developer sees when they click an object in the FPS view — pure read of the graph."""
        depends_on = sorted(s for s in self.cg.nodes if e in self.cg.edges.get(s, set()))
        return {
            "entity": e,
            "causal_role": "faction" if e in self.factions else ("hub" if self.cg.reach_ge1(e) else "leaf"),
            "depends_on": depends_on,                       # who can affect me
            "affects": sorted(self.cg.reach_ge1(e)),        # who I can affect (downstream)
            "blast_radius": len(self.cg.reach_ge1(e)),
            "controller": self.controller(e),
            "state": self.runtime[e]["status"], "alive": self.runtime[e]["alive"],
            "health": self.runtime[e]["health"],
        }


def render_primitives(snap: Snapshot) -> tuple:
    """PURE projection: Snapshot → render primitives. Receives only a Snapshot, returns geometry, never
    touches a WorldSim. This is the seam UE5/any engine would implement; the authority stays put."""
    fac_color = {}
    palette = ["#da3633", "#1f6feb", "#2ea043", "#d29922"]
    for i, (f, _p) in enumerate(snap.factions):
        fac_color[f] = palette[i % len(palette)]
    out = []
    for e in snap.entities:
        if not e.alive:
            continue
        if e.is_faction:
            color = fac_color.get(e.id, "#8b949e")
        elif e.controller == "contested":
            color = "#e3742f"
        elif e.controller == "neutral":
            color = "#8b949e"
        else:
            color = fac_color.get(e.controller, "#8b949e")
        if e.status in ("disabled", "destroyed"):
            color = "#5a5f66"
        out.append({"kind": "block", "id": e.id, "pos": e.pos, "color": color,
                    "status": e.status, "controller": e.controller})
    return tuple(out)


# ---- network instrumentation (Phase 4 carried forward; MEASURED STRUCTURE, not network performance) ----
def net_report(world_text: str, kind: str, target: str, amount: int = 0, faction: str = "") -> dict:
    """NAIVE (send every changed record) vs CAUSAL (send the event, client re-derives). Measures bytes,
    entities touched, and reconstruction OP COUNT (deterministic) — NOT wall-clock, NOT latency."""
    a = WorldSim(world_text); rep = a.apply_event(kind, target, amount, faction)
    touched = rep["n_actual"]
    return {
        "naive_bytes": touched * RECORD_BYTES, "naive_msgs": touched,
        "causal_bytes": EVENT_BYTES, "causal_msgs": 1,
        "entities_touched": touched, "reconstruct_ops": touched,   # graph steps to re-derive
        "label": "MEASURED STRUCTURE — NOT NETWORK PERFORMANCE",
    }


def replay(world_text: str, events: list) -> str:
    """Deterministic replay: apply an event list to a fresh world, return the authority hash."""
    w = WorldSim(world_text)
    for ev in events:
        w.apply_event(*ev) if isinstance(ev, tuple) else w.apply_event(**ev)
    return w.authority_hash()


# A two-faction world contesting a reactor, a resource node, and territory. Positions are for the FPS view;
# the simulation ignores them. Control flows THROUGH the reactor so destroying it flips north_territory.
DEMO_WORLD = """
world "Frontier_Prototype"
zone north
zone south
zone contested

entity faction_red:
  zone north
  position -12 0 -10
  controls reactor
  claims resource_node
entity faction_blue:
  zone south
  position 12 0 10
  controls market
  claims resource_node

entity reactor:
  zone north
  position -8 0 -6
  health 100
  powers defense_grid
entity defense_grid:
  zone north
  position -4 0 -2
  health 80
  protects north_territory
entity north_territory:
  zone north
  position -6 0 4
  health 50

entity market:
  zone south
  position 8 0 6
  health 100
  supplies garrison
entity garrison:
  zone south
  position 4 0 2
  health 80
  defends south_territory
entity south_territory:
  zone south
  position 6 0 -4
  health 50

entity resource_node:
  zone contested
  position 0 0 0
  health 60
"""


def main():
    print("world_sim.py — Phase 7: the smallest living world (simulation authority)\n")
    w = WorldSim(DEMO_WORLD)
    print(f"  world '{w.spec.name}'  entities={len(w.cg.nodes)}  factions={w.factions}")
    print(f"  coupling: {regime(w.cg)['label']}\n")
    print("  initial control / power:")
    for f in w.factions:
        owned = sorted(e for e in w.cg.nodes if e not in w.factions and w.controller(e) == f)
        print(f"    {f}: power {w.faction_power(f)}  controls {owned}")
    rn = w.controller("resource_node")
    print(f"    resource_node controller: {rn}  (reachable by both factions ⇒ expect 'contested')\n")

    print("  EVENT: destroy reactor  (faction_red's power source)")
    rep = w.apply_event("destroy", "reactor")
    print(f"    potential (could affect): {rep['potential']}")
    print(f"    actual    (did affect):   {rep['actual']}")
    print(f"    unchanged: {rep['n_unchanged']} of {len(w.cg.nodes)}   (Potential ⊇ Actual)\n")
    print("  after the reactor dies:")
    for f in w.factions:
        print(f"    {f}: power {w.faction_power(f)}")
    print(f"    north_territory controller: {w.controller('north_territory')}  (red can no longer reach it)")
    print(f"    defense_grid status: {w.runtime['defense_grid']['status']}\n")

    before = w.authority_hash()
    prims = render_primitives(w.snapshot())
    after = w.authority_hash()
    print(f"  render produced {len(prims)} primitives; authority hash unchanged by rendering: {before == after}")
    print("  (observation ≠ authority — the renderer is a pure projection.)\n")
    print("  the world is alive: events cause consequences, factions rise and fall, and you can ask WHY.")
    print("  NOT claimed: MMO / UE5 / networking performance. The .wrk text + graph remain the authority.")


if __name__ == "__main__":
    main()
