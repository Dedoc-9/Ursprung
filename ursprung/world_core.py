# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/world_core.py — the CORE layer: the authoritative world trajectory (the Weltlinie).

This is the ONLY layer permitted to move committed state. It is a thin, honest wrapper over the sealed
AetherPulse reference kernel (deterministic 3-D fixed-point rigid bodies): Ursprung does not re-implement
the deterministic tick — that semantics is already defined and conformance-pinned in the workbench. We
consume it read-only and expose exactly the operations the renderer pipeline needs:

    world state → deterministic tick → canonical hash → replay → comparison

Determinism is by construction (integer/fixed-point state, id-sorted evolution, SHA-256 over canonical
bytes). We add nothing to that; we only surface it.

CLASSIFICATION: CORE (mutates_core=True). Nothing downstream of this module may write back into a world.

HONEST BOUND: a state hash proves the sim ran exactly so on this machine and replays bit-for-bit — never
that it models real physics (integrity ≠ truth). Fixed-point is a *trade* (provability over continuous
precision), not strictly "better" than float.
"""
from __future__ import annotations

from ._workbench import K


# --- world construction -----------------------------------------------------------------------------

def demo_world():
    """The smallest non-trivial authoritative scene: two boxes that will fall and collide under gravity.
    Coordinates are ints (whole units) or (num, den) rationals — floats are refused by the kernel on
    purpose, because they are exactly what determinism forbids."""
    bodies = [
        K.body("box_a", pos=(0, 30, 0), vel=(1, 0, 0), half=(2, 2, 2)),
        K.body("box_b", pos=(6, 8, 0), vel=(0, 0, 0), half=(2, 2, 2)),
        K.body("box_c", pos=(-8, 18, 0), vel=(2, 0, 0), half=(2, 2, 2)),
    ]
    return K.make_world(bodies, bounds=((-50, 0, -50), (50, 60, 50)), gravity=10, dt_ms=8)


def world_from(bodies, bounds, gravity=10, dt_ms=8):
    """Escape hatch for custom scenes / tests. Same contract as the kernel."""
    return K.make_world(bodies, bounds=bounds, gravity=gravity, dt_ms=dt_ms)


def body(bid, pos, vel, half, restitution=(8, 10)):
    """Re-export the kernel body constructor so callers need not import the workbench directly."""
    return K.body(bid, pos, vel, half, restitution=restitution)


# --- the authoritative operations -------------------------------------------------------------------

def tick(world):
    """Advance the Weltlinie by one truth-tick. Pure: returns a NEW world; the input is not mutated.
    This is the only sanctioned way to move committed state."""
    return K.step(world)


def state_hash(world):
    """Content address of the committed world state. Bit-stable across machines/languages."""
    return K.state_hash(world)


def run(world, ticks):
    """Run `ticks` truth-ticks; return (final_world, per_tick_hashes). hashes[0] is the initial state."""
    return K.run(world, ticks)


def trajectory(world, ticks):
    """Just the per-tick hash list (the committed history fingerprint) — convenient for comparison."""
    _, hashes = K.run(world, ticks)
    return hashes


# --- comparison (a CORE diagnostic, not a gate) -----------------------------------------------------

def first_divergence(hashes_a, hashes_b):
    """Index of the first differing tick between two trajectories, or None if identical (up to the
    shorter length). The exact divergence locator — same idea as a tessera shard's divergence point."""
    n = min(len(hashes_a), len(hashes_b))
    for i in range(n):
        if hashes_a[i] != hashes_b[i]:
            return i
    if len(hashes_a) != len(hashes_b):
        return n  # diverged by length
    return None


def trajectories_identical(hashes_a, hashes_b):
    return first_divergence(hashes_a, hashes_b) is None and len(hashes_a) == len(hashes_b)