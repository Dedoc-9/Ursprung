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
- **Current evidence**: `test_symbolic_b.py` written. **Missing**: a passing run + extension to a world distribution.
- **Required artifact**: green `test_symbolic_b` (+ a `differential_b` over generated worlds).
- **Verification**: same VIOLATED status, shortest length, replayable witness. **Falsifier**: any disagreeing world.
- **Difficulty**: M · **Priority**: High · **Status**: **OPEN** (CANDIDATE engine, unverified).

### PO-2 — Counterfactual accuracy
- **Statement**: trace-level ablation recovers the true critical events vs an independent gold.
- **Current evidence**: `test_counterfactual` (apparatus only). **Missing**: precision/recall vs exhaustive gold.
- **Required artifact**: `cf_quality_bench.py` + `test_cf_quality.py` (exhaustive minimal-removal-set gold).
- **Verification**: precision/recall on single-cause/mixed; honest overdetermined blind-spot; beats random.
- **Falsifier**: a flagged "critical" event whose removal does not clear the violation; or accuracy ≤ random.
- **Difficulty**: L · **Priority**: High · **Status**: **ADDRESSED** (built; pending run).

### PO-3 — Repair restore-stability
- **Statement**: `RESTORED_WITHIN_BOUND@K ⇒ restored@2K`.
- **Current evidence**: none. **Missing**: a bound-sweep experiment.
- **Required artifact**: `repair_bound_sweep.py`. **Verification**: re-verify each candidate at 2K.
- **Falsifier**: a candidate restored@K but VIOLATED@2K (a *valuable* negative: `restores-(M,E,K) ≠ safe`).
- **Difficulty**: L · **Priority**: M · **Status**: **OPEN**.

### PO-4 — Engine soundness (not just agreement)
- **Statement**: the engine's verdict equals an independent ground-truth oracle, not only another engine.
- **Current evidence**: `differential` agreement → **now**: `oracle_reference.py` + `test_oracle_conformance.py`.
- **Required artifact**: independent unbounded-fixpoint oracle. **Verification**: no false CLOSED/VIOLATED,
  reachable-set + shortest-length match on tiny worlds.
- **Falsifier**: any engine≠oracle mismatch. **Difficulty**: M · **Priority**: High · **Status**: **CLOSED** (5/5).

### PO-5 — Genuine multi-iteration capability accrual
- **Statement**: held-out work decreases across loop iterations on a *not-one-shot-learnable* task.
- **Current evidence**: `rsi_bench_scale` curve **saturates at k=1**. **Missing**: a multi-family generator.
- **Required artifact**: `rsi_bench_families.py` + iterated curve.
- **Verification**: non-trivial-then-saturating held-out REG curve. **Falsifier**: saturates at k=1 anyway
  (a publishable negative — bounds RSI intrinsically). **Difficulty**: M · **Priority**: High · **Status**: **OPEN**.

### PO-6 — Gain is not compute
- **Statement**: REG survives equal search budget.
- **Current evidence**: budget-3 hit-rate in `rsi_bench_scale`. **Missing**: explicit equal-budget A/B + statistic.
- **Required artifact**: `compute_control_bench.py`. **Falsifier**: gain vanishes at equal budget.
- **Difficulty**: L · **Priority**: M · **Status**: **OPEN**.

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
- **Difficulty**: trivial · **Priority**: M · **Status**: **OPEN**.

### PO-10 — Abstraction admissibility harness
- **Statement**: any abstraction satisfies `abstract-CLOSED ⇒ exact-CLOSED` (no false CLOSED).
- **Current evidence**: stated in `RECURSIVE_IMPROVEMENT_PROOF.md §9.7`. **Missing**: a reusable harness.
- **Required artifact**: `abstraction_soundness.py`. **Falsifier**: a false CLOSED.
- **Difficulty**: M · **Priority**: M · **Status**: **OPEN** (gates CEGAR / Approach-B `CLOSED`).

---

## Progress

CLOSED: **PO-4, PO-7, PO-8** (3/10). ADDRESSED: **PO-2**. OPEN: PO-1, PO-3, PO-5, PO-6, PO-9, PO-10.

Closing order recommended next: **PO-2** (run) → **PO-6**, **PO-9** (low effort) → **PO-5** (the
saturation-ceiling experiment, highest scientific value) → **PO-1/PO-10** (gate the symbolic/abstraction
path). See [`EVIDENCE_GRAPH.md`](EVIDENCE_GRAPH.md) for which claims each obligation supports.
