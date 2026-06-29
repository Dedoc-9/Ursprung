// SPDX-License-Identifier: AGPL-3.0-only
//! The honesty contract — the shared reporting boundary every tool emits.
//!
//! `AnalysisResult` requires a non-empty scope and at least one `Limitation`; these are enforced at
//! construction (`new` returns `Result`), so a dishonest result is unconstructable. `finding-metadata ≠
//! control`: findings/limitations describe; they never decide. `reporting-boundary ≠ domain-supertype`.

use std::error::Error;
use std::fmt;

/// One result item. Metadata DESCRIBES the result; it never decides it (no confidence/severity fields —
/// those become hidden control paths).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Finding {
    pub kind: String,
    pub scope: String,
    pub detail: String,
}

impl Finding {
    pub fn new(kind: impl Into<String>, scope: impl Into<String>, detail: impl Into<String>) -> Self {
        Self { kind: kind.into(), scope: scope.into(), detail: detail.into() }
    }
}

/// A structured honesty boundary (not a freeform string, so it composes as consumers multiply).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Limitation {
    pub scope: String,
    pub claim: String,
}

impl Limitation {
    pub fn new(scope: impl Into<String>, claim: impl Into<String>) -> Self {
        Self { scope: scope.into(), claim: claim.into() }
    }
}

/// Why an `AnalysisResult` could not be constructed — the honesty contract refusing to be skipped.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HonestyError {
    EmptyScope,
    NoLimitation,
}

impl fmt::Display for HonestyError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            HonestyError::EmptyScope => write!(f, "AnalysisResult requires a non-empty scope"),
            HonestyError::NoLimitation => {
                write!(f, "AnalysisResult requires >= 1 Limitation - honesty travels with the result")
            }
        }
    }
}

impl Error for HonestyError {}

/// What every artifact consumer emits. The honesty travels WITH the result: a non-empty `scope` and at least
/// one `Limitation` are REQUIRED and enforced at construction. There is no way to build a dishonest one.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AnalysisResult {
    scope: String,
    findings: Vec<Finding>,
    limitations: Vec<Limitation>,
}

impl AnalysisResult {
    /// Construct — refusing (with [`HonestyError`]) if the scope is empty or there are no limitations.
    pub fn new(
        scope: impl Into<String>,
        findings: Vec<Finding>,
        limitations: Vec<Limitation>,
    ) -> Result<Self, HonestyError> {
        let scope = scope.into();
        if scope.is_empty() {
            return Err(HonestyError::EmptyScope);
        }
        if limitations.is_empty() {
            return Err(HonestyError::NoLimitation);
        }
        Ok(Self { scope, findings, limitations })
    }

    pub fn scope(&self) -> &str {
        &self.scope
    }
    pub fn findings(&self) -> &[Finding] {
        &self.findings
    }
    pub fn limitations(&self) -> &[Limitation] {
        &self.limitations
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_scope_is_refused() {
        let r = AnalysisResult::new("", vec![], vec![Limitation::new("s", "c")]);
        assert_eq!(r.unwrap_err(), HonestyError::EmptyScope);
    }

    #[test]
    fn no_limitation_is_refused() {
        let r = AnalysisResult::new("scope", vec![Finding::new("k", "scope", "d")], vec![]);
        assert_eq!(r.unwrap_err(), HonestyError::NoLimitation);
    }

    #[test]
    fn honest_result_constructs() {
        let r = AnalysisResult::new(
            "scope",
            vec![Finding::new("k", "scope", "d")],
            vec![Limitation::new("scope", "does not prove global safety")],
        )
        .unwrap();
        assert_eq!(r.scope(), "scope");
        assert_eq!(r.findings().len(), 1);
        assert_eq!(r.limitations().len(), 1);
    }
}
