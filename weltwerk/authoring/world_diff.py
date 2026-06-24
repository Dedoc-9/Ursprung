# SPDX-License-Identifier: AGPL-3.0-only
"""
world_diff.py — Phase 8: the world *consequence* diff. Git-diff for living worlds, at the structural level.

A text diff says "this line changed." A graph diff says "this edge changed." Neither tells a designer the
thing they actually want: **what changed about the world.** This computes the *consequence* delta between
two `.wrk` specs from the same verified authority everything else uses:

    compare_worlds(old, new) → {
        entities_added/removed, relations_added/removed,         # what the author changed
        blast_radius_delta, peak_blast_before/after,             # who can now reach how far
        spofs_before/after, criticality_delta,                   # single points of failure
        loops_created/removed,                                   # feedback structure
        regime_before/after, coupling_delta,                     # coupling density
        compression_headroom_before/after, compression_delta,    # how prunable the world is
        verdict,                                                 # structural-resilience read (heuristic)
    }

This is a PURE authority-layer primitive: structure in, structure out, deterministic, no runtime, no
renderer, no UI. The Studio projects it later; live-edit is "continuous compare_worlds + re-derive".

EPISTEMIC HONESTY (Dentatus): the `verdict` is a STRUCTURAL HEURISTIC over MEASURED deltas, not a truth or
a runtime prediction. `measured-delta ≠ outcome`; `fewer-SPOFs ≠ better-game`. When the signals disagree
(e.g. SPOFs fall but peak blast rises) the verdict is `mixed` / underdetermined — it does NOT force a binary.
Loops are reported as structure, not condemned: a feedback loop may be intended (see world_validate's
declared-feedback gate). Removing a loop is flagged as a change, never automatically as "better".

SCOPE BOUNDARY (stated, not hidden): this diffs STRUCTURE. Faction *territory/control* deltas depend on the
sim's alive-graph controller and belong to the sim-aware layer (where live-edit lives); they are out of
scope here on purpose, to keep the primitive uncoupled from runtime.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_format import build_causal_graph, parse_world   # noqa: E402
from world_design import design_warnings, regime            # noqa: E402
from world_lint import sccs                                 # noqa: E402


def _spec(x):
    """Accept either .wrk text or an already-parsed WorldSpec."""
    return parse_world(x) if isinstance(x, str) else x


def _relations(spec) -> set:
    """Authored relations as (entity, relation, target) — what the developer actually edits."""
    return {(e.name, rel, tgt) for e in spec.entities.values() for rel, tgt in e.relations}


def _loops(cg) -> set:
    """Feedback loops as frozensets of member ids (order-independent, comparable across worlds)."""
    return {frozenset(c) for c in sccs(cg) if len(c) > 1}


def _spofs(cg) -> list:
    return sorted(w["subject"] for w in design_warnings(cg) if w["kind"] == "single_point_of_failure")


def _headroom(peak: float) -> float:
    """Causal compression headroom: how much an edit DOESN'T reach. High coupling ⇒ low headroom.
    (Same definition world_health_report uses; sparse worlds prune well, dense worlds don't.)"""
    return round(1.0 - peak, 2)


def compare_worlds(old, new) -> dict:
    so, sn = _spec(old), _spec(new)
    go, gn = build_causal_graph(so), build_causal_graph(sn)

    ents_o, ents_n = set(so.entities), set(sn.entities)
    rels_o, rels_n = _relations(so), _relations(sn)

    common = sorted(ents_o & ents_n)
    blast_delta = {}
    for e in common:
        bo, bn = len(go.reach_ge1(e)), len(gn.reach_ge1(e))
        if bo != bn:
            blast_delta[e] = {"before": bo, "after": bn, "delta": bn - bo}

    reg_o, reg_n = regime(go), regime(gn)
    peak_o, peak_n = reg_o["peak_blast_pct"], reg_n["peak_blast_pct"]
    loops_o, loops_n = _loops(go), _loops(gn)
    spof_o, spof_n = _spofs(go), _spofs(gn)

    diff = {
        "entities_added":   sorted(ents_n - ents_o),
        "entities_removed": sorted(ents_o - ents_n),
        "relations_added":   sorted(rels_n - rels_o),
        "relations_removed": sorted(rels_o - rels_n),
        "blast_radius_delta": blast_delta,
        "peak_blast_before": peak_o, "peak_blast_after": peak_n,
        "coupling_delta": round(peak_n - peak_o, 2),
        "spofs_before": spof_o, "spofs_after": spof_n,
        "spof_count_delta": len(spof_n) - len(spof_o),
        "loops_created": sorted(sorted(c) for c in (loops_n - loops_o)),
        "loops_removed": sorted(sorted(c) for c in (loops_o - loops_n)),
        "regime_before": reg_o["label"], "regime_after": reg_n["label"],
        "compression_headroom_before": _headroom(peak_o),
        "compression_headroom_after": _headroom(peak_n),
        "compression_delta": round(_headroom(peak_n) - _headroom(peak_o), 2),
    }
    diff["verdict"] = _verdict(diff)
    return diff


def _verdict(d: dict) -> dict:
    """Resilience read from MEASURED deltas. A structural heuristic, NOT a guarantee or a prediction.
    Two primary safety signals: SPOF count and peak blast radius. If they agree → a direction; if they
    disagree → 'mixed' (underdetermined). Loops/coupling are reported as supporting context, not condemned."""
    spof = d["spof_count_delta"]            # negative = safer
    blast = d["coupling_delta"]             # negative = safer
    signals = []
    if spof < 0: signals.append("safer")
    elif spof > 0: signals.append("riskier")
    if blast < 0: signals.append("safer")
    elif blast > 0: signals.append("riskier")

    if not signals:
        label = "unchanged"
    elif all(s == "safer" for s in signals):
        label = "increased"
    elif all(s == "riskier" for s in signals):
        label = "decreased"
    else:
        label = "mixed"     # signals conflict — underdetermined, do not force a binary

    return {
        "resilience": label,
        "basis": "structural heuristic over measured deltas (SPOF count + peak blast); NOT a runtime prediction",
        "spof_count_delta": spof, "peak_blast_delta": blast,
    }


def _fmt_pct(p): return f"{round(100 * p)}%"


def _arrow(a, b, lower_is_better=True):
    if a == b:
        return "unchanged"
    better = (b < a) if lower_is_better else (b > a)
    return ("improved" if better else "worsened")


def render_diff(old, new) -> str:
    """The 'Structural consequences' report — the part a designer reads. Authored change THEN consequence."""
    d = compare_worlds(old, new)
    L = ["WORLD DIFF — structural consequences", "-" * 38, "Authored change:"]
    if d["entities_added"]:   L.append(f"  + entities: {', '.join(d['entities_added'])}")
    if d["entities_removed"]: L.append(f"  - entities: {', '.join(d['entities_removed'])}")
    for (e, r, t) in d["relations_added"]:   L.append(f"  + {e} {r} {t}")
    for (e, r, t) in d["relations_removed"]: L.append(f"  - {e} {r} {t}")
    if not (d["entities_added"] or d["entities_removed"] or d["relations_added"] or d["relations_removed"]):
        L.append("  (no structural change)")

    loops = "unchanged"
    if d["loops_created"] and d["loops_removed"]: loops = "changed"
    elif d["loops_created"]: loops = f"+{len(d['loops_created'])} created"
    elif d["loops_removed"]: loops = f"-{len(d['loops_removed'])} removed"

    L += ["", "Structural consequences:",
          f"  SPOFs:                 {len(d['spofs_before'])} → {len(d['spofs_after'])}   "
          f"({_arrow(len(d['spofs_before']), len(d['spofs_after']))})",
          f"  Peak blast radius:     {_fmt_pct(d['peak_blast_before'])} → {_fmt_pct(d['peak_blast_after'])}   "
          f"({_arrow(d['peak_blast_before'], d['peak_blast_after'])})",
          f"  Feedback loops:        {loops}",
          f"  Coupling regime:       {d['regime_before']}  →  {d['regime_after']}",
          f"  Compression headroom:  {_fmt_pct(d['compression_headroom_before'])} → "
          f"{_fmt_pct(d['compression_headroom_after'])}   "
          f"({_arrow(d['compression_headroom_before'], d['compression_headroom_after'], lower_is_better=False)})",
          "",
          f"  World resilience:      {d['verdict']['resilience'].upper()}   "
          f"(structural heuristic — measured deltas, not a runtime prediction)"]
    return "\n".join(L)


# Demo: remove a single point of failure with a redundant path. OLD: reactor → power → gate, so `power`
# is the sole mediator between reactor and gate (a SPOF). NEW: add a direct reactor → gate path; now
# losing `power` no longer severs gate from reactor — the SPOF is gone.
OLD_WORLD = """
world "Old"
entity reactor:
  feeds power
entity power:
  feeds gate
entity gate:
  health 100
"""
NEW_WORLD = """
world "New"
entity reactor:
  feeds power
  feeds gate
entity power:
  feeds gate
entity gate:
  health 100
"""


def main():
    print("world_diff.py — Phase 8: the world consequence diff (git-diff for living worlds)\n")
    print(render_diff(OLD_WORLD, NEW_WORLD))
    print("\n  same authority as the rest of the stack; deterministic; structure-only.")
    print("  verdict is a STRUCTURAL HEURISTIC over measured deltas — not truth, not a runtime prediction.")
    print("  (territory/control deltas are runtime ⇒ deferred to the sim-aware layer where live-edit lives.)")


if __name__ == "__main__":
    main()
