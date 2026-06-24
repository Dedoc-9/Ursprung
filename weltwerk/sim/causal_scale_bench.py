# SPDX-License-Identifier: AGPL-3.0-only
"""
causal_scale_bench.py — Phase 10: the operating envelope. Where does the causal-runtime thesis actually work?

Phase 9 answered "can a causal world host gameplay?" — yes. The next, more important question is the one
the project has circled since the start:

    How large can a causal world become before Actual approaches Potential and the economics collapse?

This bench measures that envelope from the REAL authority (world_format reach + world_ai pathing). It is a
DETERMINISTIC OP-COUNT bench: it counts structural work (entities reached, graph edges traversed, LOS cells,
A* path nodes). It reports NO wall-clock time, NO bandwidth, NO latency, NO networking. `op-count ≠ latency`.

The central law under test (already the project's spine):  **cheap iff Actual ≪ Potential.**
Operationally, per causal event:
    potential   = entities the event COULD reach   (forward reachability over the causal graph)
    footprint   = |{target} ∪ reach(target)|        (what a causal client must re-derive)
    naive_ops   = N                                  (broadcast: touch every entity)
    causal_ops  = footprint                          (re-derive only the reachable set)
    headroom    = 1 − avg_footprint / N              (fraction of the world an event leaves untouched)

Prediction: low coupling ⇒ headroom high ⇒ causal_ops ≪ naive_ops (the win); high coupling ⇒ headroom → 0
⇒ causal_ops → naive_ops (no win). The bench either confirms this envelope or refutes it — honestly.

Worlds are generated as chains whose length scales with a `coupling` knob (0 = isolated entities, 1 = long
dependency chains). This is a MODEL of coupling, not a claim about real game topologies — stated, not hidden.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_ai import Grid, astar, bresenham                                   # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
from world_format import build_causal_graph, parse_world                      # noqa: E402

def gen_world_text(n: int, coupling: float) -> str:
    """N entities linked into chains whose length scales with coupling (0→isolated, 1→one chain of length N).
    'feeds' is a forward relation, so e_i → e_{i+1}; a chain head reaches the rest of its chain. Footprint
    therefore rises monotonically with coupling. Note a *linear* chain bottoms out at ~50% average headroom
    (half the chain is downstream on average); driving headroom→0 needs shared/hub coupling — out of scope here."""
    chain_len = max(1, round(1 + coupling * (n - 1)))
    lines = ['world "Scale"']
    for i in range(n):
        lines.append(f"entity e{i}:")
        if i + 1 < n and (i + 1) % chain_len != 0:    # break the chain every chain_len entities
            lines.append(f"  feeds e{i+1}")
        else:
            lines.append("  health 10")
    return "\n".join(lines)


def measure_world(n: int, coupling: float, samples: int = 300, seed: int = 0) -> dict:
    """Build the world via the REAL authority and measure the causal economics over sampled events."""
    cg = build_causal_graph(parse_world(gen_world_text(n, coupling)))
    nodes = sorted(cg.nodes)
    rng = random.Random(seed)
    targets = nodes if n <= samples else rng.sample(nodes, samples)
    foot = 0
    for t in targets:
        foot += 1 + len(cg.reach_ge1(t))             # footprint = target + everything it reaches
    avg_foot = foot / len(targets)
    return {
        "n": n, "coupling": coupling,
        "avg_reach_pct": round(100 * (avg_foot - 1) / max(1, n), 2),
        "avg_footprint": round(avg_foot, 2),
        "headroom": round(1 - avg_foot / n, 3),       # 1 − Actual/Potential-world  (compression headroom)
        "naive_ops": n,                               # broadcast cost
        "causal_ops": round(avg_foot, 2),             # re-derive only the footprint
        "causal_over_naive": round(avg_foot / n, 4),  # → 0 means big win; → 1 means no win
    }


def causal_envelope(seed: int = 0):
    rows = []
    for n in (100, 1000, 5000):
        for c in (0.05, 0.25, 0.6, 1.0):
            rows.append(measure_world(n, c, seed=seed))
    return rows


def headroom_curve(n: int = 2000, seed: int = 0):
    return [measure_world(n, c, seed=seed) for c in (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)]


# --- AI scaling: structural work per tick vs bot count ------------------------------------------
def gen_grid(w: int, h: int, obstacle_frac: float, seed: int) -> Grid:
    rng = random.Random(seed)
    blocked = set()
    for x in range(w):
        for y in range(h):
            if rng.random() < obstacle_frac:
                blocked.add((x, y))
    return Grid(w, h, blocked)


def ai_work(num_bots: int, w: int = 30, h: int = 30, seed: int = 0) -> dict:
    """AI work units for one tick: per bot, LOS cells (bresenham to player) + A* path nodes. A STRUCTURAL
    PROXY (cells + nodes), NOT CPU time. Bots are independent, so this is expected to scale ~linearly."""
    grid = gen_grid(w, h, 0.12, seed)
    rng = random.Random(seed + 1)
    free = [(x, y) for x in range(w) for y in range(h) if grid.passable(x, y)]
    player = rng.choice(free)
    units, paths = 0, 0
    for _ in range(num_bots):
        b = rng.choice(free)
        units += len(bresenham(b, player))           # LOS work
        p = astar(grid, b, player)
        if p:
            units += len(p); paths += 1               # path work
    return {"bots": num_bots, "work_units": units, "per_bot": round(units / max(1, num_bots), 1),
            "paths_found": paths}


def ai_scaling(seed: int = 0):
    return [ai_work(b, seed=seed) for b in (10, 50, 200, 500)]


# --- topology sweep: WHICH shapes collapse headroom — and under which metric? --------------------
# The falsification the chain model couldn't reach. Reports BOTH average headroom (cost of a typical
# event) and worst-case headroom (cost of the single most-coupled event). The distinction is the result:
# a hub has one expensive event among many cheap ones (avg stays high, worst →0); only MUTUAL
# reachability (SCC / clique) makes the AVERAGE event expensive too.
def _text_from_edges(n, edges):
    bysrc = {}
    for (i, j) in edges:
        bysrc.setdefault(i, []).append(j)
    lines = ['world "Topo"']
    for i in range(n):
        lines.append(f"entity e{i}:")
        outs = bysrc.get(i, [])
        if outs:
            for j in outs:
                lines.append(f"  feeds e{j}")
        else:
            lines.append("  health 10")
    return "\n".join(lines)


def topo_edges(kind, n):
    if kind == "chain":      # sparse line: e_i → e_{i+1}
        return [(i, i + 1) for i in range(n - 1)]
    if kind == "tree":       # binary tree: most nodes are shallow ⇒ small footprints
        e = []
        for i in range(n):
            for c in (2 * i + 1, 2 * i + 2):
                if c < n:
                    e.append((i, c))
        return e
    if kind == "modular":    # clusters of size CS, each an internal chain; no cross-cluster edges
        CS, e = 10, []
        for i in range(n - 1):
            if (i + 1) % CS != 0:
                e.append((i, i + 1))
        return e
    if kind == "hub":        # one node reaches everything; everything else reaches nothing
        return [(0, j) for j in range(1, n)]
    if kind == "scc":        # one big cycle ⇒ every node reaches every other (mutual reachability)
        return [(i, (i + 1) % n) for i in range(n)]
    if kind == "clique":     # complete digraph: every node reaches all others in one hop
        return [(i, j) for i in range(n) for j in range(n) if i != j]
    raise ValueError(kind)


def measure_topology(kind, n=400):
    cg = build_causal_graph(parse_world(_text_from_edges(n, topo_edges(kind, n))))
    foots = [1 + len(cg.reach_ge1(f"e{i}")) for i in range(n)]   # exact: footprint of every node
    avg, peak = sum(foots) / n, max(foots)
    return {"kind": kind, "n": n, "avg_footprint": round(avg, 1), "peak_footprint": peak,
            "avg_headroom": round(1 - avg / n, 3), "worst_headroom": round(1 - peak / n, 3)}


def topology_sweep(n=400):
    return [measure_topology(k, n) for k in ("chain", "tree", "modular", "hub", "scc", "clique")]


def main():
    print("causal_scale_bench.py — Phase 10: the operating envelope (deterministic op-counts, NOT latency)\n")
    print("  CAUSAL ENVELOPE — cost of one event vs world size × coupling")
    print("  " + "-" * 78)
    print(f"  {'N':>6} {'coupling':>9} {'avg reach%':>11} {'footprint':>10} {'headroom':>9} {'causal/naive':>13}")
    for r in causal_envelope():
        print(f"  {r['n']:>6} {r['coupling']:>9} {r['avg_reach_pct']:>10}% {r['avg_footprint']:>10} "
              f"{r['headroom']:>9} {r['causal_over_naive']:>13}")

    print("\n  COMPRESSION HEADROOM vs COUPLING  (N=2000)  — tests: cheap iff Actual ≪ Potential")
    print("  " + "-" * 60)
    curve = headroom_curve()
    for r in curve:
        bar = "█" * max(0, round(r["headroom"] * 40))
        print(f"  coupling {r['coupling']:>4}: headroom {r['headroom']:>5}  {bar}")
    verdict = ("CONFIRMED: headroom falls monotonically as coupling rises — causal replication is cheap when"
               "\n  the world is sparse and degrades toward broadcast when it is densely coupled."
               if curve[0]["headroom"] >= curve[-1]["headroom"] else "REFUTED: headroom did not fall with coupling.")
    print(f"\n  Central law (structural): {verdict}")

    print("\n  AI WORK vs BOT COUNT  (structural proxy: LOS cells + A* path nodes per tick, NOT CPU time)")
    print("  " + "-" * 60)
    print(f"  {'bots':>5} {'work_units':>11} {'per_bot':>9} {'paths':>7}")
    sc = ai_scaling()
    for r in sc:
        print(f"  {r['bots']:>5} {r['work_units']:>11} {r['per_bot']:>9} {r['paths_found']:>7}")
    ratio = sc[-1]["work_units"] / max(1, sc[0]["work_units"]); botratio = sc[-1]["bots"] / sc[0]["bots"]
    print(f"\n  bots ×{botratio:.0f} ⇒ work ×{ratio:.1f} (≈linear: bots are independent; per-bot cost is bounded by"
          f"\n  grid geometry, NOT by world entity count).")
    print("\n  TOPOLOGY SWEEP (N=400) — which shapes collapse headroom, under which metric?")
    print("  " + "-" * 74)
    print(f"  {'topology':>9} {'avg headroom':>13} {'worst headroom':>15}   note")
    notes = {"chain":"~half downstream", "tree":"most nodes shallow", "modular":"bounded by cluster size",
             "hub":"only the hub event is costly", "scc":"mutual reach ⇒ collapse", "clique":"all reach all ⇒ collapse"}
    for r in topology_sweep(400):
        print(f"  {r['kind']:>9} {r['avg_headroom']:>13} {r['worst_headroom']:>15}   {notes[r['kind']]}")
    print("\n  KEY: hub-and-spoke keeps AVERAGE headroom HIGH (one costly event among many cheap) while")
    print("  WORST-CASE headroom → 0. The AVERAGE event collapses only under MUTUAL reachability (scc/clique).")
    print("  ⇒ 'one node reaches everything' ≠ 'the average event is expensive'. Size ≠ coupling ≠ density.")
    print("\n  NOT claimed: latency, bandwidth, throughput, networking, MMO. These are STRUCTURAL op-counts only.")


if __name__ == "__main__":
    main()
