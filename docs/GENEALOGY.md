# Ursprung — genealogy & checklist (thus far)

The engineering lineage of Ursprung: what was built, in what order, which law it established, how it was
verified, and its honest bound. Modeled on the workbench's `GENEALOGY.md`. `integrity ≠ truth` throughout.

## The five laws (the philosophy layer)

```
Reality Debt Law          (underneath)  every approximation incurs debt ≈ approx × persistence × consequence (a model)
   └─ Arbitrary-Boundary Law            representation choices are deterministic conventions, not truth
   └─ Predictive Fidelity Law (PFAL/TCFF) spend where future failure cost is highest (U·C·P·S·τ, a weighting model)
   └─ Polygon Reconciliation Law        keep polygons iff declared abandonment cost ≥ approximation error
   └─ Temporal Fidelity Accounting      fixed-budget transfer (a bookkeeping model, not physical conservation); minimize consequential discontinuity
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
  - [x] PFAL R = U×C×P×S (a weighting model) + falsification bench w/ negative control — `pfal_bench.py`
  - [x] TCFF F = U×C×P×S×τ proactive + Perceptual Continuity per Joule — `tcff.py`
  - [x] Polygon Reconciliation Law; `reconcile()` over declared costs, not replace — `polygon_reconciliation.py`
  - [x] Temporal Fidelity Accounting Law (was "Conservation"); transfer is a fixed-budget bookkeeping model — `fidelity_conservation.py`
  - [x] Reality Debt Law; Debt = approx × persistence × consequence (a bookkeeping model) — `reality_debt.py`
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

- [x] **Milestone 15 — Representation Privacy / Ambiguity Control (`image ≠ generator`).**
  - [x] `representation_privacy.py` — once the system *intentionally* manages uncertainty, the management can
    become a signal; the final attack infers not the hidden object but the **generator** (the rule mapping
    hidden state → representation: "streaming stalls ⇒ enemy near"). The refinement of `consequence ≠
    mechanism` into `image ≠ generator`. Five mechanisms with controls: (1) **Ambiguity Debt** — an invertible
    uncertainty radius is a ruler (debt **9.09**, 11 recoverable levels) vs a coarse exposure (**0.00**, 1
    level); (2) **Representation Hysteresis** — a single threshold oscillates (**10** flips, probe-able) vs an
    enter≠exit band (**1** flip), the shader-stability fix applied to security; (3) **decoy without reality
    mutation** — fake REALITY forbidden (CORE cannot lie), fake OBSERVABILITY PATTERN admissible; (4)
    **Observer Fingerprint Debt** — uncaused per-observer policy variance leaks the rules (**40** vs **0**),
    extending `importance ≠ exposure` to `observer behavior ≠ representation policy`; (5) **`image ≠
    generator`** — expose world facts, never the implementation tells correlated with hidden state. **Honest
    bound:** these are structural proxies, not a cryptographic guarantee; the formal form of `image ≠
    generator` is **Indistinguishability Obfuscation** (Goldreich-Levin hard-core predicates, LWE / discrete-log
    hardness) — this is its *shape*, not its *proof*. ambiguity ≠ deception; image ≠ generator; integrity ≠ truth.

- [x] **Milestone 16 — Execution Surface Privacy (`observable cost ≠ hidden state`).**
  - [x] `execution_surface.py` — the boundary condition the stack converged on: you can protect information
    flow, but a renderer is a PHYSICAL PROCESS and the process is observable. The attacker stops asking "what
    is hidden?" and asks "what does the renderer *struggle* with?" Where M6 (shader cache / transition debt)
    and M15 (privacy) fuse — the industrial bridge is the physical implementation of the security model. Five
    mechanisms with controls: (1) **Transition Signature Debt** — Signature = Δ(latency, cache, memory,
    bandwidth, shader_state); on-demand streaming spikes for the secret (debt **13**), pre-preparation does
    not (**0**); (2) **Cache Side-Channel Budget** — a hit/miss is a message; prepare by allowed policy not
    by hidden-state visibility (exposure **1 → 0**); (3) **semantic constant-time** — world A (enemy exists)
    vs B (does not) must not be separable from behavior (on-demand classifier accuracy **1.0** → prepared
    **0.5**, chance); (4) **three-currency objective** — the safest renderer may look wasteful because
    *unused* preparation is cheaper than an *observable* preparation event; counting leakage flips the
    cheapest plan from `min_gpu` to `over_prepared` over the SAME two plans (old GPU-only objective vs new
    fidelity+transition+leakage); (5) **renderer ≠ oracle** — a client may observe the world, never the
    machinery by which hidden state becomes observable. **Honest bound:** declared cost-vector / separability
    proxies, not a measured micro-architectural channel; on real silicon leakage is continuous (cache lines,
    DVFS, bus contention) and these integer signatures collapse to noise. observable cost ≠ hidden state;
    renderer ≠ oracle; integrity ≠ truth.

- [x] **Milestone 17 — Convergence Surface / Distributed Reality Reconciliation (`correction ≠ cause`).**
  - [x] `convergence.py` — the dual of M10–M16: the system can hide information, but it must survive
    DISAGREEMENT. Two legitimate observers hold different partial realities (A predicted state A, B predicted
    state B, server committed C) and must converge without the convergence leaking. Normal engines snap →
    replay, but the stack made snapping suspicious (correction magnitude leaks hidden state, timing leaks
    causality, objects corrected reveal dependencies, rollback cost reveals expensive futures). New currency:
    **Convergence Debt** = the observable cost of making multiple private representations become one reality.
    Four mechanisms + invariant: (1) **Reconciliation Signature Debt** — an exact rollback distance is
    invertible (**41** distinguishable states) vs a bounded family {none,small,medium,large} (**4**); (2)
    **Divergence Firewall** — an unentitled client learns "world changed" (**1** field) not "…hidden collision
    37 m away, entity 184" (**4**); M14 was many-observers→fact, this is disagreement→fact; (3) **Convergence
    Readiness** — the M7/M9 question turns to "what makes the CORRECTION cheap?"; a prepared representation
    absorbs the rollback (debt **0**) vs an unprepared spike (**39**); (4) **Distributed Correction
    Reconstruction** — a fleet of honest clients comparing their own corrections is a distributed microscope;
    each safe (4 × 15 bits = 0.23), union reconstructs **0.94**, firewalled to **0.47**. **Invariant
    (`correction ≠ cause`):** a correction may reveal THAT reality changed, never WHY/WHERE/WHO — `consequence
    ≠ mechanism` and `image ≠ generator` on the convergence axis. M16 foreshadowed this: a shader hitch is a
    *local* correction, a rollback a *temporal* one — both are "reality had to be repaired." **Honest bound:**
    correction-distance / bit / fragment proxies, not measured netcode under real latency/jitter/loss;
    convergence is only meaningful against REAL divergence — the first layer in the arc that cannot be
    validated with constructed numbers. correction ≠ cause; convergence ≠ disclosure; integrity ≠ truth.

- [x] **Milestone 18 — the Reality Harness (`traffic produces the hypothesis`).** *The method inverts.*
  - [x] `reality_harness.py` — M1–M17 were "bench proves hypothesis"; M17 exposed the limit (convergence is
    only meaningful against real divergence). M18 is not another defense — it is the measurement substrate:
    an authoritative server (CORE-driven), a SIMULATED `NetworkChannel` (latency/jitter/loss, deterministic,
    seeded), and client mirrors that predict → diverge → reconcile. It MEASURES correction entropy,
    convergence time, observer distinguishability, info-per-correction, counterfactual bits, aggregate
    extraction, and fidelity cost across reconciliation policies, and lets the numbers fall where they do.
    **Produced (not asserted) finding:** bucketing (M17) cuts correction entropy **1.76 → 1.36** but
    distinguishability stays **1.0** — it hides *magnitude*, not the *existence* of disagreement; a
    cover-correction floor (a Convergence Privacy Budget) lowers distinguishability to **0.6** but raises
    fidelity cost **18 → 28**, and large corrections still leak. So **convergence-privacy ⟂ convergence-fidelity
    is a measured frontier, not a win** — the traffic-derived form of the user's proposed equivalence-classes /
    privacy-budget refinements, *and their limit.* **The swappable seam:** `NetworkChannel.delay_for` is the
    one model boundary; replace it with a real socket's RTT and the harness becomes the real experiment,
    unchanged above that line. **Honest bound:** the network is SIMULATED (Arbitrary-Boundary: a model, not the
    network); measurements are measured-from-simulation — the MODE changed (traffic-driven, reproducible), the
    proof has not. simulation ≠ physics; integrity ≠ truth.

- [x] **Milestone 19 — the Behavioral Reality Harness (`the last observer is the player`).**
  - [x] `behavioral_harness.py` — M18 forced the distinction between a representation policy and an
    information-flow guarantee, but it was still passive and collapsed leakage into scalars. M19 closes three
    gaps and names the final observer. (1) **Convergence Leakage Vector** — privacy is not a scalar; magnitude
    / existence / timing / correlation / aggregation are independent axes (mirroring the M6 resistance
    tensor). The vector makes a produced finding explicit: bucketing closes *magnitude* but not *existence*,
    and **no M17/M18 policy ever touched the *timing* axis** — only a timing-normalized policy (M16, folded
    in) closes it. A scalar (floor 3.4 < bucketed 4.4) would have hidden that. (2) **Counterfactual
    Amplification** — a passive client cannot localize the server's hidden boundary (uncertainty **100**); an
    adversary that *chooses* its inputs binary-searches it to near zero (**0.006**). `Counterfactual Debt =
    correction_information × probe_control`; one bit × 10⁴ chosen experiments is a query oracle (M13, where
    the query is now a *world perturbation*). (3) **The experiment-layer seam** — one measurement API over a
    SIMULATED channel (deterministic, replayable → regression) and a REAL channel (UDP/TCP/QUIC → validity);
    the simulator becomes the regression bed, not discarded. **The final observer:** a player need not infer
    the enemy mathematically — they learn the *policy by feel* ("my shots behave differently behind cover"),
    which is `image ≠ generator` at the gameplay layer; the last firewall is behavioral indistinguishability
    (constant-feel). **Honest bound:** the axes / probe model / behavioral "classifier" are declared proxies,
    not a learned adversary, a real player, or a real socket; the real channel is intentionally unbuilt
    (reports unavailable). privacy ≠ scalar; image ≠ generator; simulation ≠ physics; integrity ≠ truth.

- [x] **Milestone 20 — the Adaptive Adversary Harness (`can an intelligent observer learn the system?`).**
  - [x] `adversary_harness.py` — M19's observer was one-shot; M20 closes the loop, because a player is not a
    passive recipient but an active EXPERIMENTER. The attacker model becomes a learning problem (`policy →
    observe → infer → choose next experiment → exploit`); the player learns the *transfer function*, not a
    fact. The harness builds the loop (world → policy → adaptive agent → observation → memory → new strategy →
    world) with a probing `AdaptiveObserver` (belief interval + active experiment selection = max-information
    bisection + memory), and measures, per policy: **regret / learning curve**, **Behavioral Leakage =
    information_gained / experiments** (leakage from *strategies*, not frames), **incentive / decision-channel
    leakage** (hit-reg, movement prediction, audio occlusion, matchmaking, AI behaviour — the action economy,
    not pixels), and an **extraction bound**. **Produced result:** against a naive policy the learner localizes
    the hidden boundary in O(log N) (regret **128 → 1**, below the bound); against M19's **constant-feel** the
    regret stays pinned (**≈399, flat**) no matter how many chosen experiments it runs — constant-feel
    *withstands a learning adversary*, which is the test that separates "secure" from "looks secure." **Honest
    bound:** the agent is a 1-D active-threshold learner; constant-feel resists THIS observer class — a real ML
    agent or human may model channels outside it. The agent, channel, and player are all still simulated.
    secure-against-this-observer ≠ secure; learning ≠ truth; simulation ≠ physics; integrity ≠ truth.

- [x] **Milestone 21 — Adversary Information Capacity (`security = non-identifiability under bounded access`).**
  - [x] `adversary_capacity.py` — takes M20's own warning (*secure against THIS observer class ≠ secure*) and
    makes it the experiment: it does not add a defense, it VARIES THE ADVERSARY and watches what becomes
    identifiable. It splits the blurred target into two — the **secret** (the hidden boundary T) and the
    **generator** (the rule mapping hidden state → behaviour) — and sweeps a lattice of adversary classes
    (Adversary Information Capacity = hypothesis-space richness, *not* probes/bandwidth/memory): C0 passive ·
    C1 threshold (M20's bisection agent) · C2 single-bit · C3 structured (threshold ∪ single-bit ∪ parity).
    Every cell is computed by an actual little learner. **Produced results:** (1) constant-feel's **secret** is
    non-identifiable under *every* class — the policy severs T from the channel, so no learner, however rich,
    can extract what was never transmitted (information-theoretic, AIC-independent — the **only absolute
    guarantee in the stack**); (2) constant-feel's **generator** is invisible to C1 (M20's learner could not
    express it) but **identified by C2/C3** (a structure learner names the rule — "keys off bit 3") — so M20's
    "resists learning" was always **class-relative**; (3) the classes are **incomparable** (C1 cracks the
    threshold rule not the bit rule; C2 the reverse) — **AIC is a lattice, not a scalar**; only C3 dominates,
    and a parity-keyed rule needs C3. **The synthesis the whole arc was building toward:** secret-privacy can
    be made **absolute** (sever the secret from the channel); generator-privacy is **only ever class-relative**
    — for any finite rule a rich enough class identifies it (`image ≠ generator` can be bounded, never
    guaranteed). **Honest bound:** a tiny illustrative lattice; a real ML agent/human occupies an unknown,
    far richer class; the "absolute" secret result holds only for a channel that genuinely omits T — any
    correlated side effect in a real engine breaks it. identifiability ≠ truth; secure-against-class ≠ secure.

- [x] **Channel Discovery (a harness feature, not a law) — `what channels EXIST?`** *the bridge to the empirical phase.*
  - [x] `channel_discovery.py` — M21 reduced anti-cheat to "can hidden state influence an observable?", but
    that guarantee is only as good as the list of channels you thought to check. M20's bit-7 slip was a bug in
    the model of the *observer*; the dual bug is in the model of the *world* — the channel you never
    enumerated. This inverts the harness question from "does channel X leak?" to "what channels exist, and
    which carry information about the secret?": it scans an observable trace (latency, frame_time,
    packet_timing, correction/resource/audio/animation events), computes **mutual information** I(channel ;
    secret) per channel, ranks, and flags the leakers. **Produced result:** the clean channels read as severed
    (I = **0.000** → M21's class-independent absolute guarantee), `correction_events` fully reveals (I ≈ **0.95**
    = H(secret)), and — the headline — an **unmodeled channel** (`animation_events`, I ≈ **0.27**, a partial
    leak) is discovered *outside* the modeled audit set: an audit of only the enumerated channels would have
    PASSED while the system bled. The dangerous channel is the one you didn't list. I = 0 ⇒ severed ⇒ absolute;
    I > 0 ⇒ the leak is real and is handed to the adversary class (`adversary_capacity`), where exploitability
    is class-relative. **A negative control caught a modeling error mid-build:** the first `animation = secret
    XOR block_parity` was a one-time pad (I = 0, *perfectly* severed — the opposite of a leak); `secret OR
    block_parity` gives the intended partial correlation. **Honest bound:** discrete MI over a constructed,
    deterministic trace — by definition discovery cannot find a channel the *trace* omits; on real silicon the
    channels are continuous, coupled, and MI must be estimated with error. Absence of evidence here ≠ evidence
    of absence on real hardware. measurement ≠ truth; simulation ≠ physics; integrity ≠ truth.

> **Status after M21 — the model has formalized its own success condition.** The progression reads as one
> question per milestone: M10 *trust?* · M11 *may I use it?* · M12 *reconstruct?* · M13 *accumulate?* · M14
> *learn from the defense?* · M15 *infer the generator?* · M16 *infer the machine?* · M17 *infer reality from
> correction?* · M18 *can measurement replace assumptions?* · M19 *who is the final observer (the player)?* ·
> M20 *can an intelligent observer learn the system?* · M21 *learnable by WHICH class of observer?* The arc
> resolves to a single primitive — **security = non-identifiability under bounded experimental access** — with
> a sharp split: **sever the secret from the channel for an absolute guarantee; everything else (the
> generator, the machine, the convergence) is only ever non-identifiable relative to an adversary's model
> class.** The harnesses (M18/M20/M21) are **substrate, not law**; another firewall would be decorative. The
> remaining work is empirical, behind intentionally-unbuilt seams: `reality_harness.NetworkChannel` and
> `behavioral_harness.ExperimentLayer(channel="real")` (real socket / netcode), the adversary upgraded from
> these toy learners to a real ML class, telemetry, and human studies. The question is no longer "what law is
> missing?" but "which of the twenty-one milestones survive contact with real latency, GPUs, drivers,
> learners, and players?"

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

- [x] **Re-specified Causal Continuity (constructed gate PASSED → `supported_constructed`)** — the
  water-filling form (samples ∝ √(U·C·P · resistance), the structural term included) re-ran the gate
  (`promotion_gate.py`, seeds 1..8) and strictly beats uniform, distance, visibility, **PFAL**, and the
  structural-only optimum on the future-causal residual, with the negative control losing. Decisive: it beats
  PFAL (dropping present-perception S helps the future-causal objective) and beats structural-only (the causal
  weight adds value beyond geometry). *Promotion to a LAW is NOT granted — that needs the real-silicon
  benchmark below; the candidate is the analytic optimum of the declared objective. `declared ≠ verified`.*
- [ ] **Causal Continuity → LAW** — requires the real-silicon benchmark (next item): does future-causal
  allocation reduce *real perceived* error, not just the declared residual? Only then does `supported_constructed`
  become a law.
- [ ] Real-silicon benchmark: PFAL/TCFF at equal GPU time, measuring temporal artifacts, input-to-photon
  latency, reconstruction error, and motion stability (the numbers above expire here). **Plan fixed** in
  [`REAL_SILICON_BENCHMARK.md`](REAL_SILICON_BENCHMARK.md) — device = constrained oracle (run-provenance
  recorded), GPU-timestamp budget = the shared ruler, provenance kept off the frame path, temporal error is a
  Pareto *profile* not a summed score, three harnesses (fidelity / latency / thermal) + reproducibility.
  Substrate ≠ benchmark. **Contract core built + verified (no GPU):** `experiments/bench_gpu/` (9/9) —
  RunRecord (UNACCOUNTED without provenance), Pareto profile (no scalar collapse), equal-GPU-tick guard, and
  the `RealBackend` seam that raises rather than fakes. **Seam plumbing also built + verified (8/8):**
  `frame.py` (FrameArtifact + backend-agnostic GoldenReplay), `timing.py` (GpuInterval = the ruler · CpuTiming
  = provenance · LatencyProfile = separate instrument), `backends.py` (ReferenceBackend no-pixels +
  RealGpuBackend seam). **`observation.py` added (11/11):** `BenchmarkObservation` binds artifact_digest ·
  run-provenance · backend · gpu_budget · gpu_interval · temporal_profile · provenance (+ optional latency) —
  `TemporalErrorProfile without a BenchmarkObservation = UNACCOUNTED`; GPU budget is an execution condition,
  not frame identity; provenance can't be a bare label; the image hash is a receipt, not the lineage. The only
  thing left is the `RealGpuBackend` body (Vulkan/DX12/wgpu submit + GPU timestamp queries + present-to-photon)
  on device — deliberately boring; no new theory. **Milestone 1 DONE — verified on real silicon:**
  `experiments/bench_gpu_real/` (wgpu 22.1, Vulkan) ran on the ASUS ROG Xbox Ally X (Radeon 890M, RDNA 3.5):
  the GPU-interval ruler EXISTS and is monotonic (`end > begin`), timestamp period 10 ns/tick, empty-pass
  interval 40 ns (bracket overhead, not work, not fidelity). The project's first datum that did not expire on
  silicon. **M2 DONE — the ruler measures real work (Ally X):** a trivial WGSL compute LCG timed across 3
  workload sizes (7 runs each) scales 880 ns → 30760 ns (overhead-bound small end, ~linear large end),
  emitted as the contract-shaped `BenchmarkObservation` JSON; the 1M `min 6720` outlier recorded as a
  measurement ghost (median used, never min — `timing is an event`). Still no FPS/PFAL/TCFF claim. **M3 DONE — measurement
  bound to world identity (Ally X):** a `GoldenReplay` derives a `FrameArtifact` (digest 4f1cb7c2495167e7);
  12 runs of one frame → identities seen 1, timing varies 9600–11720 ns. A REAL ghost fired — run 1 returned
  a zero interval (cold-start timestamp), flagged `NonPositive`, excluded from stats, identity intact: a ghost
  changes the number, never the digest (the Q2 handling firing on a genuine anomaly). 6/6. **M4 DONE —
  render-pass timing under the SAME contract (Ally X):** a headless fullscreen-triangle render pass
  (offscreen 1080p, frag loop ×64) timed via `RenderPassTimestampWrites` (in-pass path, no fallback) →
  ~0.7–0.9 ms, 12 runs one identity, a real ghost again excluded. Digest IDENTICAL to M3's compute run
  (4f1cb7c2495167e7) — same GoldenReplay → same world identity whether compute or render: identity is the
  world's, not the pass's. 7/7. **M5 DONE — equal-budget comparison is FAIR (metrology, Ally X):** two
  allocation policies that are PERMUTATIONS of one effort multiset measure the same GPU-tick budget
  (391668 vs 391688 ticks, 0.005% apart) → admitted and compared as a Pareto vector (A dominates B on a
  declared synthetic error model — NOT a fidelity claim); a cheat with a larger effort sum measures ~1.4×
  (548156 ticks) → budget_violation → comparison REFUSED. Published rule: ±20% of target measured ticks,
  policy-independent. 7/7. No policy declared superior — that is M6. **M6a DONE — a fair PERCEPTUAL ruler (apparatus, Ally X):**
  against a frozen 256-sample SSAA reference, a lower-sample approximation's error is measured as a
  policy-neutral, blind VECTOR — pixel (0.0098/0.0050/0.0027 at S=4/16/64, monotone) / structural / temporal;
  negative control (ref vs ref) = 0.000000; reproducibility 0.000039; identity preserved (sample budget is a
  condition, not identity); ghost handling intact (warm-up + cold-start zero interval flagged/excluded, pixels
  unaffected); explicit limits stated. 7/7. **No policy declared superior** — that is M6b. **M6b DONE — the
  Causal Continuity gate, and it (partially) FALSIFIED the hypothesis on a neutral ruler (Ally X):** six
  policies (uniform/distance/visibility/PFAL/causal-waterfill/drifted) allocate a per-tile sample budget from
  DECLARED priors only — the policy signature `fn(&TilePriors,u32)->Vec<u32>` cannot see pixels/reference/
  ground-truth, so Goodhart is structurally unrepresentable (the sealed-observer invariant is enforced by the
  type boundary, not a comment). Equal budget (1024 samples ≈ 16/tile); ε-dominance with ε measured from the
  data (pixel/struct/temporal 0.000083/0.000133/0.000090). RESULT: **uniform ε-dominates causal-waterfill in
  BOTH scenes** — aligned (priors track difficulty): causal ties on pixel/struct (<ε) but is measurably WORSE
  on temporal stability (0.00014 > ε); adversarial (priors anti-track): causal worse on every axis (~28%).
  Causal allocation showed NO measured upside at any alignment and a temporal downside that grows under
  misalignment — asymmetric, downside-only. This partially falsifies the constructed gate's blessing (its
  metric was U·C·P-weighted/circular; a neutral metric removes that). `causal_continuity.STATUS =
  unsupported_on_neutral_ruler`. Honest ceiling: one device/scene/budget — at ~16 samples/tile every tile is
  near-converged, so there is little to reallocate; the variance-optimal SSAA exponent is ∝ difficulty^(2/3)
  while causal weights ∝ difficulty (likely OVER-concentrates). Open ghost → M6c: an alignment×budget sweep,
  to find whether a LOWER budget (unconverged tiles) ever lets causal reach the frontier. `benchmark gain ≠
  universal` — and neither does a benchmark loss. **M6c DONE — the sweep REFINED M6b's flat loss into a
  measured boundary (Ally X):** swept prior_alignment α∈{+1,+0.5,0,−0.5,−1} × budget∈{2,4,8,16,64} avg
  samples/tile, running TWO causal exponents side by side — causal_d1 (∝difficulty^1, the M6b policy) and
  causal_d23 (∝difficulty^(2/3), the VARIANCE-OPTIMAL SSAA exponent) — vs uniform + drifted, sealed policies,
  per-cell ε-dominance. (1) WRONG EXPONENT: causal_d1 over-concentrates — on the ε-frontier only at b2, else
  dominated, usually by causal_d23; M6b's loss was largely a wrong-exponent artifact. (2) GENUINE NARROW WINS:
  at α=+1, causal_d23 is the SOLE ε-frontier member (ε-DOMINATES uniform) at b8 & b64 — b8/α+1 clears ε on all
  three axes (pixel .00009>ε.00005, struct .00046>ε.00014, temporal .00008>ε.00005), real though sub-1%. (3) NO
  ROBUSTNESS MARGIN: at α≤0 uniform ε-dominates everywhere — the allocator can't tell its priors are wrong.
  GHOSTS kept: a non-monotonic b4 dip (d23 loses b4, wins b8 — likely Hamilton rounding × convergence curve),
  and a b2 scatter regime (even drifted reaches the frontier via tradeoffs — weak evidence at extreme
  scarcity). NET: the STRONG claim ("causal generally beats uniform at equal budget") stays FALSIFIED; a
  CONDITIONAL claim is SUPPORTED on silicon — causal helps only with informative priors AND the matched
  concentration exponent. `causal_continuity.STATUS = conditional_on_neutral_ruler`. A measured boundary, not
  a law. The apparatus did its job: the policy was allowed to lose, then to win narrowly, and the ruler told
  the difference. `benchmark gain ≠ universal`, and neither does a benchmark loss. **M6d/T1 DONE — the TEMPORAL
  apparatus, on the RealityKernel (Ally X, 7/7, apparatus no verdict):** M6a–M6c were single-frame and so only
  tested allocation vs *present* render difficulty; the ORIGINAL Causal Continuity claim is about *future*
  consequence (drop present-perception S; spend now to cut error LATER), which needs a world that EVOLVES. T1
  builds + verifies the apparatus first (M6a discipline). The world (an occlusion edge sweeping the tile grid)
  runs THROUGH the kernel: each frame is a `reality_core::Event` committed by `Core::apply`, chained by
  `requires` (frame t requires frame t−1's digest) — so this is also the **first world-loop client** (kernel
  carries a world; replay-identity + lineage now operate across TIME). The present≠future decoupling is
  EMERGENT not declared (a tile is cheap before the edge reaches it, expensive after) — the sealed-observer
  rule lifted into time. 7 checks, no policy: world_evolves (8 distinct states); temporal_replay_identity
  (commit-digest chain byte-identical across 2 runs, head 34d29a70…); commit_path_severance (orphan transition
  on an uncommitted prerequisite REFUSED, legit chain refused 0); future_reference_reproducible (frame-5 hi-fi
  render reproduced bit-identically across 2 calls UNDER THE TESTED STACK, RDNA3.5/AMD-Vulkan/release — an
  implementation result, no ε needed *here*; NOT elevated to a portability claim, the scientific claim is only
  reproducibility-under-stated-conditions); temporal_error_measurable
  (future-frame err @4spp 0.01368 > @64spp 0.00376 > 0); present≠future_decoupling_exists (24 tiles easy@T0=2
  hard@frame5, emergent); identity⟂render_budget (commit chain unchanged by rendering at 2 budgets; T0 lineage
  resolves — compress≠sever). reality_core wired as a path dep into bench_gpu_real (first cross-crate use; built
  clean). **M6d/T2 DONE — the TEMPORAL RULER (Ally X, 5/5, apparatus no verdict):** builds the future-error
  ruler T3 will score policies on, and proves it fair first (M6a discipline in time). THE COUPLING MODEL is a
  DECLARED boundary condition, NOT "the temporal law": TAA-style history accumulation + explicit DISOCCLUSION
  INVALIDATION — a tile's samples accumulate across frames while content is stable and RESET the frame content
  changes (edge passes). Chosen (user) as the *weakest* coupling still real in renderers: present work can
  survive, history can become wrong, future benefit is earned not assumed, emerges from scene dynamics not
  oracle foresight. Rendering analogue of the project's recurring lesson (carried info has a cost, valid only
  until assumptions change; disocclusion reset ≈ provenance invalidation; compress≠sever in time). `declared ≠
  verified` — the claim is scoped: "future consequence is measurable UNDER THIS model," not a temporal law. KEY
  ISOLATION (check 4): future_penalty = err(tf | accumulation WITH disocclusion resets) − err(tf | WITHOUT),
  same future content+budget → measures exactly the cost of history becoming invalid. 5 checks: future_error_
  monotonic (err @b2 0.01165 > @b8 0.00599 > 0); negative_control_zero (ref vs ref 0.000000); reproducibility_
  floor (ε=0.000053 across 4 seeds); temporal_sensitivity (emergence penalty 0.00169 ≈32× ε vs static EXACTLY
  0.000000 — the ruler distinguishes present error from future consequence WITHOUT looking inside any policy);
  identity_preservation (same kernel world-history, 6 commits → identical future reference). Also (this turn)
  SOFTENED the T1 bit-exact language across README/GENEALOGY/memory per user caution: bit-exact replay is an
  implementation result under the tested stack (RDNA3.5/AMD-Vulkan/release), NOT a portability/scientific claim;
  the claim is reproducibility-under-stated-conditions. NEXT: T3 — the temporal causal gate: uniform/PFAL/
  causal_d1/causal_d23/controls allocate the per-frame budget (sealed observer, present priors only) under EQUAL
  measured budget, scored on THIS temporal ruler against FUTURE references — does spending NOW measurably reduce
  FUTURE error, and for which policies? Expected: another conditional region (future consequence matters only
  when prediction_quality × horizon × budget_scarcity clear a threshold, AND only post-disocclusion since
  pre-warming occluded content is reset), not a universal law. **M6d/T3 DONE — the temporal causal gate, a
  conditional POSITIVE (Ally X):** 5 SEALED policies (present state + own accumulation only) allocate the
  per-frame budget under EQUAL budget (3072 samples), scored on the T2 temporal ruler vs future references; +
  a NON-ADMISSIBLE prophet (future knowledge) as calibration ceiling. RESULT (future pixel/struct): uniform
  0.00599/0.00875; present_pfal 0.00511/0.00754; causal_future_d1 0.00486/0.00694; causal_future_d23 0.00486/
  0.00694; drifted 0.00809/0.01155 (worst, control behaves); prophet 0.00486/0.00694 (gap EXACTLY 0). ε floor
  0.000053/0.000079. ε-frontier (sealed) = {causal_future_d1, causal_future_d23}. FOUR FINDINGS: (1) the
  temporal lever PAYS OFF — causal_future ε-DOMINATES BOTH uniform (Δpixel 0.00113 ≈21× ε) AND present_pfal
  (Δpixel 0.00025 ≈5× ε) on both axes; beating present_pfal (which ALSO avoids occluded waste) proves the win
  is the genuine FUTURE-CAUSAL DEFICIT signal, NOT mere culling. (2) the EXPONENT did NOT matter — d1 ≡ d23
  exactly, UNLIKE M6c: that scene had heterogeneous spatial difficulty (exponent governs concentration), here
  all revealed tiles are equally hard and only TIMING differs → exponent has nothing to bite on (a clean
  boundary). (3) the PROPHET COLLAPSED (gap exactly 0) → this monotone scene holds NO hidden-future opportunity
  (present predicts future); reaching the ceiling means "present info suffices," not "universally optimal." (4)
  CONTRAST with spatial M6 — spatial causal was falsified/conditional, TEMPORAL causal clearly HELPS; the
  temporal lever (don't spend on soon-reset content; feed the freshly-revealed deficit) is a real efficiency
  the budget-blind policies miss. KEY META: the SAME apparatus that FALSIFIED the spatial claim (M6b) SUPPORTS
  the temporal one — strongest evidence it is not biased either way. HONEST SCOPE: supported UNDER the declared
  TAA+disocclusion coupling, on THIS monotone scene where the oracle ceiling is uninformative by construction.
  NEXT: T4 — a HIDDEN-FUTURE scene (future relevance NOT visible in present state) where the prophet genuinely
  separates from sealed policies. **M6d/T4 DONE — the hidden-future importance sweep, the deep temporal test
  (Ally X, 6/6):** the hidden channel is future IMPORTANCE not difficulty (a difficulty spike would reset
  history → forbid preparation → reproduce T3's tautology), so CONTENT is stable (no reset; accumulation
  survives) but a TF event makes some tiles MATTER more — the ruler weights per-tile error by future_importance,
  invisible in present pixels. Coupling FIXED (scene the only variable). Precursor knob ρ∈{0,.25,.5,.75,1}:
  precursor = ρ·importance + (1−ρ)·noise; sealed policies see only the precursor, the prophet sees true
  importance. RESULT — importance-weighted future pixel error, gap(ρ)=causal_future−prophet: ρ0 uniform 0.00552
  / pfal 0.00822 / causal 0.00722 / prophet 0.00480 / gap +0.00242; ρ.25 gap +0.00102; ρ.5 +0.00039; ρ.75
  +0.00011; ρ1.0 +0.00000. ε=0.000076/0.000137. THREE FINDINGS: (1) the CHANNEL IS REAL — at ρ=0 the prophet
  ε-DOMINATES every sealed by ~32× ε (FIRST scene in the arc where the oracle is informative); gap(ρ) MEASURES
  the value of inaccessible future information, decaying to 0 as the present signals it. (2) a WEAK SIGNAL IS
  WORSE THAN NONE — at ρ<0.5 both causal_future AND precursor_pfal are WORSE than uniform (acting on a noisy
  precursor STARVES the truly-important tiles more than spreading); causal⪯uniform flips true only at ρ≥0.5 → a
  RECOVERABILITY THRESHOLD: below it "trying to be causal" backfires, above it it pays (a cautionary boundary
  for any predictive allocator with an unreliable signal). (3) SEALED REACHES THE CEILING EXACTLY AT ρ=1 (gap
  0.00000 — precursor IS the importance signal up to scale ⇒ sealed = oracle); causal_future consistently edges
  precursor_pfal (deficit water-fill-in-time adds a little over pure-proportional). THE TEMPORAL ARC AS ONE
  STORY: present-predicts-future (T3) → causal works, reaches ceiling; future-hidden (T4) → recoverable only
  above a precursor threshold, weak signal harmful. Temporal analogue of M6c's alignment sweep, delivered. The
  whole GPU benchmark (M1–M6c spatial + T1–T4 temporal) maps boundaries; the apparatus is the asset.
- [ ] Native (C++/Rust) **renderer/fidelity** port validated against the Python reference via conformance
  vectors. (The conformance-vector method has been demonstrated at the kernel layer: `reality_kernel/core_rs`
  validated against the Python reference via `golden_kernel.tsv`; this item remains open for PFAL/TCFF/raster.)
- [ ] Multi-lens presentations (cinematic / competitive / VR / handheld / debug) over one committed world.

## Verify locally

```bash
PYTHONHASHSEED=0 python3 tests/test_ursprung.py     # unit suite
PYTHONHASHSEED=0 python3 loop.py                    # live loop + milestone + benches
```
