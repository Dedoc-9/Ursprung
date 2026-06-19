# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/raster_bench.py — the equal-budget pressure test for the Causal Continuity Hypothesis.

The VIEW slice instruments uncertainty (U), consequence (C), persistence (P), sensitivity (S) and a fixed
SAMPLE budget (the 4.13 ms proxy). Allocators split the SAME budget across regions; we measure
**consequential edge error** — Σ consequence · aliasing_error(size, samples_allocated) — where aliasing falls
as samples rise (`raster.aliasing_error`). Lower is better.

    uniform               equal samples everywhere (safe floor)
    distance              budget follows nearness        (an engine baseline)
    visibility            budget follows on-screen size  (an engine baseline)
    pfal (U×C×P×S)        predictive fidelity, includes present-perception S    (proportional)
    causal (U×C×P)        expected future causal loss, NO present-perception S  (proportional) ← the hypothesis
    drifted (control)     a scrambled causal estimate    (negative control — must lose)

Promotion rule (`causal_continuity.earns_promotion`): the hypothesis is promoted ONLY if proportional causal
strictly beats EVERY control at equal budget AND the drifted control loses. Otherwise it stays a hypothesis
and the result is recorded as architectural information.

RESULT (seed=1, budget=400 — recorded, not rigged): the hypothesis **does NOT earn promotion** — proportional
causal (≈2.15e6) loses even to uniform (≈1.68e6). The failure is informative, and the diagnosis is itself a
falsifiable claim (FINDINGS below), so two diagnostic allocators are included to test it:

    causal_waterfill   (√(U×C×P))        water-filling FORM of the causal weight
    optimal_waterfill  (√(C×perimeter))  the analytic optimum for this convex metric

FINDINGS (measured):
  1. The metric Σ C·perimeter/samples is CONVEX in samples, so PROPORTIONAL allocation (∝ weight)
     over-concentrates and loses to uniform. The correct form is WATER-FILLING (∝ √weight).
  2. The optimal weight must include the error's own structural term (here perimeter/size), which both PFAL
     and causal OMIT — so even causal_waterfill (≈1.64e6) only marginally beats uniform, while the size-aware
     optimum (≈1.43e6) wins. Allocation weight must match the error model's structure.

HONEST BOUND: a CONSTRUCTED-world result on a declared aliasing-error model and a consequence-weighted metric.
It tests the hypothesis on THIS objective; on a present-perceptual (S-weighted) metric PFAL would be favored.
Numbers `expire_if` measured on real silicon. `observation → allocation`, never `→ truth`. integrity ≠ truth.
"""
from __future__ import annotations

import math
import random

from .raster import aliasing_error
from . import causal_continuity as cc

FINDINGS = (
    "1) convex error ⇒ proportional allocation over-concentrates and loses to uniform; use water-filling "
    "(∝ √weight). 2) the optimal weight must include the error's structural term (size/perimeter), which "
    "PFAL and causal omit — so causal must be re-specified before it can be promoted."
)


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


def make_scene(n=50, seed=1):
    """Regions with the latent factors AND a built-in tension between present perception (S) and future
    causal weight (C): some loud-but-inert (high S, low C), others quiet-but-pivotal (low S, high C)."""
    rng = random.Random(seed)
    scene = []
    for i in range(n):
        loud_inert = (i % 2 == 0)
        scene.append({
            "id": "r%02d" % i,
            "uncertainty": rng.uniform(0.5, 4.0),
            "consequence": rng.randint(1, 3) if loud_inert else rng.randint(6, 10),
            "persistence": rng.randint(1, 5),
            "sensitivity": rng.randint(6, 10) if loud_inert else rng.randint(1, 3),
            "size": rng.randint(2, 12),
            "distance": rng.randint(1, 100),
            "visibility": rng.randint(1, 100),
        })
    return scene


def _u(r):  return int(round(r["uncertainty"] * 100))

def w_uniform(r):    return 1
def w_distance(r):   return max(1, 1_000_000 // (r["distance"] + 1))
def w_visibility(r): return r["visibility"]
def w_pfal(r):       return _u(r) * r["consequence"] * r["persistence"] * r["sensitivity"]
def w_causal(r):     return cc.expected_future_causal_loss(r)                       # U×C×P (proportional)
def w_causal_wf(r):  return max(1, int(math.isqrt(max(1, cc.expected_future_causal_loss(r))) * 100))
def w_optimal_wf(r): return max(1, int(math.isqrt(max(1, r["consequence"] * 8 * r["size"])) * 100))

def _drifted(seed):
    rng = random.Random(seed * 17 + 3)
    return lambda r: rng.randint(1, 1000)


def consequential_error(scene, alloc):
    """Σ consequence · aliasing_error(size, samples). samples = allocated + 1 (a one-sample floor)."""
    return sum(r["consequence"] * aliasing_error(r["size"], alloc.get(r["id"], 0) + 1) for r in scene)


def run(seed=1, budget=400):
    scene = make_scene(seed=seed)
    policies = {
        "uniform": w_uniform, "distance": w_distance, "visibility": w_visibility,
        "pfal (U×C×P×S)": w_pfal, "causal (U×C×P)": w_causal, "drifted (control)": _drifted(seed),
        "causal_waterfill (√U×C×P)": w_causal_wf, "optimal_waterfill (√C×perim)": w_optimal_wf,
    }
    return {name: consequential_error(scene, _hamilton({r["id"]: wf(r) for r in scene}, budget))
            for name, wf in policies.items()}


def evaluate(seed=1, budget=400):
    res = run(seed=seed, budget=budget)
    promote, reason = cc.earns_promotion(res)   # judges the STATED hypothesis: proportional "causal (U×C×P)"
    return res, promote, reason


def demo(seed=1, budget=400):
    res, promote, reason = evaluate(seed=seed, budget=budget)
    print("VIEW slice — equal-budget allocation bench (constructed world, seed=%d, budget=%d samples)" % (seed, budget))
    print("  metric = consequential edge error (lower better)\n")
    order = ["uniform", "distance", "visibility", "pfal (U×C×P×S)", "causal (U×C×P)", "drifted (control)",
             "causal_waterfill (√U×C×P)", "optimal_waterfill (√C×perim)"]
    for name in order:
        tag = ""
        if name == "causal (U×C×P)":
            tag = "  ← the STATED hypothesis (proportional)"
        if name.startswith("causal_waterfill"):
            tag = "  ← diagnostic: water-filling form"
        if name.startswith("optimal_waterfill"):
            tag = "  ← diagnostic: analytic optimum (size-aware)"
        print("  %-30s %d%s" % (name, res[name], tag))
    print("\n  Causal Continuity Hypothesis: %s" % ("PROMOTED" if promote else "REMAINS A HYPOTHESIS"))
    print("  reason: %s" % reason)
    print("  FINDINGS: %s" % FINDINGS)
    print("  Honest bound: constructed world + declared aliasing model + consequence-weighted metric.")
    return res, promote
