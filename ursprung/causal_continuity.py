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

HONEST BOUND: promotion is earned by the bench in TWO tiers, never asserted. The naive proportional form
was falsified; the re-specified water-filling form PASSED the constructed gate (`promotion_gate.py`,
seeds 1..8) → `supported_constructed`. The real-silicon gate has now RUN (M6b, `experiments/
bench_gpu_real`) on a *neutral* perceptual ruler — and did NOT support it. The constructed gate's metric
was U·C·P-weighted (the thing being optimized); strip that circularity and the support does not survive.
`integrity ≠ truth`; `declared ≠ verified`; `benchmark gain ≠ universal`.
"""
from __future__ import annotations

# Tier reached: "hypothesis" → "supported_constructed" (circular metric) → REAL SILICON, NEUTRAL ruler:
# M6b unsupported (flat loss) → M6c sweep REFINED it to CONDITIONAL. The strong/general claim stays
# falsified; a narrow conditional claim is supported on silicon. Never hard-code "law".
STATUS = "conditional_on_neutral_ruler"   # general claim FALSIFIED; conditional claim supported (see SWEEP_M6C)

# M6b (real silicon, ASUS ROG Xbox Ally X / Radeon 890M, Vulkan) — the falsification-grade result.
NEUTRAL_RULER_RESULT = (
    "M6b ran the actual gate on a SEALED, policy-neutral perceptual ruler (pixel/structural/temporal error vs "
    "a frozen 256-sample reference), policies allocating a per-tile sample budget from DECLARED priors only "
    "(the ruler is not in the policy's function scope — Goodhart is structurally unrepresentable). At equal "
    "measured GPU budget (1024 samples/frame, ~16/tile), under ε-dominance (ε measured from the data: "
    "pixel/struct/temporal ≈ 0.000083/0.000133/0.000090), UNIFORM allocation ε-dominates causal-waterfill in "
    "BOTH the aligned scene (priors track real difficulty) and the adversarial scene (priors anti-track it). "
    "ALIGNED: causal ties uniform on pixel/structural (within ε) but is measurably WORSE on temporal stability "
    "(gap 0.00014 > ε 0.00009) — concentration starves de-prioritized tiles into flicker while buying no "
    "measurable spatial accuracy at this near-converged budget. ADVERSARIAL: causal is worse on every axis "
    "(~28%, far above ε). So causal allocation showed NO measured upside at any alignment tested and a "
    "downside that grows under misalignment — an asymmetric, downside-only profile. This PARTIALLY FALSIFIES "
    "the constructed gate's blessing on a neutral metric. HONEST CEILING & open question: this is one device, "
    "one synthetic scene, one budget (16 samples/tile). Whether a LOWER budget — where tiles are genuinely "
    "unconverged and there is real error to reallocate — ever lets causal allocation reach the frontier is the "
    "open ghost (the variance-optimal exponent for SSAA error is ∝ difficulty^(2/3); causal weights ∝ "
    "difficulty, i.e. it likely OVER-concentrates). Pending an alignment×budget sweep (M6c)."
)

STATEMENT = ("Fidelity may be allocated according to expected future causal loss resulting from "
             "representational error.")

PROMOTION_CRITERIA = (
    "Two tiers, earned by the bench, never asserted. (1) SUPPORTED (constructed): at equal budget, the "
    "re-specified causal-waterfill yields strictly lower future-causal residual than EVERY control (uniform, "
    "distance, visibility, PFAL), is ≤ the structural-only optimum, the drifted control loses, and it holds "
    "across seeds (`promotion_gate.decide` / `.robust`), with the cardinal invariant intact. (2) LAW: "
    "additionally requires the real-silicon benchmark (equal GPU time — temporal artifacts, input-to-photon "
    "latency, reconstruction error, motion stability); constructed numbers expire there. The constructed gate "
    "PASSED; the real-silicon gate RAN (M6b) on a neutral perceptual ruler and did NOT support the policy as "
    "specified; the M6c sweep then REFINED that flat loss to a CONDITIONAL result (right exponent + informative "
    "priors). STATUS = conditional_on_neutral_ruler (not a law; general claim falsified, narrow conditional "
    "claim supported — see NEUTRAL_RULER_RESULT and SWEEP_M6C)."
)

# M6c (real silicon, Ally X) — the alignment × budget × exponent sweep that refined M6b's flat loss.
SWEEP_M6C = (
    "M6c swept prior_alignment α∈{+1,+0.5,0,-0.5,-1} × budget∈{2,4,8,16,64} avg samples/tile, running TWO "
    "causal exponents side by side: causal_d1 (∝√(U·C·P·resistance) ≈ difficulty^1, the M6b policy) and "
    "causal_d23 (∝(U·C·P·resistance)^(1/3) ≈ difficulty^(2/3), the VARIANCE-OPTIMAL exponent for SSAA error). "
    "Sealed policies, per-cell ε-dominance. THREE findings: (1) WRONG EXPONENT — causal_d1 over-concentrates: "
    "it reaches the ε-frontier only at the lowest budget (b2/α≥+0.5) and is dominated elsewhere, usually BY "
    "causal_d23. The corrected exponent is consistently better; M6b's flat loss was in large part a "
    "wrong-exponent artifact. (2) GENUINE BUT NARROW WINS — at α=+1 (informative priors), causal_d23 is the "
    "SOLE ε-frontier member (ε-DOMINATES uniform, not merely ties) at b8 and b64; the b8/α+1 win clears ε on "
    "all three axes (pixel 0.00009>ε0.00005, struct 0.00046>ε0.00014, temporal 0.00008>ε0.00005) — real, "
    "though sub-1%. (3) NO ROBUSTNESS MARGIN — at α≤0 (uninformative/inverted priors) uniform ε-dominates "
    "everywhere; the allocator does not detect that its own priors are wrong. GHOSTS kept as attention signals: "
    "a non-monotonic b4 dip (d23 loses at b4 but wins at b8 — likely Hamilton integer-rounding × the "
    "convergence curve) and a b2 scatter regime where even the drifted control reaches the frontier via "
    "tradeoffs (frontier membership is weak evidence at extreme scarcity). NET: the STRONG claim ('causal "
    "importance weighting generally beats neutral allocation at equal budget') remains FALSIFIED; a CONDITIONAL "
    "claim is supported on silicon — causal allocation helps only when the priors are informative AND the "
    "concentration exponent matches the convergence regime. A measured boundary, not a law. `benchmark gain ≠ "
    "universal`, and neither does a benchmark loss."
)

PROMOTION_RESULT = (
    "promotion_gate (seeds 1..8): SUPPORTED on the constructed bench. The re-specified causal-waterfill "
    "(rank U·C·P, water-fill samples ∝ √(U·C·P · representation_resistance)) strictly beats PFAL, the "
    "structural-only optimum, uniform, distance, visibility, and the drifted control on the future-causal "
    "residual, every seed. Two decisive isolations: it beats PFAL — dropping present-perception S helps the "
    "FUTURE-causal objective — and it beats structural-only — the causal weight adds value beyond geometry. "
    "Honest: the candidate is the analytic optimum of the DECLARED objective on the declared aliasing model; "
    "promotion to a LAW is pending real silicon. `declared ≠ verified`."
)

# Re-specification (Milestone 3.1): the failure split one object into two. See allocation.py / representation.py.
RESPECIFICATION = (
    "The bench did not falsify causal allocation — it falsified one allocation FUNCTION. Importance and "
    "allocation are different objects: Priority = U·C·P·S·τ RANKS regions; Allocation = "
    "WaterFill(Priority, RepresentationResistance) DISTRIBUTES the budget. 'PFAL ranks · water-filling "
    "allocates · Reality Debt constrains.' On the future-causal residual metric the two-stage allocator "
    "(rank by U·C·P, water-fill under perimeter resistance) STRICTLY BEATS uniform, distance, visibility, "
    "proportional-causal, and the drifted control (allocation.run, seed=1). This is a SUPPORTED hypothesis on "
    "the constructed bench — still pending real-silicon validation before promotion to a law."
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
