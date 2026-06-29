// SPDX-License-Identifier: AGPL-3.0-only
//! Schema-D (CMI sample) ingestion → L3 forbidden-coupling firewall, end-to-end.
//!
//! Two things are proven here:
//!   1. **Byte-layout parity** — a Python-`struct`-packed `<dddd` fixture decodes to the exact `x,y,z0,w0`
//!      values (the same little-endian f64 decode the TELEM/ABI fixtures already pin in `tests/binframe.rs`).
//!   2. **`ingested ≡ constructed`** — packing the *same* planted regimes used in `tests/coupling.rs`
//!      (airgap / contam / artifact) into Schema-D bytes, parsing them, assembling a `CouplingInput`, and
//!      running `audit_coupling` reproduces the in-memory verdict *and* CMI exactly (f64 round-trips through
//!      `to_le_bytes`/`from_le_bytes`; the audit is deterministic). The ingestion step adds no distortion.
//!
//! Plus the gate's fail-closed posture: a trailing partial record blocks; OBSERVER_CONTAMINATION blocks while
//! AIR_GAP_HELD passes. `decisions match, floats need not`; `residual-CMI ≠ channel`.

use ursprung::{
    audit_coupling, coupling_input_from_rows, parse_frames, read_frames_streaming, run_coupling_streaming,
    CouplingInput, CouplingVerdict, SCHEMA_CMI,
};

// Two samples packed by Python: struct.pack('<dddd', x, y, z0, w0) for (1.5,2.0,0.25,-1.0) and (0.0,-0.5,3.0,0.125).
const CMI_HEX: &str = "000000000000f83f0000000000000040000000000000d03f000000000000f0bf0000000000000000000000000000e0bf0000000000000840000000000000c03f";

fn hx(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

// ---- the SAME planted generators as tests/coupling.rs (mirrored so the verdicts are directly comparable) ----
const N: usize = 3645;
const REPS: usize = 60;
const SEED: u64 = 0;

fn jit(i: usize) -> f64 {
    i as f64 * 1e-7
}

fn gens(kind: &str) -> (Vec<f64>, Vec<f64>, Vec<Vec<f64>>, Vec<Vec<f64>>) {
    let (mut x, mut y, mut z, mut w) = (Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for i in 0..N {
        let g0 = (i % 3) as i64;
        let g1 = ((i / 3) % 3) as i64;
        let g2 = ((i / 9) % 3) as i64;
        let g3 = ((i / 27) % 3) as i64;
        let (xc, yc, zc, wc) = match kind {
            "airgap" => ((g0 + g1) % 3, (g0 + g2) % 3, g0, g3),
            "contam" => {
                let xc = (g0 + g1) % 3;
                (xc, xc, g0, g3)
            }
            "artifact" => {
                let ax = ((i / 81) % 3) as i64;
                let ay = ((i / 243) % 3) as i64;
                let xc = if ax != 0 { g3 } else { (g3 + 1) % 3 };
                let yc = if ay != 0 { g3 } else { (g3 + 2) % 3 };
                (xc, yc, g0, g3)
            }
            _ => unreachable!(),
        };
        x.push(xc as f64 + jit(i));
        y.push(yc as f64 + jit(i));
        z.push(zc as f64 + jit(i));
        w.push(wc as f64 + jit(i));
    }
    (x, y, vec![z], vec![w])
}

fn constructed(kind: &str, identifiable: bool) -> CouplingInput {
    let (x, y, z_dims, w_dims) = gens(kind);
    CouplingInput {
        name: kind.to_string(),
        manifest_rule: "test coupling".to_string(),
        note: if identifiable { String::new() } else { "flagged unidentifiable: diagnostic is a near-function of Z".to_string() },
        x,
        y,
        z_dims,
        w_dims,
        identifiable,
        reps: REPS,
        seed: SEED,
    }
}

/// Pack (x,y,z0,w0) columns into a Schema-D byte stream (little-endian f64, schema field order).
fn pack(x: &[f64], y: &[f64], z: &[Vec<f64>], w: &[Vec<f64>]) -> Vec<u8> {
    let mut b = Vec::with_capacity(x.len() * 32);
    for i in 0..x.len() {
        b.extend_from_slice(&x[i].to_le_bytes());
        b.extend_from_slice(&y[i].to_le_bytes());
        b.extend_from_slice(&z[0][i].to_le_bytes());
        b.extend_from_slice(&w[0][i].to_le_bytes());
    }
    b
}

fn pack_kind(kind: &str) -> Vec<u8> {
    let (x, y, z, w) = gens(kind);
    pack(&x, &y, &z, &w)
}

#[test]
fn schema_d_byte_layout_matches_python() {
    let bytes = hx(CMI_HEX);
    let (rows, rep) = parse_frames(&bytes, &SCHEMA_CMI, 0);
    assert_eq!(rep.n_records, 2);
    assert_eq!(rep.rec_size, 32);
    assert!(!rep.layout_mismatch);
    let inp = coupling_input_from_rows(&rows, &SCHEMA_CMI, "fixture", "rule", true, 4, 0).unwrap();
    assert_eq!(inp.x, vec![1.5, 0.0]);
    assert_eq!(inp.y, vec![2.0, -0.5]);
    assert_eq!(inp.z_dims, vec![vec![0.25, 3.0]]);
    assert_eq!(inp.w_dims, vec![vec![-1.0, 0.125]]);
}

/// The crux: bytes → rows → CouplingInput → audit reproduces the in-memory construction exactly.
fn assert_ingested_equals_constructed(kind: &str, expected: CouplingVerdict) {
    let direct = audit_coupling(&constructed(kind, true));
    assert_eq!(direct.verdict, expected, "in-memory verdict for {kind}");

    let bytes = pack_kind(kind);
    let (rows, rep) = parse_frames(&bytes, &SCHEMA_CMI, 0);
    assert_eq!(rep.n_records, N, "all {N} samples parse for {kind}");
    assert!(!rep.layout_mismatch && rep.nonfinite == 0);
    let inp = coupling_input_from_rows(&rows, &SCHEMA_CMI, kind, "test coupling", true, REPS, SEED).unwrap();
    let ingested = audit_coupling(&inp);

    assert_eq!(ingested.verdict, direct.verdict, "ingested verdict must equal constructed for {kind}");
    assert!(
        (ingested.cmi - direct.cmi).abs() < 1e-12,
        "ingested CMI {} must equal constructed {} for {kind}",
        ingested.cmi,
        direct.cmi
    );
}

#[test]
fn ingested_equals_constructed_airgap() {
    assert_ingested_equals_constructed("airgap", CouplingVerdict::AirGapHeld);
}

#[test]
fn ingested_equals_constructed_contam() {
    assert_ingested_equals_constructed("contam", CouplingVerdict::ObserverContamination);
}

#[test]
fn ingested_equals_constructed_artifact() {
    assert_ingested_equals_constructed("artifact", CouplingVerdict::ConfoundedArtifact);
}

#[test]
fn gate_passes_airgap_blocks_contamination() {
    let air = pack_kind("airgap");
    let r = run_coupling_streaming(&air[..], &SCHEMA_CMI, 0, "airgap", "rule", true, REPS, SEED).unwrap();
    assert!(r.ok, "AIR_GAP_HELD ⇒ gate PASS; reasons={:?}", r.reasons);
    assert_eq!(r.result.as_ref().unwrap().verdict, CouplingVerdict::AirGapHeld);

    let con = pack_kind("contam");
    let r = run_coupling_streaming(&con[..], &SCHEMA_CMI, 0, "contam", "rule", true, REPS, SEED).unwrap();
    assert!(!r.ok, "OBSERVER_CONTAMINATION ⇒ gate BLOCKED");
    assert!(r.reasons.iter().any(|s| s.contains("DETECTED")));
}

#[test]
fn gate_passes_dissolved_artifact() {
    // a confounded artifact dissolves under (Z,W) ⇒ no real coupling ⇒ gate PASSes but reports the verdict
    let art = pack_kind("artifact");
    let r = run_coupling_streaming(&art[..], &SCHEMA_CMI, 0, "artifact", "rule", true, REPS, SEED).unwrap();
    assert!(r.ok, "dissolved artifact is not a detected coupling; reasons={:?}", r.reasons);
    assert_eq!(r.result.as_ref().unwrap().verdict, CouplingVerdict::ConfoundedArtifact);
}

#[test]
fn gate_fails_closed_on_trailing_partial() {
    let mut bytes = pack_kind("airgap");
    bytes.push(0xAB); // a stray byte ⇒ the stream no longer divides the 32-byte record
    let r = run_coupling_streaming(&bytes[..], &SCHEMA_CMI, 0, "airgap", "rule", true, REPS, SEED).unwrap();
    assert!(!r.ok, "a truncated dump must fail closed");
    assert!(r.parse.layout_mismatch);
    assert_eq!(r.parse.leftover_bytes, 1);
    assert!(r.result.is_none(), "no verdict is emitted on a parse anomaly");
}

#[test]
fn streaming_equals_whole_file_cmi() {
    // the assembled input (hence the verdict) is identical whether rows come from the whole-file or streamed parse
    let bytes = pack_kind("contam");
    let (rows_w, _) = parse_frames(&bytes, &SCHEMA_CMI, 0);
    let (rows_s, _) = read_frames_streaming(&bytes[..], &SCHEMA_CMI, 0).unwrap();
    assert_eq!(rows_w, rows_s);
    let a = audit_coupling(&coupling_input_from_rows(&rows_w, &SCHEMA_CMI, "c", "r", true, REPS, SEED).unwrap());
    let b = audit_coupling(&coupling_input_from_rows(&rows_s, &SCHEMA_CMI, "c", "r", true, REPS, SEED).unwrap());
    assert_eq!(a.verdict, b.verdict);
}
