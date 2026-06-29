// SPDX-License-Identifier: AGPL-3.0-only
//! # menger_telemetry — the DVSM Menger-sponge telemetry kernel, hardened
//!
//! A compilable, tested, **zero-dependency** re-engineering of the DVSM `system-telemetry-minimal` crate
//! (the `Research/MengerSponge` folder of `dvsm-meta-kernel`). It keeps the sound ideas — deterministic
//! fixed-point telemetry, a Menger fractal sparsity mask gating a coupling, and a cryptographic frame
//! commitment — and fixes the ghosts the upstream code carried under aspirational comments.
//!
//! ## Modules
//! * [`fixed`] — Q32.32 fixed-point (`i64`/`i128`; no phantom `i256`).
//! * [`sha256`] — in-tree SHA-256 (FIPS 180-4), pinned by NIST test vectors (no `sha2` dependency).
//! * [`menger`] — the Sierpinski-carpet sparsity mask; depth is **real** and the retained fraction is exactly
//!   `(8/9)^depth` (tested).
//! * [`kernel`] — the deterministic pipeline: quantize → dissipate → Menger-masked bounded coupling → EMA →
//!   SHA-256 commitment, with rate limiting, MEASURED invariants, and a **real** `verify`.
//! * [`ffi`] — the C ABI (`telemetry_*`), including a verify that actually verifies.
//!
//! ## What was fixed (see `PROVENANCE.md`)
//! 1. **Compiles.** Upstream used a non-existent `i256`. Here: Q32.32 in `i128`. `file ≠ crate`.
//! 2. **Real integrity check.** Upstream `telemetry_verify_hash` returned valid unconditionally; here `verify`
//!    recomputes the commitment and compares. `attests ≠ verifies`.
//! 3. **Real fractal depth.** Upstream's depth loop was idempotent (depth 1 == depth 2); here depth changes
//!    the mask and the retained fraction is exact. `claimed-fractal ≠ code` → fixed.
//! 4. **Measured invariants.** Boundedness, Menger fraction, κ-antisymmetry, and commitment-verified are
//!    reported by [`kernel::Invariants`], not asserted in comments. `invariant ≠ comment`.
//!
//! ## Boundary (honest)
//! This is a **bounded deterministic mixing** with a Menger sparsity structure and a hash commitment — not a
//! conservative Lie flow and not a "reality" model. The state is clamped to a non-negative range (telemetry
//! convention), which breaks energy conservation; the antisymmetric `κ` + bracket *form* is retained but no
//! conservation is claimed. `bounded ≠ conservative`; `integrity ≠ truth`; `deterministic ≠ correct`.

pub mod certificate;
pub mod ffi;
pub mod fixed;
pub mod kernel;
pub mod menger;
pub mod sha256;

pub use certificate::{certify_bounded, CertificateResult};
pub use fixed::{qmul, quantize, Fixed, ONE};
pub use kernel::{FrameSnapshot, Invariants, Kernel, ProcessError, D, HASH_SIZE, N};
pub use menger::{max_depth, MengerMask};
pub use sha256::{sha256, to_hex};

pub const VERSION: &str = "0.1.0-menger-hardened";
