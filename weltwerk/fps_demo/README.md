<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk FPS Causal Demo

A playable first-person shell whose **unique feature is not the gun** — it is that the world's **causal
structure is a first-class, visible, editable object**: you can author it as text, the tool finds
feedback loops before geometry exists, and every shot shows its causal footprint (Potential influence vs
Actual divergence) live. The FPS is the *workload*; the causal runtime is the product.

> Not a generic FPS clone. The shape is: **Unreal-style gameplay shell + causal debugger + world
> authoring tool.** Gun mechanics are deliberately thin.

## Run

- **Playable demo:** open `weltwerk_fps.html` in a browser (loads three.js r128 from CDN — needs network
  once). Click to capture the mouse · `WASD` move · mouse look · `SPACE` jump · **left-click shoot** ·
  `V` causal overlay · `B` B==A correctness audit · `R` save replay · `T` load + verify replay.
- **Verified causal backbone:** `PYTHONHASHSEED=0 python3 scenario_lint.py` — runs the demo's fortress
  scenario through the *tested* authoring layer (`world_spec` + `world_lint`) and prints the same SCC /
  load-bearing / bottleneck analysis the in-demo DSL panel mirrors.

## What is IMPLEMENTED (real, working)

- **First-person shell** (Phase 2): pointer-lock mouse-look, WASD, jump, hitscan shooting via raycaster,
  destructible entities with health/damage.
- **Causal entities + graph** (Phase 3): every entity has `id, position, influence_radius, deps,
  state_hash`; the causal neighbourhood = declared `deps` ∪ spatial entities within `influence_radius`.
  A shot's **Potential** influence is the reflexive reachability over that graph (the `(I∨A)*` closure,
  mirrored from `scale/reachability_algebra.py`); **Actual** divergence is the set of entities whose
  state truly changed (barrels chain-explode through the neighbourhood).
- **Causal overlay** (Phase 4, press `V`): entities recoloured BLUE committed · GREEN potential · YELLOW
  allocated · RED actual; green wireframe influence spheres around the potential set. The HUD shows the
  `potential − actual` gap (the win) live.
- **Text → topology authoring** (Phase 5): the right-hand DSL panel parses `<src> <relation> <dst>` into
  a causal graph and reports reachability, **SCC / feedback clusters**, and load-bearing nodes —
  mirroring `world_lint.py`. The fortress demo flags the `gate→courtyard→market→garrison` feedback loop.
- **Determinism** (Phase 6): seeded PRNG (mulberry32), `state_hash` over all entities, discrete causal
  inputs recorded; `R` saves a replay, `T` replays it and verifies the final hash matches
  (DETERMINISTIC / DIVERGED).
- **B==A correctness** (Phase 9): every shot computes a *full* re-hash (A) and the *allocated* causal
  cascade (B) and reports `PASS`/`FAIL`; `B` runs an independent audit. Correctness is asserted before
  any efficiency is shown — `B == A` or it's a bug, never a benchmark.
- **Verified Python backbone** (`scenario_lint.py`): the scenario's topology analysis run through the
  tested authoring modules.

## What is SIMULATED (toy, demo-fidelity, not production)

- **Damage / propagation model**: integer HP, fixed splash radii, chain-explosion. A stand-in for "an
  action's causal cascade", not a physics engine.
- **NPC behaviour**: entities exist as causal nodes; autonomous patrol AI is minimal/static.
- **Potential/Actual primitives in JS**: re-implemented for interactive rates. The **verified reference**
  is the Python (`scale/`, `authoring/`); the JS is a *demo mirror* of it, not a second authority.
  Cross-checking JS-vs-Python on identical scenarios is a **scaffolded** validation (not yet wired).

## What is only SCAFFOLDED (a boundary, not a system)

- **Replication / multiplayer** (Phase 7): `replicationAccounting()` decides `replicate(e)` iff
  *actual-divergence* OR *player-relevance* OR *importance*, and the HUD logs `full` vs `causal` entity
  counts **per frame**. This is the *boundary*, instrumented — **no networking, no server, and no
  savings claim.** The numbers are measured counts for this session only; whether causal replication
  beats geography is exactly the regime-dependent question documented in `../SCOPE.md` (cheap iff
  `Actual ≪ Potential`, λ≤0). `replication ≠ networking`.
- **MMO scale**: not built, not claimed. The instrumentation exists so future validation is possible.

## Honest framing (per the project's discipline)

- `structural-cycle ≠ measured-amplification` — the DSL panel flags feedback loops as a *risk*; whether a
  loop actually amplifies is a dynamical question (`scale/amplify.py`).
- `potential ≠ actual` — the overlay keeps them in separate colours; the gap is the whole point.
- `B == A` gates every efficiency story; correctness is never traded for a benchmark.
- The Python layer is the verified authority; this HTML is a playable mirror that makes the causal
  structure *visible and editable before graphics and networking are finished* — which is the deliverable.
