// SPDX-License-Identifier: AGPL-3.0-only
//! L2 contraction certifier — differential against the Python reference (`DVSM/discrete_certificate.py` +
//! `DVSM/kappa_remediation.py`). The analytic core (`frob`, `sigma_max`, `step`, `rho`, antisymmetrize) is
//! RNG-free, so it is checked to **value-parity** (~1e-9) against numbers produced by the Python code. The
//! `certify` sampled cross-check uses an in-tree RNG (not Python's `random.gauss`), so only the **decision** is
//! compared — and the decision is governed by the RNG-free `cond` (when `cond` holds the Frobenius bound proves
//! `max‖Z'‖ ≤ ρ < 1`). `decisions match, floats need not`; `certificate ≠ proof-of-everything`.

use ursprung::{
    certify, contraction_obligation, frob, hollow_residual, kappa_matrix, kappa_skew, kappa_skew_obligation,
    lie_step, sigma_max, skew_residual, CertDecision,
};
use ursprung::ObligationStatus;

const R: usize = 4;
const LAM: f64 = 0.5;
const DT: f64 = 0.1;

// Python reference values (DVSM/discrete_certificate.py with R=4, lam=0.5, dt=0.1):
const FROB_SIN: f64 = 2.846791627455805;
const FROB_SKEW: f64 = 2.3767220276469088;
const SIGMA_MAX_SIN: f64 = 0.08781815907735632;
const SIGMA_MAX_SKEW: f64 = 0.10518689063841191;
const RHO_SKEW: f64 = 0.9958719353106553;
const RHO_SIN: f64 = 1.004944515958754;
const SKEWRES_SIN: f64 = 1.7639156137698941;
// step([1,0,0,0],[0.1,0.2,0.3,0.4], kappa_skew, 0.5, 0.1):
const STEP_SKEW: [f64; 4] =
    [0.963401522955962, -0.01967261901099331, -0.00116745629693223, 0.03424159826388761];

fn close(a: f64, b: f64) -> bool {
    (a - b).abs() <= 1e-9 * (1.0 + b.abs())
}

/// The σ the Python `main` uses: midway between the two margins (so skew certifies, sin does not).
fn sigma_between() -> f64 {
    (sigma_max(&kappa_matrix(R), LAM) + sigma_max(&kappa_skew(R), LAM)) / 2.0
}

#[test]
fn analytic_value_parity_with_python() {
    assert!(close(frob(&kappa_matrix(R)), FROB_SIN), "frob(sin) parity");
    assert!(close(frob(&kappa_skew(R)), FROB_SKEW), "frob(skew) parity");
    assert!(close(sigma_max(&kappa_matrix(R), LAM), SIGMA_MAX_SIN), "sigma_max(sin) parity");
    assert!(close(sigma_max(&kappa_skew(R), LAM), SIGMA_MAX_SKEW), "sigma_max(skew) parity");
}

#[test]
fn kappa_fix_widens_margin() {
    // the precondition the certificate leans on: antisymmetrization shrinks ‖κ‖_F, which widens σ_max
    assert!(frob(&kappa_skew(R)) < frob(&kappa_matrix(R)), "‖κ_skew‖_F < ‖κ_sin‖_F");
    assert!(
        sigma_max(&kappa_skew(R), LAM) > sigma_max(&kappa_matrix(R), LAM),
        "the fix certifies on strictly more regimes"
    );
}

#[test]
fn step_matches_python() {
    let z = [1.0, 0.0, 0.0, 0.0];
    let s = [0.1, 0.2, 0.3, 0.4];
    let out = lie_step(&z, &s, &kappa_skew(R), LAM, DT);
    for (got, want) in out.iter().zip(STEP_SKEW.iter()) {
        assert!(close(*got, *want), "step parity: got {got} want {want}");
    }
}

#[test]
fn remediation_is_hollow_and_skew() {
    let k = kappa_skew(R);
    assert!(skew_residual(&k) < 1e-12, "max|κ+κᵀ| == 0 by construction");
    assert!(hollow_residual(&k) < 1e-12, "diagonal cancels");
    // the broken upstream κ is the recorded ghost: NOT skew (worst residual on the diagonal)
    assert!(close(skew_residual(&kappa_matrix(R)), SKEWRES_SIN), "the sin κ skew residual is the ghost");
    assert_eq!(kappa_skew_obligation(R).status, ObligationStatus::Closed);
}

#[test]
fn certify_decision_parity() {
    let sigma = sigma_between();

    let skew = certify(&kappa_skew(R), LAM, DT, sigma, 2000, 0);
    assert!(skew.cond, "skew κ satisfies the sufficient condition at this σ");
    assert!(close(skew.rho, RHO_SKEW), "ρ(skew) parity: {} vs {RHO_SKEW}", skew.rho);
    assert!(skew.max_ratio <= 1.0 + 1e-9, "the proven bound holds on every sample (no growth)");
    assert_eq!(skew.decision, CertDecision::ContractiveCert);

    let sin = certify(&kappa_matrix(R), LAM, DT, sigma, 2000, 0);
    assert!(!sin.cond, "sin κ fails the condition at the same σ");
    assert!(close(sin.rho, RHO_SIN), "ρ(sin) parity: {} vs {RHO_SIN}", sin.rho);
    assert_eq!(sin.decision, CertDecision::NotCertified);
}

#[test]
fn certificate_refuses_outside_its_margin() {
    // push σ above the skew margin ⇒ the sufficient condition fails ⇒ NOT_CERTIFIED (honest boundary, not a clamp)
    let over = sigma_max(&kappa_skew(R), LAM) * 2.0;
    let r = certify(&kappa_skew(R), LAM, DT, over, 2000, 0);
    assert!(!r.cond, "σ beyond σ_max breaks 2‖κ‖_F·σ < λ");
    assert_eq!(r.decision, CertDecision::NotCertified);
}

#[test]
fn obligation_grades_track_the_decision() {
    let sigma = sigma_between();
    let skew = contraction_obligation(&certify(&kappa_skew(R), LAM, DT, sigma, 2000, 0));
    assert_eq!(skew.status, ObligationStatus::Closed);
    let sin = contraction_obligation(&certify(&kappa_matrix(R), LAM, DT, sigma, 2000, 0));
    assert_eq!(sin.status, ObligationStatus::Underdetermined);
}
