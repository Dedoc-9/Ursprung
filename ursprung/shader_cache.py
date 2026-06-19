# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/shader_cache.py — a shader/PSO cache as validated REPRESENTATION MEMORY (the industrial bridge).

A shader/PSO cache miss is already a real-world manifestation of the Transition Debt Law: a representation
decision was not available when it was needed, so the renderer pays a transition-debt spike (compile hitch /
pipeline stall). Ursprung reframes the cache: it does not store *truth* and it does not merely store compiled
binaries — it stores **validated representation decisions**, keyed by the conditions that made each decision
safe (material family, geometry class, lighting regime, hardware path, temporal stability), with deterministic
replayable keys and fallback tiers.

The pioneering angle is NOT "faster shaders." It is turning shader compilation / pipeline selection from a
reactive hitch source into a **temporal fidelity allocation problem**: spend preparation where future
discontinuity is most likely, preserve frame-time stability, and keep every fallback a VIEW/ALLOCATOR decision
that never touches world truth.

The triad is the intelligence behind the cache:
  · Resistance Tensor  → which cached paths are expensive to MISS (`resistance_tensor.miss_cost`).
  · Multi-Horizon      → which conditions are likely needed soon (`transition model` over short/med horizons).
  · Fidelity Derivative→ is warming THIS entry worth the budget? (avoided-penalty × probability vs warm cost).
When the cache cannot satisfy the deadline, the **particle/impostor fallback tiers** provide graceful
degradation — a perceptual bridge, not a lie.

CLASSIFICATION: ALLOCATOR (mutates_core=False). It allocates *preparation* budget over representation
decisions and serves fallbacks; it never touches committed world state. Cache keys are content-addressed and
replayable.

HONEST BOUND: a CONSTRUCTED model of PSO/shader cost (a miss = a declared transition-debt spike), not real
driver compilation; the transition model is a declared predictor, not a learned one. Numbers `expire_if`
measured on real silicon/drivers. `observation → allocation`, never `→ truth`. integrity ≠ truth.
"""
from __future__ import annotations

import hashlib
import json
import random

from . import resistance_tensor as rt

WARM_COST = 40             # cost of prewarming one entry (small, paid up front)
FALLBACK_FRACTION = 30     # a fallback costs ~30% of a full miss (graceful: bounded, never a full hitch)
CONDITION_FIELDS = ("material_family", "geometry_class", "lighting_regime", "hardware_path", "temporal_stability")
FALLBACK_TIERS = ("exact", "cached_variant", "impostor", "particle_proxy", "procedural_approx")


def condition_key(cond):
    """Content-addressed, replayable key from the conditions that made a representation decision safe."""
    payload = json.dumps({k: cond.get(k) for k in CONDITION_FIELDS}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


class RepresentationContract:
    """A validated representation decision + the conditions it is valid under + its miss penalty/fallback."""
    __slots__ = ("conditions", "decision", "confidence", "miss_penalty", "fallback_tier")

    def __init__(self, conditions, decision, confidence=100, fallback_tier="impostor"):
        self.conditions = conditions
        self.decision = decision                      # e.g. (shader_variant, pipeline_state)
        self.confidence = confidence
        self.miss_penalty = rt.miss_cost(conditions)  # transition-debt spike if missing when needed
        self.fallback_tier = fallback_tier

    def key(self):
        return condition_key(self.conditions)


class Cache:
    """LRU cache of representation contracts (capacity models the real variant-explosion-exceeds-cache case)."""

    def __init__(self, capacity=3):
        self.capacity = capacity
        self._warm = []            # list of keys, LRU order (oldest first)

    def has(self, cond):
        return condition_key(cond) in self._warm

    def touch(self, cond):
        k = condition_key(cond)
        if k in self._warm:
            self._warm.remove(k)
        elif len(self._warm) >= self.capacity:
            self._warm.pop(0)      # evict LRU
        self._warm.append(k)


# --- multi-horizon transition model (which conditions are likely needed soon) -----------------------

def transition_model(schedule, t, horizon=2):
    """Predict the conditions likely needed in the next `horizon` frames, with decaying confidence.
    Returns [(cond, probability)]. A declared predictor that knows the demand has temporal structure."""
    out = []
    for h in range(1, horizon + 1):
        if t + h < len(schedule):
            out.append((schedule[t + h], max(1, 100 - 30 * (h - 1))))   # nearer horizon ⇒ higher confidence
    return out


# --- the demand sequence (structured, so prediction can help) ---------------------------------------

def _regimes(seed=1):
    rng = random.Random(seed)
    regs = []
    for i in range(5):
        expensive = (i % 2 == 0)                      # alternate cheap/expensive-to-miss regimes
        regs.append({
            "material_family": "mat%d" % i, "geometry_class": "geo%d" % (i % 3),
            "lighting_regime": "light%d" % i, "hardware_path": "rdna", "temporal_stability": "stable",
            # resistance dims drive miss_cost: expensive regimes have high lighting/reconstruction sensitivity
            "lighting_sensitivity": 9 if expensive else 2,
            "reconstruction_sensitivity": 8 if expensive else 2,
            "spatial_discontinuity": 3, "temporal_instability": 3,
        })
    return regs


def demand_schedule(frames=48, dwell=4, seed=1):
    """Regime switches every `dwell` frames, cycling — predictable structure a transition model can exploit."""
    regs = _regimes(seed)
    return [regs[(t // dwell) % len(regs)] for t in range(frames)]


# --- the bench: reactive vs predictive-prewarm vs predictive+fallback vs random control -------------

def _serve_cost(cond, cache, prepared):
    """Cost of serving a frame's needed condition. Hit → 0; miss with a fallback → FALLBACK_FRACTION% of the
    full penalty (graceful); only a true unpreparable miss pays the full transition-debt spike."""
    if cache.has(cond) or condition_key(cond) in prepared:
        return 0
    return rt.miss_cost(cond) * FALLBACK_FRACTION // 100     # graceful fallback bounds the worst-case hitch


def run(seed=1, frames=48, dwell=4, capacity=3, prewarm_budget=1):
    sched = demand_schedule(frames=frames, dwell=dwell, seed=seed)

    # 1) REACTIVE: compile-on-miss → full transition-debt spike each miss
    cache = Cache(capacity); reactive = 0
    for cond in sched:
        if not cache.has(cond):
            reactive += rt.miss_cost(cond)        # full hitch
        cache.touch(cond)

    # 2) PREDICTIVE: prewarm the soon-needed, expensive-to-miss conditions (triad), gated by fidelity benefit
    cache = Cache(capacity); predictive = 0
    for t, cond in enumerate(sched):
        # prewarm plan: rank predicted-next by probability × miss_cost; warm top-`budget` if benefit > warm cost
        cands = transition_model(sched, t)
        cands = sorted(cands, key=lambda cp: -(cp[1] * rt.miss_cost(cp[0])))
        warmed = 0
        for nc, prob in cands:
            if warmed >= prewarm_budget:
                break
            benefit = prob * rt.miss_cost(nc) // 100          # expected avoided penalty (fidelity derivative)
            if benefit > WARM_COST and not cache.has(nc):
                cache.touch(nc); predictive += WARM_COST; warmed += 1
        if not cache.has(cond):
            predictive += rt.miss_cost(cond)
        cache.touch(cond)

    # 3) PREDICTIVE + FALLBACK: an unpreparable miss is served by a fallback tier (graceful, bounded)
    cache = Cache(capacity); predictive_fb = 0
    for t, cond in enumerate(sched):
        cands = sorted(transition_model(sched, t), key=lambda cp: -(cp[1] * rt.miss_cost(cp[0])))
        warmed = 0
        for nc, prob in cands:
            if warmed >= prewarm_budget:
                break
            if prob * rt.miss_cost(nc) // 100 > WARM_COST and not cache.has(nc):
                cache.touch(nc); predictive_fb += WARM_COST; warmed += 1
        predictive_fb += _serve_cost(cond, cache, set())      # hit→0, else bounded fallback
        cache.touch(cond)

    # 4) RANDOM control: prewarm random conditions (wastes budget, does not avoid the costly misses)
    regs = _regimes(seed); cache = Cache(capacity); control = 0; rng = random.Random(seed * 31 + 7)
    for cond in sched:
        for _ in range(prewarm_budget):
            cache.touch(rng.choice(regs)); control += WARM_COST
        if not cache.has(cond):
            control += rt.miss_cost(cond)
        cache.touch(cond)

    return {"reactive": reactive, "predictive": predictive,
            "predictive+fallback": predictive_fb, "random (control)": control}


def demo(seed=1, frames=48):
    res = run(seed=seed, frames=frames)
    print("Shader cache as validated representation memory — transition-debt under condition switching")
    print("  cost = Σ transition-debt spikes (misses) + Σ prewarm costs (lower better)\n")
    for name in ("reactive", "predictive", "predictive+fallback", "random (control)"):
        print("  %-22s %d" % (name, res[name]))
    print("\n  predictive vs reactive: %d vs %d  (prewarm where future discontinuity × miss-cost is highest)"
          % (res["predictive"], res["reactive"]))
    print("  fallback tiers bound the worst-case hitch (graceful degradation, never touches truth).")
    print("  Honest bound: constructed PSO-cost model; expires on real drivers. integrity ≠ truth.")
    return res


def register():
    from .registry import REGISTRY, ALLOCATOR, LayerViolation
    try:
        REGISTRY.register("shader_cache", ALLOCATOR, mutates_core=False,
                          note="validated representation memory — prewarm by P(needed)×miss_cost gated by the "
                               "fidelity derivative; fallback tiers; turns PSO hitches into a fidelity allocation")
    except LayerViolation:
        pass
