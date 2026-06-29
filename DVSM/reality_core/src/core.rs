// SPDX-License-Identifier: AGPL-3.0-only
//! LAYER 1 — the immutable geometric core.
//!
//! A contractive projection dynamical system on the product manifold `S^(n-1) × St(n,r)`:
//!
//! ```text
//!   z_proj = Π_W(z) = W Wᵀ z            (geometric observation of the input)
//!   R      = z - z_proj                  (residual, ⟂ span(W) by construction)
//!   ŝ, ẑ   = normalize(s), normalize(z_proj)
//!   s      ← normalize( (1-λ)(α ŝ + (1-α) ẑ) + λ ŝ )      (contractive spherical flow)
//!   W      ← orthonormalize( W + η · cⱼ · R̂ )             (residual-driven Stiefel retraction)
//!   B(t)   = 1 - clamp(⟨ŝ, ẑ_proj⟩, -1, 1) ∈ [0,2]        (stress / angular divergence)
//! ```
//!
//! CANONICAL-CHOICE NOTE. The upstream `Two_Layer_Reality_Core.rs` specified the update three different ways
//! in one file (λ·S vs λ·Ŝ damping; true-residual vs residual-of-z basis flow). This core fixes ONE
//! internally-consistent rule (λ·Ŝ damping; true-residual `R` driving the basis, matching the header's
//! `W ← QR(W + η·ΔR)`). The rejected variants are recorded in PROVENANCE.md. `comment-invariant != code-invariant`.
//!
//! The invariants are MEASURED every step and reported in [`Observation`] — never merely asserted in a
//! comment. The state (`s`, `w`) is PRIVATE: the only mutation is [`GeometricCore::step`]. Layer 2 may observe
//! but cannot reach in and alter the geometry. `observation != authority`.

use crate::linalg::{self, Frame};

/// Tolerances above which the measured invariant residuals are reported as `Degenerate`.
pub const SPHERE_TOL: f64 = 1e-6;
pub const STIEFEL_TOL: f64 = 1e-6;

#[derive(Clone, Copy, Debug)]
pub struct Config {
    pub alpha: f64,  // state inertia / blend, 0..=1
    pub lambda: f64, // contractive damping, 0..=1
    pub eta: f64,    // basis (Stiefel) learning rate
    pub eps: f64,    // numerical floor
}

impl Default for Config {
    fn default() -> Self {
        Self { alpha: 0.5, lambda: 0.1, eta: 0.05, eps: 1e-12 }
    }
}

/// The measured health of the core after a step — an explicit epistemic state, not a boolean.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Health {
    Nominal,
    Degenerate, // an invariant residual exceeded tolerance, or a basis column was reseeded
    NonFinite,  // a NaN/inf appeared (or the input carried one) — state left unchanged
}

/// Read-only telemetry emitted by each step. This is an OBSERVATION of the core, carrying its own measured
/// limits — it grants no authority to mutate the core. `B(t) ∈ [0,2]`.
#[derive(Clone, Copy, Debug)]
pub struct Observation {
    pub frame: u64,
    pub stress: f64,            // B(t) = 1 - cos(angle(s, z_proj)) ∈ [0,2]
    pub sphere_residual: f64,   // |‖s‖ - 1|
    pub stiefel_residual: f64,  // ‖WᵀW - I‖_F
    pub residual_ortho: f64,    // ‖Wᵀ R‖ (should be ~0 by construction)
    pub reseeded: bool,         // a basis column collapsed and was reseeded this step
    pub health: Health,
}

/// LAYER 1. Private `s`/`w`: the geometry can only evolve through [`step`](Self::step).
pub struct GeometricCore {
    s: Vec<f64>,
    w: Frame,
    cfg: Config,
    frame: u64,
}

impl GeometricCore {
    pub fn new(n: usize, r: usize, cfg: Config) -> Self {
        Self { s: vec![0.0; n], w: Frame::identity(n, r), cfg, frame: 0 }
    }

    pub fn dims(&self) -> (usize, usize) {
        (self.w.n, self.w.r)
    }
    pub fn config(&self) -> Config {
        self.cfg
    }
    pub fn frame_index(&self) -> u64 {
        self.frame
    }
    /// Read-only view of the spherical state. Observation, not authority — there is no mutable accessor.
    pub fn state(&self) -> &[f64] {
        &self.s
    }

    /// Measure the current invariant residuals without stepping (a non-invasive probe).
    pub fn probe(&self) -> Observation {
        let sphere_residual = (linalg::norm(&self.s) - 1.0).abs();
        let stiefel_residual = self.w.stiefel_residual();
        let finite = linalg::all_finite(&self.s) && self.w.all_finite();
        Observation {
            frame: self.frame,
            stress: f64::NAN,
            sphere_residual,
            stiefel_residual,
            residual_ortho: 0.0,
            reseeded: false,
            health: classify(finite, sphere_residual, stiefel_residual, false),
        }
    }

    /// One geometric step. A non-finite input is REJECTED (state unchanged, `Health::NonFinite`) rather than
    /// allowed to poison the manifold. Returns the measured observation.
    pub fn step(&mut self, z: &[f64]) -> Observation {
        assert_eq!(z.len(), self.w.n, "input dimension mismatch");
        let cfg = self.cfg;

        if !linalg::all_finite(z) {
            let mut o = self.probe();
            o.health = Health::NonFinite;
            return o; // do not advance the frame; do not touch state
        }

        // 1. geometric observation of the input
        let z_proj = self.w.project(z);
        let r = self.w.residual(z);
        let residual_ortho = linalg::norm(&self.w.coeffs(&r)); // ‖Wᵀ R‖, measured before W moves

        // 2. contractive spherical state flow  (canonical: λ·ŝ damping)
        let s_hat = linalg::normalized(&self.s, cfg.eps);
        let z_hat = linalg::normalized(&z_proj, cfg.eps);
        let blend = linalg::combine2(&s_hat, cfg.alpha, &z_hat, 1.0 - cfg.alpha);
        let damped = linalg::combine2(&blend, 1.0 - cfg.lambda, &s_hat, cfg.lambda);
        self.s = linalg::normalized(&damped, cfg.eps);

        // 3. residual-driven Stiefel retraction  (canonical: W ← orthonormalize(W + η·cⱼ·R̂))
        let r_hat = linalg::normalized(&r, cfg.eps);
        let c = self.w.coeffs(z);
        for j in 0..self.w.r {
            linalg::axpy(&mut self.w.cols[j], cfg.eta * c[j], &r_hat);
        }
        let reseeded = self.w.orthonormalize(cfg.eps);

        self.frame += 1;

        // 4. measured observation
        let s_hat2 = linalg::normalized(&self.s, cfg.eps);
        let zp_hat = linalg::normalized(&z_proj, cfg.eps);
        let stress = 1.0 - linalg::dot(&s_hat2, &zp_hat).clamp(-1.0, 1.0);
        let sphere_residual = (linalg::norm(&self.s) - 1.0).abs();
        let stiefel_residual = self.w.stiefel_residual();
        let finite = linalg::all_finite(&self.s) && self.w.all_finite();
        Observation {
            frame: self.frame,
            stress,
            sphere_residual,
            stiefel_residual,
            residual_ortho,
            reseeded,
            health: classify(finite, sphere_residual, stiefel_residual, reseeded),
        }
    }
}

fn classify(finite: bool, sphere: f64, stiefel: f64, reseeded: bool) -> Health {
    if !finite {
        Health::NonFinite
    } else if reseeded || sphere > SPHERE_TOL || stiefel > STIEFEL_TOL {
        Health::Degenerate
    } else {
        Health::Nominal
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // a tiny deterministic LCG so the tests need no rand crate
    struct Lcg(u64);
    impl Lcg {
        fn f(&mut self) -> f64 {
            self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            ((self.0 >> 11) as f64 / (1u64 << 53) as f64) * 2.0 - 1.0
        }
        fn vec(&mut self, n: usize, scale: f64) -> Vec<f64> {
            (0..n).map(|_| self.f() * scale).collect()
        }
    }

    #[test]
    fn invariants_hold_after_many_steps() {
        let mut core = GeometricCore::new(8, 3, Config::default());
        let mut rng = Lcg(1);
        let mut last = core.probe();
        for _ in 0..500 {
            last = core.step(&rng.vec(8, 1.0));
            assert!(last.stress >= 0.0 && last.stress <= 2.0, "stress out of range: {}", last.stress);
        }
        assert!(last.sphere_residual < SPHERE_TOL, "‖s‖-1 = {}", last.sphere_residual);
        assert!(last.stiefel_residual < STIEFEL_TOL, "‖WᵀW-I‖ = {}", last.stiefel_residual);
        assert!(last.residual_ortho < 1e-8, "‖Wᵀ R‖ = {}", last.residual_ortho);
        assert_eq!(last.health, Health::Nominal);
    }

    #[test]
    fn bounded_under_adversarial_input() {
        let mut core = GeometricCore::new(6, 2, Config::default());
        let mut rng = Lcg(2);
        for _ in 0..200 {
            let o = core.step(&rng.vec(6, 1e6)); // huge excitation
            assert_ne!(o.health, Health::NonFinite);
        }
        assert!((linalg::norm(core.state()) - 1.0).abs() < SPHERE_TOL);
    }

    #[test]
    fn nonfinite_input_is_rejected() {
        let mut core = GeometricCore::new(4, 2, Config::default());
        core.step(&[0.1, 0.2, 0.3, 0.4]);
        let before = core.frame_index();
        let o = core.step(&[f64::NAN, 0.0, 0.0, 0.0]);
        assert_eq!(o.health, Health::NonFinite);
        assert_eq!(core.frame_index(), before, "rejected input must not advance the frame");
    }

    #[test]
    fn determinism() {
        let run = || {
            let mut core = GeometricCore::new(8, 3, Config::default());
            let mut rng = Lcg(7);
            (0..100).map(|_| core.step(&rng.vec(8, 1.0)).stress).collect::<Vec<_>>()
        };
        assert_eq!(run(), run());
    }
}
