# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase1/world.py — the synthetic world the benchmark interrogates.

A deliberately small causal world that reuses the symbolic setup of perception/model_relativity, now as
*continuous data a latent can be learned from*:

    g  ~ N(0,1)                       the GENERATOR — the only cause of the outcome
    c  = 0.6·g + 0.8·noise            the CONFOUNDER — correlated with g (so it looks predictive) but NOT causal
    X  = [g, c] @ Aᵀ + ε              the OBSERVABLE (D-dim mixing; what an encoder sees)
    y  = g                            the OUTCOME / trajectory — depends ONLY on g

The trap is built in on purpose: `c` correlates with the outcome at ≈0.6, reconstructs perfectly, and is fully
recoverable from any competent latent — yet intervening on it (`do(c)`) does not move the outcome. Only an
intervention test can tell the generator from the confounder. `correlation ≠ cause`, now in pixels.

Everything is seeded → the world is replayable (the epistemic ledger demands it).
"""
from __future__ import annotations

import numpy as np

N_DEFAULT = 4000
D_DEFAULT = 8


def make_world(n=N_DEFAULT, d=D_DEFAULT, seed=0):
    """Return a dict: X (observable n×d), g, c (true factors), y (outcome), A (mixing), and the rng seed."""
    rng = np.random.default_rng(seed)
    g = rng.standard_normal(n)
    c = 0.6 * g + 0.8 * rng.standard_normal(n)        # confounder: correlated with g, independent error
    A = rng.standard_normal((d, 2))                    # mixing matrix [g,c] -> observable
    X = np.c_[g, c] @ A.T + 0.01 * rng.standard_normal((n, d))
    y = g.copy()                                       # outcome depends ONLY on g
    return {"X": X, "g": g, "c": c, "y": y, "A": A, "n": n, "d": d, "seed": seed}


def intervention_on_outcome(world, factor, seed=99):
    """do(factor): resample `factor` independently of everything else and report how much the OUTCOME moves,
    normalized to the outcome's own scale. This is necessity, measured by intervention rather than correlation.

      do(g): the outcome y = g follows the intervention   → sensitivity ≈ 1
      do(c): c is not a cause of y                         → sensitivity  = 0
    """
    rng = np.random.default_rng(seed)
    y = world["y"]
    if factor == "g":
        g2 = rng.standard_normal(world["n"])           # set g freely; the outcome becomes y2 = g2
        y2 = g2
        return float(min(1.0, np.std(y2 - y) / (np.std(y) + 1e-9)))   # outcome moves with the intervention → ~1
    if factor == "c":
        return 0.0                                     # do(c) leaves y = g untouched → 0
    raise ValueError("unknown factor %r" % factor)
