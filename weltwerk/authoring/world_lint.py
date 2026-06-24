# SPDX-License-Identifier: AGPL-3.0-only
"""
world_lint.py — a causal design linter (the "World Author" core).

It answers a question no renderer can: *"Show me the causal structure of my world and tell me where I've
accidentally created feedback, runaway influence, single points of failure, or dead zones."* It found a
5-node feedback cluster in the fortress demo that the author did not consciously write — this turns that
one-off catch into a repeatable diagnostic pass.

KEY PROPERTY (why this is regime-INDEPENDENT and useful NOW): every check operates purely on **Potential**
— structural reachability over the declared dependency graph. It never touches **Actual** (which needs
dynamics and is hostage to the Lyapunov regime). So the linter is exact and useful whether or not the
runtime allocator wins in a given dynamical regime. It reports *where to look*; the runtime reports
*whether it bites*.

DIAGNOSTICS (all exact over the declared graph):
  feedback clusters  — SCCs of size > 1: where amplification COULD occur (risk, confirm dynamically)
  load-bearing       — high out-reach (blast radius): an edit here has large potential reach
  exposure           — high in-reach: many entities can affect this one (fragile / over-coupled)
  bottleneck         — structural criticality: total influence lost if this node is removed (single point)
  dead / isolated    — no in- and no out-edges: inert / disconnected from the causal graph

HONEST FRAMING: these are structural **necessary-conditions and risks, not behavioral verdicts**.
`structural-cycle ≠ measured-amplification`; `high-potential-reach ≠ high-actual-impact`. The linter says
where the risk lives; only the runtime (amplify.py / divergence) says whether it materialises.
"""
from __future__ import annotations

from dataclasses import dataclass

from world_spec import CausalGraph, FORTRESS, parse_spec


def _reach(adj: dict, start: str) -> set:
    seen, stack = set(), list(adj.get(start, ()))
    while stack:
        x = stack.pop()
        if x not in seen:
            seen.add(x)
            stack.extend(adj.get(x, ()))
    return seen


def reverse_adj(g: CausalGraph) -> dict:
    radj = {n: set() for n in g.nodes}
    for s in g.nodes:
        for d in g.edges[s]:
            radj[d].add(s)
    return radj


def sccs(g: CausalGraph) -> list:
    """Strongly connected components (mutual reachability is an equivalence relation). Sorted, partitioned."""
    reach = {n: g.reach_ge1(n) for n in g.nodes}
    seen, comps = set(), []
    for n in sorted(g.nodes):
        if n in seen:
            continue
        comp = {n} | {m for m in reach[n] if n in reach.get(m, set())}
        seen |= comp
        comps.append(sorted(comp))
    return comps


def criticality(g: CausalGraph, v: str) -> int:
    """Potential influence MEDIATED by v: reach lost AMONG THE SURVIVING nodes when v is removed.
    Both terms count reach restricted to survivors (nodes∖{v}), so paths *to* v don't inflate the score
    — only paths *through* v count. A leaf therefore scores 0; a chain's middle node scores >0."""
    survivors = g.nodes - {v}
    full = sum(len(g.reach_ge1(n) & survivors) for n in survivors)
    sub = {n: (g.edges[n] - {v}) for n in survivors}        # reach_sub ⊆ survivors automatically
    minus = sum(len(_reach(sub, n)) for n in survivors)
    return full - minus


@dataclass(frozen=True)
class Diagnostic:
    severity: str       # "warn" | "info"
    kind: str
    subject: str
    detail: str


def lint(g: CausalGraph) -> list:
    radj = reverse_adj(g)
    diags = []

    # feedback clusters (SCCs > 1) — amplification RISK
    for comp in sccs(g):
        if len(comp) > 1:
            diags.append(Diagnostic("warn", "feedback-cluster", ",".join(comp),
                                    f"strongly connected component of {len(comp)} entities — amplification "
                                    f"RISK (a cycle; confirm dynamically, structural-cycle ≠ measured-amp)"))

    # load-bearing (out-reach) and exposure (in-reach)
    out_rank = sorted(g.nodes, key=lambda n: (-g.blast_radius(n), n))
    in_rank = sorted(g.nodes, key=lambda n: (-len(_reach(radj, n)), n))
    if out_rank:
        top = out_rank[0]
        diags.append(Diagnostic("info", "load-bearing", top,
                                f"largest potential blast radius ({g.blast_radius(top)}/{len(g.nodes)}) "
                                f"— an edit here can reach the most"))
    for n in in_rank:
        ex = len(_reach(radj, n))
        if ex >= max(2, len(g.nodes) // 2):
            diags.append(Diagnostic("info", "exposure", n,
                                    f"reachable from {ex} entities — heavily coupled / sensitive"))

    # bottlenecks — structural criticality
    crit = {n: criticality(g, n) for n in g.nodes}
    cmax = max(crit.values(), default=0)
    if cmax > 0:
        for n in sorted(g.nodes, key=lambda n: (-crit[n], n)):
            if crit[n] == cmax:
                diags.append(Diagnostic("warn", "bottleneck", n,
                                        f"removing it costs {crit[n]} units of total potential influence "
                                        f"— a structural single point"))

    # dead / isolated
    for n in sorted(g.nodes):
        if not g.edges[n] and not radj[n]:
            diags.append(Diagnostic("info", "isolated", n, "no in- or out-edges — inert / disconnected"))

    return diags


def report(g: CausalGraph) -> str:
    lines = [f"  causal lint — {len(g.nodes)} entities, regime: {g.regime()}"]
    diags = lint(g)
    if not diags:
        lines.append("  (clean — no structural risks found)")
    for d in diags:
        tag = "⚠ " if d.severity == "warn" else "· "
        lines.append(f"  {tag}[{d.kind}] {d.subject}: {d.detail}")
    return "\n".join(lines)


def main():
    g = parse_spec(FORTRESS)
    print("world_lint.py — causal design linter (structural; Potential-side; regime-independent)\n")
    print(report(g))
    print("\n  These are structural RISKS, not verdicts. The linter says where to look; the runtime "
          "(amplify.py / divergence) says whether it bites.")


if __name__ == "__main__":
    main()
