<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# stream_auditor/ — the first backend client of `orchestrator.py`

A domain-agnostic **Causal Stream Auditor** (routing profile **C**) that turns the orchestrator's two chokepoints
into an inescapable runtime reality on a live, multi-dimensional stream (simulated physics, telemetry, or
financial / ad-attribution time-series). It consumes `weltwerk/verify/` unchanged; it adds **no authority**.
`router ≠ verifier`; `composition ≠ capability`; `integrity ≠ truth`.

## What it does

Window a stream of rows `(…columns…)`; a `ChannelSpec(x, y, z, w)` selects two channels `X, Y`, the modeled
confounder `Z`, and a candidate confounder `W`. Per window:

- **Answer chokepoint.** `residual_channel` conditions `X, Y` on `Z` (CMI + shuffle null) and stress-tests with
  a **refine-with-`W`** mis-specification. The window's finding is an `AnalysisResult` and a graded
  `claim_ledger.Claim`. Windows are reported **side by side — never fused into one confidence scalar**; the
  disagreement across windows is the finding.
  - `CONSISTENT_WITH_NULL` → **HEALTHY** (all coupling explained by `Z`)
  - `RESIDUAL_MISSPEC_STABLE` → **CHANNEL** (a real dependence that survives conditioning on `(Z, W)`)
  - `RESIDUAL_MISSPEC_FRAGILE` → **MISSPEC** (a missing-confounder artifact that dissolves under `(Z, W)`)
- **Action chokepoint.** `promote(window, action)` runs the downstream act **only** through
  `orchestrator.enact`, grounded by `ChannelEstablished` (decision == CHANNEL). A `HEALTHY` or `MISSPEC` window
  raises `UngroundedError` **before** the action body — atomic refusal, state pristine. *Don't deploy on a
  fragile or confounder-explained signal.*
- **Metric deflation.** `frontier_gate` reads the window-over-window coverage multiplier; when it goes
  subcritical the auditor emits a **bounded** `PIVOT` (re-window / re-baseline / widen the confounder set),
  never "the stream keeps improving."

## Boundaries (load-bearing)

`residual-CMI ≠ channel` — a surviving residual is a *candidate*, not proof; conditioning is only as good as the
**modeled** `(Z, W)` (the complete confounder set is unattainable). Results are window-relative
(nonstationarity). Continuous streams must be **binned by the caller** (the bundled generators are discrete).
This proves a property of the **decision procedure** on the modeled stream, not a physical fact —
`proves-the-procedure ≠ proves-the-phenomenon`.

## Profiles (the scaffolding)

`OrchestratedBackend` (two chokepoints via the orchestrator) is the base. **C** (`CausalStreamAuditor`) is built
here. **A** (SMT trapping-region engine) and **B** (code-synthesis linter) inherit the same base as alternative
routing profiles — *not built here* (A is z3-bound and fail-closes without a sound certificate; B's proof oracle
is the open part). `improved_map ≠ changed_criterion`.

## Files & run

`stream_auditor.py` (`OrchestratedBackend`, `CausalStreamAuditor`, `ChannelSpec`, synthetic streams) +
`test_stream_auditor.py` (8 validity-not-outcome checks). Pure-stdlib; reuses `../verify/` unchanged
(orchestrator, residual_channel, epistemic_types, claim_ledger, frontier_gate, artifacts).

```powershell
cd "weltwerk\stream_auditor"; python stream_auditor.py; python test_stream_auditor.py
```

The tests assert the gates, not a happy outcome: a confirmed CHANNEL promotes; a MISSPEC/HEALTHY window is
refused atomically; every answer is an `AnalysisResult`; the panel carries no scalar; coverage attrition fires a
bounded pivot. `tested ≠ safe`; `measured ≠ guaranteed`.
