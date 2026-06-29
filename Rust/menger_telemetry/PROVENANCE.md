<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# PROVENANCE — menger_telemetry

## Source

Derived from `github.com/Dedoc-9/dvsm-meta-kernel`, folder `Research/MengerSponge`
(crate `system-telemetry-minimal`), reviewed at `main`. Files read from source (code is authoritative):
`lib.rs`, `Cargo.toml`, `KERNEL.rs`, `BINARY_API.rs`. The docs (`Documentation/*.md`, `L4_TORSION_LAYER.md`)
and the optional layers (`GUDERMANNIAN_PROJECTION.rs`, `BYZANTINE_HARDENING.rs`, `TEST_SUITE.rs`) were
surveyed via the file tree and `lib.rs` exports, not ported. `surveyed ≠ ported`.

## Findings on the source (from the code)

1. **Non-compiling `i256`.** `KERNEL.rs` uses `as i256`, `0i256`, `1i256` for Q64.64 products. Rust has no
   `i256`; `Cargo.toml` lists only `sha2`. The crate does not build as written. `file ≠ crate`.
2. **`telemetry_verify_hash` always returns `1`** ("For now: always valid") — an integrity check that never
   checks. `attests ≠ verifies`.
3. **Idempotent Menger depth.** `menger_mask_generate` loops `for level in 1..=depth` but the body ignores
   `level`, so depth 1 and 2 yield the same single-scale mask. `test_menger_sparsity` expects `(20/27)²` — the
   3D sponge ratio — applied to a 2D `DIM×DIM` matrix whose removal pattern actually keeps 4/9. The claim, the
   test, and the code disagree three ways. `claimed-fractal ≠ code`.
4. **Non-orthonormal "Stiefel retraction."** `stiefel_retract` normalizes by `1<<96 / norm_sq` (≈ `1/norm²`,
   not `1/norm`) and clamps `≥0`, so `WᵀW=I` is not maintained. `claimed-invariant ≠ code`.
5. **Non-negative-only clamps** (`.max(0)` everywhere, `quantize` to `[0,1)`) make the "Lie bracket"
   energy/antisymmetry framing a clamped heuristic, not a conservative flow. `bounded ≠ conservative`.

## Decisions (what this product changed, and why)

- **Q32.32 (i64/i128) instead of Q64.64 (i256).** Chosen so every operation stays inside `i128` and the crate
  compiles deterministically. *Rejected:* a bare `i256` (doesn't exist) and a hand-rolled 256-bit multiply
  (added risk for no functional gain at this scope). `representable > aspirational`.
- **In-tree SHA-256 instead of the `sha2` dependency.** Zero supply-chain surface; correctness pinned by the
  NIST `""`/`"abc"`/long test vectors. *Rejected:* `sha2` (a dependency for a hash we can fully self-contain).
- **A true Sierpinski-carpet mask with exact `(8/9)^depth` retention.** Fixes the idempotent-depth ghost; the
  2D index grid gets the 2D fractal (carpet, 8/9 per level), named honestly rather than the 3D sponge ratio.
  *Rejected:* the upstream removal pattern + `(20/27)²` test.
- **A real `verify` (recompute + compare).** Fixes the always-valid ghost. *Rejected:* a constant-return
  integrity stub.
- **Dropped the Stiefel/W projection.** It was the most broken part (non-orthonormal in fixed-point with
  `≥0` clamps); a correct fixed-point orthonormal retraction is `OPEN` and out of scope for v1. The observable
  projection here is a fixed deterministic fold, documented as such. *Rejected:* shipping a "Stiefel" layer
  that isn't one.
- **`std` (not `no_std`) for v1.** Simpler/testable; the crate is `sha2`-free so a `no_std` port is mechanical.

## Honesty / status

- Grades are about THIS reformulation, not the upstream kernel. The kernel's invariants (boundedness, Menger
  fraction, κ-antisymmetry, commitment-verified) are **measured** by `kernel::Invariants`, not asserted.
- Ships **compile-unverified** (no Rust toolchain in the build environment). std-only, zero-dep, hand-reviewed;
  the SHA-256 NIST vectors and exact Menger counts make most of the surface decidable on `cargo test`.
  `written ≠ compiled`; `tested ≠ safe`.
- This is a bounded deterministic mixing + cryptographic commitment. It makes no physical or "reality" claim.
  `integrity ≠ truth`.
