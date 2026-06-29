# SPDX-License-Identifier: AGPL-3.0-only
# Commercial use beyond AGPL-3.0 requires a separate license — see LICENSE-COMMERCIAL.md.
"""
commercial_obligations.py — the buyer-facing claims ledger, PROOF-GATED. This is the commercial expression of
the project's core discipline: a sales claim is honest only if a discharged technical obligation backs it.

`consider those proofs`: every `CommercialClaim` names the obligation it `rests_on`. The ledger is honest iff
  (a) every claim is on the grade ladder with a `does_not_show` and a `falsifier`;
  (b) no SUPPORTED (ESTABLISHED/MEASURED) claim rests on an UNDISCHARGED or REJECTED obligation;
  (c) no SUPPORTED claim contains hype-lexicon language;
  (d) every `rests_on` names a known obligation.
So marketing cannot exceed evidence — the same vulnerability the whole project treats as a defect, enforced at
the contract layer. `claim ≠ proof`; `grade ≠ truth`.

Grades reuse the open-core epistemic ladder (`claim_ledger.GRADES`): ESTABLISHED, MEASURED, UNDERDETERMINED,
SPECULATIVE, NOT_MEASURED. SUPPORTED = {ESTABLISHED, MEASURED}.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "weltwerk", "verify"))
from claim_ledger import Claim, audit_ledger, GRADES, SUPPORTED                 # noqa: E402


# Technical obligations ACTUALLY discharged by the DVSM test suite — the evidence a sales claim may rest on.
DISCHARGED: Dict[str, str] = {
    "coupling.detect_identifiable":
        "test_coupling_audit::omega_detected, novelty_detected — planted identifiable leaks → OBSERVER_CONTAMINATION",
    "coupling.airgap_clean":
        "test_coupling_audit::clean_air_gap — an air-gapped trace reads AIR_GAP_HELD",
    "coupling.declares_blindness":
        "test_coupling_audit::unidentifiable_flagged — declines to rule on unidentifiable couplings",
    "backend.refuse_contaminated_atomic":
        "test_dvsm_backend / test_kernel_auditor — contaminated telemetry refused before any effect",
    "backend.honest_answers":
        "test_dvsm_backend::windows_emit_analysis — every answer is an AnalysisResult (scope + ≥1 limitation)",
    "backend.no_fused_scalar":
        "test_dvsm_backend::panel_no_scalar / test_kernel_auditor::posture_no_scalar — no single health score",
    "auditor.custom_probe":
        "test_kernel_auditor::custom_probe — a customer-defined probe over arbitrary telemetry columns works",
    "reproducibility.determinism":
        "test_dvsm_reference::determinism + invariant_ledger DVSM-6 — identical input ⇒ identical report",
    "ledger.catches_ghosts":
        "test_invariant_ledger::kappa_ghost_caught, energy_law_rejected — obligations grade honestly",
    "kappa.remediated_skew":
        "test_kappa_remediation (DVSM) — antisymmetrized κ=(κ−κᵀ)/2 is hollow+skew (max|κ+κᵀ|=0); the skew "
        "obligation flips VIOLATED→CLOSED",
    "certificate.discrete_contraction":
        "test_discrete_certificate (DVSM) — a checkable sufficient condition (2‖κ‖_F·σ<λ ∧ dt·λ≤1 ⇒ ρ<1) with "
        "the σ-margin and ρ stated; analytic ρ bounds measured growth; the κ fix widens the margin",
}

# Obligations that are OPEN or REJECTED — a SUPPORTED commercial claim may NOT rest on any of these.
OPEN_OR_REJECTED: Dict[str, str] = {
    "kernel.boundedness":
        "DVSM-2 REJECTED_AS_PROOF (continuous energy law ≠ discrete bound); discrete Lyapunov cert OPEN",
    "coupling.exhaustive":
        "undetected ≠ absent; unidentifiable couplings exist — the firewall is not a completeness proof",
    "kernel.energy_law_holds":
        "DVSM-1 VIOLATED — κ=sin(k·1.37−j·1.73) is not skew-symmetric, the energy-law premise fails",
    "realkernel.lift":
        "all reference grades are reference-relative until re-run on real BinaryFrame dumps (reference ≠ kernel)",
}

# Hype lexicon — banned from any SUPPORTED claim (semantic inflation the product treats as a defect).
HYPE: Tuple[str, ...] = (
    "guarantee", "guaranteed", "100%", "unhackable", "proves your", "certified safe", "bug-free",
    "prevents all", "eliminates all", "fully secure", "provably safe", "zero risk")


@dataclass(frozen=True)
class CommercialClaim:
    """A buyer-facing claim. `rests_on` MUST name an obligation key; a SUPPORTED grade is honest only when that
    key is DISCHARGED. Boundary claims (what we do NOT sell) rest on OPEN_OR_REJECTED at a non-supported grade."""
    id: str
    statement: str
    grade: str
    rests_on: str
    does_not_show: str
    falsifier: str
    tier: str = "open-core"          # open-core (AGPL-3.0) | commercial (paid license)

    def to_claim(self) -> Claim:
        return Claim(self.id, self.statement, self.grade, f"rests_on={self.rests_on}",
                     self.does_not_show, self.falsifier)


# The SHIPPED commercial ledger. Supported value-props rest on discharged obligations; boundary rows are
# explicitly downgraded so the contract states, in writing, what the product does NOT do.
COMMERCIAL_CLAIMS: Tuple[CommercialClaim, ...] = (
    CommercialClaim(
        "C1", "Detects identifiable diagnostic→dynamics leaks (observer contamination) in your kernel telemetry.",
        "MEASURED", "coupling.detect_identifiable",
        "a mechanism or magnitude; only that a residual survives conditioning on the modeled drivers.",
        "the residual dissolves under a further candidate confounder or finer windowing.", "open-core"),
    CommercialClaim(
        "C2", "Refuses to certify contaminated or unidentifiable telemetry as controller-safe — atomically.",
        "ESTABLISHED", "backend.refuse_contaminated_atomic",
        "that certified telemetry is correct — only that an ungrounded certification cannot execute.",
        "an action running on a non-AIR_GAP_HELD window.", "open-core"),
    CommercialClaim(
        "C3", "Every finding carries its scope and at least one limitation; no fused 'health score'.",
        "ESTABLISHED", "backend.honest_answers",
        "that the findings are complete — only that none ships without its boundary.",
        "an answer emitted without a scope or limitation, or a single aggregate score field.", "open-core"),
    CommercialClaim(
        "C4", "Deterministic, reproducible reports: identical telemetry yields an identical report.",
        "ESTABLISHED", "reproducibility.determinism",
        "correctness or cross-precision parity; integrity ≠ truth.",
        "identical input producing divergent reports.", "open-core"),
    CommercialClaim(
        "C5", "Works on YOUR kernel: customer-defined probes over arbitrary telemetry columns.",
        "MEASURED", "auditor.custom_probe",
        "that your specific kernel is leak-free — only that the procedure runs on your schema.",
        "a probe schema the auditor cannot evaluate.", "commercial"),
    CommercialClaim(
        "C6", "States where it is blind: a coupling whose diagnostic is a function of the conditioned state is "
              "reported UNIDENTIFIABLE, not falsely cleared.",
        "ESTABLISHED", "coupling.declares_blindness",
        "that blind couplings are absent — undetected ≠ absent.",
        "an unidentifiable coupling silently reported AIR_GAP_HELD.", "open-core"),
    CommercialClaim(
        "C7", "Ships with a checkable discrete-time contraction certificate: a sufficient condition "
              "(2‖κ‖_F·σ < λ, dt·λ ≤ 1) with the noise margin σ_max and the contraction factor ρ stated.",
        "MEASURED", "certificate.discrete_contraction",
        "stability for ‖S‖ > σ, the fixed-point clamps, or the full coupled Z–S–W system — it is a SUFFICIENT "
        "condition, NOT a global stability proof.",
        "a sampled trajectory whose growth exceeds the analytic ρ within the certified σ.", "commercial"),
    CommercialClaim(
        "C8", "The Lie-coupling κ can be antisymmetrized to a hollow, skew-symmetric matrix, after which the "
              "skew-symmetry obligation closes (max|κ+κᵀ| = 0).",
        "ESTABLISHED", "kappa.remediated_skew",
        "that the shipped upstream kernel uses the corrected κ — only that the remediation satisfies the premise.",
        "an entry with κ[i,j] + κ[j,i] ≠ 0 after antisymmetrization (a coding error in the remediation).",
        "open-core"),
    # ---- boundary claims: what we explicitly do NOT sell — downgraded, rest on OPEN_OR_REJECTED ----
    CommercialClaim(
        "B1", "We do NOT guarantee your kernel is numerically bounded.",
        "NOT_MEASURED", "kernel.boundedness",
        "boundedness — the continuous energy law does not certify the discrete kernel; a Lyapunov cert is open.",
        "a discrete-time trapping certificate (would upgrade this).", "open-core"),
    CommercialClaim(
        "B2", "We do NOT claim to detect every coupling — only identifiable ones.",
        "NOT_MEASURED", "coupling.exhaustive",
        "completeness or absence of a leak. undetected ≠ absent.",
        "a completeness proof over the coupling space.", "open-core"),
    CommercialClaim(
        "B3", "Reference-model results are reference-relative until run on your real kernel trace dumps.",
        "UNDERDETERMINED", "realkernel.lift",
        "any property of the shipped Rust kernel from the Python reference alone.",
        "a run on real BinaryFrame dumps reproducing the verdicts.", "commercial"),
)


def audit_commercial_ledger(claims: Tuple[CommercialClaim, ...]) -> dict:
    """Honest iff: on-ladder + boundary fields present (claim_ledger); no SUPPORTED claim rests on an
    undischarged/rejected obligation; no SUPPORTED claim contains hype; every `rests_on` is a known key."""
    base = audit_ledger([c.to_claim() for c in claims])
    exceeds = [c.id for c in claims if c.grade in SUPPORTED and c.rests_on not in DISCHARGED]
    hype = [c.id for c in claims if c.grade in SUPPORTED and any(w in c.statement.lower() for w in HYPE)]
    unknown_ref = [c.id for c in claims if c.rests_on not in DISCHARGED and c.rests_on not in OPEN_OR_REJECTED]
    missing = [c.id for c in claims if not c.does_not_show or not c.falsifier]
    honest = base["honest"] and not exceeds and not hype and not unknown_ref and not missing
    return {"honest": honest, "exceeds_proof": exceeds, "hype": hype,
            "unknown_obligation": unknown_ref, "missing_boundary": missing, "base": base}


def main():
    print("commercial_obligations.py — proof-gated buyer claims (consider those proofs)\n")
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS)
    for c in COMMERCIAL_CLAIMS:
        kind = "value" if c.grade in SUPPORTED else "boundary"
        print(f"  [{c.grade:15s}] {c.id} ({c.tier}, {kind}) ← {c.rests_on}")
    print(f"\n  ledger honest: {a['honest']}  exceeds_proof={a['exceeds_proof']}  hype={a['hype']}  "
          f"unknown={a['unknown_obligation']}")
    print("  marketing cannot exceed evidence; claim ≠ proof; grade ≠ truth.")


if __name__ == "__main__":
    main()
