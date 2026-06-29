// SPDX-License-Identifier: AGPL-3.0-only
//! commercial_obligations — the proof-gated buyer-facing claims ledger (gateway layer 4), ported from
//! `DVSM/commercial/commercial_obligations.py` over the validated [`crate::claim_ledger`] substrate.
//!
//! A sales claim is honest only if a *discharged* technical obligation backs it. The ledger audits honest iff:
//!   (a) every claim carries a non-empty `does_not_show` and `falsifier` (reused from `claim_ledger::audit_ledger`);
//!   (b) no SUPPORTED (Established/Measured) claim rests on an UNDISCHARGED obligation (`exceeds_proof`);
//!   (c) no SUPPORTED claim contains hype-lexicon language (`hype`);
//!   (d) every `rests_on` names a known obligation — discharged or open/rejected (`unknown_obligation`).
//!
//! `claim ≠ proof`; `grade ≠ truth`. Grades are on-ladder by construction (the `Grade` enum), a Rust
//! strengthening over the Python string ladder.
//!
//! ## LOAD-BEARING `does_not_show` (the boundary the grading pass surfaced)
//! `static-check ≠ live-execution`. This gate verifies that a claim *names* a discharged obligation; it does
//! **NOT** execute that obligation's test, nor confirm it passed in this build. The `discharged` set is a
//! declared cross-reference, trusted as data. Binding `discharged` to a live `verify.py` / `cargo test` run is
//! an OPEN hardening, not done here.
//!
//! ## Drift note
//! The Python ledger remains canonical; this is a mirror for the single-binary gateway. The differential test
//! (`tests/commercial_gate.rs`) asserts the shipped ledger audits honest exactly as the Python does, which
//! catches gross drift — but two hand-maintained ledgers can still diverge in detail. `mirror ≠ source`.

use crate::claim_ledger::{audit_ledger, Claim, Grade};
use std::collections::BTreeSet;

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
        // mechanism carries the obligation reference, mirroring the Python `rests_on=...`
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
}

/// The proof-gated commercial ledger.
pub struct CommercialLedger {
    pub claims: Vec<CommercialClaim>,
    pub discharged: BTreeSet<String>,
    pub open_or_rejected: BTreeSet<String>,
}

impl CommercialLedger {
    /// Audit honest iff: boundary fields present (via `claim_ledger::audit_ledger`); no SUPPORTED claim rests
    /// on an undischarged obligation; no SUPPORTED claim contains hype; every `rests_on` is a known key.
    pub fn audit(&self) -> CommercialAudit {
        let mapped: Vec<Claim> = self.claims.iter().map(|c| c.to_claim()).collect();
        let base = audit_ledger(&mapped); // boundary-field (does_not_show / falsifier) check + on-ladder

        let mut exceeds_proof = Vec::new();
        let mut hype = Vec::new();
        let mut unknown_obligation = Vec::new();
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
        }

        let honest = base.honest
            && exceeds_proof.is_empty()
            && hype.is_empty()
            && unknown_obligation.is_empty();
        CommercialAudit {
            honest,
            exceeds_proof,
            hype,
            unknown_obligation,
            missing_boundary: base.missing_boundary,
        }
    }
}

fn set(keys: &[&str]) -> BTreeSet<String> {
    keys.iter().map(|s| s.to_string()).collect()
}

/// The SHIPPED ledger — a faithful mirror of the Python `COMMERCIAL_CLAIMS` + registries. Supported
/// value-props (C*) rest on discharged obligations; boundary rows (B*) are explicitly downgraded and rest on
/// open/rejected keys. The Python remains canonical (see the Drift note).
pub fn shipped_ledger() -> CommercialLedger {
    let discharged = set(&[
        "coupling.detect_identifiable",
        "coupling.airgap_clean",
        "coupling.declares_blindness",
        "backend.refuse_contaminated_atomic",
        "backend.honest_answers",
        "backend.no_fused_scalar",
        "auditor.custom_probe",
        "reproducibility.determinism",
        "ledger.catches_ghosts",
        "kappa.remediated_skew",
        "certificate.discrete_contraction",
    ]);
    let open_or_rejected = set(&[
        "kernel.boundedness",
        "coupling.exhaustive",
        "kernel.energy_law_holds",
        "realkernel.lift",
    ]);

    let claims = vec![
        CommercialClaim::new("C1", "Detects identifiable diagnostic→dynamics leaks (observer contamination) in your kernel telemetry.",
          Grade::Measured, "coupling.detect_identifiable",
          "a mechanism or magnitude; only that a residual survives conditioning on the modeled drivers.",
          "the residual dissolves under a further candidate confounder or finer windowing.", "open-core"),
        CommercialClaim::new("C2", "Refuses to certify contaminated or unidentifiable telemetry as controller-safe — atomically.",
          Grade::Established, "backend.refuse_contaminated_atomic",
          "that certified telemetry is correct — only that an ungrounded certification cannot execute.",
          "an action running on a non-AIR_GAP_HELD window.", "open-core"),
        CommercialClaim::new("C3", "Every finding carries its scope and at least one limitation; no fused 'health score'.",
          Grade::Established, "backend.honest_answers",
          "that the findings are complete — only that none ships without its boundary.",
          "an answer emitted without a scope or limitation, or a single aggregate score field.", "open-core"),
        CommercialClaim::new("C4", "Deterministic, reproducible reports: identical telemetry yields an identical report.",
          Grade::Established, "reproducibility.determinism",
          "correctness or cross-precision parity; integrity ≠ truth.",
          "identical input producing divergent reports.", "open-core"),
        CommercialClaim::new("C5", "Works on YOUR kernel: customer-defined probes over arbitrary telemetry columns.",
          Grade::Measured, "auditor.custom_probe",
          "that your specific kernel is leak-free — only that the procedure runs on your schema.",
          "a probe schema the auditor cannot evaluate.", "commercial"),
        CommercialClaim::new("C6", "States where it is blind: a coupling whose diagnostic is a function of the conditioned state is reported UNIDENTIFIABLE, not falsely cleared.",
          Grade::Established, "coupling.declares_blindness",
          "that blind couplings are absent — undetected ≠ absent.",
          "an unidentifiable coupling silently reported AIR_GAP_HELD.", "open-core"),
        CommercialClaim::new("C7", "Ships with a checkable discrete-time contraction certificate: a sufficient condition (2‖κ‖_F·σ < λ, dt·λ ≤ 1) with the noise margin σ_max and the contraction factor ρ stated.",
          Grade::Measured, "certificate.discrete_contraction",
          "stability for ‖S‖ > σ, the fixed-point clamps, or the full coupled Z–S–W system — it is a SUFFICIENT condition, NOT a global stability proof.",
          "a sampled trajectory whose growth exceeds the analytic ρ within the certified σ.", "commercial"),
        CommercialClaim::new("C8", "The Lie-coupling κ can be antisymmetrized to a hollow, skew-symmetric matrix, after which the skew-symmetry obligation closes (max|κ+κᵀ| = 0).",
          Grade::Established, "kappa.remediated_skew",
          "that the shipped upstream kernel uses the corrected κ — only that the remediation satisfies the premise.",
          "an entry with κ[i,j] + κ[j,i] ≠ 0 after antisymmetrization (a coding error in the remediation).", "open-core"),
        // ---- boundary claims: what we explicitly do NOT sell — downgraded, rest on open/rejected ----
        CommercialClaim::new("B1", "We do NOT guarantee your kernel is numerically bounded.",
          Grade::NotMeasured, "kernel.boundedness",
          "boundedness — the continuous energy law does not certify the discrete kernel; a Lyapunov cert is open.",
          "a discrete-time trapping certificate (would upgrade this).", "open-core"),
        CommercialClaim::new("B2", "We do NOT claim to detect every coupling — only identifiable ones.",
          Grade::NotMeasured, "coupling.exhaustive",
          "completeness or absence of a leak. undetected ≠ absent.",
          "a completeness proof over the coupling space.", "open-core"),
        CommercialClaim::new("B3", "Reference-model results are reference-relative until run on your real kernel trace dumps.",
          Grade::Underdetermined, "realkernel.lift",
          "any property of the shipped Rust kernel from the Python reference alone.",
          "a run on real BinaryFrame dumps reproducing the verdicts.", "commercial"),
    ];

    CommercialLedger { claims, discharged, open_or_rejected }
}
