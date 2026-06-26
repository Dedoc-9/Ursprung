<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Research memo — recursive self-improvement over the Weltwerk verification kernel

**Status:** research memo, not a build plan. Substrate fixed at the current commit. No new engine, no external
data, no replacement of the verification spine. The question is whether *recursive self-improvement* (RSI)
can emerge from the artifacts already present, and where it must be refused.

## 0. Thesis (deflationary, up front)

RSI in this substrate is real but **bounded to the map, never the territory**. The system may recursively
improve *how it searches, ranks, abstracts, and proposes* — the map. It may never recursively improve *the
thing it is graded against* — the territory: the `TransitionRelation` semantics, the supplied `Invariant`s,
the engines, and the differential criterion. The instant the loop is allowed to edit what it is scored by,
"improvement" becomes **inflation**: the system raises its score by lowering the bar. This is the existing
No-Strength-Creation result (`claim_lattice.py`) and the no-inflation latch (`no_inflation_latch.py`)
restated at the loop level. `better-map ≠ changed-territory`; `higher-score ≠ more-true`.

Everything below is an application of one rule:

> **The loop may change anything it is NOT graded against, and nothing it IS graded against.**
> The grade is produced by {exact engine, supplied invariants, differential harness}. Those are frozen
> relative to the loop. Proposals to change them are surfaced to a human as candidates — never auto-applied.

**Prior art in this very repo.** This conclusion is not new here — the repo's own RSI arc already reached it.
`rsi_engine.py` is a *verified-improvement* engine; `no_inflation_latch.py` enforces it at the gate;
`claim_lattice.py` proves No-Strength-Creation; `limit_discriminator.py` separates inflation / search / real
improvement / transfer; `recursion_witness.py` measures actual recursive acceleration (d²/dt²) on *held-out*
tasks; `verified_improvement_theorem.py` states the bound. This memo does not re-derive that; it **applies
the existing RSI-measurement substrate to the verify kernel**. That changes the character of the work below
from "invent RSI safely" to "wire already-proven safeguards into the verification loop."

## 1. The smallest recursive loop from existing artifacts

The components of a loop already exist; only the *feedback edge* is missing.

```
world (WorldModel)
   → verify            (engine → VerificationResult)        [exact, frozen oracle]
   → if VIOLATED: diagnose + counterfactual                 (AnalysisResult)
   → propose RepairCandidate                                (repair.propose, seeded from critical set)
   → apply candidate → world'  (a CANDIDATE world, not authoritative)
   → re-verify world'          (VerificationResult', restores_world evidence)
   → record (world, change, result')  ────┐
        ▲                                  │   the missing edge: the record informs the next proposal
        └──────────────────────────────────┘
```

The smallest *recursive* increment is **counterexample-guided**: each `VerificationResult` (a ghost) and each
recorded outcome constrains the next `RepairCandidate`, and re-verification accepts or rejects it. This is
CEGAR-shaped and **sound by construction** — every iteration is judged by the frozen exact engine. It needs
no new substrate, only (a) a general `apply(world, change) → world'` (today only the `_ForbidRelation`
special case exists) and (b) a persistent record of outcomes. Both are data, both keep worlds non-authoritative.

What the loop "learns" in this minimal form is *which proposals tend to survive re-verification* — i.e. it
improves **candidate ranking and search order**, not the verdict. That is genuine, safe self-improvement.

## 2. What is missing (and how dangerous each is)

| Missing piece | Needed for | Danger | Verdict |
|---|---|---|---|
| **Memory** (append-only `ExperimentLog`) | "learn from result" | becomes a hidden authority (`replay ≠ correctness`) if trusted instead of re-verified | **Safe, build first** — append-only, every entry re-verifiable |
| **Model revision** (`apply(world, change)→world'`) | proposing modifications generally | a change applied to *authoritative* state instead of a candidate | **Safe if** worlds stay candidates; reversible; change is data |
| **Repair ranking** | prioritizing candidates | Goodharting "candidates-to-success" with trivial candidates | **Safe** — reorders only; verdict unchanged |
| **Experiment selection** | which world/edit to try next | starves the search of falsifying cases | **Safe** — allocation, not truth |
| **Policy improvement** (meta over the log) | recursion proper | overfit to seen worlds → false confidence | **Safe iff** evaluated on held-out worlds vs a baseline |
| **Invariant synthesis** | generating new properties | adopting a *weak* invariant ⇒ vacuous CLOSED = inflation | **Dangerous** — only as *conjectures to be falsified*, human-gated for promotion |
| **Meta-verification** | guarding the loop itself | the loop edits what it is graded against | **Required guard**, not a feature |

The single highest-value safe addition is **memory** (the `ExperimentLog`): without it there is no "learn",
and with it most of Phase 2 follows. The single most dangerous temptation is **invariant synthesis adopted
as criteria** — it is the canonical inflation move.

## 2a. Most of this already exists elsewhere in the repo — wire, don't build

A repo-wide pass shows the verify kernel is the *newest* consumer of machinery the project already built for
its earlier RSI and causal-world work. The honest reframing: this is ~80% an **integration** problem.

| RSI need | Already present in the repo | What is genuinely new |
|---|---|---|
| apply a change → candidate world (cheaply) | `weltwerk/world_edit.py` ("edit = new authority"), `weltwerk/cow_world.py` (copy-on-write **counterfactual-by-difference**), `weltwerk/fork.py` (trajectory pair) | a thin `apply(WorldModel, change)` shim unifying these for `verify/` |
| impact analysis of a change | `weltwerk/world_diff.py` (**structural consequence diff**: blast radius, SPOFs, regime) | nothing — consume it on each candidate |
| experiment selection | `discrimination_matrix.py` (**experiment epistemic-value ranking**, `UNKNOWN` vs `UNDERCOMMITTED`, `collapse_power` partition entropy) | a binding from `VerificationResult`/`AnalysisResult` → its scoring inputs |
| is this real improvement, search, or inflation? | `limit_discriminator.py` (A/B/C/D + TRANSFER), `inflation_vs_search.py`, `no_inflation_latch.py`, `claim_lattice.py`, `rsi_engine.py`, `recursion_witness.py` (d²/dt² on held-out), `generativity_estimator.py`, `verified_branching_estimator.py` | feed the loop's per-iteration deltas into these — **do not write a new metric** |
| ranking stability under perturbation | `transfer_robustness.py` | apply to candidate/experiment rankings |
| honest aggregation of disagreeing signals | `witness_panel.py` (one fact, many witnesses; **lattice, not hierarchy**), `reconcile_status.py` (**CONTESTED** state survives disagreement), `reality_status.py`/`repo_status.py` (convergence object), `runtime_witness.py` | route engine + analysis + repair signals through a panel instead of a scalar |
| held-out / baseline-aware evaluation | `eval_harness.py` (precision/recall vs **random + degree baselines**) | reuse verbatim to grade any learned policy |
| resource / work accounting | `resource_accounting.py` (work-avoidance), `orbit_estimator.py` (trajectory geometry), `causal_scale_bench.py` (operating envelope) | track loop cost so "improvement" isn't just spending more |
| guardrails for self-modification | `docs/SELF_MODIFICATION_BOUNDARY.md`, `docs/AUTHORITY_ARBITRAGE_BOUNDARY.md`, `docs/ADJUDICATION_THROUGHPUT_BOUNDARY.md`, `docs/FAILURE_MODE_MATRIX.md`, `docs/EPISTEMIC_ACCOUNTING.md` | adopt as the loop's threat model; add the meta-write-access test |

Two consequences. First, the genuinely new artifacts are small: the append-only `ExperimentLog`, the
`apply()` shim, and the `ResearchLoop` glue (§4). Second — and more important — **the hard, dangerous part
(distinguishing improvement from inflation) is already built and proven**; the loop must *route through*
`limit_discriminator` / `no_inflation_latch` / `recursion_witness`, never invent a fresh success metric. A
loop that scores itself with a metric it also authored is the textbook inflation failure. `own-metric ⇒ inflation-risk`.

## 3. Safe self-improvement vs dangerous self-modification

**Safe (improving the map — the verdict is invariant under it):**
- better heuristics: search order, candidate ranking, experiment selection. Pure allocation. `salience ≠ truth`.
- learned abstractions **that are checked** by the exact engine (CEGAR). Soundness is borrowed from the oracle.
- repair search: more/better candidates, each still re-verified.
- counterexample-guided refinement: refine on a *real* counterexample; the exact engine confirms.

**Dangerous (modifying the territory — changes what "true" means):**
- editing `TransitionRelation` semantics (which transitions exist).
- weakening/editing `Invariant`s or the accept criterion.
- editing the engines, or the differential-agreement criterion.
- adopting synthesized invariants/abstractions as ground truth without independent validation.

The boundary is exactly the repo's existing ones, lifted one level: `engine ≠ semantics`, `analysis ≠ proof`,
`candidate ≠ repair`, now plus **`policy ≠ criterion`**. A self-improving *analyzer* is safe; a self-modifying
*verifier or semantics* is the thing `docs/AUTHORITY_ARBITRAGE_BOUNDARY.md` warns about — and must stay
human-gated and structurally prevented (the loop has no write access to those files).

## 4. The `ResearchLoop` abstraction (a pure function, not an agent)

```
ResearchLoop(inputs) -> outputs        # PURE over artifacts + log; applies nothing itself

inputs:
  - VerificationResult        (current verdict + Trace/Certificate)
  - AnalysisResult            (diagnosis, counterfactual — with limitations attached)
  - RepairCandidate[]         (seeded from critical sets, with restores_world evidence)
  - ExperimentLog             (historical (world, change, result') records — append-only)

outputs:
  - next_experiment           (which world + which change to try next)   ← allocation
  - proposed_model_change     (a ranked RepairCandidate, NOT an applied edit)
  - AnalysisResult            (confidence + REQUIRED limitations; never "fixed"/"safe")
```

Discipline that keeps it honest: `ResearchLoop` **proposes and selects; it never applies**. Application is a
separate, human-or-policy-gated step that writes one immutable `ExperimentLog` entry. Outputs are
`AnalysisResult`-shaped, so the honesty contract (scope + ≥1 limitation) travels automatically. It is
deterministic given (inputs, log) — replay reproduces the same proposal. It emits ranked candidates +
evidence + limitations, never a verdict; the verdict only ever comes from the frozen engine.

Crucially, `ResearchLoop` **authors no success metric of its own**: it scores candidates/iterations only
through the existing, proven discriminators (`limit_discriminator`, `inflation_vs_search`,
`no_inflation_latch`, `recursion_witness`), selects experiments via `discrimination_matrix`, and aggregates
disagreeing signals through `witness_panel` (a lattice with a `CONTESTED` state, not a scalar). `historical
experiments` is the append-only `ExperimentLog`. A loop that grades itself with a metric it also defines is
the canonical inflation; routing through frozen discriminators is what forbids it.

## 5. Can recursive improvement actually emerge? (skeptical, technique by technique)

| Technique | Emerges? | Why / boundary |
|---|---|---|
| better heuristics | **Yes (modest)** | improves *time-to-result*, not truth. Measurable (experiments-to-ghost). No inflation. |
| learned invariants | **Only as conjectures** | a hypothesis *generator*; adopting them as criteria is inflation. Must be falsified on held-out worlds + human-promoted. |
| learned abstractions | **Yes, iff checked** | unchecked abstraction is unsound; checked = CEGAR. Soundness borrowed from the exact engine. |
| repair search | **Yes** | each candidate re-verified; improvement = better generation/ranking. |
| **CEGAR** | **Yes — the soundest core** | recursion that is sound *by construction*: refine on a real counterexample, exact engine is the oracle. This is the honest center of "self-improvement" here. |
| symbolic synthesis | **Yes as a generator** | Z3 can synthesize candidate repairs/invariants — but output is a *candidate* requiring verification, not a truth source. |

**Conclusion:** recursive improvement *can* emerge, exclusively in the map (search / ranking / abstraction /
candidate generation) with the exact verifier as a frozen oracle. It *cannot* produce improvement in truth
without external evidence; every attempt to do so internally is inflation and is rejected. This is not a
limitation to engineer around — it is the No-Strength-Creation theorem the repo already proved.

## 6. Phases

| Phase | New artifact | Invariant preserved | Failure mode | Test strategy |
|---|---|---|---|---|
| **0 — current** | — | engine≠semantics; analysis≠proof; candidate≠repair | (baseline) | the existing 10 suites + differential + conformance |
| **1 — Experiment manager** | `ExperimentLog` (append-only) + `Experiment(world_hash, change, options, result_summary, engine, bound, seq)` | append-only history; worlds non-authoritative; every entry **re-verifiable** | the log is trusted instead of re-verified (`replay ≠ correctness`); non-deterministic ⇒ non-reproducible records | replay each entry → identical `VerificationResult`; assert append-only; assert a corrupted/stale entry does **not** change a fresh verdict |
| **2 — Self-improving analyzer** | `Policy` (ranking/selection over candidates+experiments) + `ResearchLoop` | policy **reorders only**; verdicts identical with policy on/off (`policy ≠ criterion`) | overfit to seen worlds; Goodhart "candidates-to-success"; silently drops a correct candidate | train/test split over the log (the `eval_harness` discipline): beat a random + naive-ordering **baseline** on held-out worlds; ablation: same verdicts policy-on vs policy-off; every deprioritized candidate stays reachable |
| **3 — Self-improving verifier (CEGAR only)** | `Abstraction` + refinement loop (abstraction *guides/prunes*; exact engine confirms) | **one-directional soundness:** abstract-CLOSED ⇒ exact-CLOSED; exact engine stays the frozen oracle; `CLOSED = proof-over-alphabet` unchanged | **false CLOSED** (claims safe when not) — the worst failure in the system; non-terminating refinement | extend the differential harness: on every test world, any abstract verdict must be confirmed exactly; seed with known-VIOLATED worlds the abstraction must never call CLOSED. **Reject** any version that changes what CLOSED/VIOLATED *mean* or treats the abstraction as final. |
| **4 — Constrained self-modification (mostly refuse)** | `SemanticChangeProposal` (a diff to semantics/invariants) + impact analysis | the loop **never auto-applies** to semantics/invariants/engines/criterion; human commit is structural; meta no-inflation latch | reward-hacking the verifier (improve by weakening a criterion); a semantics change that fools *both* engines consistently; human rubber-stamp | diff every proposal against the full `ExperimentLog` (which past verdicts flip?); **inflation check**: flag any proposal that turns a previously-VIOLATED world CLOSED by changing the *criterion* rather than the *world*; adversarial meta-verification (à la the Fog/authority-arbitrage probes) that the loop *cannot* write to the graded files at all |

## Recommendation

Build **Phase 1** (the `ExperimentLog`, atop `fork.py`/`world_edit.py`/`cow_world.py`) and **Phase 2**
(ranking/selection `Policy` + `ResearchLoop`): both are pure consumers of existing artifacts, both are safe
(map-only), and both are evaluable with the held-out + baseline discipline already in `eval_harness.py`,
gated by `no_inflation_latch` / `limit_discriminator`, and fed by `discrimination_matrix` for experiment
choice. Almost no new metric code should be written — if you find yourself writing one, stop: reuse the
discriminators. Treat **Phase 3** as *CEGAR-with-a-soundness-gate only* (candidate worlds via
`cow_world`'s counterfactual-by-difference, impact via `world_diff`), and only if scale actually demands it —
its single load-bearing test (no false CLOSED) is non-negotiable. Treat **Phase 4** as *proposal-only,
human-gated* under the `SELF_MODIFICATION_BOUNDARY` / `AUTHORITY_ARBITRAGE_BOUNDARY` threat model, and most
likely **not worth building**: it buys little and concentrates all the catastrophic risk.

The honest summary: this architecture can host a **self-improving researcher of its own bounded questions**,
not a self-improving truth. The AI proposes, the spine tests, the differential harness guards the meaning,
the counterfactual says what to tweak — and *only the committed trajectory records what occurred*. RSI here
is the disciplined accumulation of better maps over a fixed territory. `integrity ≠ truth`; a loop that
forgets this is not improving — it is inflating.
