<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# hotswap/ — live program hot-swapping as a verified, bounded search problem (PO-11 / PO-12)

This extension models **hot-swapping a running target** (Program Alpha → Program Beta) while a **data stream
must stay uncorrupted**, and treats the swap as an *optimization action sequence* judged by the **frozen**
Ursprung verification contracts. It adds **semantics, not authority**: nothing here modifies the engine, the
`CLOSED/BOUNDED/VIOLATED` grading, the certificate checker, the oracle pattern, or the honesty contract — those
judge the swap. `engine ≠ semantics`; `integrity ≠ truth`; `improved_map ≠ changed_criterion`.

## What is frozen vs. what is added

Frozen (reused unchanged): `artifacts.Invariant / Trace / ReachabilityCertificate / AnalysisResult`, the
explicit-state grading semantics, the PO-4 oracle pattern, the PO-8 inductive-certificate closure check, the
PO-7 boundary-immutability discipline, and the PO-9 honesty contract.

Added (this folder): a small **swap transition system** the frozen machinery checks, plus a candidate-ranking
policy and a built-in falsifier. A dedicated relation is necessary (a recorded fork): the existing
`{destroy,repair}` cascade cannot express make-before-break redundancy or buffered stream gaps.

## The model (finite by construction — Arbitrary-Boundary Law)

A `SwapView` is `(active, migrated, aligned, buffer, broken)`. Absolute stream offsets are unbounded, so
continuity is **latched** to a boolean (`broken`) computed per transition; the stream is discretized to
`{intact, broken}`. The view *is* the state signature (bijective), so a certificate's state set is directly
re-checkable. Two **frozen invariants**:

- `continuity := ¬broken` — the stream is never starved (no skip/gap has occurred).
- `no_race := ¬(active=="both" ∧ ¬aligned)` — no two-writer state without an aligned migration pointer.

A **plan** is a set of guards (transition restrictions). It cannot touch the invariants or the grading; it
only forbids transitions — the candidate-ranking surface.

## Layer 1 — stream invariant + certificate (PO-11)

`swap_relation.py` — `SwapRelation` (guards), `SwapModelChecker` (BFS → `CLOSED/BOUNDED/VIOLATED` + a swap-native
`Trace` + `ReachabilityCertificate`), an independent unbounded-fixpoint `swap_oracle` (PO-4), and
`swap_check_certificate` (PO-8 closure: `init∈S ∧ invariants hold on S ∧ S closed under T ⇒ reachable ⊆ S`).

`swap_translate.py` — the state-translation proof: the migration map `μ: State_α → State_β` is correct iff it
**commutes with the stream projection** `π∘μ = π` on every reachable α-state (PO-10 admissibility reused with
π as the preserved property). Non-stream state may be re-laid-out; a stream-corrupting μ is caught with a
witness, never passed as a false restore. `refinement ≠ identity`.

## Layer 2 — candidate-ranking swap policy (PO-12)

`swap_rank.py` — a swap **succeeds** iff the frozen checker returns `CLOSED` (no violation reachable) **and**
the migration is reachable. Success is the engine's verdict, never the policy's. Verified work `w(π, W)` =
re-verifications until a successful plan is found (the `rsi_bench` `work()` metric). A learned ordering (rank
plans by guards the frozen evaluator shows REMOVE a violation) reaches success with less work at **equal
budget** than canonical — the gain is *ordering*, not compute (PO-6). One-shot signal ⇒ bounded gain.

## Layer 3 — adversarial control / falsifier (PO-12)

`swap_falsifier.py` — two failure modes at two depths so a greedy "minimize downtime" policy is punished:

- **Deferred-race flip (PO-3 analogue):** dropping alpha early (`{ALIGN}` only) opens an `active="none"`
  window; the primed buffer masks it at bound `K=2` (looks safe) but underflows at `2K=4` → `continuity`
  VIOLATED. `swap-CLOSED@K ≠ safe`.
- **Race trap:** activating beta unaligned (`{MBB}` only) hits `active="both" ∧ ¬aligned` → `no_race` VIOLATED
  at depth 1.

Neither single guard suffices (independent failure modes) — only the **overdetermined** `{MBB, ALIGN}` is
CLOSED with the migration reachable. `restores-(M,E,K) ≠ safe`.

## `AnalysisResult` schema for a swap proposal

`swap_rank.as_analysis(plan)` projects into the shared honesty contract (scope + ≥1 limitation; PO-9):

```
AnalysisResult(
  source_trace = ("ALIGN","MBB"),            # the plan
  scope        = "bounded-swap",
  findings     = [ SWAP_PLAN(status, goal, success), DOWNTIME(steps_to_migrated),
                   CERTIFICATE(inductive_check via PO-8) ],
  limitations  = [ "CLOSED@K is over the swap alphabet + bound; deeper deferred races UNDERDETERMINED",
                   "stream discretized to {intact,broken}; offsets abstracted — holds-here ≠ true",
                   "a plan OBSERVED safe under (checker,bound); candidate ≠ deployed-swap" ],
)
```

## Files & run

| File | Role |
|---|---|
| `swap_relation.py` | swap domain: `SwapRelation`, `SwapModelChecker`, `swap_oracle`, `swap_check_certificate` (PO-11) |
| `swap_translate.py` | stream projection π, migration μ, `stream_preserving` (`π∘μ=π`) (PO-11) |
| `swap_rank.py` | candidate-ranking policy, `work()`, equal-budget, `as_analysis()` (PO-12) |
| `swap_falsifier.py` | deferred-race flip@2K, race@1, overdetermined (PO-12) |
| `test_swap_relation.py` · `test_swap_translate.py` · `test_swap_rank.py` · `test_swap_falsifier.py` | proofs (validity-not-outcome) |

```powershell
cd "weltwerk\verify\hotswap"; python test_swap_relation.py; python test_swap_translate.py; python test_swap_rank.py; python test_swap_falsifier.py
```

Pure-stdlib; no solver required. Every claim is `MEASURED` only once its suite is green — until then the rows in
[`../PROOF_OBLIGATIONS.md`](../PROOF_OBLIGATIONS.md) read **ADDRESSED (pending run)**.
