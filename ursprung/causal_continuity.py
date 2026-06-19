# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/causal_continuity.py — the Causal Continuity HYPOTHESIS (provisional; not yet a law).

STATEMENT (provisional):

    Fidelity may be allocated according to expected future causal loss resulting from representational error.

This is NOT a law. It is an explicit hypothesis that becomes a law only if it survives implementation,
replay, a negative control, and equal-budget benchmarking against the existing policies (uniform, distance,
visibility, PFAL). If it fails, the failure is kept as architectural information. The Ursprung discipline:

    interesting idea → explicit hypothesis → deterministic implementation → replay → negative control
                     → benchmark → (only then) law

The PFAL ⇄ Reality-Debt duality this sits on top of:

    PFAL:   R    = U × C × P × S × τ     allocates future FIDELITY        (the payment)
    Debt:   Debt = Approximation × P × C  measures future LIABILITY        (the cost)

They share Persistence and Consequence; τ is the time-axis of persistence; Approximation is the inverse of
the fidelity PFAL buys. So they are the payment and the cost of one ledger. Causal Continuity is the limit
both approach: drop the *present-perception* term S and allocate purely by **expected future causal loss** —
uncertainty, consequence, and persistence as proxies for future causal impact:

    expected_future_causal_loss(region) = U × C × P      (future-causal; no present-perception term)

The distinction from PFAL is deliberate and testable: PFAL includes S (how visible the error is NOW); Causal
Continuity does not (it weights how much being wrong costs the world's FUTURE causal structure). A region can
be perceptually loud now but causally inert, or quiet now but causally pivotal — the bench is built to tell
them apart (`raster_bench.py`).

CLASSIFICATION: OBSERVER (mutates_core=False). It proposes an allocation weighting; it allocates nothing
itself, asserts no truth, and is explicitly provisional.

HONEST BOUND: a hypothesis with a measurement plan, not a result. `STATUS` stays "hypothesis" until
`earns_promotion()` is satisfied by a real bench. `integrity ≠ truth`.
"""
from __future__ import annotations

STATUS = "hypothesis"   # never hard-code "law"; promotion is earned by the bench, not asserted

STATEMENT = ("Fidelity may be allocated according to expected future causal loss resulting from "
             "representational error.")

PROMOTION_CRITERIA = (
    "Promoted to a law ONLY if, at equal budget, causal-continuity allocation yields strictly lower "
    "consequential discontinuity / future failure cost than EVERY control (uniform, distance, visibility, "
    "PFAL), AND a drifted negative control loses, AND the cardinal invariant (CORE trajectory unchanged) "
    "holds throughout. Otherwise it remains a hypothesis and the result is recorded as architectural "
    "information."
)

# Milestone-3 result (raster_bench, seed=1) — recorded, NOT promoted. The stated (proportional) form FAILS.
FINDINGS = (
    "STATUS stays 'hypothesis': the STATED form (allocate ∝ U·C·P) loses even to uniform on the VIEW slice "
    "(causal ≈2.15e6 vs uniform ≈1.68e6), because the aliasing-error metric is CONVEX in samples — "
    "proportional allocation over-concentrates. Two corrections fall out of the failure: (1) use WATER-FILLING "
    "form (∝ √weight) not proportional; (2) the weight must include the error's structural term (size/"
    "perimeter), which U·C·P omits. Re-specified causal must beat uniform AND the size-aware optimum before "
    "promotion. Failure kept as architectural information (Ursprung discipline)."
)


def expected_future_causal_loss(region):
    """U × C × P — uncertainty × consequence × persistence, as proxies for future causal impact. Note the
    absence of S (present perceptual sensitivity): this weights future causal cost, not current visibility."""
    u = int(round(region.get("uncertainty", 0.0) * 100))
    c = int(region.get("consequence", 1))
    p = int(region.get("persistence", 1))
    return max(0, u) * max(1, c) * max(1, p)


def allocate_weights(regions):
    """Per-region integer weight for an allocator to apportion a budget by (expected future causal loss)."""
    return {rid: expected_future_causal_loss(r) for rid, r in regions.items()}


def duality_note():
    """The dual relationship, returned as data so it travels with the code."""
    return {
        "pfal": "R = U*C*P*S*tau  (allocates future fidelity — the payment)",
        "debt": "Debt = Approximation*P*C  (measures future liability — the cost)",
        "shared": ["consequence", "persistence"],
        "causal_continuity_limit": "allocate by U*C*P (expected future causal loss); drop present-perception S",
    }


def earns_promotion(bench_result):
    """Decide promotion from a raster_bench result dict {policy: consequential_error}. Returns
    (promote: bool, reason). Lower error is better. Causal must strictly beat ALL controls and the drifted
    control must not win."""
    if not bench_result or "causal (U×C×P)" not in bench_result:
        return False, "no bench result"
    causal = bench_result["causal (U×C×P)"]
    controls = {k: v for k, v in bench_result.items()
                if k in ("uniform", "distance", "visibility", "pfal (U×C×P×S)")}
    drifted = bench_result.get("drifted (control)")
    beats_all = all(causal < v for v in controls.values())
    control_loses = (drifted is None) or (drifted >= causal)
    if beats_all and control_loses:
        return True, "causal strictly beats every control at equal budget; control loses"
    if not beats_all:
        worst = min(controls, key=lambda k: controls[k])
        return False, "does not beat %s (%.3f vs causal %.3f) — remains a hypothesis" % (
            worst, controls[worst], causal)
    return False, "negative control did not lose — remains a hypothesis"


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("causal_continuity", OBSERVER, mutates_core=False,
                          note="PROVISIONAL hypothesis — allocate fidelity by expected future causal loss "
                               "(U*C*P); promoted to a law only by the equal-budget bench, never asserted")
    except LayerViolation:
        pass
