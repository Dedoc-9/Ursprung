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

What began as a renderer *philosophy* became, under benchmarking, a set of measurable **rendering economics**:
finite fidelity is a budget, every approximation is debt, and the bench — not the manifesto — decides which
allocation policy wins. The central result so far came from a *failed* hypothesis (see below): **priority and
allocation are different mathematical objects.**

It then grew a **second arc**. Because a renderer of a partially-hidden world is also a *potential leak* of
hidden state, rendering became an **information firewall** and finally a **measurement discipline** — a system
that reports what it can and cannot see rather than declaring itself safe. The broadest framing (research, not
built) is that this fidelity engine is *one backend* of a committed, leakage-bounded **perception compiler**
([`docs/INFORMATION_INTENT.md`](docs/INFORMATION_INTENT.md)).

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
| **Representation Resistance** | *what is expensive to represent?* | `Rr` (perimeter proxy; 7-dim tensor in `resistance_tensor.py`) | `representation.py` |
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

## The second arc — the renderer as an information firewall (and the side-channel defense)

The same separation that makes the renderer an *observer of truth* makes it a candidate **leak** of truth: in
a shared, partially-hidden world (multiplayer, fog-of-war, anti-cheat), the renderer must show enough to be
playable without becoming an oracle for hidden state. A second arc grew out of this, reframing rendering as a
**fidelity control system / information firewall.** Its progression reads as one question per milestone:

> trust it? → may I use it? → can I reconstruct it? → accumulate it? → learn from the defense? → infer the
> generator? → infer the machine? → infer reality from correction? → can measurement replace assumptions? →
> who is the final observer? → learnable by *which class* of observer?

The early rungs are classic firewalls — content-hash integrity + k-of-n consensus (`dependency_integrity.py`),
capability tokens (`capability.py`), an access-control layer that blocks a wallhack even when the claim is
*unforged and agreed* (`causal_access.py`), and a composition firewall that caps a *set* of individually-
authorized fragments so they can't jointly reconstruct a secret (`reconstruction.py`). The chain they enforce:
**integrity ≠ confidentiality ≠ authorization ≠ harmlessness.**

### The novel part: the defense is the leak

The harder result — and the part with no standard textbook answer — is that once information flow is
controlled, **the system's own behavior becomes the channel.** The side-channel defense family treats the
renderer/netcode itself as a sensor an adversary reads:

| Leak (the system as sensor) | Defense | Module |
|---|---|---|
| response time correlated with the secret | **timing normalization** (quantize → zero resource-dependent spread) | `side_channel.py` |
| which branch was prepared reveals the cause | **prediction-inversion breadth** (`prepare ≠ announce probability`) | `side_channel.py` |
| a colluding majority of clients | **weighted-trust consensus** (evidence×authority×reliability, not headcount) | `side_channel.py` |
| the *defense's own reaction* (fog spikes near the enemy) | **Reaction Debt** — make the reaction uncorrelated with the secret | `adversarial_dynamics.py` |
| something conspicuously **missing** (no footstep, no packet) | **absence firewall** (`missing ≠ informative`) | `adversarial_dynamics.py` |
| an uncertainty radius that shrinks as you approach | **Ambiguity Debt** (uncertainty must not become a ruler) | `representation_privacy.py` |
| a boundary that flips on hovering | **Representation Hysteresis** (enter ≠ exit threshold) | `representation_privacy.py` |
| a hitch / cache miss / cost spike when the secret is near | **Execution Surface Privacy** (`observable cost ≠ hidden state`) | `execution_surface.py` |
| a rollback whose magnitude/timing leaks the cause | **Reconciliation Signature Debt** (bounded correction family) | `convergence.py` |

These unify into one ladder of invariants the renderer enforces: **`consequence ≠ mechanism` → `image ≠
generator` → `renderer ≠ oracle` → `correction ≠ cause`.** A representation may reveal *what* happened in the
world; it may never reveal the *rule that maps hidden state to representation*, nor the *machinery* (timing,
cache, cost) by which that rule runs. Every defense ships with an executable bench and a negative control
(e.g. naive timing spread 7 ms → 0; on-demand cost signature 13 → 0 when pre-prepared; reconstruction 1.00 →
0.31 firewalled).

The same **inversion** recurs across M15–M21: each defense names an *observable* an adversary would read
backward into a *hidden* thing, and the boundary that forbids it. This is the thread tying the arc together:

| Observable | Hidden thing inferred | The boundary |
|---|---|---|
| timing / cost | execution state | `execution ≠ hidden state` |
| representation | the generator | `image ≠ generator` |
| correction | the cause | `correction ≠ cause` |
| observer behavior | the policy | `behavior ≠ representation rule` |
| measurement result | reality | `measurement ≠ truth` |

The last row is the recursive one: even the defender's *own measurement* is an observable that must not be
mistaken for the truth about the system — which is why a result names its estimator class and coverage
boundary rather than declaring "safe."

### What it actually proves (the measurement discipline)

Pushed to its limit, the arc stops being a stack of defenses and becomes a **measurement discipline** — and it
is honest about exactly one guarantee. Varying the *adversary's model class* (`adversary_capacity.py`) shows
that "secure" is almost always **relative to an observer class**: M20's "constant-feel resists a learning
adversary" was true only against a 1-D learner; a structure learner recovers the rule. Adversary Information
Capacity is a *lattice*, not a scalar. The single class-independent result:

> **Security = non-identifiability under bounded experimental access.** The only *absolute* guarantee is to
> **sever the secret from every observable channel** (`I(secret ; observable) = 0` for all observables). The
> generator, the machine, the convergence, the player's *feel* — all are non-identifiable only relative to a
> stated observer class, and dissolve against a richer one.

And because the defender is *also* a bounded observer, `channel_discovery.py` inverts the audit from "does
channel X leak?" to "what channels **exist**?" — computing mutual information per channel and surfacing an
*unmodeled* leaker an enumerated audit would miss. Its own twist: the **detector is itself a hypothesis
class** — the same channel reads `I = 0.00` under a marginal estimator and `I = 1.00` under a sequence
estimator, so a result is never `safe`, only "no leak found *by estimator E, over trace D, against class A*."
The full epistemic boundary — including the separators (`measured ≠ guaranteed`, `tested ≠ safe`,
`simulation ≠ physics`, `bounded observer ≠ all observers`, `zero MI on trace ≠ zero MI on hardware`) — is in
[`docs/MEASUREMENT_DISCIPLINE.md`](docs/MEASUREMENT_DISCIPLINE.md).

## What category is this? — Intent-Aware Information Mediation

Ursprung is not, at root, a rendering technology, a security framework, or an AI-safety system — each is too
narrow. It is **composition, not invention**: it applies *quantitative information flow* and *information
design* as a **closed-loop architecture** for interactive systems, in which the representation itself becomes a
**controlled interface rather than a passive output.** It anchors to existing research rather than replacing it:

- **Quantitative Information Flow (QIF)** supplies the *measurement* — how many bits escaped, under which
  observer class, through which channel (`channel_discovery.py`, `adversary_capacity.py`).
- **Declassification** supplies the *permission model* — what is intentionally released (`disclosure.py`).
- **Information design / Bayesian persuasion** supplies the *purpose model* — *why* it is released and what
  decision it should enable.
- The **measurement discipline** supplies the operational loop most systems lack:

```
policy → implementation → observable behavior → measurement → policy revision
```

Most stacks stop at `policy → implementation`; the closed loop — *prove the realized system matched the
intended disclosure* — is the differentiator. The control point moves from access control's "**may** this
observer receive this object?" to "**what representation lets this observer accomplish the task while minimizing
unintended inference?**" The defensible one-line: *a QIF-backed, closed-loop information-mediation architecture
for interactive systems, in which the representation is a controlled interface — of which a renderer is one
backend* (game engines, agent environments, robotics, collaborative software, simulation, medical/scientific
viz, adaptive interfaces). Full taxonomy and the honest "composition, not invention" caveat:
[`docs/INFORMATION_INTENT.md`](docs/INFORMATION_INTENT.md) §9.

## Run it

```bash
PYTHONHASHSEED=0 python3 loop.py                  # live loop: milestone + prediction/membrane/PFAL/TCFF/PCJ
PYTHONHASHSEED=0 python3 tests/test_ursprung.py   # unit suite (stdlib asserts)
```

On Windows PowerShell, use `python` and set the seed inline: `$env:PYTHONHASHSEED="0"; python loop.py`
(env vars do not persist across separate command blocks, so keep the assignment on the same line).
If the engine is not at `~/Desktop/Reality_Engine`, set `URSPRUNG_WORKBENCH=/path/to/Reality_Engine`.

## The cardinal proof — the renderer is observer-only (Milestone 1)

This is the foundational invariant the whole project stands on, not the current frontier (see *Status*):

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
| `ursprung/channel_discovery.py` | **OBSERVER** | Channel Discovery (a harness feature, the bridge to the empirical phase): inverts "does channel X leak?" into "what channels *exist*?" — mutual information per observable channel, surfacing an **unmodeled** leaker an audit would miss. `I = 0 ⇒ severed/absolute; I > 0 ⇒ feed the adversary class` |
| `ursprung/disclosure.py` | **OBSERVER** | the intent → representation seam (first brick of the *perception compiler*): a committed, content-addressed `DisclosurePolicy(observer, purpose, allowed, forbidden)` + a toy compiler + the M10–M21 firewall as auditor — *policy says reveal X; did the output contain only X?* Instrument, not a law; `compliant ≠ safe` |
| `ursprung/perception/` | **OBSERVER** | the first complete **perception loop** (the repo's first privacy-funnel benchmark): `world → DisclosurePolicy → compiled observation → agent → task → leakage`. Measures **participation utility** (task success) against **leakage** (`I(secret;view)`, via `channel_discovery`). Result: only the *compiled* policy preserves full task success (U=1.0) under the leakage budget — `raw` over-discloses (L=6 bits), `blind` under-serves (U=0.56). `adversary.py` then turns the frontier *adversarial*: a per-frame leakage estimate of **0.79 bits** is **falsified** by an accumulating learner that recovers the **exact** secret (6 bits) across a session — **`leakage ≠ exploitability`** (class-relative, M21; temporal, M13). `session_accounting.py` is the fix and the first **general** result: accounting leakage per *session*, the accumulation-aware compiler drops the triangulating channel and keeps the stable task band — utility stays **1.0** while session exploitability **collapses 6 → 0.83 bits** (exact never recovered) under a 2-bit session budget. *Purpose-preserving disclosure under an accumulating observer.* `frontier.py` then removes the free lunch: for a **non-separable** task (exact interception, where utility *is* the secret) it produces the **privacy–utility frontier** — utility ≈ `2^(leakage−6)`, doubling per bit, full utility strictly requiring full leakage. *The measurable cost of knowledge* — the framework now MEASURES the irreducible tradeoff rather than escaping it. `fidelity.py` unifies the three into the **Perception Fidelity Condition** (a Dini-style *sufficient* test): a representation is *task-faithful* (`utility ≥ U_min`) **and** *inference-bounded* (`session recovery < τ`) — it HOLDS for the separable task and is provably **infeasible** for the non-separable one (the reconstruction bound is an *upper Dini derivate* of accumulated recovery; the regime split echoes the Denjoy–Young–Saks theorem) |
| `loop.py` | — | smallest executable world loop, end to end |
| `AGENTS.md` | — | the renderer contract (the rules every change obeys) |

## Status

The full suite is **373 checks** (stdlib asserts), every milestone carrying a verified demo, a negative
control, and an explicit "expires on real silicon" bound.

- **M1 — foundation.** Invariant harness; the renderer is proven observer-only (`integrity ≠ truth`).
- **M2 — the five laws.** Reality Debt · Arbitrary-Boundary · Predictive Fidelity (PFAL/TCFF) · Polygon
  Reconciliation · Temporal Fidelity Conservation, each encoded as data/rule.
- **M3 / 3.1 — rendering economics.** VIEW raster slice + the Causal Continuity Hypothesis, which **failed**
  the equal-budget bench (recorded, not hidden) and became the *ranking ≠ allocation* refinement;
  `ranked_waterfill` strictly beat every control.
- **M4–M9 — fidelity as an economy.** Stressors, transition debt, the resistance tensor + fidelity
  derivative, the shader cache (hitches → allocation), Causal Surface Area, the Readiness Layer, provider
  contracts, dependency surface/integrity, and the representation compiler.
- **M10–M21 — the information-firewall arc** (see *The second arc* above). Integrity → authorization →
  reconstruction safety → accumulation safety → adversarial dynamics → representation privacy → execution
  surface privacy → convergence → the reality/behavioral/adaptive harnesses → Adversary Information Capacity.
- **Channel Discovery + Measurement Discipline — the landing.** The audit is inverted to "what channels
  exist?", the detector is shown to be its own hypothesis class, and the project's epistemic boundary is
  written down ([`docs/MEASUREMENT_DISCIPLINE.md`](docs/MEASUREMENT_DISCIPLINE.md)).
- **The perception loop — measurement becomes *classification*.** `disclosure.py` adds the intent →
  representation seam; `ursprung/perception/` runs the first complete loop and the repo's first **privacy-funnel**
  benchmark; `adversary.py` *falsifies* its per-frame leakage number (an accumulating learner recovers the exact
  secret); `session_accounting.py` answers with the first **general** result — *purpose-preserving disclosure
  under an accumulating observer*; `frontier.py` removes the free lunch on a non-separable task; and
  `fidelity.py` is the **Perception Fidelity Condition** that ties them together. The object of study has
  shifted from the channel `I(S;O)` to the observer's **belief trajectory** `B_t = P(S | O_{1:t})`, and the
  repo now *exhibits and classifies* three recovery regimes: **bounded** (separable — task converges, secret
  does not), **tradeoff** (non-separable — a real frontier), and **cascade-collapse** (a session of weak signals
  reconstructs the secret). The condition reports *which regime a given `(task, policy, observer-class)` falls
  in* — a **behavioral forecast, not a safety certificate.** A general classifier (a "Denjoy–Young–Saks for
  perception") is the open target, not a claim. And `observer_capacity.py` makes the dependence a curve —
  **`Leakage(C)`**: the *same* representation leaks 0.39 bits to a memoryless observer and the *whole* secret to
  an accumulating one, so "low leakage" is undefined until the observer class is named. That curve only *defines
  the axis*; scaling `C` to a real model on a non-toy world is the genuine next frontier, deliberately not faked
  here. Finally `response.py` opens the **action channel**: reaction is itself a leakage channel (`I(S;A)`) — an
  always-react actor leaks the whole secret through *what it does* even if disclosure was sealed; a **response
  gate** (act iff `ΔU ≥ info+signaling cost`) makes **non-action a first-class, *attributable* output**
  (optimal abstention vs ignorance), trading action-utility against action-leakage. World-side direction:
  [`docs/INFORMATION_INTENT.md`](docs/INFORMATION_INTENT.md).

**The conceptual arc is complete; the remaining work is empirical, not more laws.** It lives behind the
intentionally-unbuilt seams — `reality_harness.NetworkChannel` (point it at a real socket),
`behavioral_harness.ExperimentLayer(channel="real")`, and the perception compiler's lookup compiler — plus:
- A **real-silicon benchmark** — every constructed-world number expires there (equal GPU time; temporal
  artifacts, input-to-photon latency, reconstruction error, motion stability).
- **Composing + calibrating the resistance tensor** — the 7-dimensional `resistance_tensor.py` already exists;
  what is open is using it as the resistance *everywhere* and tuning its weights against measured artifacts.
- A **stronger adversary class** (replace the toy learners with a real ML/RL class), **channel discovery over
  real telemetry traces**, and a **non-separable task** for the perception loop — the natural first experiments
  of the empirical phase.

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
experiments. [`docs/GENEALOGY.md`](docs/GENEALOGY.md) — the full genealogy & checklist.
[`docs/MEASUREMENT_DISCIPLINE.md`](docs/MEASUREMENT_DISCIPLINE.md) — the project's epistemic boundary: the
measurement loop, closed-world failure, what a result means, and what NOT to claim.
[`docs/INFORMATION_INTENT.md`](docs/INFORMATION_INTENT.md) — the *next-gen direction* (research, not built):
the world-side dual of the M10–M21 arc — a committed, leakage-bounded **Perception Compiler** of which the
fidelity engine is one backend. [`AGENTS.md`](AGENTS.md) — the contract every change obeys.

## License

Ursprung is licensed under the [GNU Affero General Public License v3.0 only](LICENSE) (AGPL-3.0-only).
Copyright (C) 2026 Daniel J. Dillberg. It consumes the sealed `Reality_Engine` workbench read-only (the
Sibling Law) and does not vendor or relicense any of it.
