// SPDX-License-Identifier: AGPL-3.0-only
//! # Ursprung fundamentals (Rust)
//!
//! A faithful Rust port of the Ursprung / weltwerk epistemic core. The discipline is the same as the
//! Python original — but Rust lets two of the invariants be enforced by the *type system* rather than by a
//! runtime re-check:
//!
//! * **The honesty contract is a constructor invariant.** [`AnalysisResult::new`] returns a `Result`; an
//!   analysis with an empty scope or zero limitations cannot be constructed. There is no dishonest
//!   `AnalysisResult` to leak. (`analysis ≠ proof`.)
//! * **The action chokepoint is a type, not a check.** [`Grounded<T>`](epistemic_types::Grounded) holds its
//!   value in a private field; the only constructor refuses unless a [`Grounding`](epistemic_types::Grounding)
//!   proof `is_grounded()`. Holding a `Grounded<T>` *is* the witness that `T` was verified. (`grounded ≠ true`.)
//!
//! ## The fundamentals
//! * [`artifacts`] — the honesty contract: `AnalysisResult` / `Finding` / `Limitation`.
//! * [`epistemic_types`] — `Grounding`, `Grounded<T>`, `enact` (the action chokepoint), `Attested`.
//! * [`claim_ledger`] — `Grade` (an enum ⇒ off-ladder grades are *unrepresentable*), `Claim`, `audit_ledger`.
//! * [`frontier_gate`] — bounded metric deflation: SUPER/SUB/NEAR → EXPLOIT/PIVOT/HOLD.
//! * [`residual_channel`] — the confounder-conditioned mutual-information diagnostic (deterministic).
//! * [`coupling_audit`] — the forbidden-coupling taxonomy (AIR_GAP_HELD / OBSERVER_CONTAMINATION /
//!   CONFOUNDED_ARTIFACT / UNIDENTIFIABLE) on top of the residual core, with quantile binning + (Z,W) stress.
//! * [`orchestrator`] — the Epistemic Runtime Orchestrator: a router with the two chokepoints. It adds no
//!   authority. `router ≠ verifier`; `composition ≠ capability`; `integrity ≠ truth`.
//!
//! Separators (load-bearing maxims), preserved from the Python: `integrity ≠ truth`, `router ≠ verifier`,
//! `grounded ≠ true`, `residual-CMI ≠ channel`, `proves-the-procedure ≠ proves-the-phenomenon`,
//! `salience ≠ importance`, `prediction ≠ causation`.

pub mod artifacts;
pub mod binframe_adapter;
pub mod claim_ledger;
pub mod commercial_obligations;
pub mod contraction_cert;
pub mod coupling_audit;
pub mod epistemic_types;
pub mod frontier_gate;
pub mod gateway;
pub mod invariant_ledger;
pub mod orchestrator;
pub mod residual_channel;

pub use artifacts::{AnalysisResult, Finding, HonestyError, Limitation};
pub use claim_ledger::{audit_ledger, Claim, Grade, LedgerAudit, SupportedClaim};
pub use binframe_adapter::{
    containment, containment_from, field, lift, lift_streaming, non_liftable, parse_frames,
    read_frames_streaming, replay_parity, stream_frames, Field, FieldType, ParseReport, Row, Schema,
    NON_LIFTABLE_NEEDS, SCHEMA_ABI, SCHEMA_CMI, SCHEMA_TELEM, U_MAX_DEFAULT,
};
pub use invariant_ledger::{ObligationResult, ObligationStatus};
pub use gateway::{
    coupling_input_from_rows, parse_receipt, render_coupling_report, render_report, run_coupling_streaming,
    run_gateway, run_gateway_streaming, CmiAssembleError, CouplingGateReport, GatewayReport,
};
pub use commercial_obligations::{
    shipped_ledger, CommercialAudit, CommercialClaim, CommercialLedger, HYPE,
};
pub use coupling_audit::{audit_coupling, Binner, CouplingInput, CouplingResult, CouplingVerdict};
pub use contraction_cert::{
    antisymmetrize, as_obligation as contraction_obligation, certify, frob, hollow_residual, kappa_matrix,
    kappa_skew, kappa_skew_obligation, sigma_max, skew_residual, step as lie_step, CertDecision, CertifyResult,
};
pub use epistemic_types::{enact, Attested, Grounded, Grounding, UngroundedError};
pub use frontier_gate::{classify_regime, Action, Decision, FrontierGate, Regime};
pub use orchestrator::{
    default_orchestrator, CouplingTool, EpistemicTool, FrontierTool, LedgerTool, Orchestrator,
    OrchestratorError, Request, ResidualTool,
};
pub use residual_channel::{
    audit, audit_default, conditional_mutual_information, demo_gen_channel, demo_gen_null,
    mutual_information, ChannelDecision, ChannelEstablished, NoHiddenChannel, ResidualChannelResult, Sample,
};
