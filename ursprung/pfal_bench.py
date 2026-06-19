# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/pfal_bench.py — Predictive Fidelity Allocation Field, and its falsification bench.

PFAL is a **closed-loop perceptual error budget.** The renderer does not ask "where are the most polygons?"
It asks: *"where is my current approximation most likely to fail within the next few frames, and how
expensive is that failure?"* — then converts that into GPU work. The per-region score:

    R = U × C × P × S

    U = uncertainty   — how wrong is our prediction likely to be?      (from prediction.py / the ghost)
    C = consequence   — if wrong, how noticeable / gameplay-relevant?  (INPUT, from causal_runtime)
    P = persistence   — will this error last across frames?
    S = sensitivity   — human/perceptual sensitivity to that artifact

R does NOT say "important object." It says "this approximation deserves more observation." The big claim,
carefully worded: **the renderer spends computation where its current approximation has the highest expected
failure cost** — not "the renderer knows what matters." That is a *measurable hypothesis*, which is why this
file is a bench, not a claim.

THE BENCH (the first place the philosophy could become a real engine advantage). Three allocators split the
SAME fixed budget over a constructed scene:

    1. uniform              — equal quality everywhere (the safe floor / negative-control reference)
    2. distance_visibility  — what engines do today (budget follows pixels: near + on-screen)
    3. pfal                 — budget follows U × C × P × S

Metric: **failure-cost covered** — the fraction of true expected failure cost (M = U·C·P·S·needed) that the
allocation actually funds, at equal budget (higher is better); and residual perceptual error (lower better).
A **negative control** (`drifted_pfal`, a scrambled estimate) MUST lose to the uniform floor — if it does
not, the bench cannot falsify a bad policy and is decoration (the Goodhart guard).

CLASSIFICATION: OBSERVER (mutates_core=False). It measures and ranks allocation policies; it changes nothing
and decides no truth.

HONEST BOUND (read before quoting any number): this is a CONSTRUCTED workload model, not silicon. Results are
conditional on the world generator and **expire if measured on real GPU hardware** (perceptual quality,
input-to-photon latency, reconstruction error, motion stability are the real metrics; this models their
proxy). A benchmark measures the benchmark's world; it does not prove universal superiority.
`observation → allocation`, never `observation → truth`. integrity ≠ truth.
"""
from __future__ import annotations

import random

from .temporal_membrane import _hamilton


def pfal_score(region, scale=100):
    """R = U × C × P × S as an integer weight (U quantized by `scale`). Higher ⇒ more observation budget."""
    u = int(round(region.get("uncertainty", 0.0) * scale))
    c = int(region.get("consequence", 1))
    p = int(region.get("persistence", 1))
    s = int(region.get("sensitivity", 1))
    return max(0, u) * max(1, c) * max(1, p) * max(1, s)


# --- constructed scene ------------------------------------------------------------------------------

def make_scene(n=60, seed=1):
    """Regions with both the OBSERVABLE signals an engine sees (distance, visibility) and the latent factors
    that drive true failure cost (U, C, P, S). The FPS-killer case is built in: some high-failure-cost
    regions are small/far/low-visibility, so a distance/visibility budget is blind to them — exactly the
    'tiny moving object behind foliage' the user described."""
    rng = random.Random(seed)
    scene = []
    for i in range(n):
        far = rng.random() < 0.5
        distance = rng.randint(60, 100) if far else rng.randint(1, 40)
        visibility = rng.randint(1, 30) if far else rng.randint(40, 100)  # far ⇒ small on screen
        # latent failure factors: deliberately make some FAR/low-vis regions high-U,high-C (the killers)
        killer = far and (i % 3 == 0)
        uncertainty = (rng.uniform(2.0, 5.0) if killer else rng.uniform(0.0, 1.0))   # prediction unstable
        consequence = (rng.randint(6, 10) if killer else rng.randint(1, 4))           # gameplay-relevant
        persistence = (rng.randint(3, 5) if killer else rng.randint(1, 3))
        sensitivity = rng.randint(2, 6)
        needed = 10 + (rng.randint(0, 20))
        scene.append({
            "id": "r%02d" % i, "distance": distance, "visibility": visibility,
            "uncertainty": uncertainty, "consequence": consequence,
            "persistence": persistence, "sensitivity": sensitivity, "needed": needed,
        })
    return scene


# --- allocation policies (each → integer weight per region) -----------------------------------------

def w_uniform(r):
    return 1


def w_distance_visibility(r):
    # what engines do: budget follows pixels (near + large on screen)
    return max(1, r["visibility"] * 1000 // (r["distance"] + 1))


def w_pfal(r):
    return pfal_score(r)


def _drifted(seed):
    rng = random.Random(seed * 7 + 1)
    def w(r):
        return rng.randint(1, 1000)   # negative control: a scrambled / stale PFAL estimate
    return w


# --- measurement ------------------------------------------------------------------------------------

def _true_failure_cost(r):
    """M — the true expected failure cost if this region is under-funded: U·C·P·S·needed (the thing a good
    allocator should cover). This is the bench's hidden objective; it is an INPUT to the bench, never a
    truth the renderer asserts."""
    return r["uncertainty"] * r["consequence"] * r["persistence"] * r["sensitivity"] * r["needed"]


def failure_cost_covered(scene, alloc):
    """Fraction of total true failure cost that the allocation actually funds (higher = better)."""
    tot = sum(_true_failure_cost(r) for r in scene) or 1.0
    covered = 0.0
    for r in scene:
        got = alloc.get(r["id"], 0)
        frac = min(1.0, got / r["needed"]) if r["needed"] else 1.0
        covered += _true_failure_cost(r) * frac
    return covered / tot


def run(seed=1, budget=600):
    scene = make_scene(seed=seed)
    policies = {
        "uniform": w_uniform,
        "distance_visibility": w_distance_visibility,
        "pfal (U×C×P×S)": w_pfal,
        "drifted_pfal (control)": _drifted(seed),
    }
    out = {}
    for name, wf in policies.items():
        weights = {r["id"]: wf(r) for r in scene}
        alloc = _hamilton(weights, budget)
        out[name] = failure_cost_covered(scene, alloc)
    return out


def demo(seed=1, budget=600):
    res = run(seed=seed, budget=budget)
    floor = res["uniform"]
    print("PFAL falsification bench (constructed world, seed=%d, equal budget=%d)" % (seed, budget))
    print("  metric = fraction of true failure-cost covered (higher better)\n")
    for name in ("uniform", "distance_visibility", "pfal (U×C×P×S)", "drifted_pfal (control)"):
        v = res[name]
        tag = ""
        if name.startswith("pfal"):
            tag = "  ← spends where approximation fails under consequence"
        if name.startswith("drifted"):
            tag = "  ← negative control: MUST lose to uniform floor" + (" (PASS)" if v < floor else " (FAIL)")
        print("  %-26s %.3f%s" % (name, v, tag))
    pfal = res["pfal (U×C×P×S)"]
    dv = res["distance_visibility"]
    print("\n  PFAL vs distance/visibility: %.3f vs %.3f  (%.2fx)" % (pfal, dv, (pfal / dv) if dv else float("inf")))
    print("  Honest bound: constructed world; a hypothesis; expires_if measured on real GPU silicon.")
    print("  observation → allocation, never observation → truth.")
    return res
