// SPDX-License-Identifier: AGPL-3.0-only
//! `cargo run --example demo` — drive the 2-layer core over a synthetic stream and print the measured
//! invariants. Deterministic (logical clock + seeded LCG).

use dvsm_reality_core::{Config, GeometricCore, Mode, Runtime};

struct Lcg(u64);
impl Lcg {
    fn f(&mut self) -> f64 {
        self.0 = self.0.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.0 >> 11) as f64 / (1u64 << 53) as f64) * 2.0 - 1.0
    }
    fn vec(&mut self, n: usize) -> Vec<f64> {
        (0..n).map(|_| self.f()).collect()
    }
}

fn main() {
    let n = 8;
    let r = 3;
    let core = GeometricCore::new(n, r, Config::default());
    let mut rt = Runtime::new(core, Mode::Hybrid);
    let mut rng = Lcg(1);

    println!("dvsm_reality_core demo — n={n} r={r} mode=Hybrid (logical clock, deterministic)\n");
    let mut last = None;
    for k in 0..400 {
        rt.ingest(rng.vec(n));
        if let Some(o) = rt.advance_and_tick(1) {
            if k % 80 == 0 {
                println!(
                    "  frame {:>4}: stress={:.4}  ‖s‖-1={:.2e}  ‖WᵀW-I‖={:.2e}  ‖Wᵀ R‖={:.2e}  {:?}",
                    o.frame, o.stress, o.sphere_residual, o.stiefel_residual, o.residual_ortho, o.health
                );
            }
            last = Some(o);
        }
    }
    if let Some(o) = last {
        println!(
            "\n  final: stress={:.4}  ‖s‖-1={:.2e}  ‖WᵀW-I‖={:.2e}  health={:?}",
            o.stress, o.sphere_residual, o.stiefel_residual, o.health
        );
    }
    println!("  buffered={} dropped={} clock={}", rt.buffered(), rt.dropped(), rt.clock());
    println!("\n  Layer 2 observed the core; it never altered the geometry. observation != authority.");
}
