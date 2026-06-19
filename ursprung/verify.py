# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/verify.py — the verification harness. The milestone is proven HERE, not asserted by labels.

Milestone 1 is not "a pretty frame." It is: **"I can replay the same world and prove the renderer is only
an observer."** Three empirical checks, each baseline→change→compare:

  1. REPLAY IDENTITY        run the same world N times → all committed trajectories byte-identical.
  2. VIEW-PERTURBATION      run CORE alone (baseline); run CORE again while the VIEW layer is active and
     INVARIANCE            DELIBERATELY corrupted every tick → CORE trajectory must equal the baseline.
                           This is the cardinal invariant: VIEW is downstream-only, no write-back.
  3. ORDERING INVARIANCE    shuffle the input body order → same trajectory (evolution is id-sorted).

This mirrors the workbench's own cardinal proof (attaching the observer leaves the committed hash
trajectory byte-identical). A green result means: no regression in the monitored invariants + the renderer
demonstrably cannot move the Weltlinie. It does NOT mean the renderer is correct or pretty — integrity ≠
truth.

CLASSIFICATION: OBSERVER (mutates_core=False).
"""
from __future__ import annotations

from . import world_core as core
from . import view_layer as view
from . import ghost_report as gr
from .registry import REGISTRY, CORE, VIEW, OBSERVER


def register_milestone_systems():
    """Declare the layering so it is inspectable at runtime. Idempotent-ish: ignores re-registration."""
    from .registry import LayerViolation
    decls = [
        ("world_core", CORE, True, "authoritative trajectory (wraps AetherPulse kernel)"),
        ("view_layer", VIEW, False, "read-only snapshot interpretation; no write-back"),
        ("ghost_report", OBSERVER, False, "ghost capture & classification"),
        ("verify", OBSERVER, False, "the milestone verification harness"),
    ]
    for name, layer, mut, note in decls:
        try:
            REGISTRY.register(name, layer, mutates_core=mut, note=note)
        except LayerViolation:
            pass  # already registered in this process
    return REGISTRY


class VerificationResult:
    def __init__(self):
        self.checks = {}        # name -> bool
        self.detail = {}        # name -> human string
        self.report = gr.GhostReport()

    def record(self, name, ok, detail):
        self.checks[name] = bool(ok)
        self.detail[name] = detail

    def passed(self):
        return all(self.checks.values()) if self.checks else False

    def __repr__(self):
        return "<VerificationResult %s>" % (" ".join(
            "%s=%s" % (k, "OK" if v else "FAIL") for k, v in self.checks.items()))


# --- the three checks -------------------------------------------------------------------------------

def replay_identity(world_factory, ticks=60, runs=4):
    base = core.trajectory(world_factory(), ticks)
    for _ in range(runs - 1):
        h = core.trajectory(world_factory(), ticks)
        if not core.trajectories_identical(base, h):
            idx = core.first_divergence(base, h)
            return False, "diverged at tick %s across identical runs" % idx, base
    return True, "%d runs × %d ticks all byte-identical (final=%s)" % (runs, ticks, base[-1][:12]), base


def view_perturbation_invariance(world_factory, ticks=60, client_seed=7):
    """Run CORE alone → baseline hashes. Run CORE again, and EACH tick: snapshot → interpret → perturb the
    VIEW. Assert the CORE trajectory is unchanged. If the renderer could touch state, this would diverge."""
    baseline = core.trajectory(world_factory(), ticks)

    w = world_factory()
    observed = [core.state_hash(w)]
    cam = view.Camera()
    for _ in range(ticks):
        # --- VIEW activity happens BEFORE the next tick, on a read-only snapshot of current state ---
        snap = view.snapshot(w)
        frame = view.interpret(snap, cam, client_seed=client_seed)
        corrupted = view.perturb(frame)             # actively maul the visual output
        _ = (corrupted.sprites, corrupted.particles)  # use it, so nothing is optimized away
        # --- only CORE advances the Weltlinie ---
        w = core.tick(w)
        observed.append(core.state_hash(w))

    if not core.trajectories_identical(baseline, observed):
        idx = core.first_divergence(baseline, observed)
        return False, "VIEW activity changed CORE trajectory at tick %s — write-back leak!" % idx, observed
    return True, "CORE trajectory byte-identical with VIEW active+corrupted every tick (renderer is observer-only)", observed


def ordering_invariance(bodies, bounds, ticks=40):
    ghost = gr.detect_order_dependence(bodies, bounds, ticks=ticks)
    if ghost is not None:
        return False, ghost.detail, None
    return True, "input-order permutation yields identical trajectory (id-sorted evolution)", None


# --- the milestone runner ---------------------------------------------------------------------------

def run_milestone_1(verbose=True):
    register_milestone_systems()
    res = VerificationResult()

    def factory():
        return core.demo_world()

    ok, detail, base = replay_identity(factory)
    res.record("replay_identity", ok, detail)

    ok, detail, _ = view_perturbation_invariance(factory)
    res.record("view_perturbation_invariance", ok, detail)

    # ordering check needs raw bodies + bounds (reuse the demo scene's definition)
    demo = core.demo_world()
    bodies = [core.body(b["id"],
                        tuple(int(round(c / _SCALE())) for c in b["pos"]),
                        tuple(int(round(c / _SCALE())) for c in b["vel"]),
                        tuple(int(round(c / _SCALE())) for c in b["half"]))
              for b in demo["bodies"]]
    bounds = ((int(round(demo["min"][0] / _SCALE())), int(round(demo["min"][1] / _SCALE())),
               int(round(demo["min"][2] / _SCALE()))),
              (int(round(demo["max"][0] / _SCALE())), int(round(demo["max"][1] / _SCALE())),
               int(round(demo["max"][2] / _SCALE()))))
    ok, detail, _ = ordering_invariance(bodies, bounds)
    res.record("ordering_invariance", ok, detail)

    # --- ghost sweep (attention signals; never gates) ---
    w = factory()
    res.report.add(gr.detect_float_leak(w))
    res.report.add(gr.detect_hidden_nondeterminism(factory))
    res.report.add(gr.detect_snapshot_data_loss(view.snapshot(w)))
    res.report.add(gr.detect_view_reconstruction_loss(view.interpret(view.snapshot(w))))
    res.report.add(gr.measure_tick_timing(factory))  # informational temporal ghost

    if verbose:
        _print_result(res)
    return res


def _SCALE():
    from ._workbench import SCALE
    return SCALE


def _print_result(res):
    print("=" * 78)
    print("URSPRUNG — Milestone 1: the renderer is an observer of an authoritative world")
    print("=" * 78)
    for name, ok in res.checks.items():
        print("  [%s] %-28s %s" % ("PASS" if ok else "FAIL", name, res.detail[name]))
    print("-" * 78)
    print("  Ghost sweep (attention signals — never gate the trajectory):")
    if res.report.clean():
        print("    (none fired)")
    for g in res.report.ghosts:
        print("    · %-16s %-20s %s" % (g.category, g.origin, g.detail))
    print("-" * 78)
    print("  MILESTONE 1:", "ACHIEVED — replay-identical + renderer cannot move the Weltlinie"
          if res.passed() else "NOT met — see FAIL lines above")
    print("=" * 78)