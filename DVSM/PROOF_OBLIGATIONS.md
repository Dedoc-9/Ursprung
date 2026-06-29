<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# DVSM — Proof Obligations

The DVSM-π+++ deployment manifest (`ReadMe.rs`) re-expressed as checkable obligations, with the module that
discharges each and the current status **on the reduced reference**. Status is reference-relative —
`reference-model ≠ authoritative-kernel`; `proves-the-procedure ≠ proves-the-phenomenon`. To lift any row to
the shipped kernel, re-run the same checks on real `BinaryFrame` trace dumps.

Status vocabulary: **CLOSED** (established over the checked domain) · **BOUNDED** (empirical, sample-relative) ·
**VIOLATED** (replayable counter-witness) · **REJECTED_AS_PROOF** (the cited mechanism does not prove the
property) · **UNDERDETERMINED** / **UNIDENTIFIABLE** (not decided by the available evidence).

| ID | Manifest source | Obligation | Discharged by | Status (reference) |
|----|-----------------|------------|---------------|--------------------|
| DVSM-1 | §2 Skew-Symmetry | `κ[k,j] = −κ[j,k]` as the comment claims | `invariant_ledger.obl_kappa_skew` | **VIOLATED** — `max|κ+κᵀ| ≈ 1.76` at the diagonal `(3,3)`; a skew matrix must be hollow |
| DVSM-2 | §1 Numerical Stability | the energy law `d‖Z‖²/dt = −2λ‖Z‖²` certifies the discrete kernel is bounded | `invariant_ledger.obl_energy_law` | **REJECTED_AS_PROOF** — continuous identity; executed map is Euler + non-skew κ + drive |
| DVSM-3 | §7 Failure-mode containment | `‖Z‖` stays under `U_MAX` (GhostSnap recovers excursions) | `invariant_ledger.obl_containment_bounded` | **BOUNDED** — `max‖Z‖ ≈ 0.105` over the run; empirical, not certified |
| DVSM-4 | §5 NO ν → λ | `∂λ/∂ν = 0` (novelty does not modulate dissipation) | `invariant_ledger.obl_lambda_constant` → `coupling_audit` | **CLOSED** clean / **VIOLATED** when planted |
| DVSM-5 | §3/§5 Observability Separation | no identifiable diagnostic feeds dynamics (air-gap held) | `invariant_ledger.obl_observability_separation` → `coupling_audit` | **CLOSED** clean / **VIOLATED** when planted |
| DVSM-6 | User Guarantee: Deterministic Ordering | same seed reproduces an identical replay-hash sequence | `invariant_ledger.obl_determinism` | **CLOSED** — `integrity ≠ truth`; cross-precision parity NOT tested (Q16/Q31/Q64 differ) |
| DVSM-7 | §5 NO Ω → V | long-term drift does not influence instantaneous velocity | `coupling_audit` (`omega_to_v`) | **AIR_GAP_HELD** clean / **OBSERVER_CONTAMINATION** when planted (identifiable) |
| DVSM-8 | §4 NO Stiffness → Dynamics | V17-K diagnostic does not feed the field | `coupling_audit` (`stiffness_to_z`) | **UNIDENTIFIABLE** — stiffness ≈ 2|z₀| ⊂ conditioning set; the firewall declines to rule |

## Open obligations (honest backlog)

- **A discrete-time boundedness certificate** for the saturating fixed-point map (the real DVSM-2). The
  continuous energy law is rejected as a proof; a Lyapunov / trapping certificate is the z3-bound profile-A
  job — **OPEN**.
- **Cross-precision replay parity** as a measured FP-ghost (Q16 vs Q31 vs Q64 hash divergence). Recorded as a
  limitation under DVSM-6; not yet an executed obligation. `hash ≠ reality`.
- **Real-kernel lift**: every CLOSED/BOUNDED row above is reference-relative until re-run on emitted
  `BinaryFrame` traces from the Rust kernel.

## Evidence

All obligations are exercised by `test_invariant_ledger.py`, `test_coupling_audit.py`,
`test_dvsm_backend.py`, and `test_dvsm_reference.py` (29 validity-not-outcome checks total). The tests assert
the apparatus is sound (ghosts caught, leaks separated from air-gapped traces, contaminated telemetry refused
atomically), never that a hoped-for result occurred. `tested ≠ safe`.
