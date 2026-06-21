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

## What is proven, what you get, and where it goes next

**What is proven** — each claim ships with an executable bench, a negative control, and an explicit "expires
on real silicon" bound; nothing here is asserted without a runnable check.

- **The renderer is observer-only.** Replay identity, view-perturbation invariance, and ordering invariance:
  the VIEW layer cannot move the committed trajectory even when deliberately corrupted every tick
  (`integrity ≠ truth`).
- **Priority and allocation are different objects.** A *failed* hypothesis became the measured result that a
  two-stage `ranked_waterfill` strictly beats proportional / uniform / distance / visibility on the
  future-causal residual — *knowing what matters* is not *knowing where representation breaks*.
- **Observation cannot resolve a backdoor; only intervention can.** A confounder that reconstructs perfectly,
  is gauge-invariant, and correlates ≈0.6 with the outcome still fails the gate because `do(c)` does not move
  it. `observation ≠ intervention`, made a *measured boundary* rather than hidden behind a score.
- **The defense is the leak, and "secure" is class-relative.** The side-channel firewall family neutralizes
  timing/reaction/absence/hysteresis/cost/rollback channels; the one *absolute* guarantee is severing the
  secret from every channel (`I(secret;observable)=0`) — everything else is non-identifiable only relative to a
  stated observer class.
- **Identity includes provenance — and it survives learning, consolidation, and a real substrate.** Six latent
  phases plus three runtimes show *a value bound to the conditions of its own existence*. The **RealityKernel**
  consolidates them into four primitives — `Artifact / Event / CommitReceipt / Query` (a receipt is a *record*,
  never an authorization) — reproducing the prior benches' diagnoses exactly (7/7, a real differential against
  the Python oracle). Its **Rust CORE port is verified on real silicon** (`cargo test` 10/10: semantic
  preservation + adversarial concurrency — many-producer commits collapse to one ordered transition, corruption
  yields *unresolvable* not a guess, a panicking producer never publishes partial state). And the **lineage
  closure test** proves the load-bearing rule — **optimization cannot erase history**: `compress ≠ sever`
  measured to 5×10⁵ commits with zero lineage lost, where discarding lineage for a still-live digest is *caught
  as severance*, never silently allowed.

**What you get** — a **specification + reference implementation + measurement discipline**, not a turnkey
engine. Concretely: a *provenance-preserving execution substrate* (the kernel) with a verified Rust core that
refuses to let state outlive its explanation; a transplantable, re-validatable *information-firewall /
disclosure-audit* family for partially-hidden shared worlds (anti-cheat, fog-of-war); a *fidelity-allocation
economics* (priority ≠ allocation, the resistance tensor, shader/PSO prewarm); a *causal-attribution procedure*
that separates a generator from a confounder/artifact for residuals, anomalies, and ML features; and an
*LLM-on-track methodology* (`observe → hypothesize → implement → verify → record`). Every result names its
estimator class and coverage boundary instead of declaring "safe."

**Where it goes next** — the kernel is the minimal center; everything else is a **client**. A renderer, a
physics step, an agent, and a world generator all *consume* the kernel — **transition history is the center,
not the world**. The scoped, deliberately un-faked frontiers: the Rust CORE at real scale (1e6–1e8 lineage,
frame-loop integration, and the Windows sub-granularity timing question — full-frame spin vs. raising OS timer
resolution); the first world-loop client built *on top of* the kernel; a real estimator under intervention
scarcity (unknown graph); a real external anchor (a verifiable delay function / proof-of-sequential-work); and
the GPU real-silicon benchmark where every constructed-world number finally expires.

What began as a renderer *philosophy* became, under benchmarking, a set of measurable **rendering economics**:
finite fidelity is a budget, every approximation is debt, and the bench — not the manifesto — decides which
allocation policy wins. The central result so far came from a *failed* hypothesis (see below): **priority and
allocation are different mathematical objects.**

It then grew a **second arc**. Because a renderer of a partially-hidden world is also a *potential leak* of
hidden state, rendering became an **information firewall** and finally a **measurement discipline** — a system
that reports what it can and cannot see rather than declaring itself safe. Pushed further, that discipline
turned into a question of **causes, not channels**: a residual outside the observer's projection is not hidden
truth but a *candidate set*, and the renderer learns to separate a real generator from a projection artifact (a
stable, reproducible, hash-identical residue that is nonetheless not causal) by what survives changing the
observer, intervening on the dynamics, and changing the model. *Generator = invariant necessity; integrity ≠
truth; stable ≠ causal.* The broadest framing (research, not built) is that this fidelity engine is *one
backend* of a committed, leakage-bounded **perception compiler**
([`docs/INFORMATION_INTENT.md`](docs/INFORMATION_INTENT.md)).

> ### The pioneering result — observation cannot resolve a backdoor; only intervention can
>
> The load-bearing novelty, and the one not to undervalue: **some causal structure is *not identifiable from
> observation alone*.** When a confounding (backdoor) path is unobserved, or the observation map is
> non-invertible, *no* amount of reconstruction, recoverability, correlation, or model-fit can separate a
> generator from a confounder — the question is **observationally underdetermined** (relative to the available
> variables and observation map, not to physics). Most systems hide this behind a high score; Ursprung makes it
> a **measured boundary**: observation *defines the horizon*, and the only thing that crosses it is an **active
> causal operation** — an intervention, `do(·)`. This is the renderer's deepest separator, `observation ≠
> intervention`, and it is architecture-independent — it does not depend on any encoder, optimizer, or gauge
> family (those are *candidates inside* the frame, never foundations beneath it). It is demonstrated, not
> asserted: in the Phase-1 latent benchmark ([`experiments/latent_phase1/`](experiments/latent_phase1/)) a
> confounder that reconstructs perfectly, is recoverable across every encoder family, is gauge-invariant, **and**
> correlates with the outcome at ≈0.6 still **fails the gate**, because `do(c)` does not move the outcome.
> Observation said "generator" five different ways; only intervention disagreed, and it was right. Two honest
> bounds kept in view: the verdict is a **gate (pass/fail), never a confidence scalar** — the project spent
> hundreds of checks dismantling the one-dimensional confidence object and will not quietly rebuild it; and
> passing the gate means *robust causal **candidate***, not "the deepest generator" — a mediator on `g → x → y`
> survives intervention too (`survives intervention ≠ root generator`). When the causal graph is *unknown*, the
> crossing requires a real intervention mechanism, not a ground-truth oracle — the open problem the next phases
> face, not fake.

## The five laws (the philosophy layer — the ontology of fidelity)

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

These five govern **fidelity economics** — how finite rendering is spent. They are not the project's deepest
invariant, and that deepest one is deliberately *not* numbered as a sixth law, because it is a different
category: a law of the **runtime**, not of the world. (`observation ≠ intervention` is true whether this system
exists or not; *identity includes provenance* is a design requirement the runtime *chooses* to enforce.) It is
treated on its own terms below in *The Provenance Principle* — and **Law 2 (Arbitrary-Boundary) is its earliest
instance**, which is why the rest of the architecture fell out of it.

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

### The novel part: the ghost is a candidate set, not a truth

The arc's deepest turn is in `ursprung/perception/`, where the inversion is applied to the project's *own*
founding object. Milestone 1 already produced a **ghost** — the residual `G = Z − Π(Z)`, what the observer
cannot see. The naive reading is `ghost ≈ hidden mechanism`. The attribution layer shows that is too strong: a
residual is **candidate explanations**, and the system must separate *causes* from *artifacts* by tests against
the other operators — not from the residual itself.

| Question | Test | Module |
|---|---|---|
| was it ever hidden? | membership in the ghost under *some* projection | `attribution.py` |
| is it observer-independent? | **invariance** — ghosted under *every* projection `Π` | `ghost_invariance.py`, `attribution.py` |
| is it causal? | **necessity** — remove it, run `F`; does the trajectory change? | `attribution.py` |
| causal *to which model?* | necessity is **model-relative**; take `⋂ G_F(F)` over the admissible model class | `model_relativity.py` |

The result decomposes the ghost as `G = G_F + G_C` (generator residue + confounder/projection residue). The
decisive, counter-intuitive case is a component that is **invariant, reproducible, observer-independent, and
hash-identical — yet not causal** (the system is the same system without it): a *stable artifact*. Invariance
alone would promote it; only intervention demotes it. So **`stable ≠ causal`**, the hash certifies a
trajectory's *identity* not its *explanation* (**`integrity = reproducibility ≠ causal validity`**), and
necessity itself is only as trustworthy as the model class it is tested against (**`causal-under-a-model ≠
causal-across-models`**). The compact statement of the whole arc: **`Generator = invariant necessity`** — what
survives changing the observer, intervening on the dynamics, *and* changing the model; everything else is a
candidate artifact, however deep it looks. This is what prevents the system turning ignorance into ontology.

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

The full suite is **495 checks** (stdlib asserts), every milestone carrying a verified demo, a negative
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
  (optimal abstention vs ignorance), trading action-utility against action-leakage. And `intent.py` reaches the
  deepest secret: **`I(G;A,O)`** — an inverse-planning observer recovers the agent's *policy/goal* `G` from
  behaviour even when the world secret `S` stays hidden ("hide the data, expose the strategy"); it accumulates
  to the whole policy, capped only by behavioral ambiguity at a coupled cost. *The secret is the policy, not the
  data.* Then `consistency.py` and `identifiability.py` flip the axis from *leakage* to *coherence*: behaviour
  **under-determines its cause** (adaptation and drift emit identical trajectories; `I(cause;behaviour) <
  H(cause)`), and the deepest adversary asks not "what goal?" but **"is there a stable generator to recover at
  all?"** — three regimes (identifiable / ambiguous / non-identifiable), where non-identifiability is
  class-relative and "become noise" only *relocates* the secret to the stochastic character (`noise ≠
  ignorance`). The object becomes **identity under observation**. And `substrate.py` adds the *physical* layer:
  the generator leaks through its **residue** `R` (power/timing/EM) even when the output is encrypted
  (`signal privacy ≠ generator privacy`); the observer is a **sensor-fusion** adversary; `L` becomes a physical
  capacity curve `L(C_sensors)`; and `unobserved ≠ unknown` (a determined generator with no available channel is
  *unobservable*, not absent — the limit is observability, not computation). Finally `adaptation.py` adds
  **provenance**: the cost is *distinguishability* of state change, not change — interface adaptation (VIEW)
  gives each observer a different projection while `CORE` stays byte-identical (the M1 invariant), so the system
  can prove *"I adapted your interface, not my truth"*; only a core-invariance attestation tells "changed
  itself" from "changed what it showed," and `observer-relative ≠ observer-controlled`. And `operators.py` names
  the spine the whole arc instantiates: **leakage `= L(F, M, Π, A_C)`** — dynamics, memory, projection, observer
  reconstruction — four *independent knobs* (the projection and the observer class move leakage separately; the
  dynamics `F` is independent of the projection, CORE ⟂ VIEW in operator form). *The useful artifact is the
  separation, not a final equation.* And `confounder.py` adds the slot the diagram needed —
  `F, M → Π → O ← C ← A_C`: the observer sees `O`, never `F`, so `P(F|O)` is identifiable only by **varying the
  confounder**. Within one context a generator and a confounder are indistinguishable; across contexts only the
  generator survives — *the generator is what stays invariant when observer, projection, and context all change*
  (and a higher-capacity observer **overfits** the confounder). `mechanism ≠ correlation`; `fitted rule ≠ causal
  source`. And `ghost_invariance.py` closes the loop to M1's `ghost_report`: the residual `G = Z − Π(Z)` is a
  generator component only if it is **invariant** across projections *and* **necessary** (removing it changes
  `F`); otherwise it is a **projection artifact — the observer's shadow**. *Generator = invariant necessity;
  `ghost ≠ hidden truth`.* Then `attribution.py` makes that the spine: the residual is a **candidate set, not a
  truth** — it decomposes `G = G_F + G_C` (generator residue + confounder/projection residue), split by two
  questions kept apart (*was it ever hidden?* vs *was it causal?*). The decisive case is a component that is
  invariant across *every* projection yet **not necessary** — a *stable artifact*: invariance alone
  over-attributes it, so both tests are required (`stable ≠ causal`). The hash sits *below* attribution — it
  certifies a trajectory's identity, not its explanation (`integrity = reproducibility ≠ causal validity`), so
  the old 7-stage stack becomes a 9-stage **attribution** stack (`… Projection · Attribution · Integrity`).
  Finally `model_relativity.py` turns the principle on the causal test itself: necessity is **model-relative**
  (`G_F(F₁) ≠ G_F(F₂)`) — a component can be necessary under a restricted model and redundant under a richer one
  that fits the same data, so the robust generator is what survives the *admissible model class* (`⋂ G_F(F)`).
  *Causal-under-a-model ≠ causal-across-models* — the `A_C` loop, one layer deeper. And `grounded_claim.py`
  makes the whole chain a **runtime object**: a conclusion you cannot construct without declaring its floor
  (evidence, projection `Π`, observer class `A_C`, model class `𝓕`, stopping rule), that never asserts truth
  and emits only *"given (A, Π, 𝓕, E), X is the best **surviving** explanation"* — and that classifies a bare
  *"the evidence proves X"* as **floor-hiding**. Its payoff is operational: the *same* evidence under two
  *different declared* `𝓕` yields *different* surviving conclusions, so confidence is **conditional on the
  declared floor, not a scalar of the evidence**. The project's first rule — *arbitrary boundaries require
  deterministic handling, not claims of truth* — has become an epistemology: `proven ≠ surviving`; `declared ≠
  derived`; the floor is exposed, not smuggled. Then `ledgers.py` refuses the last fusion: it splits *can we
  reproduce/audit this?* (**epistemic** integrity) from *does it correspond to the world?* (**ontological**
  adequacy) into two separate objects, with the buggy calculator (integrity 1.0 / adequacy 0.0 — reproducible
  but wrong) as proof they come apart. A single "confidence" scalar can't tell that calculator from real
  science, so the ledgers stay separate — `integrity ≠ truth` made a runtime. Finally `trajectory.py` adds
  **motion**: confidence is not a scalar or even a point but a coordinate `(integrity, adequacy)` with a
  *direction of change* — four quadrants that each allocate a different next action, **no total order** (the
  pair `(1.0,0.2)` / `(0.2,1.0)` is Pareto-incomparable until a goal is declared), and named vectors
  (`accumulating_support`, `entering_crisis`, …). The path matters: the same integrity gain can end in
  *accounted-and-supported* or in *reproducible-error*. `position ≠ ranking`; `integrity-gain ≠ progress`; and
  crisis is declining adequacy regardless of integrity — `integrity ≠ immunity`. And `acceleration.py` adds the
  second derivative: two claims can share a *velocity* and be in different regimes (fragile-early vs
  consolidating-late), so `velocity ≠ regime` — acceleration tells **stabilizing** (motion slowing) from
  **diverging** (speeding up), and **accelerating crisis** (`Δ²correspondence < 0`) from steady decline; a
  confident model can lose the world at a *worsening rate*. `declining ≠ accelerating-decline`. World-side
  direction: [`docs/INFORMATION_INTENT.md`](docs/INFORMATION_INTENT.md).

**The conceptual arc is complete, the empirical phase ran, and it has now crossed into the substrate** (see
*The empirical phase* below): `experiments/` carries six executed latent phases, the three provenance runtimes,
the live/latent compression bench, and the **RealityKernel** consolidation — whose **Rust CORE port is verified
on real silicon** (`cargo test` 10/10) and whose lineage-scale closure test proves *optimization cannot erase
history* to 5×10⁵ commits. Each is a seeded, replayable bench with its own self-check. What stays deliberately
un-faked lives behind the intentionally-unbuilt seams — `reality_harness.NetworkChannel` (point it at a real
socket), `behavioral_harness.ExperimentLayer(channel="real")`, and the perception compiler's lookup compiler —
plus:
- The **Rust CORE at real scale** — the verified port proves *correctness* under real concurrency; behaviour at
  1e6–1e8 lineage, under a frame budget, and under memory pressure (where the failure to hunt is *digest exists,
  lineage gone*) is the next substrate rung, with the Windows sub-granularity timing question (full-frame spin
  vs. raising OS timer resolution) attached.
- The **first world-loop client** built *on top of* the kernel — the point where the substrate stops being
  tested in isolation and starts carrying a world.
- A **real-silicon benchmark** — every constructed-world number expires there (equal GPU time; temporal
  artifacts, input-to-photon latency, reconstruction error, motion stability).
- **Composing + calibrating the resistance tensor** — the 7-dimensional `resistance_tensor.py` already exists;
  what is open is using it as the resistance *everywhere* and tuning its weights against measured artifacts.
- A **real estimator under intervention scarcity** — every experiment so far runs ground-truth `do()` on a
  known synthetic world; recovering causal structure when the graph is *unknown* and interventions are
  expensive (instrumental variables, invariance/ICP, counterfactual estimation) is the genuine frontier, and a
  **real external anchor** (a verifiable delay function / proof-of-sequential-work / external clock) is the only
  thing that would supply the irreversibility software cannot.

## The Provenance Principle (the meta-invariant — the bridge from reality to development)

The five laws are the **ontology** layer (what reality and observation permit). Everything the second arc and
the empirical phase added is governed by something of a *different category* — not a law of the world but a law
of the **runtime**, a design requirement the system chooses to enforce:

> **Identity includes provenance.** An object is not fully specified until the conditions that license its
> existence are attached. *Claims carry floors. Edges carry support. Inferences carry costs. Worlds carry
> histories.*

This is the bridge between *reality* and *development*: it is what lets a system not merely observe a world but
**build in one without mistaking what it authored for what it found**. It is enforced in code, not asserted —
`grounded_claim`, `floor_digest`/`graph_digest`, `CausalEdge`, `EstimatorOutput`, the `Artifact` runtime — and
the entire separator chain is its consequence (`observation ≠ intervention → causal relevance ≠ causal position
→ edge ≠ edge-without-support → latent ≠ discovered structure → coordinate ≠ claim → accuracy ≠
identifiability`). The **Runtime Corollary**, almost a theorem of it, is the one the developable-reality work
turns on: *an edit is an event with identity.*

The full stack the project now spans, each layer with the question it answers and the invariant that governs it:

| Layer | Core question | Invariant |
|---|---|---|
| **Reality** | what exists? | the Five Laws |
| **Knowledge** | what can be justified? | identity includes provenance |
| **Causality** | what supports this edge? | edge provenance |
| **Learning** | what supports this latent? | representation humility |
| **Inference** | what paid for this conclusion? | the identification ledger |
| **Authoring** | how did this world become this way? | an edit is an event |

The consequence for a developable digital reality is the one ordinary engines don't have: **the world itself
becomes provenance-bearing.** Most engines store *state*; this runtime stores *state + history + source +
admissibility conditions* — the world is never merely what it is, it remembers how it became what it is. The
Reality Authoring Runtime (`experiments/reality_authoring/`, below) is the **first architectural realization**
of this meta-invariant, not another entry in the separator list. (Capstone treatment:
[`docs/MEASUREMENT_DISCIPLINE.md`](docs/MEASUREMENT_DISCIPLINE.md), "the meta-invariant.")

### Capstone — Structure, Provenance, Ignorance

> **This is not an ontology of reality. It is an ontology of *declared provenance*.**

The runtime does not treat presence as primary and absence as a void. **Presence and absence are both
first-class objects, and neither is allowed to exist without the conditions that license it.** The whole arc
compresses into three layers under one meta-invariant:

| Layer | Question | Object |
|---|---|---|
| **Structure** | what is present? | `Edit`, `CausalEdge`, `Representation`, `Graph` |
| **Provenance** | why is it present? | floor · support · identification cost · lineage |
| **Ignorance** | why is it absent or unresolved? | `NonRecovery` |

```
RealityModel = Structure + Provenance + Ignorance
  Structure  = what the runtime currently represents
  Provenance = the declared conditions licensing that representation
  Ignorance  = the declared conditions preventing representation
```

It never claims *what exists*, *what is true*, or *what reality is* — only *what is represented*, *why it is*,
and *why something is not*. A narrower statement, and a more defensible one. The same meta-rule holds across
every object — eight families, one invariant (*an object is incomplete until the thing that licenses it is
attached*):

| Family | Identity requires |
|---|---|
| Claim (`GroundedClaim`) | floor |
| Coordinate (`ledgers`) | ledger (integrity + adequacy) |
| Edge (`CausalEdge`) | support |
| Graph (`ProvenanceGraph`) | edge provenance |
| Representation | creator manifest + claim |
| Inference (`EstimatorOutput`) | identification cost |
| Edit (Reality Authoring) | source + lineage |
| Ignorance (`NonRecovery`) | diagnosis + source |

> **The honesty clause.** All provenance in the runtime is *declared* provenance unless independently verified.
> The system records the history of claims, assumptions, costs, edits, and failures; it does not guarantee their
> truth. `declared ≠ verified` — a **notary of history, not an oracle of reality.**

## The empirical phase — provenance survives learning (`experiments/`)

The conceptual arc ended at a claim it could not yet test: that the project's discipline would survive contact
with a real, flexible learning system. `experiments/` is where that claim meets numbers. Each phase is a small,
**seeded, replayable** bench (numpy or pure stdlib) kept *outside* the 495-check core so the verified renderer
stays dependency-free; each has its own self-check, an explicit "expires on a non-toy world" bound, and reuses
the prior phase's contract *unedited* — the reuse is the experiment. The organizing instruction was
**"define the horizon, then trust the dark"** ([`docs/LATENT_SPACETIME.md`](docs/LATENT_SPACETIME.md)): demarcate
what a representation can recover from what it structurally cannot, validate only on the lit side, and never
fabricate the dark. The one thing never liquidated is the sealed core — `liquidate the schema ≠ liquidate the
floor`.

| Phase | Object | Measured result (seed 0) | Separator earned |
|---|---|---|---|
| **1** `latent_phase1/` | latent benchmark (PCA / linear-AE / MLP-AE) | a confounder reconstructs, is recoverable across every encoder, is gauge-invariant, **and** correlates with the outcome — yet `GeneratorScore = 0`; only `do(c)` (which doesn't move the outcome) catches it | `good reconstruction ≠ recovered generator` |
| **2** `latent_phase2/` | topology discovery from intervention asymmetry | `do(g)` moves x,y; `do(x)` moves y not g → roles root/mediator/sink recovered; root and mediator are *both* relevant, only topology separates them | `causal relevance ≠ causal position` |
| **3** `latent_phase3/` | edge provenance — support is part of a graph's identity | two graphs with identical adjacency but different support have different digests; removing an assumption removes an edge; the `𝓐`-invariant core *is* the intervention-grounded subgraph | `recovered topology ≠ discovered ontology` |
| **4** `latent_phase4/` | the contract under a learned representation | g/m/c all recoverable ≥0.99 from the learned latent; the Phase-3 contract still refuses an assumption edge without its assumption — over learned-factor nodes | `created coherence ≠ discovered coherence` |
| **5** `latent_phase5/` | provenance-preserving learning | two encoders with different latents (`[0.28,0.96,0.95]` vs `[0.95,0.71,0.81]`) yield the **same** provenance-qualified claim → equivalent; rescaling the input doesn't change it (the **scale gauge is closed**) | `latent coordinate ≠ the claim` |
| **6** `latent_phase6/` | the inference contract — no edge without its price | the same edge via `do()` vs via assumption are *different objects*; `IdentificationCost` is a structured ledger (not a scalar); a cost-free or accuracy-only claim is rejected at construction | `accuracy ≠ identifiability` |

**Three runtimes consolidate it.** Once the phases all produced the same shape — *a value bound to the
conditions of its own existence* — they collapse into one object:

- **`experiments/provenance_runtime/` — the runtime that *records*.** One `Artifact` (identity · provenance ·
  evidence · status), and every prior phase becomes an artifact *type* sharing a single identity system. Two
  digests: a `claim_digest` (what is asserted) and a full `digest` (including provenance — *identity includes
  provenance*). `transform()` produces a child with inherited provenance, so a developer can **swap the model,
  encoder, estimator, or assumptions without losing the history of what made the result admissible**; the model
  is a plugin, the contract is not. `compare()` is over claims not representations; `audit()` separates
  *demonstrated* from *assumed*. The creator enters as a named provenance source — neither hidden nor sovereign
  — which blocks both anthropomorphism ("it discovered because it thinks like us") and technological projection
  ("it discovered because it is outside us").
- **`experiments/adversarial_runtime/` — the runtime that *attacks*.** The offensive complement: it
  **weaponizes** `declared ≠ verified` (flagging any artifact that asserts a higher status than its evidence
  backs — laundering), runs a **Paradox Engine** for structural contradiction (verified-without-evidence,
  same-claim-at-two-statuses, provenance cycles), runs **adversarial survival tests** and a **Necro-Registry**
  that buries falsified artifacts *with their cause of death* (a dead claim is information), and provides an
  **External Anchor** — an append-only, tamper-evident commitment chain that grounds *ordering*. Its loudest
  honest bound: a software anchor is `tamper-evident ordering ≠ physical irreversibility` (a fresh chain from
  the same inputs reproduces), so a real anchor needs an irreversible external cost — the frontier.
- **`experiments/reality_authoring/` — the runtime that *authors*.** The first architectural realization of the
  meta-invariant: a world where **an edit is an event with identity**, not a mutation. `Edit(target, old→new,
  source, justification, scope, survival_tests)` makes the world remember *how* it became what it is, so the
  runtime answers what ordinary engines cannot — *was this behaviour designed or did it emerge? which structure
  came from which source? if I remove this edit, what collapses? which parts are stable under the world's own
  transformations* (the **discovered** constraints, vs the **authored** rules and the **emergent** patterns).
  The non-anthropocentric invariant: it is the *source of structure* that stays inspectable — `{developer,
  algorithm, learned_model, external_data, environment}`, **no origin privileged, none erased** — so a world
  can be authored and generated without quietly starting to look autonomous. The bridge from "renderer + a
  provenance discipline" toward "a world a developer develops *in*."

**The consolidation and the substrate (the fourth movement).** Once the three runtimes shared one shape, the
arc crossed from *what must be true* to *what must remain true under pressure*.

- **`experiments/live_latent_provenance/` — provenance survives compression.** The hot path carries only a
  provenance *digest*; the full lineage resolves on demand from a latent store; an optimization that *severs*
  (drops the digest) is a caught runtime failure, never a silent fallback to `unknown` (`compress ≠ sever`,
  `PROVENANCE_SEVERED ≠ UNACCOUNTED`). Its first real-clock probe produced a **reversal**: provenance carry is
  near-free; *uncontrolled time sources*, not provenance, are what threaten a frame budget — so deadline pacing,
  not metadata thrift, is the lever (jitter fell ~12× on Linux; the Windows sub-granularity case is named, not
  faked).
- **`experiments/reality_kernel/` — the organism, assembled.** Four immutable primitives —
  `Artifact / Event / CommitReceipt / Query` — over the objects already earned, reusing the prior benches as
  *evidence modules* (reuse, not reimplementation) and reproducing their diagnoses exactly. `Query` is the new
  surface: existence *and* absence (`present / absent / unresolved / unaccounted`) with diagnosis and a
  resolution path, a strict refinement of the old `explain()`. A receipt is a record, never an authorization
  (`attestation ≠ authority`). 7/7, including a real differential against the Python oracle.
- **`experiments/reality_kernel/core_rs/` — the substrate, verified.** The Rust CORE port as a *semantic
  preservation* exercise (the Python kernel is the reference model; the differential asserts against a frozen
  oracle). **Verified on real silicon** — `cargo test` 10/10: the typed `CommitPath` (never drops) /
  `ResolveRing` (may drop) split, many-producer→single-ordered commits with no loss, corruption→unresolvable,
  and a mid-write panic that never publishes partial state.
- **`experiments/reality_kernel/lineage_scale/` — the closure test.** Optimization cannot erase history:
  hot plane (state + digest) and cold plane (lineage) measured separately so a fast cache can't hide a missing
  lineage; to 5×10⁵ commits, every digest resolves, and the forbidden transition (`digest present + lineage
  unavailable = severance`) is *detected*, never guessed.

The whole ladder is generated by one principle — **`identity includes provenance`** (the Provenance Principle
above) — applied, in the end, even to the creator:

```
observation ≠ intervention  →  causal relevance ≠ causal position  →  edge ≠ edge-without-support
→  latent ≠ discovered structure  →  coordinate ≠ claim  →  accuracy ≠ identifiability
```

**Honest scope of the empirical phase.** Every intervention is still a ground-truth `do()` on a *known*
synthetic world: these phases prove the *discipline survives learning and consolidates into a runtime*, not
that causal discovery is solved. The estimator that pays the identification price in valid coin (under
scarcity, without a known graph) and a real external anchor are named, scoped, and intentionally not faked.

## Pioneering methods (what is genuinely new here)

Stated with the project's own calibration — much of this is *composition* of established research (quantitative
information flow, information design, causal identifiability, gauge invariance), and the novelty is the fusion
and the runtime, not a claim to have invented the pieces.

- **Falsification-first engineering.** Every result ships with a negative control and an explicit
  "expires on real silicon" bound, and a *failed* hypothesis (Causal Continuity) is preserved as a load-bearing
  result rather than deleted. The deliverable is "a framework for discovering where our own assumptions fail,"
  not a leaderboard number.
- **`observation ≠ intervention` as a measured boundary.** A system that detects when a question is *not
  identifiable from observation alone* and refuses to resolve it — exposing the boundary instead of hiding it
  behind a high score. Most pipelines silently cross it; this one marks it and names the price of crossing.
- **The provenance discipline / `identity includes provenance`.** An object is not fully specified until what
  licenses it is attached: claim+floor, edge+support, representation+claim, inference+price — content-addressed,
  so two artifacts with identical content but different provenance are different objects. This is the thread
  that turns a pile of separators into one mechanism.
- **The side-channel firewall family ("the defense is the leak").** Treating the renderer/netcode itself as a
  sensor an adversary reads, and neutralizing timing, reaction, absence, hysteresis, execution-cost, and
  rollback channels — each with an executable bench. No standard textbook hands you this for interactive
  systems.
- **The benchmark hierarchy (reconstruction is the weakest test).** A 5-tier gate — reconstruction →
  intervention → topology → model-class robustness → gauge invariance — where a feature is only "real" if it
  clears 2–4. It catches the confounder that fools accuracy.
- **Confidence as structure, never a scalar.** Integrity ⟂ adequacy (two ledgers), a coordinate with quadrants
  that allocate work, motion (`trajectory`) and acceleration (regime/crisis) — each step replaces a
  one-dimensional score with a richer object because the scalar was collapsing distinctions that matter.
- **Determinism as an executable epistemic, not a metaphysical claim.** Reproducibility is a property of the
  *account* (same inputs + declared floor + procedure → same result), enforced by a sealed verification
  substrate — distinct from any claim that the world is deterministic.
- **The typed inference contract + the two runtimes.** A model/encoder/estimator that is a *plugin* beneath a
  fixed contract: an estimator that cannot emit an edge without its identification cost, an artifact that
  records its conditions of existence, and an adversarial runtime that attacks declarations and keeps the
  corpses. The discipline is the asset; the model is replaceable.

## Use cases — for developers and for investors

Ursprung is a **specification + reference implementation + measurement discipline** (plus an early empirical ML
layer), not a turnkey product — read the use cases through that frame.

**For developers (concrete, usable now):**

- **Anti-cheat / multiplayer disclosure.** Show enough of a partially-hidden world to be playable without
  becoming an oracle: the access-control + composition firewall + accumulation + side-channel families, each a
  transplantable, re-validatable reference (`causal_access`, `reconstruction`, `accumulation`, `side_channel`,
  `execution_surface`, `convergence`).
- **Renderer fidelity allocation.** Spend compute by expected future failure cost, not present complexity;
  `ranking ≠ allocation` (water-filling under a resistance tensor), and turning shader/PSO hitches into a
  prewarm allocation problem.
- **A measurement / audit substrate.** Point `channel_discovery` + the `DisclosurePolicy` auditor at a real
  telemetry or output stream — *"policy said reveal X; did the output contain only X?"* — and get a result that
  names its estimator class and coverage boundary instead of declaring "safe."
- **Causal attribution for residuals, anomalies, and ML features.** Given an unexplained signal, decide whether
  it is a generator or a confounder/artifact by invariance + intervention + model-robustness + gauge — the
  latent benchmark's procedure transfers even where its toy numbers do not.
- **A provenance runtime for ML pipelines.** Wrap any learned artifact so it carries its conditions of
  existence; swap the model without losing what made the result admissible; `audit()` what was *demonstrated*
  vs *assumed*; weaponize `declared ≠ verified` to catch a result that asserts more than its evidence backs.
- **LLM-on-track methodology.** `observe → hypothesize → implement → verify → record`, with guards against
  silent architectural drift, accidental authority leakage, unreplayable behavior, and unmeasured optimization
  claims — portable to any systems project ([`docs/LLM_ON_TRACK.md`](docs/LLM_ON_TRACK.md)).

**For investors / strategic readers (honest framing):**

- **Category.** Not a renderer, security tool, or AI-safety product alone — a horizontal **intent-aware
  information-mediation / verifiable-representation-governance** architecture, of which a renderer is one
  backend. The same contract applies to game engines, agent environments, robotics, collaborative software,
  simulation, medical/scientific visualization, and AI evaluation.
- **The moat is a contract, not a model.** The asset is *representation-invariant epistemic accounting* — it
  survives model and representation churn, because the model is a plugin and the provenance contract is fixed.
  As models commoditize, the durable layer is the one that says *under what declared conditions this result
  exists.*
- **Timing.** As generative and agentic systems proliferate, the scarce capability is not producing coherent
  output (modern ML is excellent at that) but **telling created coherence from discovered structure** — the
  exact failure (`created coherence ≠ discovered coherence`) this layer is built to prevent. Provenance is the
  audit substrate that frontier will require.
- **Defensibility & candor.** AGPL-3.0; built as honest composition of peer-reviewed disciplines into a
  closed-loop, typed, falsification-first system. It does not claim to have solved causal discovery or to ship
  GPU pixels; it claims to make every assumption visible, every result replayable, and every conclusion carry
  its price — and it states its frontiers rather than papering over them.

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
fidelity engine is one backend. [`docs/LATENT_SPACETIME.md`](docs/LATENT_SPACETIME.md) — the *real-ML pivot*: from a
hardcoded schema to a learned latent substrate, organized around *define the horizon, then trust the dark*; the
discipline layers are **built** in `experiments/` (Phases 1–6 + two runtimes), the estimator under scarcity and
a real external anchor remain the frontier. [`experiments/`](experiments/) — the executed empirical phase
(`latent_phase1`–`6`, `provenance_runtime`, `adversarial_runtime`, `reality_authoring`, `live_latent_provenance`,
and `reality_kernel/` — the four-primitive consolidation, its Rust CORE port `core_rs/` verified on real
silicon, and the `lineage_scale/` closure test), each a seeded, self-checking bench outside the core. [`AGENTS.md`](AGENTS.md) — the contract every change obeys.

## License

Ursprung is licensed under the [GNU Affero General Public License v3.0 only](LICENSE) (AGPL-3.0-only).
Copyright (C) 2026 Daniel J. Dillberg. It consumes the sealed `Reality_Engine` workbench read-only (the
Sibling Law) and does not vendor or relicense any of it.
