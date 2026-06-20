# Ursprung

A deterministic high-fidelity renderer that treats rendering as a **perception layer over an authoritative
world model**. Ursprung consumes the sealed `Reality_Engine` (Chronicle/Dentatus) workbench read-only as its
verification substrate; the workbench supplies the deterministic kernel and the integrity discipline, and
Ursprung is the renderer projected off the committed trajectory.

```
authoritative world state → deterministic snapshot → visual interpretation → GPU execution → presented frame
```

**Author:** Daniel J. Dillberg · **Contact:** [bigdilly95@gmail.com](mailto:bigdilly95@gmail.com)
**License:** [AGPL-3.0-only](LICENSE)

The renderer never discovers truth; it manages where its approximations fail. Its one-line philosophy:
**arbitrary boundaries require deterministic handling, and finite fidelity should be allocated by expected
future failure cost, not present visual complexity.**

What began as a renderer *philosophy* has, under benchmarking, become a set of measurable **rendering
economics**: finite fidelity is a budget, every approximation is debt, and the bench — not the manifesto —
decides which allocation policy wins. The central result so far came from a *failed* hypothesis (see below):
**priority and allocation are different mathematical objects.**

## The five laws (the philosophy layer)

1. **Reality Debt Law** *(underneath)* — every approximation incurs debt: `Debt = Approximation ×
   Persistence × Consequence`. Fidelity is conserved, but debt is accumulated; allocation places debt where
   future consequence is lowest. (`reality_debt.py`)
2. **Arbitrary-Boundary Law** — representation choices (pixel coverage, float format, LOD threshold, tick
   rate, polygons) are deterministic *conventions*, never truth claims. (`conventions.py`)
3. **Predictive Fidelity Law (PFAL / TCFF)** — spend computation where future failure cost is highest:
   `R = U × C × P × S × τ`. (`prediction.py`, `temporal_membrane.py`, `pfal_bench.py`, `tcff.py`)
4. **Polygon Reconciliation Law** — keep polygons iff abandoning them costs more than their approximation
   error; rasterization is transport, allocation is strategy. (`polygon_reconciliation.py`)
5. **Temporal Fidelity Conservation Law** — fidelity is transferred, not created; the objective is *minimum
   consequential discontinuity under a fixed budget*, not maximum detail. (`fidelity_conservation.py`)

```
WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → DEBT MANAGEMENT → RASTERIZATION → IMAGE
```

## Rendering economics — priority ≠ allocation (the discovered hierarchy)

The benchmark that *failed* the naive Causal Continuity Hypothesis (allocate ∝ U·C·P) exposed a missing
hierarchy and a result more useful than any single law: **what matters**, **what is expensive to represent**,
and **how to distribute finite budget** are three separate objects.

```
Truth layer        →  Consequence layer  →  Priority layer  →  Allocation layer  →  Rasterization layer
(the Weltlinie)       (Reality Debt)         (PFAL ranks)       (water-filling)       (executes)
```

| Quantity | Answers | Form | Module |
|---|---|---|---|
| **Reality Debt** | future liability | `A × P × C` | `reality_debt.py` |
| **Priority (PFAL)** | *what matters?* | `U × C × P × S × τ` | `pfal_bench.py`, `tcff.py` |
| **Representation Resistance** | *what is expensive to represent?* | `Rr` (perimeter today; composite later) | `representation.py` |
| **Allocation (water-filling)** | *how to distribute budget?* | `WaterFill(Priority, Resistance) ∝ √(Priority·Rr)` | `allocation.py` |
| **Rasterization** | executes the allocation | conventions | `raster.py` |

**The measured result.** Proportional allocation (∝ priority) *over-concentrates* on a convex error metric;
two-stage `ranked_waterfill` (rank by priority, then water-fill under representation resistance) **strictly
beat** uniform, distance, visibility, proportional-causal, and a negative control on the future-causal
residual metric. The proportional allocator *knew what mattered*; the water-filling allocator *knew what
mattered and where representation actually breaks.* (Constructed-world; expires on real silicon.)

The **Causal Continuity Hypothesis** therefore remains explicitly *provisional* — the naive (proportional)
form failed; the re-specified two-stage form is *supported on the constructed bench, pending real silicon*.
Nothing is promoted to a law by a benchmark on a model world.

See [`docs/GENEALOGY.md`](docs/GENEALOGY.md) for the full genealogy & checklist of what is built, verified,
and not yet built, and [`docs/PREDICTIVE_FIDELITY.md`](docs/PREDICTIVE_FIDELITY.md) for the prediction →
membrane → PFAL → TCFF chain.

## Run it

```bash
PYTHONHASHSEED=0 python3 loop.py                  # live loop: milestone + prediction/membrane/PFAL/TCFF/PCJ
PYTHONHASHSEED=0 python3 tests/test_ursprung.py   # unit suite (stdlib asserts)
```

If the engine is not at `~/Desktop/Reality_Engine`, set `URSPRUNG_WORKBENCH=/path/to/Reality_Engine`.

## What Milestone 1 proves (and only this)

> *I can replay the same world and prove the renderer is only an observer.*

- **replay identity** — the same world run N times yields byte-identical committed trajectories.
- **view-perturbation invariance** — the CORE trajectory is byte-identical even with the VIEW layer active
  and *deliberately corrupted* every tick (the renderer cannot move the Weltlinie — no write-back).
- **ordering invariance** — permuting input body order does not change the trajectory (id-sorted evolution).

It does **not** prove the renderer is correct, fast, or pretty. `integrity ≠ truth`.

## Layout

| Path | Layer | Role |
|---|---|---|
| `ursprung/_workbench.py` | bridge | Sibling-Law read-only access to `Reality_Engine` |
| `ursprung/world_core.py` | **CORE** | authoritative trajectory (wraps the AetherPulse kernel): tick · hash · replay · compare |
| `ursprung/view_layer.py` | **VIEW** | read-only snapshot → camera → VisualFrame; no write-back |
| `ursprung/registry.py` | — | system-classification register; enforces "only CORE may mutate the trajectory" |
| `ursprung/ghost_report.py` | **OBSERVER** | ghost capture & classification (6 categories × origins) |
| `ursprung/verify.py` | **OBSERVER** | the milestone verification harness |
| `ursprung/render_record.py` | **OBSERVER** | emits a render Verification Record (features as experiments) |
| `ursprung/conventions.py` | **OBSERVER** | the Arbitrary-Boundary Law / Boundary Ledger (declared, hashed, never truth) |
| `ursprung/divergence.py` | **OBSERVER** | the 3 divergence classes (world / representation / observation) |
| `ursprung/prediction.py` | **OBSERVER** | Dini-style predict→observe→ghost (surprise → attention, never authority) |
| `ursprung/temporal_membrane.py` | **ALLOCATOR** | Temporal Prediction Membrane + Temporal Reality Budget (uncertainty × consequence) |
| `ursprung/pfal_bench.py` | **OBSERVER** | PFAL `R=U×C×P×S` + falsification bench (uniform / distance-vis / PFAL, negative control) |
| `ursprung/tcff.py` | **ALLOCATOR** | TCFF `F=U×C×P×S×τ` proactive pre-warming + Perceptual Continuity per Joule bench |
| `ursprung/polygon_reconciliation.py` | **OBSERVER** | Polygon Reconciliation Law: polygons as deterministic convention; `reconcile()` not replace |
| `ursprung/fidelity_conservation.py` | **OBSERVER** | Temporal Fidelity Conservation Law: fidelity is transferred, not created; minimize consequential discontinuity |
| `ursprung/reality_debt.py` | **OBSERVER** | Reality Debt Law: `Debt = Approximation × Persistence × Consequence`; place debt where consequence is lowest |
| `ursprung/causal_continuity.py` | **OBSERVER** | Causal Continuity *Hypothesis* (provisional): allocate ∝ expected future causal loss `U×C×P`; PFAL⇄Debt duality |
| `ursprung/raster.py` | **VIEW** | deterministic reference rasterizer: projection→coverage→sampling→raster, each a declared convention; hashable framebuffer |
| `ursprung/raster_bench.py` | **OBSERVER** | equal-budget allocation bench + promotion gate (the hypothesis *failed* as stated — recorded with diagnosis) |
| `ursprung/representation.py` | **OBSERVER** | Representation Resistance (difficulty to represent) + `DebtPressure = RealityDebt × RepresentationResistance` |
| `ursprung/allocation.py` | **ALLOCATOR** | the ranking/allocation split: `rank(priority)` then `waterfill(priority, resistance)` — *PFAL ranks, water-filling allocates* |
| `ursprung/perceptual.py` | **OBSERVER** | Perceptual Continuity Loss (reallocation churn × sensitivity) — the measurable *success* axis |
| `ursprung/policy_arena.py` | **OBSERVER** | dual-axis arena (causal residual × perceptual continuity); Pareto front; hardened `damped_waterfill` |
| `ursprung/stress.py` | **OBSERVER** | adversarial weakness extraction (Goodhart mutation guard + WRONG/GAMEABLE), after the workbench's `mutate`/`adversary` |
| `ursprung/transition_debt.py` | **OBSERVER** | Total Cost = Representation + λ·Transition (+ Latency); the winning policy is a function of the exchange rate λ (modes = λ) |
| `ursprung/adversarial_scenes.py` | **OBSERVER** | flicker / false-future / delayed-consequence / cliff traps; greedy thrashes vs damped lags — no universal damping |
| `ursprung/resistance_tensor.py` | **OBSERVER** | multi-dimensional Representation Resistance (7 dims) + `miss_cost` + fidelity derivative `∂Fidelity/∂Budget` |
| `ursprung/shader_cache.py` | **ALLOCATOR** | shader/PSO cache as validated representation memory; multi-horizon prewarm + fallback tiers (turns hitches into allocation) |
| `ursprung/causal_surface.py` | **OBSERVER** | Causal Surface Area = agents × divergence × representation cost (how many futures depend on it); prepare ≠ decide guard |
| `ursprung/readiness.py` | **ALLOCATOR** | Representation Readiness Layer — shader/stream/residency/neural/particles as one prewarm problem (`P(needed) × CSA`) |
| `ursprung/causal_contract.py` | **OBSERVER** | Causal Contract: a map of possible causality (never an outcome) + CSA temporal decay (`CausalAuthorityLeak` guard) |
| `ursprung/representation_futures.py` | **ALLOCATOR** | Representation Futures Graph: prepare branches by `P(transition)×CSA`; `select_future()` forbidden; rollback = representation survives truth |
| `ursprung/causal_mutation.py` | **OBSERVER** | Causal Mutation Surface = `authority_distance × agents × rollback × rep`; Shared Object Crucible (loses least when reality disagrees) |
| `ursprung/provider_contract.py` | **OBSERVER** | representation providers declare `{inputs, cost, failure_mode}`; readiness selects by contract, degrades gracefully |
| `ursprung/dependency_surface.py` | **OBSERVER** | Dependency Surface Area + `Preparation Value = CSA × Dependency Access` (the hidden resource is dependency access) |
| `ursprung/dependency_integrity.py` | **OBSERVER** | Dependency Integrity Layer: content-hash tautology + exact-integer k-of-n consensus stream validator + evidence/decay (access ≠ relevance) |
| `ursprung/representation_compiler.py` | **ALLOCATOR** | compose provider contracts into the cheapest representation chain that preserves continuity under a latency budget |
| `ursprung/capability.py` | **OBSERVER** | Causal Capability Token: permissioned use of dependency knowledge; `mutate/select/reveal_hidden` forbidden on every token |
| `ursprung/causal_access.py` | **OBSERVER** | Causal Access Control Layer (information firewall): a claim influences representation only if unforged AND in authorized causal scope AND capability-permitted (blocks wallhack/ESP) |
| `ursprung/reconstruction.py` | **OBSERVER** | Causal Composition Firewall + Information Reconstruction Debt: cap a SET of allowed fragments so they can't jointly reconstruct forbidden knowledge |
| `ursprung/side_channel.py` | **OBSERVER** | side-channel defenses: timing normalization, prediction-inversion breadth guard, weighted-trust consensus (defeats colluding clients) |
| `ursprung/accumulation.py` | **OBSERVER** | Accumulation Safety: temporal Reconstruction Debt (history-compression), Representation Privacy Budgets, Causal Query Rate Limiting, `importance ≠ exposure` — the query is allowed, the *sequence* is not |
| `ursprung/adversarial_dynamics.py` | **OBSERVER** | Adversarial Information Dynamics: Reaction Debt (the defense leaks through its reactions), absence firewall (`missing ≠ informative`), Distributed Reconstruction Debt (cross-client triangulation), adaptive ≠ random, and the floor — reveal `consequence`, never `mechanism` |
| `ursprung/representation_privacy.py` | **OBSERVER** | Representation Privacy / Ambiguity Control: Ambiguity Debt (uncertainty ≠ instrument), Representation Hysteresis (enter ≠ exit), decoy-without-mutation, Observer Fingerprint Debt, and the invariant `image ≠ generator` (structural shape of Indistinguishability Obfuscation, not its proof) |
| `ursprung/execution_surface.py` | **OBSERVER** | Execution Surface Privacy: Transition Signature Debt (Δ latency/cache/memory must not correlate with the secret), Cache Side-Channel Budget, semantic constant-time (world A vs B indistinguishable), three-currency objective (fidelity + transition + leakage), and `renderer ≠ oracle` — where M6 and M15 fuse |
| `ursprung/convergence.py` | **OBSERVER** | Convergence Surface / Distributed Reality Reconciliation: Reconciliation Signature Debt (rollback is a side channel; bounded correction family), Divergence Firewall (disagreement ↛ hidden fact), Convergence Readiness (prepared so the correction is cheap), distributed correction reconstruction (honest clients as a microscope), and `correction ≠ cause` |
| `ursprung/reality_harness.py` | **OBSERVER** | the Reality Harness: authoritative server + simulated `NetworkChannel` (the swappable seam to real netcode) + client mirrors; measures correction entropy / convergence / observer distinguishability / fidelity cost across reconciliation policies. `traffic produces the hypothesis` (simulation ≠ physics) |
| `ursprung/behavioral_harness.py` | **OBSERVER** | the Behavioral Reality Harness: Convergence Leakage Vector (privacy ≠ scalar), counterfactual amplification (adversarial probe control), the experiment-layer seam (simulated=regression / real=validity), and the player as the final observer — `image ≠ generator` at the gameplay layer |
| `ursprung/adversary_harness.py` | **OBSERVER** | the Adaptive Adversary Harness: a closed-loop learning observer (probe + memory + active experiment selection + regret); `Behavioral Leakage = info / experiments`; measures whether constant-feel withstands a *learning* adversary (naive cracked in O(log N); constant-feel regret stays flat). `secure-against-this-observer ≠ secure` |
| `ursprung/adversary_capacity.py` | **OBSERVER** | Adversary Information Capacity: sweeps the adversary's **model class** (a lattice: passive / threshold / single-bit / structured) over two targets — the **secret** vs the **generator**. Result: severing the secret is *absolute* (beats all classes); generator-privacy is only ever *class-relative* (M20's constant-feel falls to a structure learner). `security = non-identifiability under bounded experimental access` |
| `loop.py` | — | smallest executable world loop, end to end |
| `AGENTS.md` | — | the renderer contract (the rules every change obeys) |

## Status

- **Milestone 1 — done.** Foundation + invariant harness; the renderer is proven observer-only.
- **Milestone 2 — done.** Predictive-fidelity architecture + the five laws (debt · boundary · PFAL ·
  reconciliation · conservation), each encoded as data/rule with a verified demo and an honest bound.
- **Milestone 3 — done.** VIEW vertical slice (deterministic projection→coverage→sampling→raster) + the
  Causal Continuity Hypothesis. The naive hypothesis **failed** the equal-budget bench (recorded, not hidden).
- **Milestone 3.1 — done.** The failure became a refinement: the ranking/allocation split + Representation
  Resistance. `ranked_waterfill` strictly beat every control.

**Open work (bench-defined, not more laws):**
- A **real-silicon benchmark** — every constructed-world number above expires there (equal GPU time;
  temporal artifacts, input-to-photon latency, reconstruction error, motion stability).
- A **richer Representation Resistance** than perimeter: geometric, temporal, shading, reconstruction,
  perceptual, and causal resistance fields composed into one `CompositeResistance`.

## Toward a fidelity operating system (direction, not built)

The strongest thing Ursprung has is not any single law — it is the separation between what is **invariant**
and what is **replaceable**. The aim is a model where entire *reasoning systems about rendering* are
pluggable over one verified world:

```
WORLD                 invariant        OBSERVATION PROVIDERS   pluggable
SNAPSHOT              invariant        PREDICTION PROVIDERS    pluggable
                                       RESISTANCE PROVIDERS    pluggable
verification substrate INVARIANT       FIDELITY POLICIES       pluggable
(snapshot contract,                    ALLOCATION SOLVERS      pluggable
 ghost taxonomy,                       RASTERIZATION BACKENDS  pluggable
 verification record,                  PRESENTATION BACKENDS   pluggable
 replay harness,
 determinism rules)
```

The hard line: the **verification substrate is immutable.** The moment integrity itself becomes pluggable,
integrity becomes subjective and the whole discipline dissolves. Everything above it — observation,
prediction, resistance, policy, allocation, raster/presentation backends, even a hardware-abstraction layer
that lowers one allocation graph onto different GPUs — may evolve. (Open forks worth keeping distinct:
*causal weight vs perceptual weight* as separate scores; *fidelity derivatives* `d(FailureCost)/dt` for
anticipatory rather than reactive allocation.) None of this is built; it is the debate the architecture is
being kept open for.

## Further reading

[`docs/LLM_ON_TRACK.md`](docs/LLM_ON_TRACK.md) — how the workbench mechanisms keep an LLM coding partner on
the renderer track. [`docs/PREDICTIVE_FIDELITY.md`](docs/PREDICTIVE_FIDELITY.md) — the prediction → membrane →
PFAL → TCFF chain. [`docs/RENDER_VERIFICATION_RECORD.md`](docs/RENDER_VERIFICATION_RECORD.md) — features as
experiments. [`docs/GENEALOGY.md`](docs/GENEALOGY.md) — the full genealogy & checklist. [`AGENTS.md`](AGENTS.md)
— the contract every change obeys.

## License

Ursprung is licensed under the [GNU Affero General Public License v3.0 only](LICENSE) (AGPL-3.0-only).
Copyright (C) 2026 Daniel J. Dillberg. It consumes the sealed `Reality_Engine` workbench read-only (the
Sibling Law) and does not vendor or relicense any of it.
