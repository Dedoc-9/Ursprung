# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/readiness.py — the Representation Readiness Layer (the abstraction the shader cache was hiding).

The shader cache was the first physical manifestation of a deeper idea: a PSO miss is a representation that
was available *in theory* but not *prepared* when the world demanded it. Generalized, the allocator stops
asking "what should I render?" and asks **"what representations must already exist before the future
arrives?"** That single question covers shader variants, geometry streaming, texture residency, neural
reconstruction, particle fallback, animation decompression, and ray-tracing acceleration structures — all the
same class of problem.

    readiness_score(resource) = P(needed soon)  ×  Causal Surface Area  ×  (miss cost is inside CSA)

Prepare the high-readiness resources under a budget; gate each by the fidelity derivative (is warming worth
it?). Every preparation is routed through the prepare-≠-decide guard: readiness PREPARES possible future
representations; it NEVER commits world state or asserts an outcome. The renderer becomes better prepared,
never prophetic.

CLASSIFICATION: ALLOCATOR (mutates_core=False). It allocates preparation budget over representation
resources; it touches no committed state. `observation → allocation`, never `→ truth`. integrity ≠ truth.

HONEST BOUND: a framework + a greedy planner over declared probabilities and CSA; not a measured residency/
streaming model. Numbers `expire_if` measured on real hardware. The value is the *single abstraction*, not
the constants.
"""
from __future__ import annotations

from . import causal_surface as cs

# the resource kinds the readiness layer unifies (the shader cache is just one)
RESOURCE_KINDS = ("shader_pso", "geometry_stream", "texture_residency", "neural_recon",
                  "particle_fallback", "anim_decompress", "rt_accel")

WARM_COST = 40


def readiness_score(resource, prob_needed):
    """P(needed soon) × Causal Surface Area. CSA already folds in miss cost (resistance tensor), so a
    resource is 'ready-worthy' when it is likely soon AND many futures depend on it AND it is costly to miss."""
    return max(0, int(prob_needed)) * cs.causal_surface_area(resource)


def plan(resources, prob_by_id, budget, warm_cost=WARM_COST):
    """Greedily prepare the highest-readiness resources under `budget` units, gating each by the fidelity
    derivative (expected avoided cost must exceed the warm cost). Every preparation is asserted to be a
    representation forecast (prepare ≠ decide) — a reality forecast would raise ProphecyViolation. Returns the
    set of prepared resource ids."""
    scored = sorted(resources, key=lambda r: -readiness_score(r, prob_by_id.get(r["id"], 0)))
    prepared, spent = set(), 0
    for r in scored:
        if spent + warm_cost > budget:
            break
        benefit = readiness_score(r, prob_by_id.get(r["id"], 0)) // 100   # expected avoided cost (fidelity deriv.)
        if benefit <= warm_cost:
            continue
        # the moat: preparing a representation is allowed; this is NOT an assertion about the future.
        cs.assert_prepared(cs.representation_forecast(r["id"], r.get("kind", "representation")))
        prepared.add(r["id"]); spent += warm_cost
    return prepared


def demo(seed=1, budget=400):
    import random
    rng = random.Random(seed)
    resources, prob = [], {}
    for i in range(30):
        rid = "res%02d" % i
        shared = (i % 5 == 0)
        resources.append({"id": rid, "kind": RESOURCE_KINDS[i % len(RESOURCE_KINDS)],
                          "agents_can_affect": rng.randint(2, 5) if shared else 1,
                          "expected_divergence": rng.randint(4, 9) if shared else 1,
                          "lighting_sensitivity": rng.randint(5, 9) if shared else 2,
                          "reconstruction_sensitivity": rng.randint(5, 9) if shared else 2})
        prob[rid] = rng.randint(60, 100) if shared else rng.randint(1, 30)
    prepared = plan(resources, prob, budget)
    shared_ids = {r["id"] for r in resources if r["agents_can_affect"] > 1}
    hit = len(prepared & shared_ids)
    print("Representation Readiness Layer — one abstraction over shader/stream/residency/neural/particles")
    print("  prepared %d resources under budget=%d; of the %d shared high-CSA resources, %d were prepared."
          % (len(prepared), budget, len(shared_ids), hit))
    print("  readiness = P(needed) × Causal Surface Area, gated by the fidelity derivative.")
    print("  every preparation is a representation forecast (prepare ≠ decide). integrity ≠ truth.")
    return prepared, shared_ids


def register():
    from .registry import REGISTRY, ALLOCATOR, LayerViolation
    try:
        REGISTRY.register("readiness", ALLOCATOR, mutates_core=False,
                          note="Representation Readiness Layer — prepare representations by P(needed)×CSA gated "
                               "by the fidelity derivative; shader cache/streaming/residency are instances; prepare ≠ decide")
    except LayerViolation:
        pass
