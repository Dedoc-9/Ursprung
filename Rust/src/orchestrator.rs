// SPDX-License-Identifier: AGPL-3.0-only
//! The Epistemic Runtime Orchestrator — a router with two chokepoints, and NO new authority.
//!
//! * **Answer chokepoint.** Every tool returns an [`AnalysisResult`], which is honest *by construction*
//!   (see [`crate::artifacts`]). The orchestrator cannot emit, and a tool cannot build, a dishonest answer.
//!   [`Orchestrator::panel`] reports many witnesses side by side — there is NO fused confidence scalar.
//! * **Action chokepoint.** [`Orchestrator::enact`] runs an action only on a value a verifier-issued
//!   [`Grounding`] grounds; otherwise it refuses before any effect.
//!
//! `router ≠ verifier`; `composition ≠ capability`; `integrity ≠ truth`.

use std::collections::BTreeMap;
use std::error::Error;
use std::fmt;

use crate::artifacts::{AnalysisResult, Finding, Limitation};
use crate::claim_ledger::{audit_ledger, Claim};
use crate::epistemic_types::{enact, Grounding, UngroundedError};
use crate::frontier_gate::FrontierGate;
use crate::residual_channel::{audit, Sample};
use crate::coupling_audit::{audit_coupling, CouplingInput};

/// The request a tool consumes. One variant per fundamental tool.
pub enum Request {
    Residual { samples: Vec<Sample>, reps: usize, seed: u64 },
    Frontier { m_novel: f64, ci: (f64, f64) },
    Ledger { claims: Vec<Claim> },
    Coupling(Box<CouplingInput>),
}

/// A registered tool: a name + a total function into the honesty contract.
pub trait EpistemicTool {
    fn name(&self) -> &str;
    fn analyze(&self, req: &Request) -> AnalysisResult;
}

fn unsupported(tool: &str) -> AnalysisResult {
    AnalysisResult::new(
        "error",
        vec![Finding::new("UNSUPPORTED_REQUEST", "error", tool.to_string())],
        vec![Limitation::new("error", "this tool received a request variant it does not handle")],
    )
    .expect("unsupported() always satisfies the honesty contract")
}

/// Confounder-conditioned dependence audit.
pub struct ResidualTool;
impl EpistemicTool for ResidualTool {
    fn name(&self) -> &str {
        "residual_channel"
    }
    fn analyze(&self, req: &Request) -> AnalysisResult {
        match req {
            Request::Residual { samples, reps, seed } => {
                audit(samples, *reps, *seed, 4.0, 0.005, &[]).as_analysis()
            }
            _ => unsupported(self.name()),
        }
    }
}

/// Bounded metric-deflation gate.
pub struct FrontierTool;
impl EpistemicTool for FrontierTool {
    fn name(&self) -> &str {
        "frontier_gate"
    }
    fn analyze(&self, req: &Request) -> AnalysisResult {
        match req {
            Request::Frontier { m_novel, ci } => {
                let d = FrontierGate::default().decide(*m_novel, *ci);
                AnalysisResult::new(
                    "frontier",
                    vec![
                        Finding::new("REGIME", "frontier", format!("{:?}", d.regime)),
                        Finding::new("ACTION", "frontier", d.action.as_str()),
                        Finding::new("M_NOVEL", "frontier", format!("{:.4}", d.m_novel)),
                    ],
                    vec![Limitation::new(
                        "frontier",
                        "m_novel is an estimate; pivot != guaranteed-escape",
                    )],
                )
                .expect("frontier analysis satisfies the honesty contract")
            }
            _ => unsupported(self.name()),
        }
    }
}

/// Graded claim-ledger audit.
pub struct LedgerTool;
impl EpistemicTool for LedgerTool {
    fn name(&self) -> &str {
        "claim_ledger"
    }
    fn analyze(&self, req: &Request) -> AnalysisResult {
        match req {
            Request::Ledger { claims } => {
                let a = audit_ledger(claims);
                AnalysisResult::new(
                    "ledger",
                    vec![
                        Finding::new("HONEST", "ledger", a.honest.to_string()),
                        Finding::new("COUNTS", "ledger", format!("{:?}", a.counts)),
                        Finding::new("MISSING_BOUNDARY", "ledger", format!("{:?}", a.missing_boundary)),
                    ],
                    vec![Limitation::new("ledger", "honest = graded + falsifiable; honest != true")],
                )
                .expect("ledger analysis satisfies the honesty contract")
            }
            _ => unsupported(self.name()),
        }
    }
}

/// Forbidden-coupling firewall — the taxonomy (AIR_GAP_HELD / OBSERVER_CONTAMINATION / CONFOUNDED_ARTIFACT /
/// UNIDENTIFIABLE) layered on the residual-channel core.
pub struct CouplingTool;
impl EpistemicTool for CouplingTool {
    fn name(&self) -> &str {
        "coupling_audit"
    }
    fn analyze(&self, req: &Request) -> AnalysisResult {
        match req {
            Request::Coupling(inp) => audit_coupling(inp).as_analysis(),
            _ => unsupported(self.name()),
        }
    }
}

/// Tool dispatch failure.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OrchestratorError {
    UnknownTool(String),
}

impl fmt::Display for OrchestratorError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            OrchestratorError::UnknownTool(n) => write!(f, "no tool '{}' registered", n),
        }
    }
}

impl Error for OrchestratorError {}

/// A router over registered [`EpistemicTool`]s. Adds no authority — it dispatches answers and gates actions.
pub struct Orchestrator {
    tools: BTreeMap<String, Box<dyn EpistemicTool>>,
}

impl Orchestrator {
    pub fn new() -> Self {
        Self { tools: BTreeMap::new() }
    }

    pub fn register(&mut self, tool: Box<dyn EpistemicTool>) -> &mut Self {
        self.tools.insert(tool.name().to_string(), tool);
        self
    }

    /// ANSWER chokepoint: dispatch by name. The returned `AnalysisResult` is honest by construction.
    pub fn analyze(&self, name: &str, req: &Request) -> Result<AnalysisResult, OrchestratorError> {
        match self.tools.get(name) {
            Some(t) => Ok(t.analyze(req)),
            None => Err(OrchestratorError::UnknownTool(name.to_string())),
        }
    }

    /// Many witnesses on one question, side by side — NO aggregation, NO scalar, no global winner.
    pub fn panel(
        &self,
        calls: &[(String, Request)],
    ) -> Vec<(String, Result<AnalysisResult, OrchestratorError>)> {
        calls.iter().map(|(n, r)| (n.clone(), self.analyze(n, r))).collect()
    }

    /// ACTION chokepoint: run `action` only on a value the `proof` grounds; else `Err` before any effect.
    pub fn enact<T, P, R, F>(&self, value: T, proof: &P, action: F) -> Result<R, UngroundedError>
    where
        P: Grounding,
        F: FnOnce(T) -> R,
    {
        enact(value, proof, action)
    }

    pub fn tool_names(&self) -> Vec<String> {
        self.tools.keys().cloned().collect()
    }
}

impl Default for Orchestrator {
    fn default() -> Self {
        Self::new()
    }
}

/// An orchestrator with the fundamental tools registered.
pub fn default_orchestrator() -> Orchestrator {
    let mut o = Orchestrator::new();
    o.register(Box::new(ResidualTool))
        .register(Box::new(FrontierTool))
        .register(Box::new(LedgerTool))
        .register(Box::new(CouplingTool));
    o
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::claim_ledger::Grade;
    use crate::epistemic_types::Attested;
    use crate::residual_channel::demo_gen_channel;

    #[test]
    fn unknown_tool_errors() {
        let o = default_orchestrator();
        let r = o.analyze("nope", &Request::Frontier { m_novel: 1.0, ci: (0.9, 1.1) });
        assert!(matches!(r, Err(OrchestratorError::UnknownTool(_))));
    }

    #[test]
    fn answers_are_honest_by_construction() {
        let o = default_orchestrator();
        let a = o
            .analyze("residual_channel", &Request::Residual { samples: demo_gen_channel(2000, 3, 2), reps: 40, seed: 0 })
            .unwrap();
        assert!(!a.scope().is_empty());
        assert!(!a.limitations().is_empty());
    }

    #[test]
    fn panel_carries_no_scalar() {
        let o = default_orchestrator();
        let calls = vec![
            ("frontier_gate".to_string(), Request::Frontier { m_novel: 0.5, ci: (0.3, 0.8) }),
            (
                "claim_ledger".to_string(),
                Request::Ledger {
                    claims: vec![Claim::new("D1", "E reproduces", Grade::Established, "m", "the magnitude", "a failed rep")],
                },
            ),
        ];
        let panel = o.panel(&calls);
        // one witness per call; the panel is a Vec of named results — no fused score anywhere
        assert_eq!(panel.len(), 2);
        assert!(panel.iter().all(|(_n, r)| r.is_ok()));
    }

    #[test]
    fn action_chokepoint_gates() {
        let o = default_orchestrator();
        assert!(o.enact("apply", &Attested::new(true, "grounded"), |v| v).is_ok());
        assert!(o.enact("apply", &Attested::new(false, "ungrounded"), |v| v).is_err());
    }
}
