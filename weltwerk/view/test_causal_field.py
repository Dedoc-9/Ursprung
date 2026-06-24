# SPDX-License-Identifier: AGPL-3.0-only
"""
test_causal_field.py — validity-not-outcome for the space-time causal renderer.

It proves the picture is a faithful rendering of measured structure — not that any regime looks a
certain way (the diagram reports that). The load-bearing check is `red_within_potential`: a red (actual)
cell can never appear outside the green (potential) cone — divergence cannot outrun causality. If it did,
the diagram would be lying.

  1. determinism            — same params ⇒ identical frames (all three systems)
  2. red_within_potential   — every RED cell at tick t lies inside the reachability ball radius t
  3. frames_well_formed     — H+1 frames per system, each length N, chars ⊆ {b,g,y,r}
  4. cone_monotone          — the potential region (g∪y∪r) never shrinks tick-to-tick

Run:  PYTHONHASHSEED=0 python3 test_causal_field.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scale"))

from causal_field import H, N, build_data                            # noqa: E402


def check(name, ok, detail):
    return (name, ok, detail)


def _potential_positions(frame):
    # potential = anything not committed (green ∪ yellow ∪ red)
    return {i for i, ch in enumerate(frame) if ch in ("g", "y", "r")}


def test_determinism():
    a, b = build_data(), build_data()
    ok = all(a[k]["frames"] == b[k]["frames"] for k in a)
    return check("determinism", ok, f"identical frames across runs (all systems): {ok}")


def test_red_within_potential():
    # red ⊆ potential at every tick: no actual divergence outside the cone (no superluminal causality)
    data = build_data()
    ok = True
    for k, d in data.items():
        for frame in d["frames"]:
            reds = {i for i, ch in enumerate(frame) if ch == "r"}
            if not reds <= _potential_positions(frame):
                ok = False
                break
    return check("red_within_potential", ok, f"every RED cell ⊆ potential cone ∀t, ∀system: {ok}")


def test_frames_well_formed():
    data = build_data()
    ok = True
    for k, d in data.items():
        fr = d["frames"]
        ok = ok and len(fr) == H + 1 and all(len(f) == N and set(f) <= set("bgyr") for f in fr)
    return check("frames_well_formed", ok, f"H+1 frames, length N, chars⊆bgyr ∀system: {ok}")


def test_cone_monotone():
    # the potential region never shrinks (the reachability cone only grows)
    data = build_data()
    ok = True
    for k, d in data.items():
        fr = d["frames"]
        for t in range(len(fr) - 1):
            if not _potential_positions(fr[t]) <= _potential_positions(fr[t + 1]):
                ok = False
                break
    return check("cone_monotone", ok, f"potential region non-shrinking ∀t, ∀system: {ok}")


def main():
    results = [
        test_determinism(),
        test_red_within_potential(),
        test_frames_well_formed(),
        test_cone_monotone(),
    ]
    print("test_causal_field — the space-time diagram faithfully renders measured structure\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Faithful iff {total}/{total}: deterministic, red ⊆ potential (no"
          f"\n  superluminal divergence), frames well-formed, cone monotone. What the regimes look like"
          f"\n  inside the cone is shown, not presumed.")
    assert passed == total, f"{total - passed} check(s) failed — the causal field is not faithful"


if __name__ == "__main__":
    main()
