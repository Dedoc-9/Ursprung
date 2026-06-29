// SPDX-License-Identifier: AGPL-3.0-only
//! A discrete-time stability certificate for the reality core — a CHECKABLE SUFFICIENT CONDITION, honestly
//! scoped, not a blanket "proven safe".
//!
//! SUFFICIENT CONDITION (structural): the state update ends in `normalize(...)` onto `S^(n-1)`, so `‖s‖ = 1`
//! (within `eps`) for ANY finite input — the spherical state is bounded by 1 regardless of input magnitude.
//! We certify it by MEASURING the worst sphere residual over a (possibly adversarial) input stream and
//! confirming it stays under tolerance.
//!
//! DOES NOT SHOW: a bound on the basis (`W`) or stress dynamics beyond the measured residual; behavior under
//! non-finite input other than the documented rejection; anything for the un-normalized intermediate.
//! `bounded-by-normalization ≠ globally-stable`; `certificate ≠ proof-of-everything`.

use crate::core::{Config, GeometricCore};

#[derive(Clone, Debug)]
pub struct CertificateResult {
    pub name: &'static str,
    pub holds: bool,
    pub witness: String,
    pub does_not_show: &'static str,
}

/// Certify the spherical-state bound over an input stream.
pub fn certify_sphere_bound(
    n: usize,
    r: usize,
    cfg: Config,
    inputs: &[Vec<f64>],
    tol: f64,
) -> CertificateResult {
    let mut core = GeometricCore::new(n, r, cfg);
    let mut worst = 0.0f64;
    for z in inputs {
        let o = core.step(z);
        if o.sphere_residual > worst {
            worst = o.sphere_residual;
        }
    }
    CertificateResult {
        name: "sphere_bound",
        holds: worst < tol,
        witness: format!("max |‖s‖-1| = {worst:.2e} over {} steps (tol {tol:.0e})", inputs.len()),
        does_not_show:
            "a bound on the basis/stress dynamics beyond the measured residual; holds for finite inputs",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct Lcg(u64);
    impl Lcg {
        fn vec(&mut self, n: usize, scale: f64) -> Vec<f64> {
            (0..n)
                .map(|_| {
                    self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
                    (((self.0 >> 11) as f64 / (1u64 << 53) as f64) * 2.0 - 1.0) * scale
                })
                .collect()
        }
    }

    #[test]
    fn sphere_bound_holds_under_adversarial_input() {
        let mut rng = Lcg(1);
        let inputs: Vec<Vec<f64>> = (0..300).map(|_| rng.vec(8, 1e7)).collect(); // pathological magnitudes
        let cert = certify_sphere_bound(8, 3, Config::default(), &inputs, 1e-6);
        assert!(cert.holds, "{}", cert.witness);
    }

    #[test]
    fn nonfinite_input_does_not_break_the_bound() {
        let inputs: Vec<Vec<f64>> = vec![
            vec![0.3; 6],
            vec![f64::NAN, 0.0, 0.0, 0.0, 0.0, 0.0],
            vec![0.5; 6],
        ];
        let cert = certify_sphere_bound(6, 2, Config::default(), &inputs, 1e-6);
        assert!(cert.holds, "{}", cert.witness);
    }
}
