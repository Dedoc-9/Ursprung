# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase4/topology.py — recover the intervention graph over LEARNED factors (Phase-2 logic).

Same asymmetry recovery as Phase 2 (`moves(i, j)` = does do(i) move j?), but the factors are now learned latent
coordinates rather than hand-written variables. The graph is over the recovered factors; the recovery still
uses ground-truth structural interventions (Phase 4 learns the representation, not the intervention).
"""
from __future__ import annotations

import numpy as np

from world import NODES, intervene, values


def moves(world, i, j, thresh=0.15):
    after = intervene(world, i)
    base = values(world)[j]
    return float(np.std(after[j] - base) / (np.std(base) + 1e-9)) > thresh


def response_matrix(world, thresh=0.15):
    return {i: {j: moves(world, i, j, thresh) for j in NODES if j != i} for i in NODES}


def roles(world, thresh=0.15):
    R = response_matrix(world, thresh)
    def role(n):
        mv = any(R[n][o] for o in R[n])
        moved = any(R[o].get(n, False) for o in NODES if o != n)
        if mv and not moved:
            return "root"
        if mv and moved:
            return "mediator"
        if moved and not mv:
            return "sink"
        return "isolated"
    return {n: role(n) for n in NODES}, R
