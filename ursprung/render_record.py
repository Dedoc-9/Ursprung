# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/render_record.py — the render-specific Verification Record, emitted (not hand-filled).

The point of this module: turn every future renderer feature — Nanite-like triangle allocation, AI
upscaling, ray tracing, foveated rendering — into an **experiment** rather than an architectural invasion.
A feature is admitted only if it can produce a record proving it is observer-only and its numbers were
measured, not asserted.

It implements the project's feature lifecycle as code:

    observe → hypothesize → implement → verify → record

`evaluate_feature()` runs the candidate feature alongside the CORE trajectory and emits a
`RenderVerificationRecord` carrying real content hashes (input snapshot, renderer config, output artifact),
the CORE-trajectory-changed verdict (the cardinal invariant), the measured frame budget (an OBSERVABLE,
never a gate), and any ghosts. The record is the thing a reviewer reads — boundaries as data, not prose.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures and reports; it changes nothing.

HONEST BOUND: a record proves the feature was observer-only on the tested world and that its numbers were
measured under the stated conditions — never that the feature is universally better. A benchmark measures
the benchmark's world (`integrity ≠ truth`).
"""
from __future__ import annotations

import hashlib
import json
import time

from . import world_core as core
from . import view_layer as view
from . import ghost_report as gr
from .registry import REGISTRY, OBSERVER, CORE, VIEW, ALLOCATOR


# --- canonical hashing (12-significant-digit float floor, mirroring the workbench's discipline) -----

def _canonicalize(obj):
    """Recursively coerce to a canonical, hashable form. Floats are formatted to 12 significant digits so
    presentation-side float reassociation cannot fork the record hash (AGENTS.md §1). This is for the
    OBSERVER record only — committed CORE state is integer and never passes through here."""
    if isinstance(obj, float):
        return format(obj, ".12g")
    if isinstance(obj, dict):
        return {str(k): _canonicalize(obj[k]) for k in sorted(obj, key=str)}
    if isinstance(obj, (list, tuple)):
        return [_canonicalize(x) for x in obj]
    return obj


def canon_hash(obj):
    """Content address of an observable artifact / config. SHA-256 over canonical, sorted JSON."""
    payload = json.dumps(_canonicalize(obj), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _artifact_observable(artifact):
    """Extract the comparable observable content from whatever a feature returns. Handles a VIEW
    VisualFrame and a plain dict (e.g. an ALLOCATOR's {region: budget}). The l1_hash is intentionally
    EXCLUDED — we hash the presentation, not the truth it was derived from."""
    if isinstance(artifact, view.VisualFrame):
        return {"sprites": [{k: s[k] for k in ("id", "x", "y", "depth", "size", "visible")}
                            for s in artifact.sprites],
                "particles": artifact.particles, "screen_shake": artifact.screen_shake}
    return artifact  # dict / list / scalar — canon_hash handles it


# --- the record -------------------------------------------------------------------------------------

class RenderVerificationRecord:
    """A self-contained, reviewable record for one renderer feature experiment."""

    def __init__(self, feature, layer, input_snapshot_hash, renderer_config_hash, output_artifact_hash,
                 core_trajectory_changed, view_divergence, measured, known_ghosts, effect="", non_effect=""):
        self.feature = feature
        self.layer = layer
        self.input_snapshot_hash = input_snapshot_hash
        self.renderer_config_hash = renderer_config_hash
        self.output_artifact_hash = output_artifact_hash
        self.core_trajectory_changed = core_trajectory_changed
        self.view_divergence = view_divergence          # "expected" | "unexpected"
        self.measured = measured                          # {hardware, resolution, scene, frame_budget_ms}
        self.known_ghosts = known_ghosts                  # list[Ghost]
        self.effect = effect
        self.non_effect = non_effect

    def admissible(self):
        """A non-CORE feature is admissible only if it did NOT change the committed trajectory. A CORE
        feature is expected to (that is its job) — but only CORE may. This is the cardinal invariant as a
        boolean on the record."""
        if self.layer == CORE:
            return True
        return (not self.core_trajectory_changed) and self.view_divergence == "expected"

    def to_markdown(self):
        g = "\n".join("  - %s / %s: %s" % (gh.category, gh.origin, gh.detail) for gh in self.known_ghosts) \
            or "  (none fired)"
        m = self.measured or {}
        return (
            "## Render Verification Record — %s — %s\n\n"
            "Feature:               %s\n"
            "Layer:                 %s\n"
            "Effect:                %s\n"
            "Non-effect (invariant):%s\n"
            "Input snapshot hash:   %s\n"
            "Renderer config hash:  %s\n"
            "Output artifact hash:  %s\n\n"
            "CORE trajectory changed:  %s\n"
            "VIEW divergence:          %s\n\n"
            "Measured:\n"
            "  hardware:     %s\n"
            "  resolution:   %s\n"
            "  scene:        %s\n"
            "  frame budget: %s ms (observable, never a gate)\n\n"
            "Known ghosts:\n%s\n\n"
            "Verdict: %s\n"
            "Scope: integrity ≠ truth — measured on the tested world only; not a universal-superiority claim."
            % (self.feature, _today(), self.feature, self.layer, self.effect or "—",
               self.non_effect or "committed CORE trajectory unchanged",
               self.input_snapshot_hash[:16], self.renderer_config_hash[:16], self.output_artifact_hash[:16],
               "YES" if self.core_trajectory_changed else "NO", self.view_divergence,
               m.get("hardware", "—"), m.get("resolution", "—"), m.get("scene", "—"),
               m.get("frame_budget_ms", "—"), g,
               "ADMISSIBLE" if self.admissible() else "REJECTED — see CORE/VIEW lines"))

    def __repr__(self):
        return "<RenderVerificationRecord %s [%s] admissible=%s>" % (
            self.feature, self.layer, self.admissible())


def _today():
    return time.strftime("%Y-%m-%d")


# --- the experiment harness -------------------------------------------------------------------------

def evaluate_feature(feature, layer, render_fn, config=None, world_factory=None, ticks=60, measured=None):
    """Run a candidate renderer feature as an experiment and emit a RenderVerificationRecord.

    feature      : human name ("nanite_like_lod", "ai_upscale", "ray_tracing", "foveated").
    layer        : CORE / VIEW / ALLOCATOR / OBSERVER (registry vocabulary).
    render_fn    : callable(snapshot, config) -> observable artifact (VisualFrame, allocation dict, ...).
                   MUST be pure observation: it may read the snapshot, never the world.
    config       : the renderer config dict (hashed into the record).
    world_factory: builds the authoritative world (defaults to the demo scene).
    measured     : caller-supplied {hardware, resolution, scene} — frame_budget_ms is filled by the harness.

    The harness proves observer-only by comparing the CORE trajectory with the feature active vs absent.
    """
    world_factory = world_factory or core.demo_world
    config = {} if config is None else config

    # baseline: CORE trajectory with the feature ABSENT
    baseline = core.trajectory(world_factory(), ticks)

    # active: run the feature every tick on a read-only snapshot; only CORE advances the Weltlinie
    w = world_factory()
    observed = [core.state_hash(w)]
    rep_snap = rep_artifact = None
    budget = []
    for i in range(ticks):
        snap = view.snapshot(w)
        t0 = time.perf_counter()
        artifact = render_fn(snap, config)
        budget.append(time.perf_counter() - t0)
        if i == ticks // 2:
            rep_snap, rep_artifact = snap, artifact
        w = core.tick(w)
        observed.append(core.state_hash(w))

    core_changed = not core.trajectories_identical(baseline, observed)
    divergence = "unexpected" if (core_changed and layer != CORE) else "expected"

    meas = dict(measured or {})
    if budget:
        meas["frame_budget_ms"] = round(sum(budget) / len(budget) * 1e3, 4)

    ghosts = []
    if rep_artifact is not None and isinstance(rep_artifact, view.VisualFrame):
        g = gr.detect_view_reconstruction_loss(rep_artifact)
        if g is not None:
            ghosts.append(g)

    return RenderVerificationRecord(
        feature=feature, layer=layer,
        input_snapshot_hash=(rep_snap or view.snapshot(world_factory()))["l1_hash"],
        renderer_config_hash=canon_hash(config),
        output_artifact_hash=canon_hash(_artifact_observable(rep_artifact)) if rep_artifact is not None else canon_hash(None),
        core_trajectory_changed=core_changed,
        view_divergence=divergence,
        measured=meas,
        known_ghosts=ghosts,
    )


def register():
    from .registry import LayerViolation
    try:
        REGISTRY.register("render_record", OBSERVER, mutates_core=False,
                          note="emits the render-specific Verification Record (experiments, not invasions)")
    except LayerViolation:
        pass
