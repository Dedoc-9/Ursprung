# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/reality_debt.py — the Reality Debt Law (the law underneath the other four).

THE LAW:

    Every approximation incurs reality debt. The role of predictive allocation is not to eliminate debt, but
    to ensure debt accumulates where future consequence is lowest and repayment cost is smallest.

    Debt = Approximation × Persistence × Consequence

The pioneering reframing: **fidelity is conserved, but debt is accumulated.** So PFAL/TCFF are not merely
allocating fidelity — they are allocating DEBT REPAYMENT. The renderer becomes a financial system for
approximation. Every optimization is one of two things, and the distinction is the whole point:

    BORROWING — reduces cost now by taking fidelity from the future (incurs debt that comes due as an artifact)
    GENUINE   — reduces cost with no future fidelity loss (no debt)

A traditional optimizer asks "save 0.5 ms?". Ursprung asks "save 0.5 ms — and is it borrowed or genuine?"

| Approximation             | Immediate benefit | Future debt              |
|---------------------------|-------------------|--------------------------|
| aggressive LOD            | lower cost now    | pop-in later             |
| temporal reconstruction   | fewer samples now | ghosting later           |
| culling                   | less work now     | visibility error later   |
| quantization              | less memory now   | precision error later    |
| prediction                | lower latency now | mis-prediction later     |

This is where Dini-style observation becomes anticipatory: most engines ask "artifact detected"; Ursprung asks
"which approximation created it?" and then "which approximation is likely to create the NEXT one?" — so debt
is placed before it comes due.

The hierarchy gains a debt-management layer (rasterization stays transport):

    WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → DEBT MANAGEMENT → RASTERIZATION → IMAGE
    truth → prediction → fidelity → debt → image  (compactly)

CLASSIFICATION: OBSERVER / reference (mutates_core=False). It accounts for debt and recommends where it
should accumulate; it allocates nothing itself and asserts no truth.

HONEST BOUND: debt here is computed over DECLARED approximation/persistence/consequence — an accounting
model that makes the borrow-vs-genuine distinction explicit and auditable, not a measurement of real future
artifacts. `integrity ≠ truth`.
"""
from __future__ import annotations

# Known approximation classes and their debt signature (immediate benefit vs the artifact that comes due).
APPROXIMATIONS = {
    "aggressive_lod":          {"benefit": "lower cost now",    "debt_artifact": "pop-in later",          "category": "spatial"},
    "temporal_reconstruction": {"benefit": "fewer samples now", "debt_artifact": "ghosting later",        "category": "temporal"},
    "culling":                 {"benefit": "less work now",     "debt_artifact": "visibility error later", "category": "perceptual"},
    "quantization":            {"benefit": "less memory now",   "debt_artifact": "precision error later",  "category": "numerical"},
    "prediction":              {"benefit": "lower latency now", "debt_artifact": "mis-prediction later",   "category": "temporal"},
}


def debt(approximation, persistence, consequence):
    """Debt = Approximation × Persistence × Consequence. Higher approximation, longer-lived, and more
    consequential ⇒ more debt. A genuine (non-borrowing) optimization has approximation 0 ⇒ debt 0."""
    return max(0, approximation) * max(0, persistence) * max(0, consequence)


def is_borrowing(reduces_future_fidelity):
    """The distinction that matters: borrowing fidelity from the future incurs debt; a genuine cost
    reduction does not. Returns True iff the optimization takes fidelity from a future frame."""
    return bool(reduces_future_fidelity)


class DebtRecord:
    __slots__ = ("kind", "approximation", "persistence", "consequence", "debt", "borrowed", "region")

    def __init__(self, kind, approximation, persistence, consequence, borrowed=True, region=None):
        self.kind = kind
        self.approximation = approximation
        self.persistence = persistence
        self.consequence = consequence
        self.debt = debt(approximation, persistence, consequence) if borrowed else 0
        self.borrowed = borrowed
        self.region = region

    def __repr__(self):
        return "<DebtRecord %s debt=%d %s>" % (self.kind, self.debt, "borrowed" if self.borrowed else "genuine")


class DebtLedger:
    """Accounts for accumulated reality debt. Fidelity is conserved elsewhere; debt is what accrues here."""

    def __init__(self):
        self.records = []

    def incur(self, kind, approximation, persistence, consequence, borrowed=True, region=None):
        rec = DebtRecord(kind, approximation, persistence, consequence, borrowed, region)
        self.records.append(rec)
        return rec

    def total_debt(self):
        return sum(r.debt for r in self.records)

    def by_category(self):
        out = {}
        for r in self.records:
            cat = APPROXIMATIONS.get(r.kind, {}).get("category", "unclassified")
            out[cat] = out.get(cat, 0) + r.debt
        return out

    def repayment_priority(self):
        """Repay (raise fidelity for) debt where CONSEQUENCE is highest first — that is where coming due
        hurts most. Ties broken by debt then kind for determinism."""
        return sorted(self.records, key=lambda r: (-r.consequence, -r.debt, r.kind))


def recommend_debt_placement(regions):
    """Given {region: future_consequence}, return regions ordered LOWEST-consequence first — the order in
    which debt should be allowed to accumulate (place debt where being wrong matters least). Deterministic
    (ties by region key). This is a RECOMMENDATION for an allocator, never a truth about the regions."""
    return sorted(regions, key=lambda rid: (regions[rid], rid))


def demo():
    # two strategies place the same amount of debt; one follows the law (low-consequence first), one doesn't
    regions = {"sky": 1, "far_wall": 2, "crosshair": 9, "enemy": 10}
    print("Reality Debt Law — place debt where future consequence is lowest")
    order = recommend_debt_placement(regions)
    print("  recommended debt placement (low consequence first):", order)
    # lawful: dump approximation onto the two lowest-consequence regions
    lawful = DebtLedger()
    for rid in order[:2]:
        lawful.incur("aggressive_lod", approximation=8, persistence=3, consequence=regions[rid], region=rid)
    # naive: dump the same approximation onto the two highest-consequence regions
    naive = DebtLedger()
    for rid in order[-2:]:
        naive.incur("aggressive_lod", approximation=8, persistence=3, consequence=regions[rid], region=rid)
    print("  consequential debt — lawful placement: %d   naive placement: %d"
          % (lawful.total_debt(), naive.total_debt()))
    print("  → same approximation, far less consequential debt when it lands on low-consequence regions.")
    # borrow vs genuine
    g = DebtLedger(); g.incur("cache_reuse_unchanged_tile", approximation=5, persistence=4, consequence=10, borrowed=False)
    print("  a GENUINE cost reduction (borrowed=False) incurs debt:", g.total_debt(), "(zero)")
    print("  Honest bound: declared accounting, not measured future artifacts. integrity ≠ truth.")
    return lawful, naive


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("reality_debt", OBSERVER, mutates_core=False,
                          note="Reality Debt Law — every approximation incurs debt = approx×persistence×"
                               "consequence; place debt where consequence is lowest; repay where highest")
    except LayerViolation:
        pass
