// SPDX-License-Identifier: AGPL-3.0-only
//! The graded claim ledger. `Grade` is an enum, so an off-ladder grade is *unrepresentable* — a Rust
//! strengthening of the Python string ladder. A claim must carry the boundary it does NOT establish and the
//! observation that would falsify it; `audit_ledger` refuses a ledger missing either. `grade ≠ truth`;
//! `honest ≠ true`.

use std::collections::BTreeMap;

use crate::artifacts::{AnalysisResult, Finding, Limitation};
use crate::epistemic_types::Grounding;

/// The epistemic ladder. SUPPORTED = {Established, Measured}.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Grade {
    Established,
    Measured,
    Underdetermined,
    Speculative,
    NotMeasured,
}

impl Grade {
    pub const ALL: [Grade; 5] = [
        Grade::Established,
        Grade::Measured,
        Grade::Underdetermined,
        Grade::Speculative,
        Grade::NotMeasured,
    ];

    pub fn as_str(&self) -> &'static str {
        match self {
            Grade::Established => "ESTABLISHED",
            Grade::Measured => "MEASURED",
            Grade::Underdetermined => "UNDERDETERMINED",
            Grade::Speculative => "SPECULATIVE",
            Grade::NotMeasured => "NOT_MEASURED",
        }
    }

    /// Grades that assert a claim is currently supported.
    pub fn supported(&self) -> bool {
        matches!(self, Grade::Established | Grade::Measured)
    }
}

/// A graded, falsifiable claim. `does_not_show` and `falsifier` are REQUIRED to be non-empty for the ledger
/// to audit as honest.
#[derive(Debug, Clone)]
pub struct Claim {
    pub id: String,
    pub statement: String,
    pub grade: Grade,
    pub mechanism: String,
    pub does_not_show: String,
    pub falsifier: String,
    pub quantity: String,
}

impl Claim {
    pub fn new(
        id: impl Into<String>,
        statement: impl Into<String>,
        grade: Grade,
        mechanism: impl Into<String>,
        does_not_show: impl Into<String>,
        falsifier: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            statement: statement.into(),
            grade,
            mechanism: mechanism.into(),
            does_not_show: does_not_show.into(),
            falsifier: falsifier.into(),
            quantity: String::new(),
        }
    }

    pub fn with_quantity(mut self, q: impl Into<String>) -> Self {
        self.quantity = q.into();
        self
    }

    /// Project into the shared honesty contract. Always honest by construction (scope + 2 limitations).
    pub fn as_analysis(&self) -> AnalysisResult {
        AnalysisResult::new(
            "claim",
            vec![
                Finding::new("CLAIM", "claim", self.statement.clone()),
                Finding::new("GRADE", "claim", self.grade.as_str()),
                Finding::new("MECHANISM", "claim", self.mechanism.clone()),
            ],
            vec![
                Limitation::new("claim", format!("does not show: {}", self.does_not_show)),
                Limitation::new("claim", format!("falsifier: {}", self.falsifier)),
            ],
        )
        .expect("claim as_analysis always satisfies the honesty contract")
    }
}

/// The result of auditing a ledger. `honest` requires every claim to carry both boundary fields. Grades are
/// on-ladder by construction (the `Grade` enum), so there is no off-ladder failure mode to check.
#[derive(Debug, Clone)]
pub struct LedgerAudit {
    pub honest: bool,
    pub counts: BTreeMap<&'static str, usize>,
    pub missing_boundary: Vec<String>,
}

pub fn grade_counts(claims: &[Claim]) -> BTreeMap<&'static str, usize> {
    let mut counts: BTreeMap<&'static str, usize> = BTreeMap::new();
    for g in Grade::ALL {
        counts.insert(g.as_str(), 0);
    }
    for c in claims {
        *counts.get_mut(c.grade.as_str()).unwrap() += 1;
    }
    counts
}

pub fn audit_ledger(claims: &[Claim]) -> LedgerAudit {
    let missing: Vec<String> = claims
        .iter()
        .filter(|c| c.does_not_show.trim().is_empty() || c.falsifier.trim().is_empty())
        .map(|c| c.id.clone())
        .collect();
    LedgerAudit { honest: missing.is_empty(), counts: grade_counts(claims), missing_boundary: missing }
}

/// Grounded iff the wrapped claim is graded ESTABLISHED/MEASURED on the ladder.
pub struct SupportedClaim<'a> {
    pub claim: &'a Claim,
}

impl<'a> Grounding for SupportedClaim<'a> {
    fn is_grounded(&self) -> bool {
        self.claim.grade.supported()
    }
    fn label(&self) -> String {
        format!("claim-grade={}", self.claim.grade.as_str())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn good(id: &str, g: Grade) -> Claim {
        Claim::new(id, "stmt", g, "mech", "the boundary", "a failing observation")
    }

    #[test]
    fn honest_ledger_passes() {
        let ledger = vec![good("A", Grade::Established), good("B", Grade::Measured)];
        assert!(audit_ledger(&ledger).honest);
    }

    #[test]
    fn missing_falsifier_is_dishonest() {
        let bad = Claim::new("X", "stmt", Grade::Measured, "mech", "boundary", "");
        let a = audit_ledger(&[bad]);
        assert!(!a.honest);
        assert_eq!(a.missing_boundary, vec!["X".to_string()]);
    }

    #[test]
    fn supported_claim_grounds_only_when_supported() {
        let est = good("A", Grade::Established);
        let spec = good("B", Grade::Speculative);
        assert!(SupportedClaim { claim: &est }.is_grounded());
        assert!(!SupportedClaim { claim: &spec }.is_grounded());
    }
}
