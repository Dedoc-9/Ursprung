<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk — Phase 9: production-shaped FPS vertical slice

The purpose of this phase is one claim: **a causal world can host actual gameplay** without the gameplay
becoming the authority. The renderer is still a projection; the `.wrk` world + Python authority remain the
source of truth. Delete the FPS file and the world still exists.

```
world.wrk → WorldSpec → CausalGraph → lint/health/validation → RuntimeWorld → events → replication
                                                                     │
                                              world_ai.py (LOS · A* · FSM · squad)  ← AUTHORITY
                                                                     │
                                       weltwerk_fps_prototype.html (projection, mirrors the above)
```

## Files

| File | Role | Grade |
|---|---|---|
| `sim/world_ai.py` | combat-AI **authority**: Grid, line-of-sight, A*, table-driven state machine, perceive, squad | MEASURED |
| `sim/test_world_ai.py` | 10 proofs incl. the `destroy(generator)` causal cascade | MEASURED (run for 10/10) |
| `fps_demo/weltwerk_fps_prototype.html` | the playable FPS **projection** (mirrors `world_ai` + `world_sim`) | IMPLEMENTED |

## Run

```powershell
cd "weltwerk\sim"; $env:PYTHONHASHSEED="0"; python test_world_ai.py; python world_ai.py
```

Then open `weltwerk\fps_demo\weltwerk_fps_prototype.html` in a browser. Click to play. Controls: **WASD**
move · **SHIFT** sprint · **CTRL** crouch · **SPACE** jump · mouse look · **LEFT-CLICK** fire · **1** rifle ·
**2** shotgun · **R** reload · **F1** gameplay / **F2** causal / **F3** AI / **F4** replication.

The headline: walk to the gold **generator** and shoot it. Its turrets lose power and stop firing — routed
through `destroy(generator)` over the causal graph, not a script. Open **F2** to see the affected set.

---

## MEASURED (verified by tests / runs)

- **Line of sight blocks on walls; no omniscience.** `line_of_sight` returns false when a blocked cell lies
  between bot and player; `visible` also enforces view range. A bot that cannot see the player cannot fire.
  (`test_world_ai`: `los_blocked`, `los_clear`, `no_omniscience_range`.)
- **A* paths around obstacles.** 4-connected grid A*, deterministic; never routes through a blocked cell;
  reaches the goal when one exists. (`astar_around_wall`.)
- **Explicit state machine.** IDLE/PATROL/INVESTIGATE/CHASE/ATTACK/SEARCH with one small handler per state;
  transitions are total and pure. (`patrol_to_attack`, `attack_to_search`, `chase_to_search`.)
- **Squad awareness.** A spotter alerts only same-team allies within radius; an alerted ally with no LOS
  escalates to INVESTIGATE. (`squad_alert`.)
- **Causal death.** `destroy(generator)` propagates through `world_sim` to disable `turret/door/light`
  by reachability — not scripted. (`destroy_generator_cascade`.)
- **Determinism.** Identical inputs ⇒ identical paths and identical bot steps. (`determinism`.)

## IMPLEMENTED (in the projection; behavior exercised on open, not in an automated suite)

- **FPS feel:** acceleration + friction movement, sprint, crouch (lower eye + speed), jump with clean
  stand-on-top collision; smooth pointer-lock look; head bob; muzzle flashes; damage screen flash.
- **Two weapons** sharing one hitscan model: **rifle** (fast, tight, 30-round) and **shotgun** (8 pellets,
  wide spread, slow, 6-round); reload with reserve ammo.
- **Bots** that mirror `world_ai`: per-tick FSM at a fixed cadence, grid LOS to the player, A* movement around
  walls/cover, **fire only in ATTACK with LOS + range** (no wallhacks), **squad alerts** on sighting,
  **simple cover** (when hurt, move to the nearest cell that breaks LOS), and respawn from spawn points.
- **Turrets as causal entities:** they fire only while `powered` (alive ∧ not disabled); cutting the
  generator disables them through the same event path. Door/light also go dark in the cascade.
- **HUD:** health bar, ammo/reserve, weapon, live bot + powered-turret counts, objective, damage flash.
- **Debug modes (F1–F4):** gameplay; causal (potential/actual/affected of the last event); AI (per-bot
  state, LOS clear/blocked, target, and the A* path drawn in 3D); replication (event, affected set,
  naive-vs-causal byte estimate, labelled *measured structure, not network performance*).

## VISION (not built; would extend, not replace)

- Richer tactical cover (true peek-fire timing, suppression, flanking), navmesh instead of a uniform grid.
- Bots registered as first-class `.wrk` entities so bot death is a full causal event with downstream
  consequences (currently bot death emits an event-shaped record; only world entities cascade).
- Weapon variety, hit locations/armor, sound-based perception, difficulty tuning.
- Live-edit the world while playing (Phase: `world_diff` + re-derive) and ask runtime "why" questions.

## NOT CLAIMED

- **No MMO, no networking, no latency claim, no UE5, no procedural generation.** The replication panel
  reports *structural* bytes/op-counts, never wall-clock or network performance.
- The AI is a **deterministic grid-level substrate**, not state-of-the-art game AI; pathing is 4-connected
  A*, perception is grid LOS. Behavior is honest, not optimal.
- The renderer holds **no authority**: it never mutates world state except through the mirrored event/AI
  functions, and the Python authority is the source of truth. `observation ≠ authority`.

## Architecture note (the separation this phase preserves)

Gameplay logic that must be trusted lives in `world_ai.py` (authority) and `world_sim.py` (events). The HTML
**mirrors** those functions in JS (clearly labelled `MIRROR`) for the live loop; it does not invent
gameplay truth. The same `transition` table, the same LOS rule, the same A*, the same destroy-cascade.
If the two ever disagree, the Python authority is correct and the mirror is the bug.
