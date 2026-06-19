# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/tcff.py — the Temporal Causal Fidelity Field (proactive fidelity), and its PCJ bench.

PFAL asked "where is my approximation most likely to fail, and how expensive is that failure?" TCFF adds the
missing axis — **when**:

    F(x,t) = U × C × P × S × τ

    U uncertainty        prediction instability
    C consequence        causal downstream effect      (input, from causal_runtime)
    P persistence        how long the artifact lasts
    S sensitivity        human/perceptual sensitivity
    τ temporal proximity HOW SOON the error becomes observable   ← the new axis

τ is what turns the renderer from REACTIVE to PROACTIVE. A tiny object 200 m away has low current value, but
if it is about to enter view, a motion vector predicts a collision, a LOD transition is imminent, lighting is
about to reveal it, or temporal reconstruction will amplify the mistake — then τ spikes, and the renderer
PREPARES before the frame demands it:

    reactive : artifact appears → detect → fix → player sees the hitch
    proactive: predict instability → allocate ahead of time → the artifact never becomes visible

Concrete proactive gains (each an allocation response, never a world change):
  · TAA           more samples where HISTORY will break, not everywhere (history confidence is low → preload).
  · LOD           pre-warm + blend the representation BEFORE the threshold crossing → the pop becomes an
                  invisible deterministic convention instead of a visible event.
  · input→photon  prioritize what an imminent player action will touch (weapon view, crosshair region,
                  collision surfaces, moving targets) — not because they are "more real", but because the
                  cost of a prediction error there is higher.

THE METRIC: Perceptual Continuity per Joule.

    PCJ = avoided perceptual discontinuities / compute budget

A 240 fps renderer with visible temporal ghosts can be worse than a 120 fps one that maintains causal
continuity — so the natural metric is continuity per unit compute, not raw FPS.

CLASSIFICATION: ALLOCATOR (mutates_core=False). It chooses WHERE and WHEN to spend effort; it never moves
committed state and decides no truth. τ, C, and the events are INPUTS / predictions, never truths.

HONEST BOUND: constructed-world bench; a measurable hypothesis that EXPIRES on real GPU silicon (real PCJ
needs measured discontinuities + measured joules). `observation → allocation`, never `observation → truth`.
The renderer never discovers truth; it manages WHERE the arbitrary boundary fails, so it fails where failure
is least perceptually destructive. integrity ≠ truth.
"""
from __future__ import annotations

import random

from .temporal_membrane import _hamilton

DEFAULT_HORIZON = 8   # frames of look-ahead over which τ ramps up


def temporal_proximity(frames_to_event, horizon=DEFAULT_HORIZON):
    """τ: sooner ⇒ larger. An event in 1 frame → τ=horizon; at the horizon → τ=1; beyond → 1 (clamped).
    A frames_to_event of None (no predicted event) → τ=1 (no urgency)."""
    if frames_to_event is None:
        return 1
    return max(1, horizon - int(frames_to_event) + 1)


def tcff_score(region, horizon=DEFAULT_HORIZON, scale=100):
    """F = U × C × P × S × τ as an integer weight."""
    u = int(round(region.get("uncertainty", 0.0) * scale))
    c = int(region.get("consequence", 1))
    p = int(region.get("persistence", 1))
    s = int(region.get("sensitivity", 1))
    tau = temporal_proximity(region.get("frames_to_event"), horizon)
    return max(0, u) * max(1, c) * max(1, p) * max(1, s) * max(1, tau)


class TemporalCausalFidelityField:
    """Proactive allocator: distributes a fixed budget by F = U×C×P×S×τ, so imminent high-cost failures are
    pre-warmed before they become visible. A `floor` keeps hard-gated regions funded."""

    def __init__(self, horizon=DEFAULT_HORIZON):
        self.horizon = horizon

    def weights(self, regions):
        return {rid: tcff_score(r, self.horizon) for rid, r in regions.items()}

    def allocate(self, regions, total_budget, floor=0):
        ids = sorted(regions)
        if not ids:
            return {}
        rest = max(0, total_budget - floor * len(ids))
        split = _hamilton(self.weights(regions), rest)
        return {rid: floor + split.get(rid, 0) for rid in ids}


# --- PCJ bench: reactive vs PFAL vs TCFF, equal budget ----------------------------------------------

def make_scene(n=60, seed=1, fire_window=3):
    """Regions with a FUTURE event at `frames_to_event`. A region causes a perceptual discontinuity if it is
    under-funded when its event FIRES (within `fire_window`). Some imminent, high-cost events are off-screen
    NOW (visible_now=False) — exactly what a reactive, visibility-driven budget cannot pre-warm."""
    rng = random.Random(seed)
    scene = []
    for i in range(n):
        frames_to_event = rng.randint(1, 12)
        imminent = frames_to_event <= fire_window
        offscreen = rng.random() < 0.5
        # build the killer case: imminent + off-screen + high consequence/sensitivity
        killer = imminent and offscreen
        scene.append({
            "id": "r%02d" % i,
            "frames_to_event": frames_to_event,
            "visible_now": (not offscreen),
            "uncertainty": rng.uniform(1.0, 4.0) if killer else rng.uniform(0.0, 2.0),
            "consequence": rng.randint(5, 10) if killer else rng.randint(1, 5),
            "persistence": rng.randint(2, 5),
            "sensitivity": rng.randint(2, 6),
            "needed": 8 + rng.randint(0, 16),
        })
    return scene


def w_reactive(r):
    """What a visibility-driven renderer does: fund what is already on screen (cannot pre-warm off-screen)."""
    return 100 if r["visible_now"] else 1


def w_pfal(r):
    """U×C×P×S — failure cost, but blind to WHEN (no τ)."""
    u = int(round(r.get("uncertainty", 0.0) * 100))
    return max(0, u) * r["consequence"] * r["persistence"] * r["sensitivity"]


def w_tcff(r):
    return tcff_score(r)


def _drifted(seed):
    rng = random.Random(seed * 13 + 5)
    return lambda r: rng.randint(1, 1000)


def perceptual_continuity(scene, alloc, fire_window=3):
    """Avoided perceptual discontinuities: for events that FIRE within the window, a region pre-warmed to
    `needed` avoids a discontinuity whose perceptual cost is sensitivity × consequence. Funding events that
    do NOT fire this window yields no avoided discontinuity (wasted) — which is where τ-blind policies lose."""
    avoided = 0.0
    for r in scene:
        if r["frames_to_event"] <= fire_window:
            got = alloc.get(r["id"], 0)
            if got >= r["needed"]:
                avoided += r["sensitivity"] * r["consequence"]
    return avoided


def run(seed=1, budget=600, fire_window=3):
    scene = make_scene(seed=seed, fire_window=fire_window)
    policies = {
        "reactive (visibility)": w_reactive,
        "pfal (U×C×P×S)": w_pfal,
        "tcff (U×C×P×S×τ)": w_tcff,
        "drifted (control)": _drifted(seed),
    }
    out = {}
    for name, wf in policies.items():
        alloc = _hamilton({r["id"]: wf(r) for r in scene}, budget)
        cont = perceptual_continuity(scene, alloc, fire_window)
        out[name] = {"continuity": cont, "pcj": cont / budget}
    return out


def demo(seed=1, budget=600, fire_window=3):
    res = run(seed=seed, budget=budget, fire_window=fire_window)
    floor = res["reactive (visibility)"]["pcj"]
    print("TCFF — Perceptual Continuity per Joule bench (constructed world, seed=%d, budget=%d)" % (seed, budget))
    print("  PCJ = avoided perceptual discontinuities / compute budget (higher better)\n")
    order = ["reactive (visibility)", "pfal (U×C×P×S)", "tcff (U×C×P×S×τ)", "drifted (control)"]
    for name in order:
        v = res[name]
        tag = ""
        if name.startswith("tcff"):
            tag = "  ← pre-warms imminent high-cost failures (τ)"
        if name.startswith("drifted"):
            tag = "  ← control: should not win" + (" (PASS)" if v["pcj"] <= res["tcff (U×C×P×S×τ)"]["pcj"] else " (FAIL)")
        print("  %-24s continuity=%6.0f  PCJ=%.3f%s" % (name, v["continuity"], v["pcj"], tag))
    t = res["tcff (U×C×P×S×τ)"]["pcj"]
    p = res["pfal (U×C×P×S)"]["pcj"]
    print("\n  TCFF vs PFAL: PCJ %.3f vs %.3f  (τ adds proactive pre-warming of imminent events)" % (t, p))
    print("  Honest bound: constructed world; a hypothesis; expires_if measured on real GPU silicon.")
    print("  observation → allocation, never observation → truth.")
    return res


def register():
    from .registry import REGISTRY, ALLOCATOR, LayerViolation
    try:
        REGISTRY.register("tcff", ALLOCATOR, mutates_core=False,
                          note="Temporal Causal Fidelity Field — proactive F=U×C×P×S×τ; PCJ metric; "
                               "observation→allocation, never →truth")
    except LayerViolation:
        pass
