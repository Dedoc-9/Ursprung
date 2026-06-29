// SPDX-License-Identifier: AGPL-3.0-only
//! Differential test for the proof-gated commercial gate vs the Python reference
//! (`DVSM/commercial/commercial_obligations.py`). The shipped ledger must audit honest exactly as the Python
//! does (user-confirmed 9/9), and each broken mutation must land in the same independent list Python uses
//! (`exceeds_proof` / `hype` / `unknown_obligation` / `missing_boundary`). `claim ≠ proof`; `grade ≠ truth`.

use ursprung::claim_ledger::Grade;
use ursprung::commercial_obligations::{shipped_ledger, CommercialClaim};

#[test]
fn shipped_ledger_is_honest() {
    let a = shipped_ledger().audit();
    assert!(a.honest, "shipped ledger must be honest (mirrors Python 9/9)");
    assert!(a.exceeds_proof.is_empty());
    assert!(a.hype.is_empty());
    assert!(a.unknown_obligation.is_empty());
    assert!(a.missing_boundary.is_empty());
}

#[test]
fn manifest_loads_single_source_ledger() {
    // shipped_ledger() is built from the SAME ledger.tsv / obligations.tsv the Python reads — verify the Rust
    // parser reproduces the expected shape (11 claims, 11 discharged + 4 open obligations).
    let led = shipped_ledger();
    assert_eq!(led.claims.len(), 11, "ledger.tsv holds C1-C8 + B1-B3");
    assert_eq!(led.discharged.len(), 11);
    assert_eq!(led.open_or_rejected.len(), 4);
    let ids: Vec<&str> = led.claims.iter().map(|c| c.id.as_str()).collect();
    for want in ["C1", "C7", "C8", "B1", "B3"] {
        assert!(ids.contains(&want), "manifest must load claim {want}");
    }
}

#[test]
fn boundary_negation_is_not_flagged_as_hype() {
    // B1's statement literally contains "guarantee" ("We do NOT guarantee ...") — but it is NOT_MEASURED, and
    // the hype scan is grade-gated to SUPPORTED claims, so the ledger stays honest. This is the load-bearing
    // distinction between a boundary disclaimer and an inflated value-prop.
    let led = shipped_ledger();
    let b1 = led.claims.iter().find(|c| c.id == "B1").expect("B1 present");
    assert!(b1.statement.to_lowercase().contains("guarantee"), "B1 negates a hype word on purpose");
    assert!(!b1.grade.supported(), "B1 is a non-supported boundary claim");
    assert!(led.audit().honest, "a negated hype word in a boundary claim does not break the gate");
}

#[test]
fn hype_in_a_supported_claim_is_caught() {
    let mut led = shipped_ledger();
    led.claims.push(CommercialClaim::new(
        "XH", "This kernel module is 100% unhackable and provably safe.", Grade::Established,
        "kappa.remediated_skew", "boundary", "falsifier", "commercial",
    ));
    let a = led.audit();
    assert!(!a.honest);
    assert!(a.hype.contains(&"XH".to_string()), "hype list must flag XH; got {:?}", a.hype);
    assert!(a.exceeds_proof.is_empty(), "XH rests on a discharged key, so it does not exceed proof");
}

#[test]
fn supported_claim_on_open_obligation_exceeds_proof() {
    let mut led = shipped_ledger();
    led.claims.push(CommercialClaim::new(
        "XE", "Clean statement regarding system boundedness.", Grade::Established,
        "kernel.boundedness", "boundary", "falsifier", "open-core", // an OPEN/REJECTED key
    ));
    let a = led.audit();
    assert!(!a.honest);
    assert!(a.exceeds_proof.contains(&"XE".to_string()), "supported claim on an open key exceeds proof");
    assert!(a.unknown_obligation.is_empty(), "the key IS known (open/rejected), so not 'unknown'");
}

#[test]
fn unknown_obligation_reference_is_caught() {
    let mut led = shipped_ledger();
    // non-supported grade isolates the 'unknown' list (a supported grade would also trip exceeds_proof)
    led.claims.push(CommercialClaim::new(
        "XU", "Clean statement.", Grade::Speculative,
        "does.not.exist", "boundary", "falsifier", "open-core",
    ));
    let a = led.audit();
    assert!(!a.honest);
    assert!(a.unknown_obligation.contains(&"XU".to_string()), "an unregistered key must be flagged unknown");
    assert!(a.exceeds_proof.is_empty(), "non-supported grade does not exceed proof");
}

#[test]
fn missing_boundary_field_is_caught() {
    let mut led = shipped_ledger();
    led.claims.push(CommercialClaim::new(
        "XM", "Clean statement.", Grade::Measured,
        "auditor.custom_probe", "", "falsifier", "commercial", // empty does_not_show
    ));
    let a = led.audit();
    assert!(!a.honest);
    assert!(a.missing_boundary.contains(&"XM".to_string()), "a claim missing its boundary field is caught");
}
