# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/fidelity_conservation.py — the Temporal Fidelity Accounting Law (the synthesis).

(The module keeps its filename; the law was stated earlier as "Conservation." The conserved-quantity framing
is a fixed-budget ACCOUNTING MODEL, not a physical conservation law — "conservation" names the bookkeeping, not
a conserved quantity of nature: model ≠ verified structure.)

THE LAW:

    A renderer does not create fidelity. It distributes finite fidelity across competing uncertainties.
    Therefore the objective is not maximum detail — it is MINIMUM CONSEQUENTIAL DISCONTINUITY under a fixed
    budget.

Fidelity is treated as not created but **transferred** — across space, across time, across representation:

    more fidelity here   = less fidelity somewhere else
    more fidelity now    = less fidelity later
    more spatial fidelity= less temporal fidelity
    more shading fidelity= less geometry fidelity

So every optimization is a transfer on a fixed budget, and the engineering problem is:

    maximize perceived continuity   subject to   a fixed frame budget        (≈ 4.13 ms)
    NOT  maximize local image quality

This is the bridge across the other three laws:
  · Arbitrary-Boundary Law      — the boundaries fidelity flows across are deterministic conventions.
  · PFAL / TCFF                 — WHERE/WHEN to move fidelity = expected future failure cost (U·C·P·S·τ).
  · Polygon Reconciliation Law  — rasterization is the TRANSPORT mechanism, not the strategy.

The hierarchy is re-centered (rasterization is no longer the center — it is transport):

    WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → RASTERIZATION → IMAGE
                                     ^^^^^^^^^^^^^^^^^^^^                  (the strategic layer)

CLASSIFICATION: OBSERVER / reference (mutates_core=False). It defines the conservation invariant and the
objective; it allocates nothing itself (the ALLOCATORs do) and asserts no truth.

HONEST BOUND: conservation here is over a DECLARED integer budget and DECLARED consequence/need — it makes
the zero-sum nature explicit and auditable; it does not measure real GPU joules or real perceptual
continuity (those are the silicon metrics, e.g. PCJ). `integrity ≠ truth`.
"""
from __future__ import annotations

# The fixed budget the conservation is solved under (~242 FPS). An OBSERVABLE target, never a gate.
FRAME_BUDGET_MS = 4.13


class ConservationError(Exception):
    """Raised when a fidelity transfer would create or destroy budget (violating conservation)."""


def total(allocation):
    return sum(allocation.values())


def is_conserved(allocation, budget):
    """The invariant: a valid allocation neither creates nor destroys fidelity — it sums to the budget."""
    return total(allocation) == budget


def transfer(allocation, src, dst, amount):
    """Move `amount` of fidelity from `src` to `dst`. Zero-sum by construction: the total is invariant.
    Fails closed if `src` lacks the fidelity (you cannot transfer what you do not have)."""
    if amount < 0:
        raise ConservationError("transfer amount must be non-negative")
    if allocation.get(src, 0) < amount:
        raise ConservationError("cannot transfer %d from %r (has %d)" % (amount, src, allocation.get(src, 0)))
    out = dict(allocation)
    out[src] = out.get(src, 0) - amount
    out[dst] = out.get(dst, 0) + amount
    return out


def consequential_discontinuity(regions, allocation):
    """The quantity to MINIMIZE: Σ consequence · (per-mille under-allocation). A starved high-consequence
    region contributes most; a fully-funded region contributes zero. regions: {id: {consequence, needed}}."""
    total_disc = 0
    for rid, r in regions.items():
        need = r.get("needed", 0)
        if need <= 0:
            continue
        got = allocation.get(rid, 0)
        under = max(0, need - got) * 1000 // need          # ‰ under-allocated
        total_disc += int(r.get("consequence", 1)) * under // 1000
    return total_disc


class TransferLedger:
    """Records each fidelity transfer with its reason — every optimization is an auditable, zero-sum move."""

    def __init__(self, allocation):
        self.allocation = dict(allocation)
        self.transfers = []

    def move(self, src, dst, amount, reason=""):
        self.allocation = transfer(self.allocation, src, dst, amount)
        self.transfers.append({"src": src, "dst": dst, "amount": amount, "reason": reason})
        return self.allocation

    def conserved_against(self, budget):
        return is_conserved(self.allocation, budget)


# --- the objective swap, demonstrated (max local quality vs min consequential discontinuity) --------

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


def alloc_max_local_quality(regions, budget):
    """The naive objective: spend on the most-detailed regions (by `needed`), blind to consequence."""
    return _hamilton({rid: r.get("needed", 1) for rid, r in regions.items()}, budget)


def alloc_min_discontinuity(regions, budget):
    """The conservation objective: spend by consequence, to minimize consequential discontinuity."""
    return _hamilton({rid: int(r.get("consequence", 1)) * r.get("needed", 1) for rid, r in regions.items()},
                     budget)


def demo(budget=600):
    import random
    rng = random.Random(1)
    regions = {}
    for i in range(40):
        # detail (needed) and consequence are deliberately anti-correlated: big background vs tiny critical
        needed = rng.randint(20, 40) if i % 3 else rng.randint(4, 10)
        consequence = rng.randint(1, 3) if i % 3 else rng.randint(7, 10)
        regions["r%02d" % i] = {"needed": needed, "consequence": consequence}
    a_local = alloc_max_local_quality(regions, budget)
    a_mind = alloc_min_discontinuity(regions, budget)
    print("Temporal Fidelity Conservation — objective swap (fixed budget=%d)" % budget)
    print("  both allocations are CONSERVED (zero-sum): Σ = budget")
    print("    max_local_quality conserved:  %s (Σ=%d)" % (is_conserved(a_local, budget), total(a_local)))
    print("    min_discontinuity conserved:  %s (Σ=%d)" % (is_conserved(a_mind, budget), total(a_mind)))
    print("  consequential discontinuity (lower = better):")
    print("    max local quality:        %d" % consequential_discontinuity(regions, a_local))
    print("    min consequential disc.:  %d" % consequential_discontinuity(regions, a_mind))
    print("  → same conserved budget, fewer consequential discontinuities when fidelity flows by consequence.")
    print("  Honest bound: declared integer budget/consequence; not measured joules. integrity ≠ truth.")
    return regions, a_local, a_mind


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("fidelity_conservation", OBSERVER, mutates_core=False,
                          note="Temporal Fidelity Conservation Law — fidelity is transferred, not created; "
                               "minimize consequential discontinuity under a fixed budget")
    except LayerViolation:
        pass
