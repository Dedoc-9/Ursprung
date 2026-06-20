# URSPRUNG — renderer contract (read before editing)

Ursprung is a deterministic high-fidelity renderer built as a **read-only consumer** of the sealed
`Reality_Engine` (Chronicle/Dentatus) workbench. The workbench is the **verification substrate**, not the
renderer. Do not expand Chronicle/Dentatus concepts here unless they directly improve one of: frame-time
stability, visual fidelity, deterministic replay, debugging, the asset/world pipeline, player experience, or
**information integrity** (anti-cheat / multiplayer disclosure — the second arc; see *The information-firewall
discipline* below).

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

### Temporal Fidelity Conservation Law (the synthesis)

> A renderer does not create fidelity. It distributes finite fidelity across competing uncertainties.
> Therefore the objective is not maximum detail — it is **minimum consequential discontinuity under a fixed
> budget.**

Fidelity is **transferred**, never created: more here = less elsewhere; more now = less later; more spatial =
less temporal; more shading = less geometry. Every optimization is a zero-sum transfer on a fixed (~4.13 ms)
budget (`ursprung/fidelity_conservation.py`): `is_conserved(alloc, budget)` (Σ = budget), `transfer()` (zero-
sum, fail-closed), and the quantity to minimize, `consequential_discontinuity(regions, alloc)`. This bridges
the other three laws — the Arbitrary-Boundary Law makes the boundaries fidelity flows across deterministic;
PFAL/TCFF decide where/when to move it; the Polygon Reconciliation Law makes rasterization the *transport*,
not the strategy. The hierarchy re-centers on allocation:

```
WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → RASTERIZATION → IMAGE
                                 (the strategic layer)   (transport)
```

### Reality Debt Law (the law underneath the other four)

> Every approximation incurs reality debt. The role of predictive allocation is not to eliminate debt, but
> to ensure debt accumulates where future consequence is lowest and repayment cost is smallest.
>
> **Debt = Approximation × Persistence × Consequence**

The reframing: **fidelity is conserved, but debt is accumulated** — so PFAL/TCFF allocate *debt repayment*,
and the renderer is a financial system for approximation (`ursprung/reality_debt.py`). Every optimization is
either **borrowing** (reduces cost now by taking fidelity from the future — incurs debt that comes due as an
artifact: LOD→pop-in, temporal reconstruction→ghosting, culling→visibility error, quantization→precision
error, prediction→mis-prediction) or **genuine** (no future fidelity loss — no debt). A traditional optimizer
asks "save 0.5 ms?"; Ursprung asks "save 0.5 ms — borrowed or genuine?" Dini-style observation becomes
anticipatory: not "artifact detected" but "which approximation will create the *next* artifact?"

The hierarchy gains a debt-management layer (rasterization stays transport):

```
WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → DEBT MANAGEMENT → RASTERIZATION → IMAGE
        truth  →  prediction  →  fidelity  →  debt  →  image   (compactly)
```

The one-line philosophy Ursprung is built to be known for: **arbitrary boundaries require deterministic
handling, and finite fidelity should be allocated by expected future failure cost, not present visual
complexity.**

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

## The information-firewall discipline (the renderer must not become an oracle)

In a shared, partially-hidden world the renderer is also a potential **leak** of hidden state. Treat any
new VIEW/ALLOCATOR/OBSERVER system as something an adversary will read, and obey this ladder of invariants
(modules in parentheses; full synthesis in the README's *second arc* and `docs/MEASUREMENT_DISCIPLINE.md`):

- **integrity ≠ confidentiality ≠ authorization ≠ harmlessness.** Unforged + agreed-upon does not mean a
  client is *entitled* to use a claim (`causal_access.py`), and individually-authorized fragments must not
  *jointly* reconstruct a secret (`reconstruction.py`).
- **the defense is the leak.** The system's own behavior is a side channel — response timing, which branch
  was prepared, the *reaction* to a secret (fog/LOD/latency), a conspicuous *absence*, an uncertainty radius,
  a boundary that flips on hovering, an execution-cost hitch, a rollback's magnitude/timing. A new feature
  must not make any observable correlate with hidden state. Defenses: timing normalization +
  prediction-inversion breadth + weighted-trust consensus (`side_channel.py`), Reaction Debt + absence
  firewall (`adversarial_dynamics.py`), Ambiguity Debt + Representation Hysteresis (`representation_privacy.py`),
  Execution Surface Privacy (`execution_surface.py`), Reconciliation Signature Debt (`convergence.py`).
- **the invariant ladder:** `consequence ≠ mechanism` → `image ≠ generator` → `renderer ≠ oracle` →
  `correction ≠ cause`. A representation may reveal *what happened in the world*; never the *rule that maps
  hidden state to representation*, nor the *machinery* (timing/cache/cost) that runs it, nor the *cause of a
  correction* beyond the fact that the world changed.
- **the one absolute, and the honest rest.** `Security = non-identifiability under bounded experimental
  access.` The only class-independent guarantee is to **sever the secret from every observable channel**
  (`I(secret ; observable) = 0` ∀ observable; `channel_discovery.py`). Everything else is non-identifiable
  only *relative to a stated observer class* and dissolves against a richer one (`adversary_capacity.py`).
  Never claim "safe"; report what was found, by which estimator class, with what coverage boundary —
  `secure-against-this-observer ≠ secure`, and the detector is itself a hypothesis class.
- **report your blind spot.** Every measurement/observer tool must return its **coverage boundary** — what
  its estimator/hypothesis class *cannot* see — alongside what it found, never a bare `safe`/`leak` boolean.
  The detector is itself a bounded observer (its reach is an Adversary-Information-Capacity choice one level
  up); `I = 0 under estimator E` is not `I = 0 in the system`. An instrument that hides its blind spot
  silently upgrades `tested` to `safe`. The pattern is `MeasurementResult` in `channel_discovery.py`
  (`{channel, estimator_class, detected_information, coverage_boundary}`). For maintainers this flips the
  default question from *"what mechanism blocks this?"* to *"what does this mechanism make observable, and
  what observer class are we bounding?"*

Every such system is an **OBSERVER** (it measures, ranks, attributes; it never mutates the trajectory and
never asserts truth). The cardinal invariant and the four-layer law above still bind it.

## Performance work

Prefer measurable experiments: **baseline → change → replay → benchmark → compare**. Preserve failed
approaches and the reasons they failed — a failed branch carries architectural information. An
allocation/optimization claim is judged by *comparative utility at equal budget with a negative control*,
never by correctness.

## Use cases — how to apply Ursprung in a real project

Ursprung is a **specification + reference + measurement discipline**, not a turnkey product. Hold that framing
before adopting any of it: `integrity ≠ truth`, `tested ≠ safe`, `simulation ≠ physics`, and every bench number
is constructed and **expires on real silicon**. With that in mind, there are four robust ways an engineer — or
an LLM acting as one — can produce real value from this repo today, followed by an honest statement of the
adoption gap.

**1. As a design discipline / guardrails (usable as-is, nothing to run).** Apply the four-layer law to classify
every subsystem *before* building it; hold the cardinal invariant (replay-identical with the observer active
and deliberately corrupted) as the definition of done; route every feature through the render Verification
Record (`TYPE` / `EFFECT` / `NON-EFFECT` / `EVIDENCE`); and enforce the ladders — `observation → allocation`
ALLOWED, `observation → truth` FORBIDDEN; `consequence ≠ mechanism → image ≠ generator → renderer ≠ oracle →
correction ≠ cause`; plus *report your blind spot*. This is portable to any renderer / multiplayer / anti-cheat
/ simulation codebase, independent of Ursprung's own modules. **Highest current value.**

**2. As a pattern / reference library (adapt the working code).** The mechanisms are real, tested reference
implementations to transplant and re-validate on your data: water-filling allocation + the resistance tensor
(LOD / quality budgeting), transition & reaction debt (hitch / leak avoidance), the composition firewall +
capability / access-control layers (anti-cheat information flow), `channel_discovery` (mutual-information leak
auditing), `DisclosurePolicy` (intent → representation), and the privacy-funnel framing
(`maximize utility − λ·leakage`). Port the *shape*; the constructed numbers do not transfer.

**3. As a measurement / audit substrate (the nearest real win).** Point `channel_discovery` + the
`DisclosurePolicy` auditor at a real telemetry or output stream to find *actual* leaks — *policy says reveal X;
did the output contain only X?* This is the empirical phase and yields real results with modest work; it needs
an estimator that handles continuous, coupled signals (the bundled one is discrete / symbolic), but the loop,
the `MeasurementResult` boundary discipline, and the adversary-class sweep (`adversary_capacity`) are already
here. Report findings as "found by estimator E over trace D against class A," never "safe."

**4. As an LLM-on-track methodology (for any systems project).** The `observe → hypothesize → implement →
verify → record` loop, the four LLM failure-mode guards (silent architectural drift, accidental authority
leakage, unreplayable behavior, unmeasured optimization claims), and *preserve failed branches* keep an LLM
coding partner disciplined on work that has nothing to do with rendering (`docs/LLM_ON_TRACK.md`).

**The adoption gap (what it is NOT yet).** It does not run for a stranger out of the box. CORE
(`world_core.py`) consumes the *sealed* `Reality_Engine` kernel via `URSPRUNG_WORKBENCH`, so a new project must
**substitute its own deterministic world / sim** behind the snapshot contract. There are **no production
backends**: `raster.py` emits a hashable *reference* framebuffer (not GPU pixels), `reality_harness.NetworkChannel`
is a *simulated* socket, the adversary learners are toy, and `disclosure.compile_emission` is a lookup, not the
funnel solve. The adoption path is therefore: (a) wire your own CORE / world behind the snapshot contract;
(b) lower one real backend (GPU / audio / netcode / agent-observation); (c) re-run the relevant benches on real
data — at which point the constructed numbers become measured ones and the discipline begins governing a live
system. Until then, uses 1–4 apply; "Ursprung as a shipped feature" does not.

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

The conceptual arc is **complete** (303-check suite). M1 foundation + invariant harness → M2 the five laws →
M3/3.1 the VIEW raster slice and the *ranking ≠ allocation* result (from a recorded **failed** hypothesis) →
M4–M9 fidelity-as-economy (resistance tensor, shader cache, readiness, providers, dependency integrity,
compiler) → M10–M21 the information-firewall arc (see the section above) → Channel Discovery + the
Measurement Discipline. Run: `PYTHONHASHSEED=0 python3 loop.py`; suite `python3 tests/test_ursprung.py`.

**The remaining work is empirical, not more laws.** Do not add another conceptual milestone without explicit
direction; the only sanctioned additions now are **better measurement substrates** or **stronger observer
classes**, both *experiments*. The next builds live behind two intentionally-unbuilt seams —
`reality_harness.NetworkChannel` (wire to a real socket) and `behavioral_harness.ExperimentLayer(channel="real")`
— plus a real-silicon benchmark (every constructed number expires there), a richer `CompositeResistance`, a
real ML/RL adversary class replacing the toy learners, and channel discovery over real telemetry traces.
