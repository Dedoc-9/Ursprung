# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/toy_task.py — a tiny, deterministic "survive the encounter" task.

The smallest world that exercises the whole thesis: an enemy sits on an 8×8 grid (the *secret* is its exact
cell), and the agent must choose hide / advance / retreat. The crucial property: the OPTIMAL action depends
only on two derived features — threat level (coarse distance) and cover — NOT on the exact position. So a
*compiled* observation of {threat, cover} is sufficient for optimal play while revealing almost nothing about
the exact cell. That gap is the privacy funnel made concrete.
"""
from __future__ import annotations

GRID = 8
THREAT_DIST = 6
ACTIONS = ("hide", "advance", "retreat")


def world_state(ex, ey):
    """A committed encounter. `dist` and `cover` are derived truths; the exact (ex, ey) is the secret."""
    return {
        "enemy_x": ex,
        "enemy_y": ey,
        "enemy_health": 50 + ((ex * 7 + ey * 3) % 50),
        "dist": ex + ey,
        "cover": (ex % 2 == 0),
    }


def encounters():
    """The full, deterministic encounter distribution: one per grid cell (64 equally-likely secrets → 6 bits)."""
    return [world_state(ex, ey) for ex in range(GRID) for ey in range(GRID)]


def threat_level(ws):
    return "high" if ws["dist"] <= THREAT_DIST else "low"


def cover_available(ws):
    return ws["cover"]


def optimal_action(ws):
    """Ground truth: the action that survives — a function of (threat, cover) ONLY, never of exact position."""
    if threat_level(ws) == "high":
        return "hide" if cover_available(ws) else "retreat"
    return "advance"


def survives(action, ws):
    return action == optimal_action(ws)


def secret(ws):
    """What an adversary must not be able to reconstruct: the enemy's exact cell (0..63)."""
    return ws["enemy_x"] * GRID + ws["enemy_y"]


def agent_action(view):
    """A fixed decision rule. It plays optimally if it can see (or derive) threat + cover; otherwise it must
    fall back to a guess. Raw views let it derive threat/cover; compiled views give them directly; a blind view
    leaves it guessing (the most-common action, 'advance')."""
    t = view.get("threat_level")
    c = view.get("cover_available")
    if t is None and "enemy_x" in view and "enemy_y" in view:
        ex, ey = view["enemy_x"], view["enemy_y"]
        t = "high" if ex + ey <= THREAT_DIST else "low"
        c = (ex % 2 == 0)
    if t is not None and c is not None:
        if t == "high":
            return "hide" if c else "retreat"
        return "advance"
    return "advance"
