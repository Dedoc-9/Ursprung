// SPDX-License-Identifier: AGPL-3.0-only
//! Differential test for the obligation lift (Sub-Slice 1B) vs the Python reference
//! (`DVSM/commercial/binframe_adapter.py::lift` + `DVSM/invariant_ledger.py`). The same Python-`struct`-packed
//! fixtures from 1A are parsed, then lifted; the obligation profile, statuses, and non-liftable boundary flags
//! must match the Python verdicts (confirmed: TELEM → BOUNDED + UNDERDETERMINED; ABI → BOUNDED + CLOSED; both
//! declare the two Ω→V / ν→λ air-gaps non-liftable). `undetected ≠ absent`; `reference-model ≠ kernel`.

use ursprung::binframe_adapter::{
    containment, lift, parse_frames, replay_parity, Field, SCHEMA_ABI, SCHEMA_TELEM, U_MAX_DEFAULT,
};
use ursprung::claim_ledger::{audit_ledger, Grade};
use ursprung::invariant_ledger::ObligationStatus;

const TELEM_HEX: &str = "0100000000000000000020400000003f0000a03f0000404000000000000080400000c0bf0000403f020100000200000000000000000000400000803e0000803f00006040cdcccc3d00009040000080bf0000003f00010100";
const ABI_HEX: &str = "0a000000000000000000000000001440000000000000f03f0000000000000040010115cd5b07000000000b000000000000000000000000001840000000000000f83f00000000000004400000b168de3a00000000";

fn hx(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

#[test]
fn telem_lift_matches_python() {
    let (rows, _) = parse_frames(&hx(TELEM_HEX), &SCHEMA_TELEM, 0);
    let (obs, notlift) = lift(&rows, &SCHEMA_TELEM, U_MAX_DEFAULT, None);
    assert_eq!(obs.len(), 2);
    assert_eq!(obs[0].id, "DVSM-3-kernel");
    assert_eq!(obs[0].status, ObligationStatus::Bounded); // max energy 2.5 < 100
    assert_eq!(obs[1].id, "DVSM-6-kernel");
    assert_eq!(obs[1].status, ObligationStatus::Underdetermined); // no hash field in TELEM
    // both air-gap checks are non-liftable (no v / lambda_eff in the public frame)
    assert_eq!(notlift.len(), 2);
    assert!(notlift.iter().any(|(id, _)| id.starts_with("DVSM-7")));
    assert!(notlift.iter().any(|(id, _)| id.starts_with("DVSM-4")));
}

#[test]
fn abi_lift_matches_python() {
    let (rows, _) = parse_frames(&hx(ABI_HEX), &SCHEMA_ABI, 0);
    let rs = rows.as_slice();
    let (obs, notlift) = lift(rs, &SCHEMA_ABI, U_MAX_DEFAULT, Some(rs)); // rows_b = self ⇒ identical hashes
    assert_eq!(obs.len(), 2);
    assert_eq!(obs[0].id, "DVSM-3-kernel");
    assert_eq!(obs[0].status, ObligationStatus::Bounded); // max energy 6.0 < 100
    assert_eq!(obs[1].id, "DVSM-6-kernel");
    assert_eq!(obs[1].status, ObligationStatus::Closed); // identical replay-hash sequence
    assert_eq!(notlift.len(), 2);
}

#[test]
fn containment_violation_on_low_bound() {
    let (rows, _) = parse_frames(&hx(ABI_HEX), &SCHEMA_ABI, 0);
    let o = containment(&rows, 1.0); // max energy 6.0 ≥ 1.0
    assert_eq!(o.status, ObligationStatus::Violated);
}

#[test]
fn replay_parity_closed_then_violated() {
    let (rows, _) = parse_frames(&hx(ABI_HEX), &SCHEMA_ABI, 0);
    assert_eq!(replay_parity(&rows, &rows).status, ObligationStatus::Closed);
    let mut rb = rows.clone();
    for kv in rb[0].iter_mut() {
        if kv.0 == "hash" {
            kv.1 = Field::U64(999); // perturb one hash ⇒ sequences diverge
        }
    }
    assert_eq!(replay_parity(&rows, &rb).status, ObligationStatus::Violated);
}

#[test]
fn obligation_projects_to_honest_claim_and_analysis() {
    let (rows, _) = parse_frames(&hx(ABI_HEX), &SCHEMA_ABI, 0);
    let o = containment(&rows, U_MAX_DEFAULT); // Bounded
    // status → grade: BOUNDED ⇒ MEASURED
    let claim = o.as_claim();
    assert_eq!(claim.grade, Grade::Measured);
    assert!(audit_ledger(&[claim]).honest, "the obligation's claim carries both boundary fields");
    // as_analysis is honest by construction (scope + ≥1 limitation)
    let an = o.as_analysis();
    assert_eq!(an.scope(), "manifest-invariant");
    assert!(!an.limitations().is_empty());
}
