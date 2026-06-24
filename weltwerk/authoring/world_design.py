# SPDX-License-Identifier: AGPL-3.0-only
"""
world_design.py — Phase 3: the world DESIGNER authority (debugger → world-building instrument).

The author→view→play loop answers "if I change this, what breaks?" This layer answers the design
question: "if I design THIS, what kind of world am I creating?" — before any asset exists. It is the
verified backbone the interactive designer renders; pure Potential-side structural analysis (engine-
independent, regime-independent), reusing the tested world_format + world_lint.

Provides:
  design_warnings(cg)   — design INSIGHTS (not errors): high blast-radius %, single point of failure,
                          feedback loops, unstable dependency chains, orphaned/unreachable entities.
  failure_cascade(cg,n) — the BFS layers an entity's death propagates through (power→doors→defense→…).
  regime(cg)            — world coupling density: bounded (safe) vs dangerous-coupling. MEASURED
                          structure, NOT a prediction.
  simulate_timeline(..) — a deterministic tick sequence of destroy events; scrub "what happened after
                          the generator died". Each tick records cumulative divergence and the
                          potential⊇actual gap.

HONEST: a warning is a design insight, not an error (`structural-risk ≠ failure`); regime is measured
coupling, not a forecast (`measured ≠ predicted`); the discrete destroy model's actual divergence is
graph propagation (`event ≠ measured-dynamics`).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_format import build_causal_graph, parse_world, simulate_destroy   # noqa: E402
from world_lint import criticality, reverse_adj, sccs                        # noqa: E402


def failure_cascade(cg, node: str) -> list:
    """BFS layers of what falls when `node` dies: [[direct], [next], …]."""
    layers, frontier, seen = [], {node}, {node}
    while True:
        nxt = set()
        for f in frontier:
            for m in cg.edges.get(f, ()):
                if m not in seen:
                    nxt.add(m); seen.add(m)
        if not nxt:
            break
        layers.append(sorted(nxt))
        frontier = nxt
    return layers


def cascade_str(cg, node: str) -> str:
    layers = failure_cascade(cg, node)
    reps = [node] + [("{" + ",".join(L) + "}" if len(L) > 1 else L[0]) for L in layers]
    return " → ".join(reps)


def design_warnings(cg) -> list:
    """Design insights over the causal graph. Each is {kind, subject, detail, ...} — risk, not error."""
    n = len(cg.nodes) or 1
    radj = reverse_adj_compat(cg)
    scc_members = set()
    loops = [c for c in sccs(cg) if len(c) > 1]
    for c in loops:
        scc_members.update(c)
    crit = {x: criticality(cg, x) for x in cg.nodes}
    cmax = max(crit.values(), default=0)
    out = []

    # high blast radius — but NOT for feedback-loop members: their high reach IS the loop (flagged below).
    # Reporting it per-member is redundant noise; the genuinely separate insight is a high-blast entity
    # OUTSIDE any loop (a single choke point feeding the tangle).
    for node in sorted(cg.nodes, key=lambda x: (-cg.blast_radius(x), x)):
        pct = cg.blast_radius(node) / n
        if pct >= 0.5 and cg.reach_ge1(node) and node not in scc_members:
            out.append({"kind": "high_blast_radius", "subject": node, "pct": round(pct, 2),
                        "detail": f"affects {round(100 * pct)}% of the world",
                        "cascade": cascade_str(cg, node)})
    for x in sorted(cg.nodes):
        if cmax > 0 and crit[x] == cmax:
            out.append({"kind": "single_point_of_failure", "subject": x, "cost": cmax,
                        "detail": f"removing it severs {cmax} units of influence among survivors"})
    for c in loops:
        out.append({"kind": "feedback_loop", "subject": ",".join(c), "members": c,
                    "detail": f"{len(c)} entities mutually depend — amplification RISK (confirm "
                              f"dynamically); this loop inflates the blast radius of all its members"})
    for x in sorted(cg.nodes):
        deps = cg.reach_ge1_rev(x) if hasattr(cg, "reach_ge1_rev") else _rev_reach(radj, x)
        if deps & scc_members and x not in scc_members:
            out.append({"kind": "unstable_dependency", "subject": x,
                        "detail": "depends on a feedback cluster — its stability is coupled to a loop"})
    for x in sorted(cg.nodes):
        if not cg.edges[x] and not radj[x]:
            out.append({"kind": "orphaned", "subject": x,
                        "detail": "no relations — unreachable / disconnected from the causal world"})
    return out


def reverse_adj_compat(cg):
    try:
        return reverse_adj(cg)
    except Exception:
        r = {n: set() for n in cg.nodes}
        for s in cg.nodes:
            for d in cg.edges[s]:
                r[d].add(s)
        return r


def _rev_reach(radj, start):
    seen, st = set(), list(radj.get(start, ()))
    while st:
        x = st.pop()
        if x not in seen:
            seen.add(x); st.extend(radj.get(x, ()))
    return seen


def regime(cg) -> dict:
    """World coupling density. MEASURED structure, not a forecast. bounded ⇒ safe to optimize;
    expanding ⇒ dangerous coupling (some entity can reach most of the world)."""
    n = len(cg.nodes) or 1
    peak = max((cg.blast_radius(x) for x in cg.nodes), default=0) / n
    label = "bounded (safe for optimization)" if peak < 0.5 else "expanding (dangerous coupling)"
    return {"peak_blast_pct": round(peak, 2), "label": label}


def simulate_timeline(spec, destroy_seq: list) -> list:
    """Deterministic tick sequence: tick k destroys destroy_seq[k-1]. Each tick records cumulative
    dead / diverged and the potential⊇actual gap. Scrub 'what happened after X died'."""
    cg = build_causal_graph(spec)
    ticks = [{"tick": 0, "event": None, "dead": [], "diverged": [], "new": [], "potential": 0, "gap": 0}]
    dead, diverged, potential = set(), set(), set()
    for i, target in enumerate(destroy_seq, 1):
        r = simulate_destroy(cg, target)
        newdiv = set(r["diverged"]) - diverged
        dead.add(target); potential |= set(r["diverged"]); diverged |= set(r["diverged"])
        ticks.append({"tick": i, "event": f"destroy {target}", "dead": sorted(dead),
                      "diverged": sorted(diverged), "new": sorted(newdiv),
                      "potential": len(potential), "gap": len(potential) - len(diverged)})
    return ticks


def world_health_report(cg) -> str:
    """A glance-level report a developer reads BEFORE building a world. All MEASURED structure — the
    'summary' is not a runtime prediction (we never claim prediction; only what the graph already says)."""
    n = len(cg.nodes) or 1
    warns = design_warnings(cg)
    reg = regime(cg)
    loops = [c for c in sccs(cg) if len(c) > 1]
    largest = max((len(c) for c in loops), default=0)
    ranked = sorted(cg.nodes, key=lambda x: (-cg.blast_radius(x), x))[:5]
    L = ["WORLD HEALTH REPORT", "-" * 34,
         f"Coupling: {reg['label']}",
         f"Largest feedback loop (SCC): {largest} node(s)", "",
         "Critical nodes (by blast radius):"]
    for x in ranked:
        pct = cg.blast_radius(x) / n
        fill = max(0, min(10, round(pct * 10)))
        L.append(f"  {x:<14}{'█' * fill}{'░' * (10 - fill)} {round(100 * pct)}%")
    has_cascade = reg["peak_blast_pct"] >= 0.5
    has_loop = bool(loops)
    has_orphan = any(w["kind"] == "orphaned" for w in warns)
    spof = sum(1 for w in warns if w["kind"] == "single_point_of_failure")
    L += ["", "Failure modes:",
          f"  [{'!' if has_cascade else ' '}] cascade risk",
          f"  [{'!' if has_loop else ' '}] feedback loop",
          f"  [{'!' if has_orphan else ' '}] isolated zones", "",
          "Structural summary (MEASURED, not a runtime prediction):",
          f"  max blast radius: {round(100 * reg['peak_blast_pct'])}% of world",
          f"  single points of failure: {spof}",
          f"  causal compression headroom: {'low' if reg['peak_blast_pct'] >= 0.5 else 'high'} "
          f"({'high coupling ⇒ edits reach far ⇒ little to prune' if reg['peak_blast_pct'] >= 0.5 else 'local edits ⇒ prunable'})"]
    return "\n".join(L)


FACTION_WORLD = """
world "Frontier"
zone red_territory
zone blue_territory
zone contested
entity faction_red:
  zone red_territory
  owns reactor
  attacks bridge
entity faction_blue:
  zone blue_territory
  owns market
  allied_with garrison
entity reactor:
  zone red_territory
  health 100
  emits power
entity bridge:
  zone contested
  health 80
  blocks supply_route
entity market:
  zone blue_territory
  trades_with garrison
entity garrison:
  zone blue_territory
  defends bridge
  powered_by reactor
"""


def main():
    from world_format import DEMO_WORLD
    cg = build_causal_graph(parse_world(DEMO_WORLD))
    print("world_design.py — Phase 3 designer authority\n")
    print(f"  regime: {regime(cg)['label']}  (peak blast {int(100*regime(cg)['peak_blast_pct'])}%)\n")
    print("  DESIGN WARNINGS (insights, not errors):")
    for w in design_warnings(cg):
        extra = f"  cascade: {w['cascade']}" if "cascade" in w else ""
        print(f"    ⚠ [{w['kind']}] {w['subject']}: {w['detail']}{extra}")
    print("\n  TIMELINE — destroy the reactor (power), then the gate:")
    for t in simulate_timeline(parse_world(DEMO_WORLD), ["power", "gate"]):
        print(f"    tick {t['tick']}: {t['event'] or 'initial'}  diverged={t['diverged']}  (new: {t['new']})")
    print("\n" + "\n".join("  " + ln for ln in world_health_report(cg).splitlines()))
    print("\n  FACTION sample (causal layer only — owns/attacks/allied/trades parse as relations):")
    fcg = build_causal_graph(parse_world(FACTION_WORLD))
    print(f"    faction_red blast radius: {fcg.blast_radius('faction_red')} → {sorted(fcg.influence('faction_red')-{'faction_red'})}")
    print("\n  mesh is replaceable; the graph is the world.")


if __name__ == "__main__":
    main()
