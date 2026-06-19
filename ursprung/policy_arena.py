# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/policy_arena.py — the dual-axis Policy Arena (causal residual × perceptual continuity).

The most dangerous missing benchmark: the system optimizes the **future-causal residual**, but humans
experience **perceived continuity**, and those are not guaranteed to align. The arena evaluates every
allocation policy on BOTH axes over a sequence of drifting frames, at equal budget, and reports the Pareto
front — so a policy that wins one axis while losing the other is exposed instead of hidden.

    x-axis: causal residual          Σ_t Σ_i (U·C·P) · aliasing_error(size, samples)     (lower better)
    y-axis: perceptual continuity    Σ_t Σ_i sensitivity · |alloc_t − alloc_{t-1}|       (lower better)

Expected mismatch (the hidden variable this is built to surface): a churny optimum (`ranked_waterfill`)
minimizes causal residual but reallocates every frame → high perceptual loss; `uniform` is perfectly steady
(zero perceptual loss) but high causal residual. Neither dominates. The HARDENING is `damped_waterfill`: it
water-fills a slowly-moving (EMA) weight, trading a little causal residual for much lower perceptual loss —
a Pareto improvement over the churny optimum.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures and ranks policies on two axes; it allocates
nothing into committed state and asserts no truth.

HONEST BOUND: constructed drifting world + declared aliasing & PCL proxies; the *shape* (a two-axis trade-off
with a Pareto front) is the result, not the exact numbers, which `expire_if` measured on real silicon with
real perceptual error. `integrity ≠ truth`.
"""
from __future__ import annotations

import random

from .raster import aliasing_error
from . import allocation as al
from . import perceptual as pc
from . import representation as rep


def evolving_frames(n=40, frames=24, seed=1):
    """A sequence of frames whose volatile attributes (uncertainty, consequence) drift each frame, while
    sensitivity and size are stable. Drift is what makes a greedy reallocator churn."""
    rng = random.Random(seed)
    base = []
    for i in range(n):
        base.append({"id": "r%02d" % i, "sensitivity": rng.randint(1, 10), "size": rng.randint(2, 12),
                     "persistence": rng.randint(1, 5)})
    seq = []
    for t in range(frames):
        frame = {}
        for b in base:
            r = random.Random(seed * 100003 + t * 1009 + int(b["id"][1:]))
            frame[b["id"]] = {"id": b["id"], "sensitivity": b["sensitivity"], "size": b["size"],
                              "persistence": b["persistence"],
                              "uncertainty": r.uniform(0.5, 4.0), "consequence": r.randint(1, 10)}
        seq.append(frame)
    return seq


def _causal_residual(regions, alloc):
    return sum(al._causal_priority(r) * aliasing_error(r["size"], alloc.get(rid, 0) + 1)
               for rid, r in regions.items())


# --- per-frame allocators -------------------------------------------------------------------------

def _uniform(regions, budget):       return al._hamilton({rid: 1 for rid in regions}, budget)
def _proportional(regions, budget):  return al._hamilton(al.rank(regions, al._causal_priority), budget)
def _distance(regions, budget):      return al._hamilton({rid: 1 for rid in regions}, budget)  # no distance here → flat
def _waterfill(regions, budget):     return al.two_stage_allocate(regions, budget, al._causal_priority)


def run(seed=1, budget=400, frames=24, ema_num=1, ema_den=4):
    seq = evolving_frames(frames=frames, seed=seed)
    sensitivity = {rid: r["sensitivity"] for rid, r in seq[0].items()}

    policies = {
        "uniform": _uniform,
        "proportional_causal": _proportional,
        "ranked_waterfill": _waterfill,
    }
    out = {}
    for name, fn in policies.items():
        causal = 0
        allocs = []
        for regions in seq:
            a = fn(regions, budget)
            causal += _causal_residual(regions, a)
            allocs.append(a)
        out[name] = (causal, pc.sequence_pcl(allocs, sensitivity))

    # hardened: damped_waterfill — water-fill a slowly-moving (EMA) weight to cut churn
    causal = 0
    allocs = []
    ema = None
    for regions in seq:
        target = {rid: max(1, al._causal_priority(r) * rep.representation_resistance(r)) for rid, r in regions.items()}
        if ema is None:
            ema = dict(target)
        else:
            ema = {rid: (ema.get(rid, 0) * (ema_den - ema_num) + target[rid] * ema_num) // ema_den
                   for rid in target}
        import math
        weights = {rid: max(1, int(math.isqrt(max(1, ema[rid]))) * 100) for rid in ema}
        a = al._hamilton(weights, budget)
        causal += _causal_residual(regions, a)
        allocs.append(a)
    out["damped_waterfill (hardened)"] = (causal, pc.sequence_pcl(allocs, sensitivity))
    return out


# --- Pareto analysis --------------------------------------------------------------------------------

def dominates(a, b):
    """a=(causal,pcl) Pareto-dominates b if a is <= on both axes and strictly < on at least one."""
    return a[0] <= b[0] and a[1] <= b[1] and (a[0] < b[0] or a[1] < b[1])


def pareto_front(points):
    """Names not dominated by any other point. points: {name: (causal, pcl)}."""
    return sorted(n for n in points if not any(dominates(points[m], points[n]) for m in points if m != n))


def demo(seed=1, budget=400, frames=24):
    res = run(seed=seed, budget=budget, frames=frames)
    print("Policy Arena — dual axis (causal residual × perceptual continuity loss), equal budget=%d, frames=%d"
          % (budget, frames))
    print("  both axes: lower is better\n")
    print("  %-30s %14s %16s" % ("policy", "causal_residual", "perceptual_loss"))
    for name in sorted(res, key=lambda k: res[k][0]):
        print("  %-30s %14d %16d" % (name, res[name][0], res[name][1]))
    front = pareto_front(res)
    best_causal = min(res, key=lambda k: res[k][0])
    best_pcl = min(res, key=lambda k: res[k][1])
    print("\n  Pareto front: %s" % ", ".join(front))
    print("  min causal: %s   |   min perceptual loss: %s" % (best_causal, best_pcl))
    print("  MISMATCH: %s — minimizing causal residual is NOT the same as maximizing perceptual continuity."
          % ("CONFIRMED" if best_causal != best_pcl else "not seen at this seed"))
    print("  Honest bound: constructed drifting world + declared proxies; shape is the result, not the numbers.")
    return res


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("policy_arena", OBSERVER, mutates_core=False,
                          note="dual-axis (causal residual × perceptual continuity loss) policy comparison; "
                               "exposes the mismatch; Pareto front; hardened damped_waterfill")
    except LayerViolation:
        pass
