# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/provider_contract.py — representation providers that declare contracts (plugability without coupling).

A renderer should not hard-code `plugin.render(object)`. A representation provider should instead declare its
**capabilities**, and the readiness layer reasons over the contract without knowing the concrete plugin:

    capabilities() = {
        inputs:        which world conditions it can consume (material/lighting/motion/...),
        cost:          {compile_time, memory, latency},
        failure_mode:  the fallback to use when it cannot meet the deadline
    }

Particles, shaders, neural upscalers, ray tracers, impostors, meshlets, animation compression all become the
same category — *representation providers* — and the readiness/allocation layers select among them by contract
under a budget. This is the plugability frontier: future rendering technologies slot in behind the same
interface without changing the allocator.

CLASSIFICATION: OBSERVER / reference (mutates_core=False). It describes providers and selects one under a
budget; it renders nothing here, commits no state, and asserts no truth. integrity ≠ truth.

HONEST BOUND: declared cost/latency numbers, not measured driver/hardware costs — the value is the
contract-based selection, not the constants.
"""
from __future__ import annotations


class ProviderContract:
    """A representation provider's declared capabilities. The allocator reasons over THIS, not the plugin."""
    __slots__ = ("name", "inputs", "cost", "failure_mode", "quality")

    def __init__(self, name, inputs, cost, failure_mode, quality=50):
        self.name = name
        self.inputs = set(inputs)                 # condition kinds it can consume
        self.cost = dict(cost)                    # {compile_time, memory, latency}
        self.failure_mode = failure_mode          # provider name to fall back to (or "drop")
        self.quality = quality                    # declared representational quality (higher better)

    def admissible(self, conditions):
        """A provider is usable iff every input it needs is present in the current conditions."""
        return self.inputs <= set(conditions)

    def fits(self, latency_budget):
        return self.cost.get("latency", 0) <= latency_budget


def default_providers():
    """A registry of representation providers as contracts (not implementations)."""
    return {
        "raster_shader":   ProviderContract("raster_shader", {"material", "lighting"},
                                            {"compile_time": 20, "memory": 10, "latency": 4}, "impostor", quality=70),
        "ray_tracer":      ProviderContract("ray_tracer", {"material", "lighting", "geometry"},
                                            {"compile_time": 40, "memory": 30, "latency": 30}, "raster_shader", quality=95),
        "neural_upscaler": ProviderContract("neural_upscaler", {"history", "motion"},
                                            {"compile_time": 60, "memory": 40, "latency": 8}, "raster_shader", quality=85),
        "impostor":        ProviderContract("impostor", {"material"},
                                            {"compile_time": 2, "memory": 2, "latency": 1}, "particle_fallback", quality=35),
        "particle_fallback": ProviderContract("particle_fallback", set(),
                                            {"compile_time": 1, "memory": 1, "latency": 1}, "drop", quality=15),
        "meshlet":         ProviderContract("meshlet", {"geometry"},
                                            {"compile_time": 15, "memory": 20, "latency": 5}, "impostor", quality=60),
    }


def select_provider(providers, conditions, latency_budget):
    """Pick the highest-quality provider that is admissible (inputs satisfied) AND fits the latency budget. If
    none fits, follow failure_mode chains to a provider that does (graceful degradation). Returns
    (provider_name, used_fallback). The allocator never needs to know what any provider actually does."""
    admissible = [p for p in providers.values() if p.admissible(conditions)]
    fitting = [p for p in admissible if p.fits(latency_budget)]
    if fitting:
        best = max(fitting, key=lambda p: p.quality)
        return best.name, False
    # nothing admissible fits the deadline → walk the failure_mode chain to something that does
    start = max(admissible, key=lambda p: p.quality) if admissible else providers.get("particle_fallback")
    seen, cur = set(), start
    while cur is not None and cur.name not in seen:
        seen.add(cur.name)
        if cur.fits(latency_budget):
            return cur.name, (cur is not start)
        cur = providers.get(cur.failure_mode)
    return "drop", True


def demo():
    P = default_providers()
    print("Representation provider contracts — readiness selects by capability, not by plugin identity\n")
    scenarios = [
        ("ample budget, full conditions", {"material", "lighting", "geometry", "history", "motion"}, 40),
        ("tight latency (4ms), full conditions", {"material", "lighting", "geometry", "history", "motion"}, 4),
        ("very tight (1ms)", {"material", "lighting"}, 1),
        ("missing inputs (geometry only)", {"geometry"}, 6),
    ]
    for label, cond, budget in scenarios:
        name, fb = select_provider(P, cond, budget)
        print("  %-38s → %-18s %s" % (label, name, "(fallback)" if fb else ""))
    print("\n  particles/shaders/neural/RT/impostor/meshlet are one category: representation providers.")
    print("  integrity ≠ truth — a contract declares capability, never that the output is correct.")
    return P


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("provider_contract", OBSERVER, mutates_core=False,
                          note="representation providers declare capabilities {inputs, cost, failure_mode}; "
                               "readiness selects by contract without knowing the concrete plugin")
    except LayerViolation:
        pass
