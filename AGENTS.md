# URSPRUNG — renderer contract (read before editing)

Ursprung is a deterministic high-fidelity renderer built as a **read-only consumer** of the sealed
`Reality_Engine` (Chronicle/Dentatus) workbench. The workbench is the **verification substrate**, not the
renderer. Do not expand Chronicle/Dentatus concepts here unless they directly improve one of: frame-time
stability, visual fidelity, deterministic replay, debugging, the asset/world pipeline, player experience, or
**information integrity** (anti-cheat / multiplayer disclosure — the second arc; see *The information-firewall
discipline* below).

> **Repo orientation (current).** Beyond the renderer described here (`ursprung/`, `experiments/`), the
> repository's **current center of gravity is `weltwerk/`** — a verification kernel with interchangeable proof
> engines, a Proof-Obligations ledger, an epistemic-runtime layer, and applications (hot-swap, the snowflake
> language audit, the Halvorsen attractor). It obeys the *same* Dentatus discipline as this contract; see the
> **weltwerk** section below. This renderer contract remains in force for `ursprung/`.

## The pipeline (the only shape)

```
authoritative world state → deterministic snapshot → visual interpretation → GPU execution → presented frame
```

The renderer may optimize *representation*. It must never mutate authoritative state.

## Rules of engagement (for any agent — human or LLM — modifying this repo)

This repository is an **Epistemic Runtime Environment**: it governs *claim integrity*, and that discipline binds
the agent editing it as much as the code. Any pass — and an automated/LLM pass especially — operates under:

1. **Tag every claim.** State a modification's **maturity** (`IMPLEMENTED` / `SCOPED` / `UNDERCOMMITTED`) and
   **evidence** (`MEASURED_BY_INTERVENTION` / `MEASURED` / `DECLARED` / `N/A`). The no-inflation invariant is
   absolute: *evidence may not exceed what maturity licenses.* Uncommitted rhetoric is `UNDERCOMMITTED / N/A`.
2. **A passing check certifies execution, never semantic meaning.** Comb the output fields; a green self-test does
   not prove a metric means what its name says. Watch specifically for **hidden averaging boundaries** and
   **outcome-dependent assertions** — a self-test must assert *validity* (did it run, are the numbers consistent),
   never the result you hoped for. (This session caught four such slips by reading output, not the green check.)
3. **Propose nothing without a falsifier.** A new mechanism ships with a deterministic, seedable self-test
   (`PYTHONHASHSEED=0`) that *can fail*, plus the stated condition that would refute it.
4. **Preserve trajectory properties.** Path-dependent quantities (e.g. `m_novel(Sₜ)`) must not be collapsed to a
   domain average; report disagreements between views rather than averaging them away.
5. **Determinism is the floor.** Everything runs reproducibly under `PYTHONHASHSEED=0`; a result that depends on
   hash-seed randomness is not a result.

This is not a productivity technique — it is the same gate the code enforces on itself (`claim_ledger` →
`rsi_engine` → `no_inflation_latch`), turned on whoever edits it. `declared ≠ verified`.

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
where their approximations fail. The decision is a deterministic rule over **declared** costs —
`reconcile(abandonment_cost, approximation_error)` keeps polygons iff `abandonment_cost ≥ approximation_error`
— never a truth claim about representation, and never a *measured* cost: the inputs must carry their provenance,
because a cost estimate without lineage is just another unaccounted number (`declared ≠ verified`).

### Temporal Fidelity Accounting Law (the synthesis; stated earlier as "Conservation")

> A renderer does not create fidelity. It distributes finite fidelity across competing uncertainties.
> Therefore the objective is not maximum detail — it is **minimum consequential discontinuity under a fixed
> budget.**

Fidelity is **transferred**, never created — *a fixed-budget accounting model, not a physical conservation law
(`model ≠ verified structure`; "conservation" names the bookkeeping, not a conserved quantity of nature)*: more
here = less elsewhere; more now = less later; more spatial =
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
>
> *(The product is a bookkeeping model — a chosen weighting relationship, not a derived necessity of reality.)*

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

Each of these five is the **Provenance Principle applied to approximation**: every approximation, boundary
choice, and tradeoff must carry the history and assumptions that make it interpretable. The kernel did not add
this to the laws; the laws acknowledge the contract the kernel now enforces. Their equations are bookkeeping
models (chosen weightings), not derived invariants — `model ≠ verified structure`.

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
- **PFAL**: `R = U × C × P × S` (a weighting model — uncertainty · consequence · persistence · sensitivity —
  not a derived law). Carefully worded
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

- **the ghost is a candidate set, not a truth.** When a system surfaces a residual it cannot explain — a
  divergence, a reconstruction mismatch, a persistent ghost — do not treat it as a hidden mechanism. It is
  `G = G_F + G_C` (real generator residue vs projection/confounder artifact), separated by **invariance**
  (persists across observers/projections?), **necessity** (removing it changes `F` under intervention?), and
  **model-robustness** (necessary across the admissible model class, not just one model?). A residual can be
  stable, reproducible, observer-independent, and hash-identical and *still* be a non-causal artifact:
  `stable ≠ causal`, `integrity = reproducibility ≠ causal validity`, `causal-under-a-model ≠
  causal-across-models`. Keep only the invariant necessity (`perception/ghost_invariance.py`,
  `attribution.py`, `model_relativity.py`). `Generator = invariant necessity`; the hash certifies a
  trajectory's identity, never its explanation.

Every such system is an **OBSERVER** (it measures, ranks, attributes; it never mutates the trajectory and
never asserts truth). The cardinal invariant and the four-layer law above still bind it.

## The provenance kernel — the constraint surface (judge new layers as clients)

The empirical arc consolidated into a minimal runtime contract, `experiments/reality_kernel/`: four immutable
primitives the rest of the system is now built *against*. The governing rule for any new layer — **it is a
client of the kernel, not an extension of it:**

- a renderer **asks `Query`** (existence *and* absence: `present / absent / unresolved / unaccounted`, with a
  diagnosis and a resolution path);
- a simulation step **emits an `Event`** (a transition with a named source — no silent mutation);
- a state transition **produces a `CommitReceipt`** (a *record*, never an authorization — `attestation ≠
  authority`; the runtime is a notary that enforces non-forgetting, not a sovereign that grants permission);
- generated structure **produces an `Artifact`** (a thing with declared provenance);
- a failure **produces a `NonRecovery`** (typed ignorance — never a bare "unknown").

Two invariants the kernel adds, enforced *by type* in the Rust CORE port (`core_rs/`, verified on real silicon,
`cargo test` 10/10 — semantic preservation + adversarial concurrency): **a dropped observation is allowed; a
dropped transition is forbidden**, and **optimization may compress provenance but may not sever it**
(`compress ≠ sever`; a digest that no longer resolves is severance, caught, never a silent fallback to
`unknown`). New work is judged against this surface exactly as it is against the four-layer law and the
cardinal invariant. *Verified* here is the narrow, stronger claim: the runtime's distinctions **survived a
substrate transition** — not that the runtime is complete.

## The auditable-epistemology stack (`experiments/live_world_kernel/`) — and its red-team phase-1 use

The first world-loop client on the kernel grew into a stack whose subject is **how much of a claim's
justification survives extraction, compression, replay, disagreement, and time.** It is single-process logic
(no concurrency, scale, or networking), and it obeys one invariant above all: **provenance strength is a ceiling
set by evidence — every transformation may lower or hold it, never raise it** (strength is *partially* ordered,
not totally ordered). The epistemic vocabulary, ordered by justification strength, plus the conflict marker:

```
MEASURED_BY_INTERVENTION  >  MEASURED  >  DECLARED  >  N/A          CONTESTED = conflicting evidence (≠ "not measured")
```

The instruments (each self-testing; all `OBSERVER`-class — observe, never enforce, never a verdict, never a
scalar): `live_world_kernel` (commit / irreversible / durable), the three boundary probes (`frontier_probe`,
`concurrency_probe`, `klein_probe`) bundled by `topology_provenance_engine`, the extraction pair (`module_graph`
→ `fidelity_gap`, which separates a recoverable model defect from a runtime frontier), and the convergence stack
that puts every boundary on one fact with provenance attached: `reality_status` (one witness) → `repo_status`
(extraction *downgrades* strength) → `reconcile_status` (disagreement → `CONTESTED`, never inflation) →
`runtime_witness` (earns evidence static cannot; orthogonal blind spots) → `witness_panel` (many witnesses, one
fact, no global winner). The full ledger — every instrument marked `BUILT` / `CONTRACT` / `ABSENT` with its
verification strength — is `docs/EPISTEMIC_ACCOUNTING.md`, and the four boundary *contracts* (not yet code) are
`SELF_MODIFICATION` / `AUTHORITY_ARBITRAGE` / `ADJUDICATION_THROUGHPUT` / `FAILURE_MODE_MATRIX`.

The stack then turns reflexively — on its own claims and on the hardest one, recursive self-improvement.
`discrimination_matrix` ranks experiments by uncertainty collapsed; `claim_ledger` reconciles statements about the
kernel as *claims with commitment levels*, enforcing `evidence ≤ maturity` (the no-inflation rule made executable);
`no_inflation_latch` compiles that same rule to NAND gates (an over-claim is a forbidden state, proven exhaustively).
On RSI it is a **decomposition, not an engine**: `self_improvement_witness` (a verified step exists) →
`recursion_witness` (`d²/dt²` — no acceleration) → `limit_discriminator` / `inflation_vs_search` / `transfer_*`
(the binding limiter is the *evaluator*, not search; transfer is not robust across regimes) → the branching theorem
(`verified_improvement_theorem`: a verified-edit branching mean `m ≤ 1` ⇒ almost-sure extinction; classical, conditional)
→ `rsi_engine` (promote only externally-verified + replicated + calibrated edits) → `verified_branching_estimator`
and `generativity_estimator` (estimate `m_offspring` vs `m_novel` with bootstrap CIs; informative only if the CI
excludes 1). Thesis: **RSI requires generativity of the verified-improvement space, not merely self-modification** —
which relocates it from the optimizer to the *(system, domain, verification-regime)* triple. The runaway's signature
is `m̂ > 1 ≥ m_verified` (proxy mean above 1, verified mean below). New separators this arc recorded:
`experiment-ran ≠ hypothesis-confirmed`, `measurement-valid ≠ prediction-true`, `optimization-pressure ≠ search-budget`;
governing asymmetry **expectation may follow evidence; evidence may not follow expectation**. A self-test here checks
*validity + classifier soundness* — that the bench measured correctly and no verdict contradicts its own numbers —
never that a hoped outcome occurred; a verification gate that enforces the experimenter's prior is itself inflation.

**Red-team / pentest phase 1 (authorized structural reconnaissance).** This stack is a *phase-1* tool — it
**maps**, it does not exploit. Pointed at a codebase you own or are authorized to assess, it surfaces the class
of finding CVE/port/SAST pattern-matchers miss — **architectural / boundary** weakness — and, uniquely, attaches
**epistemic provenance** to each finding instead of a risk score:

- a high fan-in module → *blast-radius concentration* (`HIGH_FAN_IN [MEASURED]`) — highest-value review target;
- an import cycle → *resilience / DoS / re-entrancy surface* (`IN_DEPENDENCY_CYCLE [MEASURED]`);
- a cross-package import that violates intended isolation → *privilege-boundary smell / lateral-movement surface*
  (`concurrency_probe` leakage);
- a dynamic import static missed → caught by `runtime_witness` and reconciled as `runtime refines static`.

The discipline binds here exactly as everywhere else, and it is what keeps this defensive rather than alarmist:
**`flagged ≠ exploitable`** (every output is an attention signal, never a confirmed vuln; a human confirms);
phase 1 is **recon only** — it ships **no exploit, payload, or targeting**; it reads source/executes import-time
code you are **authorized** to assess (the `runtime_witness` trace executes target code — trusted/authorized
targets only); and it **declares its blind spots** — a *static* graph has provenance `NOT_APPLICABLE` (it cannot
find the irreversibility frontier / point-of-no-return; that needs runtime or git), `identifiability` stays
`DECLARED` until a replay/test-execution witness runs, and `runtime_witness` coverage is currently *over-counted*
(it treats `from x import f` names as modules — a recorded ghost in the ledger; the strength discipline is
unaffected, the coverage *count* is lower-confidence). The defensive wedge is the one most tooling misses: not
*"is there a known-bad pattern here?"* but *"does the architecture's **real** boundary structure match its
**intended** one — and how confident is each finding?"* — with every answer carrying whether it was `MEASURED`,
`DECLARED`, or `CONTESTED`, never a single fabricated number.

## weltwerk — the verification kernel and its applications (current center of gravity)

`weltwerk/` is the line the repo now grows along: a **verification kernel** plus an epistemic-runtime layer and
applications built on it. Same discipline as the renderer (tag claims, validity-not-outcome self-tests,
falsifiers, separators), turned on *world-model verification* instead of rendering. Pure-stdlib core; z3 optional
and confined to `solver_adapter*`.

**The kernel (`weltwerk/verify/`).** A model checker that became a verification kernel: the *result contract* is
the boundary and engines plug in behind it. `TransitionRelation` (semantics) → `VerificationEngine` (search) →
`VerificationResult` (contract); `engine ≠ semantics`. The `ExplicitStateBFSEngine` is the reference (clean-room
from model-checking theory, JPF-inspired, no NASA source); `SymbolicEngine` (approach A, SMT over the extracted
relation) and the direct-re-encoding CANDIDATE (approach B) satisfy the same protocol. Grading is mechanical and
honest: **CLOSED** = proof over the chosen action alphabet + transition function (carries a re-derivable
`ReachabilityCertificate`); **BOUNDED** ≠ proof (depth-truncated, UNDERDETERMINED beyond); **VIOLATED** ships a
replayable witness `Trace`. The honesty contract `AnalysisResult` cannot be constructed without a scope + ≥1
`Limitation`; consumers (`diagnose`, `counterfactual`, `repair`) all project through it.

**The Proof-Obligations ledger (`PROOF_OBLIGATIONS.md` / `EVIDENCE_GRAPH.md`).** The kernel advances by *closing
obligations*, not adding features — each converts an intuition-terminating chain into executable evidence, and a
README claim may not rest on an unproven chain. **PO-1 … PO-10 are all built and run-green**: oracle soundness
(PO-4, `agreement ≠ soundness`), certificate independence (PO-8), boundary immutability (PO-7, the map cannot
move the judge), counterfactual accuracy vs an exhaustive gold (PO-2), repair grade-stability (PO-3 —
`RESTORED_WITHIN_BOUND` shown to flip at 2K; `restores-(M,E,K) ≠ safe`), Approach-B differential over a generated
distribution (PO-1, acyclic fragment), abstraction admissibility (PO-10, `abstract-CLOSED ⇒ exact-CLOSED`),
honesty-contract universality (PO-9), and the two RSI bounds (PO-5/PO-6).

**The RSI result (bounded on both sides).** The kernel's sharpest claim is deflationary and executable: PO-6
shows the natural restore task is **one-shot** (a single linear policy wins at budget B=1), and PO-5 shows that on
a *constructed not-one-shot* (XOR-shaped) task an iterated loop delivers **bounded, saturating** accrual while
one-shot + 4×-data stay at chance. Recursive improvement here is **real but bounded, task-gated, first-order** —
never open-ended or second-order. `iteration ≠ open-ended`.

**The epistemic-runtime layer (judge → compiler).** Reusable, domain-agnostic modules:
- `residual_channel.py` — the confounder-conditioned-MI firewall: `audit(X,Y,Z)` decides signal-vs-confounder-leak
  via `I(X;Y|Z)` + within-Z shuffle null + mis-specification stress. `residual-CMI ≠ channel`;
  `proves-the-procedure ≠ proves-the-phenomenon`.
- `claim_ledger.py` — the epistemic ladder (ESTABLISHED / MEASURED / UNDERDETERMINED / SPECULATIVE /
  NOT_MEASURED) as an enforced `Claim` template; `audit_ledger` refuses ungraded/unfalsifiable/boundary-free claims.
- `epistemic_types.py` + `enforced_transition.py` — `Grounded[T]` cannot be constructed without a verifier proof;
  `require_grounded` gates a state mutation so a raw/ungrounded action is refused **before** any effect (atomic).
  The no-inflation invariant moved from post-hoc audit into the type system. `grounded ≠ true`.
- `certificate_compiler.py` — an inductive `ConstraintCertificate`: a no-search 1-step check (`Init⊆Inv ∧ Inv
  closed under T ∧ Inv⊆Safe`). Checker DEMONSTRATED; auto-deriving the invariant and the size-independent symbolic
  check are flagged OPEN / z3-path. `verify ≠ prove`; `checking ≠ finding`.
- `frontier_gate.py` — reads `m_novel` (the frontier multiplier from `generativity_estimator`) + CI; SUBCRITICAL
  ⇒ PIVOT. Sensor/trigger DEMONSTRATED; "escape" graded bounded (PO-5 saturation), not unbounded.
- `orchestrator.py` — the **Epistemic Runtime Orchestrator**: a *thin* registry that makes the tools above
  interchangeable behind two chokepoints. It adds **no authority** (a router, not a verifier); it makes tools
  *composable*, not *capable*. `orchestration ≠ authority`; `composition ≠ capability`.

### Using the orchestrator — the default entry point (agents and users, read this)

**Reach for `orchestrator.py` first** when you want to run, compose, or extend the weltwerk tools. It is the
sanctioned way to use them, because it enforces the two invariants the whole repo rests on, by type, at one place:

- **Every answer is an `AnalysisResult`.** Call `EpistemicRuntimeOrchestrator.analyze(tool_name, request)`; the
  honesty contract (scope + ≥1 limitation) is re-checked at the boundary, so a tool that emits a bare verdict is
  rejected. Use `panel([(tool, request), …])` to get **many witnesses on one question, side by side** — never
  average or rank them into a scalar (the standing refusal). Get a wired instance from `default_orchestrator()`
  (registers `residual_channel`, `frontier_gate`, `claim_ledger`, `certificate_compiler`).
- **Every action is `Grounded[T]`.** Run side effects only through `orchestrator.enact(value, proof, action)`:
  the action fires *only* if `value` is grounded by a verifier-issued proof; an ungrounded action raises
  `UngroundedError` before any effect. Do not mutate state outside this chokepoint.
- **Adding a new tool? Register it, don't bypass it.** A new analyzer implements the `EpistemicTool` protocol
  (`name` + `analyze(request) -> AnalysisResult`) and is `register()`-ed; a new prover returns a `Grounding`
  object for `enact`. A tool that returns a non-`AnalysisResult`, or a mutation that skips `enact`, is the thing
  this layer exists to forbid. `router ≠ verifier`: the orchestrator dispatches and gates; it never grants truth.

```python
from orchestrator import default_orchestrator
o = default_orchestrator()
o.analyze("residual_channel", {"samples": xyz})        # → AnalysisResult (signal vs confounder-leak)
o.panel([("frontier_gate", {"m_novel": m, "ci": ci}),  # → {name: AnalysisResult}, side by side, no scalar
         ("claim_ledger", {"ledger": claims})])
o.enact(action_value, proof, apply_fn)                 # runs only if Grounded; else UngroundedError
```

**The reference backend client is `weltwerk/stream_auditor/`** (profile **C**, the Causal Stream Auditor): read
it for how to consume the chokepoints on a live stream — `OrchestratedBackend` (the base profiles A/B inherit),
per-window `AnalysisResult` witnesses reported side by side (no fused scalar), `ChannelEstablished`-gated
`promote()` via `enact` (HEALTHY/MISSPEC refused atomically), and `frontier_gate` coverage-attrition → bounded
PIVOT. Build a new backend by subclassing `OrchestratedBackend`, never by bypassing the gates.

**Hot-swap (PO-11/12, `weltwerk/verify/hotswap/`).** Live program hot-swapping as a *verified bounded search*
behind the frozen contracts: a stream-preservation invariant + certificate (`π∘μ=π`), candidate-ranking swap
planning as equal-budget search-acceleration, and a built-in falsifier (deferred-race flip@2K, race@1,
overdetermined safe plan). It adds semantics, not authority (`engine ≠ semantics`).

**Applications (the discipline pointed at real domains).**
- `weltwerk/halvorsen/` — the Halvorsen chaotic attractor: exact-invariant floor (`∇·f=-3a`, C₃ symmetry); a
  trapping certificate **honestly rejected** for a quadratic V (`empirical ≠ certified boundedness`); the FP
  `determinism ≠ reproducibility` ghost; differential-on-measures-not-paths; a **telemetry anomaly engine** (fault
  vs sensor-misspec via `residual_channel`); and a **safety-gate mechanism** (fail-closed without a sound
  certificate — the sound certificate is OPEN).
- `weltwerk/stream_auditor/` — the **first true backend client** of the orchestrator (profile C): a
  domain-agnostic Causal Stream Auditor that windows a stream, audits each window via `residual_channel`
  (HEALTHY / CHANNEL / MISSPEC), grades it on `claim_ledger`, tracks coverage attrition via `frontier_gate`, and
  gates `promote()` behind the Grounded chokepoint — only a confirmed CHANNEL acts; HEALTHY/MISSPEC are refused
  atomically. The scaffolding profiles A (SMT) and B (linter) inherit.
- `weltwerk/verify/snowflake/` — the "does morphology encode a language?" audit: every information-theoretic
  representation reduces to the field-driven growth law; the decisive test is field-conditioned inter-branch CMI
  (predicted 0). The worked example that produced the reusable firewall.

**Run (PowerShell, folder-directed).** Each subfolder README lists exact commands; pure-stdlib suites need no
dependencies; z3 suites skip cleanly without it. The discipline is identical to the renderer's: `integrity ≠
truth`, validity-not-outcome tests, every claim carries its grade and its boundary.

### Building standalone products (how an LLM should use these tools commercially)

The weltwerk tools are a **specification + reference implementation + measurement discipline**, not a turnkey
product — exactly like the renderer (`Use cases` below). A product is an **adaptation**: the LLM wires its own
domain behind the contracts, keeps the metrology, and ships each claim with its boundary. The *method* is fixed
and binds the LLM the same way it binds the code: enter through `orchestrator.default_orchestrator()`; make every
answer an `AnalysisResult`; gate every action through `enact`/`Grounded[T]`; grade every claim on the ladder;
run **validity-not-outcome** tests (assert the apparatus is sound, never that a hoped result occurred); and
**never collapse a panel of witnesses to a scalar**. The non-negotiable separators travel with the product:
`integrity ≠ truth`, `residual-CMI ≠ channel`, `proves-the-procedure ≠ proves-the-phenomenon`, `grounded ≠ true`,
`tested ≠ safe`, `measured ≠ guaranteed`. A product that drops them is the inflation this repo exists to detect.

Concrete product patterns (tool · law/method · how the LLM builds it · the metrology it reports · its boundary):

- **Signal-vs-confounder-leak SaaS** (`residual_channel`). *Method:* confounder-conditioned CMI + within-Z
  shuffle null + mis-specification stress. *Build:* map the domain to `(X, Y, Z=confounder)` — predictive
  maintenance (sensor X,Y / control Z), adtech attribution (exposure X / conversion Y / organic-intent Z),
  fraud, quant strategy-validation. *Reports:* `I(X;Y)` vs `I(X;Y|Z)` vs the null, mis-spec stability, and the
  enum `HEALTHY / RESIDUAL_MISSPEC_STABLE / FRAGILE` — never a bare "fraud" / "alpha". *Boundary:* the complete
  `Z` is unattainable (a surviving residual is a *candidate*, not proof), and the result is window-relative
  (nonstationarity). `weltwerk/halvorsen/telemetry_audit.py` is the worked template.
- **Claims-integrity / compliance layer** (`claim_ledger` + `AnalysisResult`). *Method:* the no-inflation rule
  (`evidence ≤ maturity`) made executable. *Build:* force every generated report / marketing or medical / ESG /
  scientific claim through `Claim` (grade + mechanism + does-not-show + falsifier); `audit_ledger` refuses
  ungraded / unfalsifiable / boundary-free claims. *Reports:* `honest`, the ladder counts, and the violation
  list. *Boundary:* it checks the **form** of a claim (graded + falsifiable + bounded), not its truth.
- **Grounded-action gate for autonomous agents / code-gen / RPA** (`epistemic_types` + `enforced_transition` +
  `orchestrator.enact`). *Method:* judge → compiler — an action executes only if `Grounded` by a verifier proof.
  *Build:* put `require_grounded` in front of the side-effecting applier (trade, deploy, write, actuate); the
  generator must supply a proof or get `UngroundedError` before any effect. *Reports:* grounded/refused counts +
  each proof's label, atomically. *Boundary:* **only as strong as its proof oracle** — it blocks what a verifier
  can ground/refute, not arbitrary "bad" output.
- **Verified-config / policy checker** (`certificate_compiler`, the kernel). *Method:* model checking with honest
  grading. *Build:* encode a config / access-policy / feature-flag / rule-set as a transition system; `CLOSED` =
  proof no bad state is reachable over the alphabet (+ a re-checkable certificate), `VIOLATED` = a replayable
  counterexample. *Reports:* `CLOSED / BOUNDED / VIOLATED` + certificate or witness. *Boundary:* proof is over
  the chosen alphabet, not the world (`BOUNDED ≠ proof`).
- **Edge safety-gate library** (`safety_gate` / trapping certificate). *Method:* `verify ≠ simulate` — an O(1)
  certified-region membership replaces forward simulation. *Build:* ship the gate fail-closed; it permits a move
  only under a *sound* certificate. *Reports:* permit/refuse + the certificate's soundness. *Boundary:* the
  guarantee needs a sound certificate (hard cases are OPEN — `unsound-certificate ≠ safety`).
- **Frontier-health monitor** (`frontier_gate`). *Method:* `m_novel` depletion → PIVOT. *Build:* feed a coverage
  / novelty / exploration multiplier + CI (fuzzing coverage, search, RNG health, A/B exploration). *Reports:*
  the regime (SUPER/NEAR/SUB) + the pivot signal. *Boundary:* bounded, `estimate ≠ property`,
  `pivot ≠ guaranteed-escape`.

**The adoption gap (state it in every product).** None of these run for a stranger out of the box: the LLM must
(a) supply its own domain adapter (its `(X,Y,Z)`, its transition system, its `Claim` set, its proof oracle);
(b) lower a real backend where one is stubbed; (c) re-run the relevant validity tests on real data. Until then
the constructed numbers are illustrative; the *discipline and the interfaces* are what transfer. The defensible
one-line for any of them: *a verification/measurement product that reports what it found, by which estimator
class, with what coverage boundary — and refuses to act, grade, or claim beyond it.*

## Performance work

Prefer measurable experiments: **baseline → change → replay → benchmark → compare**. Preserve failed
approaches and the reasons they failed — a failed branch carries architectural information. An
allocation/optimization claim is judged by *comparative utility at equal budget with a negative control*,
never by correctness.

**The sealed-observer rule (proven load-bearing in M6b/M6c).** When a policy is benchmarked against a metric,
the policy must **not** be able to read the metric, the reference, or the ground truth it is scored against —
enforce it *structurally* (the policy's function signature simply does not receive them), not by comment.
Otherwise the bench silently becomes "optimize the metric" (Goodhart), which is exactly the failure this
project exists to detect. A gate whose scoring metric is built from the same quantities the policy optimizes is
**circular** (`attestation ≠ authority`): the constructed promotion gate read `supported_constructed` precisely
because its metric was U·C·P-weighted; the sealed neutral ruler then **falsified** that on silicon. Two
companion rules the same milestones earned: claim dominance only beyond the **measured noise floor**
(ε-dominance — ε estimated from the data, never assumed), and **keep a benchmark loss as a result** — M6b's
flat loss, refined by M6c into a measured boundary, is more valuable than a win would have been.

## Use cases — how to apply Ursprung in a real project

Ursprung is a **specification + reference + measurement discipline**, not a turnkey product. Hold that framing
before adopting any of it: `integrity ≠ truth`, `tested ≠ safe`, `simulation ≠ physics`, and every bench number
is constructed and **expires on real silicon**. With that in mind, there are five robust ways an engineer — or
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

**3. As a measurement / audit substrate, and a representation *classifier* (the nearest real win).** Point
`channel_discovery` + the `DisclosurePolicy` auditor at a real telemetry or output stream to find *actual*
leaks — *policy says reveal X; did the output contain only X?* But the deeper use, via `ursprung/perception/`,
is to stop judging the *channel* and start classifying the *observer's reconstruction trajectory* `B_t =
P(S | O_{1:t})`: the Perception Fidelity Condition (`perception/fidelity.py`) reports which regime a `(task,
policy, observer-class)` falls in — **bounded** (task converges, secret does not), **tradeoff** (a real
frontier), or **cascade-collapse** (a session of weak signals reconstructs the secret). The output is a
**behavioral forecast** (`task_convergence`, `secret_recovery_risk`, `regime`, bounding `observer_class`),
never a safety flag. The new optimization target this implies: *deliver the least representation that produces
the intended behavior* — not the most accurate one. (It needs an estimator for continuous, coupled signals; the
bundled one is discrete/symbolic. The `MeasurementResult` boundary discipline and the adversary-class sweep
(`adversary_capacity`) are already here.) Report "found by estimator E over trace D against class A," never "safe."

**4. As a causal-attribution discipline for residuals / anomalies / ghosts (the deepest transferable idea).**
Any system that produces an *unexplained residual* — a divergence, a reconstruction mismatch, a persistent
anomaly, a "ghost" — faces the same trap: treating the residual as evidence of a hidden mechanism. The
`ursprung/perception/` attribution layer is a portable procedure for *not* doing that. A residual is a
**candidate set**, decomposed `G = G_F + G_C` (real generator vs projection/confounder artifact) by three
tests, none of which read the residual itself: **invariance** (does it persist when you change the observer /
projection?), **necessity** (does removing it change the dynamics under intervention?), and **model-robustness**
(is it still necessary across the admissible *model class*, or only under one model?). The decisive lesson is
the counter-intuitive one: a residual can be stable, reproducible, observer-independent, and hash-identical and
*still* be a non-causal artifact — `stable ≠ causal`, `integrity = reproducibility ≠ causal validity`,
`causal-under-a-model ≠ causal-across-models`. This is directly reusable for anomaly triage, model debugging,
A/B-result attribution, and any "is this signal real or an artifact of how we looked?" question — symbolic/toy
in the repo, but the *procedure* (vary the projection, intervene, vary the model; keep only the invariant
necessity) transfers unchanged. *Generator = invariant necessity.*

**5. As an LLM-on-track methodology (for any systems project).** The `observe → hypothesize → implement →
verify → record` loop, the four LLM failure-mode guards (silent architectural drift, accidental authority
leakage, unreplayable behavior, unmeasured optimization claims), and *preserve failed branches* keep an LLM
coding partner disciplined on work that has nothing to do with rendering (`docs/LLM_ON_TRACK.md`).

**6. As an authorized red-team / pentest *phase-1* recon tool (`experiments/live_world_kernel/`).** The
auditable-epistemology stack maps a target you are authorized to assess and surfaces **architectural / boundary**
weakness that CVE/port/SAST scanners miss — blast-radius concentration (high fan-in), resilience/DoS surface
(import cycles), isolation/lateral-movement smells (cross-package leakage), and dynamic behavior static misses
(via `runtime_witness`) — with **epistemic provenance on every finding** (`MEASURED` / `DECLARED` / `CONTESTED`)
instead of a risk score, so a lead knows which findings are confirmed, which need runtime confirmation, and which
are contested. It is **phase 1 only**: it maps, it does not exploit; `flagged ≠ exploitable`; it ships no
exploit/payload/targeting; the runtime trace executes target import-time code so it runs on **trusted/authorized**
targets only; and it declares its blind spots (a static graph cannot find the irreversibility frontier;
`runtime_witness` coverage is currently over-counted — see `docs/EPISTEMIC_ACCOUNTING.md`). Defensive use:
*find and close your own structural attack surface before an adversary maps it from a leak.*

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

> **Current line:** the *renderer* arc described in this Status section is the earlier **complete** arc. The
> repository's active work is **`weltwerk/`** (see the *weltwerk* section above): its Proof-Obligations ledger is
> fully discharged (PO-1 … PO-10 run-green), the RSI claim is bounded on both sides (PO-5/PO-6), the
> epistemic-runtime layer is wired into a real applier (`enforced_transition`), hot-swap is verified behind the
> frozen contracts (PO-11/12), and the discipline has been applied to two domains (snowflake, Halvorsen). The
> renderer Status below remains accurate for `ursprung/` and `experiments/`.

The conceptual arc is **complete** (502-check core suite), the empirical phase **ran**, and it has **crossed
onto real silicon.** The conceptual genealogy: M1 foundation + invariant harness → M2 the five laws → M3/3.1
the VIEW raster slice and the *ranking ≠ allocation* result (from a recorded **failed** hypothesis) → M4–M9
fidelity-as-economy (resistance tensor, shader cache, readiness, providers, dependency integrity, compiler) →
M10–M21 the information-firewall arc → Channel Discovery + the Measurement Discipline → the **perception loop**
(`ursprung/perception/`: the privacy-funnel benchmark; `adversary.py` falsifies its per-frame leakage;
`session_accounting.py` answers with *purpose-preserving disclosure under an accumulating observer*) → the
**causal-attribution + epistemic-accounting capstone** (`attribution` / `model_relativity` / `grounded_claim` /
`ledgers` / `trajectory` — `integrity ≠ truth`, `integrity ≠ immunity`, `position ≠ ranking`). Governed by the
meta-invariant **`identity includes provenance`** (the Provenance Principle — a law of the runtime, not a
numbered world-law). Run: `PYTHONHASHSEED=0 python3 loop.py`; suite `python3 tests/test_ursprung.py`.

The empirical phase (`experiments/`, seeded benches *outside* the 502-check core): six latent phases → three
provenance runtimes → live/latent compression → the **RealityKernel** consolidation (the constraint surface
above), whose **Rust CORE port is verified on real silicon** (`cargo test` 10/10) and whose **lineage-scale
closure** proves *optimization cannot erase history* to 5×10⁵ commits with zero lineage lost. Then the **GPU
benchmark, verified on hardware through the summit and into the temporal arc** (`experiments/bench_gpu_real`,
**M1–M6c (spatial) + M6d / T1–T4 (temporal)** on an ASUS ROG Xbox Ally X / Radeon 890M, Vulkan): the timestamp
ruler exists, measures real compute *and* render work, binds each measurement to a world-identity digest,
compares allocation policies *fairly* at equal measured GPU-tick budget (over-spenders refused, M5), and on
**sealed, neutral perceptual rulers** ran the genuine Causal Continuity gates. **The verdict is a measured
boundary, not a win — and the same unbiased apparatus moved the hypothesis both directions:** the **spatial**
strong claim was **falsified** (at equal budget on a neutral metric the causal policy did *not* beat uniform;
M6c showed its exponent wrong — ∝ difficulty¹ over-concentrates vs the variance-optimal ∝ difficulty^(2/3)),
leaving a **conditional** spatial claim (informative priors + corrected exponent); the **temporal** form, built
on the Rust kernel as a multi-frame scene that decorrelates causal consequence from present render difficulty
(M6d / T1–T4 — the rig M6 could not build), came back **conditional-positive**; and the **hidden-future** form
(T4) is recoverable only above a precursor-reliability threshold, below which a weak signal is *worse* than
uniform → `causal_continuity.STATUS = conditional_on_neutral_ruler`; the whole boundary is consolidated in
`docs/BOUNDARY_MAP.md`. The durable artifact is the apparatus that could tell the difference — and it told it
both ways.

**Verified means the distinctions survived a substrate transition — not that the runtime is complete.**
*Proven:* kernel invariants, semantic preservation across implementations, the tested failure distinctions, and
lineage preservation within the benchmark envelope. *Frontier:* broader scale, distributed persistence,
learned-world verification, a real-time world substrate.

**The remaining work is substrate and clients, not more laws.** Do not add another conceptual milestone without
explicit direction; sanctioned work now is **better measurement substrates**, **stronger observer classes**, or
**a client built on the kernel contract** — all *experiments*. Two of the prior frontiers have since landed: the
**multi-frame causal test** is built (M6d / T1–T4, above), and the **first world-loop client on the kernel** has
its first step in `experiments/live_world_kernel/` (the embedded-authoring kernel + the auditable-epistemology
stack below — single-process logic; concurrency and scale remain open). The next builds: the Rust CORE at real
scale (1e6–1e8 lineage, frame-loop integration, the Windows sub-granularity timing question), concurrency at the
kernel (many actors, one region — the lethal test the live kernel has not faced), plus the standing seams —
`reality_harness.NetworkChannel` (a real socket), `behavioral_harness.ExperimentLayer(channel="real")`, the
perception compiler's lookup compiler, a real ML/RL adversary class, and a real estimator under intervention
scarcity (unknown graph).
