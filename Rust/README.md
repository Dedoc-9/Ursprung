<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Rust/ — Ursprung fundamentals in Rust

A faithful, dependency-free Rust port of the Ursprung / `weltwerk/verify` epistemic core — the honesty
contract, the epistemic type `Grounded<T>`, the graded claim ledger, the frontier gate, the residual-channel
diagnostic, and the **Epistemic Runtime Orchestrator** (the two chokepoints). It is `std`-only with **zero
dependencies**, mirroring the Python core's pure-stdlib discipline. AGPL-3.0-only.

## Why a Rust port — two invariants become type-level

The Python enforces the discipline at runtime; Rust lets two of the load-bearing invariants be enforced by
the compiler and the type system instead:

1. **The honesty contract is a constructor invariant.** `AnalysisResult::new` returns `Result<_, HonestyError>`
   and refuses an empty scope or zero limitations. A dishonest answer is *unconstructable* — so the
   orchestrator's "answer chokepoint" needs no runtime re-check. `analysis ≠ proof`.
2. **The action chokepoint is a type.** `Grounded<T>` holds its value in a **private** field; the only
   constructor refuses unless a `Grounding` proof `is_grounded()`. Possessing a `Grounded<T>` *is* the witness
   that `T` was verified — you cannot fabricate one. `enact` runs an action only behind that gate.
   `grounded ≠ true`.

A third nicety: `Grade` is an `enum`, so an off-ladder grade is **unrepresentable** (the Python ladder is a
string set checked at runtime).

## Module map (mirrors the Python)

| Rust | Python original | role |
|------|-----------------|------|
| `src/artifacts.rs` | `artifacts.py` | `AnalysisResult` / `Finding` / `Limitation`, honesty enforced at construction |
| `src/epistemic_types.rs` | `epistemic_types.py` | `Grounding`, `Grounded<T>`, `enact`, `Attested` |
| `src/claim_ledger.rs` | `claim_ledger.py` | `Grade` enum, `Claim`, `audit_ledger`, `SupportedClaim` |
| `src/frontier_gate.rs` | `frontier_gate.py` | SUPER/SUB/NEAR → EXPLOIT/PIVOT/HOLD |
| `src/residual_channel.rs` | `residual_channel.py` | confounder-conditioned CMI + within-Z shuffle null + mis-spec stress (deterministic LCG) |
| `src/orchestrator.rs` | `orchestrator.py` | `EpistemicTool`, `Orchestrator`, `panel` (no scalar), `enact` |

## Run

```powershell
cd "C:\Users\dillb_lzxy763\Claude\Projects\Ursprung\Rust"
cargo test            # unit tests (each module) + tests/chokepoints.rs integration
cargo run --example chokepoints
```

`cargo test` exercises: the honesty contract refuses dishonest results; the `Grounded`/`enact` gate runs an
action only when grounded and refuses atomically otherwise; the residual-channel audit separates a planted
null from a planted channel; the frontier gate classifies regimes; the ledger refuses a claim missing its
boundary; and the orchestrator's two chokepoints hold end to end.

## Boundaries (load-bearing)

This is the *fundamentals* layer — the honesty substrate and router, not a verifier. `router ≠ verifier`;
`composition ≠ capability`; `residual-CMI ≠ channel` (a residual is a candidate until mis-specification-stable);
`proves-the-procedure ≠ proves-the-phenomenon`. The residual-channel estimators are discrete (callers
discretize their own data); the LCG is for *reproducibility*, not cryptographic randomness — `integrity ≠ truth`.

## Parity note

This port reproduces the *structure and decisions* of the Python core, not bit-identical floating-point values
(different RNG, different float evaluation order). Decisions (CONSISTENT_WITH_NULL / RESIDUAL_* etc.) are the
invariant; exact CMI magnitudes are not. `reproducible-within-impl ≠ identical-across-impls`.
