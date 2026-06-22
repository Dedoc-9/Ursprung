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
  silicon. Remaining: M2 Rust BenchmarkObservation → M3 FrameArtifact→submission→GpuInterval → M4 shaders /
  pixels / present-to-photon / thermal.
- [ ] Native (C++/Rust) **renderer/fidelity** port validated against the Python reference via conformance
  vectors. (The conformance-vector method has been demonstrated at the kernel layer: `reality_kernel/core_rs`
  validated against the Python reference via `golden_kernel.tsv`; this item remains open for PFAL/TCFF/raster.)
- [ ] Multi-lens presentations (cinematic / competitive / VR / handheld / debug) over one committed world.

## Verify locally

```bash
PYTHONHASHSEED=0 python3 tests/test_ursprung.py     # unit suite
PYTHONHASHSEED=0 python3 loop.py                    # live loop + milestone + benches
```
