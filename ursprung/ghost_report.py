# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/ghost_report.py — the OBSERVER: ghost capture & classification.

A *ghost* is any unexplained artifact, divergence, instability, mismatch, or residual. The discipline:
**classify the layer before patching the symptom.** A ghost allocates investigation; it never certifies a
cause and never gates the committed trajectory.

Two orthogonal axes are recorded for every ghost:

  CATEGORY (which layer produced it):  temporal · spatial · numerical · perceptual · causal · pipeline-ordering
  ORIGIN   (what kind of thing it is): measurement · approximation · timing · data_loss · model_limit ·
                                       implementation_error · unclassified

Milestone-1 detectors are intentionally modest — they cover the failure classes that a foundation must not
get wrong (float leaks into committed state, order-dependence, hidden nondeterminism, snapshot data loss,
VIEW reconstruction loss, and wall-clock jitter). Each returns an attention signal, not a verdict.

CLASSIFICATION: OBSERVER (mutates_core=False). It reads trajectories and frames; it changes nothing.

HONEST BOUND: absence of a ghost here is not proof of correctness — these detectors see only what they were
built to see (`salience ≠ truth`, applied to our own instrument). A clean report means "no monitored
residual fired", never "the renderer is right".
"""
from __future__ import annotations

import time

from . import world_core as core

# --- categories & origins (vocabulary, kept as data) ------------------------------------------------

TEMPORAL = "temporal"
SPATIAL = "spatial"
NUMERICAL = "numerical"
PERCEPTUAL = "perceptual"
CAUSAL = "causal"
PIPELINE_ORDERING = "pipeline-ordering"

MEASUREMENT = "measurement"
APPROXIMATION = "approximation"
TIMING = "timing"
DATA_LOSS = "data_loss"
MODEL_LIMIT = "model_limit"
IMPLEMENTATION_ERROR = "implementation_error"
UNCLASSIFIED = "unclassified"


class Ghost:
    __slots__ = ("category", "origin", "detail", "magnitude", "persistent")

    def __init__(self, category, origin, detail, magnitude=None, persistent=False):
        self.category = category
        self.origin = origin
        self.detail = detail
        self.magnitude = magnitude       # optional measured residual; None when categorical
        self.persistent = persistent     # a persistent ghost earns MORE investigation, not a conclusion

    def __repr__(self):
        m = "" if self.magnitude is None else " mag=%s" % (self.magnitude,)
        return "<Ghost %s/%s%s: %s>" % (self.category, self.origin, m, self.detail)


class GhostReport:
    def __init__(self):
        self.ghosts = []

    def add(self, ghost):
        if ghost is not None:
            self.ghosts.append(ghost)
        return ghost

    def by_category(self, category):
        return [g for g in self.ghosts if g.category == category]

    def clean(self):
        """True iff no monitored residual fired. (Not a correctness claim — see honest bound.)"""
        return not self.ghosts

    def __repr__(self):
        return "<GhostReport %d ghost(s)>" % len(self.ghosts)


# --- detectors --------------------------------------------------------------------------------------

def detect_float_leak(world):
    """NUMERICAL / implementation_error: committed coordinates must be integers (fixed-point). A float in
    L1 is the classic determinism leak. The kernel refuses floats at construction, so this should never
    fire — it is a tripwire, not a gate."""
    for b in world["bodies"]:
        for comp in ("pos", "vel", "half"):
            for v in b[comp]:
                if not isinstance(v, int):
                    return Ghost(NUMERICAL, IMPLEMENTATION_ERROR,
                                 "non-integer in committed %s of %s: %r" % (comp, b["id"], v))
    return None


def detect_order_dependence(bodies, bounds, ticks=20):
    """PIPELINE-ORDERING / implementation_error: feeding the same bodies in a different input order must
    yield the same trajectory (the kernel sorts by id). If the hash changes, evolution depends on input
    ordering — a pipeline-ordering ghost."""
    w1 = core.world_from(list(bodies), bounds)
    w2 = core.world_from(list(reversed(bodies)), bounds)
    h1 = core.trajectory(w1, ticks)
    h2 = core.trajectory(w2, ticks)
    idx = core.first_divergence(h1, h2)
    if idx is not None:
        return Ghost(PIPELINE_ORDERING, IMPLEMENTATION_ERROR,
                     "input-order changed trajectory at tick %d" % idx, magnitude=idx)
    return None


def detect_hidden_nondeterminism(world_factory, ticks=30, runs=3):
    """CAUSAL / unclassified: identical inputs run N times must produce identical trajectories. A
    divergence means an undeclared input (clock/RNG/iteration order) escaped the capture seam — a causal
    ghost (something is coupling into the result that the model does not declare)."""
    base = core.trajectory(world_factory(), ticks)
    for _ in range(runs - 1):
        h = core.trajectory(world_factory(), ticks)
        idx = core.first_divergence(base, h)
        if idx is not None:
            return Ghost(CAUSAL, UNCLASSIFIED,
                         "repeat run diverged at tick %d — undeclared nondeterminism" % idx, magnitude=idx)
    return None


def detect_snapshot_data_loss(snap):
    """SPATIAL / data_loss: the L1 snapshot must carry the fields the VIEW needs. A missing field is data
    lost at the CORE→VIEW boundary."""
    needed = ("tick", "bodies", "l1_hash")
    missing = [k for k in needed if k not in snap]
    if missing:
        return Ghost(SPATIAL, DATA_LOSS, "snapshot missing fields: %r" % missing)
    for b in snap["bodies"]:
        if not all(k in b for k in ("id", "pos", "vel", "half")):
            return Ghost(SPATIAL, DATA_LOSS, "snapshot body missing geometry: %r" % b.get("id"))
    return None


def detect_view_reconstruction_loss(frame):
    """PERCEPTUAL / approximation: sprites projected off-screen or behind the camera are detail the player
    cannot see — information the VIEW dropped. This is EXPECTED (it is approximation, not error); we record
    it as an attention signal so a downstream ALLOCATOR can decide whether the loss matters."""
    dropped = sum(1 for s in frame.sprites if not s["visible"])
    if dropped:
        return Ghost(PERCEPTUAL, APPROXIMATION,
                     "%d/%d sprites not presented (off-screen / behind camera)"
                     % (dropped, len(frame.sprites)), magnitude=dropped)
    return None


def measure_tick_timing(world_factory, ticks=50):
    """TEMPORAL / timing: wall-clock cost per tick across a run. This is a CAPTURED OBSERVABLE — it may
    inform an ALLOCATOR's budget, but it must NEVER gate the trajectory (telemetry ≠ control). Returns a
    Ghost only as a carrier for the measured jitter; it is informational by construction."""
    w = world_factory()
    samples = []
    for _ in range(ticks):
        t0 = time.perf_counter()
        w = core.tick(w)
        samples.append(time.perf_counter() - t0)
    if not samples:
        return None
    mean = sum(samples) / len(samples)
    spread = max(samples) - min(samples)
    return Ghost(TEMPORAL, TIMING,
                 "per-tick wall-clock mean=%.2fus spread=%.2fus (observable, never gates physics)"
                 % (mean * 1e6, spread * 1e6), magnitude=spread)