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

## Renderer application rules

The LLM is a **design accelerator, not an authority layer.** Every renderer change follows
`observe → hypothesize → implement → verify → record`, and guards the four LLM failure modes: silent
architectural drift, accidental authority leakage, unreplayable behavior, unmeasured optimization claims.

- **LOCKSTEP** — the simulation tick is authoritative; frame rate / interpolation / presentation timing are
  observations; a frame budget is a measurement, not a simulation constraint.
- **LOD / CULLING** — visibility decides what to *render*, not what *exists*; never convert missing
  information into hidden truth.
- **SALIENCE / ALLOCATION** — may prioritize perception, consequence, uncertainty, future relevance; may not
  redefine world state, causality, or simulation importance.
- **AI GENERATION LOOP** — generated code must pass determinism, replay, boundary, and performance-comparison
  checks. *A faster renderer with altered world semantics is a regression.*
- **PERFORMANCE CLAIMS** — never "better/faster/more realistic" without baseline, test conditions,
  measurement method, and comparison. A benchmark measures the benchmark's world, not universal superiority.

Every new feature declares `TYPE` (CORE/VIEW/ALLOCATOR/OBSERVER), `EFFECT` (what changes), `NON-EFFECT` (what
must remain unchanged), and `EVIDENCE` (how verified) — via the render Verification Record
(`ursprung/render_record.py`; template `docs/RENDER_VERIFICATION_RECORD.md`). This makes Nanite-like
allocation, AI upscaling, ray tracing, foveated rendering *experiments*, not architectural invasions.

## The Arbitrary-Boundary Law

> **Arbitrary boundaries require deterministic handling, not claims of truth.** (The renderer's `integrity ≠ truth`.)

```
determinism → integrity of PROCESS    (same convention → same result)
determinism ↛ correctness of OUTCOME  (the convention is a choice, not a law of nature)
```

Wherever the renderer makes an arbitrary choice (pixel coverage, float representation, LOD threshold, tick
rate), the choice is declared explicit, deterministic, and content-addressed in `ursprung/conventions.py`,
carrying its rejected alternatives and `not_a_truth_claim = True`. An artifact is often the **footprint of a
boundary choice**, not an error: ask *"what assumption created this, and is it acceptable for the purpose?"*
— not *"the artifact exists, therefore the model is wrong."* Tag such artifacts with
`conventions.boundary_ghost()` (origin `boundary_choice`); they allocate investigation, never certify error.

### Polygon Reconciliation Law

> Polygons are not preserved because they are correct. Polygons are preserved because abandoning them imposes
> greater practical cost than their approximation error. The optimization target is **reconciliation under a
> fixed 4.13 ms budget, not replacement.** Polygons cannot be marginalized.

The Arbitrary-Boundary Law applied to representation itself (`ursprung/polygon_reconciliation.py`). Polygons
are a deterministic **convention** and the **industrial compatibility layer** (hardware, APIs, content tools,
engines, assets), not an ontological commitment. The triple: **polygons = compatibility layer · rasterization
= execution mechanism · predictive allocation (PFAL/TCFF) = fidelity multiplier.** The engineering task is not
to prove polygons correct nor to replace them with a "purer" representation (voxels, point clouds, neural
fields, Gaussian splats, SDFs, hybrid scene graphs — all recorded as rejected *replacements*), but to manage
where their approximations fail. The decision is a deterministic rule over declared costs —
`reconcile(abandonment_cost, approximation_error)` keeps polygons iff `abandonment_cost ≥ approximation_error`
— never a truth claim about representation.

The standing risk: too many interesting capabilities competing to become the center of gravity. Success may
be **more than one result in a pool** of composable features that each stay on their side of the membrane —
not a single dominant technique. `docs/LLM_ON_TRACK.md` is the counterweight.

## Predictive fidelity (the pioneering direction)

A renderer that spends computation where its **approximation is most likely to fail, weighted by the cost of
being wrong** — never where it merely "looks important." The chain (full treatment in
`docs/PREDICTIVE_FIDELITY.md`):

- A frame is a *prediction*; `ghost = max(0, observed − predicted)`, and **ghost ≠ error** — it means the
  representation failed to predict this region (`ursprung/prediction.py`, OBSERVER).
- Classify render ghosts into **temporal / spatial / numerical / causal**; each maps to an allocation
  response, never a world change (`ursprung/temporal_membrane.py`, ALLOCATOR).
- The **Temporal Reality Budget** allocates a fixed budget by `uncertainty × consequence` (consequence is an
  input from `causal_runtime`), not by visible complexity.
- **PFAL**: `R = U × C × P × S` (uncertainty · consequence · persistence · sensitivity). Carefully worded
  claim: *the renderer spends computation where its current approximation has the highest expected failure
  cost* — not "knows what matters." A measurable hypothesis, with a comparative bench + negative control
  (`ursprung/pfal_bench.py`); constructed-world numbers that **expire on real silicon**.

Three classes of difference gate every artifact before it is called a bug (`ursprung/divergence.py`): WORLD
(CORE changed — invalid for non-CORE), REPRESENTATION (same CORE, different lens — expected, measure),
OBSERVATION (same lens, different measured behavior — investigate the ghost). The laws that never bend:
`ghost → change world` FORBIDDEN; `observation → allocation` ALLOWED; `observation → truth` FORBIDDEN.
Because allocation never touches truth, one committed world can feed many renderers (cinematic, competitive,
VR, handheld, debug) — each a lens, none redefining the world.

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
