# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perceptual.py — Perceptual Continuity Loss (the measurable end-state).

The arena so far optimizes the **future-causal residual** — but humans experience **perceived continuity**,
and those are not guaranteed to align. Adding this term gives the project a measurable *success* axis instead
of only a resource-distribution theory:

    Reality Debt           → liability
    PFAL                   → priority
    Representation Resistance → difficulty
    Water-Filling          → allocation
    Perceptual Continuity  → SUCCESS

Perceptual Continuity Loss (PCL) measures the visible cost of *moving* fidelity between frames. An allocator
that chases the causal residual by reallocating samples every frame produces flicker/shimmer — a perceptual
discontinuity — even when each individual frame is "well allocated." PCL is the reallocation churn weighted
by perceptual sensitivity:

    PCL = Σ_t Σ_i  sensitivity_i · | alloc_t[i] − alloc_{t-1}[i] |

The deep point (the next likely discovery): **minimizing causal residual and maximizing perceptual continuity
are related but NOT identical objectives.** A policy can win one and lose the other — exactly the kind of
mismatch that has produced Ursprung's best refinements (cf. ranking ≠ allocation).

CLASSIFICATION: OBSERVER (mutates_core=False). It measures a presentation-quality proxy; it allocates nothing
and asserts no truth.

HONEST BOUND: PCL here is a declared proxy for temporal flicker (frame-to-frame reallocation), not a measured
human-perception study. Spatial discontinuity and contrast masking are not modeled yet. `integrity ≠ truth`.
"""
from __future__ import annotations


def perceptual_continuity_loss(prev_alloc, cur_alloc, sensitivity):
    """Visible cost of reallocating between two frames: Σ sensitivity · |Δ samples|. Lower is steadier."""
    ids = set(prev_alloc) | set(cur_alloc)
    return sum(max(1, int(sensitivity.get(i, 1))) * abs(cur_alloc.get(i, 0) - prev_alloc.get(i, 0))
               for i in ids)


def sequence_pcl(allocs, sensitivity):
    """Total PCL across a sequence of per-frame allocations. allocs: list[{id: samples}]."""
    return sum(perceptual_continuity_loss(allocs[t - 1], allocs[t], sensitivity)
               for t in range(1, len(allocs)))
