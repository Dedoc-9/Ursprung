<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Rust/ — Ursprung fundamentals + the `ursprung-gateway` binary

A dependency-free (`std`-only) Rust crate: the Ursprung / `weltwerk/verify` epistemic core, the Rust ports of
the DVSM audit layers, and the **`ursprung-gateway`** single binary that composes them into a fail-closed
integrity gate. AGPL-3.0-only. Mirrors the Python core's pure-stdlib discipline — **zero dependencies**.

Status: `cargo test` green (56 tests across the suites below) and `cargo build --bin ursprung-gateway` builds.
Parity with the Python is of *decisions*, not bit-identical floats (`reproducible-within-impl ≠ identical-across-impls`).

## Why a Rust port — two invariants become type-level

The Python enforces the discipline at runtime; Rust lets two load-bearing invariants be enforced by the type
system instead:

1. **The honesty contract is a constructor invariant.** `AnalysisResult::new` returns `Result<_, HonestyError>`
   and refuses an empty scope or zero limitations — a dishonest answer is *unconstructable*. `analysis ≠ proof`.
2. **The action chokepoint is a type.** `Grounded<T>` holds its value in a **private** field; the only
   constructor refuses unless a `Grounding` proof `is_grounded()`. Possessing one *is* the witness. `grounded ≠ true`.

A third nicety: `Grade` is an `enum`, so an off-ladder grade is **unrepresentable**.

## Module map

**Fundamentals** (mirror `weltwerk/verify`):

| Rust | role |
|------|------|
| `src/artifacts.rs` | `AnalysisResult` / `Finding` / `Limitation` — honesty enforced at construction |
| `src/epistemic_types.rs` | `Grounding`, `Grounded<T>`, `enact`, `Attested` |
| `src/claim_ledger.rs` | `Grade` enum, `Claim`, `audit_ledger`, `SupportedClaim` |
| `src/frontier_gate.rs` | SUPER/SUB/NEAR → EXPLOIT/PIVOT/HOLD |
| `src/residual_channel.rs` | confounder-conditioned CMI + within-Z shuffle null + mis-spec stress (deterministic LCG) |
| `src/orchestrator.rs` | `EpistemicTool`, `Orchestrator`, `panel` (no scalar), `enact` — two chokepoints, no new authority |

**DVSM audit layers** (the gateway's L1/L3/L4; differential-tested against the Python):

| Rust | role |
|------|------|
| `src/coupling_audit.rs` | forbidden-coupling taxonomy (AIR_GAP_HELD / OBSERVER_CONTAMINATION / CONFOUNDED_ARTIFACT / UNIDENTIFIABLE) on the residual core; wired into the orchestrator as `CouplingTool` |
| `src/binframe_adapter.rs` | **L1** — BinaryFrame parser (`parse_frames` + `ParseReport`, two anomalies: layout-mismatch, non-finite) + obligation `lift()` (containment / replay-parity, and honest non-liftable air-gaps) |
| `src/invariant_ledger.rs` | `ObligationStatus` (CLOSED/BOUNDED/VIOLATED/REJECTED_AS_PROOF/UNDERDETERMINED — five, no OPEN) + `ObligationResult` (`as_analysis`/`as_claim`) |
| `src/commercial_obligations.rs` | **L4** — the proof-gated claims ledger over a single-source manifest; `audit()` (static) + `audit_live(receipts)` (Obligation B, Rust-side live receipt) |
| `src/gateway.rs` | `run_gateway()` + `render_report()` — composes L1 ingest+lift → L4 proof-gate into a fail-closed `GatewayReport` |

**Single source of truth.** `commercial_obligations.rs` loads the SAME `DVSM/commercial/ledger.tsv` +
`obligations.tsv` the Python reads, via `include_str!` — edit the manifest, both languages follow
(`mirror ≠ source` closed by construction).

## The binary

```powershell
cd Rust
cargo build --bin ursprung-gateway
./target/debug/ursprung-gateway --telemetry <dump.bin> [--schema telem|abi] [--receipt .verify_receipt.tsv] `
                                [--u-max 100.0] [--header-lines 1] [--output gate_report.md] [--strict]
```

It ingests a BinaryFrame dump → lifts graded obligations → runs the proof-gated ledger (live-bound when
`--receipt` is given) → writes a disclaimer-first report → exits **0** only if parse is clean, no obligation
is VIOLATED, and the ledger is honest; otherwise non-zero (fail-closed).

**Honest scope (`parts ≠ whole`).** The binary covers the *frame-drivable* path (L1 + L4). It does **not** run
L2 (the contraction certifier) or L3 (the CMI firewall) from a frame dump — those need typed inputs (κ
matrices; `(X,Y,Z)` samples) a public frame doesn't carry, which is exactly why the Ω→V / ν→λ air-gaps come
back **non-liftable**. They remain library APIs. The verdict is a checkable **commitment**, not a signature,
and never a certification of model safety.

## Run the tests

```powershell
cd Rust
cargo test            # 56: module units + chokepoints + binframe + lift + coupling + commercial_gate + differential_residual + gateway
cargo run --example chokepoints
```

Integration suites (`tests/`): `chokepoints` (the two chokepoints hold), `differential_residual` (Rust CMI ==
Python on packed fixtures — value+decision parity), `coupling` (the four verdicts), `commercial_gate` (the
proof-gate + manifest load), `binframe` (parse parity + anomalies), `lift` (obligation verdicts), `gateway`
(end-to-end gate logic). Tests assert the *apparatus* (validity-not-outcome), never a hoped result.

## Boundaries (load-bearing)

`router ≠ verifier`; `composition ≠ capability`; `residual-CMI ≠ channel`; `proves-the-procedure ≠
proves-the-phenomenon`; `receipt ≠ proof` (the live gate proves a suite ran+passed in this build, not that it
is correct); `parts ≠ whole`; `integrity ≠ truth`. The LCG is for reproducibility, not cryptographic
randomness. Parity with the Python is structural (decisions), not bit-identical floats.
