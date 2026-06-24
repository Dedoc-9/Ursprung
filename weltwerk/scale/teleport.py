# SPDX-License-Identifier: AGPL-3.0-only
"""
teleport.py — long-range coupling, and the two layers it forces apart.

Nearest-neighbour diffusion (light_cone.py) is a model of GEOGRAPHY. MMOs become hard when geography
stops being the only topology: auction houses, guild storage, global markets, portals, chat-driven
coordination — all couple distant regions. This probe adds a TELEPORT edge (chunk a ↔ chunk b, far
apart) and measures what it does to the counterfactual cost.

THE ARCHITECTURAL POINT THIS MAKES CONCRETE (the merge): a counterfactual has two cost layers —
  POTENTIAL cone  = what COULD be affected = topological reachability = a conservative DEPENDENCY graph
                    (safe, correct, pessimistic — what a compiler computes).
  ACTUAL divergence = what WAS affected = measured CHANGE PROPAGATION (a lower bound, the truth).
A teleport edge makes the POTENTIAL cone explode (the far chunk is reachable in one hop). But ACTUAL
divergence can stay sparse — an attenuated perturbation crossing one edge may barely move the far
region. So an observer that re-simulates only where divergence is MEASURED (not merely reachable)
recovers the win exactly where the conservative cone loses it. The observer becomes an ALLOCATOR.

This is correct, not a heuristic: a chunk can diverge at t+1 ONLY if one of its inputs actually diverged
at t. So pruning the frontier to measured-divergence + its immediate neighbours can never miss a real
effect. test_teleport.py proves both reconstructions byte-identical to a full honest sim.

SEPARATORS:
  potential ≠ actual            (dependency reachability ≠ measured change propagation)
  reachable ≠ affected          (a teleport edge changes reachability; it may not change much)
  conservative-safe ≠ cheap     (the safe upper bound can be 12× the truth — measured)
  observer-as-description ≠ observer-as-allocation  (measuring actual divergence DECIDES what to sim)
"""
from __future__ import annotations

from dataclasses import dataclass

from cow_world import (ChunkState, Edit, Rules, apply_edit, genesis,
                       snapshot_hash, step_chunk)

EVIDENCE = "EXACT_UNDER_MODEL"
LEAK_PCT = 10


class Topology:
    """A ring of n chunks plus optional long-range (teleport) edges. Undirected; deterministic order."""
    def __init__(self, n: int, teleport_edges: tuple = ()):
        self.n = n
        adj = {c: set() for c in range(n)}
        for c in range(n):
            adj[c].add((c - 1) % n)
            adj[c].add((c + 1) % n)
        for a, b in teleport_edges:
            adj[a].add(b)
            adj[b].add(a)
        self.adj = {c: tuple(sorted(v)) for c, v in adj.items()}
        self.teleport_edges = tuple(teleport_edges)

    def neighbors(self, c: int) -> tuple:
        return self.adj[c]


def _leak(resource: int) -> int:
    return (resource * LEAK_PCT) // 100


def next_chunk(get, d: int, topo: Topology, rules: Rules, seed: int, tick: int) -> ChunkState:
    """Coupled transition over an arbitrary topology: local dynamics + diffusion to/from ALL neighbours
    (ring and teleport alike). Outflow scales with degree so resource is conserved-ish per edge."""
    nbrs = topo.neighbors(d)
    sd = get(d)
    inflow = sum(_leak(get(k).resource) for k in nbrs)
    outflow = len(nbrs) * _leak(sd.resource)
    stepped = step_chunk(sd, rules, seed, d, tick)
    new_res = max(0, min(rules.regen_cap, stepped.resource + inflow - outflow))
    return ChunkState(ents=stepped.ents, resource=new_res)


def full_sim_traced(snap: dict, topo: Topology, rules: Rules, seed: int, horizon: int) -> tuple[list, int]:
    traj = [dict(snap)]
    cost = 0
    state = dict(snap)
    for t in range(horizon):
        cur = state
        nxt = {}
        for d in range(topo.n):
            cost += cur[d].count()
            nxt[d] = next_chunk(lambda i: cur[i], d, topo, rules, seed, t)
        state = nxt
        traj.append(state)
    return traj, cost


@dataclass(frozen=True)
class Reconstruction:
    line_b: dict
    cone_count: tuple        # chunks simulated per tick (POTENTIAL for conservative; ACTUAL-frontier for pruned)
    actual_count: tuple      # chunks that genuinely differ from line A per tick
    cost: int                # entity-steps simulated
    pruned: bool


def reconstruct(snap: dict, topo: Topology, rules: Rules, seed: int, edit: Edit,
                horizon: int, prune: bool) -> Reconstruction:
    """Counterfactual-by-difference. prune=False → conservative (whole cone propagates, dependency
    analysis). prune=True → frontier follows MEASURED divergence (change propagation, the allocator)."""
    traj_a, _ = full_sim_traced(snap, topo, rules, seed, horizon)
    snap_b, rules_b, dirty0 = apply_edit(snap, rules, edit)

    tracked = set(dirty0)
    b_state = {c: snap_b[c] for c in tracked}
    cone_count = [len(tracked)]
    actual_count = [sum(1 for c in tracked if snap_b[c] != traj_a[0][c])]
    cost = 0

    for t in range(horizon):
        if prune:
            base = {c for c in tracked if b_state[c] != traj_a[t][c]}   # only ACTUALLY-diverged propagate
        else:
            base = set(tracked)                                         # conservative: all reachable propagate
        frontier = set(base)
        for c in base:
            frontier.update(topo.neighbors(c))
        get = lambda i, _t=t, _b=b_state: _b[i] if i in _b else traj_a[_t][i]
        new_b = {}
        for d in sorted(frontier):
            cost += get(d).count()
            new_b[d] = next_chunk(get, d, topo, rules_b, seed, t)
        b_state = new_b
        tracked = frontier
        cone_count.append(len(tracked))
        actual_count.append(sum(1 for d in b_state if b_state[d] != traj_a[t + 1][d]))

    line_b = dict(traj_a[horizon])
    for d in b_state:
        line_b[d] = b_state[d]
    return Reconstruction(line_b=line_b, cone_count=tuple(cone_count),
                          actual_count=tuple(actual_count), cost=cost, pruned=prune)


def brute_force_edit_future(snap: dict, topo: Topology, rules: Rules, seed: int, edit: Edit, horizon: int) -> dict:
    snap_b, rules_b, _ = apply_edit(snap, rules, edit)
    traj, _ = full_sim_traced(snap_b, topo, rules_b, seed, horizon)
    return traj[horizon]


@dataclass(frozen=True)
class TeleportReport:
    conservative: Reconstruction
    pruned: Reconstruction
    naive_cost: int
    n_chunks: int
    has_teleport: bool
    evidence_class: str = EVIDENCE

    def render(self) -> str:
        c, p = self.conservative, self.pruned
        peak_actual = max(c.actual_count)
        peak_cone = max(c.cone_count)
        return (f"  [{self.evidence_class}] teleport={self.has_teleport}  "
                f"peak potential-cone={peak_cone}/{self.n_chunks}  peak actual-divergence={peak_actual}\n"
                f"    cost: conservative={c.cost}  pruned={p.cost}  naive={self.naive_cost}  "
                f"(pruned/naive {p.cost / self.naive_cost:.1%}, conservative/naive {c.cost / self.naive_cost:.1%})")


def measure(snap: dict, topo: Topology, rules: Rules, seed: int, edit: Edit, horizon: int) -> TeleportReport:
    cons = reconstruct(snap, topo, rules, seed, edit, horizon, prune=False)
    pru = reconstruct(snap, topo, rules, seed, edit, horizon, prune=True)
    n_entities = sum(cs.count() for cs in snap.values())
    return TeleportReport(conservative=cons, pruned=pru, naive_cost=n_entities * horizon,
                          n_chunks=topo.n, has_teleport=bool(topo.teleport_edges))


if __name__ == "__main__":
    snap = genesis(n_entities=4000, n_chunks=200, seed=0)
    rules = Rules()
    edit = Edit("cull_pred_chunk", chunk=5)
    print("teleport.py — long-range coupling: potential cone vs actual divergence\n")
    ring = Topology(200)
    tele = Topology(200, teleport_edges=((5, 130),))
    print("  nearest-neighbour only:")
    print(measure(snap, ring, rules, 0, edit, horizon=30).render())
    print("\n  with one teleport edge (5 ↔ 130):")
    print(measure(snap, tele, rules, 0, edit, horizon=30).render())
    print("\n  (a teleport edge explodes the POTENTIAL cone; the PRUNED observer tracks ACTUAL spread)")
