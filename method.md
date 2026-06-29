<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# method.md — how Ursprung works, and an honest index of what it contains

This file is the canonical statement of the **method** the repository practices, plus a **graded index** of
its parts. It is held to the same discipline it describes: it states what each component *is*, the evidence
behind it, and the boundary it does **not** cross. It is not a roadmap and not marketing. `claim ≠ proof`;
`integrity ≠ truth`.

## 1. The thesis

Ursprung treats software the way the Chronicle/Dentatus workbench treats measurement: a system should
**expose where its competence ends, where its assumptions begin, and where further investigation is
required.** Concretely, the repo's recurring act is to take a representation (a research kernel, a claim, a
spec) and produce an artifact whose guarantees are *measured and graded*, never asserted. The separators
below are the load-bearing maxims; the loop in §3 is how they get enforced.

## 2. The epistemic ladder (how every claim is graded)

| Grade | Meaning |
|-------|---------|
| **CLOSED** / **ESTABLISHED** | Established over the checked domain (exact or structural). |
| **BOUNDED** / **MEASURED** | Supported empirically on the sampled run; sample/parameterisation-relative. |
| **UNDERDETERMINED** | Not decided by the available evidence. |
| **VIOLATED** | A replayable counter-witness exists. |
| **REJECTED_AS_PROOF** | The cited mechanism does not prove the property it is invoked for. |
| **OPEN** | Known to be unproven; explicitly on the backlog. |

A **ghost** is an unexplained artifact, divergence, or residual. Ghosts are recorded as attention signals;
they allocate investigation — they do not certify a cause. `salience ≠ importance`.

## 3. The loop (the repeatable method)

1. **Research — code is authority.** Read the source, not the README/comments; treat prose claims as
   hypotheses. `claim ≠ code`.
2. **Port / harden — make it real.** Produce a compiling, dependency-light, deterministic module. Records of
   *rejected* design variants are preserved (e.g. in `PROVENANCE.md`). `file ≠ crate`.
3. **Measure, don't assert.** Surface invariant residuals every step (e.g. `‖WᵀW−I‖`, `‖s‖−1`, sphere/Stiefel
   residuals, Menger sparsity fraction, replay-hash parity). `invariant ≠ comment`.
4. **Grade.** Attach a ladder grade + a `does_not_show` + a `falsifier` to every claim.
5. **Gate — validity-not-outcome.** Tests assert the *apparatus* (the gate bites, the leak is caught, the
   ghost is flagged), never that a hoped result occurred. One command (`DVSM/verify.py`, `make verify`) must
   read `GATE PASSED`. `tested ≠ safe`; a red gate is decisive.
6. **Commercialize honestly (optional).** A buyer-facing claim is honest only if a *discharged* obligation
   backs it; the gate rejects any claim that exceeds its proof or uses hype language; compliance documents are
   *generated from* the gated ledger so they cannot drift. `warranty ≠ proof`; `generated ≠ executed`.

## 4. Separators (the maxims, enforced not decorative)

`integrity ≠ truth` · `claim ≠ code` · `router ≠ verifier` · `grounded ≠ true` · `observation ≠ authority` ·
`residual-CMI ≠ channel` · `proves-the-procedure ≠ proves-the-phenomenon` · `borrow-checker-clean ≠
air-gap-sound` · `bounded ≠ conservative` · `bounded-by-clamp ≠ stable-dynamics` · `certificate ≠
proof-of-everything` · `prediction ≠ causation` · `undetected ≠ absent` · `determinism ≠ validity` ·
`measured ≠ guaranteed` · `built ≠ adopted`.

## 5. Graded index of the repository

Maturity legend: **VERIFIED** (compiles / tests green, gate-covered) · **DEMONSTRATION** (runs, illustrative,
not a product) · **RESEARCH** (exploratory) · **SEALED** (external, read-only research object).

| Area | What it is | Maturity | Evidence | Does not show |
|------|-----------|----------|----------|---------------|
| `weltwerk/verify/` | The verification kernel: `engine`, `artifacts` (honesty contract), `epistemic_types` (`Grounded<T>`), `claim_ledger`, `orchestrator` (two chokepoints), `residual_channel`, `frontier_gate`, `certificate_compiler`; PO-1..10 ledger | **VERIFIED** | ~30 `test_*.py`; `PROOF_OBLIGATIONS.md` / `EVIDENCE_GRAPH.md` | that the discipline implies a correct *product* — it is the substrate, not the application |
| `weltwerk/` (sim, render, view, splat, authoring, scale, net, fps_demo, worlds) | Renderer / causal-world experiments and playable slices | **DEMONSTRATION / RESEARCH** | per-subfolder READMEs + tests | production fidelity; these are slices and probes, not a shipped renderer |
| `weltwerk/halvorsen/`, `weltwerk/stream_auditor/` | Attractor audit stack; first orchestrator backend client (profile C) | **VERIFIED** | their test suites | a sound discrete trapping certificate (OPEN for Halvorsen) |
| `DVSM/` (Python) | Auditors of the **external** DVSM-π+++ kernel: `coupling_audit` (forbidden-coupling CMI firewall), `invariant_ledger`, `dvsm_backend` (profile D), `dvsm_reference`, `kappa_remediation`, `discrete_certificate` | **VERIFIED** | `verify.py` gate, 10 suites green | properties of the shipped Rust kernel — results are reference-relative |
| `DVSM/reality_core/` (Rust) | Hardened 2-Layer Reality Core: geometric core + runtime + verification probe + C-ABI | **VERIFIED** | `cargo test` (26) + `reality_core_probe.py` | a conservative flow; bounded-by-normalization, not globally stable |
| `Rust/` (crate `ursprung`) | std-only port of the fundamentals + orchestrator (honesty contract & `Grounded<T>` as type-level invariants) | **VERIFIED** | `cargo test` | bit-identical parity with the Python (decisions match, floats need not) |
| `Rust/menger_telemetry/` | Hardened Menger-sponge telemetry kernel: Q32.32, in-tree SHA-256, real fractal depth, real `verify`, C-ABI, boundedness certificate | **VERIFIED** | `cargo test` (21) | dynamical stability — bounded by clamp, committed by hash, not "correct" |
| `DVSM/commercial/` | Proof-gated commercial layer: `kernel_auditor` (product API), `commercial_obligations` (no-overclaim gate), `binframe_adapter` (B3 lift), `compliance_doc` (gate-bound doc generator); AGPL + commercial dual-license | **VERIFIED (infrastructure)** | suites in `verify.py` | revenue or adoption — no customers; financial value is **SPECULATIVE**, this is de-risking, not money |
| `../Reality_Engine` | The sealed Chronicle workbench it descends from | **SEALED** | n/a (read-only) | n/a — immutable during this project |

## 6. Honest scope of the whole repo

Ursprung began as a deterministic high-fidelity **renderer** and has, in practice, become a **verification /
honesty workbench** (`weltwerk/verify`) plus (a) renderer & causal-world experiments, (b) hardened ports of
sibling research kernels (`reality_core`, `menger_telemetry`, the DVSM auditors), and (c) a proof-gated
commercial/compliance layer. The sibling-kernel work is *adjacent to*, not an advancement of, the original
renderer thesis — it is the discipline applied outward. Its value is as **demonstration of the method** and as
**reusable layers** (the verify kernel; the claim→compliance gate), not as adopted products. `adjacent ≠
on-mission`; `demonstration ≠ product`; `quantity ≠ coherence`.

## 7. Operating rules (for contributors and LLMs)

- Read the code, not the prose; record rejected variants. `claim ≠ code`.
- Measure invariants and surface them; never assert them in a comment. `invariant ≠ comment`.
- Keep it deterministic and dependency-light; a change that breaks replay is a regression. `determinism ≠ validity`, but losing it loses audit.
- A change is not done until the gate reads `GATE PASSED`. `tested ≠ safe`.
- Grade every new claim (ladder + `does_not_show` + `falsifier`); a commercial claim must rest on a discharged obligation. `grade ≠ truth`.
- State what a change does **not** establish. Overclaiming is the defect this repo exists to catch.

## 8. Provenance

This file indexes the repository as of the DVSM / Menger-sponge hardening work. Grades are point-in-time and
checkable: re-run `DVSM/verify.py` and the per-crate `cargo test` to confirm the **VERIFIED** rows. The
maturity grades themselves are a claim — falsifiable by a failing gate or a subfolder that does not run as
described. `written ≠ true`; verify it.
