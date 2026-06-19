# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/allocation.py — the ranking/allocation split (the Milestone-3 result, made structural).

THE FINDING (from the failed Causal Continuity Hypothesis):

    Importance metrics and allocation functions cannot be conflated. Causal importance should RANK regions;
    resource distribution should be solved through a SEPARATE constrained optimization. The original
    hypothesis (allocate ∝ U·C·P) accidentally merged a ranking problem with an optimization problem; the
    rasterizer split them apart.

    PFAL ranks.  Water-filling allocates.  Reality Debt constrains.

Two distinct objects:

    Priority   = U × C × P × S × τ                 — WHERE budget should go     (a ranking problem)
    Allocation = WaterFill(Priority, ErrorStructure) — HOW MUCH to spend         (a constrained optimization)

For a convex residual `Σ priority · error(samples)` with `error ∝ resistance/samples`, the constrained
optimum is **water-filling**: `samples ∝ √(priority × resistance)` — NOT proportional to priority. That is
why proportional allocation over-concentrated and lost; the two-stage allocator below recovers the optimum.

CLASSIFICATION: ALLOCATOR (mutates_core=False). It ranks and distributes a budget; it never moves committed
state and decides no truth. Priority, resistance, and budget are inputs/observables.

HONEST BOUND: constructed-world demonstration on the declared aliasing model. It shows the two-stage
allocator beats both uniform and proportional allocation on the future-causal residual metric — a property
of this model, `expires_if` measured on real silicon. `observation → allocation`, never `→ truth`.
"""
from __future__ import annotations

import math
import random

from .raster import aliasing_error
from . import representation as rep


# --- stage 1: ranking (what matters) ----------------------------------------------------------------

def rank(regions, priority_fn):
    """Assign each region a priority (the 'what matters' ranking). priority_fn(region) -> int >= 0."""
    return {rid: max(0, int(priority_fn(r))) for rid, r in regions.items()}


# --- stage 2: allocation (how much to spend) --------------------------------------------------------

def _hamilton(weights, budget):
    keys = sorted(weights)
    tot = sum(max(0, weights[k]) for k in keys)
    if budget <= 0 or not keys:
        return {k: 0 for k in keys}
    if tot == 0:
        base, rem = divmod(budget, len(keys))
        return {k: base + (1 if i < rem else 0) for i, k in enumerate(keys)}
    raw = {k: max(0, weights[k]) * budget / tot for k in keys}
    floor = {k: int(raw[k]) for k in keys}
    for k in sorted(keys, key=lambda k: (-(raw[k] - floor[k]), k))[:budget - sum(floor.values())]:
        floor[k] += 1
    return floor


def waterfill(priority, resistance, budget):
    """Distribute `budget` by the convex-optimal rule: samples ∝ √(priority × resistance). `priority` and
    `resistance` are {id: int}. Integer, deterministic (Hamilton). This is the 'how much to spend' stage."""
    weights = {rid: max(1, int(math.isqrt(max(1, priority.get(rid, 0) * resistance.get(rid, 1)))) * 100)
               for rid in priority}
    return _hamilton(weights, budget)


def two_stage_allocate(regions, budget, priority_fn, resistance_fn=rep.representation_resistance):
    """The full re-specified allocator: rank by priority, then water-fill under representation resistance.
    `Determine what matters. Then determine how much to spend.`"""
    priority = rank(regions, priority_fn)
    resistance = {rid: resistance_fn(r) for rid, r in regions.items()}
    return waterfill(priority, resistance, budget)


# --- the re-specified bench (does separating ranking from allocation recover the win?) --------------

def _scene(n=50, seed=1):
    rng = random.Random(seed)
    out = {}
    for i in range(n):
        li = (i % 2 == 0)
        out["r%02d" % i] = {
            "uncertainty": rng.uniform(0.5, 4.0),
            "consequence": rng.randint(1, 3) if li else rng.randint(6, 10),
            "persistence": rng.randint(1, 5),
            "size": rng.randint(2, 12),
            "distance": rng.randint(1, 100),
            "visibility": rng.randint(1, 100),
        }
    return out


def _U(r): return max(1, int(round(r["uncertainty"] * 100)))
def _causal_priority(r): return _U(r) * r["consequence"] * r["persistence"]   # U×C×P (the ranking)


def _future_causal_residual(regions, alloc):
    """The objective: Σ (future-causal weight = U·C·P) · aliasing_error(size, samples). Lower is better —
    the expected future causal loss that remains after spending the budget."""
    total = 0
    for rid, r in regions.items():
        total += _causal_priority(r) * aliasing_error(r["size"], alloc.get(rid, 0) + 1)
    return total


def run(seed=1, budget=400):
    regions = _scene(seed=seed)
    pol = {
        "uniform": lambda: _hamilton({rid: 1 for rid in regions}, budget),
        "proportional_causal (∝U·C·P)": lambda: _hamilton(rank(regions, _causal_priority), budget),
        "distance": lambda: _hamilton({rid: 1_000_000 // (r["distance"] + 1) for rid, r in regions.items()}, budget),
        "visibility": lambda: _hamilton({rid: r["visibility"] for rid, r in regions.items()}, budget),
        "ranked_waterfill (√(prio·RR))": lambda: two_stage_allocate(regions, budget, _causal_priority),
        "drifted (control)": lambda: _hamilton(
            {rid: random.Random(seed * 17 + i).randint(1, 1000) for i, rid in enumerate(regions)}, budget),
    }
    return {name: _future_causal_residual(regions, fn()) for name, fn in pol.items()}


def demo(seed=1, budget=400):
    res = run(seed=seed, budget=budget)
    best = min(res, key=lambda k: res[k])
    print("Ranking/allocation split — re-specified causal bench (constructed, seed=%d, budget=%d)" % (seed, budget))
    print("  metric = future-causal residual Σ (U·C·P)·aliasing(size, samples)  (lower better)\n")
    for name in ("uniform", "distance", "visibility", "proportional_causal (∝U·C·P)",
                 "ranked_waterfill (√(prio·RR))", "drifted (control)"):
        tag = "  ← rank by U·C·P, allocate by water-filling under resistance" if name.startswith("ranked") else ""
        if name.startswith("proportional"):
            tag = "  ← conflates ranking & allocation (suboptimal)"
        print("  %-32s %d%s" % (name, res[name], tag))
    print("\n  best policy: %s" % best)
    print("  finding: PFAL ranks · water-filling allocates · Reality Debt constrains — they are different objects.")
    print("  Honest bound: constructed world + declared aliasing model; expires on real silicon. integrity ≠ truth.")
    return res, best


def register():
    from .registry import REGISTRY, ALLOCATOR, LayerViolation
    try:
        REGISTRY.register("allocation", ALLOCATOR, mutates_core=False,
                          note="ranking/allocation split — rank(priority) then waterfill(priority, resistance); "
                               "PFAL ranks, water-filling allocates, Reality Debt constrains")
    except LayerViolation:
        pass
