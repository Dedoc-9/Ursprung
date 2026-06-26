# SPDX-License-Identifier: AGPL-3.0-only
"""
splat_adapter.py — Phase 15: the inversion made concrete. Gaussian splats as a GeometryAdapter LENS over a
causal authority — a representation, never the authority.

Most splat systems treat the cloud AS the scene. Weltwerk inverts that:

    world.wrk → CausalGraph → WorldSim (runtime AUTHORITY) → splat_adapter → Gaussian splats

The splats are disposable. They are recomputed from the authority's snapshot; they never define it. Destroy
a node in the authority and its splats degrade — because the projection reflects the graph, not because
anyone edited the splat file or the renderer. This module is a PURE READ: it calls snapshot() / controller()
/ powered() and returns gaussians; it never calls apply_event. `observation ≠ authority`, extended to splats.

What this proves (with test_multilens): the SAME authority snapshot can be projected to voxel/FPS primitives,
a topology lens, AND splats, leaving the authority hash byte-identical — i.e. the GeometryAdapter boundary
does real work and the world's identity is independent of how it is viewed.

OUT OF SCOPE (honest): the *reverse* direction — `scan → splats → entity extraction → authority graph` —
hides a real perception/segmentation research problem (`perception ≠ authority`). This module is the
authority→splats half only.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from splat_format import Splat, encode_scene   # noqa: E402
from world_sim import WorldSim                  # noqa: E402

# faction palette assigned by sorted faction order (deterministic)
_PALETTE = [(60, 120, 255), (255, 90, 70), (90, 210, 140), (220, 180, 60)]
_CONTESTED = (230, 120, 40)
_NEUTRAL = (120, 128, 140)


def entity_view(sim: WorldSim, eid: str) -> dict:
    """The per-entity PROJECTION DECISION — a pure read of the authority. The splat cloud is built from this;
    so is the test. controller() colours it; powered() sets its brightness; dead entities are omitted."""
    r = sim.runtime[eid]
    ctrl = sim.controller(eid)
    if ctrl == "contested":
        rgb = _CONTESTED
    elif ctrl == "neutral":
        rgb = _NEUTRAL
    elif ctrl in sim.factions:
        rgb = _PALETTE[sim.factions.index(ctrl) % len(_PALETTE)]
    else:
        rgb = _PALETTE[0]
    powered = sim.powered(eid)
    if not powered:                              # disabled / unpowered ⇒ dim (degraded projection)
        rgb = tuple(int(c * 0.30) for c in rgb)
    return {"id": eid, "alive": r["alive"], "powered": powered, "controller": ctrl,
            "color": rgb, "opacity": 230 if powered else 90}


def world_to_splats(sim: WorldSim, per_entity: int = 150, spread: float = 0.7, seed: int = 0):
    """Project the world to a gaussian cloud. ALIVE entities become a small cluster; DESTROYED entities
    vanish (their splats disappear); DISABLED entities dim. Deterministic. PURE — never mutates the authority."""
    rng = random.Random(seed)
    snap = sim.snapshot()                        # frozen, read-only view of the authority
    out = []
    for ev in snap.entities:
        if not ev.alive:
            continue                             # destroyed ⇒ no splats (the visible consequence of a kill)
        v = entity_view(sim, ev.id)
        n = per_entity if v["powered"] else per_entity // 3
        px, py, pz = ev.pos
        for _ in range(n):
            jx, jy, jz = (rng.random() * 2 - 1) * spread, (rng.random() * 2 - 1) * spread, (rng.random() * 2 - 1) * spread
            out.append(Splat(pos=(px + jx, py + jy, pz + jz), scale=(0.06, 0.06, 0.06),
                             color=(v["color"][0], v["color"][1], v["color"][2], v["opacity"])))
    return out


def world_to_splat_bytes(sim: WorldSim, **kw) -> bytes:
    """The world as a loadable .splat file (the verified contract). Open it in weltwerk_splat_editor.html."""
    return encode_scene(world_to_splats(sim, **kw))


DEMO_WORLD = """
world "Lens"
entity faction_blue:
  controls generator
entity generator:
  position -4 1 0
  powers turret
  powers light
entity turret:
  position 0 1 0
  health 100
entity light:
  position 4 1 0
  health 100
"""


def main():
    print("splat_adapter.py — Phase 15: WorldSim → Gaussian splats (a non-authoritative lens)\n")
    sim = WorldSim(DEMO_WORLD)
    h0 = sim.authority_hash()
    before = world_to_splats(sim)
    h1 = sim.authority_hash()
    print(f"  projecting to splats did NOT mutate authority: {h0 == h1}")
    print(f"  alive world → {len(before)} splats; turret view: {entity_view(sim, 'turret')['color']} powered={sim.powered('turret')}")
    sim.apply_event("destroy", "generator")      # authority event — the ONLY way the world changes
    after = world_to_splats(sim)
    tv = entity_view(sim, "turret")
    print(f"\n  after destroy(generator) — a pure authority event:")
    print(f"    splats {len(before)} → {len(after)}  (generator's splats vanished)")
    print(f"    turret now powered={tv['powered']}  colour dimmed to {tv['color']}  (disabled by cascade)")
    print(f"    nothing edited the splats or the renderer — the projection reflects the graph.")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "world.splat")
    with open(out, "wb") as fh:
        fh.write(encode_scene(after))
    print(f"\n  wrote {out} — the world AS splats; load it in weltwerk_splat_editor.html")
    print("  splats are a disposable lens; the .wrk graph + WorldSim remain the authority.")


if __name__ == "__main__":
    main()
