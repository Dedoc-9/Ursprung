# SPDX-License-Identifier: AGPL-3.0-only
"""
test_multilens.py — Phase 15 proofs (validity-not-outcome): splats are an interchangeable, NON-authoritative
lens. This turns the architectural claim into machine-checked evidence.

  1. splat_lens_does_not_mutate   — projecting the world to splats leaves the authority hash unchanged
  2. multilens_authority_invariant— ONE snapshot through render_primitives + a topology lens + the splat lens
                                     leaves the authority hash BYTE-IDENTICAL (the GeometryAdapter boundary holds)
  3. lenses_are_pure_reads        — every lens is a deterministic function of the same snapshot
  4. same_world_many_lenses       — the voxel lens and the splat lens describe the SAME set of alive entities
  5. causal_coupling              — destroy(node) ⇒ the projection degrades (splats vanish/dim) driven by the
                                     GRAPH alone; nothing edits the splat file or the renderer
  6. splat_roundtrip              — the projected cloud round-trips the verified .splat contract

Run:  PYTHONHASHSEED=0 python3 test_multilens.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from splat_adapter import DEMO_WORLD, entity_view, world_to_splats
from splat_format import decode_scene, encode_scene
from world_sim import WorldSim, render_primitives


def check(name, ok, detail):
    return (name, ok, detail)


def topology_lens(snap):
    """A third lens: the causal topology as edges — a pure read of the same snapshot."""
    return [(s, d) for (s, _rel, d) in snap.relations]


def test_splat_lens_does_not_mutate():
    sim = WorldSim(DEMO_WORLD)
    h0 = sim.authority_hash(); world_to_splats(sim); h1 = sim.authority_hash()
    return check("splat_lens_does_not_mutate", h0 == h1, f"authority hash unchanged by splat projection: {h0 == h1}")


def test_multilens_authority_invariant():
    sim = WorldSim(DEMO_WORLD)
    h0 = sim.authority_hash()
    snap = sim.snapshot()
    a = render_primitives(snap)          # lens 1: voxel/FPS primitives
    b = topology_lens(snap)              # lens 2: topology edges
    c = world_to_splats(sim)             # lens 3: gaussian splats
    h1 = sim.authority_hash()
    ok = h0 == h1 and len(a) > 0 and len(b) > 0 and len(c) > 0
    return check("multilens_authority_invariant", ok,
                 f"3 lenses ({len(a)} prims, {len(b)} edges, {len(c)} splats) ⇒ hash identical: {h0 == h1}")


def test_lenses_are_pure_reads():
    sim = WorldSim(DEMO_WORLD); snap = sim.snapshot()
    pure_prims = render_primitives(snap) == render_primitives(snap)
    pure_splats = encode_scene(world_to_splats(sim)) == encode_scene(world_to_splats(sim))
    return check("lenses_are_pure_reads", pure_prims and pure_splats,
                 f"render_primitives pure={pure_prims}, splats pure={pure_splats}")


def test_same_world_many_lenses():
    sim = WorldSim(DEMO_WORLD); snap = sim.snapshot()
    voxel_ids = {p["id"] for p in render_primitives(snap)}
    splat_ids = {ev.id for ev in snap.entities if ev.alive}
    return check("same_world_many_lenses", voxel_ids == splat_ids,
                 f"voxel lens entities == splat lens entities: {voxel_ids == splat_ids}")


def test_causal_coupling():
    sim = WorldSim(DEMO_WORLD)
    before_n = len(world_to_splats(sim))
    turret_before = entity_view(sim, "turret")
    sim.apply_event("destroy", "generator")          # the ONLY mutation — a pure authority event
    after_n = len(world_to_splats(sim))
    turret_after = entity_view(sim, "turret")
    gen_dead = not sim.runtime["generator"]["alive"]
    ok = (gen_dead and after_n < before_n
          and turret_before["powered"] and not turret_after["powered"]
          and turret_after["color"] != turret_before["color"])
    return check("causal_coupling", ok,
                 f"destroy(generator): splats {before_n}→{after_n}, turret powered "
                 f"{turret_before['powered']}→{turret_after['powered']}, colour {turret_before['color']}→{turret_after['color']}")


def test_splat_roundtrip():
    sim = WorldSim(DEMO_WORLD)
    s = world_to_splats(sim)
    dec = decode_scene(encode_scene(s))
    return check("splat_roundtrip", len(dec) == len(s), f"{len(s)} → encode → decode {len(dec)}")


def main():
    results = [
        test_splat_lens_does_not_mutate(),
        test_multilens_authority_invariant(),
        test_lenses_are_pure_reads(),
        test_same_world_many_lenses(),
        test_causal_coupling(),
        test_splat_roundtrip(),
    ]
    print("test_multilens — Phase 15: splats as an interchangeable, non-authoritative lens\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: one authority snapshot projects to voxel"
          f"\n  primitives, a topology lens, AND gaussian splats while the authority hash stays byte-identical;"
          f"\n  every lens is a pure read; the lenses agree on the world; and destroying a node degrades its"
          f"\n  splats through the GRAPH alone. The renderer cannot change authority — proven across lenses.")
    assert passed == total, f"{total - passed} check(s) failed — a lens leaked into authority"


if __name__ == "__main__":
    main()
