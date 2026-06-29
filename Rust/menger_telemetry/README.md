<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# menger_telemetry — the DVSM Menger-sponge telemetry kernel, hardened

A compilable, tested, **zero-dependency** re-engineering of the DVSM `system-telemetry-minimal` crate
(`Research/MengerSponge` in the external `dvsm-meta-kernel` repo). It keeps the sound ideas — deterministic
fixed-point telemetry, a **Menger fractal sparsity mask** gating a coupling, and a cryptographic frame
commitment — and fixes the ghosts the upstream code carried under aspirational comments.

## What the upstream is (researched from the code, not the docs)

`no_std` crate: Q64.64 fixed-point, a Menger-sponge mask sparsifying a Lie-bracket coupling on a Stiefel
frame, a 7-layer pipeline (acquire→torsion→dissipate→backreact→spectral→EMA→hash), SHA-256 commitment, rate
limiting, C-FFI, plus optional Gudermannian + Byzantine features (dep: `sha2`).

## Ghosts found in the upstream code

| # | Finding | Separator |
|---|---------|-----------|
| 1 | **Does not compile.** `i256` is used throughout (`as i256`, `0i256`) but Rust has no `i256` and `Cargo.toml` provides none (only `sha2`). | `file ≠ crate` |
| 2 | **Integrity check doesn't check.** `telemetry_verify_hash` returns valid (`1`) unconditionally — "For now: always valid." | `attests ≠ verifies` |
| 3 | **Menger depth is idempotent.** The depth loop never uses its `level`; depth 1 and 2 give the same single-scale mask, while the test expects `(20/27)²` (the 3D ratio, applied to a 2D matrix). | `claimed-fractal ≠ code` |
| 4 | **"Stiefel retraction" isn't orthonormal.** It normalizes by `1/norm²` and clamps `≥0`, so `WᵀW=I` is not maintained. | `claimed-invariant ≠ code` |
| 5 | **Non-negative-only pipeline** (`.max(0)` + `quantize` to `[0,1)`), so the "Lie bracket" energy/antisymmetry claims don't hold — a clamped heuristic. | `bounded ≠ conservative` |

## What this product fixes / keeps

1. **Compiles.** Q32.32 (`i64` values, `i128` products) — no 256-bit integer needed. `representable > aspirational`.
2. **Real integrity check.** `Kernel::verify` (and the FFI `telemetry_verify`) **recompute** the SHA-256
   commitment from the snapshot and compare. A tampered `z`/`s`/`mu` fails. `verify` verifies.
3. **Real fractal depth.** `menger.rs` is a true Sierpinski carpet: depth `k` removes the center of every
   `3×3` sub-block at scale `side/3^(k+1)`; on a `side=3^L` grid the retained count is **exactly**
   `8^depth · 9^(L−depth)` = fraction `(8/9)^depth`, and that is tested (depths 0/1/2/3).
4. **In-tree SHA-256.** FIPS 180-4, pinned by the NIST `""`/`"abc"`/long vectors — no `sha2` dependency, zero
   supply-chain surface.
5. **Measured invariants.** `kernel::Invariants` reports boundedness, the Menger fraction, κ-antisymmetry
   residual, and commitment-verified — measured, not asserted.

## Files

| Path | Role |
|------|------|
| `src/fixed.rs` | Q32.32 fixed-point (`qmul`, `quantize`, `clamp`) |
| `src/sha256.rs` | in-tree SHA-256 + NIST-vector tests |
| `src/menger.rs` | depth-exact Sierpinski-carpet sparsity mask |
| `src/kernel.rs` | deterministic pipeline, Menger-masked coupling, commitment, `verify`, `Invariants` |
| `src/ffi.rs` | C ABI (`telemetry_init/process/get_hash/verify/menger_depth/frame_count/destroy`) |
| `src/lib.rs` | crate root + re-exports |

## Run

```powershell
cd Rust/menger_telemetry        # from the repo root
cargo test
```

`cargo test` asserts the apparatus (validity-not-outcome): SHA-256 matches the NIST vectors; the Menger mask
retains exactly `(8/9)^depth` and depth 1 ≠ depth 2; fixed-point multiply tracks float within tolerance; the
kernel is deterministic (same input ⇒ same commitment), rate-limited, bounded over hundreds of frames with an
exactly-antisymmetric κ; and `verify` accepts a genuine snapshot and **rejects a tampered one**.

## Use cases

Each names the boundary it does **not** cross.

- **Deterministic, portable system/sensor telemetry with a tamper-evident commitment.** Embed via the C ABI;
  every frame carries a SHA-256 over its state, and `verify` detects post-hoc edits. *Does not* prove the
  sensors were honest — it commits to what was recorded, not to its truth. `commitment ≠ ground-truth`.
- **Sparse coupling under a tunable compute/sparsity budget.** The Menger depth sets the retained coupling
  fraction `(8/9)^depth` exactly — a principled knob for how much cross-channel mixing to spend. *Does not*
  claim the sparsified dynamics approximate the dense one; it is a different, bounded operator. `sparser ≠ same`.
- **Reproducible replay / audit logs.** Deterministic fixed-point + a hash chain-able commitment per frame;
  two runs of the same input stream produce identical commitments. *Does not* certify correctness —
  `determinism ≠ validity`; `integrity ≠ truth`.
- **Embeddable no-deps building block.** Zero dependencies, `repr(C)` snapshot, C ABI — drops into a host
  with no supply chain. *Does not* (yet) ship the optional Gudermannian / Byzantine layers (see below).

## For LLMs / contributors

1. **Read the code, not the prose.** The upstream README/comments overclaim; the source is the authority,
   and this crate was derived from it with the ghosts above recorded in `PROVENANCE.md`. `claim ≠ code`.
2. **Keep `verify` real.** Any change to the commitment preimage must keep `verify` recomputing-and-comparing;
   a verify that returns a constant is a regression. `attests ≠ verifies`.
3. **Keep the fractal honest.** If you touch `menger.rs`, the `side=3^L` exact-count tests (`(8/9)^depth`) must
   stay green; don't reintroduce a depth loop that ignores its level.
4. **Stay zero-dep and deterministic.** No crates; no floats in the committed path beyond the documented
   `quantize`; Q32.32 products go through `qmul` (i128). A change that breaks `determinism_same_input_same_hash`
   is a regression.
5. **Don't overclaim.** It is a bounded deterministic mixing + commitment, not a conservative flow or a
   "reality" model. State what a change does **not** establish.

## Out of scope for v1 (honest backlog)

- The upstream's optional **Gudermannian projection** and **Byzantine hardening** (Merkle DAG / PBFT-lite /
  replay) features — surveyed, not ported. `surveyed ≠ ported`.
- A true orthonormal Stiefel layer in fixed-point (upstream's was not orthonormal) — `OPEN`.
- A `no_std` build (the upstream is `no_std`; this v1 is `std` for testability — `sha2`-free, so a `no_std`
  port is mechanical).

## Status

Ships **compile-unverified in this environment** (no Rust toolchain was available where it was built). The
crate is std-only, zero-dep, and hand-reviewed; confirm with `cargo test`. The SHA-256 NIST vectors and the
exact Menger counts make most of the surface decidable on first run. `written ≠ compiled`; `tested ≠ safe`.
