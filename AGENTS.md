# URSPRUNG — renderer contract (read before editing)

Ursprung is a deterministic high-fidelity renderer built as a **read-only consumer** of the sealed
`Reality_Engine` (Chronicle/Dentatus) workbench. The workbench is the **verification substrate**, not the
renderer. Do not expand Chronicle/Dentatus concepts here unless they directly improve one of: frame-time
stability, visual fidelity, deterministic replay, debugging, the asset/world pipeline, or player experience.

## The pipeline (the only shape)

```
authoritative world state → deterministic snapshot → visual interpretation → GPU execution → presented frame
```

The renderer may optimize *representation*. It must never mutate authoritative state.

## The four layers — classify every system before building it

| Layer | Meaning | May move the committed trajectory? |
|---|---|---|
| **CORE** | affects committed simulation / replay identity | **yes** |
| **VIEW** | affects presentation only | no |
| **ALLOCATOR** | chooses *where* computation is spent (LOD, culling, quality) | no |
| **OBSERVER** | measures, ranks, reports | no |

Only CORE may affect the authoritative trajectory. LOD, culling, reconstruction, and neural/AI enhancement
are **ALLOCATORs**: they decide *where to spend effort*, never *what is true*. This law is enforced
mechanically at registration time in `ursprung/registry.py` — a non-CORE system that declares
`mutates_core=True` is rejected. The label states intent; the harness (`ursprung/verify.py`) proves behavior.

## The cardinal invariant (the definition of done for any change)

> Run the world with and without the renderer/observer active. The committed hash trajectory must be
> **byte-identical**. If it diverges, the change crossed the membrane and is wrong by definition.

This is checked by `verify.view_perturbation_invariance` (CORE trajectory is byte-identical even with the
VIEW active and deliberately corrupted every tick). `fidelity ⟂ integrity`: visual quality and world
identity are independent axes that must remain separate but composable.

## Ghosts — classify the layer before patching the symptom

A ghost is any unexplained artifact, divergence, instability, mismatch, or residual. Before fixing,
classify it on two axes (`ursprung/ghost_report.py`):

- **category**: temporal · spatial · numerical · perceptual · causal · pipeline-ordering
- **origin**: measurement · approximation · timing · data_loss · model_limit · implementation_error

A ghost allocates investigation. It never certifies a cause and never gates the committed trajectory
(`telemetry ≠ control`). A persistent ghost earns *more* investigation, not a conclusion.

## Performance work

Prefer measurable experiments: **baseline → change → replay → benchmark → compare**. Preserve failed
approaches and the reasons they failed — a failed branch carries architectural information. An
allocation/optimization claim is judged by *comparative utility at equal budget with a negative control*,
never by correctness.

## Working with the sealed workbench

`Reality_Engine` is immutable during this project. Ursprung imports it read-only via `ursprung/_workbench.py`
(the Sibling-Law bridge). Never edit or vendor a workbench file. Reserved top-level module names owned by the
workbench (do not shadow them): `kernel, snapshot, _cores, canon, batch, shard, fixedpoint, ghost, field,
regime, coherence, evolve, predictive, stiefel, spd`. Set `URSPRUNG_WORKBENCH` if the engine lives off the
default path.

## Honest scope

`integrity ≠ truth`. A green milestone means: replay-identical + the renderer demonstrably cannot move the
Weltlinie + monitored invariants intact. It does **not** mean the renderer is correct, fast, or pretty.

## Status

- **Milestone 1 — ACHIEVED.** Smallest world loop + CORE/VIEW/OBSERVER layers + verification harness +
  ghost reporter. The renderer is proven to be observer-only. Run: `PYTHONHASHSEED=0 python3 loop.py`.
- **Next (VIEW vertical slice):** camera → geometry → basic raster path → lighting → frame presentation.
- **Then (ALLOCATOR experiments):** LOD · visibility · adaptive quality · salience · compute budgets — each
  must prove *same world trajectory, different resource allocation*.
