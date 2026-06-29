# SPDX-License-Identifier: AGPL-3.0-only
"""
invariant_ledger.py — the DVSM deployment manifest (ReadMe.rs §2 invariants, §5 forbidden couplings, §8
validation protocol) re-expressed as MECHANICALLY CHECKABLE obligations, each carrying its grade, its
witness, the boundary it does NOT establish, and the observation that would falsify it.

Status vocabulary (deliberately not binary):
  CLOSED            — established over the checked domain (exact/structural, reference-relative).
  BOUNDED           — supported EMPIRICALLY on the sampled run; not a guarantee (sample/parameterisation-relative).
  VIOLATED          — a counter-witness exists (replayable).
  REJECTED_AS_PROOF — the stated mechanism does not prove the property it is invoked for (mirrors the
                      Halvorsen quadratic-V rejection: continuous-law ≠ discrete-kernel boundedness).
  UNDERDETERMINED   — not decided by the available evidence.

`integrity ≠ truth`; `proves-the-procedure ≠ proves-the-phenomenon`; `empirical-boundedness ≠ certified`.
Everything here grades the REFERENCE (and the procedure on it), never the executed Rust kernel.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))
from artifacts import AnalysisResult, Finding, Limitation           # noqa: E402
from claim_ledger import Claim, audit_ledger                        # noqa: E402

from dvsm_reference import (DvsmReference, kappa_matrix, gen_clean, U_MAX, LAMBDA0, DT, R, StepRecord)
from coupling_audit import audit_coupling, _BY_NAME

CLOSED, BOUNDED, VIOLATED, REJECTED_AS_PROOF, UNDERDETERMINED = (
    "CLOSED", "BOUNDED", "VIOLATED", "REJECTED_AS_PROOF", "UNDERDETERMINED")

# status → claim_ledger grade (for the cross-check that the ledger stays honest)
_GRADE = {CLOSED: "ESTABLISHED", BOUNDED: "MEASURED", VIOLATED: "ESTABLISHED",
          REJECTED_AS_PROOF: "ESTABLISHED", UNDERDETERMINED: "UNDERDETERMINED"}


@dataclass(frozen=True)
class ObligationResult:
    id: str
    statement: str
    status: str
    witness: str
    does_not_show: str
    falsifier: str

    def as_analysis(self) -> AnalysisResult:
        findings = (
            Finding("OBLIGATION", "manifest-invariant", self.statement),
            Finding("STATUS", "manifest-invariant", self.status),
            Finding("WITNESS", "manifest-invariant", self.witness),
        )
        limitations = (
            Limitation("manifest-invariant", f"does not show: {self.does_not_show}"),
            Limitation("scope", "graded over the REFERENCE; reference-model ≠ authoritative-kernel"),
        )
        return AnalysisResult(source_trace=(), scope="manifest-invariant",
                              findings=findings, limitations=limitations)

    def as_claim(self) -> Claim:
        return Claim(f"INV::{self.id}", self.statement, _GRADE[self.status],
                     f"status={self.status}; {self.witness}", self.does_not_show, self.falsifier)


# ---- the obligations (each maps the manifest to a check) ------------------------------------------
def obl_kappa_skew(r: int = R) -> ObligationResult:
    """§2 Skew-Symmetry: κ[k,j] = −κ[j,k]. The kernel comment asserts this for κ=sin(k·1.37−j·1.73)."""
    k = kappa_matrix(r)
    worst = (0, 0, 0.0)
    for i in range(r):
        for j in range(r):
            v = abs(k[i][j] + k[j][i])
            if v > worst[2]:
                worst = (i, j, v)
    status = CLOSED if worst[2] < 1e-9 else VIOLATED
    return ObligationResult(
        "kappa_skew_symmetry", "κ is skew-symmetric (κ[k,j] = −κ[j,k]) as the comment claims", status,
        f"max|κ+κᵀ|={worst[2]:.4f} at (k,j)=({worst[0]},{worst[1]})  [0 ⇒ skew]",
        "that the kernel mis-runs — only that the ENERGY LAW's skew-symmetry premise is false as initialised",
        "antisymmetrise κ ← (κ−κᵀ)/2; then max|κ+κᵀ| → 0 and the premise is restored")


def obl_energy_law(trace: List[StepRecord]) -> ObligationResult:
    """§1 Numerical Stability via d‖Z‖²/dt = −2λ‖Z‖². Tested AS A BOUNDEDNESS PROOF for the discrete map."""
    pred_vs_actual = []
    for a, b in zip(trace, trace[1:]):
        e2a, e2b = a.energy ** 2, b.energy ** 2
        predicted = -2.0 * LAMBDA0 * e2a * DT
        actual = e2b - e2a
        denom = max(abs(predicted), 1e-9)
        pred_vs_actual.append(abs(actual - predicted) / denom)
    mean_rel = sum(pred_vs_actual) / max(1, len(pred_vs_actual))
    # the continuous identity does NOT govern the executed map (explicit-Euler + non-skew κ + drive term)
    return ObligationResult(
        "energy_law_as_boundedness", "the continuous law d‖Z‖²/dt = −2λ‖Z‖² proves the discrete kernel is bounded",
        REJECTED_AS_PROOF,
        f"mean |Δ‖Z‖² − (−2λ‖Z‖²dt)| / |pred| = {mean_rel:.2f} over the run (continuous identity not obeyed step-wise)",
        "that the discrete fixed-point kernel is unbounded — only that THIS law does not certify boundedness",
        "a discrete-time Lyapunov / trapping certificate for the saturating fixed-point map (OPEN)")


def obl_containment_bounded(trace: List[StepRecord]) -> ObligationResult:
    """§7 Failure-mode containment: ‖Z‖ stays under U_MAX (GhostSnap recovers excursions)."""
    mx = max(r.energy for r in trace)
    status = BOUNDED if mx < U_MAX else VIOLATED
    return ObligationResult(
        "containment_boundedness", "‖Z‖ remains under the containment bound U_MAX on the run", status,
        f"max‖Z‖={mx:.3f} over {len(trace)} frames (bound={U_MAX})",
        "boundedness for ALL inputs/parameterisations — only for this sampled trajectory",
        "an input/parameterisation that drives ‖Z‖ ≥ U_MAX without GhostSnap recovery")


def obl_lambda_constant(trace: List[StepRecord]) -> ObligationResult:
    """§5 NO ν→λ: dissipation must not depend on novelty. Checked via the coupling firewall on the trace."""
    r = audit_coupling(trace, _BY_NAME["novelty_to_lambda"], seed=33)
    status = CLOSED if r.verdict == "AIR_GAP_HELD" else (VIOLATED if r.verdict == "OBSERVER_CONTAMINATION"
                                                         else UNDERDETERMINED)
    return ObligationResult(
        "lambda_constant", "∂λ/∂ν = 0 (novelty does not modulate dissipation) on the trace", status,
        f"coupling firewall: {r.verdict} (I(ν;λ)={r.result.cmi:.3f})",
        "the Rust kernel's λ — only the reference trace's λ–ν relationship",
        "a trace with I(ν;λ) > shuffle null beyond legitimate drivers")


def obl_observability_separation(trace: List[StepRecord]) -> ObligationResult:
    """§3/§5 Observability Separation: no IDENTIFIABLE diagnostic leaks into dynamics."""
    from coupling_audit import COUPLINGS
    res = [audit_coupling(trace, c, seed=44) for c in COUPLINGS if c.identifiable]
    leaks = [r.name for r in res if r.verdict == "OBSERVER_CONTAMINATION"]
    status = CLOSED if not leaks else VIOLATED
    return ObligationResult(
        "observability_separation", "no identifiable diagnostic channel feeds dynamics (air-gap held)", status,
        f"identifiable couplings audited: {[r.verdict for r in res]}",
        "absence of UNIDENTIFIABLE couplings (diagnostic = function of legit state); undetected ≠ absent",
        "any identifiable diagnostic→dynamics coupling reading OBSERVER_CONTAMINATION")


def obl_determinism(seed: int = 5, n: int = 400) -> ObligationResult:
    """§ User Guarantee Deterministic Ordering: same seed ⇒ identical replay hash sequence."""
    a = [r.hash for r in DvsmReference(seed=seed).run(n)]
    b = [r.hash for r in DvsmReference(seed=seed).run(n)]
    status = CLOSED if a == b else VIOLATED
    return ObligationResult(
        "determinism_replay", "same seed reproduces an identical replay-hash sequence", status,
        f"{n} frames; hash sequences identical = {a == b}",
        "CORRECTNESS or cross-PRECISION parity — integrity ≠ truth; hash ≠ reality; Q16/Q31/Q64 differ",
        "identical seed yielding divergent hashes (a nondeterminism leak)")


def evaluate(trace: Optional[List[StepRecord]] = None) -> List[ObligationResult]:
    """Evaluate every obligation. Trace-dependent ones use the supplied trace (default: a clean run)."""
    trace = trace if trace is not None else gen_clean(4000)
    return [
        obl_kappa_skew(),
        obl_energy_law(trace),
        obl_containment_bounded(trace),
        obl_lambda_constant(trace),
        obl_observability_separation(trace),
        obl_determinism(),
    ]


def main():
    print("invariant_ledger.py — DVSM manifest → checkable obligations (integrity ≠ truth)\n")
    obs = evaluate()
    for o in obs:
        print(f"  [{o.status:17s}] {o.id:24s} {o.witness}")
    ledger = [o.as_claim() for o in obs]
    print(f"\n  claim-ledger honest: {audit_ledger(ledger)['honest']}")
    print("  the κ ghost and the energy-law rejection are FINDINGS, recorded not hidden. "
          "proves-the-procedure ≠ proves-the-phenomenon.")


if __name__ == "__main__":
    main()
