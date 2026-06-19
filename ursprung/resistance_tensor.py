# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/resistance_tensor.py — multi-dimensional Representation Resistance + the fidelity derivative.

The cliff result (M3.1/M5) warned that scalar perimeter resistance is threshold-blind. Real failure is
multi-dimensional: a wireframe edge and a fast reflective object can have the same polygon count and utterly
different fidelity risk. The Resistance Tensor replaces "how complex is it?" with "what dimension of
approximation is currently failing?":

    R = [ spatial_discontinuity, temporal_instability, lighting_sensitivity, motion_sensitivity,
          occlusion_sensitivity, reconstruction_sensitivity, latency_sensitivity ]

`miss_cost` is how expensive it is to be WRONG about a region's representation (used by the shader cache to
decide which cached paths are expensive to miss). The **fidelity derivative** is the marginal-utility signal
the project was missing — not "where should fidelity go?" but "where does one more unit of budget buy the
most continuity?":

    ∂Fidelity / ∂Budget   (40%→70% is worth a lot; 95%→96% is worth ~nothing)

CLASSIFICATION: OBSERVER (mutates_core=False). It measures difficulty and marginal utility; it allocates
nothing and asserts no truth.

HONEST BOUND: the seven dimensions are declared proxies, not measured GPU/perception quantities; `composite`
is a declared bounded combination, not a learned model. `integrity ≠ truth`.
"""
from __future__ import annotations

DIMENSIONS = ("spatial_discontinuity", "temporal_instability", "lighting_sensitivity", "motion_sensitivity",
              "occlusion_sensitivity", "reconstruction_sensitivity", "latency_sensitivity")


def resistance_tensor(region):
    """Extract the 7-dim resistance vector from a region (missing dims default to 1, the low-risk floor)."""
    return {d: max(0, int(region.get(d, 1))) for d in DIMENSIONS}


def composite(tensor, weights=None):
    """A bounded combination of the dimensions → a scalar resistance. Default: weighted sum (declared). A
    region is hard to represent if ANY dimension is high, so a max term is folded in to preserve cliffs."""
    w = weights or {d: 1 for d in DIMENSIONS}
    wsum = sum(w.get(d, 1) * tensor.get(d, 0) for d in DIMENSIONS)
    peak = max(tensor.values()) if tensor else 0
    return wsum + peak * 4          # the peak term keeps a single failing dimension (a cliff) visible


def dominant_dimension(tensor):
    """The currently-failing dimension — *what kind* of approximation is breaking, not just how much."""
    if not tensor:
        return None
    return max(DIMENSIONS, key=lambda d: tensor.get(d, 0))


def miss_cost(region):
    """How expensive it is to be WRONG about this region's representation. The shader cache uses this to
    decide which cached paths are expensive to miss. = composite resistance of its tensor."""
    return composite(resistance_tensor(region))


def fidelity_derivative(quality_fn, budget, step=1):
    """∂Fidelity/∂Budget ≈ (Q(budget+step) − Q(budget)) / step — marginal continuity per unit budget.
    `quality_fn(budget) -> int` returns the continuity/quality achieved at that budget. Higher = more worth
    spending the next unit here."""
    if step <= 0:
        return 0
    return (quality_fn(budget + step) - quality_fn(budget)) / step


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("resistance_tensor", OBSERVER, mutates_core=False,
                          note="multi-dimensional Representation Resistance (7 dims) + miss_cost + fidelity "
                               "derivative (∂Fidelity/∂Budget marginal utility); replaces the scalar perimeter proxy")
    except LayerViolation:
        pass
