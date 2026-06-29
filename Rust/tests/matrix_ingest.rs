// SPDX-License-Identifier: AGPL-3.0-only
//! Schema-C (dense κ-block) ingestion → L2 contraction certifier, end-to-end.
//!
//! Proven here:
//!   1. **Byte-layout parity** — a Python-`struct`-packed 160-byte record (`<Q` frame + 16 κ row-major + λ,dt,σ)
//!      decodes to the exact matrix + scalars.
//!   2. **`ingested ≡ constructed`** — packing `kappa_skew(4)` (remediated) and `kappa_matrix(4)` (un-remediated)
//!      into Schema-C bytes, parsing, assembling, and certifying reproduces the Python-confirmed Frobenius norms
//!      and contraction factors (~1e-9) AND the decision (skew → CONTRACTIVE_CERT, sin → NOT_CERTIFIED). The
//!      byte path adds zero mathematical distortion.
//!   3. **Fail-closed** — a trailing partial record or a non-finite κ entry blocks; a stream with ANY
//!      un-certified block blocks. `parsed ≠ validated`; `certificate ≠ proof-of-everything`.

use ursprung::{
    certify, kappa_input_from_row, kappa_matrix, kappa_skew, parse_frames, run_cert_streaming, sigma_max,
    CertDecision, SCHEMA_KAPPA,
};

const LAM: f64 = 0.5;
const DT: f64 = 0.1;

// Python reference values (R=4, lam=0.5, dt=0.1) — same as tests/contraction_cert.rs:
const FROB_SIN: f64 = 2.846791627455805;
const FROB_SKEW: f64 = 2.3767220276469088;
const RHO_SKEW: f64 = 0.9958719353106553;
const RHO_SIN: f64 = 1.004944515958754;

// A Python-packed Schema-C record: struct.pack('<Q'+'d'*19, frame=1, *kappa_skew(4) row-major, lam, dt, sigma).
const KAPPA_C_SKEW_HEX: &str = "01000000000000000000000000000000ef367e9de779efbfe0d1a7c3b1eca3bf23ef34e8ad64eb3fef367e9de779ef3f0000000000000000777afa85d470ebbfc8378f036301a0bfe0d1a7c3b1eca33f777afa85d470eb3f0000000000000000984b6db320e3e3bf23ef34e8ad64ebbfc8378f036301a03f984b6db320e3e33f0000000000000000000000000000e03f9a9999999999b93f6ffc3eb463b4b83f";

fn hx(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

fn close(a: f64, b: f64) -> bool {
    (a - b).abs() <= 1e-9 * (1.0 + b.abs())
}

fn sigma_between() -> f64 {
    (sigma_max(&kappa_matrix(4), LAM) + sigma_max(&kappa_skew(4), LAM)) / 2.0
}

/// Pack a κ block into a Schema-C byte record (frame u64 + 16 κ row-major f64 + λ,dt,σ f64).
fn pack_kappa(frame: u64, k: &[Vec<f64>], lam: f64, dt: f64, sigma: f64) -> Vec<u8> {
    let mut b = Vec::with_capacity(160);
    b.extend_from_slice(&frame.to_le_bytes());
    for row in k.iter() {
        for &v in row.iter() {
            b.extend_from_slice(&v.to_le_bytes());
        }
    }
    b.extend_from_slice(&lam.to_le_bytes());
    b.extend_from_slice(&dt.to_le_bytes());
    b.extend_from_slice(&sigma.to_le_bytes());
    b
}

#[test]
fn schema_c_byte_layout_matches_python() {
    let bytes = hx(KAPPA_C_SKEW_HEX);
    assert_eq!(bytes.len(), 160, "one κ block is 160 bytes");
    let (rows, rep) = parse_frames(&bytes, &SCHEMA_KAPPA, 0);
    assert_eq!(rep.n_records, 1);
    assert_eq!(rep.rec_size, 160);
    assert!(!rep.layout_mismatch);
    let (kappa, lam, dt, sigma) = kappa_input_from_row(&rows[0], &SCHEMA_KAPPA).unwrap();
    let want = kappa_skew(4);
    for i in 0..4 {
        for j in 0..4 {
            assert!(close(kappa[i][j], want[i][j]), "κ[{i}][{j}] layout parity");
        }
    }
    assert!(close(lam, LAM) && close(dt, DT) && close(sigma, sigma_between()), "scalars decode in order");
}

#[test]
fn ingested_skew_certifies() {
    let bytes = pack_kappa(1, &kappa_skew(4), LAM, DT, sigma_between());
    let (rows, _) = parse_frames(&bytes, &SCHEMA_KAPPA, 0);
    let (kappa, lam, dt, sigma) = kappa_input_from_row(&rows[0], &SCHEMA_KAPPA).unwrap();
    let r = certify(&kappa, lam, dt, sigma, 2000, 0);
    assert_eq!(r.decision, CertDecision::ContractiveCert);
    assert!(close(r.frob, FROB_SKEW), "frob(skew) through the byte path");
    assert!(close(r.rho, RHO_SKEW), "ρ(skew) through the byte path");
}

#[test]
fn ingested_sin_not_certified() {
    let bytes = pack_kappa(1, &kappa_matrix(4), LAM, DT, sigma_between());
    let (rows, _) = parse_frames(&bytes, &SCHEMA_KAPPA, 0);
    let (kappa, lam, dt, sigma) = kappa_input_from_row(&rows[0], &SCHEMA_KAPPA).unwrap();
    let r = certify(&kappa, lam, dt, sigma, 2000, 0);
    assert_eq!(r.decision, CertDecision::NotCertified, "the un-remediated κ fails the margin");
    assert!(close(r.frob, FROB_SIN));
    assert!(close(r.rho, RHO_SIN));
}

#[test]
fn ingested_equals_constructed_cert() {
    // certifying the ingested κ is bit-identical to certifying the in-memory κ (f64 round-trips; deterministic)
    let k = kappa_skew(4);
    let sigma = sigma_between();
    let direct = certify(&k, LAM, DT, sigma, 1500, 7);

    let bytes = pack_kappa(42, &k, LAM, DT, sigma);
    let (rows, _) = parse_frames(&bytes, &SCHEMA_KAPPA, 0);
    let (kappa, lam, dt, sg) = kappa_input_from_row(&rows[0], &SCHEMA_KAPPA).unwrap();
    let ingested = certify(&kappa, lam, dt, sg, 1500, 7);

    assert_eq!(ingested.decision, direct.decision);
    assert_eq!(ingested.frob.to_bits(), direct.frob.to_bits(), "frob is bit-identical");
    assert_eq!(ingested.rho.to_bits(), direct.rho.to_bits(), "ρ is bit-identical");
    assert_eq!(ingested.max_ratio.to_bits(), direct.max_ratio.to_bits(), "sampled max is bit-identical");
}

#[test]
fn gate_passes_skew_blocks_sin() {
    let sigma = sigma_between();

    let skew = pack_kappa(1, &kappa_skew(4), LAM, DT, sigma);
    let r = run_cert_streaming(&skew[..], &SCHEMA_KAPPA, 0, 512, 0).unwrap();
    assert!(r.ok, "a certified κ block ⇒ PASS; reasons={:?}", r.reasons);
    assert_eq!(r.n_certified, 1);

    let sin = pack_kappa(1, &kappa_matrix(4), LAM, DT, sigma);
    let r = run_cert_streaming(&sin[..], &SCHEMA_KAPPA, 0, 512, 0).unwrap();
    assert!(!r.ok, "an un-certified κ block ⇒ BLOCKED");
    assert!(r.reasons.iter().any(|s| s.contains("NOT_CERTIFIED")));

    // a mixed stream fails closed if ANY block fails
    let mut mixed = pack_kappa(1, &kappa_skew(4), LAM, DT, sigma);
    mixed.extend(pack_kappa(2, &kappa_matrix(4), LAM, DT, sigma));
    let r = run_cert_streaming(&mixed[..], &SCHEMA_KAPPA, 0, 512, 0).unwrap();
    assert!(!r.ok);
    assert_eq!(r.parse.n_records, 2);
    assert_eq!(r.n_certified, 1, "only the skew block certifies");
}

#[test]
fn gate_fails_closed_on_trailing_partial() {
    let mut bytes = pack_kappa(1, &kappa_skew(4), LAM, DT, sigma_between());
    bytes.push(0xAB); // stray byte ⇒ the stream no longer divides the 160-byte record
    let r = run_cert_streaming(&bytes[..], &SCHEMA_KAPPA, 0, 512, 0).unwrap();
    assert!(!r.ok, "a truncated κ dump fails closed");
    assert!(r.parse.layout_mismatch);
    assert_eq!(r.parse.leftover_bytes, 1);
}

#[test]
fn gate_fails_closed_on_nonfinite() {
    let mut k = kappa_skew(4);
    k[0][0] = f64::NAN; // a corrupt κ entry
    let bytes = pack_kappa(1, &k, LAM, DT, sigma_between());
    let r = run_cert_streaming(&bytes[..], &SCHEMA_KAPPA, 0, 512, 0).unwrap();
    assert!(!r.ok, "a non-finite κ entry fails closed");
    assert!(r.parse.nonfinite >= 1);
}
