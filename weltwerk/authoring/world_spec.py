# SPDX-License-Identifier: AGPL-3.0-only
"""
world_spec.py — text → causal TOPOLOGY (not text → geometry).

The thesis the whole project earned: work on a world's causal structure first; geometry and art are a
*later projection*. This is the authoring front: a declarative spec whose causal CONSEQUENCES are
measured by the engine — "what does editing this entity affect?" is exactly the Potential reachability
from reachability_algebra, now over a NAMED entity graph instead of a chunk ring.

DSL (one relation per line):  `<src> <relation> <dst>`  — a directed causal edge: editing/destroying
`src` can affect `dst`. `relation` is kept for display (supports / connected_to / collapses_into / …).
`entity <name>` declares an isolated node. `#` starts a comment.

WHAT IS MEASURED (exact over the DECLARED graph):
  influence(e)  = reflexive reachability of e = the Potential blast radius (who an edit on e can reach).
  in_cycle(e)   = e participates in a feedback loop (e reaches itself in ≥1 step).
  regime flag   = DAG (no cycles → bounded blast radii, allocator-friendly) vs HAS-CYCLES (feedback →
                  AMPLIFICATION RISK).

HONEST BOUNDARIES (declared, per the no-inflation rule):
  * the spec is a DECLARED authoring input (what a human/LLM asserts) — untrusted until measured here;
  * a structural cycle is an amplification-RISK flag, NOT a measured λ>0: `structural-cycle ≠
    measured-amplification` — only running dynamics (amplify.py) confirms whether a loop actually
    amplifies or is damped;
  * geometry is downstream and NOT produced here. Topology is cheap to change; geometry is expensive,
    so the causal topology is the durable artifact and meshes are regenerable projections of it.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CausalGraph:
    nodes: set = field(default_factory=set)
    edges: dict = field(default_factory=dict)       # src -> set(dst)
    labels: dict = field(default_factory=dict)      # (src,dst) -> relation

    def add_node(self, n: str) -> None:
        self.nodes.add(n)
        self.edges.setdefault(n, set())

    def add_edge(self, src: str, rel: str, dst: str) -> None:
        self.add_node(src)
        self.add_node(dst)
        self.edges[src].add(dst)
        self.labels[(src, dst)] = rel

    # -- the measured quantities ----------------------------------------------------------------
    def reach_ge1(self, start: str) -> set:
        """Nodes reachable from `start` in ≥1 step (transitive closure of successors)."""
        seen, stack = set(), list(self.edges.get(start, ()))
        while stack:
            n = stack.pop()
            if n not in seen:
                seen.add(n)
                stack.extend(self.edges.get(n, ()))
        return seen

    def influence(self, e: str) -> set:
        """Potential blast radius: {e} ∪ everything an edit on e can reach (reflexive reachability)."""
        return {e} | self.reach_ge1(e)

    def in_cycle(self, e: str) -> bool:
        return e in self.reach_ge1(e)

    def cyclic_nodes(self) -> set:
        return {n for n in self.nodes if self.in_cycle(n)}

    def regime(self) -> str:
        return "HAS-CYCLES (amplification risk)" if self.cyclic_nodes() else "DAG (bounded blast radii)"

    def blast_radius(self, e: str) -> int:
        return len(self.influence(e))


def parse_spec(text: str) -> CausalGraph:
    g = CausalGraph()
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        toks = line.split()
        if toks[0] == "entity" and len(toks) == 2:
            g.add_node(toks[1])
        elif len(toks) == 3:
            src, rel, dst = toks
            g.add_edge(src, rel, dst)
        else:
            raise ValueError(f"cannot parse spec line: {raw!r} (expected '<src> <rel> <dst>' or 'entity <name>')")
    return g


# A demo fortress. The structural half (keep/towers/walls collapsing into the courtyard) is an acyclic
# DAG with bounded blast radii. The "world systems" half contains feedback — and the detector finds MORE
# of it than the author consciously wrote: the intended loop is supply ↔ garrison (a 2-cycle), but
# `gate obstructs courtyard` closes a SECOND, unintended loop
#   courtyard →(connected_to) market →(feeds) garrison →(defends) gate →(obstructs) courtyard
# which interlocks with the supply loop into one 5-node SCC {courtyard, market, garrison, gate, supply}.
# That catch is the point: the tool surfaces amplification-risk feedback the author didn't realize they
# authored, before any geometry exists. (Risk only — `structural-cycle ≠ measured-amplification`.)
FORTRESS = """
# structural dependencies — editing/destroying the src can affect the dst
keep        supports     wall_n
keep        supports     wall_s
wall_n      collapses_into courtyard
wall_s      collapses_into courtyard
tower_ne    supports     wall_n
tower_nw    supports     wall_n
gate        obstructs    courtyard
courtyard   connected_to market
market      feeds        garrison
garrison    defends      gate
# the intended supply-economy loop — but see the note above: it is not the only cycle present:
garrison    consumes     supply
supply      sustains     garrison
"""


def main():
    g = parse_spec(FORTRESS)
    print("world_spec.py — text → causal topology (not geometry)\n")
    print(f"  entities={len(g.nodes)}  edges={sum(len(v) for v in g.edges.values())}  regime: {g.regime()}\n")
    for e in sorted(g.nodes):
        cyc = "  ⟲ in feedback loop" if g.in_cycle(e) else ""
        print(f"  edit {e:<11} → blast radius {g.blast_radius(e):>2}  {sorted(g.influence(e) - {e})}{cyc}")
    print(f"\n  cyclic (amplification-risk) entities: {sorted(g.cyclic_nodes())}")
    print("  NOTE: a cycle flags RISK, not measured amplification — confirm with amplify.py. Geometry is downstream.")


if __name__ == "__main__":
    main()
