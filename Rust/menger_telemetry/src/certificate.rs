// SPDX-License-Identifier: AGPL-3.0-only
//! A boundedness certificate for the telemetry kernel — the simplest, FULLY-DECIDABLE certificate in the
//! family, and honest about why.
//!
//! SUFFICIENT CONDITION (structural): every write to `z`/`s` in `kernel::process_frame` is
//! `fixed::clamp(·, 0, Z_MAX)`, and `fixed::quantize` maps non-finite / out-of-range inputs into `[0,1)`.
//! Therefore **every observable lies in `[0, Z_MAX]` for any input whatsoever** — bounded by construction,
//! not by dynamics. We confirm it over an adversarial stream (huge magnitudes, NaN/inf).
//!
//! DOES NOT SHOW: dynamical stability, convergence, or that the bound is *meaningful* — a clamp guarantees
//! the range, not that the trajectory is right. `bounded-by-clamp ≠ stable-dynamics`; `bounded ≠ correct`.

use crate::kernel::{Kernel, N, RATE_LIMIT_NS};

#[derive(Clone, Debug)]
pub struct CertificateResult {
    pub name: &'static str,
    pub holds: bool,
    pub witness: String,
    pub does_not_show: &'static str,
}

/// Certify that every frame's observables stay in `[0, Z_MAX]` (and finite) over an input stream.
pub fn certify_bounded(menger_depth: u8, inputs: &[[f64; N]]) -> CertificateResult {
    let mut k = Kernel::new(menger_depth);
    let mut t = 0u64;
    let mut all_ok = true;
    let mut frames = 0usize;
    for z in inputs {
        t += RATE_LIMIT_NS;
        if let Ok(snap) = k.process_frame(z, t) {
            let inv = k.invariants(&snap);
            if !(inv.bounded && inv.finite && inv.commitment_verified) {
                all_ok = false;
            }
            frames += 1;
        }
    }
    CertificateResult {
        name: "telemetry_bounded",
        holds: all_ok && frames > 0,
        witness: format!("all {frames} frames bounded ∈ [0,Z_MAX], finite, commitment-verified"),
        does_not_show: "dynamical stability or meaningfulness — bounded-by-clamp ≠ stable-dynamics",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bounded_under_adversarial_and_nonfinite() {
        let mut inputs: Vec<[f64; N]> = Vec::new();
        inputs.push([1e9; N]); // huge
        let mut nanrow = [50.0; N];
        nanrow[0] = f64::NAN;
        nanrow[1] = f64::INFINITY;
        inputs.push(nanrow); // non-finite
        for i in 0..200 {
            inputs.push([(i % 97) as f64; N]);
        }
        let cert = certify_bounded(2, &inputs);
        assert!(cert.holds, "{}", cert.witness);
    }
}
