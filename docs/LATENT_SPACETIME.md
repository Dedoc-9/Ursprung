<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Latent Spacetime — the next-gen direction (spec, not built)

> **Define the horizon, then trust the dark.**

This document specifies the pivot from a hardcoded symbolic schema to a **learned latent substrate**, and it is
deliberately a *spec* and not code. Everything below is a target with a declared floor and a falsifier; nothing
here is claimed to work until it is measured on a real encoder over real state. The point of writing it first is
the project's own discipline: *do not let metaphor wear an engineering badge.* Several of the imperatives that
prompted this (`latent spacetime`, `black hole of weight space`, `holographic compression`) are **analogies**;
each section below states plainly what is mechanism and what is analogy.

This is the empirical frontier the repo has flagged from the start (`reality_harness.NetworkChannel`, "a real
ML/RL adversary class," "every constructed number expires on real silicon"). It cannot be faked with another
symbolic toy. So the build is **phased**, and Phase 0 is a constraint, not a feature.

---

## Phase 0 — the one thing that is NOT liquidated (the sealed core)

`liquidate the hardcoded schema` does **not** mean liquidating the verified core. `Reality_Engine`
(Chronicle/Dentatus) is sealed and immutable; `world_core` wraps it; the **cardinal invariant** holds — the
committed hash trajectory is byte-identical with any observer active and corrupted. The latent substrate is a
new **representation layer above the committed trajectory**, never a replacement for it.

```
authoritative world state  →  [committed trajectory — SEALED, the floor]  →  encoder E  →  latent Z  →  …
                               (the Weltlinie; uncrossable, byte-identical, replayable)
```

The Weltlinie is the declared floor everything latent is validated *against*. The moment integrity itself
becomes learned, integrity becomes subjective and the whole discipline dissolves (`integrity ≠ truth`, one
level up). **New separator: `liquidate the schema ≠ liquidate the floor`.** What dies is the hand-authored
state schema (`Z = (visible, g, c)`); what stays is the verified, deterministic, replayable trajectory the
latent is an interpretation *of*.

---

## The central object — the horizon

A learned representation has a **lit side** (what the decoder can recover from the observable boundary) and a
**dark side** (what it structurally cannot). The architecture's first job is to *compute and declare that
boundary* — the horizon — and its second job is to *trust the dark*: make no claim about the interior it cannot
cross.

```
LIT (observable boundary)        |   DARK (unobservable interior)
recoverable by the decoder       |   in the kernel / null space of recovery
gauge-invariant quantities       |   gauge (pure redundancy) + unidentifiable directions
validated, attested, ranked      |   acknowledged, bounded, NEVER fabricated
```

This is `substrate.py`'s `unobserved ≠ unknown` made architectural, with the honest upgrade: here the dark is
not merely *unobserved*, it is *structurally unrecoverable from this boundary* — and the disciplined response is
not to guess it but to **mark it and stop**. `define the horizon ≠ cross it`; `trust the dark ≠ know the dark`.

---

## The five imperatives → engineering targets

Each target: **mechanism** (the real thing), **analogy** (the metaphor it came in), **build** (Phase, concrete),
**floor** (the chosen boundary it rests on), **falsifier** (what would refute it).

### 1. Liquidate the hardcoded schema → a learned latent schema
- **mechanism.** An encoder `E: committed_state → Z ∈ ℝ^d` and decoder `D: Z → reconstructed_state`, trained for
  reconstruction + downstream task fidelity. The state schema becomes *discovered*, not declared.
- **analogy.** "latent spacetime" — `Z` is a coordinate space, not literal spacetime.
- **build (Phase 1).** Minimal autoencoder over the existing toy world state; measure reconstruction error and
  whether the latent recovers the *generator* (the `g` of `model_relativity`) vs *confounders*.
- **floor.** The encoder architecture, dimension `d`, and training objective **are** the declared model class
  `𝓕`. A learned schema is still a chosen schema. **`learned ≠ assumption-free`.**
- **falsifier.** If reconstruction is perfect but the latent fails gauge-invariance (§3) or cross-context
  robustness (`model_relativity`), the schema fit a confounder, not the generator.

### 2. Symmetries as the ghost / listening to silence → Noether-style absence inference
- **mechanism.** A *declared* symmetry of the dynamics implies a conserved quantity; a forbidden state that is
  conspicuously **absent** is positive evidence the invariant holds, and a residual where structure *must* exist
  but is silent is a ghost to investigate (it routes attention, it does not certify a cause).
- **analogy.** "the ghost in the machine," "listening to silence."
- **build (Phase 2).** Over the latent `Z`: declare a symmetry group, check the conserved quantity is invariant
  along trajectories; flag silent residuals as ghosts (reuse `ghost_invariance` + the absence firewall).
- **floor.** The symmetry is *declared*, not discovered-as-true (it is an `F`/`𝓕` choice). `absence ≠ proof` —
  silence is consistent with the invariant *and* with not-yet-observed violation.
- **falsifier.** A predicted-forbidden state that does occur falsifies the declared symmetry.

### 3. Gauge-invariant validation — *the strongest, most concrete target*
- **mechanism.** A latent has **redundancy**: transformations of `Z` (rotation, relabeling, rescaling) that
  leave `D(Z)` — the observable — unchanged. These are the **gauge**. A validation metric is admissible **iff it
  is invariant under the declared gauge group**; any check whose value changes under a gauge transform is
  measuring an artifact of the representation, not the world. This is "invariant across projections"
  (`ghost_invariance`) generalized from a discrete set of `Π` to a continuous symmetry group.
- **analogy.** none needed — gauge invariance is literal (this is how consistent field theories are built).
- **build (Phase 3).** Implement `is_gauge_invariant(metric, group)`: sample group elements, assert the metric is
  unchanged (within ε) under each; reject gauge-dependent metrics. Validate the latent's *generator* claims only
  through gauge-invariant quantities.
- **floor.** The gauge group itself is **declared** (you choose which symmetries count as redundancy). Wrong
  group → either false invariants or destroyed real structure (the `model_relativity` knife edge, again).
- **falsifier.** A "result" that flips under a declared-gauge transformation is, by definition, not a result.
  **New separator: `gauge-dependent ≠ real`.**

### 4. Cognitive firewalls — the M10–M21 arc on a latent system
- **mechanism.** Treat each latent module as an observer that an adversary reads. Bound what `Z` (or a module's
  activations) leaks about protected state, and what one module can *reconstruct* about another's hidden inputs —
  reusing capability tokens, access control, the composition firewall, and accumulation/adaptation defenses,
  now over learned representations instead of declared claims.
- **analogy.** "black hole of weight space" — you cannot read the generator off the weights (`signal ≠
  generator`); the weights are an *unobservable interior*, a horizon of their own.
- **build (Phase 4).** Measure `I(protected_state ; Z)` with a real estimator; firewall = a representation whose
  task-relevant content is preserved while protected leakage stays below a declared budget (the privacy funnel,
  now learned).
- **floor.** The leakage estimator is itself a bounded observer class (`MeasurementResult` discipline) — "no
  leak" is always "no leak *under estimator E*."
- **falsifier.** A stronger estimator that recovers protected state the firewall claimed to bound.

### 5. Holographic compression — bounded boundary→bulk reconstruction
- **mechanism.** Encode the world so the **observable boundary** determines the interior under a declared
  reconstruction operator, with an explicit **information bound** (Bekenstein-style: recoverable bits scale with
  the boundary, not the volume). Compression is validated by reconstruction error *under the bound*.
- **analogy.** "holographic" — the holographic principle motivates the shape; this is not a claim that the world
  *is* a hologram.
- **build (Phase 5).** A boundary encoder + bulk decoder with a budget on boundary bits; measure how much of the
  interior is recoverable vs how much falls past the horizon into the dark.
- **floor.** The boundary, the reconstruction operator, and the bound are **declared conventions**
  (`conventions.py` again). `compressed ≠ complete`.
- **falsifier.** Interior structure that affects the committed trajectory yet is unrecoverable from the boundary
  at the declared bound — a real loss, to be reported, not hidden.

---

## Phase 1 — BUILT (the benchmark first, then the autoencoders)

> **Status: built and run** — `experiments/latent_phase1/` (real numpy, seeded, outside the stdlib core).
> The benchmark was built *first* and is encoder-agnostic; `𝓕 = {E1 PCA, E2 linear-AE, E3 MLP-AE}` are
> candidates fed into it. Measured result (seed 0): reconstruction, recoverability, robustness, gauge-invariance
> **and** correlation-with-outcome all fail to separate the generator `g` from the confounder `c`; only the
> **intervention gate** does — `GeneratorScore(g)=0.99`, `GeneratorScore(c)=0.00` (`do(c)` does not move the
> outcome though `c` reconstructs, is recoverable across all of `𝓕`, and correlates with the outcome at ≈0.6).
> The confounder was caught by intervention, not by reconstruction. See `experiments/latent_phase1/README.md`.

## Phase 1 first — and the benchmark is NOT reconstruction

The temptation is to measure a learned latent by reconstruction error. That rewards the wrong thing: a
sufficiently expressive model reconstructs almost anything, and a latent that tracks the **confounder** `c`
perfectly while missing the **generator** `g` can score excellent reconstruction. This is `confounder.py`
reappearing inside representation learning — *fitting the observable is not recovering the mechanism.*

**New separator: `good reconstruction ≠ recovered generator`.** So Phase 1's benchmark is a *hierarchy*, run in
order, where each tier is a stronger test than the last and reconstruction is merely the entry gate:

```
1. reconstruction              can the decoder rebuild the observable?         (necessary, weakest — entry gate)
2. intervention relevance      do latent dims that matter CHANGE the trajectory under F? (attribution: necessity)
3. topology recovery           WHERE in the intervention graph does the factor sit?      (root vs mediator vs sink)
4. model-class robustness      does a latent feature survive across encoder families?    (model_relativity: ⋂ over 𝓕)
5. gauge-invariant evaluation  does the metric survive latent rotations/relabelings?      (gauge: invariance)
```

Tier 3 (topology) sits between intervention and robustness because intervention-relevance alone cannot tell a
**root from a mediator** — both move the outcome. A latent that passes Tier 2 but fails Tier 3 is exactly the
mediator case. Built and run: **Phase 2** (`experiments/latent_phase2/`) recovers the order `g→x→y` from
intervention asymmetries (`do(g)` moves x,y; `do(x)` moves y not g; `do(y)` moves nothing) — `g` root, `x`
mediator, `y` sink, `c` isolated; `g` and `x` are both Tier-2 relevant and only the topology separates them.
`survives intervention ≠ root generator`. Honest bound: `recovered topology ≠ discovered ontology` (a graph
over declared latent factors under `𝓕`, assuming a real `do()` — not a final description of reality).

Only a feature that clears tiers 2–4 is a *recovered generator* rather than a well-fit confounder. Tier 1 alone
would reward the artifact. This is where the existing machinery stops being illustrative and starts paying rent:
`attribution` asks whether a latent dimension is causal or confounded; `model_relativity` asks whether it
survives a change of encoder family (a change of `𝓕`); `ledgers` separates *reproducibility of the training run*
(epistemic) from *adequacy of the learned representation* (ontological); and every result is emitted as a
`GroundedClaim` that must declare architecture, objective, data distribution, and training regime as its floor.

## Toward an efficient codebase — orthogonal projection gates & masking matrices (forward note, not built)

The Phase-1 harness measures recoverability and gauge-invariance with `lstsq` and explicit rotations — correct
but not cheap, and it scores *factors* rather than *carving the latent*. The efficient form, for when this
becomes a real codebase: an **orthogonal projection-gate layer**. Hold a declared (or learned) orthonormal
basis `Q` (so `QᵀQ = I`), and a set of **masking matrices** `M_k = Q · diag(m_k) · Qᵀ` that project the latent
onto candidate subspaces. A caveat stated up front so it does not become a hidden floor: **the orthogonal group
is the *first tractable* gauge family, not the gauge family.** Real latent symmetries are often non-orthogonal —
scaling, permutation, affine, or nonlinear reparameterizations — and treating "gauge = orthogonal" as a
foundation would bake a convenience assumption into the base (exactly the floor-hiding move the framework
catches). Orthogonality is chosen here because it is cheap, invertible, and norm-preserving, and it is *declared*
as such. With that caveat, the orthogonal case buys:

- a **mask is gauge-fixing made explicit** — it names which subspace a claim lives in, and the orthogonality of
  `Q` is what makes "does this survive a latent rotation?" a property you *construct* rather than test by
  sampling rotations;
- the **causal subspace is the one whose mask survives intervention** — `do(·)` moves the outcome through `M_g`
  and not through `M_c`; isolating it is a projection, not a search;
- composing masks gives a cheap **information-firewall**: zero out the subspaces a downstream module is not
  entitled to read (`reconstruction`/`capability` over latents, as a linear projection).

Honest caveat, in the same spirit as everything above: an orthogonal projection only cleanly separates subspaces
when the factors are **linearly mixed and the split is real** — the moment the generator and confounder share a
nonlinear, entangled manifold (or the backdoor is unobserved), no projection matrix resolves it and you are back
at `observation ≠ intervention`. The gate makes the *resolvable* part efficient; it does not make the
*unresolvable* part resolvable. `projection ≠ disentanglement`.

## "Trust the dark" — the discipline that makes this honest

The horizon is an **Arbitrary Boundary** in the project's exact sense: declared, content-addressed, carrying its
rejected alternatives, `truth_claim = False`. Once it is declared, the rule is absolute:

- The system **may** rank, attest, reconstruct, and validate on the lit side.
- The system **must not** infer, claim, or optimize against the dark side — that is crossing a horizon it
  declared uncrossable, the precise smuggled-floor move `grounded_claim` forbids.
- A residual from the dark is a **ghost** (route attention), never a **truth** (`ghost ≠ hidden truth`).

In `ledgers`/`trajectory` terms: a claim about the dark has *no admissible epistemic coordinate* — it cannot be
stated as a `GroundedClaim` because its floor (`evidence`) is, by construction, unavailable. Trusting the dark is
not mysticism; it is declining to manufacture a coordinate where there is no evidence.

---

## Separators this direction introduces (to be earned, not assumed)

```
liquidate the schema   ≠ liquidate the floor    (the Weltlinie stays sealed)
learned                ≠ assumption-free        (the encoder is your 𝓕)
define the horizon     ≠ cross it
trust the dark         ≠ know the dark
gauge-dependent        ≠ real
compressed             ≠ complete
latent                 ≠ truth                  (Z is a representation, not the world)
good reconstruction    ≠ recovered generator    (a latent can fit the confounder c and miss the generator g)
```

## Build sequence (real-ML, phased — every number measured, none illustrative)

```
Phase 0  seal the core, define the representation boundary           (constraint — done conceptually)
Phase 1  minimal encoder/decoder over committed state; reconstruction + generator-recovery
Phase 2  declared symmetry + Noether absence inference over Z
Phase 3  gauge-invariant validation metric (the keystone)
Phase 4  leakage firewall over the latent (privacy funnel, learned)
Phase 5  holographic boundary→bulk compression with an information bound
```

## Honest scope

This is a research direction, not a result. It requires real artifacts (an encoder, a latent space, trained
weights) and real estimators; the moment those exist, every claim here becomes a *measured* one — or fails, and
the failure is recorded like the Causal Continuity Hypothesis was. Until then this document is a **declared map
of intent**, and per the discipline it documents, it is `not_a_truth_claim`. The renderer's purpose is unchanged:
produce a coherent high-fidelity experience from a verified world model while making its assumptions visible —
now with the assumptions, and the horizon, learned rather than hand-written.
