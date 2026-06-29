<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# DVSM/ — auditing the DVSM-π+++ meta-kernel with the weltwerk verification stack

This subfolder applies Ursprung's `weltwerk/verify/` discipline to the **DVSM-π+++ meta-kernel**
(`github.com/Dedoc-9/dvsm-meta-kernel`) — a deterministic bounded-recurrence engine (Lie-bracket flow on a
Stiefel basis, fixed-point arithmetic, FNV-1a replay hashes, GhostSnap containment, a read-only observability
layer). DVSM's deployment manifest (`ReadMe.rs`) is already a list of invariants, **forbidden feedback
couplings**, failure modes, and a validation protocol — i.e. a proof-obligation ledger written in prose. This
batch makes those guarantees **mechanically checkable** and routes every verdict through the orchestrator's
two chokepoints. It **adds no authority** to DVSM. `router ≠ verifier`; `integrity ≠ truth`.

## The load-bearing boundary

We cannot execute the Rust kernel here, so the audit runs against a **reduced Python reference**
(`dvsm_reference.py`) that reproduces DVSM's *structure* (Lie evolution + EMA memory + Z→Ω drift + read-only
diagnostics + containment) but not its bit-exact trajectory. Everything graded is therefore a property of the
**reference** (or of the **procedure** run on it), never of the shipped kernel:

> `reference-model ≠ authoritative-kernel` · `proves-the-procedure ≠ proves-the-phenomenon`

To audit the real kernel, feed actual `BinaryFrame` / Q-type trace dumps into the same backend (the frame is
already `repr(C)`, ABI-stable, delta-encoded — the stream the auditor was built for).

## Modules

- **`dvsm_reference.py`** — the reduced reference recurrence + planted clean/contaminated trace generators.
  It uses the kernel's **actual** `κ_{kj} = sin(k·1.37 − j·1.73)` init, so the auditor catches the real
  skew-symmetry discrepancy rather than a sanitised one.
- **`coupling_audit.py`** — the **forbidden-feedback-coupling firewall** (the killer app). Built on
  `weltwerk/verify/residual_channel`, it tests whether a diagnostic channel `X` leaks information into a
  future dynamics channel `Y` beyond the legitimate drivers `Z` (confounder-conditioned CMI + shuffle null +
  a refine-with-`W` mis-specification stress). `AIR_GAP_HELD` / `OBSERVER_CONTAMINATION` / `CONFOUNDED_ARTIFACT`
  / `UNIDENTIFIABLE`. `borrow-checker-clean ≠ air-gap-sound`.
- **`invariant_ledger.py`** — the manifest invariants re-expressed as graded obligations
  (`CLOSED` / `BOUNDED` / `VIOLATED` / `REJECTED_AS_PROOF` / `UNDERDETERMINED`), each with a witness, a
  `does_not_show`, and a falsifier; cross-checked by `claim_ledger.audit_ledger`.
- **`dvsm_backend.py`** — the DVSM Trace Auditor (routing **profile D**), a client of
  `weltwerk/verify/orchestrator.py` that **reuses `OrchestratedBackend` unchanged**. Answer chokepoint =
  per-coupling `AnalysisResult` (side by side, **no fused scalar**); action chokepoint = "certify this
  window's telemetry as controller-safe" gated by `NoHiddenChannel` — a contaminated window raises
  `UngroundedError` **before** any effect. `frontier_gate` deflates the novelty-coverage metric.

## Findings (the ghosts this batch already caught)

1. **κ is not skew-symmetric.** The kernel comment asserts `κ[i,j] = −κ[j,i]` for `sin(i·1.37 − j·1.73)`, but
   that holds only if `1.37 = 1.73`. The worst witness is the **diagonal** (`max|κ+κᵀ| ≈ 1.76` at `(3,3)`) —
   a skew matrix must be hollow, and this one isn't. The energy law `d‖Z‖²/dt = −2λ‖Z‖²` leans on that
   premise. Status: **VIOLATED** (exact arithmetic). `claimed-skew ≠ actual-skew`.
2. **The energy law does not certify the discrete kernel.** It is the continuous identity; the executed map
   is explicit-Euler, non-skew κ, saturating fixed-point, with a drive term. Status: **REJECTED_AS_PROOF**
   (mirrors the Halvorsen quadratic-V rejection). A discrete-time Lyapunov certificate is **OPEN**.
3. **Identifiability boundary.** `Ω→V` and `ν→λ` are detectable (the diagnostic varies independently of `Z`).
   `Stiffness→Dynamics` is **UNIDENTIFIABLE**: stiffness ≈ 2|z₀| is a function of the conditioned `z₀`, so a
   positive CMI cannot be told from binning-resolution confounding. The firewall **declines to rule** rather
   than emit a false positive. `undetected ≠ absent`; `detected-on-unidentifiable ≠ contamination`.

## Run (PowerShell, folder-directed)

```powershell
cd "C:\Users\dillb_lzxy763\Claude\Projects\Ursprung\DVSM"
$env:PYTHONHASHSEED=0
python dvsm_reference.py
python coupling_audit.py
python invariant_ledger.py
python dvsm_backend.py
python test_dvsm_reference.py
python test_coupling_audit.py
python test_invariant_ledger.py
python test_dvsm_backend.py
```

Pure-stdlib; imports `../weltwerk/verify/` (residual_channel, artifacts, claim_ledger, epistemic_types,
frontier_gate, orchestrator) and `../weltwerk/stream_auditor/` (`OrchestratedBackend`) **unchanged**. Tests
assert the apparatus, not a happy outcome (validity-not-outcome): the firewall separates a planted leak from
an air-gapped trace, the ledger catches the ghosts instead of rubber-stamping them, and only an air-gap-held
window may be certified controller-safe. `tested ≠ safe`; `measured ≠ guaranteed`.

## Sealing note

DVSM is treated as a **read-only research object** (the auditor replays/observes telemetry, never mutates
kernel state) — the same shadow-evaluation discipline Ursprung applies to the sealed `Reality_Engine`.
