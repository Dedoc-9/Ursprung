# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase4/intervene.py — recoverability (gauge-invariant) + intervention on the outcome.

`recover_r2` is the gauge-invariant statistic from Phase 1: R² of predicting a true factor from the latent's
column space — invariant under any reparameterization of the latent, so it measures *how recoverable* a factor
is, never *which dimension* carries it. `outcome_sensitivity` is the ground-truth do() on a structural node:
does intervening on it move the outcome? (Tier 1 — the intervention gate, over learned factors.)
"""
from __future__ import annotations

import numpy as np

from world import intervene, values


def recover_r2(target, Z):
    Zb = np.c_[Z, np.ones(len(Z))]
    w, *_ = np.linalg.lstsq(Zb, target, rcond=None)
    pred = Zb @ w
    ss = float(((target - pred) ** 2).sum())
    tot = float(((target - target.mean()) ** 2).sum())
    return max(0.0, 1.0 - ss / tot)


def reconstruction_r2(X, X_hat):
    return max(0.0, 1.0 - float(((X - X_hat) ** 2).sum()) / float(((X - X.mean(0)) ** 2).sum()))


def outcome_sensitivity(world, node, outcome="y", seed=7):
    """do(node): does the OUTCOME move? Normalized to the outcome's scale. (Necessity, by intervention.)"""
    base = world[outcome]
    after = intervene(world, node, seed=seed)[outcome]
    return float(min(1.0, np.std(after - base) / (np.std(base) + 1e-9)))


def gauge_invariant(target, Z, n_rot=8):
    """Recoverability must not move under latent rotations; per-dim correlation, by contrast, does."""
    base = recover_r2(target, Z)
    k = Z.shape[1]
    for s in range(n_rot):
        q, _ = np.linalg.qr(np.random.default_rng(s).standard_normal((k, k)))
        if abs(recover_r2(target, Z @ q.T) - base) > 1e-6:
            return False
    return True
