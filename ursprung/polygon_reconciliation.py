# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/polygon_reconciliation.py — the Polygon Reconciliation Law, encoded as data + a decision rule.

THE LAW (Dentatus formulation):

    Polygons are not preserved because they are correct. Polygons are preserved because abandoning them
    imposes greater practical cost than their approximation error. Therefore the optimization target is not
    polygon replacement, but polygon RECONCILIATION under a fixed 4.13 ms budget. Polygons cannot be
    marginalized.

This is the Arbitrary-Boundary Law applied to representation itself. Polygons are not the truth of the world
— but they are the practical exchange medium of the graphics industry, integrated with hardware, APIs,
content tools, engines, artists, and asset ecosystems. Ursprung therefore treats polygons as a deterministic
**convention** and an **industrial compatibility layer**, not an ontological commitment:

    polygons              → the industrial compatibility layer  (interoperability, tooling, assets)
    rasterization         → the execution mechanism             (throughput, hardware acceleration)
    predictive allocation → the fidelity multiplier             (PFAL/TCFF: spend where error costs most)

The engineering task is NOT to prove polygons are correct, nor to replace them with a "purer"
representation, but to MANAGE WHERE AND HOW their approximations fail — concentrating fidelity (via the
observation/prediction/salience/temporal stack) where future perceptual error, temporal instability, and
causal consequence are greatest, within a strict frame budget.

CLASSIFICATION: OBSERVER / reference (mutates_core=False). It declares a convention and a deterministic
decision rule; it changes no committed state and asserts no truth about representation.

HONEST BOUND: `reconcile()` is a deterministic policy over DECLARED costs — it does not measure the real
abandonment cost or approximation error, and it never claims polygons are the right description of reality.
`integrity ≠ truth`; the convention is a choice, recorded, not a discovery.
"""
from __future__ import annotations

from . import conventions as conv

# The fixed budget the reconciliation is optimized under (~242 FPS). An OBSERVABLE target, never a gate.
FRAME_BUDGET_MS = 4.13

# Representations polygons are reconciled *with* (not replaced *by*) — the rejected-replacement set.
ALTERNATIVE_REPRESENTATIONS = (
    "voxels", "point clouds", "neural fields", "Gaussian splats",
    "signed distance fields", "hybrid scene graphs",
)


def reconcile(abandonment_cost, approximation_error):
    """The deterministic decision rule: KEEP polygons iff abandoning them costs at least as much as their
    approximation error. A choice over declared costs — not a truth claim about representation.

    Returns a dict carrying the verdict and the (recorded) inputs, so the decision is auditable.
    """
    keep = abandonment_cost >= approximation_error
    return {
        "keep_polygons": keep,
        "abandonment_cost": abandonment_cost,
        "approximation_error": approximation_error,
        "rationale": ("abandoning polygons costs more than their approximation error → reconcile, "
                      "do not replace" if keep else
                      "approximation error exceeds abandonment cost → a replacement may be justified"),
        "truth_claim": False,   # this is a cost-based choice, never a claim that polygons are 'real'
        "optimization_target": "reconciliation under a %.2f ms budget, not replacement" % FRAME_BUDGET_MS,
    }


def declare_into(ledger=None):
    """Declare the polygon + rasterization substrate choices into a Boundary Ledger (defaults to a fresh
    one). Each is a CONVENTION carrying its purpose, the cost-based reason it was selected, its deterministic
    rule, and the replacement alternatives it rejected — `truth_claim = False`."""
    L = ledger or conv.default_ledger()
    L.declare(
        "polygon_substrate", conv.RASTERIZATION,
        rule="triangulated polygon meshes are the exchange medium / industrial compatibility layer",
        purpose="interoperate with existing hardware, APIs, content tools, engines, artists, and asset "
                "ecosystems built around polygonal representations",
        selected_reason="abandoning polygons imposes greater practical cost than their approximation error "
                        "(reconcile, do not replace); polygons cannot be marginalized",
        deterministic_rule="reconcile(abandonment_cost, approximation_error): keep iff abandonment_cost >= "
                           "approximation_error",
        alternatives_rejected=list(ALTERNATIVE_REPRESENTATIONS))
    L.declare(
        "rasterization_substrate", conv.RASTERIZATION,
        rule="rasterization is the execution mechanism; predictive allocation is the fidelity multiplier",
        purpose="best balance of throughput, compatibility, and fidelity within a strict frame budget",
        selected_reason="contemporary hardware accelerates raster; observation/prediction decide WHERE "
                        "fidelity is concentrated, polygons express it efficiently",
        deterministic_rule="raster coverage + LOD + sampling are deterministic conventions (see "
                           "pixel_coverage, lod_threshold); manage where they fail, do not pretend they are truth",
        alternatives_rejected=["pure path tracing as the primary substrate", "fully neural frame synthesis"])
    return L


# A ledger that includes the reconciliation conventions, ready to pin into a render Verification Record.
RECONCILED_LEDGER = declare_into()


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("polygon_reconciliation", OBSERVER, mutates_core=False,
                          note="Polygon Reconciliation Law — polygons as deterministic convention + "
                               "compatibility layer; reconcile() not replace; never a truth claim")
    except LayerViolation:
        pass
