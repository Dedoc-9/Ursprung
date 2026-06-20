# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/representation_compiler.py — compose providers into the cheapest continuity-preserving chain.

Provider contracts (M9) become **compositional**. Instead of one monolithic `RayTracingProvider`, a frame is
a *representation pipeline* of stages — geometry + lighting + motion + continuity — each declaring the
dependencies it consumes, the guarantee it provides, and how it degrades when starved. The system then
answers a compiler-shaped question:

    Given this future possibility and these available dependencies, what is the CHEAPEST representation chain
    that PRESERVES CONTINUITY under the latency budget?

That is closer to a compiler than a renderer: it lowers a desired representation onto whatever providers can
meet the deadline, degrading gracefully (high-quality stage → cheaper stage → fallback) rather than hitching.
Continuity is the one guarantee that must never be dropped — only downgraded — which is why the particle/
impostor tiers exist.

CLASSIFICATION: ALLOCATOR (mutates_core=False). It selects a provider chain under a budget; it renders
nothing here, commits no state, and asserts no truth. integrity ≠ truth — a compiled chain is a *plan* that
meets the deadline, not a claim the image is correct.

HONEST BOUND: declared per-stage latency/quality, not measured driver costs; the result is the *composition*
(cheapest chain that keeps continuity), not the constants.
"""
from __future__ import annotations

STAGES = ("geometry", "lighting", "motion", "continuity")


def stage_providers():
    """Per-stage candidate providers: {name, inputs, latency, quality, fallback}. The continuity stage always
    has a near-free fallback so continuity can be DOWNGRADED but never DROPPED."""
    return {
        "geometry": [
            {"name": "meshlet", "inputs": {"geometry"}, "latency": 5, "quality": 80, "fallback": "impostor"},
            {"name": "impostor", "inputs": set(), "latency": 1, "quality": 35, "fallback": None},
        ],
        "lighting": [
            {"name": "ray_traced", "inputs": {"lighting", "geometry"}, "latency": 30, "quality": 95, "fallback": "baked"},
            {"name": "baked", "inputs": {"lighting"}, "latency": 3, "quality": 60, "fallback": "flat"},
            {"name": "flat", "inputs": set(), "latency": 1, "quality": 25, "fallback": None},
        ],
        "motion": [
            {"name": "neural_interp", "inputs": {"history", "motion"}, "latency": 8, "quality": 85, "fallback": "reproject"},
            {"name": "reproject", "inputs": {"motion"}, "latency": 2, "quality": 55, "fallback": "hold"},
            {"name": "hold", "inputs": set(), "latency": 0, "quality": 20, "fallback": None},
        ],
        "continuity": [
            {"name": "temporal_history", "inputs": {"history"}, "latency": 4, "quality": 80, "fallback": "particle_bridge"},
            {"name": "particle_bridge", "inputs": set(), "latency": 1, "quality": 40, "fallback": None},
        ],
    }


def _pick(stage_list, conditions, latency_left):
    """Highest-quality provider whose inputs are satisfied AND fits the remaining latency; else degrade along
    the fallback chain to the first admissible+fitting (continuity always bottoms out at a near-free tier)."""
    by_name = {p["name"]: p for p in stage_list}
    admissible = [p for p in stage_list if p["inputs"] <= set(conditions)]
    fitting = [p for p in admissible if p["latency"] <= latency_left]
    if fitting:
        return max(fitting, key=lambda p: p["quality"]), False
    # walk fallbacks from the best admissible down to something that fits
    start = max(admissible, key=lambda p: p["quality"]) if admissible else stage_list[-1]
    cur, seen = start, set()
    while cur is not None and cur["name"] not in seen:
        seen.add(cur["name"])
        if cur["latency"] <= latency_left and cur["inputs"] <= set(conditions):
            return cur, (cur is not start)
        cur = by_name.get(cur["fallback"])
    return stage_list[-1], True          # last resort: the cheapest tier (continuity never dropped)


def compile_pipeline(conditions, latency_budget, required=STAGES):
    """Lower a desired representation onto the cheapest provider chain that preserves continuity under the
    budget. RESERVES each later stage's cheapest tier so the whole chain fits the deadline and continuity is
    never starved by a greedy earlier stage. Returns {chain, total_latency, total_quality, degraded,
    continuity_preserved}."""
    sp = stage_providers()
    cheapest = {s: min(p["latency"] for p in sp[s]) for s in required}     # the floor each stage can hit
    chain, total_latency, total_quality, degraded = {}, 0, 0, False
    for idx, stage in enumerate(required):
        reserve = sum(cheapest[s] for s in required[idx + 1:])             # keep enough for the remaining stages
        available = latency_budget - total_latency - reserve
        prov, _deg = _pick(sp[stage], conditions, available)
        best_q = max((p["quality"] for p in sp[stage] if p["inputs"] <= set(conditions)), default=0)
        chain[stage] = prov["name"]; total_latency += prov["latency"]; total_quality += prov["quality"]
        degraded = degraded or prov["quality"] < best_q   # a stage got less than its best admissible provider
    continuity_preserved = "continuity" in chain          # continuity is always assigned (never dropped)
    return {"chain": chain, "total_latency": total_latency, "total_quality": total_quality,
            "degraded": degraded, "continuity_preserved": continuity_preserved}


def demo():
    print("Representation Compiler — cheapest provider chain that preserves continuity\n")
    scenarios = [
        ("ample budget, full deps", {"geometry", "lighting", "motion", "history"}, 60),
        ("tight latency (8ms)", {"geometry", "lighting", "motion", "history"}, 8),
        ("missing deps (geometry only)", {"geometry"}, 30),
    ]
    for label, cond, budget in scenarios:
        r = compile_pipeline(cond, budget)
        print("  %-30s lat=%2d q=%3d cont=%s%s" % (label, r["total_latency"], r["total_quality"],
              r["continuity_preserved"], "  (degraded)" if r["degraded"] else ""))
        print("      chain: %s" % r["chain"])
    print("\n  continuity is downgraded, never dropped. integrity ≠ truth — a chain meets the deadline, not 'correct'.")
    return compile_pipeline({"geometry", "lighting", "motion", "history"}, 8)


def register():
    from .registry import REGISTRY, ALLOCATOR, LayerViolation
    try:
        REGISTRY.register("representation_compiler", ALLOCATOR, mutates_core=False,
                          note="compose provider contracts into the cheapest representation chain that "
                               "preserves continuity under a latency budget; continuity downgrades, never drops")
    except LayerViolation:
        pass
