<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk — Phase 12: Times Square (believable FPS over a causal world)

Phase 11 proved a causal world can host gameplay. Phase 12 proves it can host a **visually convincing**
game — without moving any authority into the renderer. The city's lights, screens, turrets, and territory
all derive from `worlds/times_square.wrk` → `world_sim` / `world_ai` / `world_edit`. The renderer mirrors
that state every frame and owns none of it. `observation ≠ authority`; delete the HTML and the world remains.

## Files

| File | Role |
|---|---|
| `worlds/times_square.wrk` | the city as a **causal graph** (blue power grid, red transit grid, shared data_center→central_square) |
| `sim/test_times_square.py` | 8 tests proving the scenario's territory / cascade / flip behavior |
| `fps_demo/weltwerk_times_square.html` | the believable night-city projection (mirrors the authority) |

(Authority modules `world_ai.py`, `world_sim.py`, `world_edit.py` are unchanged from Phase 11 — Phase 12 is
a renderer phase. Total verified tests across Phases 11–12: **46** — 18 AI + 11 sim + 9 edit + 8 Times Square.)

## Run

```powershell
cd "weltwerk\sim"; $env:PYTHONHASHSEED="0"; python test_times_square.py
```

Open `weltwerk\fps_demo\weltwerk_times_square.html`. Click to deploy. Controls: WASD · SHIFT sprint · CTRL
crouch (SHIFT+CTRL = slide) · SPACE jump · **1/2/3** rifle/assault/shotgun · R reload · LMB fire (hold the
assault) · **F1–F4** debug · **TAB** inspector · **F8** edit the world live.

**The demo:** fight soldiers in the plaza → shoot the blue **power station** (north-west). The whole blue
grid darkens (media tower, billboards, surveillance, turret), smoke + sparks rise, and the contested
**central square flips to red** — through `destroy → graph → affected → runtime → view`, never a script
(F2 shows the affected set). Press **TAB**, click `central_square`, read *why it's red now*. Press **F8**,
re-route power, **Apply**, and watch the city re-derive without reloading the map.

## MEASURED (verified by `test_times_square.py`, 8/8, + the 38 Phase-11 tests)

- The **city is the graph**: territory derives from causal reach (blue/red grids; data_center + central_square
  contested). (`loads_and_factions`, `initial_territory`)
- **Infrastructure cascade**: destroying the power_station disables its whole media/surveillance grid. (`power_station_cascade`)
- **Territory flips** blue-contested → red when blue's path dies. (`territory_flips`, `blue_loses_power`)
- **Renderer is authority-invariant**: building geometry from a snapshot never changes the authority hash. (`renderer_invariant`)
- **Inspector explanations are deterministic** and come from runtime authority. (`inspector_determinism`)
- **Determinism** of the whole event. (`determinism`)
- Live-edit (graph/control/AI updates, territory flips, generator cascade, invalid-edit rejection) is covered
  by the Phase-11 `test_world_edit` / `test_world_sim` / `test_world_ai` suites the projection mirrors.

## IMPLEMENTED (the projection — exercised on open, not auto-tested)

- **Believable night Times Square:** generated skyline of lit-window skyscrapers (canvas emissive maps),
  neon billboards (animated canvas textures), streets + sidewalks + crosswalks, jersey barriers, a subway
  entrance, a construction zone, alley gaps, fog, shadow-mapped moonlight, PBR-ish `MeshStandardMaterial`,
  vignette. No cube terrain, no floating boxes.
- **Procedural soldiers** (not cubes/capsules): head+helmet+torso+limbs+rifle, walk/run gait, aim pose,
  head-tracking, and a **pose that reflects authority state** — ATTACK raises and points the weapon,
  SEARCH sweeps the head, PATROL/CHASE differ by gait speed.
- **FPS viewmodel:** arms + gun with bob, sway, and recoil kick.
- **Combat feel:** muzzle flash, tracers, impact sparks, blood hits, shell ejection, weapon recoil, camera
  shake, hit markers, damage flash + directional cue. Authority still owns damage; these only visualize it.
- **Causal destruction:** each frame, every entity's emissive = `world.powered(id)`; a destroyed entity emits
  smoke + sparks and its billboards go black — driven by the graph, never `if(dead)` in the renderer.
- **Visual territory:** the central square's ground-glow + holographic banner are coloured by
  `world.controller()` (blue/red/orange-contested/grey-neutral), recomputed live from authority.
- **F8 live editor** (edit relations → Apply → re-derive graph/power/territory, player state preserved) and
  **TAB inspector** (controller / why / depends / dependents / blast, from runtime authority).
- **Debug F1–F4:** gameplay / causal (potential·actual·affected) / AI (state + LOS) / replication
  (naive-vs-causal bytes, labelled *measured structure, not network performance*).

## VISION (not built; would extend, not replace)

- Photoreal/PBR **textured** assets, normal maps, real reflections/SSR, volumetrics, post-process bloom —
  here approximated with emissive + additive sprites + fog + shadow maps ("surprisingly believable web FPS").
- Asset-based skinned-mesh characters and animations (current soldiers are stylized procedural low-poly).
- A real navmesh (current AI navigation is a uniform grid), destructible building geometry, vehicle traffic.
- Live-editing that **adds brand-new entities** with placed geometry (F8 today re-derives among existing ones).

## NOT CLAIMED

- **No UE5-quality**, no MMO, no networking, no latency, no "unlimited players", no procedural-content claims.
- The replication panel reports **structural** bytes/op-counts only.
- The renderer holds **no authority** — it mutates world state only through the mirrored event/edit functions,
  and the Python authority (the `.wrk` + sim) is the source of truth. If mirror and authority disagree, the
  mirror is the bug.

## The point

A screenshot reads as a modern shooter; the architecture still reads as a compiler. The city of Times Square
is *generated from a causal world definition*, not scripted — and you can stand inside it, break it, watch it
react, ask why, and rewrite it live. *Git + Compiler + Profiler for living worlds*, made visible.
