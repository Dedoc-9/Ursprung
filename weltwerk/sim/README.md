<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# weltwerk/sim — the Weltwerk World Prototype (Phase 7)

The smallest world you can **walk inside**, where things happen for reasons you can inspect.

This phase turns the verified stack into a living vertical slice **without** rebuilding the engine. It
reuses the proven pipeline — `authoring/world_format` (parse → causal graph), `authoring/world_design`
(regime), the Phase-5 renderer boundary, the Phase-4 replication model — and adds the layer that makes a
world feel alive: runtime state, an event vocabulary, and graph-derived factions.

```
world.wrk text → WorldSpec → CausalGraph → factions/runtime → causal events → projection (FPS view)
                                   ↑__________ the .wrk text is the authority __________|
```

## Files

| File | What it is | Grade |
|------|------------|-------|
| `world_sim.py` | The simulation **authority**. RuntimeWorld + event vocabulary + graph-derived factions. Mesh-blind. | IMPLEMENTED |
| `test_world_sim.py` | 7 proofs (validity-not-outcome). | MEASURED (run to confirm 7/7) |
| `../fps_demo/weltwerk_world_prototype.html` | The playable FPS slice. Mirrors `world_sim.py` in JS. | IMPLEMENTED (UNTESTED interactively) |

## What the simulation does

**Event vocabulary** — every important thing is an event, and every event returns the honest report:

```
event → causal-graph lookup → affected set → runtime update → (renderer refresh)

  destroy(e)   e dies; everything reachable from it is disabled (downstream cascade)
  damage(e,n)  health -= n; if it hits 0, it dies (then cascades)
  repair(e,n)  health += n (capped); status recovers iff its upstream is alive;
               revives a destroyed entity if its sources are alive
  capture(e,F) F takes ownership of e (explicit override of reach)
  transfer(e,F) move ownership to F

  report = { potential, actual, affected, unchanged }   with  Potential ⊇ Actual
```

`potential` = what the event *could* touch (causal reach). `actual`/`affected` = what it *did* (a state
diff, including derived control flips). `unchanged` = the rest. This is the project's central law made
visible on every single action.

**Factions are just entities.** No new format: a faction is any entity that sources a control relation
(`controls`, `owns`, `claims`, …). Control and power are **derived**, never stored as a second authority:

- `controller(e)` = the faction that reaches `e` in the **currently-alive** causal graph. Reached by two
  factions ⇒ `contested`; by none ⇒ `neutral`. Explicit `capture` overrides reach.
- `faction_power(f)` = count of alive entities `f` controls.

So when you `destroy` the reactor that a faction's power flows through, that faction's territory stops
being reachable and **flips on its own** — the consequence is computed from structure, not scripted. That
is the demo: two factions contest a reactor, a market, and a shared `resource_node`; break the reactor and
watch one side's territory go neutral and its defense grid go dark, then ask the inspector *why*.

## Model boundaries (stated, not hidden — Arbitrary-Boundary Law)

- **"control = causal reach in the alive graph"** is a model construct. A real game layers ownership and
  visibility rules on top; this is the smallest honest definition that makes capture/territory-flip observable.
- **"faction power = alive entities controlled"** is a *structural count*, not game balance or HP.
  `measured-reach ≠ game-balance`.
- The discrete event model's divergence is **graph propagation**, not continuous dynamics.
  `event ≠ measured-dynamics`.
- The replication panel reports **bytes / entities-touched / reconstruction op-count** — deterministic
  structure, **not** wall-clock latency. `MEASURED STRUCTURE ≠ NETWORK PERFORMANCE`.

## The boundary still holds

`observation ≠ authority`, carried forward from Phase 5 and machine-checked here:
`render_does_not_mutate_authority` confirms building the geometry leaves the authority hash unchanged, and
`snapshot()` is frozen. **Delete the HTML and the world still exists** — it lives in `world.wrk` + `world_sim.py`.
`render_primitives()` is the pure seam an engine (UE5 or anything) would implement *without* moving the
authority out of the text.

## Verify (PowerShell — sandbox mount truncates these files; PowerShell reads the real ones)

```powershell
cd "weltwerk\sim"
$env:PYTHONHASHSEED="0"
python test_world_sim.py          # expect 7/7
python world_sim.py               # the destroy-the-reactor walkthrough

# syntax-check the prototype, then open it
cd "weltwerk\fps_demo"
node --check weltwerk_world_prototype.html   # (or just open it in a browser)
```

## NOT claimed

MMO scale, UE5 integration, networking performance, competitive latency, AI. This is a **causal world
substrate** that can later *project into* those engines — the next real question (carried from Phase 4) is
whether a sparse world holds competitive latency, which is a **measurement**, not an assumption.
