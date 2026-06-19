# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/temporal_membrane.py — the Temporal Prediction Membrane (the chef's kiss).

A frame is not just an image. It is a **prediction about how the world should continue to appear.** Modern
raster pipelines already do this implicitly — TAA predicts history, motion vectors predict correspondence,
temporal upscalers predict missing detail, reprojection predicts where samples belong. The missing piece is
making those predictions **observable, deterministic, and self-auditing**:

    authoritative snapshot(t) → render prediction → predicted frame(t+1)
                                                          │
                              observed frame(t+1) ────────┤
                                                          ▼
                                                  divergence field
                                          ghost = observed − predicted

The crucial reframing: **ghost ≠ error.** A ghost means "the current representation failed to predict this
region." The cause is then *classified*, and each class maps to an ALLOCATION response — never a change to
the world:

    1. TEMPORAL  ghost  prediction failed over time (TAA trails, disocclusion, fast camera).
                        → raise temporal samples / reweight history.        NOT: change world state.
    2. SPATIAL   ghost  the representation lost geometry (LOD pop, occlusion miss, missing detail).
                        → allocate geometry budget.                          NOT: "this object is less real."
    3. NUMERICAL ghost  the representation boundary is showing (z-buffer precision, fp drift, interp diff).
                        → change representation / precision strategy.        NOT: ascribe semantic meaning.
    4. CAUSAL    ghost  small, barely-visible, off-center — but affects gameplay/AI/future (the FPS killer).
                        → raise observation budget (prediction confidence is LOW here).
                        NOT: "this object is important" (that is the ALLOCATOR's call, on consequence input).

The pioneering part is the **Temporal Reality Budget**: every frame has a fixed compute budget, and instead
of `more pixels = more quality`, you get `more uncertainty × consequence = more observation budget`. A huge,
visible, predictable wall gets a LOW budget; a tiny, uncertain, future-affecting object behind foliage gets
a HIGH budget. This connects the prediction observer (uncertainty) + a consequence field (input, from
`causal_runtime`) + `lockstep` (temporal cadence) + rasterization (the consumer).

THE FINAL LAW:
    A renderer should not spend computation on what LOOKS important. It should spend computation where its
    PREDICTIONS are WEAKEST under the CONSEQUENCES of being wrong.

Always obeying:  observation → allocation   (ALLOWED)
                 observation → truth         (FORBIDDEN)

CLASSIFICATION: ALLOCATOR (mutates_core=False). It chooses WHERE effort goes; it never moves committed state
and never decides what is true. Consequence is an INPUT, never a result computed here.

HONEST BOUND: the budget follows measured surprise × declared consequence — not importance and not truth. A
region can be wrongly modeled and still succeed by directing attention where the model is weakest. The
spatial/numerical ghost detectors are stubs until the raster slice supplies depth/geometry signals; today
the membrane produces temporal and causal ghosts from the available frame stream (integrity ≠ truth).
"""
from __future__ import annotations

from . import prediction as pred
from . import ghost_report as gr

# Ghost classes and their fixed response / forbidden interpretation.
TEMPORAL = "temporal"
SPATIAL = "spatial"
NUMERICAL = "numerical"
CAUSAL = "causal"

_RESPONSE = {
    TEMPORAL:  ("raise temporal samples / reweight history (TAA, motion vectors, reprojection)",
                "change world state"),
    SPATIAL:   ("allocate geometry / LOD budget",
                "treat the object as 'less real'"),
    NUMERICAL: ("change representation / precision strategy (z-buffer, fp, interpolation)",
                "ascribe semantic meaning to the artifact"),
    CAUSAL:    ("raise observation budget where prediction confidence is low AND consequence is high",
                "declare the object 'important'"),
}


def classify_render_ghost(kind):
    """Return the fixed {response, never} for a render-ghost class. The mapping is the discipline: every
    ghost has an allocation response and a forbidden truth/world interpretation."""
    resp, never = _RESPONSE[kind]
    return {"kind": kind, "response": resp, "never": never}


# --- integer apportionment (deterministic largest-remainder; same math as salience) -----------------

def _hamilton(weights, budget):
    """Apportion an integer budget across keys by integer weights. Exact (sums to budget), deterministic
    (ties broken by key). If all weights are zero, distribute as evenly as possible by key order."""
    keys = sorted(weights)
    total = sum(max(0, weights[k]) for k in keys)
    if budget <= 0 or not keys:
        return {k: 0 for k in keys}
    if total == 0:
        base, rem = divmod(budget, len(keys))
        return {k: base + (1 if i < rem else 0) for i, k in enumerate(keys)}
    raw = {k: (max(0, weights[k]) * budget) / total for k in keys}
    floor = {k: int(raw[k]) for k in keys}
    used = sum(floor.values())
    remainder = budget - used
    # hand out the remaining units to the largest fractional parts (ties → lower key first)
    order = sorted(keys, key=lambda k: (-(raw[k] - floor[k]), k))
    for k in order[:remainder]:
        floor[k] += 1
    return floor


class TemporalRealityBudget:
    """Allocates a fixed per-frame compute budget by uncertainty × consequence. Consequence is an INPUT
    (from a consequence field / causal_runtime), never computed here as truth."""

    def __init__(self, uncertainty_scale=100):
        self.uncertainty_scale = uncertainty_scale   # quantize float surprise to integer weight

    def weights(self, regions):
        """regions: {id: {"uncertainty": float>=0, "consequence": int>=0}} → integer weight per id."""
        return {rid: int(round(r.get("uncertainty", 0.0) * self.uncertainty_scale)) * int(r.get("consequence", 1))
                for rid, r in regions.items()}

    def allocate(self, regions, total_budget, floor=0):
        """Return {id: budget}. `floor` guarantees a minimum to every region first (hard-gated regions —
        e.g. anti-cheat occlusion — still get a baseline), then uncertainty×consequence splits the rest."""
        ids = sorted(regions)
        if not ids:
            return {}
        floor_total = floor * len(ids)
        rest = max(0, total_budget - floor_total)
        split = _hamilton(self.weights(regions), rest)
        return {rid: floor + split.get(rid, 0) for rid in ids}


class MembraneReport:
    __slots__ = ("ghosts", "budget", "regions", "law")
    LAW = ("A renderer should not spend computation on what LOOKS important. It should spend computation "
           "where its PREDICTIONS are WEAKEST under the CONSEQUENCES of being wrong. "
           "observation → allocation; never observation → truth.")

    def __init__(self, ghosts, budget, regions):
        self.ghosts = ghosts            # list[Ghost] with render-ghost class in the detail
        self.budget = budget            # {id: integer compute budget}
        self.regions = regions          # {id: {uncertainty, consequence}}
        self.law = self.LAW

    def hottest(self, k=3):
        return sorted(self.budget.items(), key=lambda kv: kv[1], reverse=True)[:k]

    def __repr__(self):
        return "<MembraneReport ghosts=%d budgeted=%d>" % (len(self.ghosts), len(self.budget))


def membrane(prev_frame, cur_frame, observed_next_frame, consequence=None, total_budget=1000,
             floor=0, causal_uncertainty_threshold=2.0, causal_consequence_threshold=2):
    """The full Temporal Prediction Membrane over three consecutive VIEW frames + a consequence input.

    consequence : {id: int>=1} — declared future-consequence weight per object (INPUT, from causal_runtime).
                  Defaults to uniform 1. This module never computes consequence as truth.
    Returns a MembraneReport: classified ghosts (temporal vs the causal FPS-killer) + the Temporal Reality
    Budget allocation. It never reads or writes CORE.
    """
    rep = pred.observe(prev_frame, cur_frame, observed_next_frame, ghost_threshold=causal_uncertainty_threshold)
    uncertainty = rep.attention_hint                         # {id: G+}
    cons = consequence or {}
    regions = {rid: {"uncertainty": u, "consequence": int(cons.get(rid, 1))}
               for rid, u in uncertainty.items()}

    ghosts = []
    for rid, u in uncertainty.items():
        c = int(cons.get(rid, 1))
        if u >= causal_uncertainty_threshold and c >= causal_consequence_threshold:
            # the FPS killer: low prediction confidence AND high consequence
            info = classify_render_ghost(CAUSAL)
            ghosts.append(gr.Ghost(gr.CAUSAL, gr.MODEL_LIMIT,
                          "CAUSAL ghost at '%s' (G+=%.2f, consequence=%d): low prediction confidence where "
                          "being wrong matters → %s; NEVER %s" % (rid, u, c, info["response"], info["never"]),
                          magnitude=round(u, 4)))
        elif u >= causal_uncertainty_threshold:
            info = classify_render_ghost(TEMPORAL)
            ghosts.append(gr.Ghost(gr.TEMPORAL, gr.MODEL_LIMIT,
                          "TEMPORAL ghost at '%s' (G+=%.2f): prediction failed over time → %s; NEVER %s"
                          % (rid, u, info["response"], info["never"]), magnitude=round(u, 4)))

    budget = TemporalRealityBudget().allocate(regions, total_budget, floor=floor)
    return MembraneReport(ghosts, budget, regions)


def register():
    from .registry import REGISTRY, ALLOCATOR, LayerViolation
    try:
        REGISTRY.register("temporal_membrane", ALLOCATOR, mutates_core=False,
                          note="Temporal Reality Budget — allocates by uncertainty×consequence, not visible "
                               "complexity; observation→allocation, never →truth")
    except LayerViolation:
        pass
