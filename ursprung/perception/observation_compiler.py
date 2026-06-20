# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/observation_compiler.py — lowers committed world state into an observer-specific view.

The toy perception compiler: it materializes exactly the features a `DisclosurePolicy` allows, deriving the
coarse ones (threat / cover) from truth on the way. No pixels required — the "representation" here is a small
dict, which is the point: a renderer is only one backend of this same lowering.

(This is a lookup-driven placeholder for the real privacy-funnel solve of `docs/INFORMATION_INTENT.md` §3.)
"""
from __future__ import annotations

from .toy_task import threat_level, cover_available


def compile_observation(ws, policy):
    """world_state + policy → observer_view (only the allowed features; coarse ones derived from truth)."""
    f = policy.allowed_features
    view = {}
    if "threat_level" in f:
        view["threat_level"] = threat_level(ws)
    if "cover_available" in f:
        view["cover_available"] = cover_available(ws)
    if "enemy_x" in f:
        view["enemy_x"] = ws["enemy_x"]
    if "enemy_y" in f:
        view["enemy_y"] = ws["enemy_y"]
    if "enemy_health" in f:
        view["enemy_health"] = ws["enemy_health"]
    return view


def view_key(view):
    """A hashable canonical form of a view, for the mutual-information leakage measurement."""
    return tuple(sorted(view.items()))
