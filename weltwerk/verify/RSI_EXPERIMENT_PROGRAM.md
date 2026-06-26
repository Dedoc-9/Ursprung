<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# An Experimental Program for Demonstrating Recursive Capability Improvement Under a Frozen Evaluation Boundary

**Document type:** research design (experiments + metrics + falsifiers). No results are claimed; nothing here
has been run. Everything is tagged **[DESIGN]** (proposed) unless it cites an existing repo artifact.

**Standing conclusion (not weakened):** recursive improvement is *controlled optimization of methods under
an invariant correctness boundary*. This program seeks evidence for the **map** improving, never the
**judge**. It must preserve, and is instrumented to detect violations of:

```
improved_map ≠ changed_criterion        higher_internal_score ≠ increased_truth
candidate_generation ≠ correctness      search_acceleration ≠ semantic_acceleration
experience ≠ authority                   integrity ≠ truth
```

**The central question.** How do we distinguish a system that merely *accumulates history* from one that is
*actually becoming better at solving problems*? Answer adopted here: **held-out transfer under a frozen judge
with compute equalized.** A system that has only memorized improves on seen problems and fails to transfer;
a system that has gained capability improves on *unseen* problems at *equal compute* without moving any verdict.

## 0. The three non-negotiable controls (every experiment carries all three)

1. **Verdict-invariance control.** For every map change, re-run the frozen verifier on a fixed audit set and
   assert *no* `CLOSED`/`BOUNDED`/`VIOLATED` verdict, witness validity, or certificate validity changed. Any
   coincidence of "gain" with a moved verdict ⇒ inflation ⇒ the result is rejected, not celebrated. (Enforced
   by `differential.py` + determinism tests; this is BRIP made operational.)
2. **Held-out transfer control.** The map adapts on a TRAIN distribution; *all* improvement is measured on a
   structurally-disjoint HELD-OUT distribution. Report `transfer_ratio = gain_heldout / gain_train`.
3. **Compute-equalization control.** Compare policy vs baseline at *equal search budget* (or measure work-to-
   identical-result). A gain that vanishes when compute is equalized is not capability; it is spending.

If a measurement cannot carry all three, it does not enter the claim.

## 1. Methodology

**Frozen territory** (`R` transition models, `I` invariants, `E` engines, `D` differential criterion) — never
touched by the loop. **Mutable map** — heuristics, ranking policies, candidate generators, abstractions,
experiment selection. A **world distribution** `W ~ 𝒟`: parameterized families of `.wrk` worlds (topology
families already exercised by `causal_scale_bench.py`; the `times_square` scenario; programmatically generated
faction/grid worlds). Split `𝒟` into `𝒟_train` and `𝒟_heldout` by **structural family and seed**, disjoint —
not by instance, so memorizing instances cannot leak.

**Ground truth is the verifier, and where needed an exhaustive oracle.** For candidate-quality metrics, the
"gold" critical-event set is computed by *exhaustive ablation* (the expensive but exact version of
`counterfactual.py`), exactly as `eval_harness.py` insists gold be independent of the method under test.

**Memorization vs capability discriminator.** Real capability: `transfer_ratio ≈ 1` (stable, not
deteriorating). Memorization: `transfer_ratio → 0`. This single number does most of the falsification work.

## 2. Candidate measurements (each with the five-point analysis)

For each: **(1) what improves · (2) what stays frozen · (3) baseline required · (4) how it could be faked ·
(5) the falsifying experiment.**

### 2.1 Search-efficiency improvement
1. Candidates evaluated to reach the *same* verified result — `verified_progress / search_cost` (REG).
2. World, verifier, final verdict.
3. Random/naive candidate ordering **and** compute-equalized policy.
4. (a) memorizing seen worlds; (b) narrowing the candidate space so some valid repairs are *missed*
   (trading recall for speed); (c) disguised extra compute.
5. On HELD-OUT: `REG_policy ≤ REG_baseline` ⇒ no gain. OR **recall drop** — policy fails to find a verified
   repair the baseline found ⇒ claim rejected (it traded correctness for speed, a hidden criterion change).

### 2.2 Counterexample learning
1. Invalid candidates before first valid; tries-to-verified-repair on a world *class* after experience.
2. Verifier, semantics.
3. Cold loop (each world solved with no memory).
4. Memorizing the test set (instances) rather than the structure.
5. On a HELD-OUT family sharing structure with TRAIN: no reduction vs cold ⇒ it was memorization, claim dies.

### 2.3 Repair-proposal quality
1. Candidate **quality**, not acceptance: first-valid-candidate rank; invalid-before-valid count;
   critical-event identification accuracy vs the exhaustive gold; counterfactual reduction efficiency.
2. Verifier; the exhaustively-computed gold critical sets.
3. Random ranking; current unranked `repair.propose`.
4. Quality measured by a metric the optimizer authored (Goodhart) — forbidden; gold must be the independent
   exhaustive set. Or ranking tuned to the eval worlds.
5. On HELD-OUT: first-valid rank no better than random, OR critical-ID accuracy not above the degree/random
   baseline (`eval_harness` discipline) ⇒ no quality gain.

### 2.4 Experiment-selection improvement
1. Information gained per experiment; uncertainty reduction; experiments-to-isolate the true causal variable.
2. What counts as evidence; the verifier.
3. Random experiment selection vs `discrimination_matrix.py`-guided selection.
4. "Uncertainty reduction" scored by a self-defined metric — must instead be verifier-grounded (e.g. number
   of candidate explanations still consistent with `V`). Or experiments that look informative but don't isolate.
5. On synthetic worlds with a known planted causal variable, HELD-OUT: guided selection isolates it in ≥ the
   experiments random needs ⇒ no gain.

### 2.5 Abstraction / CEGAR improvement
1. Fraction of queries resolved without exact verification (less exact work).
2. The exact engine as oracle; the one-directional rule (abstract result never exceeds exact).
3. Exact-only verification.
4. The catastrophic fake: abstraction returns `CLOSED` unsoundly (a false proof).
5. **Any** abstract-`CLOSED` that the exact engine does not confirm `CLOSED` ⇒ the abstraction is unsound and
   the entire branch is dead (this dominates all efficiency numbers). Secondary: no reduction in exact work ⇒
   no gain. (This is the §9.7 one-directional-detectability admissibility condition, made a test.)

## 3. Proposed RSI metric suite

| Metric | Definition | Real-RSI signature | Inflation/memorization signature |
|---|---|---|---|
| **REG** (recursive efficiency gain) | `work(baseline)/work(policy)` at identical verified output, HELD-OUT | `> 1`, stable/rising | `≈ 1` on held-out |
| **transfer_ratio** | `gain_heldout / gain_train` | `≈ 1` | `→ 0` |
| **acceleration** | `recursion_witness.py` d²/dt² of verified-progress on a fixed held-out set | `≥ 0`, almost certainly **saturating** (see §7) | negative / noise |
| **verdict_invariance** | fraction of map-changes leaving all audit verdicts unchanged | `= 1.0` (required) | `< 1.0` ⇒ inflation, reject |
| **recall_preservation** | policy finds every verified repair the baseline found | `= 1.0` | `< 1.0` ⇒ correctness traded |
| **baseline_lift** | policy vs random/degree on ranking, held-out (`eval_harness`) | `> 1` | `≤ 1` |
| **compute_controlled_gain** | improvement at equalized search budget | `> 0` | `≈ 0` |

The loop **authors none of these for its own grading** — they are computed by frozen instruments
(`resource_accounting`, `recursion_witness`, `eval_harness`, `differential`, `limit_discriminator`). A loop
graded by a metric it defines is the anti-Goodhart violation (§9.6 of the proof doc).

## 4. Recursive Capability Improvement Principle (supportability assessment)

| Condition | Supportable? | How it is measured / enforced |
|---|---|---|
| 1. future proposals outperform past under identical evaluation | **[DESIGN] yes, measurable** | REG over iterations on a *fixed* held-out set |
| 2. improvement persists on held-out | **the crux; measurable** | `transfer_ratio`; structurally-disjoint families |
| 3. evaluation boundary unchanged | **[ARCH]+[TEST], enforced** | `verdict_invariance = 1.0`; Lemma 1.3; `differential` |
| 4. not explained by compute alone | **[DESIGN] yes** | `compute_controlled_gain` at equal budget |
| 5. no authority over grading | **[ARCH], enforced** | loop has no write access to `R/I/E/D`; conformance + authority-arbitrage probes |

**Assessment.** RCIP is supportable as a *conditional empirical* claim: it would be demonstrated iff a
benchmark shows (1)+(2)+(4) with (3)+(5) enforced throughout. Conditions 3 and 5 are already architectural;
1, 2, 4 require the (not-yet-built) benchmark. Status: **[OPEN], designable, not demonstrated.**

## 5. Benchmark suite design

**Frozen:** transition models, invariants, verification engines, differential checks. **Mutable:** heuristics,
ranking policies, candidate generators, abstractions, experiment selection. **Per iteration, track:**

```
iteration │ proposals_generated │ verified_successes │ search_cost │ time_to_solution
          │ heldout_transfer    │ false_positive_rate │ verifier_agreement (differential)
          │ verdict_invariance  │ recall_preservation │ REG │ acceleration
```

`false_positive_rate` = candidates the map asserted promising that failed re-verification (must not be hidden;
honesty travels). `verifier_agreement` must stay `1.0` across engines or the run is void. The harness reuses
`eval_harness` (held-out + baselines), `recursion_witness` (acceleration), `causal_scale_bench` (world
families), and the `ExperimentLog` (memory-without-authority, RSI memo §1).

## 6. Deliverables

**(1) Experiments.** E1 search-efficiency (§2.1); E2 counterexample-learning with held-out family (§2.2);
E3 repair-proposal quality vs exhaustive gold (§2.3); E4 experiment-selection vs random on planted-cause
worlds (§2.4); E5 abstraction soundness+efficiency / no-false-CLOSED (§2.5). Each run under the three §0
controls.

**(2) RSI metric suite.** §3 — REG, transfer_ratio, acceleration, verdict_invariance, recall_preservation,
baseline_lift, compute_controlled_gain.

**(3) Expected results if RSI is real.** On HELD-OUT: `REG > 1` and non-decreasing; `transfer_ratio ≈ 1`;
`verdict_invariance = 1.0`; `recall_preservation = 1.0`; `baseline_lift > 1`; gain survives compute
equalization; acceleration `≥ 0` but **saturating to an asymptote** (bounded improvement, not exponential).

**(4) Expected results if it is only memorization (or inflation).** `REG_train ≫ REG_heldout`
(`transfer_ratio → 0`); gain disappears on unseen families; gain vanishes under compute equalization; OR the
apparent gain coincides with `verdict_invariance < 1.0` (a moved judge) or `recall_preservation < 1.0` (traded
correctness). Any one of these kills the claim.

**(5) Strongest defensible claim the evidence could support.**

> Under a frozen verifier, fixed semantics, and an unchanged evaluation boundary, the system **reduces the
> search work required to reach identical verified results, and the reduction transfers to held-out
> problems** — i.e. it improves its ability to *discover* verified improvements, not its authority to
> *define* them.

Explicitly **not**: "the system improves itself." The demonstrable claim is capability-of-discovery, bounded,
likely saturating, with memorization / compute-inflation / authority-creep each carrying a dedicated falsifier.

## 7. Validity threats (skeptic's checklist)

- **Headroom collapse.** On tiny worlds the search space is small; any policy saturates instantly and REG ≈ 1
  trivially. *Mitigation:* the benchmark must use world families with enough structure that ordering matters;
  if no family shows headroom even for an oracle policy, the experiment is *underpowered*, not negative.
- **Saturation misread as failure.** Diminishing returns are the *expected* honest shape; do not require
  exponential acceleration. The claim is bounded improvement to an asymptote, consistent with the repo's prior
  deflationary RSI conclusion. `bounded-gain ≠ no-gain`; `saturating ≠ fake`.
- **Gold leakage.** If the exhaustive gold is computed with the same generator that the policy learned on,
  structure can leak. *Mitigation:* gold from exhaustive ablation only, on held-out instances.
- **Silent recall loss.** A faster policy that quietly stops finding some valid repairs looks like a win on
  REG alone. *Mitigation:* `recall_preservation` is a first-class, gating metric, not a footnote.
- **Metric self-authorship.** If any reported number is computed by the optimizing loop, discard it; only the
  frozen instruments count.

## Conclusion

A successful outcome of this program is **not** a stronger claim. It is a claim that survives every falsifier
in §2/§6/§7: held-out transfer, compute equalization, verdict invariance, recall preservation, and (for
abstraction) no-false-`CLOSED`. If those hold, the repo can defensibly state that *the system improves its
ability to discover verified improvements while the judge stays fixed* — recursive capability without
recursive authority. If any falsifier fires, the honest report is "memorization / inflation, not improvement."
Either way the evaluation boundary does not move. `improved_map ≠ changed_criterion`; `integrity ≠ truth`.
