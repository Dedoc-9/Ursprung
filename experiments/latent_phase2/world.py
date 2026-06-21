# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase2/world.py — a structural world with a chain, for topology discovery.

Phase 1 asked "is this factor causally relevant?" The mediator caveat showed that is not enough. Phase 2 asks
"where does this factor sit in the intervention graph?" — a topology-discovery problem, not a score problem.

The structural causal model (root → mediator → sink, plus an isolated observed factor):

    g ~ N(0,1)              ROOT       (cause of everything downstream)
    x = g + 0.3·noise       MEDIATOR   (x = f(g); carries g's effect)
    y = x + 0.3·noise       SINK / OUTCOME (y = f(x); depends on g only through x)
    c ~ N(0,1)              ISOLATED   (observed, correlated into X, but NOT in the causal chain)

Interventions reveal asymmetries a single effect-magnitude cannot:

    do(g) → moves x and y          do(x) → moves y, NOT g
    do(y) → moves nothing          do(c) → moves nothing in {g,x,y}

Both g and x are "causally relevant to the outcome" (Tier 2 passes for both). Only the *topology* (Tier 3)
separates the root from the mediator. Seeded → replayable.
"""
from __future__ import annotations

import numpy as np

N_DEFAULT = 4000
NODES = ("g", "x", "y", "c")


def make_world(n=N_DEFAULT, seed=0):
    r = np.random.default_rng(seed)
    g = r.standard_normal(n)
    x = g + 0.3 * r.standard_normal(n)
    y = x + 0.3 * r.standard_normal(n)
    c = r.standard_normal(n)                  # isolated: observed but acausal to the g→x→y chain
    return {"g": g, "x": x, "y": y, "c": c, "n": n, "seed": seed}


def intervene(world, do_node, seed=1):
    """do(node): resample it independently, propagate the structural equations DOWNSTREAM, return new values.
    The downstream propagation is what makes the intervention graph asymmetric (a mediator's parents do not
    move when the mediator is set)."""
    r = np.random.default_rng(seed)
    n = world["n"]
    g, x, y, c = (world["g"].copy(), world["x"].copy(), world["y"].copy(), world["c"].copy())
    if do_node == "g":
        g = r.standard_normal(n); x = g + 0.3 * r.standard_normal(n); y = x + 0.3 * r.standard_normal(n)
    elif do_node == "x":
        x = r.standard_normal(n); y = x + 0.3 * r.standard_normal(n)
    elif do_node == "y":
        y = r.standard_normal(n)
    elif do_node == "c":
        c = r.standard_normal(n)
    else:
        raise ValueError("unknown node %r" % do_node)
    return {"g": g, "x": x, "y": y, "c": c, "n": n}


def moves(world, i, j, thresh=0.15):
    """Does do(i) move j? (normalized by j's own scale). The atom of topology recovery."""
    after = intervene(world, i)
    return float(np.std(after[j] - world[j]) / (np.std(world[j]) + 1e-9)) > thresh
