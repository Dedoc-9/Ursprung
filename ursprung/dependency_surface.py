# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/dependency_surface.py — Dependency Surface Area + Preparation Value (the hidden resource: access).

The limiting factor is not how much fidelity budget exists, but whether the system has the **dependency graph**
needed to spend that budget intelligently. A next-gen renderer is less `more samples → more pixels` and more
`dependency knowledge → prediction → preparation → stable representation`. The hidden resource is
**dependency access**.

Fidelity is downstream of dependency visibility. If the renderer only sees `draw mesh A`, it is already late.
If it sees that A depends on its material family, lighting regime, nearby actors, possible collisions,
animation/destruction states, and streaming boundaries, it can prepare. A shader-cache miss is exactly this:
"a representation was needed whose prerequisites were not available" — transition debt.

But asking for *everything* recreates the explosion (load all assets, keep all variants, predict all
futures). So the quantity is not "what objects exist" but **Dependency Surface Area** — what dependencies
become relevant *if this object changes* — and access is spent by value:

    Preparation Value = Causal Surface Area × Dependency Access

A shared object has a larger dependency surface (more systems coupled to its mutation), so the renderer needs
enough dependency information to know *where surprises will be expensive* — not prophecy. Plugability is the
dependency-contract form of this (`provider_contract.py`): a provider declares the dependencies it requires
and its failure mode if it does not get them.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures dependency exposure and ranks where access is worth
spending; it commits no state and asserts no truth. integrity ≠ truth.

HONEST BOUND: the dependency kinds and miss-costs are declared proxies; the result is the *shape* (fidelity
tracks dependency access; access is spent by value), not the constants. They expire on a real engine graph.
"""
from __future__ import annotations

import random

from . import causal_surface as cs

DEPENDENCY_KINDS = ("material", "geometry", "lighting", "animation", "destruction", "sound",
                    "occlusion", "visibility", "network_authority", "shader_variants", "streaming")


def dependency_surface_area(obj):
    """How many systems become relevant if this object CHANGES — the count/weight of coupled dependencies,
    not the object's complexity. A door coupled to hinge animation + destruction + sound + lighting +
    occlusion + visibility + network + shaders has a large dependency surface; a static prop has a tiny one."""
    deps = obj.get("dependencies", ["material"])
    return max(1, len(set(deps) & set(DEPENDENCY_KINDS)) or len(deps))


def dependency_access(obj):
    """How much of that surface the renderer can actually SEE (0..100). Low access ⇒ the renderer is late ⇒
    fidelity is bounded regardless of sample budget."""
    return max(0, min(100, int(obj.get("dependency_access", 100))))


def preparation_value(obj):
    """Preparation Value = Causal Surface Area × Dependency Access. You can only prepare what you can both
    foresee (CSA) and see the prerequisites for (access)."""
    return cs.causal_surface_area(obj) * dependency_access(obj) // 100


# --- bench: fidelity is downstream of dependency visibility -----------------------------------------

def _scene(seed=1, n=30):
    """Objects with a true dependency set and a per-object miss cost (CSA-scaled). A renderer that cannot see
    a dependency cannot prepare it, so its representation arrives late = unprepared debt."""
    rng = random.Random(seed)
    objs = {}
    for i in range(n):
        shared = (i % 5 == 0)
        ndeps = rng.randint(6, 9) if shared else rng.randint(1, 3)
        objs["o%02d" % i] = {
            "id": "o%02d" % i,
            "dependencies": rng.sample(DEPENDENCY_KINDS, ndeps),
            "affected_agents": rng.randint(3, 6) if shared else 1,
            "expected_divergence": rng.randint(3, 6) if shared else 1,
            "lighting_sensitivity": rng.randint(5, 9) if shared else 2,
            "reconstruction_sensitivity": rng.randint(5, 9) if shared else 2,
        }
    return objs


def access_debt(objs, access_level):
    """Unprepared debt at a uniform dependency-access level: the fraction of each object's dependency surface
    the renderer CANNOT see, weighted by its CSA miss cost. Lower access ⇒ more late representations."""
    total = 0
    for o in objs.values():
        unseen = (100 - access_level) * dependency_surface_area(o) // 100
        total += unseen * cs.causal_surface_area(o) // 100
    return total


def value_ranked_debt(objs, exposure_budget):
    """With a fixed EXPOSURE budget (you cannot see everything), expose dependencies ranked by Preparation
    Value vs uniformly. Returns {policy: residual debt}. value-ranked spends access where it is worth most."""
    items = []  # one entry per (object) unit of dependency surface, with its marginal value
    for o in objs.values():
        for _ in range(dependency_surface_area(o)):
            items.append((preparation_value(o), cs.causal_surface_area(o), o["id"]))
    total_units = len(items)
    # value-ranked: expose the highest-Preparation-Value units first
    ranked = sorted(items, key=lambda t: -t[0])
    # uniform: expose an arbitrary (id-sorted) slice; random: shuffle
    uniform = sorted(items, key=lambda t: t[2])
    rnd = list(items); random.Random(7).shuffle(rnd)
    def residual(order):
        exposed = order[:exposure_budget]
        seen = len(exposed)
        # debt = CSA miss cost of the UNEXPOSED units
        return sum(t[1] for t in order[exposure_budget:]) // 100
    return {"value_ranked": residual(ranked), "uniform": residual(uniform), "random": residual(rnd),
            "total_units": total_units}


def demo(seed=1):
    objs = _scene(seed=seed)
    print("Dependency Surface Area — fidelity is downstream of dependency visibility\n")
    print("  unprepared debt vs dependency access level (lower better):")
    for acc in (10, 40, 70, 100):
        print("    access %3d%% → debt %d" % (acc, access_debt(objs, acc)))
    units = dependency_surface_area  # noqa
    res = value_ranked_debt(objs, exposure_budget=60)
    print("\n  with a fixed exposure budget (cannot see everything), spend access by Preparation Value:")
    for pol in ("value_ranked", "uniform", "random"):
        print("    %-12s residual debt %d" % (pol, res[pol]))
    print("\n  Preparation Value = Causal Surface Area × Dependency Access.")
    print("  the limit is information topology, not GPU throughput. integrity ≠ truth.")
    return res


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("dependency_surface", OBSERVER, mutates_core=False,
                          note="Dependency Surface Area + Preparation Value = CSA × Dependency Access; the "
                               "hidden resource is dependency access (information topology), not sample budget")
    except LayerViolation:
        pass
