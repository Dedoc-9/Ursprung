// SPDX-License-Identifier: AGPL-3.0-only
//! contraction_cert (Gateway L2) — a SOUND, NARROW, checkable discrete-time contraction certificate for the
//! corrected DVSM Lie step, plus the κ-remediation it depends on. Ported from `DVSM/discrete_certificate.py`
//! + `DVSM/kappa_remediation.py`. NOT a blanket "proven safe": a **sufficient condition** with an explicit
//! boundary. `certificate ≠ proof-of-everything`; `grade ≠ truth`.
//!
//! ## The map (decoupled Z dynamics, fixed S — explicit Euler)
//! `Z' = Z + dt·([Z,S]_κ − λZ)`, where `[Z,S]_κ` is linear in Z: `[Z,S]_κ = M(S)·Z`,
//! `M(S) = diag(κS) − diag(S)κ`. Hence `Z' = [(1−dtλ)I + dt·M(S)]·Z` and, for `dtλ ≤ 1`,
//! `‖Z'‖ ≤ (1 − dtλ + dt·‖M(S)‖)·‖Z‖`.
//!
//! ## The certificate (closed-form sufficient condition for `‖Z'‖ ≤ ρ‖Z‖`, `ρ<1`)
//! A provable Frobenius bound gives `‖M(S)‖₂ ≤ ‖M(S)‖_F ≤ 2·‖κ‖_F·‖S‖₂`. With `σ = sup‖S‖₂`, the condition is
//! `2·‖κ‖_F·σ < λ` **and** `0 < dtλ ≤ 1`, giving `ρ = 1 − dt·(λ − 2‖κ‖_F·σ) ∈ [0,1)`. The admissible noise
//! margin is `σ_max = λ / (2·‖κ‖_F)`.
//!
//! ## Why the κ fix matters
//! Antisymmetrization `κ ← (κ−κᵀ)/2` is an orthogonal projection in the Frobenius inner product, so
//! `‖κ_skew‖_F ≤ ‖κ_sin‖_F` (strict when κ is not already skew). A smaller `‖κ‖_F` WIDENS `σ_max`, so the
//! corrected κ certifies on strictly more regimes than the broken `sin(...)` κ — the fix is the *precondition*
//! that makes this certificate satisfiable, not cosmetics.
//!
//! ## `does_not_show` (the honest boundary)
//! Behavior for `‖S‖ > σ`; the fixed-point CLAMPS in the shipped kernel; the full coupled Z–S–W system;
//! anything outside explicit-Euler with these parameters. `bounded-here ≠ safe-everywhere`.
//!
//! ## Differential note
//! The analytic core (`frob`, `sigma_max`, `step`, `cond`, `rho`, antisymmetrize) is RNG-free and value-parity
//! against the Python reference (`tests/contraction_cert.rs`, ~1e-9). The `certify` sampled worst-case ratio
//! uses an *in-tree* deterministic RNG (NOT Python's `random.gauss`), so its float differs — but the DECISION
//! is governed by the RNG-free `cond` (when `cond` holds the Frobenius bound *proves* `max‖Z'‖ ≤ ρ < 1`, so the
//! sampling can only ever *falsify a bug*). `decisions match, floats need not`.

use crate::invariant_ledger::{ObligationResult, ObligationStatus};

pub type Matrix = Vec<Vec<f64>>;

/// The DVSM κ init constants: `κ[k][j] = sin(k·A − j·B)`. Skew only if `A == B` (they are not) — the recorded
/// ghost the auditor catches. `claimed-skew ≠ actual-skew`.
pub const KAPPA_A: f64 = 1.37;
pub const KAPPA_B: f64 = 1.73;
/// The reduced active-mode count the DVSM reference uses (`dvsm_reference.R`).
pub const R_DEFAULT: usize = 4;

/// `κ[k][j] = sin(k·1.37 − j·1.73)` — the kernel's ACTUAL (non-skew) init.
pub fn kappa_matrix(r: usize) -> Matrix {
    (0..r)
        .map(|k| (0..r).map(|j| (k as f64 * KAPPA_A - j as f64 * KAPPA_B).sin()).collect())
        .collect()
}

/// `κ ← (κ − κᵀ)/2` — the hollow, skew-symmetric part of any square matrix.
pub fn antisymmetrize(m: &Matrix) -> Matrix {
    let n = m.len();
    (0..n).map(|i| (0..n).map(|j| (m[i][j] - m[j][i]) / 2.0).collect()).collect()
}

/// The remediated coupling: the antisymmetrized DVSM κ.
pub fn kappa_skew(r: usize) -> Matrix {
    antisymmetrize(&kappa_matrix(r))
}

/// Frobenius norm (row-major sum order, matching the Python reference).
pub fn frob(m: &Matrix) -> f64 {
    m.iter().flat_map(|row| row.iter()).map(|x| x * x).sum::<f64>().sqrt()
}

/// `max|κ[i,j] + κ[j,i]|` — the skew residual (0 ⇒ skew-symmetric).
pub fn skew_residual(m: &Matrix) -> f64 {
    let n = m.len();
    let mut mx = 0.0_f64;
    for i in 0..n {
        for j in 0..n {
            mx = mx.max((m[i][j] + m[j][i]).abs());
        }
    }
    mx
}

/// `max|κ[i,i]|` — the hollow residual (0 ⇒ zero diagonal).
pub fn hollow_residual(m: &Matrix) -> f64 {
    (0..m.len()).map(|i| m[i][i].abs()).fold(0.0_f64, f64::max)
}

/// The admissible `‖S‖` margin `σ_max = λ / (2‖κ‖_F)` (∞ when κ = 0).
pub fn sigma_max(kappa: &Matrix, lam: f64) -> f64 {
    let f = frob(kappa);
    if f == 0.0 {
        f64::INFINITY
    } else {
        lam / (2.0 * f)
    }
}

fn matvec(m: &Matrix, v: &[f64]) -> Vec<f64> {
    m.iter().map(|row| row.iter().zip(v).map(|(a, b)| a * b).sum()).collect()
}

fn norm(v: &[f64]) -> f64 {
    v.iter().map(|x| x * x).sum::<f64>().sqrt()
}

/// One decoupled corrected Lie step: `Z' = (1−dtλ)Z + dt·M(S)Z`, `M(S)Z = diag(κS)Z − diag(S)(κZ)`.
pub fn step(z: &[f64], s: &[f64], kappa: &Matrix, lam: f64, dt: f64) -> Vec<f64> {
    let kz = matvec(kappa, z);
    let a = matvec(kappa, s); // κS
    (0..z.len())
        .map(|k| {
            let mz = a[k] * z[k] - s[k] * kz[k];
            (1.0 - dt * lam) * z[k] + dt * mz
        })
        .collect()
}

/// A small, in-tree, deterministic PRNG (splitmix64) for the sampled cross-check — keeps the crate zero-dep and
/// reproducible. NOT Python's `random.gauss`, so sampled floats differ; the DECISION does not depend on them.
struct SplitMix64(u64);
impl SplitMix64 {
    fn next_u64(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn next_unit(&mut self) -> f64 {
        // 53-bit mantissa in [0,1)
        (self.next_u64() >> 11) as f64 / ((1u64 << 53) as f64)
    }
    fn gauss(&mut self) -> f64 {
        // Box–Muller (one variate per call)
        let u1 = self.next_unit().max(1e-300);
        let u2 = self.next_unit();
        (-2.0 * u1.ln()).sqrt() * (2.0 * std::f64::consts::PI * u2).cos()
    }
}

/// The certificate verdict: PROVEN contraction under the condition, or not certified.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CertDecision {
    ContractiveCert,
    NotCertified,
}
impl CertDecision {
    pub fn as_str(&self) -> &'static str {
        match self {
            CertDecision::ContractiveCert => "CONTRACTIVE_CERT",
            CertDecision::NotCertified => "NOT_CERTIFIED",
        }
    }
}

/// The result of evaluating the certificate + the sampled cross-check.
#[derive(Debug, Clone)]
pub struct CertifyResult {
    pub frob: f64,
    pub cond: bool,
    pub rho: f64,
    pub sigma: f64,
    pub sigma_max: f64,
    pub max_ratio: f64,
    pub decision: CertDecision,
}

/// Evaluate the certificate at noise margin `sigma` and cross-check it against measured worst-case growth over
/// `samples` random unit-Z / ‖S‖=σ draws (deterministic, `seed`). `decision = CONTRACTIVE_CERT` iff the
/// sufficient condition holds AND no sample grew (the latter can only fail on a bug, since the bound is proven).
pub fn certify(kappa: &Matrix, lam: f64, dt: f64, sigma: f64, samples: usize, seed: u64) -> CertifyResult {
    let f = frob(kappa);
    let cond = dt > 0.0 && dt * lam <= 1.0 && 2.0 * f * sigma < lam;
    let rho = 1.0 - dt * (lam - 2.0 * f * sigma);
    let n = kappa.len();
    let mut rng = SplitMix64(seed);
    let mut max_ratio = 0.0_f64;
    for _ in 0..samples {
        let mut z: Vec<f64> = (0..n).map(|_| rng.gauss()).collect();
        let zn = norm(&z);
        if zn == 0.0 {
            continue;
        }
        for x in z.iter_mut() {
            *x /= zn;
        }
        let mut s: Vec<f64> = (0..n).map(|_| rng.gauss()).collect();
        let sn = norm(&s);
        if sn > 0.0 {
            for x in s.iter_mut() {
                *x = *x / sn * sigma;
            }
        } else {
            s = vec![0.0; n];
        }
        let ratio = norm(&step(&z, &s, kappa, lam, dt)); // ‖Z'‖ with ‖Z‖=1
        if ratio > max_ratio {
            max_ratio = ratio;
        }
    }
    let decision = if cond && max_ratio <= 1.0 + 1e-9 {
        CertDecision::ContractiveCert
    } else {
        CertDecision::NotCertified
    };
    CertifyResult { frob: f, cond, rho, sigma, sigma_max: sigma_max(kappa, lam), max_ratio, decision }
}

/// Project a certificate result into a graded obligation (CLOSED / BOUNDED / UNDERDETERMINED).
pub fn as_obligation(result: &CertifyResult) -> ObligationResult {
    let (status, stmt) = if result.decision == CertDecision::ContractiveCert {
        (ObligationStatus::Closed, "the discrete Lie step contracts ‖Z‖ under the certificate condition")
    } else if result.cond {
        (ObligationStatus::Bounded, "the condition holds but measured worst-case growth was not below 1 (sampling)")
    } else {
        (ObligationStatus::Underdetermined, "the sufficient condition 2‖κ‖_F·σ < λ (with dtλ≤1) is not satisfied")
    };
    ObligationResult::new(
        "discrete_contraction",
        stmt,
        status,
        format!(
            "2‖κ‖_F·σ={:.4} vs λ; ρ={:.4}; measured max‖Z'‖={:.4}; σ_max={:.4}",
            2.0 * result.frob * result.sigma,
            result.rho,
            result.max_ratio,
            result.sigma_max
        ),
        "stability for ‖S‖>σ, the fixed-point clamps, or the full coupled Z–S–W system — a SUFFICIENT \
         condition, not a global proof",
        "a sampled max‖Z'‖ exceeding the analytic ρ (would falsify the bound), or growth within the certified σ",
    )
}

/// The κ-remediation obligation: the antisymmetrized κ is hollow + skew (`max|κ+κᵀ| = 0`), the precondition the
/// certificate leans on. CLOSED by construction; a non-zero residual would be a coding error in the remediation.
pub fn kappa_skew_obligation(r: usize) -> ObligationResult {
    let k = kappa_skew(r);
    let sres = skew_residual(&k);
    let hres = hollow_residual(&k);
    let status = if sres < 1e-12 && hres < 1e-12 { ObligationStatus::Closed } else { ObligationStatus::Violated };
    ObligationResult::new(
        "kappa_skew_remediated",
        "the antisymmetrized κ = (κ−κᵀ)/2 is hollow and skew-symmetric",
        status,
        format!("max|κ+κᵀ|={sres:.2e}, max|diag|={hres:.2e}  (0 ⇒ hollow + skew, by construction)"),
        "that the SHIPPED upstream kernel uses this κ — only that the remediated matrix satisfies the premise",
        "an entry where κ[i,j] + κ[j,i] ≠ 0 after antisymmetrization (a coding error in the remediation)",
    )
}
