// SPDX-License-Identifier: AGPL-3.0-only
//! # dvsm_reality_core — the DVSM 2-Layer Reality Core, hardened into a standalone product
//!
//! A faithful, compilable, tested re-engineering of the DVSM `Two_Layer_Reality_Core` (a contractive
//! projection dynamical system on `S^(n-1) × St(n,r)`). Two layers, with the boundary enforced by Rust's
//! type system rather than by convention:
//!
//! * **Layer 1 — [`GeometricCore`]** (immutable mathematics): projection `Π_W(z)=WWᵀz`, residual `R⊥W`,
//!   contractive spherical state flow, residual-driven Stiefel retraction, stress `B(t)∈[0,2]`. Its state is
//!   PRIVATE; the only mutation is [`GeometricCore::step`].
//! * **Layer 2 — [`Runtime`]** (mutable execution): streaming ingestion, bounded backpressure, logical-clock
//!   scheduling, mode switching. It holds a core privately and may *observe* it, but has no way to alter the
//!   geometry. `observation != authority`; `mode != geometry`.
//!
//! ## What "hardened for use" means here (over the upstream research file)
//! 1. **It compiles.** The upstream `.rs` is a concatenation of three divergent variants (duplicate
//!    `Config`/`DVSMCore`/`project`); this is one consistent module. `file != crate`.
//! 2. **One canonical rule.** The upstream specified the update three inconsistent ways; this fixes one and
//!    records the rejected variants (see PROVENANCE.md). `comment-invariant != code-invariant`.
//! 3. **Invariants are measured, not asserted.** Every [`Observation`] carries `sphere_residual`,
//!    `stiefel_residual`, `residual_ortho`, and a [`Health`] state. `invariant != comment`.
//! 4. **Deterministic & replayable.** No wall-clock anywhere; the runtime advances on a logical clock, so a
//!    given (stream, schedule) replays bit-for-bit. `replay-determinism > Instant::now()`.
//! 5. **Numeric hardening.** `eps` floors, non-finite input rejected (state preserved), rank-deficiency
//!    reseeds the basis, adversarial (huge-norm) input stays bounded by the sphere/Stiefel constraints.
//! 6. **Zero dependencies.** std-only linear algebra — no supply-chain surface, no BLAS nondeterminism.
//!
//! ## Boundaries (load-bearing)
//! This is a bounded dynamical *codec/observer*, not a physics or "reality" claim. `integrity != truth`;
//! `bounded != correct`; `stress-is-low != model-is-right`. The stress `B(t)` is angular divergence between
//! the internal state and the projected input — a salience signal, not a verdict. `salience != importance`.

pub mod certificate;
pub mod core;
pub mod ffi;
pub mod linalg;
pub mod runtime;
pub mod trace;

pub use crate::certificate::{certify_sphere_bound, CertificateResult};
pub use crate::core::{Config, GeometricCore, Health, Observation, SPHERE_TOL, STIEFEL_TOL};
pub use crate::ffi::ObservationC;
pub use crate::linalg::Frame;
pub use crate::runtime::{Mode, Runtime};
pub use crate::trace::{run_trace, write_csv, TraceRecord};
