// SPDX-License-Identifier: AGPL-3.0-only
//! commercial_obligations — the proof-gated buyer-facing claims ledger (gateway layer 4), over the validated
//! [`crate::claim_ledger`] substrate. A sales claim is honest only if a *discharged* technical obligation backs
//! it. The ledger audits honest iff:
//!   (a) every claim carries a non-empty `does_not_show` and `falsifier` (via `claim_ledger::audit_ledger`);
//!   (b) no SUPPORTED (Established/Measured) claim rests on an UNDISCHARGED obligation (`exceeds_proof`);
//!   (c) no SUPPORTED claim contains hype-lexicon language (`hype`);
//!   (d) every `rests_on` names a known obligation — discharged or open/rejected (`unknown_obligation`).
//!
//! `claim ≠ proof`; `grade ≠ truth`.
//!
//! ## SINGLE SOURCE OF TRUTH (mirror → source, resolved)
//! `shipped_ledger()` is loaded from the SAME manifests the Python reads — `DVSM/commercial/ledger.tsv` and
//! `obligations.tsv` — embedded at compile time via `include_str!`. There is now ONE source for the ledger
//! across both languages; editing the manifest updates both. The earlier `mirror ≠ source` drift risk is
//! closed by construction (no hand-duplicated claim data here).
//!
//! ## LOAD-BEARING `does_not_show`
//! `static-check ≠ live-execution`. This gate verifies that a claim *names* a discharged obligation; it does
//! NOT execute that obligation's test, nor confirm it passed in this build. Binding `discharged` to a live run
//! is a separate OPEN obligation (Obligation B).

use crate::claim_ledger::{audit_ledger, Claim, Grade};
use std::collections::{BTreeMap, BTreeSet};

/// Hype lexicon — banned from any SUPPORTED claim. Semantic inflation the product treats as a defect.
pub const HYPE: &[&str] = &[
    "guarantee", "guaranteed", "100%", "unhackable", "proves your", "certified safe", "bug-free",
    "prevents all", "eliminates all", "fully secure", "provably safe", "zero risk",
];

/// A buyer-facing claim. `rests_on` MUST name an obligation key; a SUPPORTED grade is honest only when that
/// key is discharged. Boundary claims (what is explicitly NOT sold) rest on an open/rejected key at a
/// non-supported grade.
#[derive(Debug, Clone)]
pub struct CommercialClaim {
    pub id: String,
    pub statement: String,
    pub grade: Grade,
    pub rests_on: String,
    pub does_not_show: String,
    pub falsifier: String,
    pub tier: String, // "open-core" (AGPL-3.0) | "commercial" (paid license)
}

impl CommercialClaim {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        id: impl Into<String>,
        statement: impl Into<String>,
        grade: Grade,
        rests_on: impl Into<String>,
        does_not_show: impl Into<String>,
        falsifier: impl Into<String>,
        tier: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            statement: statement.into(),
            grade,
            rests_on: rests_on.into(),
            does_not_show: does_not_show.into(),
            falsifier: falsifier.into(),
            tier: tier.into(),
        }
    }

    fn to_claim(&self) -> Claim {
        Claim::new(
            self.id.clone(),
            self.statement.clone(),
            self.grade,
            format!("rests_on={}", self.rests_on),
            self.does_not_show.clone(),
            self.falsifier.clone(),
        )
    }
}

/// The audit verdict — mirrors the Python `audit_commercial_ledger` dict (independent lists, claim order).
#[derive(Debug, Clone)]
pub struct CommercialAudit {
    pub honest: bool,
    pub exceeds_proof: Vec<String>,
    pub hype: Vec<String>,
    pub unknown_obligation: Vec<String>,
    pub missing_boundary: Vec<String>,
    /// SUPPORTED claims whose backing suite did not read PASS in a supplied live receipt (empty for a static
    /// audit). Obligation B; `receipt ≠ proof`.
    pub unverified_live: Vec<String>,
}

/// The proof-gated commercial ledger.
pub struct CommercialLedger {
    pub claims: Vec<CommercialClaim>,
    pub discharged: BTreeSet<String>,
    pub open_or_rejected: BTreeSet<String>,
    /// obligation key → the verify.py suite stem that discharges it (from the `suite` column of obligations.tsv).
    pub suite_of: BTreeMap<String, String>,
}

impl CommercialLedger {
    /// STATIC audit: boundary fields present (via `claim_ledger::audit_ledger`); no SUPPORTED claim rests on an
    /// undischarged obligation; no SUPPORTED claim contains hype; every `rests_on` is a known key.
    /// `unverified_live` is empty (no receipt consulted).
    pub fn audit(&self) -> CommercialAudit {
        self.audit_opt(None)
    }

    /// LIVE audit (Obligation B, Rust-side): the static checks PLUS — each SUPPORTED claim's backing suite
    /// (`suite_of`) must read `PASS` in `receipts`, else it is `unverified_live`. HONEST CEILING:
    /// `receipt ≠ proof`; `tested ≠ safe` — this proves the suite ran AND passed in this build, not that it is
    /// correct; the receipt is a trusted, freshness-bounded build artifact.
    pub fn audit_live(&self, receipts: &BTreeMap<String, String>) -> CommercialAudit {
        self.audit_opt(Some(receipts))
    }

    fn audit_opt(&self, receipts: Option<&BTreeMap<String, String>>) -> CommercialAudit {
        let mapped: Vec<Claim> = self.claims.iter().map(|c| c.to_claim()).collect();
        let base = audit_ledger(&mapped);

        let mut exceeds_proof = Vec::new();
        let mut hype = Vec::new();
        let mut unknown_obligation = Vec::new();
        let mut unverified_live = Vec::new();
        for c in &self.claims {
            let supported = c.grade.supported();
            let discharged = self.discharged.contains(&c.rests_on);
            let open = self.open_or_rejected.contains(&c.rests_on);

            if supported && !discharged {
                exceeds_proof.push(c.id.clone());
            }
            if supported {
                let low = c.statement.to_lowercase();
                if HYPE.iter().any(|tok| low.contains(*tok)) {
                    hype.push(c.id.clone());
                }
            }
            if !discharged && !open {
                unknown_obligation.push(c.id.clone());
            }
            if supported {
                if let Some(r) = receipts {
                    let live_ok = self
                        .suite_of
                        .get(&c.rests_on)
                        .map(|s| r.get(s).map(|v| v == "PASS").unwrap_or(false))
                        .unwrap_or(false);
                    if !live_ok {
                        unverified_live.push(c.id.clone());
                    }
                }
            }
        }

        let honest = base.honest
            && exceeds_proof.is_empty()
            && hype.is_empty()
            && unknown_obligation.is_empty()
            && unverified_live.is_empty();
        CommercialAudit {
            honest,
            exceeds_proof,
            hype,
            unknown_obligation,
            missing_boundary: base.missing_boundary,
            unverified_live,
        }
    }
}

// ---- single-source manifest (the SAME files the Python loads) -------------------------------------
const LEDGER_TSV: &str = include_str!("../../DVSM/commercial/ledger.tsv");
const OBLIGATIONS_TSV: &str = include_str!("../../DVSM/commercial/obligations.tsv");

fn parse_grade(s: &str) -> Grade {
    match s {
        "ESTABLISHED" => Grade::Established,
        "MEASURED" => Grade::Measured,
        "UNDERDETERMINED" => Grade::Underdetermined,
        "SPECULATIVE" => Grade::Speculative,
        "NOT_MEASURED" => Grade::NotMeasured,
        other => panic!("unknown grade {other:?} in ledger.tsv"),
    }
}

/// Load the SHIPPED ledger from the single-source manifests embedded at compile time. `str::lines()` strips the
/// `\n`/`\r\n` terminators, so field content is taken verbatim between tabs.
pub fn shipped_ledger() -> CommercialLedger {
    let mut discharged = BTreeSet::new();
    let mut open_or_rejected = BTreeSet::new();
    let mut suite_of: BTreeMap<String, String> = BTreeMap::new();
    for line in OBLIGATIONS_TSV.lines() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let f: Vec<&str> = line.split('\t').collect();
        let key = f[0].to_string();
        match f[1] {
            "DISCHARGED" => {
                discharged.insert(key.clone());
            }
            "OPEN_OR_REJECTED" => {
                open_or_rejected.insert(key.clone());
            }
            other => panic!("unknown obligation status {other:?} in obligations.tsv"),
        }
        // column 2 (optional) = the verify.py suite stem that discharges this obligation ('-' if none)
        if f.len() > 2 && f[2] != "-" && !f[2].is_empty() {
            suite_of.insert(key, f[2].to_string());
        }
    }

    let mut claims = Vec::new();
    for line in LEDGER_TSV.lines() {
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let f: Vec<&str> = line.split('\t').collect();
        assert!(
            f.len() == 7,
            "ledger.tsv row needs 7 tab-separated fields, got {}: {:?}",
            f.len(),
            f
        );
        // columns: id  grade  tier  rests_on  statement  does_not_show  falsifier
        claims.push(CommercialClaim::new(f[0], f[4], parse_grade(f[1]), f[3], f[5], f[6], f[2]));
    }

    CommercialLedger { claims, discharged, open_or_rejected, suite_of }
}
