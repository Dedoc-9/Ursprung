# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/view_layer.py — the VIEW boundary: read-only interpretation of committed state.

This is the renderer's first real surface. It implements the middle of the pipeline:

    authoritative world state → [deterministic snapshot] → [visual interpretation] → (GPU execution) → frame

The load-bearing invariant is **no write-back** (the same rule AetherPulse/snapshot.py enforces): the VIEW
receives a deep-copied, read-only snapshot of the committed L1 state and produces ONLY observables
(screen-space sprites, particles, UI). Nothing it does can reach the next truth-tick. Two clients may
produce different L2/L3 observables from the SAME L1 and that is benign OBSERVABLE drift, never a fault.

VIEW math is allowed to use floats — presentation is not committed state, so float reassociation here can
never fork a world hash. (That is precisely why the boundary exists: `fidelity ⟂ integrity`.)

CLASSIFICATION: VIEW (mutates_core=False). If anything here ever needed to influence the trajectory, it
would be the wrong layer for the job.

HONEST BOUND: a VisualFrame is an *interpretation*. It carries the l1_hash it was derived from so a verifier
can bind frame→state, but the projection (camera, scale) is a lossy model of the world, not the world.
"""
from __future__ import annotations

import math

from ._workbench import SNAP, SCALE


# --- the deterministic snapshot (CORE→VIEW handoff) -------------------------------------------------

def snapshot(world):
    """A read-only, deep-copied L1 view for the render path (double-buffer frame_N). Because it is a copy,
    anything the VIEW does to it cannot reach frame_N+1. Carries l1_hash (the consensus gate)."""
    return SNAP.l1_snapshot(world)


# --- camera (a VIEW convenience, not an invariant) --------------------------------------------------

class Camera:
    """A minimal perspective camera. Floats are fine here — VIEW only. Looks down -Z by default."""

    def __init__(self, eye=(0.0, 20.0, 80.0), focal=60.0, screen=(320, 200)):
        self.eye = eye
        self.focal = focal
        self.screen_w, self.screen_h = screen

    def project(self, x, y, z):
        """World display-units → (screen_x, screen_y, depth). Returns floats; depth is camera-space Z.
        Behind-camera points get depth<=0 and are flagged by the caller."""
        ex, ey, ez = self.eye
        cx, cy, cz = (x - ex), (y - ey), (z - ez)
        depth = -cz  # distance in front of the camera (it looks toward -Z)
        if depth <= 1e-6:
            return None, None, depth
        sx = self.screen_w / 2.0 + (cx * self.focal) / depth
        sy = self.screen_h / 2.0 - (cy * self.focal) / depth
        return sx, sy, depth


# --- visual interpretation --------------------------------------------------------------------------

class VisualFrame:
    """Pure observables. `l1_hash` binds this frame to the committed state it was derived from."""
    __slots__ = ("tick", "l1_hash", "sprites", "particles", "screen_shake")

    def __init__(self, tick, l1_hash, sprites, particles, screen_shake):
        self.tick = tick
        self.l1_hash = l1_hash
        self.sprites = sprites              # list of {id, x, y, depth, size, visible}
        self.particles = particles          # L2 observable (may differ between clients)
        self.screen_shake = screen_shake    # L2 observable

    def __repr__(self):
        return "<VisualFrame tick=%d l1=%s sprites=%d>" % (self.tick, self.l1_hash[:8], len(self.sprites))


def interpret(snap, camera=None, client_seed=0):
    """Project a read-only snapshot into a VisualFrame. Reads `snap`; returns observables ONLY. Never
    returns or mutates a world. This function is the entire VIEW contract in one place."""
    cam = camera or Camera()
    sprites = []
    for b in snap["bodies"]:
        # fixed-point integer coords → float display units (lossy, VIEW-only)
        x, y, z = (b["pos"][0] / SCALE, b["pos"][1] / SCALE, b["pos"][2] / SCALE)
        hx = b["half"][0] / SCALE
        sx, sy, depth = cam.project(x, y, z)
        visible = sx is not None
        size = (hx * cam.focal / depth) if (visible and depth > 0) else 0.0
        sprites.append({
            "id": b["id"],
            "x": sx, "y": sy, "depth": depth, "size": size,
            "visible": bool(visible),
        })
    # L2 observables derived deterministically from (tick, client_seed) by the workbench seam.
    obs = SNAP.render_observe(snap, client_seed)
    return VisualFrame(
        tick=snap["tick"], l1_hash=snap["l1_hash"],
        sprites=sprites, particles=obs["particles"], screen_shake=obs["screen_shake"],
    )


def frames_agree_on_truth(frame_a, frame_b):
    """Consensus check: the committed l1_hash (the gate) must match. L2/L3 observables may differ freely."""
    return frame_a.l1_hash == frame_b.l1_hash


# --- adversarial / fault helper (for the verification harness) --------------------------------------

def perturb(frame):
    """Return a DELIBERATELY corrupted copy of a VisualFrame — scrambled sprite positions, bogus particle
    count, a flipped l1_hash. Used by the harness to prove that mauling the VIEW changes nothing in CORE.
    This mutates only the returned copy; the world is never in scope here (that is the point)."""
    bad_sprites = [dict(s, x=(s["x"] or 0) + 9999.0, y=(s["y"] or 0) - 9999.0, size=0.0) for s in frame.sprites]
    flipped = ("0" if frame.l1_hash[:1] != "0" else "1") + frame.l1_hash[1:]
    return VisualFrame(
        tick=frame.tick, l1_hash=flipped,
        sprites=bad_sprites, particles=frame.particles + 123456, screen_shake=999,
    )