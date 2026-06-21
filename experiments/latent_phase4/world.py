# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase4/world.py — synthetic SCM whose factors a learned latent must recover.

Phase 4 asks: does the provenance contract survive contact with a LEARNED representation? So the world is the
same kind used symbolically before — a known SCM with ground-truth interventions — but now the factors are
*learned* from the observable rather than hand-written.

    g ~ N(0,1)              ROOT generator      (the only cause of the outcome)
    m = g + 0.3·noise       MEDIATOR            (carries g)
    c = 0.6·g + 0.8·noise   CONFOUNDER          (correlated with g, NOT causal — the trap)
    X = [g, m, c] @ Aᵀ + ε  OBSERVABLE          (what the encoder learns from)
    y = m                   OUTCOME             (depends on g only through m)

Intervention truth is known (synthetic world) — that is deliberate: Phase 4 learns the REPRESENTATION, not the
intervention. do() without a known graph stays the Phase-3+ frontier. Seeded → replayable.
"""
from __future__ import annotations

import numpy as np

N_DEFAULT, D_DEFAULT = 4000, 10
FACTORS = ("g", "m", "c")          # the latent factors a learned encoder must recover
NODES = ("g", "m", "y", "c")       # nodes of the intervention graph (y is the outcome)


def make_world(n=N_DEFAULT, d=D_DEFAULT, seed=0):
    r = np.random.default_rng(seed)
    g = r.standard_normal(n)
    m = g + 0.3 * r.standard_normal(n)
    c = 0.6 * g + 0.8 * r.standard_normal(n)
    A = r.standard_normal((d, 3))
    X = np.c_[g, m, c] @ A.T + 0.01 * r.standard_normal((n, d))
    y = m.copy()
    return {"X": X, "g": g, "m": m, "c": c, "y": y, "A": A, "n": n, "d": d, "seed": seed}


def values(world):
    """Node values, for the intervention graph."""
    return {"g": world["g"], "m": world["m"], "y": world["y"], "c": world["c"]}


def intervene(world, do_node, seed=1):
    """do(node): resample it, propagate the structural equations downstream. Ground-truth (synthetic world)."""
    r = np.random.default_rng(seed)
    n = world["n"]
    g, m, c = world["g"].copy(), world["m"].copy(), world["c"].copy()
    if do_node == "g":
        g = r.standard_normal(n); m = g + 0.3 * r.standard_normal(n)
    elif do_node == "m":
        m = r.standard_normal(n)
    elif do_node == "y":
        pass
    elif do_node == "c":
        c = r.standard_normal(n)
    else:
        raise ValueError("unknown node %r" % do_node)
    y = m.copy()
    return {"g": g, "m": m, "y": y, "c": c}
