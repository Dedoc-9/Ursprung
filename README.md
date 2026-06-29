# Ursprung

A deterministic high-fidelity renderer that treats rendering as a **perception layer over an authoritative
world model** — and, underneath the renderer, a **provenance-centered runtime that refuses to let state outlive
its explanation.** The renderer is the *first client* of that runtime, not the whole of it: a simulation, an
agent, or a world generator are equally valid clients — and the **`weltwerk/` verification kernel** (see
*weltwerk* below) is the runtime's most developed client today (the **index** just below maps every arc — what
each one pioneered and what it is for). Ursprung consumes the sealed `Reality_Engine`
(Chronicle/Dentatus) workbench read-only as its verification substrate; the workbench supplies the deterministic
kernel and the integrity discipline, and Ursprung is the renderer projected off the committed trajectory.

Underneath the renderer, the provenance runtime and its [`experiments/live_world_kernel/`](experiments/live_world_kernel/)
instruments form a dynamic **Epistemic Runtime Environment (ERE)** — a layer that governs *claim integrity* rather
than hardware resources, and is therefore explicitly **not** an operating system: it allocates *truth*, not CPU or
memory. Every claim carries two orthogonal fields — **maturity** (does the thing exist: `IMPLEMENTED` / `SCOPED` /
`UNDERCOMMITTED`) and **evidence** (what it rests on: `MEASURED_BY_INTERVENTION` / `MEASURED` / `DECLARED` / `N/A`) —
under one load-bearing invariant: *evidence may not exceed what maturity licenses.* That no-inflation rule is
enforced at three layers — in software (`claim_ledger`), as policy (`rsi_engine`'s promotion gate), and compiled to
logic gates (`no_inflation_latch`, where an over-claim is a forbidden state the wiring cannot store). Offshoot
framings of the same discipline: **auditable-epistemology infrastructure**, a **Verified Improvement Dynamics
analyzer** (the RSI decomposition — capability, branching, generativity, orbit), and **gate-level no-inflation
enforcement**. No claim anywhere — including this repository's own — is exempt from the rule.

That analyzer's central result is a *coherent* negative. Recast "recursive self-improvement" as a measurable
condition and the toy domain returns **Type B — frontier exhaustion**: the expansion multiplier is not a scalar but
a function of state, `m_novel(Sₜ)`. It reads **supercritical** when sampled across random states (the deceptive
"green light") yet **subcritical along any actual improvement trajectory** (`m_novel(s_high) ≈ 0.53 < 1`), so the
system consumes its own frontier and its orbit converges into a basin. The suite reports **both** views side by side
and refuses to average the disagreement away — because the disagreement *is* the finding: a space-pooled metric
would falsely report success while the running trajectory chokes itself into a dead end. The object was never `m`;
it was `m_novel(Sₜ)` along the committed trajectory.

```
authoritative world state → deterministic snapshot → visual interpretation → GPU execution → presented frame
```

**Author:** Daniel J. Dillberg · **Contact:** [bigdilly95@gmail.com](mailto:bigdilly95@gmail.com)
**License:** [AGPL-3.0-only](LICENSE)

The renderer never discovers truth; it manages where its approximations fail. Its one-line philosophy:
**arbitrary boundaries require deterministic handling, and finite fidelity should be allocated by expected
future failure cost, not present visual complexity.**

## The index — five arcs, what each pioneered, what it is for

The repository is not one program but five arcs sharing one discipline (`integrity ≠ truth`; every claim graded,
every result falsifiable, every boundary stated). They are listed in order of how the work grew; none is "the
center" — the honest, per-component graded index with a `does_not_show` for each is [`method.md`](method.md).

| Arc (where) | What it pioneered | What it is for |
|---|---|---|
| **The renderer** — `ursprung/`, `loop.py` | Rendering as a **provably observer-only** perception layer (replay-identical even with the VIEW corrupted every tick), and the **`ranking ≠ allocation`** split — *what matters* and *what is expensive to represent* are different objects (water-filling under a resistance tensor). | Allocating finite fidelity by expected future failure cost; deterministic replay; a reference for any renderer/sim that must never let presentation move committed truth. |
| **Information firewall & measurement discipline** — `ursprung/` M10–M21, `ursprung/perception/` | **"The defense is the leak"** (the system's own timing/reaction/absence/cost is a side channel) and **`observation ≠ intervention` as a *measured* boundary** — a backdoor that reconstructs, is gauge-invariant, and correlates ≈0.6 still fails because `do(c)` doesn't move it. *Security = non-identifiability under bounded access.* | Anti-cheat / fog-of-war disclosure, mutual-information leak auditing (`channel_discovery`), agent/RL observation governance — reporting what is leakable *to which observer class*, never a bare "safe." |
| **weltwerk — the verification kernel** — `weltwerk/` | A model-checker-turned-**verification kernel** with a Proof-Obligations ledger and a **judge→compiler** epistemic runtime: `Grounded[T]` (an action fires only behind a verifier proof) + an orchestrator with two chokepoints; plus a deflationary, **bounded** RSI result. | Verified-config/policy checking, signal-vs-confounder-leak auditing (`residual_channel`), grounded-action gates for autonomous agents — each answer an `AnalysisResult`, each action `Grounded`. |
| **The empirical phase** — `experiments/` | That the provenance discipline **survives learning**, and a **fair, sealed-observer GPU metrology harness** that *falsified the project's own* spatial allocation hypothesis on silicon (then supported its conditional temporal form); a RealityKernel **Rust CORE verified under concurrency**. | A falsification-grade perf A/B harness (equal *measured* budget, Pareto-vector error); a provenance kernel for any stateful system; auditing self-improving / auto-tuning AI loops. |
| **Sibling-kernel hardening** — `DVSM/`, `Rust/`, `GATEWAY_SPEC.md` | The same discipline pointed **outward** at an external research kernel, collapsed into a single dependency-free **fail-closed integrity gateway** (`ursprung-gateway`) with two **type-level** honesty invariants and a streaming, bounded-memory reader. | Auditing third-party deterministic kernels (reference-relative); a proof-gated claims/compliance layer (infrastructure VERIFIED, financial value SPECULATIVE); a single-binary integrity monitor. |

Honest framing for the whole table: every bench number is **constructed and expires on real silicon** unless it
says otherwise; the renderer/firewall/empirical arcs are the developed line, the sibling-kernel arc is
**adjacent, not an advancement** of the renderer thesis (`adjacent ≠ on-mission`). Grades are re-checkable by
re-running the gates.

> **Status (current).** The conceptual arc is complete (a deterministic stdlib suite — `tests/test_ursprung.py`
> prints the authoritative count, **506 at last run**; counts drift as milestones land, so re-run rather than trust
> a number here), the empirical phase ran,
> and it has **crossed onto real silicon all the way through the summit and into the temporal arc**: the Rust
> CORE port is verified (`cargo test` 10/10) and the GPU benchmark is verified on hardware —
> `experiments/bench_gpu_real`, **M1–M6c (spatial) plus M6d / T1–T4 (temporal)** on an ASUS ROG Xbox Ally X
> (Radeon 890M, Vulkan): the timestamp ruler exists, scales with real work, binds every measurement to a stable
> world-identity digest across compute *and* render passes, compares allocation policies *fairly* at equal
> measured GPU-tick budget (M5), and on **sealed, neutral perceptual rulers** (spatial M6a, temporal T2) put the
> Causal Continuity hypothesis through genuine, non-circular gates. **The verdict is a measured boundary, not a
> win** — and the *same* unbiased apparatus moved the hypothesis both directions: the **spatial** strong claim
> ("causal allocation generally beats uniform at equal budget") was **falsified**, leaving only a conditional
> form (informative priors *and* the variance-optimal concentration exponent `difficulty^(2/3)`, not
> `difficulty^1`); the **temporal** form came back **conditional-positive** (allocating by expected future causal
> loss helps across frames); and the **hidden-future** test (T4) is recoverable *only above a precursor
> reliability threshold* — below it, acting on a weak signal is **worse** than uniform. Status is therefore
> **`conditional_on_neutral_ruler`**, never a law; the whole measured boundary is consolidated in
> [`docs/BOUNDARY_MAP.md`](docs/BOUNDARY_MAP.md). Alongside the benchmark, a family of small **observe-only
> instruments** (`experiments/live_world_kernel/`) now probes the runtime side — an embedded-authoring kernel
> (16/16), a convergence/provenance stack that *earns* boundaries rather than asserting them (the `fidelity_gap`
> extraction pair audits real third-party code, separating a recoverable model defect from a genuine runtime
> frontier), and a **verified-self-improvement decomposition** that reduces "can it recursively self-improve?" to
> two measurable branching means — `m_offspring` (reproduction) and `m_novel` (frontier expansion) — estimated
> under an external verification regime. Every instrument self-tests; the durable artifact is the apparatus, not a
> verdict. **No claim here exceeds what a runnable bench shows.**

## weltwerk — the verification kernel

[`weltwerk/`](weltwerk/) is where the repository's active work now lives: a **verification kernel** with
interchangeable proof engines, a Proof-Obligations ledger, an epistemic-runtime layer, and applications — the
most developed realization of the ERE discipline described above, turned on *world-model verification* rather
than rendering. Same no-inflation rule, validity-not-outcome self-tests, falsifiers, and separators. Pure-stdlib
core; z3 optional and confined to `solver_adapter*`. Each subfolder has its own README with exact run commands.

- **The kernel ([`weltwerk/verify/`](weltwerk/verify/)).** A model checker that became a verification kernel:
  `TransitionRelation` (semantics) → `VerificationEngine` (search) → `VerificationResult` (contract); engines
  plug in behind the result contract (`engine ≠ semantics`). An explicit-state BFS reference engine plus symbolic
  SMT engines (z3, approaches A and a CANDIDATE B). Grading is honest and mechanical: **CLOSED** = proof over the
  chosen action alphabet + transition function (carries a re-derivable `ReachabilityCertificate`); **BOUNDED** ≠
  proof; **VIOLATED** ships a replayable witness `Trace`. The `AnalysisResult` honesty contract cannot be
  constructed without a scope + ≥1 `Limitation`; `diagnose` / `counterfactual` / `repair` all project through it.
- **The Proof-Obligations ledger** ([`PROOF_OBLIGATIONS.md`](weltwerk/verify/PROOF_OBLIGATIONS.md) /
  [`EVIDENCE_GRAPH.md`](weltwerk/verify/EVIDENCE_GRAPH.md)). The kernel advances by *closing obligations*, not
  adding features — each converts an intuition-terminating chain into executable evidence. **PO-1 … PO-10 are all
  built and run-green**: oracle soundness (`agreement ≠ soundness`), certificate independence, boundary
  immutability (the map cannot move the judge), counterfactual accuracy vs an exhaustive gold, repair
  grade-stability (a `RESTORED_WITHIN_BOUND` shown to flip at 2K; `restores-(M,E,K) ≠ safe`), Approach-B
  differential over a generated distribution, abstraction admissibility (`abstract-CLOSED ⇒ exact-CLOSED`),
  honesty-contract universality, and the two RSI bounds.
- **The RSI result (bounded on both sides).** A deflationary, executable answer to the same recursion question
  the renderer arc raised with `m_novel`: PO-6 shows the natural restore task is **one-shot** (a single linear
  policy wins at budget B=1), and PO-5 shows that on a *constructed not-one-shot* (XOR-shaped) task an iterated
  loop delivers **bounded, saturating** accrual while one-shot + 4×-data stay at chance. Recursive improvement
  here is **real but bounded, task-gated, first-order** — never open-ended or second-order. `iteration ≠ open-ended`.
- **The epistemic-runtime layer (judge → compiler).** Reusable, domain-agnostic modules: `residual_channel.py`
  (the confounder-conditioned-MI firewall — `audit(X,Y,Z)` decides signal-vs-confounder-leak; `residual-CMI ≠
  channel`; `proves-the-procedure ≠ proves-the-phenomenon`); `claim_ledger.py` (the epistemic ladder as an
  enforced `Claim` template; refuses ungraded/unfalsifiable/boundary-free claims); `epistemic_types.py` +
  `enforced_transition.py` (`Grounded[T]` cannot be constructed without a verifier proof; `require_grounded`
  refuses a raw/ungrounded state mutation *before* any effect — the no-inflation rule moved into the type system;
  `grounded ≠ true`); `certificate_compiler.py` (a no-search 1-step inductive `ConstraintCertificate`;
  `verify ≠ prove`); `frontier_gate.py` (reads `m_novel` → PIVOT on subcriticality; escape graded bounded).
- **Hot-swap ([`weltwerk/verify/hotswap/`](weltwerk/verify/hotswap/), PO-11/12).** Live program hot-swapping as
  a verified bounded search behind the frozen contracts: a stream-preservation certificate (`π∘μ=π`),
  candidate-ranking swap planning at equal budget, and a built-in falsifier (deferred-race flip@2K, race@1).
- **Applications.** [`weltwerk/halvorsen/`](weltwerk/halvorsen/) — the Halvorsen chaotic attractor: exact-invariant
  floor (`∇·f=-3a`, C₃ symmetry), a trapping certificate *honestly rejected* for a quadratic V
  (`empirical ≠ certified boundedness`), the FP `determinism ≠ reproducibility` ghost, differential-on-measures-
  not-paths, a telemetry anomaly engine (fault vs sensor-misspec) and a fail-closed safety-gate mechanism.
  [`weltwerk/verify/snowflake/`](weltwerk/verify/snowflake/) — the "does morphology encode a language?" audit:
  every information-theoretic representation reduces to the field-driven growth law; the decisive test is
  field-conditioned inter-branch CMI (predicted 0) — the worked example that produced the reusable firewall.

## DVSM, the Rust ports, and the integrity gateway (the sibling-kernel hardening arc)

A newer arc points the *same* verification discipline **outward** — at an external research kernel, at std-only
Rust ports, and at a proof-gated commercial layer — and collapses the result into a single fail-closed binary.
These are **experiments and reusable layers adjacent to (not an advancement of) the renderer thesis**:
`adjacent ≠ on-mission`. The honest, graded index of the whole repository — every component with a maturity grade
and a `does_not_show` — is [`method.md`](method.md) at the repo root; read it first for orientation
(`written ≠ true` — the grades there are a falsifiable claim, re-checkable by re-running the gates).

- **[`DVSM/`](DVSM/) — Python auditors of an EXTERNAL `DVSM-π+++` kernel.** A `coupling_audit` forbidden-coupling
  CMI firewall (built on `weltwerk/verify/residual_channel`), an `invariant_ledger` that caught a κ-skew
  **VIOLATED** on the diagonal, a `kappa_remediation` that flips it **CLOSED** (`κ←(κ−κᵀ)/2`), and a
  `discrete_certificate` that is a **sufficient condition, not a stability proof** (`2‖κ‖_F·σ<λ ∧ dt·λ≤1 ⇒ ρ<1`).
  One gate — `python DVSM/verify.py` — runs **12 suites + a LIVE commercial gate**, one exit code. Every verdict
  is **reference-relative**: it audits a reduced Python reference, never the shipped Rust kernel
  (`reference-model ≠ authoritative-kernel`; `proves-the-procedure ≠ proves-the-phenomenon`).
- **[`DVSM/commercial/`](DVSM/commercial/) — proof-gated claims.** A buyer-facing claim ships only if a
  *discharged* obligation backs it (+ a HYPE-lexicon ban); the compliance doc is *generated from* the gated ledger
  so it cannot drift past the proofs. Both languages load one **single-source manifest** (`ledger.tsv` +
  `obligations.tsv`), and the gate is **live-bound** to a fresh build receipt. Infrastructure is VERIFIED; the
  **financial value is SPECULATIVE** (no users) — de-risking, not revenue. `warranty ≠ proof`; `receipt ≠ proof`.
- **The Rust ports (`Rust/` = crate `ursprung`, plus `DVSM/reality_core/`, `Rust/menger_telemetry/`).** Std-only,
  zero-dependency. The `ursprung` crate ports the fundamentals + the Epistemic Runtime Orchestrator, with two
  invariants enforced **by the type system** rather than a runtime re-check: `AnalysisResult::new` returns a
  `Result` (an analysis with no scope or no limitation cannot be constructed), and `Grounded<T>` holds its value
  in a private field behind a checked constructor (holding one *is* the witness that it was verified). The Rust
  `residual_channel` is **differential-tested against the Python reference** (MI/CMI value-parity to 1e-9 + null/
  channel decision-parity; `decisions match, floats need not`). `cargo test` in `Rust/` is **65 green**; the crate
  ships **compile-unverified** until that run is green on the user's machine.
- **[`GATEWAY_SPEC.md`](GATEWAY_SPEC.md) → the `ursprung-gateway` binary (BUILT, cargo-green).** A single,
  dependency-free, fail-closed *integrity gateway monitor* that composes ingestion → obligation-lift →
  proof-gated ledger into one CLI. L1 ingestion **streams the telemetry dump end-to-end** (synchronous
  `BufReader`, bounded memory **O(record)**, no whole-file slurp — proven decision-equivalent to the whole-file
  parser, including under one-byte-at-a-time fragmented reads); L4 is the proof-gated claim gate over the
  single-source manifest, live-bound to a build receipt. The honest boundaries are stated, not hidden: the
  verdict is a **commitment, not a signature** (no PKI); the certificate is a **sufficient condition, not global
  stability**; L2 (contraction certifier) and L3 (CMI firewall) need typed inputs (κ matrices, `(X,Y,Z)` samples)
  a frame dump cannot supply, so those air-gaps are reported **non-liftable**; "real-time/low-latency" is
  **UNMEASURED**; and it is a technical conformity check, **not** regulatory compliance. `parts ≠ whole`;
  `integrity ≠ truth`.

## What is proven, what you get, and where it goes next

**What is proven** — each claim ships with an executable bench and a negative control. Constructed-world
claims carry an explicit "expires on real silicon" bound; several have now *crossed* onto silicon (the Rust
CORE port and the GPU ladder) rather than expired. Nothing here is asserted without a runnable check.

- **The renderer is observer-only.** Replay identity, view-perturbation invariance, and ordering invariance:
  the VIEW layer cannot move the committed trajectory even when deliberately corrupted every tick
  (`integrity ≠ truth`).
- **Priority and allocation are different objects.** A *failed* hypothesis became the measured result that a
  two-stage `ranked_waterfill` strictly beats proportional / uniform / distance / visibility on the
  future-causal residual — *knowing what matters* is not *knowing where representation breaks*. (Constructed
  bench; the silicon sequel below is what tested whether it survives a *neutral* metric.)
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
- **The benchmark can reject its own hypothesis — on silicon, in both directions.** The GPU ladder
  (`experiments/bench_gpu_real`, **M1–M6c spatial + M6d / T1–T4 temporal** on an ASUS ROG Xbox Ally X /
  Radeon 890M, Vulkan) builds a ruler that is fair *by construction* — equal *measured* GPU-tick budget
  (over-spenders refused), error as a Pareto vector never a scalar, dominance refused below the *measured* noise
  floor (ε-dominance) — and a **sealed observer**: a policy's type signature cannot read the ruler it is scored
  against, so "optimize the metric" is structurally impossible. Pointed at the project's *own* preferred
  allocation policy, it **falsified the spatial form**: at equal budget on a neutral perceptual metric,
  causal-waterfill did not beat uniform; the sweep then showed its allocation exponent was wrong (∝ difficulty¹
  over-concentrates vs the variance-optimal ∝ difficulty^(2/3)), leaving a *conditional* result. Then the *same
  apparatus*, re-pointed at the **temporal** form (allocate by expected future causal loss across frames, on the
  Rust kernel), returned a **conditional-positive** — and the hidden-future test (T4) found the result holds
  *only above a precursor-reliability threshold*, below which a weak signal is worse than uniform. A bench that
  can catch its author being wrong — and right — on the same neutral ruler is the asset: `benchmark gain ≠
  universal`, and neither is a benchmark loss. Whole boundary in [`docs/BOUNDARY_MAP.md`](docs/BOUNDARY_MAP.md).

*"Verified" here means the runtime's **distinctions survived a substrate transition** — not that the runtime is
complete. Proven: the kernel invariants, semantic preservation across implementations, the tested failure
distinctions, lineage preservation within the benchmark envelope, and — on GPU silicon — that a fair, sealed
benchmark falsifies an internally-coherent allocation claim (spatial) rather than rubber-stamping it — and
**supports the conditional temporal form on the same neutral ruler** (M6d / T1–T4). Frontier (below): broader
scale, distributed persistence, learned-world verification, a real-time world substrate, and a real estimator
under intervention scarcity. The narrower claim is the stronger one.*

**What you get** — a **specification + reference implementation + measurement discipline**, not a turnkey
engine. Concretely: a *provenance-preserving execution substrate* (the kernel) with a verified Rust core that
refuses to let state outlive its explanation; a *fair, falsification-grade GPU/perf metrology harness*
(equal *measured* budget, Pareto-vector error, sealed observer — verified on silicon, and proven by rejecting
the project's own hypothesis); a transplantable, re-validatable *information-firewall / disclosure-audit*
family for partially-hidden shared worlds (anti-cheat, fog-of-war); a *fidelity-allocation economics*
(priority ≠ allocation, the resistance tensor, shader/PSO prewarm); a *causal-attribution procedure* that
separates a generator from a confounder/artifact for residuals, anomalies, and ML features; and an
*LLM-on-track methodology* (`observe → hypothesize → implement → verify → record`). Every result names its
estimator class and coverage boundary instead of declaring "safe."

**Where it goes next** — the kernel is the minimal center; everything else is a **client**. A renderer, a
physics step, an agent, and a world generator all *consume* the kernel — **transition history is the center,
not the world**. Real silicon has arrived and the benchmark arc is *complete through its temporal form*: the GPU
benchmark runs **M1–M6c (spatial) + M6d / T1–T4 (temporal)** on an ASUS ROG Xbox Ally X — the ruler exists,
measures real work, binds to world identity across compute and render passes, compares policies fairly at equal
measured budget (M5), and on sealed neutral perceptual rulers ran the genuine Causal Continuity gates: the
**spatial** strong claim **falsified** → conditional; the **temporal** form **conditional-positive**; the
**hidden-future** form (T4) recoverable only above a precursor-reliability threshold. The multi-frame test that
was the prior frontier — decorrelating causal-consequence from present render-difficulty across frames, which
the still-frame rig could not do — is now **built** (T1–T4, on the Rust kernel) and consolidated in
[`docs/BOUNDARY_MAP.md`](docs/BOUNDARY_MAP.md). The scoped frontiers that remain genuinely un-faked: the Rust
CORE at real scale (1e6–1e8 lineage, frame-loop integration, the Windows sub-granularity timing question); the
first world-loop client built *on top of* the kernel — toward which `experiments/live_world_kernel/` is the
first step (an embedded-authoring kernel + observe-only diagnostics, single-process logic, **not yet** under
concurrency or scale); a real estimator under intervention scarcity (unknown graph); and a real external anchor
(a verifiable delay function / proof-of-sequential-work).

What began as a renderer *philosophy* became, under benchmarking, a set of measurable **rendering economics**:
finite fidelity is a budget, every approximation is debt, and the bench — not the manifesto — decides which
allocation policy wins (and, on a neutral silicon ruler, which *doesn't* — see *Status*). The pivotal result
of that arc came from a *failed* hypothesis (see below): **priority and allocation are different mathematical
objects.**

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

1. **Reality Debt Law** *(underneath)* — every approximation incurs debt, modelled as `Debt = Approximation ×
   Persistence × Consequence`. Fidelity is treated as conserved while debt is accumulated; allocation places
   debt where future consequence is lowest. *(The product is a bookkeeping model — a chosen weighting, not a
   derived necessity: `model ≠ verified structure`.)* (`reality_debt.py`)
2. **Arbitrary-Boundary Law** — representation choices (pixel coverage, float format, LOD threshold, tick
   rate, polygons) are deterministic *conventions*, never truth claims. (`conventions.py`)
3. **Predictive Fidelity Law (PFAL / TCFF)** — spend computation where future failure cost is highest, scored
   by `R = U × C × P × S × τ`. *(The product is a weighting model, not a measured law; the comparative bench
   result is constructed-world and expires on real silicon.)* (`prediction.py`, `temporal_membrane.py`,
   `pfal_bench.py`, `tcff.py`)
4. **Polygon Reconciliation Law** — keep polygons iff abandoning them costs more than their approximation
   error; rasterization is transport, allocation is strategy. *(The rule runs over **declared** costs that
   carry their provenance — a cost without lineage is an unaccounted number: `declared ≠ verified`.)*
   (`polygon_reconciliation.py`)
5. **Temporal Fidelity Accounting Law** — under a fixed budget, fidelity gained in one dimension creates
   pressure elsewhere; the objective is *minimum consequential discontinuity under a fixed budget*, not maximum
   detail. *(Stated earlier as "Conservation"; the conserved-quantity framing is a fixed-budget accounting
   model, not a physical conservation law. Implemented as `fidelity_conservation.py`.)*

```
WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → DEBT MANAGEMENT → RASTERIZATION → IMAGE
```

These five govern **fidelity economics** — how finite rendering is spent. They are not the project's deepest
invariant, and that deepest one is deliberately *not* numbered as a sixth law, because it is a different
category: a law of the **runtime**, not of the world. (`observation ≠ intervention` is true whether this system
exists or not; *identity includes provenance* is a design requirement the runtime *chooses* to enforce.) It is
treated on its own terms below in *The Provenance Principle* — and **Law 2 (Arbitrary-Boundary) is its earliest
instance**, which is why the rest of the architecture fell out of it. More generally, each fidelity law can be
read as the **Provenance Principle applied to approximation**: every approximation, boundary choice, and
tradeoff must carry the history and assumptions that make it interpretable. The kernel did not add this to the
laws; it made explicit a contract they already obey.

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

The **Causal Continuity Hypothesis** advanced one tier on the *constructed* bench, then met the *neutral* one
on silicon and came back down. On the model world: the naive (proportional) form failed; the re-specified
water-filling form (`samples ∝ √(U·C·P · resistance)`) **passed the re-run promotion gate**
(`promotion_gate.py`, seeds 1..8), beating uniform/distance/visibility/PFAL/structural with the negative
control losing → `supported_constructed`. But that gate's metric was *itself* U·C·P-weighted — the allocator
and the judge shared assumptions, a possible self-confirming loop. **M6b/M6c broke the loop on real silicon**
(`experiments/bench_gpu_real`), comparing policies on a *sealed, policy-neutral* perceptual ruler at equal
measured GPU budget. The result: the **strong claim is falsified** (at equal budget on a neutral metric, the
causal policy as specified did *not* beat uniform — and M6c showed its allocation exponent was wrong, ∝
difficulty¹ over-concentrates vs the variance-optimal ∝ difficulty^(2/3)); a **conditional claim survives** —
causal allocation reaches and narrowly wins the ε-frontier only with informative priors *and* the corrected
exponent. Status is therefore **`conditional_on_neutral_ruler`**, not a law. The honest residue that M6 left —
it conflated *causal consequence* with *present render difficulty*, so the deepest form of the claim (dropping
present-perception `S` helps the **future**) needed a multi-frame scene where the two are decorrelated — has now
been **built and run**: the **M6d / T1–T4** temporal arc on the Rust kernel decorrelated them across frames and
returned a **conditional-positive** for the temporal form, plus a **threshold law** for the hidden-future case
(T4): a precursor signal is recoverable only above a reliability threshold ρ, below which acting on it is
*worse* than uniform — the same lesson as the M6b circular gate and M6c over-concentration. The full measured
boundary (spatial conditional-negative · temporal conditional-positive · hidden-future thresholded) is stated
once and whole in [`docs/BOUNDARY_MAP.md`](docs/BOUNDARY_MAP.md). Nothing is promoted to a law by a benchmark on
a model world, and a neutral benchmark is exactly what kept the spatial claim from becoming one while letting
the temporal one survive.

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
| `ursprung/fidelity_conservation.py` | **OBSERVER** | Temporal Fidelity Accounting Law (was "Conservation"): under a fixed budget, fidelity transferred between dimensions is a bookkeeping model, not a physical conservation law; minimize consequential discontinuity |
| `ursprung/reality_debt.py` | **OBSERVER** | Reality Debt Law: `Debt = Approximation × Persistence × Consequence`; place debt where consequence is lowest |
| `ursprung/causal_continuity.py` | **OBSERVER** | Causal Continuity (`conditional_on_neutral_ruler`): naive `∝U×C×P` failed → water-filling `∝√(U·C·P·resistance)` passed the *constructed* gate → M6b/M6c on a *neutral* silicon ruler **falsified the strong spatial claim** (conditional only: informative priors + exponent `^(2/3)`) → M6d/T1–T4 on the Rust kernel returned the **temporal** form **conditional-positive** and the **hidden-future** form thresholded (T4: weak precursor below ρ is worse than uniform) — *not a law*; constants `NEUTRAL_RULER_RESULT`, `SWEEP_M6C`, `TEMPORAL_GATE_M6D`, `HIDDEN_FUTURE_T4`; whole map in `docs/BOUNDARY_MAP.md` |
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

The full suite is a deterministic set of stdlib asserts — the printed run count is authoritative (**506 at last
run**; the count drifts as milestones are added, so re-run `python tests/test_ursprung.py` rather than trust a
number here), every milestone carrying a verified demo, a negative control, and an explicit "expires on real
silicon" bound.

- **M1 — foundation.** Invariant harness; the renderer is proven observer-only (`integrity ≠ truth`).
- **M2 — the five laws.** Reality Debt · Arbitrary-Boundary · Predictive Fidelity (PFAL/TCFF) · Polygon
  Reconciliation · Temporal Fidelity Accounting (was "Conservation"), each encoded as data/rule — the product
  forms are bookkeeping models, not derived invariants.
- **M3 / 3.1 — rendering economics.** VIEW raster slice + the Causal Continuity Hypothesis, which **failed**
  the equal-budget bench (recorded, not hidden) and became the *ranking ≠ allocation* refinement;
  `ranked_waterfill` strictly beat every control. The re-specified water-filling form **passed the re-run
  promotion gate** (`promotion_gate.py`, seeds 1..8) → `supported_constructed` — but that gate's metric was
  U·C·P-weighted, so the real-silicon **M6b/M6c** gate on a *neutral* ruler later **falsified the strong claim**
  and left only a conditional one → status now `conditional_on_neutral_ruler` (see below; never a law).
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

**The conceptual arc is complete, the empirical phase ran, and it has crossed onto real silicon** (see
*The empirical phase* below): `experiments/` carries six executed latent phases, the three provenance runtimes,
the live/latent compression bench, and the **RealityKernel** consolidation — whose **Rust CORE port is verified
on real silicon** (`cargo test` 10/10) and whose lineage-scale closure test proves *optimization cannot erase
history* to 5×10⁵ commits. And the **GPU benchmark is verified on hardware through the summit and the temporal
arc** (`experiments/bench_gpu_real`, **M1–M6c spatial + M6d / T1–T4 temporal** on an ASUS ROG Xbox Ally X /
Radeon 890M, Vulkan): the timestamp ruler exists, measures real compute *and* render work, binds every
measurement to a stable world-identity digest, compares allocation policies *fairly* at equal measured GPU-tick
budget (over-spenders refused, M5), and on sealed, neutral perceptual rulers ran the genuine Causal Continuity
gates — which **falsified the strong spatial claim and left a conditional one**, then returned the **temporal
form conditional-positive** and the **hidden-future form thresholded** (`conditional_on_neutral_ruler`; whole
map in [`docs/BOUNDARY_MAP.md`](docs/BOUNDARY_MAP.md)). A separate family of small **observe-only instruments**
(`experiments/live_world_kernel/`, below) probes the runtime side. Each is a seeded, replayable bench with its
own self-check. What stays deliberately un-faked lives behind the intentionally-unbuilt seams —
`reality_harness.NetworkChannel` (point it at a real socket), `behavioral_harness.ExperimentLayer(channel="real")`,
and the perception compiler's lookup compiler — plus:
- The **Rust CORE at real scale** — the verified port proves *correctness* under real concurrency; behaviour at
  1e6–1e8 lineage, under a frame budget, and under memory pressure (where the failure to hunt is *digest exists,
  lineage gone*) is the next substrate rung, with the Windows sub-granularity timing question (full-frame spin
  vs. raising OS timer resolution) attached.
- The **first world-loop client** built *on top of* the kernel — the point where the substrate stops being
  tested in isolation and starts carrying a world.
- **M6 — the Causal Continuity gate on real silicon (spatial summit + temporal arc both reached).** M6a–M6c: a
  sealed, neutral perceptual ruler at equal measured budget **falsified** the strong spatial claim and left a
  **conditional** one — see *rendering economics* above. The multi-frame test that was the remaining frontier —
  M6 conflated *causal consequence* with *present render difficulty*, needing a scene where the two are
  *decorrelated across frames* — is now **built**: the **M6d / T1–T4** temporal arc on the Rust kernel
  (T1 apparatus · T2 the temporal ruler · T3 the causal gate vs a non-admissible prophet · T4 hidden-future
  importance + precursor sweep) returned the **temporal form conditional-positive** and a **threshold law** for
  the hidden-future case (recoverable only above precursor-reliability ρ; below it, worse than uniform). Status
  `conditional_on_neutral_ruler`; the whole spatial+temporal boundary is consolidated in
  [`docs/BOUNDARY_MAP.md`](docs/BOUNDARY_MAP.md). Constructed-world numbers expired exactly as designed; the
  apparatus crossed onto silicon both directions.
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
**seeded, replayable** bench (numpy or pure stdlib) kept *outside* the verified renderer core so the renderer
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

## The runtime instruments — embedded authoring & observe-only diagnostics (`experiments/live_world_kernel/`)

Where the GPU ladder tests the *renderer* side, this folder tests the *runtime* side of the embedded-authoring
idea ([`docs/EMBEDDED_AUTHORING.md`](docs/EMBEDDED_AUTHORING.md)): **can a running world accept, reject, and
rewind creator actions without losing causal truth?** It is a sequence of small, sealed, self-checking
instruments — each one *earns* a boundary rather than asserting it, and none enforces or issues a verdict.
`declared ≠ verified`: everything here is single-process **logic**, not a system under concurrency, latency, or
scale.

- **`live_world_kernel.py` — the kernel (16/16).** An edit is an *event*, not a mutation: `propose()` touches a
  private speculative scratchpad; `commit()` runs an authority gate and either promotes the event into the
  shared log or rejects it and rewinds *exactly* its causal subtree. It then makes explicit the **three states
  of a fact** — **committed** (authority + log + replay, at the gate) ⟂ **irreversible** (∃ a committed
  dependent) ⟂ **durable** (∃ a recovery path independent of the failure — replica *or* deterministic
  regeneration *or* archival, **not** merely quorum). Loss of a primary-only fact is reported as *severance*,
  never a fabricated value (`compress ≠ sever`).
- **Three observe-only probes (7/7 each).** `frontier_probe.py` lets dependency outrun commitment and locates
  where the irreversibility frontier actually lives (barrier redundant / earned / insufficient) through a
  **sealed observer** (`telemetry ≠ control`). `concurrency_probe.py` treats a partition as a *hypothesis* the
  dependency graph judges — leakage + Dini-shaped convergence *only in quiescence* — and refuses to import a
  physics guarantee that does not hold (`geometric locality ≠ dependency locality`). `klein_probe.py` is the one
  topology analogy that survives as **exact mathematics**: signed-graph frustration (a cycle whose sign-product
  is −1) = non-orientability = "follow this boundary through its consequences and the meaning reverses" — the
  Arbitrary-Boundary Law's adversarial test.
- **`topology_provenance_engine.py` — the integrated audit (7/7).** Bundles the three probes over one declared
  system model and reports **three independent coherence dimensions as a vector** (structural ⟂ provenance ⟂
  spatial), refusing to collapse them into a single "coherence score" — *objectivity is not one scalar, not even
  for the auditor*. Attention signals ("look here"), never verdicts.
- **`module_graph.py` → `fidelity_gap.py` — auditing code it did not author.** `module_graph` (7/7) turns a
  *real* source tree into a model — the first test of the hardest assumption, **`SystemModel` is an
  interpretation of evidence, not reality** — and its first success is *negative*: it records its blind spots
  (dynamic/relative imports, basename collisions) rather than dropping them, and declares the provenance lens
  `NOT_APPLICABLE` to a static import graph instead of fabricating one. Pointed at two real open-source repos
  (`psf/requests`, `pallets/click`) it came back almost entirely **blind** (91 and 197 blind spots, ~0 edges) —
  a finding about *the model*, not the code. `fidelity_gap.py` (7/7) reads that blindness, names its cause
  (basename identity + absolute-only resolution, where real packages need *package-path* identity + relative
  resolution), and **proves the breakthrough**: on `click`, edges **6 → 131**, basename collisions **3 → 0**,
  **196** relative imports recovered, a real circular dependency surfaced
  (`click._compat → click._winconsole → click._compat`) — while the lone **dynamic import** is fenced as a
  **runtime frontier** a static parser can never cross (declared, handed to provenance, *never* counted as
  recovered). `resolved ≠ executed`; the gap is mapped to where the committed Weltlinie begins. (`requests`
  scans the same way: collisions 4 → 0, residual = 2 dynamic imports.) A *defensive-use* note frames the same
  structural signals for **authorized** red-team / architecture review — semantic leak = isolation surface to
  close, cycle = resilience/DoS surface, high fan-in = blast radius — holding `flagged ≠ exploitable` and
  shipping no exploit, payload, or targeting.
- **The self-description stack → a falsifiable RSI ladder (`claim_ledger.py` 6/6, `self_improvement_witness.py`
  7/7, `recursion_witness.py` 7/7; index in [`experiments/live_world_kernel/INDEX.md`](experiments/live_world_kernel/INDEX.md)).**
  The same provenance discipline turned on the runtime's *own* claims. `claim_ledger` reconciles statements about
  the kernel as **claims with commitment levels**, enforcing *evidence ≤ maturity* — an over-claim is rejected,
  not trusted. The two witnesses make **recursive self-improvement an experiment, not a definition**:
  `self_improvement_witness` *proves the provable* — a guarded, self-modifying edit measurably improves the system
  on held-out data, the gain transferring to a clean split held **outside** the loop — and `recursion_witness`
  runs the hard rung, measuring `d(capability)/dt` vs `d²(capability)/dt²` **on held-out tasks with the evaluator
  outside the optimization loop**. The reference run's verdict is **sustained, NOT recursive** (d/dt +0.076;
  d²/dt² ≈ 0 — a ceiling) and **not self-certified** (the self-estimate diverges from external reality, +0.155 vs
  +0.054). It records its own ghosts: the meta-search **stalled at 9 search coords** where the true structure was
  3, and its self-estimate ran **~4× ahead of reality**. `optimize ≠ evaluate`; `sustained ≠ recursive`; and
  "proof of RSI" is held `UNDERCOMMITTED` — unavailable *in principle* for a self-judged metric, not merely
  unbuilt. A fourth instrument, `limit_discriminator.py` (7/7), adds the **TRANSFER** rung
  (`step → sustained → transfer → recursive → open-ended`) and separates *why* the upper rungs fail — search (A)
  vs task (B) vs transfer (C) vs evaluator (D) — holding the task fixed and varying the mechanism. Its reference
  run refutes the search explanation, and pointed at a search↔evaluator coupling — but a follow-up clean width
  sweep (`inflation_vs_search.py`, 7/7) **contests** it: inflation is *persistent (~+0.07) but not explosive*,
  flat across a 31× rise in search budget, because the discrete proposal space saturates at K≈2 (a new separator,
  `optimization-pressure ≠ search-budget`). The honest standing claim is that evaluator inflation *exists and is
  stable in this regime*, not that more search amplifies it. The discriminator's self-tests were also
  the occasion for a caught error worth recording: the first version gated on *expected outcomes*
  (`strong ≥ weak`), which is itself inflation — a verification that enforces the experimenter's prior. Rewritten
  to check **validity + classifier soundness** only (`experiment-ran ≠ hypothesis-confirmed`).

The pass means the embedded-authoring idea **earned the right to be scaled**, not that it has been: the boundary
that actually decides the engine vision — concurrency at scale — is the next probe, not this one.

## Pioneering methods (what is genuinely new here)

Stated with the project's own calibration — much of this is *composition* of established research (quantitative
information flow, information design, causal identifiability, gauge invariance), and the novelty is the fusion
and the runtime, not a claim to have invented the pieces.

- **Falsification-first engineering.** Every result ships with a negative control and an explicit
  "expires on real silicon" bound, and a *failed* hypothesis (Causal Continuity) is preserved as a load-bearing
  result rather than deleted. The deliverable is "a framework for discovering where our own assumptions fail,"
  not a leaderboard number.
- **A falsifiable recursive-self-improvement ladder (`optimize ≠ evaluate`).** Re-poses "RSI" as a *measurable
  experiment* rather than a definition or a vibe: a claim ladder (step → sustained → recursive → open-ended →
  self-certified) with a sharp criterion — `d²(capability)/dt² > 0` measured on **held-out tasks**, surviving an
  **evaluator held outside the optimization loop** — plus the structural argument that the top rung is
  `NON_ORIENTABLE`: a self-judged metric cannot certify its own improvement from inside (a train-only optimizer
  drives its metric up while real capability falls). The reference run answers **NO with receipts** (sustained,
  not recursive) and surfaces *its own* stall and inflated self-estimate. Not a claim to have built RSI — a claim
  to have made the question testable, and to have a bench that can catch itself short.

  > **The verified-improvement branching criterion — theorem, model, and conclusion kept separate.**
  >
  > *The theorem (classical, true, conditional — Bienaymé–Galton–Watson).* For a branching process where each node
  > independently has offspring of mean `m` and generating function `f(s)=Σ pₖ sᵏ`, under standard non-degenerate
  > assumptions: `m ≤ 1` ⇒ extinction with probability 1; `m > 1` ⇒ extinction probability is the smallest fixed
  > point `q < 1` of `f`, so the process survives with probability `1 − q > 0` (never certain for one trajectory).
  > This is classical; `experiments/live_world_kernel/verified_improvement_theorem.py` is a Monte-Carlo check that
  > reproduces it.
  >
  > *The modeling claim (NOT a theorem).* That the stream of **verified** self-edits — those passing external +
  > replicated + calibrated checks — *can be modeled as* such a process, with each verified edit producing a random
  > number of verified successors of reasonably stable mean `m_verified`. This is an abstraction, and real systems
  > break it: `mₜ` drifts, improvements interact, resources deplete, new capabilities open new edit spaces,
  > verification standards evolve. **Open-ended RSI is itself a *departure* from Galton–Watson** (non-stationary,
  > generative offspring space) — so GW is the *null* model and the interesting case is where it fails. The
  > simulator can verify the theorem; it cannot verify the modeling claim, which is empirical per domain.
  >
  > *The defensible conclusion (conditional).* **If** verified self-improvement is modeled this way, **then**
  > `m_verified` is the critical quantity: `m_verified ≤ 1` ⇒ the verified-improvement stream eventually goes
  > extinct; `m_verified > 1` ⇒ sustained growth with nonzero probability. Whether a given domain/architecture has
  > `m_verified ≤ 1` or `> 1` is **empirical**, not decided by the theorem.
  >
  > *The contribution* is not the extinction theorem but **(a)** the *verified branching mean* `m_verified =
  > E[verified improvements generated by a verified improvement]` as an operational scalar, and **(b)** the runaway
  > signature **`m̂ > 1 ≥ m_verified`** (proxy mean above 1, verified mean at/below — looks self-sustaining, goes
  > extinct). It reframes "does RSI exist?" into the measurable *"can the system establish `m_verified > 1` under
  > external verification?"* **Consistent-with (domain-specific, not universal):** the toy domain's evidence is
  > consistent with `m_verified < 1`, which explains the single-promotion plateau without weak search, compute, or
  > tuning — a property of that toy, not a general claim.
- **RSI as a decomposition, not an engine — and a *relocation*.** The branching theorem turned "recursive
  self-improvement" into a measurable ladder, and the instruments carried it through: a *self-improvement step*
  (real, `self_improvement_witness`), *recursion* `d²/dt²` (not observed — plateau, `recursion_witness`),
  *reproduction* `m_offspring`, and *frontier expansion* `m_novel` (net-new reachable verified states per verified
  parent; invariant `m_novel ≤ m_offspring`, and the gap *is* the overlap). The thesis: **RSI requires
  generativity of the verified-improvement space, not merely successful self-modification.** That *relocates* RSI
  from a property of the optimizer to a structural property of the **(system, domain, verification-regime)
  triple** — the same optimizer reads supercritical under a lax regime and subcritical under a strict one
  (`m̂ > 1 ≥ m_verified` is the runaway). In the toy domain the measured `m_novel(s)` *declines through 1* with
  capability (≈ 4.64 → 1.93 → 0.53): generativity is highest when the system is *worst* and depletes as it
  improves. The output is always an estimate under a stated regime, never "this domain has/lacks RSI," and even
  the relocated question keeps the asymptotic ceiling — only ever "frontier still expanding after N." The verified
  arc — `rsi_engine` (promote only what's externally verified + replicated + calibrated), the branching theorem
  and its proof-check, and `verified_branching_estimator` / `generativity_estimator` — is the apparatus, and its
  honest result is a *sharper question*, not a verdict on RSI.
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
- **A fair GPU/perf comparison harness (metrology, not marketing).** `experiments/bench_gpu_real` is a
  transplantable pattern for performance A/Bs that can't cheat: compare only at **equal *measured* GPU-tick
  budget** (a policy that spent more is *refused*, not crowned), report error as a **Pareto vector** never a
  summed score, bind every measurement to the identity of what it measured, and treat a zero/negative interval
  as a recorded ghost. Drop it onto any "policy A beats B" GPU question where a scalar score would smuggle the
  conclusion — and it earns its keep by moving the verdict *both* directions on the same neutral ruler:
  M1–M6c spatial + M6d/T1–T4 temporal on an Ally X, where the sealed ruler **falsified** the project's own
  preferred spatial allocation policy and then **supported** its conditional temporal form — never
  rubber-stamping either.
- **A provenance kernel for any stateful system.** `experiments/reality_kernel` (Artifact / Event /
  CommitReceipt / Query, with a Rust CORE verified under concurrency) is a domain-agnostic, event-sourced core:
  every transition emits a *receipt* (a record, never an authorization), and **absence is queryable** —
  `present / absent / unresolved / unaccounted`. Usable as the spine of an editor, a simulation, or a
  collaborative tool that must answer *why is the state this way, who introduced it, and what is missing.*
- **An "optimization cannot erase history" guarantee for caches/compression.** `live_latent_provenance` +
  `lineage_scale`: a hot path may carry only a digest while the lineage resolves on demand, but a compression
  that drops the pointer is caught as *severance*, never silently allowed. Transplantable to telemetry
  pipelines, model-artifact stores, and event logs that compress state yet must stay auditable.
- **Agent / RL observation governance.** The perception loop (`disclosure` + `ursprung/perception/`) bounds how
  much of a hidden world an agent-observer may see while preserving task utility, and classifies the observer's
  reconstruction regime (bounded / tradeoff / cascade-collapse) — a fit for agent sandboxes and AI evaluation
  where you must reveal enough to act without leaking the whole state.
- **Authorized red-team / pentest *phase-1* reconnaissance (`experiments/live_world_kernel/`).** The
  auditable-epistemology stack maps a codebase you are authorized to assess and surfaces **architectural /
  boundary** weakness that CVE/port/SAST scanners miss — blast-radius concentration (high fan-in), resilience /
  DoS surface (import cycles), isolation / lateral-movement smells (cross-package leakage), and dynamic behavior
  static analysis misses (`runtime_witness`). Its differentiator: **epistemic provenance on every finding**
  (`MEASURED` / `DECLARED` / `CONTESTED`) instead of a risk score, so a lead knows which findings are confirmed,
  which need runtime confirmation, and which are contested between witnesses. **Phase 1 only — it maps, it does
  not exploit:** `flagged ≠ exploitable`, no exploit/payload/targeting, runs on trusted/authorized targets (the
  runtime trace executes import-time code), and it declares its blind spots (a static graph cannot find the
  irreversibility frontier; `runtime_witness` coverage is currently over-counted — see
  [`docs/EPISTEMIC_ACCOUNTING.md`](docs/EPISTEMIC_ACCOUNTING.md)). *Find and close your own structural attack
  surface before an adversary maps it from a leak.*
- **Auditing self-improving AI / auto-tuning / agent pipelines (estimate, not verdict).** Any loop that edits its
  own configuration, prompts, weights, or search policy and claims to be getting better — AutoML, self-refining
  agents, eval-driven/RLHF tuning, "self-improving" model pipelines — can be audited with the verified-improvement
  stack: gate every self-edit on **external + replicated + calibrated** gain (`rsi_engine`), then estimate the two
  branching means `m_offspring` (verified edits produced per verified edit) and `m_novel` (net-new verified
  capability reached) under a *declared* verification regime (`verified_branching_estimator`,
  `generativity_estimator`). The differentiator is the **runaway detector `m̂ > 1 ≥ m_verified`** — a pipeline
  whose internal/proxy score is climbing while *external* capability is not is fooling its own evaluator, and that
  gap is reported as a number rather than hidden behind a rising dashboard. Output is `m ± CI` with a
  "CI-excludes-1?" informativeness test (it says *cannot distinguish under current sampling* when the interval
  straddles 1), never "this system has RSI." Use it to tell whether an automated self-improvement loop is
  genuinely compounding, plateauing, or quietly overfitting the very metric that authorizes its own promotions —
  and, via `m_novel(s)`, whether its frontier of new verified opportunities is *expanding or depleting* as the
  system improves.

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
- **Verified-on-silicon credibility (M1–M6c spatial + M6d/T1–T4 temporal).** The hardware results aren't
  performance boasts — they're *metrology*: the project proved its own measuring instrument is trustworthy
  (ruler exists, scales, binds to identity, compares fairly) *before* making a performance claim, and then used
  that one instrument to move its own hypothesis **both ways** — falsifying the preferred *spatial* causal
  allocation policy (M6b/M6c) and supporting the conditional *temporal* form (M6d/T1–T4) on the same neutral
  ruler. A system that can be caught being wrong — and right — by its own bench is the credibility asset, the
  opposite of a suite that opens with a win.

**For researchers / reproducibility (the cross-domain frame):**

- **Cross-domain provenance accounting.** The recurring operation — *object + the conditions that license it*
  (claim+floor, edge+support, latent+identification-cost, edit+lineage, **absence+diagnosis**) — is a discipline
  for any computational science that needs results to carry *how they became admissible* across transformations,
  learning stages, and substrate changes. The rarest single piece is the last: **absence as a first-class
  object** (`NonRecovery`) — recording *why something is unknown*, with a typed diagnosis, instead of a silent
  gap.
- **Category-mistake hygiene.** The separator catalogue (`integrity ≠ truth`, `reconstruction ≠ generator`,
  `correlation ≠ cause`, `observation ≠ intervention`, `declared ≠ verified`, `stable ≠ causal`) is a usable
  checklist for spotting where an analysis has collapsed distinctions that matter. Honest scope: it is a
  *discipline a human applies* with worked examples, not an automated detector you can point at arbitrary code.
- **Falsification-as-record.** A preserved failed hypothesis (Causal Continuity's naive form) and the
  re-specification it forced is a template for keeping negative results load-bearing instead of deleting them —
  the habit that produced most of the architecture.
- **Epistemically-typed diagnostics / provenance-under-degradation (`experiments/live_world_kernel/`).** A
  transferable pattern for any analysis tool: carry `measurement → status → provenance`, not `measurement →
  status`. Every claim is tagged `MEASURED` / `MEASURED_BY_INTERVENTION` / `DECLARED` / `CONTESTED` / `N/A`;
  evidence strength is a *partially-ordered* ceiling that may only fall as a claim passes through extraction
  (downgrade), disagreement (refinement / `CONTESTED`), execution (orthogonal blind spots), and coexistence
  (no global winner). The capstone ledger ([`docs/EPISTEMIC_ACCOUNTING.md`](docs/EPISTEMIC_ACCOUNTING.md)) marks
  every instrument `BUILT` / `CONTRACT` / `ABSENT` and *leads with the misstatements its own comb caught* — a
  reusable discipline for tools that must never claim stronger knowledge than the witness that produced it.

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
[`docs/BOUNDARY_MAP.md`](docs/BOUNDARY_MAP.md) — **the measured boundary map for causal allocation**, stated
once and whole: spatial conditional-negative (M6a–c) · temporal conditional-positive (T1–T3) · hidden-future
recoverable only above a precursor threshold, where a weak signal is *harmful* (T4). The artifact worth
preserving. [`docs/EMBEDDED_AUTHORING.md`](docs/EMBEDDED_AUTHORING.md) — a **design note** (direction, not a
verified result) on the editor as a capability of the world: an edit is an event; guarantees captured at the
irreversibility frontier; *minimum under uncertainty*; the sealed reserve as the answer to Hyrum's Law —
closing on the Arbitrary-Boundary Law. [`docs/SELF_MODIFICATION_BOUNDARY.md`](docs/SELF_MODIFICATION_BOUNDARY.md)
— a **boundary probe** (measurement contract, not a roadmap, not an architecture): where does the commit
frontier stay *globally* definable vs *only locally* definable when a runtime modifies its own modification
mechanism? Three actors (state · mechanism · validator), three cases (external control · authority self-edit ·
provenance self-edit), three categorical axes (orientability via `klein_probe` · frontier locality via
`frontier_probe` · recovery integrity via the kernel's severance). Names the boundary without assuming it
resolves; concurrency kept deliberately separate; `declared ≠ verified`.
[`docs/AUTHORITY_ARBITRAGE_BOUNDARY.md`](docs/AUTHORITY_ARBITRAGE_BOUNDARY.md) — its **adversarial dual**: same
self-edit structure, different measured quantity — can an actor modify the authority that validates it without
creating *hidden advantage*? The load-bearing definition is `hidden ≠ unrecorded; hidden = unadjudicable` (a
fully-logged change is still arbitrage if no party independent of the changed rule can judge its legitimacy). New
axis: advantage reconstructability (`RECONSTRUCTABLE / VIA_INDEPENDENT_WITNESS / SEVERED`); the layered
witness substrate is *derived as an anti-arbitrage necessity*, not chosen — stated with its falsifier, and the
honest residual that layering relocates unadjudicability to the bootstrap (genesis). The strongest reduction is
**non-representability**, bounded by genesis; `declared ≠ verified`.
[`docs/ADJUDICATION_THROUGHPUT_BOUNDARY.md`](docs/ADJUDICATION_THROUGHPUT_BOUNDARY.md) — the third of the triad,
about *timing* not authority: **can commitment outrun verification?** A system reconstructable *in principle*
becomes effectively non-reconstructable when verification cannot keep pace with production (the reduced, testable
core of Brandolini's Law). Isolates a failure mode the other two miss — `FLOODED` (witness exists, reconstruction
can't keep up) — measured as `t_dep < t_verified` against the kernel's irreversibility frontier; clean
decomposition `SEVERED` (information loss) / `FLOODED` (throughput deficit) / `INTERVENTION_ONLY` (identifiability
limit); the proof-carrying floor (`grounded_claim`) reverses the asymmetry for the check-adjudicable class. Kept
a separate probe (split-before-unify); throughput is a declared-rate model, `integrity ≠ truth`.
[`docs/FAILURE_MODE_MATRIX.md`](docs/FAILURE_MODE_MATRIX.md) — the **cross-boundary diagnostic layer** over the
four (connective tissue, not a new ontology): the boundary docs ask *"can this happen?"*, the matrix asks *"if I
observe X, which boundary am I hitting?"* Four orthogonal failure axes (`NON_ORIENTABLE` / `SEVERED` / `FLOODED`
/ `INTERVENTION_ONLY`) — *independent invariants, not "conservation laws"* (nothing is conserved); a
forward table (failure → consequence, incl. the `FLOODED → SEVERED` cascade across the irreversibility frontier)
and an inverse one (observation → candidate set **+ the discriminating test that collapses it**). Routes toward a
boundary, never a verdict (`observation → candidate set, never cause`); orthogonality is the hypothesis it
*tests*, and an unmatched symptom is evidence of an unmodeled fifth axis.
[`docs/EPISTEMIC_ACCOUNTING.md`](docs/EPISTEMIC_ACCOUNTING.md) — **the ledger** of the live_world_kernel stack as
*auditable epistemology as infrastructure*: every instrument and boundary marked `BUILT` / `CONTRACT` / `ABSENT`
with its verification strength, the one invariant (provenance strength is a monotone-non-increasing ceiling,
*partially* ordered), the convergence stack (`reality_status → repo_status → reconcile_status → runtime_witness →
witness_panel`), and a recorded-ghosts section that *leads* with the misstatements the comb caught (e.g.
`runtime_witness` over-counting coverage by treating `from x import f` names as modules). Accounting, not
aspiration — written to refuse looking more complete than it is.
[`docs/REAL_SILICON_BENCHMARK.md`](docs/REAL_SILICON_BENCHMARK.md) — the measurement *contract* for
the GPU benchmark (device as constrained oracle, GPU-timestamp budget as the shared ruler, temporal error as a
Pareto profile). It is now **built and verified on hardware through the temporal arc** in
`experiments/bench_gpu_real` (M1–M6c spatial + M6d/T1–T4 temporal on an Ally X); the neutral rulers falsified
the strong spatial causal claim and supported a conditional temporal one. Substrate ≠ benchmark.
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
silicon, and the `lineage_scale/` closure test; `bench_gpu/` — the GPU measurement *contract*;
`bench_gpu_real/` — the **GPU benchmark verified on hardware**, M1–M6c spatial + M6d/T1–T4 temporal on an Ally X;
and `live_world_kernel/` — the **embedded-authoring kernel (16/16) + a verified-epistemology stack**:
convergence/provenance witnesses (`fidelity_gap`, `reality_status`…`witness_panel`) and an **RSI-decomposition
layer** (the verified-improvement engine, the branching theorem + its proof-check, and the generativity
estimator)), each a seeded, self-checking bench outside the core.
[`AGENTS.md`](AGENTS.md) — the contract every change obeys.

## License

Ursprung is licensed under the [GNU Affero General Public License v3.0 only](LICENSE) (AGPL-3.0-only).
Copyright (C) 2026 Daniel J. Dillberg. It consumes the sealed `Reality_Engine` workbench read-only (the
Sibling Law) and does not vendor or relicense any of it.
