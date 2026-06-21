# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase2/topology.py — recover the intervention graph from do() asymmetries (the centerpiece).

Tier 3 of the benchmark hierarchy, sitting between intervention-relevance (Tier 2) and robustness (Tier 4):

    Tier 1  reconstruction        (entry gate)
    Tier 2  intervention relevance (causally relevant?)            ← Phase 1's gate
    Tier 3  topology recovery      (WHERE in the graph?)           ← here
    Tier 4  robustness across 𝓕
    Tier 5  gauge invariance

A latent that passes Tier 2 but fails Tier 3 is exactly the **mediator**: causally relevant, but not the root.
The recovery is purely from intervention asymmetries — `moves(i, j)` = "does do(i) move j?" — built into a
response matrix, then read as a partial order:

    role(node):  root      = moves others,  moved by none
                 mediator  = moves others,  moved by some
                 sink      = moves none,     moved by some
                 isolated  = moves none,     moved by none

HONEST BOUND (the Phase-2 companion to `learned ≠ assumption-free`): **`recovered topology ≠ discovered
ontology`.** Even a perfectly recovered graph is a graph over *latent variables created by a particular
representation family* — it is a surviving explanation under a declared model class `𝓕`, not a final
description of reality. And the whole recovery assumes a *real* `do()` is available; with an unknown causal
graph and no free intervention operator, topology recovery is the open frontier, not a solved step. The graph
is content-addressed to its factor labeling and its 𝓕 — relabel the factors and you relabel the graph.
"""
from __future__ import annotations

from world import NODES, moves


def response_matrix(world, thresh=0.15):
    """R[i][j] = does do(i) move j? The raw intervention asymmetries."""
    return {i: {j: moves(world, i, j, thresh) for j in NODES if j != i} for i in NODES}


def _moves_any(R, n):
    return any(R[n][o] for o in R[n])


def _moved_by_any(R, n):
    return any(R[o].get(n, False) for o in NODES if o != n)


def role(R, n):
    """Place a node in the partial order from the asymmetries alone."""
    mv, moved = _moves_any(R, n), _moved_by_any(R, n)
    if mv and not moved:
        return "root"
    if mv and moved:
        return "mediator"
    if moved and not mv:
        return "sink"
    return "isolated"


def roles(world, thresh=0.15):
    R = response_matrix(world, thresh)
    return {n: role(R, n) for n in NODES}, R


def relevant_to(R, target):
    """Tier 2, restated: which nodes' interventions move the target (the outcome)? Both a root and a mediator
    pass this — which is why Tier 2 alone cannot separate them."""
    return {n: R[n].get(target, False) for n in NODES if n != target}


def topology_report(world, outcome="y", thresh=0.15):
    rls, R = roles(world, thresh)
    return {"response": R, "roles": rls, "relevant_to_outcome": relevant_to(R, outcome),
            "note": "recovered topology != discovered ontology — a graph over declared latent factors under 𝓕, "
                    "assuming a real do(); not a final description of reality"}
