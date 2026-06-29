// SPDX-License-Identifier: AGPL-3.0-only
//! Core-hardening checks: parameter validation clamps nonsense, a seeded start still passes through the
//! manifold invariants, and `step_many` matches stepping one at a time. Validity-not-outcome.

use dvsm_reality_core::{Config, GeometricCore, SPHERE_TOL, STIEFEL_TOL};

#[test]
fn config_validation_clamps_nonsense() {
    let c = Config { alpha: 5.0, lambda: -1.0, eta: f64::NAN, eps: -3.0 }.validated();
    assert_eq!(c.alpha, 1.0);
    assert_eq!(c.lambda, 0.0);
    assert_eq!(c.eta, 0.0);
    assert!(c.eps > 0.0);
}

#[test]
fn seeded_start_satisfies_invariants() {
    // arbitrary (non-unit, non-orthonormal) seed ⇒ constructor must project onto the manifolds
    let s0 = vec![3.0, -1.0, 2.0, 0.5];
    let w0 = vec![vec![1.0, 1.0, 0.0, 0.0], vec![0.0, 2.0, 1.0, 0.0]];
    let core = GeometricCore::seeded(4, 2, Config::default(), &s0, w0);
    let p = core.probe();
    assert!(p.sphere_residual < SPHERE_TOL, "‖s‖-1 = {}", p.sphere_residual);
    assert!(p.stiefel_residual < STIEFEL_TOL, "‖WᵀW-I‖ = {}", p.stiefel_residual);
}

#[test]
fn step_many_matches_individual_steps() {
    let inputs: Vec<Vec<f64>> = (0..50)
        .map(|i| vec![(i as f64).sin(), (i as f64).cos(), 0.3, -0.2, 0.1, 0.0])
        .collect();
    let mut a = GeometricCore::new(6, 2, Config::default());
    let batch: Vec<f64> = a.step_many(&inputs).iter().map(|o| o.stress).collect();

    let mut b = GeometricCore::new(6, 2, Config::default());
    let single: Vec<f64> = inputs.iter().map(|z| b.step(z).stress).collect();

    assert_eq!(batch, single, "step_many must match repeated step");
}

#[test]
fn observation_is_healthy_reflects_health() {
    let mut core = GeometricCore::new(4, 2, Config::default());
    assert!(core.step(&[0.2, 0.3, 0.1, 0.4]).is_healthy());
    assert!(!core.step(&[f64::NAN, 0.0, 0.0, 0.0]).is_healthy());
}
