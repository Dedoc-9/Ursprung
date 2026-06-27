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
analysis is honest                      → AnalysisResult contract   → test_analysis_contract 8/8    → ✓ executable  (universality ⚠ PO-9)
map cannot move the judge               → (no map→territory path)   → test_boundary_immutability 5/5→ ✓ executable  (PO-7 CLOSED)
diagnosis identifies cause              → diagnose.py               → test_diagnose 8/8             → apparatus ⚠ (accuracy: PO-2 ADDRESSED)
counterfactual critical set             → counterfactual.py         → test_counterfactual 8/8       → apparatus ⚠ (accuracy: PO-2 ADDRESSED)
repair restores world (bounded)         → repair.py                 → test_repair 8/8               → bounded ⚠ (stability: PO-3)
capability ≠ lookup                     → rsi_bench_scale.py        → test_rsi_bench_scale          → ✓ executable (single-task)
REG not explained by compute            → rsi_bench_scale budget    → (informal)                   → weak ⚠ (PO-6)
recursive accrual (multi-iteration)     → rsi_bench_scale curve     → (saturates)                  → null ⚠ (PO-5)
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

## Remaining ⚠ chains (open Proof Obligations)

`diagnosis/counterfactual accuracy` (PO-2, addressed), `repair stability` (PO-3), `REG-not-compute` (PO-6),
`recursive accrual` (PO-5), `Approach-B faithful` (PO-1), `abstraction no-false-CLOSED` (PO-10),
`honesty universality` (PO-9).

**Rule of advancement**: no claim tagged `[DEMONSTRATED]` in the README may rest on a ⚠ chain. When a chain
resolves, update both this graph and `PROOF_OBLIGATIONS.md`; the pair is the repository's self-audit.
