<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# DVSM/ — auditing the DVSM-π+++ meta-kernel with the weltwerk verification stack

This subfolder applies Ursprung's `weltwerk/verify/` discipline to the **DVSM-π+++ meta-kernel**
(`github.com/Dedoc-9/dvsm-meta-kernel`) — a deterministic bounded-recurrence engine (Lie-bracket flow on a
Stiefel basis, fixed-point arithmetic, FNV-1a replay hashes, GhostSnap containment, a read-only observability
layer). DVSM's deployment manifest (`ReadMe.rs`) is already a list of invariants, **forbidden feedback
couplings**, failure modes, and a validation protocol — a proof-obligation ledger written in prose. This work
makes those guarantees **mechanically checkable**, routes every verdict through the orchestrator's two
chokepoints, ports the audit layers to Rust, and packages them into the `ursprung-gateway` binary. It **adds
no authority** to DVSM. `router ≠ verifier`; `integrity ≠ truth`.

## The load-bearing boundary

We cannot execute the Rust kernel here, so the audit runs against a **reduced Python reference**
(`dvsm_reference.py`) that reproduces DVSM's *structure* (Lie evolution + EMA memory + Z→Ω drift + read-only
diagnostics + containment) but not its bit-exact trajectory. Everything graded is therefore a property of the
**reference** (or of the **procedure** on it), never of the shipped kernel:

> `reference-model ≠ authoritative-kernel` · `proves-the-procedure ≠ proves-the-phenomenon`

To audit the real kernel, feed actual `BinaryFrame` dumps into `commercial/binframe_adapter.py` (or the Rust
`ursprung-gateway`), which lifts the obligations the public frame can support and **honestly declares** the
ones it cannot.

## Modules

**Audit core**
- **`dvsm_reference.py`** — the reduced reference recurrence + planted clean/contaminated trace generators. It
  uses the kernel's **actual** `κ_{kj} = sin(k·1.37 − j·1.73)` init, so the auditor catches the real
  skew-symmetry discrepancy, not a sanitised one.
- **`coupling_audit.py`** — the **forbidden-feedback-coupling firewall** (the killer app). Built on
  `weltwerk/verify/residual_channel`: does a diagnostic `X` leak into a future dynamics channel `Y` beyond the
  legitimate drivers `Z` (confounder-conditioned CMI + shuffle null + refine-with-`W` mis-spec stress)?
  → AIR_GAP_HELD / OBSERVER_CONTAMINATION / CONFOUNDED_ARTIFACT / UNIDENTIFIABLE. `borrow-checker-clean ≠ air-gap-sound`.
- **`invariant_ledger.py`** — manifest invariants as graded obligations (CLOSED / BOUNDED / VIOLATED /
  REJECTED_AS_PROOF / UNDERDETERMINED), each with a witness, a `does_not_show`, and a falsifier.
- **`dvsm_backend.py`** — the DVSM Trace Auditor (routing **profile D**), a client of the orchestrator that
  reuses `OrchestratedBackend` unchanged; per-window `AnalysisResult` (no fused scalar), and a "certify this
  window controller-safe" action gated by `NoHiddenChannel` — contamination raises `UngroundedError` before any effect.
- **`kappa_remediation.py`** — antisymmetrize `κ ← (κ−κᵀ)/2` to a hollow, skew-symmetric matrix; the skew
  obligation flips **VIOLATED → CLOSED** (`max|κ+κᵀ| = 0`). The precondition for the certificate below.
- **`discrete_certificate.py`** — a **checkable discrete-time contraction certificate**: the *sufficient*
  condition `2‖κ‖_F·σ < λ ∧ dt·λ ≤ 1 ⇒ ρ < 1`, with the noise-margin `σ_max` and `ρ` stated. `certificate ≠ proof-of-everything`.

**Commercial layer (`commercial/`)** — the proof-gated product surface; AGPL-3.0 + a separate commercial license.
- **`ledger.tsv` + `obligations.tsv`** — the **single source of truth** for the claims ledger and the
  obligation registries (loaded by both `commercial_obligations.py` *and* the Rust `shipped_ledger()`).
- **`commercial_obligations.py`** — a buyer-facing claim is honest only if a *discharged* obligation backs it;
  the gate refuses overclaim / undischarged-support / hype / unknown-reference. Now **live-bindable**
  (Obligation B): `audit_commercial_ledger(claims, live_receipts=…)` adds an `unverified_live` check — a
  supported claim's backing suite must read `PASS` in a fresh build receipt. `static-check ≠ live-execution`; `receipt ≠ proof`.
- **`compliance_doc.py`** — a disclaimer-first compliance doc *generated from* the gated ledger (it cannot
  exceed the proofs; figures are `[PLACEHOLDER]` for counsel). `warranty ≠ proof`; `generated ≠ executed`.
- **`binframe_adapter.py`** — real `BinaryFrame` ingest (the B3 lift): parse + validate, lift the obligations a
  dump supports, and declare the Ω→V / ν→λ air-gaps **non-liftable** (the public frame omits `v` / `λ`).
- **`kernel_auditor.py`** — generic product probes over real telemetry.

**Rust port** — `reality_core/` (the hardened 2-layer reality core) plus the audit layers in `../Rust/`
(`binframe_adapter`, `invariant_ledger`, `commercial_obligations`, `coupling_audit`) and the `ursprung-gateway`
binary that composes them. Differential-tested against this Python; `parts ≠ whole`.

## Findings (the ghosts this caught)

1. **κ is not skew-symmetric** as initialised — `sin(i·1.37 − j·1.73)` is skew only if `1.37 = 1.73`; worst
   witness on the **diagonal** (`max|κ+κᵀ| ≈ 1.76`). Status **VIOLATED** (exact); `kappa_remediation` flips it
   to **CLOSED**. `claimed-skew ≠ actual-skew`.
2. **The energy law does not certify the discrete kernel** — continuous identity vs explicit-Euler, non-skew
   κ, saturating fixed-point + drive. Status **REJECTED_AS_PROOF**; the discrete certificate is the
   *sufficient-condition* answer (`discrete_certificate.py`), not a global proof.
3. **Identifiability boundary** — `Ω→V`, `ν→λ` are detectable; `Stiffness→Dynamics` is **UNIDENTIFIABLE**
   (stiffness ≈ 2|z₀| is a function of the conditioned `z₀`). The firewall **declines to rule** rather than
   emit a false positive. `undetected ≠ absent`.

## Run — one gate (PowerShell, folder-directed)

```powershell
cd DVSM               # from the repo root
python verify.py      # the single CI gate: 12 suites + the LIVE commercial gate (Obligation B), one exit code
```

`verify.py` runs every suite as an isolated subprocess (forcing UTF-8 so the κ/‖/σ separators survive cp1252),
then — on a full run — emits a fresh `.verify_receipt.tsv` and runs the **live** commercial gate: a supported
claim is only counted discharged if its backing suite PASSED *this run*. It prints `GATE PASSED` + `LIVE GATE
PASSED` and exits non-zero on any failure. Pure-stdlib; imports `../weltwerk/verify/` and
`../weltwerk/stream_auditor/` unchanged. Tests assert the apparatus, not a happy outcome (`tested ≠ safe`;
`measured ≠ guaranteed`).

Individual modules/tests still run standalone (e.g. `python coupling_audit.py`, `python commercial/test_live_gate.py`).

## Sealing note

DVSM is a **read-only research object** (the auditor replays/observes telemetry, never mutates kernel state) —
the same shadow-evaluation discipline Ursprung applies to the sealed `Reality_Engine`.
