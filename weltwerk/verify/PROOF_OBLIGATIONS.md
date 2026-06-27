<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Proof Obligations — the ledger

The repository advances by **closing Proof Obligations**, not by adding features. Each obligation is a
specific scientific uncertainty; closing it means an executable artifact now reduces that uncertainty
permanently. Status values: **CLOSED** (artifact exists and its test passes), **ADDRESSED** (artifact
written, pending a run), **OPEN** (not yet built).

Fields per obligation: *Statement · Current evidence · Missing evidence · Required artifact · Verification ·
Falsifier · Difficulty · Priority · Status.*

---

### PO-1 — Approach-B faithfulness
- **Statement**: the direct-SMT engine (`symbolic_engine_b`) equals the explicit engine on its fragment.
- **Current evidence**: `test_symbolic_b.py` (2 worlds) **+ now** `differential_b.py` + `test_differential_b.py`
  (a generated *distribution* of acyclic `{destroy,repair}` worlds).
- **Required artifact**: green `test_symbolic_b` + `differential_b` over generated worlds. **DONE** (z3-gated run).
- **Verification**: same VIOLATED status, shortest length, replayable witness on every world; distribution has
  both violable and clean worlds. **Falsifier**: any disagreeing world. **Scope**: acyclic fragment only —
  cyclic `repair` upstream-self is a *documented boundary* (the two definitions can diverge there).
- **Difficulty**: M · **Priority**: High · **Status**: **CLOSED** (3/3; `differential_b` 32/32 — 22 violable,
  10 clean). Faithful only on the acyclic `{destroy,repair}`/`not_disabled` fragment; still not a
  `CLOSED`-proving engine (needs k-induction).

### PO-2 — Counterfactual accuracy
- **Statement**: trace-level ablation recovers the true critical events vs an independent gold.
- **Current evidence**: `test_counterfactual` (apparatus only). **Missing**: precision/recall vs exhaustive gold.
- **Required artifact**: `cf_quality_bench.py` + `test_cf_quality.py` (exhaustive minimal-removal-set gold).
- **Verification**: precision/recall on single-cause/mixed; honest overdetermined blind-spot; beats random.
- **Falsifier**: a flagged "critical" event whose removal does not clear the violation; or accuracy ≤ random.
- **Difficulty**: L · **Priority**: High · **Status**: **CLOSED** (6/6 — single-cause P=R=1, decoy excluded,
  overdetermined ∅ with gold ≥2, beats expected-random 1.0 > 0.75).

### PO-3 — Repair restore-stability
- **Statement**: `RESTORED_WITHIN_BOUND@K ⇒ restored@2K`.
- **Current evidence**: none. **Missing**: a bound-sweep experiment.
- **Required artifact**: `repair_bound_sweep.py` + `test_repair_bound_sweep.py`. **Verification**: re-verify
  each candidate at 2K; PROVEN must stay restored (bound-monotone), WITHIN_BOUND is measured.
- **Falsifier**: a candidate restored@K but VIOLATED@2K (a *valuable* negative: `restores-(M,E,K) ≠ safe`).
- **Difficulty**: L · **Priority**: M · **Status**: **CLOSED** (5/5). The falsifier FIRES by construction
  (fanout/flip): RESTORED_WITHIN_BOUND@2 → VIOLATED@4, while RESTORED_PROVEN stays restored. The negative is
  the result — it shows the two grades are not interchangeable.

### PO-4 — Engine soundness (not just agreement)
- **Statement**: the engine's verdict equals an independent ground-truth oracle, not only another engine.
- **Current evidence**: `differential` agreement → **now**: `oracle_reference.py` + `test_oracle_conformance.py`.
- **Required artifact**: independent unbounded-fixpoint oracle. **Verification**: no false CLOSED/VIOLATED,
  reachable-set + shortest-length match on tiny worlds.
- **Falsifier**: any engine≠oracle mismatch. **Difficulty**: M · **Priority**: High · **Status**: **CLOSED** (5/5).

### PO-5 — Genuine multi-iteration capability accrual
- **Statement**: held-out work decreases across loop iterations on a *not-one-shot-learnable* task, then saturates.
- **Current evidence**: `rsi_bench_families.py` + `test_rsi_bench_families.py`. The family's restorer label is
  the FROZEN engine's, but XOR-shaped in two observable tags — so a one-shot linear policy *provably* cannot,
  and 4× data does not help, while an iterated additive loop climbs and saturates at the ceiling.
- **Required artifact**: `rsi_bench_families.py` + iterated curve + one-shot/data-scaling controls. **DONE.**
- **Verification**: non-increasing held-out curve dropping ≥1 from k=0 to a saturated ceiling, with both
  controls pinned near chance. **Falsifier (for the bound)**: if the loop ALSO stalls at chance, or if a
  control reaches the ceiling (then the task was one-shot, claim void).
- **Reading (sharpened by PO-6)**: PO-6 showed the *natural* restore task is one-shot (no iteration helps);
  PO-5 shows that *when a task demands it*, the loop delivers bounded, saturating, first-order accrual. Together
  they bound RSI from both sides: real but task-gated and bounded, never open-ended or second-order.
- **Difficulty**: M · **Priority**: High · **Status**: **CLOSED** (6/6 — curve `3.95 → 2.60 → 1.00 → 1.00`
  saturated; one-shot linear and 4×-data pinned at `4.00`, chance ≈ `4.5`).

### PO-6 — Gain is not compute
- **Statement**: REG survives equal search budget.
- **Current evidence**: budget-3 hit-rate in `rsi_bench_scale`. **Missing**: explicit equal-budget A/B + statistic.
- **Required artifact**: `compute_control_bench.py` + `test_compute_control.py` (anytime hit-rate sweep over
  equal budgets B). **Falsifier**: gain vanishes at equal budget (no anytime dominance / no cheap-end gain).
- **Difficulty**: L · **Priority**: M · **Status**: **CLOSED** (5/5 — anytime dominance; 40/40 vs 0 at B=1).
  Claims only equal-budget ordering gain on this world family; not generalization (PO-5), not unbounded (saturates).

### PO-7 — Boundary immutability (mechanize BRIP P4)
- **Statement**: the map cannot alter the judge (engine/semantics/invariant/metric/split).
- **Current evidence**: prose + intent → **now**: `test_boundary_immutability.py`.
- **Required artifact**: verdict-invariant-under-permutation + no-mutation + no-solver-in-map + analysis≠verdict.
- **Falsifier**: a policy permutation flips a verdict; analysis mutates invariants. **Difficulty**: L–M ·
  **Priority**: High · **Status**: **CLOSED** (5/5).

### PO-8 — Certificate independence
- **Statement**: a CLOSED `ReachabilityCertificate` is checkable as a proof, independent of the prover.
- **Current evidence**: `verify()` re-ran the engine → **now**: `certificate_checker.py` + `test_certificate_checker.py`.
- **Required artifact**: no-search closure checker (init∈S, invariants on S, S closed under T).
- **Verification**: valid passes; tamper (drop/inject) fails; no engine import. **Falsifier**: a false cert passes.
- **Difficulty**: M · **Priority**: High · **Status**: **CLOSED** (6/6).

### PO-9 — Honesty-contract universality
- **Statement**: every consumer's `as_analysis()` is honest (scope + ≥1 limitation).
- **Current evidence**: diagnose/counterfactual tested. **Missing**: parametrized conformance incl. repair.
- **Required artifact**: `test_analysis_conformance.py`. **Falsifier**: a consumer emits a limitation-free result.
- **Difficulty**: trivial · **Priority**: M · **Status**: **CLOSED** (6/6). Parametrized over
  diagnose/counterfactual/repair `as_analysis()` + the construction guard (no bypass).

### PO-10 — Abstraction admissibility harness
- **Statement**: any abstraction satisfies `abstract-CLOSED ⇒ exact-CLOSED` (no false CLOSED).
- **Current evidence**: `abstraction_soundness.py` + `test_abstraction_soundness.py` — a reusable harness that
  checks the premise (`admissible`: the abstract over-approximates the existential image) and the conclusion
  (`no_false_closed`), and *catches* an inadmissible abstraction (a dropped bad block) producing a false CLOSED.
- **Required artifact**: `abstraction_soundness.py`. **DONE** (pure-stdlib). **Falsifier**: a false CLOSED.
- **Difficulty**: M · **Priority**: M · **Status**: **CLOSED** (5/5 — unsound abstraction flagged inadmissible
  AND shown to produce a false CLOSED). Gates CEGAR / any future `abstract-CLOSED` engine:
  `admissible ⇒ no_false_closed`, mechanized.

---

### PO-11 — Hot-swap stream preservation (a NEW domain behind the frozen contracts)
- **Statement**: a live program hot-swap (Alpha→Beta) is successful iff the frozen checker returns `CLOSED`
  (no `continuity`/`no_race` violation reachable) with the migration reachable, AND the migration map μ is
  stream-preserving (`π∘μ = π`). `integrity ≠ truth`.
- **Current evidence**: `hotswap/swap_relation.py` (`SwapRelation` + `SwapModelChecker` + independent
  `swap_oracle` + `swap_check_certificate`) + `hotswap/swap_translate.py` (π, μ, the commute check) +
  `test_swap_relation.py` + `test_swap_translate.py`. Reuses `Invariant`/`Trace`/`ReachabilityCertificate`
  and the PO-4/PO-8 patterns unchanged; faithfulness asserted against the independent oracle.
- **Required artifact**: swap domain + oracle agreement + inductive certificate + `π∘μ=π`. **DONE.**
- **Verification**: checker≡oracle (status + shortest + reachable); certificate tamper-rejecting; μ preserves
  π or is caught with a witness. **Falsifier**: a false `CLOSED` swap, or a stream-corrupting μ that passes.
- **Difficulty**: M · **Priority**: M · **Status**: **ADDRESSED** (built; pending run). Bounded: `CLOSED@K`
  is over the swap alphabet + bound; stream discretized to {intact,broken} (Arbitrary-Boundary Law).

### PO-12 — Hot-swap ordering as bounded search-acceleration
- **Statement**: a candidate-ranking policy over swap plans reaches a *successful* plan with less verified
  work at EQUAL budget, where success is the frozen `CLOSED ∧ migrated` verdict — never the policy's claim.
  `improved_map ≠ changed_criterion`; `candidate ≠ deployed-swap`.
- **Current evidence**: `hotswap/swap_rank.py` (useful-guard features measured by the frozen evaluator;
  canonical vs learned ordering; `work()`; equal-budget curve; `as_analysis()` honesty projection) +
  `hotswap/swap_falsifier.py` (deferred-race flip@2K + race@1 + overdetermined) + `test_swap_rank.py` +
  `test_swap_falsifier.py`.
- **Required artifact**: equal-budget anytime dominance + overdetermined safe plan + flip@2K falsifier. **DONE.**
- **Verification**: learned work < canonical, anytime dominance; greedy VIOLATED@2K (flip) and @1 (race);
  only `{MBB,ALIGN}` succeeds; no false restore. **Falsifier**: gain vanishes at equal budget, or a greedy
  shortcut is *not* punished.
- **Difficulty**: M · **Priority**: M · **Status**: **ADDRESSED** (built; pending run). One-shot signal ⇒
  bounded gain (the PO-5/PO-6 pattern), not open-ended.

---

## Progress

CLOSED: **PO-1 … PO-10 — all ten, run-green.** ADDRESSED (built, pending run): **PO-11, PO-12** (the hot-swap
extension). OPEN: **none.**

The core scientific arc stays closed (RSI bounded both sides, PO-5/PO-6). The hot-swap work is a NEW domain
that **re-opens the evidence graph** (per the standing rule): it plugs in behind the frozen engine, grading,
certificate, oracle pattern, and honesty contract — adding semantics, not authority — and carries its own
built-in falsifier (deferred-race flip@2K, race@1, overdetermined safe plan). `engine ≠ semantics`. See
[`EVIDENCE_GRAPH.md`](EVIDENCE_GRAPH.md) and [`hotswap/README.md`](hotswap/README.md).
