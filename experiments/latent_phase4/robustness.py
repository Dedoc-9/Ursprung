# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase4/robustness.py — which recovered structure survives a change of encoder family.

The latent analogue of `robust explanation = ⋂ over 𝓕`. A factor is robustly recoverable if it is recoverable
from EVERY encoder family; an intervention relation is robust if it holds across them. min over families is
the intersection.
"""
from __future__ import annotations

from intervene import recover_r2


def robust_recoverability(target, latents):
    """⋂ over encoder families: the worst-case recoverability of a factor across the model class."""
    return min(recover_r2(target, Z) for (Z, _Xh) in latents.values())


def per_family_recoverability(target, latents):
    return {name: round(recover_r2(target, Z), 3) for name, (Z, _Xh) in latents.items()}
