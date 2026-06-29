<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# DVSM Kernel Telemetry Auditor — commercial edition

A product surface over the verified DVSM audit stack. Point it at **your** deterministic kernel's telemetry
and it tells you, with graded honesty, where a diagnostic channel is leaking into dynamics (observer
contamination) — and refuses to certify telemetry it cannot vouch for. It is **open-core**: the engine is
AGPL-3.0-only; closed/SaaS/embedded use is covered by a separate commercial license
(`LICENSE-COMMERCIAL.md`).

The distinguishing feature is not a number. It is that **every claim this product makes to you is proof-gated**:
no marketing or SLA statement may exceed a discharged technical obligation (`commercial_obligations.py`). The
hype the rest of the market sells is, here, a build failure.

## Who it's for

Teams shipping deterministic numerical kernels where a "read-only" diagnostic must stay read-only: physics /
simulation engines, DSP & RF/SIGINT pipelines, control loops, telemetry-driven safety gates, quant/recsys
feature kernels. If your design doc says "this observer must not influence state," this product *measures*
whether that holds in the emitted telemetry.

## What you get

| Tier | Contents | License |
|------|----------|---------|
| **Open core** | `coupling_audit`, `invariant_ledger`, `dvsm_backend`, the reference, all tests | AGPL-3.0-only |
| **Commercial** | `KernelAuditor` product surface, customer-probe schema, integration on your telemetry, real-`BinaryFrame` lift, support | Commercial license |

## The claims — and their boundaries (proof-gated)

Every row below is enforced by `test_commercial_obligations.py`: a SUPPORTED claim must rest on a **discharged**
obligation; boundary rows are downgraded on purpose.

**What it does (supported):**

- **C1** Detects *identifiable* diagnostic→dynamics leaks in your telemetry. (MEASURED)
- **C2** Refuses to certify contaminated/unidentifiable telemetry as controller-safe — atomically. (ESTABLISHED)
- **C3** Every finding carries scope + ≥1 limitation; no fused "health score." (ESTABLISHED)
- **C4** Deterministic, reproducible reports. (ESTABLISHED)
- **C5** Works on your kernel via customer-defined probes over arbitrary columns. (MEASURED, commercial)
- **C6** States where it is blind (UNIDENTIFIABLE), instead of falsely clearing. (ESTABLISHED)

**What it does NOT do (boundary — stated in the contract):**

- **B1** Does NOT guarantee your kernel is numerically bounded — the continuous energy law does not certify the
  discrete map; a discrete Lyapunov certificate is OPEN. (NOT_MEASURED)
- **B2** Does NOT detect *every* coupling — only identifiable ones. `undetected ≠ absent`. (NOT_MEASURED)
- **B3** Reference-model results are reference-relative until run on your real trace dumps. (UNDERDETERMINED)

`integrity ≠ truth` · `borrow-checker-clean ≠ air-gap-sound` · `residual-CMI ≠ channel` ·
`proves-the-procedure ≠ proves-the-phenomenon`.

## Integration (commercial)

1. Export your kernel's per-frame telemetry as rows (dicts) — the DVSM `BinaryFrame` is already `repr(C)`,
   ABI-stable and delta-encoded, so a thin dumper suffices.
2. Declare a `CouplingProbe` per "this must not influence that" rule (diagnostic `x`, dynamics `y`, legitimate
   drivers `z`, candidate confounder `w`). Bin continuous channels at ingest.
3. `KernelAuditor(probes).audit(rows)` → per-window posture; `certify(window, probe, action)` gates any
   downstream "trust this telemetry" effect behind the Grounded chokepoint.

## Run

```powershell
cd DVSM/commercial    # from the repo root
$env:PYTHONHASHSEED=0
python kernel_auditor.py
python commercial_obligations.py
python test_kernel_auditor.py
python test_commercial_obligations.py
```

Pure-stdlib; reuses `../coupling_audit.py` and `../../weltwerk/verify/` + `stream_auditor`'s
`OrchestratedBackend` unchanged. `tested ≠ safe`; `measured ≠ guaranteed`.
