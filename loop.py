# SPDX-License-Identifier: AGPL-3.0-only
"""
loop.py — the smallest executable Ursprung world loop, end to end.

    world state → deterministic tick → snapshot → visual interpretation → frame
    (+ the milestone verification: prove the renderer is observer-only)

Run:  PYTHONHASHSEED=0 python3 loop.py
"""
import os
import sys

# allow `python3 loop.py` from the repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ursprung import world_core as core
from ursprung import view_layer as view
from ursprung import verify


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


def main():
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("NOTE: run with PYTHONHASHSEED=0 to honor the workbench reproducible-invocation discipline.\n")
    show_loop()
    res = verify.run_milestone_1(verbose=True)
    return 0 if res.passed() else 1


if __name__ == "__main__":
    raise SystemExit(main())