# SPDX-License-Identifier: AGPL-3.0-only
"""
loop.py — the smallest executable Ursprung world loop, end to end.

    world state → deterministic tick → snapshot → visual interpretation → frame
    (+ the milestone verification: prove the renderer is observer-only)
    (+ a live read of the OBSERVER → ALLOCATOR chain: prediction · membrane · PFAL · TCFF/PCJ)

Run:  PYTHONHASHSEED=0 python3 loop.py
"""
import os
import sys

# allow `python3 loop.py` from the repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursprung import world_core as core
from ursprung import view_layer as view
from ursprung import verify
from ursprung import render_record as rr
from ursprung import prediction as pred
from ursprung import temporal_membrane as tm
from ursprung import pfal_bench as pf
from ursprung import tcff
from ursprung.registry import VIEW


def show_loop(ticks=8):
    print("--- minimal world loop (CORE tick → VIEW interpret) ---")
    w = core.demo_world()
    cam = view.Camera()
    for _ in range(ticks):
        w = core.tick(w)                       # CORE: advance the Weltlinie
        snap = view.snapshot(w)                # CORE→VIEW: read-only handoff
        frame = view.interpret(snap, cam)      # VIEW: interpret to observables
        visible = sum(1 for s in frame.sprites if s["visible"])
        print("  tick %2d  l1=%s  sprites_visible=%d  particles=%d"
              % (frame.tick, frame.l1_hash[:12], visible, frame.particles))
    print()


def show_observer_allocator_chain():
    """A live read of the chain: VIEW frames → prediction (surprise) → Temporal Reality Budget. This is
    OBSERVER → ALLOCATOR; it reads the committed world read-only and allocates compute, never truth."""
    print("--- OBSERVER → ALLOCATOR chain (prediction → membrane budget) ---")
    w = core.demo_world()
    frames = []
    for _ in range(8):
        frames.append(view.interpret(view.snapshot(w)))
        w = core.tick(w)
    # consequence is an INPUT (here: a flat declared weight); a real engine reads it from causal_runtime
    consequence = {s["id"]: 5 for s in frames[-1].sprites}
    rep = tm.membrane(frames[-3], frames[-2], frames[-1], consequence=consequence, total_budget=300)
    for sid, b in sorted(rep.budget.items()):
        u = rep.regions.get(sid, {}).get("uncertainty", 0.0)
        print("  region %-7s budget=%3d  (uncertainty G+=%.2f × consequence)" % (sid, b, u))
    for g in rep.ghosts:
        print("  ghost: %s" % g.detail)
    print("  law: %s" % rep.law)
    print()


def show_render_record():
    """Treat the current VIEW interpretation as a 'feature' and emit its render Verification Record —
    the same machinery future features (Nanite-like LOD, AI upscale, ray tracing, foveated) will use."""
    def feature(snap, cfg):
        return view.interpret(snap, view.Camera(), client_seed=cfg.get("seed", 0))
    rec = rr.evaluate_feature(
        "view_interpret_baseline", VIEW, feature, config={"seed": 0}, ticks=60,
        measured={"hardware": "reference-python", "resolution": "320x200", "scene": "demo_world(3 bodies)"})
    print()
    print(rec.to_markdown())


def main():
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("NOTE: run with PYTHONHASHSEED=0 to honor the workbench reproducible-invocation discipline.\n")
    show_loop()
    res = verify.run_milestone_1(verbose=True)
    print()
    show_observer_allocator_chain()
    pf.demo(seed=1, budget=600)
    print()
    tcff.demo(seed=1, budget=600)
    print()
    show_render_record()
    return 0 if res.passed() else 1


if __name__ == "__main__":
    raise SystemExit(main())
