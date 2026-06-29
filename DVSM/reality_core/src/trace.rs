// SPDX-License-Identifier: AGPL-3.0-only
//! Telemetry tracing — the bridge to the verification backend. Runs the core over a deterministic input
//! stream and records, per frame, the input channels plus the measured invariants. The CSV it writes is what
//! `DVSM/reality_core_probe.py` audits (air-gap / invariants / replay). Deterministic (LCG + logical order).
//!
//! A `leak` mode is provided ONLY to generate the planted-positive trace for the verification backend: it
//! steers the next input from the previous frame's stress — a deliberately broken `observation ≠ authority`.
//! The shipped core never does this; it is a test fixture for proving the auditor discriminates.

use std::fs::File;
use std::io::{self, Write};

use crate::core::{Config, GeometricCore};

/// One row of the telemetry CSV.
#[derive(Clone, Debug)]
pub struct TraceRecord {
    pub frame: u64,
    pub x0: f64,
    pub x1: f64,
    pub stress: f64,
    pub sphere_res: f64,
    pub stiefel_res: f64,
    pub residual_ortho: f64,
    pub health: &'static str,
}

struct Lcg(u64);
impl Lcg {
    fn new(seed: u64) -> Self {
        Self(seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407))
    }
    fn unit(&mut self) -> f64 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.0 >> 11) as f64 / (1u64 << 53) as f64) * 2.0 - 1.0 // [-1, 1]
    }
}

fn health_str(h: crate::core::Health) -> &'static str {
    match h {
        crate::core::Health::Nominal => "Nominal",
        crate::core::Health::Degenerate => "Degenerate",
        crate::core::Health::NonFinite => "NonFinite",
    }
}

/// Run `steps` deterministic steps and return the telemetry. With `leak=true`, the input's first component is
/// steered by the previous frame's stress (the broken-air-gap fixture for the verification backend).
pub fn run_trace(n: usize, r: usize, steps: usize, seed: u64, leak: bool) -> Vec<TraceRecord> {
    let mut core = GeometricCore::new(n, r, Config::default());
    let mut rng = Lcg::new(seed);
    let mut prev_stress = 0.0f64;
    let mut out = Vec::with_capacity(steps);
    for _ in 0..steps {
        let mut z: Vec<f64> = (0..n).map(|_| rng.unit()).collect();
        if leak {
            // stress ∈ [0,2] → quantize into {0,1,2}; a diagnostic steering the next input.
            z[0] = (prev_stress / 2.0 * 3.0).floor() + 0.05 * rng.unit();
        }
        let x0 = z[0];
        let x1 = if n > 1 { z[1] } else { 0.0 };
        let o = core.step(&z);
        prev_stress = o.stress;
        out.push(TraceRecord {
            frame: o.frame,
            x0,
            x1,
            stress: o.stress,
            sphere_res: o.sphere_residual,
            stiefel_res: o.stiefel_residual,
            residual_ortho: o.residual_ortho,
            health: health_str(o.health),
        });
    }
    out
}

/// Write the telemetry as the CSV the Python verification backend reads. Floats use round-trippable `{:e}`.
pub fn write_csv(path: &str, rows: &[TraceRecord]) -> io::Result<()> {
    let mut f = File::create(path)?;
    writeln!(f, "frame,x0,x1,stress,sphere_res,stiefel_res,residual_ortho,health")?;
    for r in rows {
        writeln!(
            f,
            "{},{:.17e},{:.17e},{:.17e},{:.17e},{:.17e},{:.17e},{}",
            r.frame, r.x0, r.x1, r.stress, r.sphere_res, r.stiefel_res, r.residual_ortho, r.health
        )?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn trace_is_deterministic_and_bounded() {
        let a = run_trace(8, 3, 200, 1, false);
        let b = run_trace(8, 3, 200, 1, false);
        assert_eq!(a.len(), 200);
        for (x, y) in a.iter().zip(&b) {
            assert_eq!(x.stress.to_bits(), y.stress.to_bits(), "trace not deterministic");
            assert!(x.stress >= 0.0 && x.stress <= 2.0);
        }
    }

    #[test]
    fn leak_changes_the_trace() {
        let clean = run_trace(8, 3, 200, 2, false);
        let leaky = run_trace(8, 3, 200, 2, true);
        let differs = clean.iter().zip(&leaky).any(|(a, b)| a.x0.to_bits() != b.x0.to_bits());
        assert!(differs, "leak mode should alter the input trace");
    }
}
