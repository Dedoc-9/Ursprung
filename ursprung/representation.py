# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/representation.py — Representation Resistance and Debt Pressure (the hidden variable the bench exposed).

Milestone 3 revealed that the optimal fidelity allocation must include the error's own structural term — how
hard a region is to represent accurately under current raster constraints. That term generalizes to:

    RepresentationResistance — how difficult a region is to represent faithfully (edge complexity / perimeter
                               / sub-pixel detail / motion). Some regions are expensive to approximate
                               correctly; others are cheap.

Composed with the Reality Debt Law, this gives the quantity a real GPU actually faces:

    DebtPressure = RealityDebt × RepresentationResistance
                 = (Approximation × Persistence × Consequence) × RepresentationResistance

So the renderer allocates by **future consequence AND the difficulty of representing it faithfully** —
"allocate by expected future causal loss UNDER the cost of representing it." This converts the Milestone-3
failure into a refinement rather than a dead end.

CLASSIFICATION: OBSERVER / reference (mutates_core=False). It measures difficulty; it allocates nothing and
asserts no truth.

HONEST BOUND: `representation_resistance` here is a declared proxy (screen perimeter ≈ 8·half-extent — edge
length, where aliasing concentrates). Real resistance depends on shading complexity, motion, occlusion
boundaries, and material — not modeled yet. `integrity ≠ truth`.
"""
from __future__ import annotations


def representation_resistance(region):
    """A region's difficulty-to-represent proxy: screen-space edge length (perimeter ≈ 8·size). Edges are
    where coverage/sampling conventions fail most, so perimeter is a first-order resistance term. Higher ⇒
    harder ⇒ deserves more samples per unit importance."""
    size = region.get("size", 1)
    return max(1, 8 * int(size))


def debt_pressure(reality_debt, resistance):
    """DebtPressure = RealityDebt × RepresentationResistance — future liability scaled by how hard the region
    is to represent. The quantity allocation should ultimately follow (under a water-filling distribution)."""
    return max(0, reality_debt) * max(1, resistance)
