// SPDX-License-Identifier: AGPL-3.0-only
//! ursprung-gateway integration test — the single-binary gate logic (`run_gateway`): clean dump ⇒ PASS;
//! a parse anomaly ⇒ BLOCKED; live binding honest with a fresh all-pass receipt ⇒ PASS; a missing backing
//! suite ⇒ BLOCKED. Fail-closed; `receipt ≠ proof`.

use std::collections::BTreeMap;

use ursprung::{render_report, run_gateway, shipped_ledger, SCHEMA_TELEM, U_MAX_DEFAULT};

// a clean 2-record TELEM dump (Python-`struct`-packed; see tests/binframe.rs)
const TELEM_HEX: &str = "0100000000000000000020400000003f0000a03f0000404000000000000080400000c0bf0000403f020100000200000000000000000000400000803e0000803f00006040cdcccc3d00009040000080bf0000003f00010100";

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

#[test]
fn report_is_disclaimer_first() {
    let report = run_gateway(&hx(TELEM_HEX), &SCHEMA_TELEM, U_MAX_DEFAULT, 0, None);
    let md = render_report(&report);
    assert!(md.contains("NOT a certification"), "report leads with the honest disclaimer");
    assert!(md.contains("verdict"));
    assert!(md.contains("parts ≠ whole"), "report states the scope boundary");
}
