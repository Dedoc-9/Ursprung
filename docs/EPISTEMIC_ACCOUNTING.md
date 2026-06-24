<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# EPISTEMIC_ACCOUNTING — the ledger (auditable epistemology as infrastructure)

> **This is accounting, not aspiration. It records what is BUILT, what is CONTRACT, and what is ABSENT — and at
> what strength each is verified. It is written to refuse looking more complete than it is.**

The work in `experiments/live_world_kernel/` plus the boundary docs in `docs/` cohere into one pattern, and the
honest name for it is **auditable epistemology as infrastructure**: a stack whose single concern is *how much of
a claim's justification survives as the claim passes through extraction, compression, replay, disagreement,
recursion, and time.* This document is the ledger of that stack. `declared ≠ verified`; an entry marked BUILT is
single-process logic verified by its own self-test, never a shipped product.

## The one invariant

> **Provenance strength is a ceiling set by evidence. Every transformation may lower or hold it — never raise
> it.** Strength is *partially* ordered, not totally ordered: a witness can be strongest on one axis and silent
> on another. The reconciler keeps the strongest *justified* claim per axis and records the rest; it never
> manufactures strength, and an absent or conflicting witness is first-class, not a blank.

The epistemic vocabulary, ordered by justification strength, plus the conflict marker:

```
MEASURED_BY_INTERVENTION  >  MEASURED  >  DECLARED  >  N/A          CONTESTED = conflicting evidence (≠ "not measured")
   (replay / do(¬x))         (observed)   (no probe)   (n/a)         strictly below MEASURED; distinct from DECLARED
```

## The ledger

Status ∈ {BUILT, CONTRACT (doc-only, code is the seam), ABSENT}. Verification ∈ {verified — self-test run on the
author's machine; synthetic-core — discipline verified, IO is a candidate; transitive — imported & exercised by
a verified dependent, own self-test not separately logged; empirical — established in the `experiments/` phase;
paper — a measurement contract, no code}.

| Artifact | Layer / question | Status | Verification |
|---|---|---|---|
| `live_world_kernel.py` | reality — accept/reject/rewind without losing causal truth; 3 states of a fact | BUILT | verified 16/16 |
| `frontier_probe.py` | frontier — where possibility becomes obligation | BUILT | verified 7/7 |
| `concurrency_probe.py` | locality — partition causal or merely geometric | BUILT | verified 7/7 |
| `klein_probe.py` | orientability — local convention vs false global claim | BUILT | verified 7/7 |
| `topology_provenance_engine.py` | bundle the three probes as a vector (no scalar) | BUILT | verified 7/7 |
| `module_graph.py` | extraction — model a system it did not author (dumb, declares blind spots) | BUILT | verified 7/7 |
| `fidelity_gap.py` | extraction repair — why the model came back blind; what is recoverable vs runtime-frontier | BUILT | verified 7/7 (click, requests) |
| `reality_status.py` | status — every boundary on one fact, each cell carrying its provenance | BUILT | verified 7/7 |
| `repo_status.py` | weak evidence — provenance survives extraction by downgrading | BUILT | verified 7/7 |
| `reconcile_status.py` | disagreement — the lattice; CONTESTED; strength never inflates | BUILT | transitive (imported & exercised by runtime_witness 8/8, witness_panel 7/7); confirm committed |
| `runtime_witness.py` | execution — earns evidence static cannot (dynamic imports) | BUILT | verified 8/8 (discipline); **coverage over-counts — see ghosts** |
| `witness_panel.py` | coexistence — one fact, many witnesses; partial order, no global winner | BUILT | verified 7/7 |
| `discrimination_matrix.py` | experiment ranking — value = `DECLARED`→`MEASURED_BY_INTERVENTION` conversions; `UNKNOWN` (our gap) vs `UNDERCOMMITTED` (theory refuses, set aside ≠ refuted) gate | BUILT | verified 12/12 |
| `claim_ledger.py` | reflexive — reconcile claims-about-the-kernel without category collapse; enforces *evidence ≤ maturity* (no inflation); refuses a single kernel-status scalar | BUILT | verified 6/6 |
| `self_improvement_witness.py` | self-improvement — proves a guarded, self-modifying *step* (C1 σ-adapts, C2 held-out gain real); measures C3 = **PLATEAU** (no recursion); holds C4 unbounded/self-certified RSI at `UNDERCOMMITTED`/`NON_ORIENTABLE` (certification is external; train-only metric rises while reality falls) | BUILT | verified 7/7 |
| `recursion_witness.py` | RSI ladder — capability across generations on **held-out tasks**, evaluator outside the loop. **sustained YES** (d/dt +0.076), **recursive NO** (d²/dt² ≈0, ceiling), **self-certified NO** (self-estimate +0.155 vs real +0.054). Ghosts: meta-search **stalled at 9 coords** (true support 3) after 4 edits; self-estimate ~4× inflated vs reality | BUILT | verified 7/7 |
| `limit_discriminator.py` | limiter discrimination — separates **A** search / **B** task / **C** transfer / **D** evaluator, task held fixed. This run: **A REFUTED**, **B SUPPORTED** (task ceiling, no acceleration), **C SUPPORTED** *for raw-weight-carry* (entangled few-sample weights transfer distortion; structure-level transfer untested), **D SUPPORTED** (self-estimate +0.073). The endpoint "search↔evaluator coupling" (0.075<0.082) is **CONTESTED** — a clean width sweep (`inflation_vs_search`) did not reproduce it; the two points differed in generations & loop type, not clean pressure. Self-tests verify **validity + classifier soundness** (incl. `verdicts_consistent_with_data`), never an expected outcome | BUILT | verified 7/7 |
| `inflation_vs_search.py` | A↔D as a *curve* — inflation = proxy − external vs search strength K∈{1,2,4,8,16,32}. Finding: inflation is **persistent (~+0.07) but NOT explosive** — flat across a 31× budget rise (93→2883 evals) because K≥2 yield *identical* optimizers (small discrete proposal space ⇒ best-of-K → greedy-best at K≈2). New separator **optimization-pressure ≠ search-budget** (`d(budget)/dK>0`, `d(pressure)/dK≈0`). "more search → more inflation" **not observed** ⇒ the earlier endpoint coupling is CONTESTED. A *more constrained, more useful* statement than the explosive-coupling suspicion. Self-tests = validity + classifier soundness | BUILT | verified 7/7 |
| `transfer_representation.py` | transfer table — encodings (reset/raw_weights/support_set/basis_structure/learned_init) × (cost, external, inflation); win = lower cost + higher external + no-worse inflation. Single-run winner is **regime-dependent** (3 of 5 mechanisms flip between noise regimes). Cost-axis degeneracy (theta unreachable ⇒ all costs pinned) was caught by combing and fixed (relative reachable threshold) | BUILT | verified 7/7 |
| `transfer_robustness.py` | replication gate — transfer table across a 3×3 noise×seed grid. Verdict **REGIME_DEPENDENT** and stronger: **6/9 regimes have no winner, all 3 wins cluster at one seed ⇒ no robust transfer advantage** (apparent winners are sampling flukes, not mechanism effects). Self-tests = validity + stability-verdict soundness | BUILT | verified 7/7 |
| `rsi_engine.py` | **RSI engine (capstone)** — self-modify only through a reconciler gate (external gain ∧ replication ∧ calibration); naive proxy-runaway control. Gated: real external gain (+0.041), **inflation −0.090** (underconfident — safe); naive: proxy +0.072 but external −0.024 (self-deception, inflation +0.096). Both promoted **once in 60 rounds** ⇒ verified gains are *rare* — a single verified step, not a sustained sequence. The gate invariant *is* the self-test (every promotion provably cleared all gates; verified capability cannot regress) | BUILT | verified 7/7 |
| `claim_lattice.py` | **formalization — the invariant as an order structure + a machine-checked theorem** (the schema `no_inflation_latch` is one instance of). Claim = (maturity × evidence) point; `VALID ⟺ rank(e) ≤ ceiling(m)`. Verified a **lattice** (glb/lub computed exhaustively — earned per the "don't overclaim 'lattice'" caution). **No-Strength-Creation theorem** (exhaustive over 9 states / 81 pairs): extract/age/reconcile/compose never raise strength — *the system cannot manufacture epistemic authority by re-describing, composing, reconciling, or aging; only `measure` (contact with reality, bounded by maturity) can*. CONTESTED is a sink (conflict destroys strength; only measurement lifts). Also verified **closed under its operators** (∀ T ∈ {extract,age,reconcile,compose,measure}: T(·) ∈ CLAIM_SPACE — latch + lattice + operators unify) and that **CONTESTED strength is a declared policy parameter** (a `CONTESTED:=strongest` policy would not downgrade ⇒ the lattice *encodes* the epistemology, it does not discover it — the Arbitrary-Boundary Law applied to the lattice itself). Honest novelty: an *instance* of info-flow lattices / provenance semirings ⇒ buys **rigor + reflexivity, not new order theory**; defensible contribution = executable + self-applied evidence-accounting for *empirical claims*; novelty pending a literature review | BUILT | verified 10/10 |
| `no_inflation_latch.py` | **gate-level floor** — `evidence ≤ maturity` realized as a NAND-built combinational guard (`VALID = ¬(E>C)`) wired to a gated D-latch enable; an over-claim is a *forbidden state*, like the SR-NOR `S=R=1`, the latch cannot store. **Exhaustive** over all 16 states: VALID equals the integer rule, the guard blocks exactly the inflating loads, the stored state is never inflated. The invariant now holds at three levels — software (`claim_ledger`), policy (`rsi_engine`), and logic gates | BUILT | verified 7/7 |
| `counterfactual_fairness.py` | **intervention discipline transferred to causal fairness** (a *domain transfer* of the same `do()` machinery, not a new axis). Counterfactual fairness on a *known* synthetic SCM (abduct U → `do(A←a')` → predict), total effect + path-specific effects; demonstrates the verdict is **partition-relative** (same indirect-only model is fair under "block direct path" and unfair under "block all A→Y"). Exposes the two hidden variables: the **graph** (unidentifiable from observation → real-world FRONTIER) and the **path partition** (a DECLARED normative boundary the math can't decide). **MEASURED only relative to the declared SCM + partition.** Reports resource accounting (SCM evals / interventions / paths), never a bare fairness bit. The stack's invariant generalizes: a counterfactual claim must carry the assumptions that make it meaningful | BUILT | verified 8/8 |
| `resource_accounting.py` | **resource cost-accounting (a layer attached to the suite, not a 5th RSI axis)** — measures *work avoidance*: naive (full-verify every candidate) vs gated (cheap single-task screen → full check only on survivors), counting capability evaluations. Reports `work_avoided` **signed and measured, never asserted positive** (a weak screen spends *more* — that's an outcome), the screen's fidelity cost (false negatives missed / false positives wasted — no free lunch), and **η = true_promotions / capability-evals** (naive, gated, Δη) — the single ratio putting saved work and lost opportunity on one ledger; a *proxy* read with false-negatives, never "higher is better". **Energy `N/A`** (no joule/power/transition bench) and **hardware efficiency `SCOPED`**: `mechanism ≠ consequence` — the latch enforces `claim ≤ evidence`, not `heat ≈ 0`. The same no-inflation rule that stopped the RSI claim stops the energy claim | BUILT | verified 7/7 |
| `orbit_estimator.py` | **orbit — 3rd axis of the RSI decomposition** (branching=reproduce, generativity=frontier-grow, orbit=*where it travels*). Trajectory geometry: `O(t)=D(S_t,S_0)`, directedness, revisit/new-region rates under a *declared* metric (active-set symdiff + 2·|Δσ~1dp|) and identity. Strict improve-only policy is monotone ⇒ cannot revisit (expands then halts in a basin); explore policy exposes cycling/basin-confinement. Classifies **NO_TRAJECTORY (dead start) / CONVERGED / CYCLING / EXPANDING**; RSI-candidate orbit = EXPANDING (`O(t)↛0` + new regions); combined candidate `ΔC>0 ∧ G(s)>1 ∧ O(t)↛0`. Invariants: D is a metric, strict non-revisiting, displacement ≤ path-length. *Ghost caught: the first run was vacuous — the fixed all-coords root had 0 verified neighbours ⇒ steps=0; a 0-step halt is now classified `NO_TRAJECTORY` (dead start ≠ basin), and the root is chosen to have verified moves.* | BUILT | verified 8/8 |
| `report.py` | **Verified Improvement Dynamics Suite** — composes the four axes (ΔC, `m_offspring`, `m_novel`, `O(t)`) into one *profile* under a declared (system, domain, regime, identity) scope, reusing the verified estimators. Emits a candidate judgement on verified frontier expansion (YES / NO / **UNCERTAIN dominates any undistinguished axis**), **never `RSI = true/false`**. Self-tests = validity + interpretation-soundness + a `no_rsi_boolean` guard. The endpoint: a measurement of the *preconditions* RSI would require, not a detector for RSI | BUILT | self-tests written; awaiting on-machine run |
| `verified_branching_estimator.py` | **domain estimator** — estimates the theorem's empirical unknown `m_verified` by walking the verified-edit graph and counting, per parent, the single-edit neighbours that pass external∧replicated∧calibrated (verified offspring, not proposed edits). Reports `m_verified ≈ x ± SE`, sub/near/super classification, and `m(s)` across capability scale. *Run was underpowered (n=3, m=1.00±1.00 — the SE correctly made the estimate uninformative; the methodological ghost: in a (near-)subcritical domain a greedy walk dies before it can sample). Superseded by `generativity_estimator`* | BUILT | verified 7/7 |
| `generativity_estimator.py` | **generativity estimator (power + the right quantity)** — fixes the n=3 vacuity (many independent roots, pooled, **bootstrap CIs over roots**; informative only if the CI excludes 1, else "cannot distinguish") and measures both `m_offspring` (reproduction) and `m_novel` (net-new reachable verified states per verified parent — frontier expansion); the gap quantifies *overlap* (offspring overstates generativity). Invariant **`m_novel ≤ m_offspring`**. State-identity boundary declared (active set, σ~1dp) — an Arbitrary-Boundary choice that could be varied. Output is `m ± CI` under a regime, never "has/lacks RSI" | BUILT | verified 7/7 |
| `verified_improvement_theorem.py` | **formal endpoint — theorem vs model kept separate** (corrected after over-claiming "recursion impossible independent of compute"). *Classical theorem (true, conditional):* a Bienaymé–Galton–Watson process with offspring mean `m≤1` ⇒ a.s. extinction, `m>1` ⇒ survival w.p. `1−q`. *Modeling claim (NOT a theorem, empirical per domain):* verified self-improvement ≈ such a process; real systems break it (`mₜ` drift, interaction, depletion, new edit spaces) — open-ended RSI is itself a *departure* from GW. *Conditional conclusion:* if so modeled, `m_verified` is critical. Contribution: `m_verified` as an operational scalar + the runaway `m̂>1≥m_verified`. MC-verifies the classical criterion; toy domain *consistent with* `m_verified<1` (not universal) | BUILT | verified 7/7 |
| `docs/SELF_MODIFICATION_BOUNDARY.md` | recursion — can a runtime define its own frontier (NON_ORIENTABLE) | CONTRACT | paper |
| `docs/AUTHORITY_ARBITRAGE_BOUNDARY.md` | adversaries — advantage that cannot be adjudicated (SEVERED) | CONTRACT | paper |
| `docs/ADJUDICATION_THROUGHPUT_BOUNDARY.md` | throughput — can commitment outrun verification (FLOODED) | CONTRACT | paper |
| `docs/FAILURE_MODE_MATRIX.md` | routing — observation → candidate boundary + discriminator | CONTRACT | paper |
| Causal identifiability | INTERVENTION_ONLY — observation cannot determine causation | — | empirical (`experiments/latent_phase1` + `observation ≠ intervention`) |
| Replay witness (repo domain) | causal necessity of a repo fact (do(¬module) via tests) | ABSENT | — |
| Self-mod / authority / throughput *probes* | the code behind the three boundary contracts | ABSENT | — |
| Concurrency at the kernel | many actors, one region | ABSENT | — |

## The four orthogonal failure axes (the lattice, not a hierarchy)

Each fails for a fundamentally different reason; none reduces to another (`FAILURE_MODE_MATRIX`):

```
NON_ORIENTABLE     recursion / no global outside      (self-modification)     — CONTRACT
SEVERED            information loss                   (authority arbitrage)   — CONTRACT
FLOODED            verification / throughput deficit  (adjudication throughput)— CONTRACT
INTERVENTION_ONLY  identifiability limit              (causal identifiability) — empirical
```

Three are contracts ahead of code; one is empirically established. The matrix is connective tissue over them;
its diagnostic value is real only as those probes are built.

## The convergence stack, and the law operating across it

```
reality_status   one witness (kernel)        — every boundary on one fact, provenance per cell
repo_status      weaker evidence (static)    — identifiability DOWNGRADES to DECLARED (a parser cannot replay)
reconcile_status disagreement                — CONTESTED distinct from DECLARED; strength only lowers on conflict
runtime_witness  new evidence (execution)    — orthogonal blind spots to static; absence is DECLARED, never denial
witness_panel    coexistence                 — partial order; no witness globally strongest; absent first-class
```

The monotone law (`STRENGTH[reconciled] ≤ max[witnesses]`) is enforced by self-test in `reconcile_status`,
`runtime_witness`, and `witness_panel`. The strongest single demonstration: on a real repo, `repo_status`
reports `~28%` of axis-cells genuinely measured and **says so** instead of inflating a score; `runtime_witness`
contributes evidence static cannot **and** stays `DECLARED` where it is blind, with `MEASURED_BY_INTERVENTION`
appearing *nowhere* over static evidence.

## Recorded ghosts and open items (the part an honest ledger leads with)

- **`runtime_witness` over-counts coverage (caught by this comb).** On `requests` the trace reported 240 runtime
  edges and 118 "refinements" — but several are *attribute imports*, not modules
  (`requests.__version__.__author__`, `__cake__`, …): the trace treats every `from x import f` name as a
  submodule without verifying `x.f` *is* a module. **The reconciliation *strength* discipline is unaffected (8/8;
  nothing inflated in strength).** What is not trustworthy is the *coverage* count — "earns new evidence" is real
  (dynamic module imports are genuinely caught) but the precise refinement number is inflated until the trace
  filters `fromlist` entries to those actually in `sys.modules`. Recorded, not laundered. Fix is ~3 lines; until
  then the number is a lower-confidence figure.
- **Replay witness for the repo domain is ABSENT.** Identifiability is `MEASURED_BY_INTERVENTION` only in the
  kernel (which can replay its log); for a real repo it stays `DECLARED`. A test-execution intervention
  (`do(¬module)` via running the suite) would change that — not built.
- **Three of the four failure-axis probes are contracts, not code.** `FAILURE_MODE_MATRIX` is therefore a paper
  diagnostic until they exist; the matrix already specifies what each must *emit* to stay separable.
- **`reconcile_status` self-test not separately logged here** (verified transitively via the witnesses that
  import it). Confirm `reconcile_status.py` is committed — `runtime_witness` and `witness_panel` import it.
- **Single-process logic throughout.** No concurrency, networking, scale, or wall-clock throughput. `runtime_witness`
  tracing executes target import-time code (candidate, trusted code only).
- **A self-test enforced an expected outcome (caught externally, fixed).** `limit_discriminator`'s first version
  asserted `strong ≥ weak` and `carry < reset` as pass/fail gates — but those are *theory expectations*, not
  correctness invariants. When the data refuted them (`A` was genuinely REFUTED; raw-weight-carry genuinely
  failed), the bench reported "broken" instead of "interesting." **A verification gate that enforces the
  experimenter's predicted result is itself a form of inflation** — it launders a prior into a green check.
  Rewritten so self-tests check **validity + classifier soundness** only, including `verdicts_consistent_with_data`
  (fires iff a verdict contradicts its own numbers). New separators this surfaced:
  `experiment-ran ≠ hypothesis-confirmed`; `measurement-valid ≠ prediction-true`. **Governing asymmetry (the
  principle behind all three): _expectation may follow evidence; evidence may not follow expectation._** A loop
  that reinterprets results until the prior survives is where proxy collapse begins; a healthy loop lets the error
  make the model more accurate rather than teaching it to defend the error. Every witness here is, at bottom, a
  test that this loop stays open to correction. It also exposed two domain
  ghosts worth keeping: fair-carry weight transfer was *negative* here (entangled few-sample estimates transfer
  distortion), and a *stronger* search reached a *lower* held-out ceiling (search↔evaluator coupling — harder
  optimization of a noisy self-metric overfits it).

- **A↔D is persistent, not explosive — and `optimization-pressure ≠ search-budget`.** `inflation_vs_search` swept
  K∈{1,2,4,8,16,32}; inflation held ~+0.07 *flat* across a 31× rise in evaluations (93→2883) because K≥2 yield
  identical optimizers (small discrete proposal space ⇒ best-of-K collapses to greedy-best at K≈2). The bench
  spent more *budget* without applying more *pressure*. The earlier `limit_discriminator` "stronger search → worse
  reality" endpoint is therefore **CONTESTED** — its two points differed in generations and loop type, not clean
  pressure. Net update, in the charitable and correct reading: inflation EXISTS, is MEASURABLE, and is STABLE in
  this regime — a tighter, more useful claim than the explosive-coupling suspicion it replaced. The open question
  moves to transfer: *what changes external capability without raising inflation?*

- **The RSI→transfer arc's net result is deflationary, and that is the finding.** Across the self-improvement
  ladder (`self_improvement_witness` → `recursion_witness` → `limit_discriminator` → `inflation_vs_search` →
  `transfer_representation` → `transfer_robustness`): a self-improvement *step* is real and provable; *recursion*
  (d²/dt²>0) is not observed; the evaluator gap is *persistent but not explosive*; and across a 3×3 regime grid
  **no transfer encoding robustly beats the cold baseline** (wins are sparse and seed-clustered — sampling flukes).
  The durable artifact is not a capability but the *method*: each witness tightened the rules under which the next
  could claim anything, and that epistemic loop — not the optimizer — is the only thing that measurably compounded.
  `expectation may follow evidence; evidence may not follow expectation`. The capstone `rsi_engine` makes the
  conclusion executable: an "RSI engine" defined defensibly is not a runaway optimizer but a self-modifier that
  promotes an edit *only* through a reconciler gate (external gain ∧ replication ∧ calibration). Run head-to-head
  with a naive proxy-runaway, the gated engine improved on reality while staying under-confident (negative
  inflation) and the runaway deceived itself (proxy up, reality down) — but the gate promoted just **once in 60
  rounds**: verified self-improvement is real and rare, and the conservatism *is* the mechanism, not a safety
  bolt-on. The only loop that recursively self-improved here was the verification discipline itself.

## What this ledger does and does not establish

It establishes that the stack's **central law holds across every built layer on real data**: provenance strength
is never inflated as evidence passes through extraction (downgrade), disagreement (refinement / CONTESTED),
execution (orthogonal blind spots), and coexistence (partial order) — and that weakness, absence, and conflict
are *recorded as first-class outputs* rather than hidden. The comb that produced this document is itself an
instance of the discipline: it caught an inflated coverage claim and wrote it down.

It does **not** establish a complete system. Most of the failure-axis probes are paper; the replay witness for
real systems is absent; nothing here has met concurrency or scale. The rarer property being claimed is not that
the system knows everything — it is that **every claim remains attached to the strongest evidence that actually
earned it, even as more witnesses and layers are added, and the gaps are named rather than papered over.**
`declared ≠ verified`; `integrity ≠ truth`; the full picture never arrives as a single object — which is exactly
why the ledger, not a score, is the honest summary.
