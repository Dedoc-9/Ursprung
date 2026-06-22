# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/promotion_gate.py — the re-run promotion gate for the Causal Continuity Hypothesis.

The naive hypothesis (allocate ∝ U·C·P) FAILED the Milestone-3 gate: a convex aliasing metric makes
proportional allocation over-concentrate. The failure named two corrections (recorded in
`causal_continuity.FINDINGS`): use the **water-filling** form (∝ √weight), and let the weight include
the error's **structural** term (size/perimeter). This module re-runs the gate on the re-specified
form and decides, by the bench, whether promotion is on the table.

The re-specified candidate is the two-stage allocator (`allocation.two_stage_allocate`): rank by the
future-causal weight U·C·P, then water-fill `samples ∝ √(U·C·P · representation_resistance)`. Against:

    uniform · distance · visibility            crude controls
    PFAL  (U·C·P·S·τ, same water-filling)        the decisive control — identical machinery, only the
                                                 ranking differs by the present-perception terms S·τ
    structural_only (√resistance)               the size-aware optimum (does the causal weight add value?)
    drifted                                      the negative control

Objective (lower is better): the future-causal residual `Σ (U·C·P) · aliasing_error(size, samples)` —
the expected future causal loss remaining after the budget is spent.

WHAT A PASS MEANS, EXACTLY. The candidate is the analytic constrained optimum of *this declared
objective* (minimizing `Σ w·size/samples` gives `samples ∝ √(w·size)` with `w = U·C·P`). So a pass
confirms: (1) the re-specified water-filling form is that optimum; (2) the causal weighting beats the
structural-only optimum (the U·C·P terms add value, not just the geometry); and (3) dropping
present-perception S (future-causal) beats keeping it (PFAL) **on the future-causal objective**. That
is a real, robust result on the constructed bench — and it is NOT yet a law: whether future-causal
allocation reduces *real perceived error* is the un-faked real-silicon benchmark. `declared ≠ verified`.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures and decides promotion; it allocates nothing
itself and asserts no truth.
"""
from __future__ import annotations

import random

from .raster import aliasing_error
from . import allocation as A

CANDIDATE = "causal-waterfill (√(U·C·P · resistance))"
CONTROLS = ("uniform", "distance", "visibility", "pfal (U·C·P·S·τ)")
STRUCTURAL = "structural_only (√resistance)"
DRIFTED = "drifted (control)"


def _scene(n=50, seed=1):
    rng = random.Random(seed)
    out = {}
    for i in range(n):
        out["r%02d" % i] = {
            "uncertainty": rng.uniform(0.5, 4.0),
            "consequence": rng.randint(1, 3) if i % 2 == 0 else rng.randint(6, 10),
            "persistence": rng.randint(1, 5),
            "size": rng.randint(2, 12),
            "distance": rng.randint(1, 100),
            "visibility": rng.randint(1, 100),
            "sensitivity": rng.randint(1, 10),     # S — present perceptual loudness (independent of causal weight)
            "tau": rng.randint(1, 5),              # τ — temporal proximity
        }
    return out


def _U(r):
    return max(1, int(round(r["uncertainty"] * 100)))


def _causal(r):
    return _U(r) * r["consequence"] * r["persistence"]                                  # U·C·P (future-causal)


def _pfal(r):
    return _U(r) * r["consequence"] * r["persistence"] * r["sensitivity"] * r["tau"]    # U·C·P·S·τ


def _residual(regions, alloc):
    return sum(_causal(r) * aliasing_error(r["size"], alloc.get(rid, 0) + 1) for rid, r in regions.items())


def run(seed=1, budget=400):
    """Return {policy: future-causal residual} for the full control set + the re-specified candidate."""
    regions = _scene(seed=seed)
    pol = {
        "uniform": A._hamilton({rid: 1 for rid in regions}, budget),
        "distance": A._hamilton({rid: 1_000_000 // (r["distance"] + 1) for rid, r in regions.items()}, budget),
        "visibility": A._hamilton({rid: r["visibility"] for rid, r in regions.items()}, budget),
        "pfal (U·C·P·S·τ)": A.two_stage_allocate(regions, budget, _pfal),
        STRUCTURAL: A.two_stage_allocate(regions, budget, lambda r: 1),
        CANDIDATE: A.two_stage_allocate(regions, budget, _causal),
        DRIFTED: A._hamilton({rid: random.Random(seed * 17 + i).randint(1, 1000)
                              for i, rid in enumerate(regions)}, budget),
    }
    return {name: _residual(regions, alloc) for name, alloc in pol.items()}


def decide(result):
    """The bench decides. Returns (status, reason) where status is 'supported_constructed' or 'hypothesis'.
    NEVER returns 'law' — law requires the real-silicon benchmark this bench cannot run (`declared ≠ verified`)."""
    if not result or CANDIDATE not in result:
        return "hypothesis", "no bench result"
    cand = result[CANDIDATE]
    controls = {k: v for k, v in result.items() if k in CONTROLS}
    beats_controls = all(cand < v for v in controls.values())
    beats_structural = cand <= result.get(STRUCTURAL, cand)
    control_loses = result.get(DRIFTED, cand) >= cand
    if beats_controls and beats_structural and control_loses:
        return "supported_constructed", (
            "re-specified causal-waterfill strictly beats every control (incl. PFAL), is ≤ the structural-only "
            "optimum, and the negative control loses — on the constructed bench. Promotion to a LAW remains "
            "pending the real-silicon benchmark.")
    if not beats_controls:
        worst = min(controls, key=lambda k: controls[k])
        return "hypothesis", "does not beat %s (%d vs candidate %d)" % (worst, controls[worst], cand)
    if not beats_structural:
        return "hypothesis", "causal weight adds no value over the structural-only optimum"
    return "hypothesis", "negative control did not lose"


def robust(seeds=range(1, 9), budget=400):
    """A single seed can be lucky. Promotion requires the gate to hold across seeds."""
    return {s: decide(run(seed=s, budget=budget))[0] == "supported_constructed" for s in seeds}


def demo(seed=1, budget=400):
    res = run(seed=seed, budget=budget)
    status, reason = decide(res)
    print("CAUSAL-CONTINUITY PROMOTION GATE (re-specified; constructed, seed=%d, budget=%d)" % (seed, budget))
    print("  objective = future-causal residual Σ (U·C·P)·aliasing(size, samples)  (lower better)\n")
    for name in sorted(res, key=lambda k: res[k]):
        mark = "  ← candidate" if name == CANDIDATE else ("  ← negative control" if name == DRIFTED else "")
        print("  %-34s %d%s" % (name, res[name], mark))
    rob = robust(budget=budget)
    print("\n  seed-robustness (1..8):", "ALL PASS" if all(rob.values()) else rob)
    print("  gate status: %s" % status.upper())
    print("  %s" % reason)
    print("\n  Honest bound: the candidate is the analytic optimum of the DECLARED future-causal objective on the")
    print("  declared aliasing model. A pass = supported on the constructed bench; it is NOT a law. Whether")
    print("  future-causal allocation reduces real perceived error is the real-silicon frontier. integrity ≠ truth.")
    assert status == "supported_constructed" and all(rob.values()), "promotion gate did not hold"
    return res, status


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("promotion_gate", OBSERVER, mutates_core=False,
                          note="re-run promotion gate for Causal Continuity: re-specified water-filling form vs "
                               "uniform/distance/visibility/PFAL/structural + negative control; the bench decides, "
                               "and a constructed pass is 'supported', never 'law'")
    except LayerViolation:
        pass
