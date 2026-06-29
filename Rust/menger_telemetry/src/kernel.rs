// SPDX-License-Identifier: AGPL-3.0-only
//! The deterministic telemetry kernel: Q32.32 fixed-point, a Menger/Sierpinski-sparsified bounded coupling,
//! an in-tree SHA-256 commitment, rate limiting, and MEASURED invariants.
//!
//! HARDENING vs the upstream kernel:
//!  • compiles (Q32.32 in `i128`, no phantom `i256`);
//!  • the Menger depth is real (`menger.rs`), not idempotent;
//!  • the integrity check actually verifies (`verify` recomputes the commitment and compares — the upstream's
//!    `telemetry_verify_hash` returned "valid" unconditionally);
//!  • invariants are MEASURED (`Invariants`), not asserted in comments.
//!
//! HONEST BOUNDARY: this is a *bounded deterministic mixing* with a Menger sparsity structure and a hash
//! commitment — NOT a conservative Lie flow. The state is clamped to a non-negative range (telemetry
//! convention), which breaks energy conservation; we keep the antisymmetric `κ` + bracket *form* but make no
//! conservation claim. `bounded ≠ conservative`; `integrity ≠ truth`.

use crate::fixed::{self, quantize, qmul, Fixed, ONE};
use crate::menger::MengerMask;
use crate::sha256::sha256;

pub const N: usize = 16; // sensor / state dimension
pub const D: usize = 9; // observable / coupling dimension (3^2 ⇒ a clean Menger carpet)
pub const HASH_SIZE: usize = 32;
pub const RATE_LIMIT_NS: u64 = 1_000_000; // 1000 fps
pub const PROTOCOL_VERSION: u32 = 1;

fn lambda() -> Fixed {
    fixed::from_f64(0.05)
}
fn alpha() -> Fixed {
    fixed::from_f64(0.98)
}
fn beta() -> Fixed {
    fixed::from_f64(0.7)
}
fn dt() -> Fixed {
    fixed::from_f64(0.05)
}
fn z_max() -> Fixed {
    fixed::from_f64(16.0)
}

const RANGES: [f64; N] = [
    100.0, 100.0, 100.0, 150.0, 500.0, // cpu%, gpu%, mem%, therm, power
    5000.0, 5000.0, 100.0, 255.0, // freq_cpu, freq_gpu, bw, latency
    100.0, 100.0, 100.0, 1.0, 1.0, 1.0, 1.0, // gpu_mem, disk, net, reserves
];

#[repr(C)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct FrameSnapshot {
    pub mu: [u8; N],
    pub z: [Fixed; D],
    pub s: [Fixed; D],
    pub hash: [u8; HASH_SIZE],
    pub timestamp_ns: u64,
    pub frame: u64,
    pub menger_depth: u8,
}

impl Default for FrameSnapshot {
    fn default() -> Self {
        Self {
            mu: [0u8; N],
            z: [0; D],
            s: [0; D],
            hash: [0u8; HASH_SIZE],
            timestamp_ns: 0,
            frame: 0,
            menger_depth: 0,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ProcessError {
    RateLimited,
}

/// Measured (not asserted) invariants of a snapshot, relative to this kernel.
#[derive(Clone, Copy, Debug)]
pub struct Invariants {
    pub bounded: bool,            // all z,s in [0, Z_MAX]
    pub finite: bool,             // no value pinned at i64 extremes
    pub menger_fraction: f64,     // retained coupling fraction = (8/9)^depth
    pub antisymmetry_residual: Fixed, // max |κ[i,j] + κ[j,i]| (0 ⇒ exactly antisymmetric)
    pub commitment_verified: bool, // hash recomputed and matched
}

pub struct Kernel {
    snapshot: FrameSnapshot,
    kappa: [Fixed; D * D], // antisymmetric coupling
    mask: MengerMask,
    menger_depth: u8,
    frame_count: u64,
    rate_limit_last_ns: u64,
    started: bool,
}

impl Kernel {
    pub fn new(menger_depth: u8) -> Self {
        let depth = menger_depth.min(crate::menger::max_depth(D) as u8);
        let mut kappa = [0 as Fixed; D * D];
        // deterministic antisymmetric seed (small, in Q32.32)
        for i in 0..D {
            for j in (i + 1)..D {
                let seed = ((i * 17 + j * 31) as i64).wrapping_mul(0x9E37_79B9) & 0x0000_0000_3FFF_FFFF;
                kappa[i * D + j] = seed; // < 0.25 in Q32.32
                kappa[j * D + i] = -seed;
            }
        }
        Self {
            snapshot: FrameSnapshot { menger_depth: depth, ..Default::default() },
            kappa,
            mask: MengerMask::new(D, depth as u32),
            menger_depth: depth,
            frame_count: 0,
            rate_limit_last_ns: 0,
            started: false,
        }
    }

    pub fn menger_depth(&self) -> u8 {
        self.menger_depth
    }
    pub fn frame_count(&self) -> u64 {
        self.frame_count
    }
    pub fn snapshot(&self) -> &FrameSnapshot {
        &self.snapshot
    }

    /// Reconfigure Menger depth (clamped). Clears nothing else — the geometry of the coupling changes, which
    /// the commitment will reflect from the next frame.
    pub fn set_menger_depth(&mut self, depth: u8) {
        let depth = depth.min(crate::menger::max_depth(D) as u8);
        self.menger_depth = depth;
        self.mask = MengerMask::new(D, depth as u32);
    }

    fn commit(mu: &[u8; N], z: &[Fixed; D], s: &[Fixed; D], depth: u8) -> [u8; HASH_SIZE] {
        let mut buf: Vec<u8> = Vec::with_capacity(N + D * 16 + 8);
        buf.extend_from_slice(mu);
        for &zi in z {
            buf.extend_from_slice(&zi.to_le_bytes());
        }
        for &si in s {
            buf.extend_from_slice(&si.to_le_bytes());
        }
        buf.extend_from_slice(&PROTOCOL_VERSION.to_le_bytes());
        buf.push(depth);
        sha256(&buf)
    }

    /// Process one frame (immutable ordering). Returns the snapshot or `RateLimited`.
    pub fn process_frame(&mut self, sensors: &[f64; N], now_ns: u64) -> Result<FrameSnapshot, ProcessError> {
        if self.started && now_ns < self.rate_limit_last_ns + RATE_LIMIT_NS {
            return Err(ProcessError::RateLimited);
        }
        self.rate_limit_last_ns = now_ns;
        self.started = true;

        let prior = self.snapshot;

        // L1 acquire → Q32.32 in [0,1)
        let mut mu_q = [0 as Fixed; N];
        for i in 0..N {
            mu_q[i] = quantize(sensors[i], RANGES[i]);
        }

        // L2 dissipate (EMA toward the prior state byte-field, lifted back to Q32.32)
        let b = beta();
        let one_minus_b = ONE - b;
        let mut mu = [0 as Fixed; N];
        for i in 0..N {
            let prior_fixed = (prior.mu[i] as Fixed) << (fixed::FRAC_BITS - 8); // byte → [0,1)
            mu[i] = fixed::clamp(qmul(mu_q[i], b) + qmul(prior_fixed, one_minus_b), 0, ONE - 1);
        }

        // bytes for the commitment (top 8 fractional bits)
        let mut mu_bytes = [0u8; N];
        for i in 0..N {
            mu_bytes[i] = ((mu[i] >> (fixed::FRAC_BITS - 8)) as i64).clamp(0, 255) as u8;
        }

        // project N → D (fixed deterministic fold), bounded
        let zmax = z_max();
        let mut z_in = [0 as Fixed; D];
        for k in 0..D {
            let extra = if k + D < N { mu[k + D] } else { 0 };
            z_in[k] = fixed::clamp(mu[k] + extra, 0, zmax);
        }

        // Menger-masked bounded coupling: z ← clamp(z + dt·([Z,S]_κ on the mask − λZ), 0, Z_MAX)
        let lam = lambda();
        let dtv = dt();
        let mut z = [0 as Fixed; D];
        for k in 0..D {
            let mut acc: i128 = 0;
            for j in 0..D {
                if self.mask.kept(k, j) {
                    let br = qmul(z_in[k], prior.s[j]).wrapping_sub(qmul(z_in[j], prior.s[k]));
                    acc += qmul(br, self.kappa[k * D + j]) as i128;
                }
            }
            let bracket = acc.clamp(i64::MIN as i128, i64::MAX as i128) as Fixed;
            let decay = qmul(lam, z_in[k]);
            let delta = qmul(dtv, bracket.wrapping_sub(decay));
            z[k] = fixed::clamp(z_in[k] + delta, 0, zmax);
        }

        // EMA residual memory S
        let a = alpha();
        let one_minus_a = ONE - a;
        let mut s = [0 as Fixed; D];
        for k in 0..D {
            s[k] = fixed::clamp(qmul(a, prior.s[k]) + qmul(one_minus_a, z[k]), 0, zmax);
        }

        let hash = Self::commit(&mu_bytes, &z, &s, self.menger_depth);

        let snap = FrameSnapshot {
            mu: mu_bytes,
            z,
            s,
            hash,
            timestamp_ns: now_ns,
            frame: self.frame_count.wrapping_add(1),
            menger_depth: self.menger_depth,
        };
        self.snapshot = snap;
        self.frame_count = self.frame_count.wrapping_add(1);
        Ok(snap)
    }

    /// REAL integrity check: recompute the commitment from the snapshot's fields and compare. Catches any
    /// tampering of `mu`/`z`/`s`/`hash`/`depth`. (The upstream's verify returned "valid" unconditionally.)
    pub fn verify(snap: &FrameSnapshot) -> bool {
        Self::commit(&snap.mu, &snap.z, &snap.s, snap.menger_depth) == snap.hash
    }

    /// Measure the invariants of a snapshot relative to this kernel.
    pub fn invariants(&self, snap: &FrameSnapshot) -> Invariants {
        let zmax = z_max();
        let bounded = snap.z.iter().chain(snap.s.iter()).all(|&v| v >= 0 && v <= zmax);
        let finite = snap.z.iter().chain(snap.s.iter()).all(|&v| v > i64::MIN && v < i64::MAX);
        let mut anti: Fixed = 0;
        for i in 0..D {
            for j in 0..D {
                let r = (self.kappa[i * D + j] + self.kappa[j * D + i]).abs();
                if r > anti {
                    anti = r;
                }
            }
        }
        Invariants {
            bounded,
            finite,
            menger_fraction: self.mask.fraction(),
            antisymmetry_residual: anti,
            commitment_verified: Self::verify(snap),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sensors(v: f64) -> [f64; N] {
        [v; N]
    }

    #[test]
    fn determinism_same_input_same_hash() {
        let mut a = Kernel::new(2);
        let mut b = Kernel::new(2);
        let sa = a.process_frame(&sensors(50.0), 1_000).unwrap();
        let sb = b.process_frame(&sensors(50.0), 1_000).unwrap();
        assert_eq!(sa.hash, sb.hash);
    }

    #[test]
    fn rate_limiting() {
        let mut k = Kernel::new(0);
        assert!(k.process_frame(&sensors(50.0), 0).is_ok());
        assert_eq!(k.process_frame(&sensors(50.0), 999_999), Err(ProcessError::RateLimited));
        assert!(k.process_frame(&sensors(50.0), 2_000_000).is_ok());
    }

    #[test]
    fn menger_depth_changes_hash_and_fraction() {
        let mut k0 = Kernel::new(0);
        let mut k2 = Kernel::new(2);
        let s0 = k0.process_frame(&sensors(50.0), 1_000).unwrap();
        let s2 = k2.process_frame(&sensors(50.0), 1_000).unwrap();
        assert_ne!(s0.hash, s2.hash, "different Menger config ⇒ different commitment");
        assert!((k0.mask_fraction() - 1.0).abs() < 1e-12);
        assert!((k2.mask_fraction() - (8.0 / 9.0_f64).powi(2)).abs() < 1e-12);
    }

    #[test]
    fn bounded_and_finite_over_many_frames() {
        let mut k = Kernel::new(2);
        let mut t = 0u64;
        let mut last = FrameSnapshot::default();
        for i in 0..500 {
            t += 2_000_000;
            last = k.process_frame(&sensors(30.0 + (i % 70) as f64), t).unwrap();
        }
        let inv = k.invariants(&last);
        assert!(inv.bounded && inv.finite, "state left the bounded range");
        assert_eq!(inv.antisymmetry_residual, 0, "κ must be exactly antisymmetric");
    }

    #[test]
    fn verify_accepts_genuine_and_rejects_tampered() {
        let mut k = Kernel::new(1);
        let snap = k.process_frame(&sensors(42.0), 1_000).unwrap();
        assert!(Kernel::verify(&snap), "genuine snapshot must verify");
        let mut tampered = snap;
        tampered.z[0] = tampered.z[0].wrapping_add(1);
        assert!(!Kernel::verify(&tampered), "tampered snapshot must fail verify");
    }
}

#[cfg(test)]
impl Kernel {
    fn mask_fraction(&self) -> f64 {
        self.mask.fraction()
    }
}
