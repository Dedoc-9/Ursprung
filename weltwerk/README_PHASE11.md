<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk — Phase 11: production FPS demonstration of a causal world

The FPS exists to make the **compiler visible**: a living world where consequences flow through the
authority (event → graph → affected → runtime → view), not through renderer scripts. Phase 11 deepens the
combat AI, adds live editing of the running world, and a runtime inspector that answers *why*.

`observation ≠ authority` holds throughout: gameplay logic that must be trusted lives in `world_ai.py`,
`world_sim.py`, and `world_edit.py`; the HTML **mirrors** those (labelled `MIRROR`), and the Python
authority is the tiebreaker. Delete the HTML and the world still exists.

## Files

| File | Role |
|---|---|
| `sim/world_ai.py` | combat-AI authority: 9-state FSM, LOS, A*, **accuracy model, reaction delay, burst, memory, cover, squad** |
| `sim/world_sim.py` | + **armor / damage types** (backward-compatible) and **causal stations** (`station_active` = powered) |
| `sim/world_edit.py` | **live-edit authority**: `apply_edit(old,new,carry)` — edit = NEW authority, validated, diffed, player-state preserved; `explain()` runtime "why" |
| `sim/test_world_ai.py` · `test_world_sim.py` · `test_world_edit.py` | **38 tests** across Phase 11 |
| `fps_demo/weltwerk_fps_prototype.html` | the projection: deeper causal base, AR + slide, **F8 world editor**, **TAB inspector** |

## Run the tests (PowerShell — sandbox mount truncates the imported modules)

```powershell
cd "weltwerk\sim"; $env:PYTHONHASHSEED="0"
python test_world_ai.py        # 18
python test_world_sim.py       # 11
python test_world_edit.py      #  9
python world_ai.py; python world_sim.py; python world_edit.py
```

Then open `weltwerk\fps_demo\weltwerk_fps_prototype.html`. Controls: WASD · SHIFT sprint · CTRL crouch
(SHIFT+CTRL while fast = **slide**) · SPACE jump · **1** rifle / **2** assault / **3** shotgun · R reload ·
LEFT-CLICK fire (hold for the AR) · **F1–F4** debug · **TAB** inspector · **F8** world editor.

The success path: fight the bots → shoot the **generator** (or just the **battery**) → watch the cascade
disable turrets/radar/repair (F2 shows the affected set) → press **TAB**, click `turret_a`, read *why it's
disabled* → press **F8**, add a redundant power path, **Apply**, and see the consequences re-derived live.

---

## MEASURED (verified by the 38 tests)

- **Line of sight & no omniscience** — walls block sight (and therefore fire); range-limited. (`los_*`, `no_omniscience_range`)
- **9-state FSM, explicit & total** — IDLE/PATROL/INVESTIGATE/CHASE/ATTACK/SEARCH/**SUPPRESS/RETREAT/RELOAD**,
  one handler per state. (`patrol_to_attack`, `attack_to_search`, `chase_to_search`, `attack_to_suppress`,
  `low_hp_retreats`, `out_of_ammo_reloads`, `reload_completes`)
- **Accuracy model** — falls with distance / movement / suppression / low HP. (`accuracy_model`)
- **Reaction delay** — deterministic 150–350 ms. (`reaction_delay_range`)
- **Bot memory** — `last_seen` / `time_since_contact` update. (`bot_memory`)
- **Cover** — `find_cover` returns a cell that breaks LOS. (`find_cover_breaks_los`)
- **Squad** — a spotter alerts same-team allies → INVESTIGATE. (`squad_alert`)
- **A\*** — paths around walls, never through them. (`astar_around_wall`)
- **Causal death cascade** — `destroy(generator)` disables turret/door/light by reachability, not script. (`destroy_generator_cascade`)
- **Armor & damage types** — armor reduces effective damage by type only. (`armor_reduces_damage`, `damage_type_specific`)
- **Causal stations** — a repair/healing station is `station_active` iff powered; cutting power disables it. (`station_powered_then_disabled`)
- **Live edit = new authority** — a topology edit re-derives graph/power/factions, reports consequences,
  preserves player state, and **rejects invalid/unparseable edits** (old authority stands). (`edit_updates_graph`,
  `edit_updates_power_path`, `edit_removes_spof`, `edit_updates_factions`, `camera_inventory_preserved`,
  `invalid_edit_rejected`, `parse_error_rejected`, `diff_deterministic`)
- **Runtime "why"** — `explain()` answers controller/neutral/depends/dependents from the **alive graph**. (`explain_runtime`)
- **Determinism** across AI, sim, and diff.

## IMPLEMENTED (in the projection; exercised on open, not auto-tested)

- **FPS feel:** acceleration + friction, sprint, crouch, **slide**, jump, air control (reduced), head bob,
  recoil + bloom, damage flash, muzzle flashes, safe respawn + spawn protection.
- **Weapons:** rifle (semi, recoil), **assault rifle** (auto + bloom), shotgun (pellets) — one hitscan model.
- **Deeper causal base:** `generator → battery → turret_a/turret_b`, `generator → radar → drone`,
  `generator → repair_station/door/light`. Shoot the **battery** to cut only the turrets, or the
  **generator** to cascade the whole network — all through the event system, mirrored from `world_sim`.
- **Healing station:** heals the player only while `world.powered("repair_station")` — power dies, healing stops.
- **F8 World Editor:** edit the `.wrk` relations live; **Apply** rebuilds the causal authority and reports
  added/removed relations + which turrets/radar/station are now powered. Camera/health/ammo preserved.
- **TAB Live Inspector:** click an entity → alive/status/powered, **why** it's powered/disabled, depends-on,
  affects, blast radius — from runtime authority.
- **Debug F1–F4:** gameplay / causal (potential·actual·affected) / AI (state, LOS clear/blocked, A* path in 3D) /
  replication (affected set, naive-vs-causal bytes, labelled *measured structure, not network performance*).

## VISION (not built; would extend, not replace)

- The HTML bot loop mirrors a **subset** of the 9-state FSM (patrol/investigate/chase/attack/search + cover/
  reposition + fire-only-on-LOS); the full SUPPRESS/RETREAT/RELOAD/burst/accuracy machine is the *authority*
  in `world_ai.py` (verified) and is only partially surfaced in the projection. Full visual mirror is VISION.
- Live-editing that **adds brand-new entities** needs live geometry placement; F8 today re-derives the causal
  graph among existing entities (re-powers, re-cascades) but won't spawn meshes for newly-named nodes.
- Bots registered as first-class `.wrk` entities so bot death is a full causal event with downstream effects.
- Navmesh (vs uniform grid), hit locations, sound perception, difficulty tuning, the full Halo-CE feel.

## NOT CLAIMED

- **No MMO, no networking, no latency, no UE5, no "unlimited players", no procedural generation.**
  The replication panel reports *structural* bytes/op-counts only.
- The AI is a deterministic grid-level substrate, not state-of-the-art game AI.
- The renderer holds **no authority** — it mutates world state only through the mirrored event/AI/edit
  functions, and the Python authority is the source of truth. If the mirror and the authority disagree, the
  mirror is the bug.

## Architecture note

Everything that matters routes through authority first. The generator→turret cascade is `destroy → causal
graph → affected → runtime → view`, never `if(generatorDead) turret.disabled=true`. Live edits create a NEW
authority (the runtime resets — the discontinuity is reported, never hidden). The product is *Git + Compiler
+ Profiler for living worlds*; the FPS exists to make that compiler visible.
