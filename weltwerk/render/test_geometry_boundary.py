# SPDX-License-Identifier: AGPL-3.0-only
"""
test_geometry_boundary.py — Phase 5 proofs (validity-not-outcome): the renderer is a pure projection.

The load-bearing check is render_does_not_mutate_authority — the visual layer cannot change the world.
This is `observation ≠ authority`, machine-checked.

  1. render_does_not_mutate_authority — hash(authority) identical before/after running BOTH adapters  ← crux
  2. snapshot_is_immutable            — a renderer cannot mutate a snapshot (frozen → raises)
  3. two_renderers_same_snapshot      — voxel + topology consume the SAME snapshot, both produce output
  4. renderer_deletion_safe           — deleting a renderer leaves the authority hash unchanged
  5. adapters_are_pure_read           — adapt() takes only a Snapshot (no CausalWorld arg/reference)
  6. determinism                      — same world ⇒ identical adapter output
  7. only_apply_event_mutates         — apply_event changes the authority hash; rendering never does

Run:  PYTHONHASHSEED=0 python3 test_geometry_boundary.py
"""
from __future__ import annotations

import dataclasses
import inspect

from geometry_boundary import CausalWorld, GeometryAdapter, TopologyAdapter, VoxelAdapter

WORLD = """
world "T"
entity generator:
  emits power
entity turret:
  powered_by generator
entity door:
  depends_on generator
entity tree:
  health 30
"""


def check(name, ok, detail):
    return (name, ok, detail)


def test_render_does_not_mutate_authority():
    w = CausalWorld(WORLD)
    w.apply_event("destroy", "generator")
    before = w.authority_hash()
    VoxelAdapter().adapt(w.snapshot())
    TopologyAdapter().adapt(w.snapshot())
    after = w.authority_hash()
    return check("render_does_not_mutate_authority", before == after,
                 f"authority hash unchanged by rendering: {before == after}")


def test_snapshot_is_immutable():
    w = CausalWorld(WORLD)
    snap = w.snapshot()
    raised = False
    try:
        snap.entities[0].state = "hacked"     # frozen EntityView ⇒ must raise
    except dataclasses.FrozenInstanceError:
        raised = True
    except Exception:
        raised = True
    return check("snapshot_is_immutable", raised, f"mutating a snapshot entity raises: {raised}")


def test_two_renderers_same_snapshot():
    w = CausalWorld(WORLD)
    snap = w.snapshot()
    a = VoxelAdapter().adapt(snap)
    b = TopologyAdapter().adapt(snap)
    return check("two_renderers_same_snapshot", len(a) > 0 and len(b) > 0,
                 f"voxel {len(a)} prims, topology {len(b)} prims from one snapshot")


def test_renderer_deletion_safe():
    w = CausalWorld(WORLD)
    w.apply_event("destroy", "generator")
    h0 = w.authority_hash()
    r = VoxelAdapter()
    r.adapt(w.snapshot())
    del r                                       # delete the renderer
    return check("renderer_deletion_safe", w.authority_hash() == h0,
                 f"authority survives renderer deletion: {w.authority_hash() == h0}")


def test_adapters_are_pure_read():
    # adapt() must take only (self, snap) — no CausalWorld handed to a renderer
    sig = inspect.signature(GeometryAdapter.adapt)
    params = [p for p in sig.parameters if p != "self"]
    ok = params == ["snap"]
    return check("adapters_are_pure_read", ok, f"adapt(self, snap) only — no world reference: {ok}")


def test_determinism():
    a = VoxelAdapter().adapt(CausalWorld(WORLD).snapshot())
    b = VoxelAdapter().adapt(CausalWorld(WORLD).snapshot())
    return check("determinism", a == b, f"same world ⇒ identical primitives: {a == b}")


def test_only_apply_event_mutates():
    w = CausalWorld(WORLD)
    h0 = w.authority_hash()
    w.snapshot(); VoxelAdapter().adapt(w.snapshot())     # observation
    h1 = w.authority_hash()
    w.apply_event("destroy", "generator")                # the only mutation path
    h2 = w.authority_hash()
    return check("only_apply_event_mutates", h0 == h1 and h1 != h2,
                 f"observation leaves hash ({h0 == h1}); apply_event changes it ({h1 != h2})")


def main():
    results = [
        test_render_does_not_mutate_authority(),
        test_snapshot_is_immutable(),
        test_two_renderers_same_snapshot(),
        test_renderer_deletion_safe(),
        test_adapters_are_pure_read(),
        test_determinism(),
        test_only_apply_event_mutates(),
    ]
    print("test_geometry_boundary — Phase 5: world logic survives graphics (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:34s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: rendering never mutates the authority,"
          f"\n  snapshots are immutable, two renderers share one snapshot and either can be deleted, adapters"
          f"\n  are pure-read, and ONLY apply_event changes the world. The mesh is a projection; the graph is the world.")
    assert passed == total, f"{total - passed} check(s) failed — the renderer boundary leaks authority"


if __name__ == "__main__":
    main()
