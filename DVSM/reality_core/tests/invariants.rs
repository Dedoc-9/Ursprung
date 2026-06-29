// SPDX-License-Identifier: AGPL-3.0-only
//! Integration test over the PUBLIC surface: the 2-layer pipeline preserves the manifold invariants under a
//! streaming load, stays bounded under adversarial input, rejects non-finite input, and replays
//! deterministically. Validity-not-outcome — we assert the apparatus, not a hoped trajectory.

use dvsm_reality_core::{Config, GeometricCore, Health, Mode, Runtime, SPHERE_TOL, STIEFEL_TOL};

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

fn fresh_runtime(n: usize, r: usize) -> Runtime {
    Runtime::new(GeometricCore::new(n, r, Config::default()), Mode::Hybrid)
}

#[test]
fn pipeline_preserves_invariants_and_bounds_stress() {
    let mut rt = fresh_runtime(8, 3);
    let mut rng = Lcg(11);
    let mut steps = 0;
    let mut last_health = Health::Nominal;
    for _ in 0..2000 {
        rt.ingest(rng.vec(8, 1.0));
        if let Some(o) = rt.advance_and_tick(1) {
            assert!(o.stress >= 0.0 && o.stress <= 2.0, "stress out of [0,2]: {}", o.stress);
            assert!(o.residual_ortho < 1e-8, "residual not ⟂ frame: {}", o.residual_ortho);
            last_health = o.health;
            steps += 1;
        }
    }
    assert!(steps > 100, "expected many steps, got {steps}");
    let p = rt.probe();
    assert!(p.sphere_residual < SPHERE_TOL, "‖s‖-1 = {}", p.sphere_residual);
    assert!(p.stiefel_residual < STIEFEL_TOL, "‖WᵀW-I‖ = {}", p.stiefel_residual);
    assert_eq!(last_health, Health::Nominal);
}

#[test]
fn bounded_under_adversarial_stream() {
    let mut rt = fresh_runtime(6, 2);
    let mut rng = Lcg(22);
    for _ in 0..1000 {
        rt.ingest(rng.vec(6, 1e7)); // pathological excitation
        if let Some(o) = rt.advance_and_tick(1) {
            assert_ne!(o.health, Health::NonFinite, "core went non-finite under large input");
        }
    }
    // the sphere constraint keeps the state bounded regardless of input magnitude
    let nrm: f64 = rt.observe_state().iter().map(|x| x * x).sum::<f64>().sqrt();
    assert!((nrm - 1.0).abs() < SPHERE_TOL, "state norm drifted: {nrm}");
}

#[test]
fn nonfinite_input_does_not_poison_the_core() {
    let mut core = GeometricCore::new(4, 2, Config::default());
    core.step(&[0.5, 0.5, 0.5, 0.5]);
    let frame_before = core.frame_index();
    let o = core.step(&[1.0, f64::INFINITY, 0.0, 0.0]);
    assert_eq!(o.health, Health::NonFinite);
    assert_eq!(core.frame_index(), frame_before, "non-finite input must not advance state");
    // a subsequent good step still works
    let o2 = core.step(&[0.1, 0.2, 0.3, 0.4]);
    assert_eq!(o2.health, Health::Nominal);
}

#[test]
fn full_pipeline_is_deterministic() {
    let drive = || {
        let mut rt = fresh_runtime(8, 3);
        let mut rng = Lcg(99);
        let mut trace = Vec::new();
        for _ in 0..300 {
            rt.ingest(rng.vec(8, 1.0));
            if let Some(o) = rt.advance_and_tick(1) {
                trace.push((o.stress, o.stiefel_residual));
            }
        }
        trace
    };
    assert_eq!(drive(), drive(), "identical stream + schedule must replay bit-for-bit");
}
