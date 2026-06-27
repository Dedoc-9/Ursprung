<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Recursive Improvement Under Frozen Evaluation Boundaries: A Proof-Oriented Analysis of the Repo Verification Architecture

**Document type:** design/proof analysis, intended for technical appendix / design review. It is written to
be inspected and challenged. It contains no roadmap and proposes no future system as fact; where a future
mechanism is discussed it appears only as an *admissibility criterion* tied to a stated proof obligation.

**Epistemic tags used throughout.** Every load-bearing statement is tagged:
- **[ARCH]** — an *implementation fact*: a property enforced by the structure of the current repo code.
- **[TEST]** — supported by an executing test suite in the repo (named where relevant).
- **[THM-C]** — a *conditional theorem*: a deductive consequence of explicitly stated premises.
- **[OPEN]** — a hypothesis or obligation that is *not* established by the current repo.

A claim tagged [ARCH] or [TEST] is not thereby a mathematical proof; it is an engineering guarantee with a
stated enforcement mechanism. The distinction between [THM-C] (valid given premises) and the *enforcement*
of those premises ([ARCH]/[TEST]/[OPEN]) is maintained deliberately.

---

## 0. Object of analysis

The substrate is the repo's verification architecture at the current commit: `transition.py`
(`TransitionRelation`), `engine.py` (`VerificationEngine`, `ExplicitStateBFSEngine`), `symbolic_engine.py`
(`SymbolicEngine`, optional), `interfaces.py` (`VerificationResult`), `artifacts.py` (`Trace`, `Invariant`,
`ReachabilityCertificate`, `AnalysisResult`), `differential.py`, `conformance.py`, `diagnose.py`,
`counterfactual.py`, `repair.py`. The analysis treats these as fixed and reasons from their interfaces.

Central claim under analysis:

> A system can recursively improve its search, ranking, abstraction, and proposal mechanisms **only while the
> criteria that determine correctness remain outside the improvement loop.**

Formal separators to be established:

```
improved_map            ≠  changed_criterion
higher_internal_score   ≠  increased_truth
candidate_generation    ≠  correctness_definition
```

**Contribution (framing).** The contribution analyzed here is *not* a mechanism for recursive
self-improvement. It is a set of conditions under which recursive improvement remains **distinguishable from
self-certifying drift** — i.e. recursive *capability* improvement without recursive *authority* creation. The
object of value is not self-modification; it is the preserved distinguishability between improvement and
inflation. The strengthened statements in §9 make this precise.

---

## 1. Definitions

Let a **world** `W` be a value accepted by `engine.build_model` (a `WorldModel`: initial state, transition
relation, invariant set, action alphabet). Let `O` be verification options (depth bound, etc.).

**Verification function.** `V : (W, O) → R`, where `R` is a `VerificationResult` carrying a status
`σ ∈ {CLOSED, BOUNDED, VIOLATED}`, an optional witness `Trace`, and an optional `ReachabilityCertificate`.
`V` is realized by an engine satisfying the `VerificationEngine` protocol. **[ARCH]**

### 1.1 Territory (the components that determine correctness)

```
Territory  T  =  ( R, I, E, D )
```

- `R` — the transition relation (`TransitionRelation`): which `(s, a, s')` transitions exist.
- `I` — the invariant set (`Invariant` objects / supplied predicates).
- `E` — the verification engine(s) implementing `V`.
- `D` — the differential-agreement criterion (`differential.py`): two engines must agree.

`T` defines the correctness predicate. Write `Corr_T(W)` for "the verdict and artifacts `V` assigns to `W`
under `T`." Correctness is *relative to* `T`; the repo makes no claim of correctness independent of `T`
(this is the standing separator `integrity ≠ truth`).

### 1.2 Map (the components that search, explain, rank, or propose)

```
Map  M  =  ( diagnose, counterfactual, repair-generation,
             experiment-selection, heuristic-ranking, abstraction-proposal )
```

Of these, `diagnose.py`, `counterfactual.py`, and `repair.py` exist; experiment-selection, ranking, and
abstraction-proposal exist only as components elsewhere in the repo (`discrimination_matrix.py`,
`transfer_robustness.py`) or as obligations. **[ARCH]/[OPEN]**

### 1.3 Boundary

The **boundary** `B` is the interface separating `M` from `T`. The admissibility rule:

```
map changes        are admissible              (M may be replaced/optimized)
territory changes  require external adjudication (T may be changed only by a human/external authority)
```

**Lemma 1.3 (V does not consume M).** `V`'s domain is `(W, O)`; `M` does not appear in it. The engines read
`R` (via `relation.successors` / `relation.materialize`) and `I`; they do not read diagnosis, counterfactual,
repair, ranking, or experiment-selection state. **[ARCH]**, **[TEST]** (`conformance.py` checks
`relation_unaware`: the transition relation exposes no search/diagnosis/repair concerns; `test_engine.py`
checks `engine.run == check()` independent of any map component). This lemma is the hinge of every result
below.

---

## 2. Existing proof spine

The repo already enforces three separations relied upon here.

### 2.1 Engine separation — `engine ≠ semantics`

An engine *evaluates* a world defined by `R`; it does not *define* `R`. **[ARCH]** (`ExplicitStateBFSEngine`
and `SymbolicEngine` both consume `TransitionRelation`; neither defines transitions). **[TEST]**
`test_engine.py` (`relation_unaware`, `engine_matches_shim`), `test_transition.py` (relation = source of
truth, differential-checked against the legacy inline successors).

### 2.2 Artifact separation — `analysis ≠ proof`, `candidate ≠ repair`

Interpretation and proposals are subordinate to verification. **[ARCH]** `AnalysisResult` requires a scope
and ≥1 `Limitation` at construction; `RepairCandidate` has no `fixed`/`safe`/`correct` field and exposes
`restores_world` only as an enum tied to `(engine, bound, status)`. **[TEST]** `test_analysis_contract.py`
(honesty contract), `test_repair.py` (`bounded_honesty`, candidates seeded only from verified critical sets).

### 2.3 Differential constraint — agreement without changing the criterion

Independent engines must agree on the same world without altering what agreement means. **[ARCH]**
`differential.py` compares engines; equivalence is *same status + replayable witness of equal length*, not a
redefined verdict. **[TEST]** `test_differential.py` (5/5 models), `test_symbolic_engine.py` (`no_unsat_status`:
no engine introduces a new verdict class). The differential criterion `D` is part of `T`; the harness uses it,
it does not let an engine rewrite it.

---

## 3. Recursive improvement theorem

**Definitions.** A **recursive process** `P` produces a sequence of map-states `M_0, M_1, …` together with a
sequence of proposals (candidate worlds / candidate experiments). `P` carries an append-only history `H`
(experiment records). An internal **score** `s(M_k, H)` is any measure `P` uses to prefer one map-state over
another (e.g. experiments-to-first-ghost, fraction of candidates that survive re-verification). `P` is
**admissible** iff:

- (P1) `P` modifies only `M`; `T = (R, I, E, D)` is held fixed across all steps.
- (P2) Every proposal is re-evaluated by `V` under the frozen `T` before being treated as established.
- (P3) `H` is never substituted for a fresh `V` evaluation (`replay ≠ correctness`).
- (P4) `P` cannot modify `Corr_T` — the function by which it is graded.

### Bounded Recursive Improvement Principle (BRIP) — [THM-C]

*If `P` is admissible, then for every world `W` and every pair of map-states `M_a, M_b` reached by `P`,*

```
Corr_T(W) under M_a  =  Corr_T(W) under M_b
```

*i.e. status `σ`, witness validity, and certificate validity are invariant under the map. Consequently any
change in `s` reflects a change in process (time, ordering, coverage), not in `Corr_T`.*

**Justification.** By Lemma 1.3, `V` is a function of `(W, O, T)` and does not take `M` as an argument. By
(P1) `T` is fixed; by (P3) the recorded history `H` is not a verification substitute, so the *established*
verdict for any `W` is always a fresh `V(W,O)` under fixed `T`. Therefore `Corr_T(W)` is independent of which
admissible `M` produced or ordered the proposals. ∎ (contingent on premises P1–P4)

**Corollaries.**
- **C1** `higher_internal_score ≠ increased_truth`: `s` ranges over `M`/`H`; `Corr_T` is invariant over them.
- **C2** `candidate_generation ≠ correctness_definition`: candidate generators live in `M`; `Corr_T ∈ T`.
- **C3** `improved_map ≠ changed_criterion`: trivial from (P1).

**Status of the premises (the real content).** BRIP is valid *given* P1–P4. Their enforcement is the
engineering question:
- P1, P4 enforcement: **[ARCH] for the current code** (no map component can reach `T`, because `V` does not
  consume `M` and the map modules import the territory read-only). **[OPEN] for any future loop**, which must
  be *structurally denied write access* to `R/I/E/D` (see §6, §4 Case B).
- P2 enforcement: **[ARCH]/[TEST]** — `repair.py` computes `restores_world` only by re-running `V` under a
  forbidden-action relation; it never asserts restoration without re-verification.
- P3 enforcement: **[OPEN]** — there is currently no `H` (no experiment log); when one exists, "never
  substitute `H` for `V`" must be a tested invariant.

---

## 4. Proof by failure modes

Each case shows that admitting a *territory* change into the loop violates a BRIP premise and destroys the
meaning of the score. These are deductive (reductio) arguments under the §1 definitions.

### Case A — self-modifying invariants  [THM-C, violation of P4]

Suppose `P` may change `I` (`I ∈ T`). Replace `I` by a weaker `I' ⊂`-strength such that `I'(s)` holds on a
superset of states. Then for a fixed world `W`:

```
weaker invariant  →  fewer states violate  →  fewer VIOLATED verdicts  →  higher s
                  →  W is unchanged
```

`Corr_{T'} ≠ Corr_T` because `T' = (R, I', E, D)`. The world did not become more correct; the criterion
became weaker. Hence `score_improvement ≠ truth_improvement`. This is the canonical inflation move and is
exactly what `no_inflation_latch.py` / `claim_lattice.py` (No-Strength-Creation) already forbid at the gate
level. **Conclusion:** invariant change is a territory change → inadmissible inside `P`; admissible only via
external adjudication (§6). ∎

### Case B — self-modifying verifier  [THM-C, violation of P4]

Suppose `P` may change `E` or `D` (the engines or the agreement criterion). Then the judge depends on the
proposer, and the pipeline degrades from

```
proposal → fixed judge → evaluation          (V independent of M; verdict has independent meaning)
```

to

```
proposal → modified judge → approval          (V depends on M; verdict is self-referential)
```

Once `V` depends on `M`, Lemma 1.3 fails, BRIP's justification collapses, and `Corr` loses independent
meaning: the system can obtain `CLOSED` by adjusting the judge rather than the world. **Conclusion:** engine
/ differential-criterion change is a territory change → inadmissible inside `P`. The repo's
`docs/AUTHORITY_ARBITRAGE_BOUNDARY.md` is the threat model for precisely this. ∎

### Case C — internal metric creation (Goodhart)  [THM-C + OPEN mitigation]

Suppose the optimizer both *authors* its success metric `s` and is *graded* by `s`. Even if `s` ranges only
over `M` (so P1/P4 are not directly violated), optimizing `s` need not improve the true objective: `s` is a
proxy, and an optimizer free to define its own proxy will tend to maximize the proxy rather than the target
(`salience ≠ importance`). The failure becomes a P3/P4 violation the moment `s` is allowed to *substitute*
for `V` (accepting a candidate because `s` is high rather than because `V` re-verified it) or to *define*
acceptance.

**Admissible mitigation (not a new metric):** the loop must route scoring through the repo's *frozen*
discriminators — `limit_discriminator.py` (improvement vs search vs inflation vs transfer),
`inflation_vs_search.py`, `recursion_witness.py` (held-out acceleration), graded by `eval_harness.py` against
random/degree baselines on held-out worlds. A loop that authors no success metric of its own cannot Goodhart
its own grade. The enforcement of "authors no metric" is **[OPEN]** for a future loop and must be a tested
property. ∎

---

## 5. Safe recursive loop — proof sketch

The admissible loop:

```
failure (VIOLATED)
   ↓
Trace (witness)
   ↓
analysis (diagnose / counterfactual)         — AnalysisResult, subordinate to V
   ↓
candidate (repair proposal)                  — RepairCandidate, seeded from verified critical set
   ↓
re-verification under frozen T               — fresh V; restores_trace / restores_world(engine,bound)
   ↓
record (append-only H)                       — never substituted for V
   ↓
better proposal ordering (M update)          — search/ranking only
```

**Proof requirement (the invariance obligation).** The established verification result must be invariant
under the proposal strategy. Formally, for proposal strategies `π_a, π_b` (both admissible),

```
∀ W:  V_T(W) is identical under π_a and π_b   in { σ, witness-validity, certificate-validity }
```

while `π_a, π_b` may differ in *time, ordering, number of attempts, which experiments are chosen*.

**Status.** The invariance obligation follows from BRIP (§3) for any admissible `P` **[THM-C]**. Its
*evidence* in the current code, for the engines that exist:
- determinism of `V` per engine — **[TEST]** (`test_engine.py`, `test_kernel_check.py`, `test_interfaces.py`).
- engine-independence of `σ` and witness validity — **[TEST]** (`differential.py`, 5/5).
- verdicts do not depend on any map component — **[ARCH]/[TEST]** (Lemma 1.3, `conformance.relation_unaware`).
For a *future* `ResearchLoop`, the obligation "verdict invariant under proposal strategy" is **[OPEN]** and
must be discharged by a test that varies the strategy and asserts identical `σ`/witness/certificate.

---

## 6. ResearchLoop admissibility criteria

A future loop, if built, is admissible only as a **proposal mechanism, not an authority mechanism**. This
section states criteria, not a design.

**Allowed (map-only):** ranking candidates; selecting experiments; generating hypotheses; proposing repairs;
proposing abstractions *that are checked by the exact engine before use*.

**Forbidden (territory):** changing what counts as verified; changing `R` (semantic rules); removing or
suppressing failed cases from `H`; rewriting `I`, `E`, or `D`.

**Admissibility predicate.** A loop `P` is admissible iff it satisfies P1–P4 (§3) and, additionally:
- (A1) `P` has *no write access* to the files defining `T` (`transition.py` semantics, the supplied `I`,
  `engine.py`, `differential.py`). This must be enforced structurally and tested adversarially — the
  authority-arbitrage / self-modification probes already in the repo are the template. **[OPEN]**
- (A2) Every territory-change *proposal* is emitted as a candidate to external adjudication with an impact
  analysis (which historical verdicts in `H` would flip), and is never auto-applied. **[OPEN]**
- (A3) An inflation check rejects any proposal that turns a previously-`VIOLATED` `W` into `CLOSED` by
  changing the criterion rather than the world. **[OPEN]**, with `no_inflation_latch.py` as the existing
  mechanism to reuse.

---

## 7. Proof status table

| Claim | Status | Evidence |
|---|---|---|
| engine / semantics separation (`engine ≠ semantics`) | architectural invariant + tested | `engine.py`/`transition.py`; `test_engine.py`, `test_transition.py`, `conformance.relation_unaware` |
| artifacts are non-authoritative (`analysis ≠ proof`, `candidate ≠ repair`) | tested | `interfaces.py`, `artifacts.py`; `test_analysis_contract.py`, `test_repair.py` |
| counterexamples replay (witness validity) | tested | `Trace.build` + replay checks; `test_kernel_check.py`, `test_symbolic_engine.py`, conformance |
| repair candidates require verification | tested | `repair.py` (`restores_world` only via re-verification); `test_repair.py` |
| differential agreement without redefining the criterion | tested | `differential.py`; `test_differential.py` |
| **V does not consume the map (Lemma 1.3)** | architectural invariant + tested | Lemma 1.3; `conformance.relation_unaware`, `test_engine.engine_matches_shim` |
| **BRIP** (safe recursive improvement) | conditional theorem | valid given premises P1–P4; premise *enforcement* partly [ARCH], partly [OPEN] |
| verdict invariant under proposal strategy | conditional theorem; tested for current engines | BRIP; `differential.py`, determinism tests. [OPEN] for a future loop |
| autonomous truth improvement | **not established** | requires external evidence; structurally excluded by Cases A/B |
| no-metric-self-authorship in a future loop | **open obligation** | must be a tested property of any built loop |

---

## 8. Explicit non-claims

The repo does **not** establish:
- general intelligence;
- autonomous self-improvement (improvement of `Corr` without external adjudication);
- automatic truth discovery (`CLOSED` is proof *over the chosen alphabet/transition function*, not global
  truth; `BOUNDED ≠ proof`; `unsat-at-k ≠ unreachable`);
- self-authorizing repair (a candidate is not a fix; `restores-under-(M,E,K) ≠ world-safe`);
- elimination of external reality checks (the differential harness catches engine disagreement, not all bugs;
  agreement is evidence, not proof).

It establishes a narrower claim, conditionally:

> **A system can improve its reasoning process while preserving correctness criteria iff those criteria
> remain outside the improvement loop.** (BRIP, §3, contingent on P1–P4.)

The forward direction (admissible `P` preserves `Corr_T`) is the conditional theorem. The reverse direction is
witnessed by the failure modes (§4): admitting a territory change into the loop produces score improvement
without truth improvement, which is what the No-Strength-Creation / no-inflation results in the repo already
forbid.

---

## 9. Strengthened boundary theorems

These sharpen §3–§6 from "safe-RSI design" into stated boundary conditions. Each is a named claim with a tag.

### 9.1 Recursive Improvement Preservation Theorem (RIPT) — [THM-C]

*A recursive system preserves validity across self-modification iff every modification is evaluated by a
criterion independent of the modification process itself.* Immediate corollary:

```
self-improvement + frozen criterion   =  optimization
self-improvement + mutable criterion  =  inflation risk
```

BRIP (§3) is the instance of RIPT in which the independent criterion is the territory `T`. RIPT states the
general constraint; BRIP instantiates it for this repo. The "iff" is justified forward by BRIP and backward
by the failure modes (§4): a criterion that is *not* independent of the process can be moved by the process,
which is precisely inflation.

### 9.2 Recursive Efficiency Gain — the measurable RSI quantity — [OPEN, but grounded]

"Improvement" is made measurable and authority-free. Define, for a fixed verified output,

```
Recursive Efficiency Gain (REG) = work(baseline) / work(policy),   same verified result
                                ≈ verified progress per unit search
```

**Claim.** The first measurable form of RSI under this architecture is *increased verified progress per unit
search*, not increased authority. Example: a policy that reaches the same 10 verified repairs after 100
candidate evaluations instead of 1000 has `REG = 10` with the **truth boundary unchanged**. REG is
instrumentable from existing repo artifacts — `resource_accounting.py` (work-avoidance), `orbit_estimator.py`
(trajectory geometry), `causal_scale_bench.py` (operating envelope) — and must be graded on held-out worlds
via `eval_harness.py` against a naive-ordering baseline. Status [OPEN]: not yet instrumented inside `verify/`.

### 9.3 Search acceleration vs semantic acceleration — [THM-C separator]

```
search acceleration   (rate of REACHING verified conclusions)   :  permitted
semantic acceleration (rate of DEFINING  conclusions)           :  forbidden
```

**Claim.** A system can recursively increase the rate at which it reaches verified conclusions without
increasing the rate at which it defines them. Follows from Lemma 1.3 (the verdict does not depend on the map)
and BRIP. This is the crispest statement of the safe/dangerous split: speed of finding ≠ change in what counts.

### 9.4 Memory Without Authority — [THM-C]

For the append-only history `H` (the `ExperimentLog`, §3):

```
H  affects      the proposal distribution
H  does NOT affect  the correctness predicate Corr_T
```

**Claim.** The system accumulates experience without accumulating authority. This is premise P3 made into a
property: `experience ≠ authority`, `replay ≠ correctness`. Memory is a prior over what to try next, never a
substitute for a fresh `V` evaluation.

### 9.5 Bounded Autonomy Ladder — [definition + boundary]

```
Level 0 : verification only
Level 1 : self-improving search                 ┐
Level 2 : self-improving explanation            │  map-only — admissible (BRIP holds)
Level 3 : self-improving proposal generation    ┘
Level 4 : self-modifying criteria               ←  invalid boundary crossing (territory)
```

**Claim.** Autonomy is not binary. The boundary is crossed exactly when the system modifies *the judge*
rather than *the contestant*. Levels 0–3 are map operations; Level 4 is a territory change and is admissible
only via external adjudication (§6).

### 9.6 Anti-Goodhart RSI Criterion — [THM-C]

The admissible loop is not "maximize score" but a *constrained* optimization:

```
argmax_policy  improvement(policy)
   subject to  verdict(policy, W) = verdict(baseline, W)   for all W
```

**Claim.** The policy may improve; the verdict may not move. Because the optimizer cannot move the quantity
it is graded against, it cannot Goodhart its own grade. This is BRIP's invariance requirement written as an
optimization constraint, and it is why the loop must author no success metric of its own (§4 Case C).

### 9.7 Approximation Admissibility (one-directional detectability) — [THM-C]

An abstraction (e.g. a future CEGAR layer) is admissible iff its errors are *one-directionally detectable*:

```
abstract says UNKNOWN  → exact engine decides     :  allowed
abstract says CLOSED   → trust the abstraction     :  forbidden
```

**Claim.** Approximation may accelerate discovery but cannot replace adjudication. The load-bearing test is
"no false CLOSED": any abstract-CLOSED must be confirmed exact-CLOSED. This sharpens the §6 (A-criteria) and
the Phase-3 row into a single admissibility condition.

### 9.8 Recursive Honesty Invariant — [ARCH principle]

*Every recursive layer inherits the limitations of the layer beneath it.* No layer may silently upgrade:

```
suggestion → fact → authority → criterion
```

Each layer's claim is strictly weaker-or-equal to the verifier's, and carries the weaker layer's limitations:

```
verification : "this state violates invariant X"
analysis     : "this trace suggests cause Y"            (AnalysisResult: scope + ≥1 limitation, required)
repair       : "this candidate prevents this trace under bound K"   (restores-under-(M,E,K) ≠ world-safe)
research loop: "this strategy improves candidate selection"          (REG; verdict invariant)
```

This is realized today by the `AnalysisResult` honesty contract (limitations travel; §2.2) carried through
`diagnose` / `counterfactual` / `repair`. The invariant is the monotone non-upgrade of epistemic status
across layers.

### 9.9 Recursive Capability Preservation Theorem — [THM-C]

Let verified work `w(π, W)` be the number of frozen-verifier evaluations a policy `π` performs to reach the
verified result on world `W`, and `REG(π, W) = w(baseline, W) / w(π, W)`.

**Theorem.** Suppose (i) the semantics `R` are fixed, (ii) the verification engine `E` is fixed, (iii) the
invariant set `I` is fixed, (iv) evaluation is performed *solely* by the frozen verifier, and (v) the policy
may reorder candidate generation but cannot alter evaluation. Then for any observed `REG(π, W) > 1`, the
improvement reflects **only search efficiency** and **cannot arise from criterion modification**.

**Justification.** By Lemma 1.3, `w(π, W)` counts evaluations of `V`, and `V` is a function of `(W, O, T)`
with `T = (R, I, E, D)` fixed by (i)–(iv); the policy enters only the *order* in which candidates are
submitted to `V`, not `V` itself (v). The verified *result* for `W` is therefore identical under any policy
(this is BRIP, §3); only the count `w` differs. Hence any change in `REG` is a change in search effort under
an unchanged `Corr_T`. ∎

The theorem is deliberately silent about *learning*: it does not assert that any policy improves. It asserts
the **contrapositive guarantee** — *if* improvement is observed, it cannot have come from moving the
goalposts. This is the load-bearing theoretical property behind every measured `REG`: it licenses reading a
held-out efficiency gain as capability rather than inflation. `observed-REG-gain ⇒ search-only`.

---

## Conclusion

The contribution is not a mechanism for unrestricted recursive self-improvement. It is a proof-oriented
architecture for **recursive capability improvement without recursive authority creation**. The system may
become better at *finding, explaining, and proposing* changes while remaining unable to *redefine the
conditions under which those changes are judged*. The central resource is therefore not self-modification but
**preserved distinguishability between improvement and inflation**.

Recursive improvement, here, is the controlled optimization of methods under an invariant correctness
boundary: `improved_map ≠ changed_criterion`; `higher_internal_score ≠ increased_truth`;
`candidate_generation ≠ correctness_definition`; `search_acceleration ≠ semantic_acceleration`;
`experience ≠ authority`; `integrity ≠ truth`. The verification result is meaningful exactly insofar as it is
produced by a judge the proposer cannot move.
