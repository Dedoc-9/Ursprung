<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Evidence Graph

Every scientific claim should trace to executable evidence. This graph maps each claim to its supporting
artifact, the test/experiment that exercises it, and **where the support chain terminates**. A chain that
ends in `✓ executable` is backed by a passing test; a chain marked `⚠` terminates in intuition, agreement,
a prover re-run, apparatus-only, or a null — each such ⚠ is tracked as a Proof Obligation in
[`PROOF_OBLIGATIONS.md`](PROOF_OBLIGATIONS.md).

```
CLAIM                                   → ARTIFACT                 → TEST / EXPERIMENT             → TERMINATES IN
engine-independent verdict              → differential.py          → test_differential 5/5         → agreement, AND
engine == ground truth (soundness)      → oracle_reference.py       → test_oracle_conformance 5/5   → ✓ executable  (PO-4 CLOSED)
verdict semantics CLOSED/BOUNDED/VIO    → engine.py / kernel_check  → test_kernel_check 8/8         → ✓ executable
CLOSED is an auditable proof            → certificate_checker.py    → test_certificate_checker 6/6  → ✓ executable  (PO-8 CLOSED)
witness is real                         → Trace + replay_path       → witness-replay tests          → ✓ executable
analysis is honest (per consumer)       → AnalysisResult contract   → test_analysis_contract 8/8    → ✓ executable
analysis honest (ALL consumers)         → diagnose/cf/repair        → test_analysis_conformance     → ✓ executable (PO-9 ADDRESSED)
map cannot move the judge               → (no map→territory path)   → test_boundary_immutability 5/5→ ✓ executable  (PO-7 CLOSED)
diagnosis identifies cause              → diagnose.py               → test_diagnose 8/8             → apparatus (accuracy: PO-2 CLOSED)
counterfactual accuracy                 → cf_quality_bench.py       → test_cf_quality 6/6           → ✓ executable (PO-2 CLOSED)
repair restores world (bounded)         → repair.py                 → test_repair 8/8               → bounded; grade-stability PO-3
repair grade-stability (K vs 2K)        → repair_bound_sweep.py     → test_repair_bound_sweep      → ✓ executable (PO-3 ADDRESSED)
capability ≠ lookup                     → rsi_bench_scale.py        → test_rsi_bench_scale          → ✓ executable (single-task)
REG not explained by compute            → compute_control_bench.py  → test_compute_control        → ✓ executable (PO-6 ADDRESSED)
natural task is one-shot                → compute_control_bench.py  → test_compute_control         → ✓ executable (PO-6: B=1 ceiling)
iterated accrual (bounded, saturating)  → rsi_bench_families.py     → test_rsi_bench_families      → ✓ executable (PO-5 ADDRESSED)
Approach-B engine faithful              → symbolic_engine_b.py      → test_symbolic_b (UNRUN)       → nothing ⚠ (PO-1)
abstraction never false-CLOSED          → (none yet)                → —                             → prose ⚠ (PO-10)
inflation vs search separable           → no_inflation_latch, ...   → repo tests (not re-verified) → executable (unverified here)
```

## Chains resolved since the last review

- `differential → agreement` **→ resolved** by `oracle_reference` (PO-4): the chain now ends in
  *agreement with an independent ground truth*, not mere inter-engine agreement.
- `certificate → prover re-run` **→ resolved** by `certificate_checker` (PO-8): the chain now ends in an
  *independent, no-search closure check*.
- `BRIP/RCPT premise → prose` **→ resolved** by `test_boundary_immutability` (PO-7): the premise is an
  executed invariant.
- `counterfactual accuracy → apparatus` **→ resolved** by `cf_quality_bench` (PO-2): accuracy is now measured
  against an *independent exhaustive gold*, not just shown well-formed.
- `repair restored → bounded` **→ addressed** by `repair_bound_sweep` (PO-3): the chain now distinguishes a
  bound-monotone PROVEN grade from a WITHIN_BOUND grade that is *shown to flip* — `restores-(M,E,K) ≠ safe`.
- `REG-not-compute → informal` **→ addressed** by `compute_control_bench` (PO-6): equal-budget anytime dominance.
- `honesty universality → one consumer` **→ addressed** by `test_analysis_conformance` (PO-9): all three
  consumers routed through the contract + a no-bypass guard.

- `recursive accrual → null/saturates` **→ addressed** by `rsi_bench_families` (PO-5): on a not-one-shot (XOR)
  task with a frozen engine label, an iterated loop climbs and *saturates*, while one-shot linear + 4× data
  stay at chance. Bounded, task-gated accrual — paired with PO-6 it bounds RSI from both sides.

## Remaining ⚠ chains (open Proof Obligations)

`Approach-B faithful` (PO-1, unrun), `abstraction no-false-CLOSED` (PO-10, prose). PO-3/PO-5/PO-6/PO-9 are
ADDRESSED pending a green run; PO-2/PO-4/PO-7/PO-8 are CLOSED. The scientific claims are bounded; PO-1/PO-10
are engine-faithfulness plumbing.

**Rule of advancement**: no claim tagged `[DEMONSTRATED]` in the README may rest on a ⚠ chain. When a chain
resolves, update both this graph and `PROOF_OBLIGATIONS.md`; the pair is the repository's self-audit.
