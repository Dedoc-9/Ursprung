# SPDX-License-Identifier: AGPL-3.0-only
"""
world_edit.py — Phase 11: LIVE EDIT authority. Editing the .wrk world while it runs.

The rule, enforced here: **edit = NEW authority, not mutate existing truth.** A topology edit produces a
fresh WorldSpec → CausalGraph → WorldSim. We do NOT silently splice the new edges into the running runtime
(that would let the renderer/editor invent state). We re-derive, and we report the discontinuity.

    old_world ──parse──▶ new_world
                          │  validate (reject if it can't even play — never hide invalidity)
                          │  WorldDiff(old, new)  ── structural consequences
                          │  re-derive: graph · factions · control/territory · power
                          ▼
                   {ok, sim(new authority), diff, consequences, carry(player state preserved)}

`carry` is player-facing state the PROJECTION owns (camera, inventory, health) — passed through untouched,
because it is not world authority. The world is rebuilt; the player is not. If the new text is unparseable
or fails the pre-play gate, the edit is REJECTED with a reason and the old authority stands.

This composes the verified primitives: world_format (parse/graph), world_validate (the BLOCK/WARN/INFO
gate), world_diff (consequence diff), world_sim (the runtime authority). No new source of truth.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
from world_sim import WorldSim                              # noqa: E402
from world_diff import compare_worlds                       # noqa: E402
from world_validate import validate                         # noqa: E402
from world_format import build_causal_graph, parse_world    # noqa: E402


def _runtime_delta(old_text: str, new_text: str) -> dict:
    """What re-deriving the world changes in CONTROL/TERRITORY and POWER (both worlds fresh = at t0)."""
    a, b = WorldSim(old_text), WorldSim(new_text)
    common = sorted(set(a.cg.nodes) & set(b.cg.nodes))
    territory = [{"entity": e, "from": a.controller(e), "to": b.controller(e)}
                 for e in common if a.controller(e) != b.controller(e)]
    facs = sorted(set(a.factions) | set(b.factions))
    power = [{"faction": f, "from": (a.faction_power(f) if f in a.factions else None),
              "to": (b.faction_power(f) if f in b.factions else None)} for f in facs
             if (a.faction_power(f) if f in a.factions else None) != (b.faction_power(f) if f in b.factions else None)]
    gained = sorted(f["faction"] for f in power if (f["to"] or 0) > (f["from"] or 0))
    lost = sorted(f["faction"] for f in power if (f["to"] or 0) < (f["from"] or 0))
    return {"territory_changes": territory, "faction_power_changes": power,
            "factions_gained_territory": gained, "factions_lost_territory": lost}


def apply_edit(old_text: str, new_text: str, carry: dict = None) -> dict:
    """Attempt a live edit. Returns a result dict; on success `sim` is the NEW authority and `carry`
    (player state) is preserved verbatim. On failure (`ok=False`) the old authority should stand."""
    carry = dict(carry) if carry else {}

    # 1. parse — an unparseable edit is rejected (the old world stands)
    try:
        spec = parse_world(new_text)
        cg = build_causal_graph(spec)
    except Exception as ex:  # noqa: BLE001
        return {"ok": False, "reason": f"parse error: {ex}", "carry": carry,
                "sim": None, "diff": None, "consequences": None}

    # 2. pre-play gate — an edit that can't play is rejected, NOT silently rebuilt (no hidden invalid state)
    v = validate(cg)
    if not v["can_play"]:
        blocks = [x for x in v["validations"] if x["level"] == "BLOCK"]
        reason = "invalid: " + "; ".join(f"{b['kind']} {b.get('subject') or ''}".strip() for b in blocks)
        return {"ok": False, "reason": reason, "carry": carry,
                "sim": None, "diff": None, "consequences": None, "validations": v["validations"]}

    # 3. consequence diff + runtime delta — answer the designer's questions
    diff = compare_worlds(old_text, new_text)
    rt = _runtime_delta(old_text, new_text)
    loops_created = diff["loops_created"]
    spof_removed = sorted(set(diff["spofs_before"]) - set(diff["spofs_after"]))
    spof_added = sorted(set(diff["spofs_after"]) - set(diff["spofs_before"]))
    consequences = {
        "what_changed": {"entities_added": diff["entities_added"], "entities_removed": diff["entities_removed"],
                         "relations_added": diff["relations_added"], "relations_removed": diff["relations_removed"]},
        "spofs_removed": spof_removed, "spofs_added": spof_added,
        "loops_created": loops_created, "loops_removed": diff["loops_removed"],
        "peak_blast_before": diff["peak_blast_before"], "peak_blast_after": diff["peak_blast_after"],
        "resilience": diff["verdict"]["resilience"],
        "territory_changes": rt["territory_changes"],
        "factions_gained_territory": rt["factions_gained_territory"],
        "factions_lost_territory": rt["factions_lost_territory"],
    }

    # 4. NEW authority — rebuild the runtime; carry (player state) is preserved untouched
    sim = WorldSim(new_text)
    return {"ok": True, "reason": "rebuilt (edit = new authority)", "carry": carry,
            "sim": sim, "diff": diff, "consequences": consequences, "validations": v["validations"]}


def explain(sim: WorldSim, entity: str) -> dict:
    """Runtime 'why' answers from the live authority (not the static graph): why neutral / who controls /
    what it depends on / what depends on it. Uses the current alive-graph controller, so it reflects damage."""
    if entity not in sim.cg.nodes:
        return {"entity": entity, "error": "no such entity"}
    ctrl = sim.controller(entity)
    reaching = [f for f in sim.factions if entity in sim.alive_reach(f)]
    depends_on = sorted(s for s in sim.cg.nodes if entity in sim.cg.edges.get(s, set()))
    dependents = sorted(sim.cg.reach_ge1(entity))
    if ctrl == "neutral":
        why = "no faction can reach it in the alive graph (its power/control path is broken or absent)"
    elif ctrl == "contested":
        why = f"reachable by multiple factions in the alive graph: {sorted(reaching)}"
    else:
        why = f"only {ctrl} reaches it in the alive graph"
    return {"entity": entity, "controller": ctrl, "why_controller": why,
            "alive": sim.runtime[entity]["alive"], "status": sim.runtime[entity]["status"],
            "health": sim.runtime[entity]["health"], "powered": sim.powered(entity),
            "depends_on": depends_on, "dependents": dependents,
            "blast_radius": len(dependents), "reaching_factions": sorted(reaching)}


# OLD: reactor → power → gate, so `power` is the sole mediator (a SPOF). NEW: add a redundant direct
# reactor → gate path (NOT a longer chain) — now losing `power` no longer severs gate. SPOF removed.
DEMO_OLD = """
world "Base"
entity faction_red:
  controls reactor
entity reactor:
  feeds power
entity power:
  feeds gate
entity gate:
  health 100
"""
DEMO_NEW = """
world "Base"
entity faction_red:
  controls reactor
entity reactor:
  feeds power
  feeds gate
entity power:
  feeds gate
entity gate:
  health 100
"""


def main():
    print("world_edit.py — Phase 11: live edit (edit = new authority)\n")
    res = apply_edit(DEMO_OLD, DEMO_NEW, carry={"camera": [0, 1.7, 20], "health": 80, "ammo": 24})
    print(f"  ok={res['ok']}  reason: {res['reason']}")
    c = res["consequences"]
    print(f"  relations added: {c['what_changed']['relations_added']}")
    print(f"  SPOFs removed: {c['spofs_removed']}   resilience: {c['resilience']}")
    print(f"  (added a redundant reactor→gate path around the `power` mediator)")
    print(f"  carry preserved (player state untouched): {res['carry']}\n")
    bad = apply_edit(DEMO_OLD, "world \"X\"\nentity a:\n  depends_on b\nentity b:\n  depends_on a\n",
                     carry={"health": 80})
    print(f"  invalid edit (undeclared feedback loop) ⇒ ok={bad['ok']}  reason: {bad['reason']}")
    print(f"  old authority stands; player state preserved: {bad['carry']}")
    print("\n  edit = NEW authority; the discontinuity is reported, never hidden. observation ≠ authority.")


if __name__ == "__main__":
    main()
