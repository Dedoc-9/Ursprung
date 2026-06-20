# Ursprung — genealogy & checklist (thus far)

The engineering lineage of Ursprung: what was built, in what order, which law it established, how it was
verified, and its honest bound. Modeled on the workbench's `GENEALOGY.md`. `integrity ≠ truth` throughout.

## The five laws (the philosophy layer)

```
Reality Debt Law          (underneath)  every approximation incurs debt = approx × persistence × consequence
   └─ Arbitrary-Boundary Law            representation choices are deterministic conventions, not truth
   └─ Predictive Fidelity Law (PFAL/TCFF) spend where future failure cost is highest (U·C·P·S·τ)
   └─ Polygon Reconciliation Law        keep polygons iff abandonment cost ≥ approximation error
   └─ Temporal Fidelity Conservation    fidelity is transferred, not created; minimize consequential discontinuity
```

One line: **arbitrary boundaries require deterministic handling, and finite fidelity should be allocated by
expected future failure cost, not present visual complexity.**

The hierarchy these produce:

```
WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → DEBT MANAGEMENT → RASTERIZATION → IMAGE
```

## Layer map (the cardinal rule: only CORE may move committed state)

- **CORE** — `world_core` (authoritative trajectory, wraps the sealed AetherPulse kernel).
- **VIEW** — `view_layer` (read-only snapshot → VisualFrame; no write-back).
- **ALLOCATOR** — `temporal_membrane`, `tcff` (decide where/when effort goes; never truth).
- **OBSERVER** — `ghost_report`, `verify`, `render_record`, `conventions`, `divergence`, `prediction`,
  `pfal_bench`, `polygon_reconciliation`, `fidelity_conservation`, `reality_debt`.

## Checklist — built & verified

- [x] **Milestone 1 — foundation + invariant harness.** Renderer proven observer-only.
  - [x] CORE world loop (tick · hash · replay · divergence locator) — `world_core.py`
  - [x] VIEW boundary (read-only snapshot → frame, no write-back) — `view_layer.py`
  - [x] System-classification register; only CORE may mutate — `registry.py`
  - [x] Ghost reporter (6 categories × origins) — `ghost_report.py`
  - [x] Verification harness: replay identity · view-perturbation invariance · ordering invariance — `verify.py`
  - [x] Cardinal invariant holds: committed trajectory byte-identical with VIEW active + corrupted.
- [x] **Milestone 2 — predictive-fidelity architecture + the five laws.**
  - [x] Render Verification Record — features are experiments (TYPE/EFFECT/NON-EFFECT/EVIDENCE) — `render_record.py`
  - [x] Arbitrary-Boundary Law / Boundary Ledger (declared, hashed, `truth_claim=false`) — `conventions.py`
  - [x] Three divergence classes (world / representation / observation) — `divergence.py`
  - [x] Dini-style prediction observer; ghost = max(0, observed − predicted) — `prediction.py`
  - [x] Temporal Prediction Membrane + Temporal Reality Budget (U × C) — `temporal_membrane.py`
  - [x] PFAL R = U×C×P×S + falsification bench w/ negative control — `pfal_bench.py`
  - [x] TCFF F = U×C×P×S×τ proactive + Perceptual Continuity per Joule — `tcff.py`
  - [x] Polygon Reconciliation Law; `reconcile()` not replace — `polygon_reconciliation.py`
  - [x] Temporal Fidelity Conservation Law; transfer is zero-sum — `fidelity_conservation.py`
  - [x] Reality Debt Law; Debt = approx × persistence × consequence — `reality_debt.py`
  - [x] Live loop wiring (prediction → membrane budget → PFAL → TCFF/PCJ → render record) — `loop.py`
  - [x] Docs: `LLM_ON_TRACK.md`, `PREDICTIVE_FIDELITY.md`, `RENDER_VERIFICATION_RECORD.md`, this file.

- [x] **Milestone 3 — VIEW vertical slice + Causal Continuity Hypothesis (provisional).**
  - [x] Causal Continuity *Hypothesis* (NOT a law): allocate ∝ expected future causal loss `U×C×P`; encodes
    the PFAL⇄Reality-Debt duality; promotion gate — `causal_continuity.py`
  - [x] Deterministic reference rasterizer: projection → coverage → sampling → rasterization, each a declared
    convention with a named ghost; content-hashable framebuffer — `raster.py`
  - [x] Cardinal invariant holds under rendering: CORE byte-identical with the rasterizer running every tick.
  - [x] Equal-budget bench + promotion gate (uniform / distance / visibility / PFAL / causal + control) — `raster_bench.py`
  - [x] **Result (recorded, not rigged): the hypothesis is NOT promoted.** Proportional causal loses even to
    uniform — the failure, and its diagnosis, are the deliverable.

- [x] **Milestone 3.1 — the failure becomes a refinement (ranking ≠ allocation).**
  - [x] `representation.py` — RepresentationResistance (the hidden variable: how hard a region is to represent;
    perimeter proxy) and `DebtPressure = RealityDebt × RepresentationResistance`.
  - [x] `allocation.py` — the ranking/allocation split: `rank(priority)` then `waterfill(priority, resistance)`.
    **PFAL ranks · water-filling allocates · Reality Debt constrains.**
  - [x] Re-specified bench: on the future-causal residual metric, two-stage `ranked_waterfill` (756,247,772)
    **strictly beats** uniform (1,063,453,324), distance, visibility, proportional-causal (844,974,909), and the
    drifted control — a **supported** hypothesis on the constructed bench (pending real silicon).
  - Result statement: *importance metrics and allocation functions cannot be conflated; causal importance ranks,
    constrained optimization distributes.*

- [x] **Milestone 4 — stressors + the perceptual axis (extract weaknesses; harden).**
  - [x] `perceptual.py` — Perceptual Continuity Loss (reallocation churn × sensitivity): the measurable
    *success* axis (liability → priority → difficulty → allocation → **continuity**).
  - [x] `policy_arena.py` — dual-axis (causal residual × perceptual continuity) over drifting frames; Pareto
    front. **Mismatch confirmed:** min-causal (ranked_waterfill) ≠ min-perceptual (uniform). Hardening:
    `damped_waterfill` cuts perceptual loss ~5× (22,016→4,228) for ~9% more causal residual.
  - [x] `stress.py` — workbench-style weakness extraction: Goodhart mutation guard (4/4 noticed), WRONG
    adversary (raw consequence broke → expected value), GAMEABLE adversary (self-report captured 68% → repair:
    independent evidence). See [`STRESSORS.md`](STRESSORS.md).

- [x] **Milestone 5 — Transition Debt + adversarial scene generation (the adaptation frontier).**
  - [x] `transition_debt.py` — Total Cost = Representation + λ·Transition (+ Latency). The winner is a
    *function of the exchange rate λ*: ranked (λ<82k) → damped (82k–591k) → uniform (λ>591k); modes are λ
    choices over one world (cinematic→ranked, competitive→damped, vr→uniform). Explains *why* damping works:
    it pays less Transition Debt.
  - [x] `adversarial_scenes.py` — flicker trap / false future / delayed consequence / representation cliff +
    probes. Measured: greedy thrashes flicker (9361 vs 901); priority hoards the false future (15% vs 0%);
    damped LAGS the delayed consequence (26/49 vs 49/49); scalar perimeter resistance MISSES the cliff
    (5.06e6 vs 61,883).
  - **Meta-finding:** damping fixes flicker but causes lag on delayed consequence — *no single damping
    constant wins all.* The right adaptation speed depends on the world's rate of change → adaptive damping /
    multi-horizon is the open frontier. (Answers: what happens when the equation is right but the world
    changes faster than the allocator adapts.)

- [x] **Milestone 6 — the shader cache as validated representation memory (the industrial bridge).**
  - [x] `resistance_tensor.py` — multi-dimensional Representation Resistance (7 dims) replacing the scalar
    perimeter proxy (closes the cliff); `miss_cost` (which paths are expensive to miss) + the **fidelity
    derivative** `∂Fidelity/∂Budget` (marginal utility — the waste-detection signal).
  - [x] `shader_cache.py` — a PSO/shader cache reframed as *validated representation decisions* keyed by the
    conditions that made each safe (material family, geometry class, lighting regime, hardware path, temporal
    stability), content-addressed + replayable. Multi-horizon transition model + fidelity-derivative gate
    drive **prewarm** (where future discontinuity × miss-cost is highest); fallback tiers (impostor / particle
    proxy / procedural) give graceful degradation. Never touches world truth.
  - [x] Bench: predictive 405 vs reactive 559 (−27%); predictive+fallback 315 (−44%); random control 2305.
    PSO hitches become a temporal fidelity-allocation problem, not a reactive hitch source.

- [x] **Milestone 7 — Causal Surface Area + the Representation Readiness Layer (the multiplayer axis).**
  - [x] `causal_surface.py` — **Causal Surface Area** = agents × expected_divergence × representation_cost:
    how many *futures* depend on an object, not how complex it is. The moat, made mechanical: a
    **representation forecast** (prepare destruction assets) is ALLOWED; a **reality forecast** (assert the
    wall breaks) raises `ProphecyViolation`. Multiplayer artifacts route to the right layer (visual snap →
    perceptual ghost; bad hit → CORE/network; missing shader → representation debt). Bench: CSA leaves **0**
    unprepared debt where futures converged vs proximity 287 / visibility 290.
  - [x] `readiness.py` — the **Representation Readiness Layer**: shader cache / geometry streaming / texture
    residency / neural reconstruction / particle fallback / animation decompression / RT structures are one
    problem — *what must already exist before the future arrives?* `readiness = P(needed) × CSA`, gated by the
    fidelity derivative; every preparation routed through `assert_prepared` (prepare ≠ decide). The shader
    cache is one instance.
  - Principle: **the renderer should never become prophetic; it should become better prepared.**

- [x] **Milestone 8 — Causal Contract + Representation Futures Graph (stress-testing the membrane).**
  - [x] `causal_contract.py` — a **map of possible causality** (`affected_by` + `possible_representations`),
    never an outcome. Asserting an outcome (`door will break at tick 400`) raises `CausalAuthorityLeak`. Adds
    **CSA temporal decay** (`temporal_relevance`, `decayed_csa`) — near-future causality expensive, distant
    cheap — fixing the readiness memory-leak (a stale convergence point cools off instead of leaking budget).
  - [x] `representation_futures.py` — the futures graph: state → possible transitions → {representation,
    fallback, readiness cost}. `prepare_branches` prepares **breadth** (several possibilities) by
    `P(transition) × CSA`; `select_future()` is **forbidden** (collapsing to one branch is causal authority
    leakage — only CORE selects). `survive_truth_correction` reframes rollback: a prepared branch survives a
    CORE truth correction with no hitch; otherwise the particle continuity buffer bridges.
  - The moat, mechanical: **the renderer may prepare for possible futures; it may never select the future.**

- [x] **Milestone 9 — shared worlds + dependency access (the fidelity OS for uncertain shared worlds).**
  - [x] `causal_mutation.py` — **Causal Mutation Surface** = authority_distance × affected_agents ×
    rollback_cost × representation_cost. The **Shared Object Crucible** (8-player destructible bridge): winner
    LOSES LEAST when reality disagrees, not best predictor. Under contention, mutation-surface (rollback-aware)
    beats CSA/proximity/visibility (loss 0 vs 3/3/4). Names the four object facets; only `physical` is CORE.
  - [x] `provider_contract.py` — representation providers declare capabilities `{inputs, cost, failure_mode}`;
    `select_provider` picks by contract under a latency budget and degrades along failure-mode chains. Shaders/
    neural/RT/impostor/particles/meshlets become one category (the dependency-contract plugability layer).
  - [x] `dependency_surface.py` — **Dependency Surface Area** (systems coupled to an object's *mutation*) and
    **Preparation Value = Causal Surface Area × Dependency Access**. The hidden resource is dependency access:
    access debt falls 99→62→28→0 as visibility rises; spending access by Preparation Value (5) beats uniform/
    random (50/42). The limit is information topology, not GPU throughput.

- [x] **Milestone 10 — Dependency Integrity Layer + Representation Compiler (trusting the access channel).**
  - [x] `dependency_integrity.py` — dependency access can be corrupted/stale/adversarial (the new seam:
    **access ≠ relevance**). A `DependencyClaim` carries its own doubt {confidence, evidence, expiration,
    consequence}. Three guards (mirroring the workbench's `chronicle`/`quorum`): a **content-hash tautology**
    (unforged iff recompute matches), an **exact-integer k-of-n consensus stream validator** (dissent kept as
    a ghost; consensus ≠ truth), and **evidence × temporal decay** folded into
    `Preparation Value = CSA × Dependency Access × Evidence Confidence × Temporal Relevance`. The **Dependency
    Fog Crucible** (hidden / false / stale) shows integrity-aware loses least.
  - [x] `representation_compiler.py` — provider contracts become compositional: a pipeline of geometry +
    lighting + motion + continuity stages. `compile_pipeline` lowers a desired representation onto the
    **cheapest chain that preserves continuity** under a latency budget, reserving each later stage's cheapest
    tier (continuity downgrades, never drops). Closer to a compiler than a renderer.
  - Invariant: the renderer may consume dependency information, but it must know how stale, uncertain, and
    expensive that information is.

- [x] **Milestone 11 — Causal Access Control Layer + Capability Token (the information firewall / anti-cheat floor).**
  - [x] `capability.py` — a **Causal Capability Token** `{what, subject, scope, horizon, source, cannot}`
    authorizes USE of dependency knowledge for a bounded purpose; `mutate / select_outcome / reveal_hidden /
    grant_authority` are forbidden on every token by construction. The question becomes "am I permitted to use
    this, and only for this purpose?", not "is it true?".
  - [x] `causal_access.py` — the information firewall: a claim may influence an observer's representation only
    if (1) unforged, (2) within the observer's **authorized causal scope**, and (3) capability-permitted. The
    **Dependency Fog Attack** shows the decisive result — a fabricated "hidden enemy" claim PASSES the
    content-hash tautology AND a colluding consensus, yet **advantage leaked = 0** because it is out of scope
    (wallhack/ESP blocked). Integrity and consensus are necessary, not sufficient; authorization is the floor.
  - Invariant: CORE owns reality · dependencies expose possibility · capabilities constrain interpretation ·
    representation consumes permissioned uncertainty. (authorized ≠ true; consensus ≠ truth; integrity ≠ truth.)

- [x] **Milestone 12 — Causal Composition Firewall + side-channel defenses (the reconstruction boss fight).**
  - [x] `reconstruction.py` — a cheat needs only enough *authorized* fragments to RECONSTRUCT the forbidden
    fact (shadow + sound + particle + animation → enemy). **Information Reconstruction Debt** measures the
    reconstruction beyond a safe threshold; the **Causal Composition Firewall** caps it (blocks the marginal
    fragment, not the piece). Crucible: naive per-fragment reconstruction 1.00 (full leak) → firewalled 0.31.
    The chain: integrity ≠ confidentiality ≠ authorization ≠ harmlessness.
  - [x] `side_channel.py` — the renderer's own behavior as a sensor: **timing normalization** (7 ms spread →
    0), the **prediction-inversion guard** (prepare breadth ≠ announce probability; 1 branch leaks 100, 4
    leak 25), and **weighted-trust consensus** (evidence × authority × reliability × validity, not headcount —
    8 colluding clients lose to 3 honest+server, trust 136 vs 0). consensus ≠ truth.

- [x] **Milestone 13 — Accumulation Safety (the query is allowed, the SEQUENCE is not).**
  - [x] `accumulation.py` — after M12 the anti-cheat problem becomes *information economics under adversarial
    constraints*; the subtlest attacker is **maliciously honest** (every request legal, the attack is in the
    aggregation). Four mechanisms: (1) **Temporal Reconstruction Debt** — M12's Reconstruction Debt gains
    MEMORY so 500 frames of per-frame-harmless fragments are caught as history-compression (5 bits/frame,
    accumulated debt **0.50**); (2) **Representation Privacy Budget** per observer×object — hidden enemy 0,
    visible door ∞, destructible wall limited; the *combination* trips, not the piece (0.6 + 0.6 > 1.0);
    (3) **Causal Query Rate Limiting** — each query legal, the accumulation throttled (first 50 allowed, then
    capped); (4) **importance ≠ exposure** — the allocator may internally know "this matters" without
    changing observable behavior, so its own spend can't fingerprint hidden importance ({10,90} → one
    external level). allowed-query ≠ allowed-sequence; authorized ≠ harmless; integrity ≠ truth.

- [x] **Milestone 14 — Adversarial Information Dynamics (the DEFENSE is the leak).**
  - [x] `adversarial_dynamics.py` — the anti-cheat problem stops being "stop bad data" and becomes "stop
    systems from inferring hidden state through the system's own behavior." Five mechanisms, each with a
    negative control: (1) **Reaction Debt** = observer_change × inference_value × persistence — a defense
    that reacts only near the secret (fog spikes, LOD drops) leaks via the discontinuity; a reaction
    *uncorrelated* with the secret leaks **0** (naive 54 vs safe 0). (2) **Absence firewall** — the
    negative-space attack ("I noticed something MISSING"); Absence Signal = expected − observed; missing ≠
    informative unless entitled, else the suppression masks its own gap (naive 10 → masked 0, entitled 10).
    (3) **Distributed Reconstruction Debt** — a colluding GROUP is a distributed sensor; each observer below
    threshold (3 × 20 bits) but the union reconstructs **0.94**, capped to **0.31** by the cross-observer
    firewall. (4) **Adaptive ≠ random** — a fixed distribution is averaged out (200 over 20 probes); an
    adaptive boundary that moves on observed probing yields **27**. (5) **The ultimate invariant** — a
    representation may reveal CONSEQUENCES (explosion, damage, motion, sound; only at/after the committed
    event) but never the MECHANISM by which hidden state becomes predictable (why-before-event, prepared
    branch). The anti-wallhack floor. reaction ≠ disclosure; absence ≠ information; consequence ≠ mechanism.

### Milestone-3 finding (the failure is the result)

The Causal Continuity Hypothesis as *stated* (allocate ∝ U·C·P) **failed** the equal-budget bench. Diagnosis
(itself falsifiable, and verified by the diagnostic allocators in `raster_bench.py`):

1. The consequential edge-error metric (`Σ C·perimeter/samples`) is **convex** in samples, so *proportional*
   allocation over-concentrates and loses to uniform.
2. The optimal weight must include the **error's own structural term** (size/perimeter), which `U·C·P` (and
   PFAL's `U·C·P·S`) omit.

Measured (seed=1, budget=400): proportional causal **2,147,735** > uniform **1,684,339**; water-filling causal
`√(U·C·P)` **1,641,016** (marginal win); size-aware optimum `√(C·perimeter)` **1,427,556** (clear win). The
re-specification — *water-filling form + include the error's structural term* — is the next hypothesis to test
before any promotion. Failure kept as architectural information.

## Measured (constructed-world; honest bounds)

| Result | Number | Status |
|---|---|---|
| Milestone-1 invariants (replay / view-perturbation / ordering) | all pass | proven on the AetherPulse kernel |
| PFAL vs distance/visibility (failure-cost covered, equal budget) | 0.897 vs 0.046 | constructed-world hypothesis |
| PFAL negative control vs uniform floor | 0.501 < 0.587 | bench can falsify (Goodhart guard) |
| TCFF vs PFAL vs reactive (Perceptual Continuity per Joule) | 0.287 / 0.245 / 0.105 | constructed-world hypothesis |
| Conservation objective swap (consequential discontinuity, equal budget) | 7 vs 30 | declared-budget accounting |
| Reality-debt placement (consequential debt, same approximation) | 72 vs 456 | declared accounting |

**Every bench number above is a constructed-world result and `expires_if` measured on real GPU silicon.** A
benchmark measures the benchmark's world; it does not prove universal superiority.

## Not yet built (honest)

- [ ] **Re-specified Causal Continuity** — water-filling form (∝ √weight) + a weight that includes the error's
  structural term (size/perimeter); re-run the gate. Only then is promotion on the table.
- [ ] Real-silicon benchmark: PFAL/TCFF at equal GPU time, measuring temporal artifacts, input-to-photon
  latency, reconstruction error, and motion stability (the numbers above expire here).
- [ ] Native (C++/Rust) port validated against the Python reference via conformance vectors.
- [ ] Multi-lens presentations (cinematic / competitive / VR / handheld / debug) over one committed world.

## Verify locally

```bash
PYTHONHASHSEED=0 python3 tests/test_ursprung.py     # unit suite
PYTHONHASHSEED=0 python3 loop.py                    # live loop + milestone + benches
```
