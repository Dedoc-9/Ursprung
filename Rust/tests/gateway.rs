// SPDX-License-Identifier: AGPL-3.0-only
//! ursprung-gateway integration test — the single-binary gate logic (`run_gateway`): clean dump ⇒ PASS;
//! a parse anomaly ⇒ BLOCKED; live binding honest with a fresh all-pass receipt ⇒ PASS; a missing backing
//! suite ⇒ BLOCKED. Fail-closed; `receipt ≠ proof`.

use std::collections::BTreeMap;

use ursprung::{
    render_report, run_gateway, run_gateway_streaming, shipped_ledger, GatewayReport, Schema, SCHEMA_ABI,
    SCHEMA_TELEM, U_MAX_DEFAULT,
};

// a clean 2-record TELEM dump (Python-`struct`-packed; see tests/binframe.rs)
const TELEM_HEX: &str = "0100000000000000000020400000003f0000a03f0000404000000000000080400000c0bf0000403f020100000200000000000000000000400000803e0000803f00006040cdcccc3d00009040000080bf0000003f00010100";
const ABI_HEX: &str = "0a000000000000000000000000001440000000000000f03f0000000000000040010115cd5b07000000000b000000000000000000000000001840000000000000f83f00000000000004400000b168de3a00000000";

fn hx(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

/// A fresh receipt where every SUPPORTED claim's backing suite reads PASS.
fn all_pass_receipt() -> BTreeMap<String, String> {
    let led = shipped_ledger();
    let mut r = BTreeMap::new();
    for c in &led.claims {
        if c.grade.supported() {
            if let Some(s) = led.suite_of.get(&c.rests_on) {
                r.insert(s.clone(), "PASS".to_string());
            }
        }
    }
    r
}

#[test]
fn passes_clean_telem_static() {
    let report = run_gateway(&hx(TELEM_HEX), &SCHEMA_TELEM, U_MAX_DEFAULT, 0, None);
    assert!(report.ok, "clean dump + honest static ledger ⇒ PASS; reasons={:?}", report.reasons);
    assert!(!report.live_enforced, "no receipt ⇒ live binding not enforced");
    assert_eq!(report.parse.n_records, 2);
}

#[test]
fn blocks_on_layout_mismatch() {
    let mut bytes = hx(TELEM_HEX);
    bytes.push(0xAB); // a stray byte ⇒ the stream no longer divides the record size
    let report = run_gateway(&bytes, &SCHEMA_TELEM, U_MAX_DEFAULT, 0, None);
    assert!(!report.ok, "a parse anomaly must block (fail-closed)");
    assert!(report.parse.layout_mismatch);
    assert!(report.reasons.iter().any(|r| r.contains("layout_mismatch")));
}

#[test]
fn live_pass_with_fresh_all_pass_receipt() {
    let r = all_pass_receipt();
    let report = run_gateway(&hx(TELEM_HEX), &SCHEMA_TELEM, U_MAX_DEFAULT, 0, Some(&r));
    assert!(report.live_enforced);
    assert!(report.commercial.honest, "all backing suites PASS ⇒ live-honest");
    assert!(report.commercial.unverified_live.is_empty());
    assert!(report.ok);
}

#[test]
fn live_blocks_on_missing_backing_suite() {
    let mut r = all_pass_receipt();
    r.remove("test_coupling_audit"); // a backing suite (C1, C6) that did not PASS this build
    let report = run_gateway(&hx(TELEM_HEX), &SCHEMA_TELEM, U_MAX_DEFAULT, 0, Some(&r));
    assert!(!report.ok, "a supported claim whose backing suite did not pass ⇒ BLOCKED");
    assert!(!report.commercial.unverified_live.is_empty());
}

/// Assert the streaming gate and the whole-file gate agree on every observable field — the binary now uses the
/// streaming path, so this is the guarantee that rewiring it changed memory behaviour, NOT the verdict.
/// `streaming ≡ whole-file`.
fn assert_reports_equal(w: &GatewayReport, s: &GatewayReport) {
    assert_eq!(w.ok, s.ok, "verdict differs");
    assert_eq!(w.reasons, s.reasons, "block reasons differ");
    assert_eq!(w.schema, s.schema);
    assert_eq!(w.parse, s.parse, "ParseReport differs");
    assert_eq!(w.live_enforced, s.live_enforced);
    assert_eq!(w.commercial.honest, s.commercial.honest);
    assert_eq!(w.non_liftable, s.non_liftable, "non-liftable set differs");
    let key = |o: &GatewayReport| -> Vec<(String, String, String)> {
        o.obligations
            .iter()
            .map(|x| (x.id.to_string(), x.status.as_str().to_string(), x.witness.clone()))
            .collect()
    };
    assert_eq!(key(w), key(s), "obligation id/status/witness differ");
}

fn run_both(hex: &str, schema: &'static Schema, recv: Option<&BTreeMap<String, String>>) {
    let bytes = hx(hex);
    let whole = run_gateway(&bytes, schema, U_MAX_DEFAULT, 0, recv);
    let streamed = run_gateway_streaming(&bytes[..], schema, U_MAX_DEFAULT, 0, recv).unwrap();
    assert_reports_equal(&whole, &streamed);
}

#[test]
fn streaming_gateway_equals_whole_file_telem() {
    run_both(TELEM_HEX, &SCHEMA_TELEM, None);
    run_both(TELEM_HEX, &SCHEMA_TELEM, Some(&all_pass_receipt()));
}

#[test]
fn streaming_gateway_equals_whole_file_abi() {
    // ABI carries the hash field ⇒ no UNDERDETERMINED no-hash obligation; exercises the other lift branch.
    run_both(ABI_HEX, &SCHEMA_ABI, None);
    run_both(ABI_HEX, &SCHEMA_ABI, Some(&all_pass_receipt()));
}

#[test]
fn streaming_gateway_blocks_on_trailing_partial() {
    // the binary's fail-closed path: a truncated trailing record ⇒ layout_mismatch ⇒ ok=false, same as whole-file
    let mut bytes = hx(TELEM_HEX);
    bytes.push(0xAB);
    let streamed = run_gateway_streaming(&bytes[..], &SCHEMA_TELEM, U_MAX_DEFAULT, 0, None).unwrap();
    assert!(!streamed.ok, "truncated dump must fail closed when streamed");
    assert!(streamed.parse.layout_mismatch);
    assert_eq!(streamed.parse.leftover_bytes, 1);
    assert_eq!(streamed.parse.n_records, 2);
}

#[test]
fn report_is_disclaimer_first() {
    let report = run_gateway(&hx(TELEM_HEX), &SCHEMA_TELEM, U_MAX_DEFAULT, 0, None);
    let md = render_report(&report);
    assert!(md.contains("NOT a certification"), "report leads with the honest disclaimer");
    assert!(md.contains("verdict"));
    assert!(md.contains("parts ≠ whole"), "report states the scope boundary");
}
