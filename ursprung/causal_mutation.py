# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/causal_mutation.py — the Causal Mutation Surface (shared objects, multiple causal timelines).

Multiplayer exposes the hard case the membrane hadn't faced: two agents may mutate the *same apparent object*
in their own causal timelines. "The door" is not one thing — it is geometry, material state, destruction
representation, collision authority, network authority, player intent, predicted futures. Each player has a
different causal surface touching the same object.

The renderer never asks **"who owns the door?"** (that is CORE's authority). It asks **"which mutations can
cross observers, and what preparation debt does that create?"** The signal:

    MutationCost = authority_distance × affected_agents × rollback_cost × representation_cost

`authority_distance` (latency/hops to the authoritative owner) and `rollback_cost` are what make this *more*
than Causal Surface Area: a shared object behind delayed replication, where being wrong forces an expensive
rollback, deserves preparation even if its raw divergence is modest. CSA counts how many futures depend on an
object; MutationCost counts how *expensive the disagreement* is when they collide.

The moat holds: this ranks objects for PREPARATION; it never collapses a future or arbitrates ownership.
`object_facets()` names the four faces of an object so they are never conflated — only the physical face is
CORE-authoritative.

CLASSIFICATION: OBSERVER (mutates_core=False). It ranks shared objects for preparation; it commits no state,
selects no future, and arbitrates no ownership. integrity ≠ truth.
"""
from __future__ import annotations

import random

from . import resistance_tensor as rt
from . import causal_surface as cs


def object_facets(obj):
    """The four faces of a shared object — kept distinct so the renderer never conflates them. Only the
    physical face is CORE-authoritative; the rest are downstream / membrane concerns."""
    return {
        "physical": "CORE",           # authoritative state — only the simulation mutates it
        "representational": "VIEW",   # how it is shown (lossy interpretation)
        "readiness": "ALLOCATOR",     # what is prepared for its possible futures
        "causal_claims": "membrane",  # which agents could affect it, and the resulting divergence
    }


def mutation_cost(obj):
    """authority_distance × affected_agents × rollback_cost × representation_cost. How expensive a shared
    mutation's *disagreement* is — the cost of being unprepared when independent timelines collide."""
    authority_distance = max(1, int(obj.get("authority_distance", 1)))
    affected_agents = max(1, int(obj.get("affected_agents", 1)))
    rollback_cost = max(1, int(obj.get("rollback_cost", 1)))
    rep_cost = rt.miss_cost(obj)
    return authority_distance * affected_agents * rollback_cost * rep_cost


# --- the Shared Object Crucible (winner = loses least when reality disagrees) ------------------------

def _crucible_scene(seed=1, n=36):
    """Two SEPARABLE shared classes + solo filler, so the rollback-aware signal actually changes allocation:
      · rollback_heavy  — modest divergence, but EXPENSIVE rollback + far authority (delayed replication).
                          CSA under-ranks it (low divergence); its disagreement loss is HIGH.
      · divergence_heavy— high divergence, but CHEAP rollback + near authority.
                          CSA over-ranks it; its disagreement loss is LOW.
    Under a tight budget the rollback-aware signal must prefer rollback_heavy, where being wrong actually hurts."""
    rng = random.Random(seed)
    objs = {}
    for i in range(n):
        role = i % 6
        rollback_heavy = (role == 0)
        divergence_heavy = (role == 3)
        shared = rollback_heavy or divergence_heavy
        if rollback_heavy:
            agents, diverg, rollback, authority = rng.randint(4, 6), rng.randint(1, 2), rng.randint(8, 10), rng.randint(6, 9)
        elif divergence_heavy:
            agents, diverg, rollback, authority = rng.randint(4, 6), rng.randint(8, 10), rng.randint(1, 2), rng.randint(1, 2)
        else:
            agents, diverg, rollback, authority = 1, 1, 1, 1
        objs["o%02d" % i] = {
            "id": "o%02d" % i,
            "affected_agents": agents, "expected_divergence": diverg,
            "rollback_cost": rollback, "authority_distance": authority,
            # rep sensitivity similar across the two shared classes → the differentiator is rollback, not rep
            "lighting_sensitivity": 7 if shared else 2,
            "reconstruction_sensitivity": 7 if shared else 2,
            "distance": rng.randint(70, 100) if shared else rng.randint(1, 60),
            "visibility": rng.randint(1, 20) if shared else rng.randint(40, 100),
            "branches": rng.randint(3, 4) if shared else 1,
            "shared": shared,
        }
    return objs


def _hamilton(weights, budget):
    keys = sorted(weights); tot = sum(max(0, weights[k]) for k in keys)
    if budget <= 0 or not keys:
        return {k: 0 for k in keys}
    if tot == 0:
        base, rem = divmod(budget, len(keys)); return {k: base + (1 if i < rem else 0) for i, k in enumerate(keys)}
    raw = {k: max(0, weights[k]) * budget / tot for k in keys}; fl = {k: int(raw[k]) for k in keys}
    for k in sorted(keys, key=lambda k: (-(raw[k] - fl[k]), k))[:budget - sum(fl.values())]:
        fl[k] += 1
    return fl


def _worst_case_loss(objs, alloc):
    """Loss when reality DISAGREES with prediction: for each object, the worst outcome is the one whose branch
    was left unprepared — costing rollback_cost × representation miss. A region must fund ALL its branches
    (~10 units each) to be robust. We score the WORST case because the renderer cannot know which branch CORE
    will pick — robustness, not prediction accuracy."""
    total = 0
    for oid, o in objs.items():
        need = 10 * o["branches"]                       # fund every branch to survive any disagreement
        got = alloc.get(oid, 0)
        unprepared_branches = max(0, (need - got)) // 10
        if unprepared_branches > 0:
            total += unprepared_branches * o["rollback_cost"] * rt.miss_cost(o) // 1000
    return total


def crucible(seed=1, budget=240):
    objs = _crucible_scene(seed=seed)
    pol = {
        "proximity": lambda o: max(1, 1_000_000 // (o["distance"] + 1)),
        "visibility": lambda o: o["visibility"],
        "causal_surface_area": lambda o: cs.causal_surface_area(o),
        "causal_mutation_surface": lambda o: mutation_cost(o),
    }
    return {name: _worst_case_loss(objs, _hamilton({oid: wf(o) for oid, o in objs.items()}, budget))
            for name, wf in pol.items()}


def demo(seed=1, budget=240):
    res = crucible(seed=seed, budget=budget)
    print("Shared Object Crucible — 8-player destructible bridge; winner LOSES LEAST when reality disagrees")
    print("  metric = worst-case rollback/representation loss over unprepared branches (lower better)\n")
    for name in ("proximity", "visibility", "causal_surface_area", "causal_mutation_surface"):
        tag = "  ← authority_distance × agents × rollback × rep cost" if name == "causal_mutation_surface" else ""
        print("  %-26s %d%s" % (name, res[name], tag))
    best = min(res, key=lambda k: res[k])
    print("\n  most robust under disagreement: %s" % best)
    print("  the renderer ranks PREPARATION for shared mutations; it never arbitrates ownership (CORE does).")
    print("  Honest bound: constructed world; robustness, not prediction. integrity ≠ truth.")
    return res


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("causal_mutation", OBSERVER, mutates_core=False,
                          note="Causal Mutation Surface = authority_distance × agents × rollback × rep cost; "
                               "ranks shared objects for preparation by disagreement cost; never arbitrates ownership")
    except LayerViolation:
        pass
