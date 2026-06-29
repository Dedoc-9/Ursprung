// SPDX-License-Identifier: AGPL-3.0-only
//! invariant_ledger — the obligation-result substrate, ported from `DVSM/invariant_ledger.py`. A manifest
//! invariant becomes a mechanically-checkable [`ObligationResult`] carrying its graded status, its witness, the
//! boundary it does NOT establish, and the observation that would falsify it.
//!
//! Status vocabulary (deliberately not binary; faithful to the Python — there is NO `OPEN` status here):
//!   * `CLOSED` — established over the checked domain (exact/structural, reference-relative);
//!   * `BOUNDED` — supported EMPIRICALLY on the sampled run (sample/parameterisation-relative, not a guarantee);
//!   * `VIOLATED` — a replayable counter-witness exists;
//!   * `REJECTED_AS_PROOF` — the stated mechanism does not prove the property it is invoked for;
//!   * `UNDERDETERMINED` — not decided by the available evidence.
//!
//! `integrity ≠ truth`; `empirical-boundedness ≠ certified`. Everything grades the REFERENCE / a dump, never
//! the executed Rust kernel (`reference-model ≠ authoritative-kernel`).

use crate::artifacts::{AnalysisResult, Finding, Limitation};
use crate::claim_ledger::{Claim, Grade};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObligationStatus {
    Closed,
    Bounded,
    Violated,
    RejectedAsProof,
    Underdetermined,
}

impl ObligationStatus {
    pub fn as_str(&self) -> &'static str {
        match self {
            ObligationStatus::Closed => "CLOSED",
            ObligationStatus::Bounded => "BOUNDED",
            ObligationStatus::Violated => "VIOLATED",
            ObligationStatus::RejectedAsProof => "REJECTED_AS_PROOF",
            ObligationStatus::Underdetermined => "UNDERDETERMINED",
        }
    }

    /// Map to the claim-ledger grade (mirrors the Python `_GRADE`): a VIOLATED / REJECTED_AS_PROOF finding is
    /// itself ESTABLISHED (we are sure of the negative result), BOUNDED is MEASURED, UNDERDETERMINED stays so.
    pub fn grade(&self) -> Grade {
        match self {
            ObligationStatus::Closed | ObligationStatus::Violated | ObligationStatus::RejectedAsProof => {
                Grade::Established
            }
            ObligationStatus::Bounded => Grade::Measured,
            ObligationStatus::Underdetermined => Grade::Underdetermined,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ObligationResult {
    pub id: String,
    pub statement: String,
    pub status: ObligationStatus,
    pub witness: String,
    pub does_not_show: String,
    pub falsifier: String,
}

impl ObligationResult {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        id: impl Into<String>,
        statement: impl Into<String>,
        status: ObligationStatus,
        witness: impl Into<String>,
        does_not_show: impl Into<String>,
        falsifier: impl Into<String>,
    ) -> Self {
        Self {
            id: id.into(),
            statement: statement.into(),
            status,
            witness: witness.into(),
            does_not_show: does_not_show.into(),
            falsifier: falsifier.into(),
        }
    }

    /// Project into the shared honesty contract (scope + 2 limitations) — honest by construction.
    pub fn as_analysis(&self) -> AnalysisResult {
        AnalysisResult::new(
            "manifest-invariant",
            vec![
                Finding::new("OBLIGATION", "manifest-invariant", self.statement.clone()),
                Finding::new("STATUS", "manifest-invariant", self.status.as_str()),
                Finding::new("WITNESS", "manifest-invariant", self.witness.clone()),
            ],
            vec![
                Limitation::new("manifest-invariant", format!("does not show: {}", self.does_not_show)),
                Limitation::new("scope", "graded over the REFERENCE; reference-model != authoritative-kernel"),
            ],
        )
        .expect("obligation as_analysis always satisfies the honesty contract")
    }

    /// Project into a graded `Claim` (status → grade via [`ObligationStatus::grade`]).
    pub fn as_claim(&self) -> Claim {
        Claim::new(
            format!("INV::{}", self.id),
            self.statement.clone(),
            self.status.grade(),
            format!("status={}; {}", self.status.as_str(), self.witness),
            self.does_not_show.clone(),
            self.falsifier.clone(),
        )
    }
}
