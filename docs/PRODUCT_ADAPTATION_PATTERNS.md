<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Product adaptation patterns — domain layers behind Ursprung's checkable conditions

**Status: analysis, not a roadmap.** This document maps the *already-built, already-tested* gateway layers onto
domain-adaptation patterns. It builds nothing and claims nothing new. Every pattern is a **domain adapter the
buyer must write**, positioned *behind* a checkable, **sufficient** mathematical condition that ships today, and
every pattern carries its `does_not_show`. The honest, graded index of what exists is [`../method.md`](../method.md);
the gateway contract is [`../GATEWAY_SPEC.md`](../GATEWAY_SPEC.md). `claim ≠ code`; `integrity ≠ truth`;
`tested ≠ safe`; `described ≠ built`.

> **What this is NOT.** Not a "safety gateway," not "hardware-validated," not "the world's first" anything. The
> gateway certifies four narrow things over telemetry dumps (below). Run the banner through the repo's own
> `commercial_obligations` HYPE gate and it is **rejected**. This document is written to stay on the right side
> of that gate.

---

## 1. The four validated layers, as they actually exist in code

Each layer is a real, differential-tested function with a fixed input schema, a typed verdict, and a fail-closed
exit. Nothing below is aspirational — it is the surface in `Rust/src/` confirmed by 88 green tests.

| Layer | Module / entry fn | Input schema (size) | Typed verdict | Fail-closed |
|---|---|---|---|---|
| **L1 ingest + obligation-lift** | `gateway::run_gateway_streaming` | TELEM 44 B / ABI 42 B | `ObligationStatus` ∈ {Closed, Bounded, Violated, RejectedAsProof, Underdetermined} + non-liftable set | exit `1` on layout_mismatch / non-finite / VIOLATED / dishonest ledger |
| **L2 contraction certifier** | `gateway::run_cert_streaming` → `contraction_cert::certify` | `SCHEMA_KAPPA` 160 B (frame + 16 κ row-major + λ,dt,σ, n=4) | `CertDecision` ∈ {ContractiveCert, NotCertified} | exit `1` on NOT_CERTIFIED / non-finite / partial |
| **L3 coupling firewall** | `gateway::run_coupling_streaming` → `coupling_audit::audit_coupling` | `SCHEMA_CMI` 32 B (x, y, z0, w0) | `CouplingVerdict` ∈ {AirGapHeld, ObserverContamination, ConfoundedArtifact, Unidentifiable} | exit `1` on OBSERVER_CONTAMINATION / non-finite / partial |
| **L4 proof-gated ledger** | `commercial_obligations::shipped_ledger().audit_live(receipts)` | `ledger.tsv` + `obligations.tsv` + `.verify_receipt.tsv` | `CommercialAudit { honest, exceeds_proof, hype, unknown_obligation, missing_boundary, unverified_live }` | exit `1` if a supported claim's suite did not PASS this build, or prose exceeds proof |

The binary `ursprung-gateway` composes these from a dump and returns `ExitCode::SUCCESS` (0) on PASS,
`ExitCode::FAILURE` (1) on any block, `ExitCode::from(2)` on a usage error. The streaming readers are zero-copy
in spirit but copy into typed fields; they hold **one record + running aggregates** (L1/L2) so memory is O(1)
per record — except L3, which collects the sample set because CMI binning is inherently O(samples).

---

## 2. The measured latency envelope — what each layer is *licensed* to do

This is the load-bearing section: it decides which patterns are physically possible. Numbers are the
[`GATEWAY_SPEC.md §6`](../GATEWAY_SPEC.md) reference run (one Windows host, single run, `--release`), bounded as
point-in-time and non-universal.

| Layer | Parse throughput | Full-gate throughput | Inline-capable? |
|---|---|---|---|
| L1 (telem/abi) | ~700–910 MB/s | ~same (fold) | **Yes** — per-record, ~30–50 ns |
| L2 (kappa) | ~1.6 GB/s | **263 MB/s** (~600 ns/block, `--samples 0`) | **Yes** — fast enough for per-control-step certification |
| L3 (cmi) | ~690 MB/s | **9.7 MB/s** (reps=20, one-shot audit) | **No** — ~70× slower than its own parse |

**The consequence, stated plainly:** L1 and L2 can run *inline* in a hot loop; **L3 cannot**. The CMI firewall
is a **windowed, periodic audit**, not a line-rate per-packet filter. Any pattern that places L3 "at the network
egress, before render" is contradicted by the measurement — at 9.7 MB/s it would be the bottleneck, not the
guard. This is the §6 hypothesis (`the firewall, not ingestion, is the latency driver`) now **measured**, not
asserted. `validated-offline ≠ real-time`; `measured ≠ guaranteed`.

---

## 3. Pattern A — Anti-cheat / fog-of-war disclosure **audit** (adversarial gaming / training sims)

**The honest framing (corrected).** Not an inline egress render-blocker — a **server-side, windowed audit** that
flags a client session for the authoritative server to act on. The server, never the gateway, takes the action.

**The adaptation (L3).** Map the disclosure question to the firewall's channels:

| Firewall channel | Anti-cheat meaning |
|---|---|
| `x` (diagnostic / source) | a client-*observable* signal (render request, reaction timing, packet a client could read) |
| `y` (future dynamics / target) | the *hidden* entity state the client must not infer (position behind an obstruction) |
| `z0` (legitimate determinant) | the legitimately-shared context that *should* explain any correlation (last-known position, audio cue) |

Stream a window of `(x, y, z0, w0)` samples as `SCHEMA_CMI` (32 B), run `audit_coupling`. The verdict is **not**
"`I(X;Y|Z) > 0`" alone — it is the residual CMI *above the within-Z shuffle null* **and** stable under the
`(Z, W)` mis-specification refinement. Only then → `OBSERVER_CONTAMINATION` (the client is inferring hidden state
beyond the legitimate channel). A residual that dissolves under `W` → `ConfoundedArtifact` (no real leak); an
unidentifiable diagnostic → `Unidentifiable` (the firewall **declines**, never false-positives).

**Required verification suite (the adapter cannot ship without it):**

- a differential test à la `tests/cmi_ingest.rs`: pack planted *airgap / contamination / artifact* windows, prove `ingested ≡ constructed` (same verdict + bit-identical CMI);
- a **calibration** test on known-clean sessions proving the false-positive rate at the chosen `(window, reps)` — because `nonstationarity → over-quarantine` is the named ghost;
- a fail-closed test: truncated / non-finite window ⇒ session flagged, not silently passed.

**`does_not_show`.** Non-leakage **only** relative to the modeled `Z`, the estimator class, and the sample
window. It does not bound unmodeled out-of-band side channels (a hardware screen-parser, an OS timing oracle):
`undetected ≠ absent`; `residual-CMI ≠ channel`; `proves-the-procedure ≠ proves-the-phenomenon`. And `AIR_GAP_HELD`
is absence-of-evidence at this window, never a proof of no coupling.

---

## 4. Pattern B — Stateful control-loop contraction **monitor** (robotics / autonomous middleware)

**The adaptation (L2).** Wire per-step coupling/stiffness telemetry into `SCHEMA_KAPPA` (160 B, n=4) and run
`certify` per control step. At ~600 ns/block this is **inline-capable** at control-loop rates — the one place a
gateway layer legitimately sits in the hot path. On `NotCertified` (the sufficient condition
`2‖κ‖_F·σ < λ ∧ dtλ ≤ 1 ⇒ ρ < 1` fails, i.e. the step left the certified contractive basin), the middleware
drops its execution flag → fail-closed e-stop.

**Two corrections the design discipline forces:**

1. **Certify κ *as ingested* — do not auto-antisymmetrize the live stream.** The gateway never silently applies
   `κ ← (κ−κᵀ)/2` to incoming data; that is a **control mutation of the operator**, a different authority than
   *observing* it (`observation ≠ authority`). Remediation is an **advisory** the gateway can report ("this κ
   would certify after antisymmetrization"); applying it to the actuator's model is a decision the control
   authority owns, logged as its own event — not something the monitor does behind the system's back.
2. **The certificate is local and sufficient, not global.** A PASS means *this* decoupled-linear step contracts
   within the derived noise margin `σ_max = λ / (2‖κ‖_F)` under explicit-Euler — it says nothing about the full
   coupled nonlinear plant, structural failure, or `‖S‖ > σ`.

**Required verification suite:**

- `tests/matrix_ingest.rs`-style `ingested ≡ constructed` (bit-identical frob/ρ/decision through the byte path);
- the **margin** test: a κ at `σ > σ_max` must read `NotCertified` (the gate refuses outside its envelope, proven in `certificate_refuses_outside_its_margin`);
- a fail-closed test: non-finite κ entry ⇒ e-stop flag, not a guessed verdict.

**`does_not_show`.** A sufficient *local* contraction certificate bound to a calculated noise envelope; **not**
global asymptotic stability under arbitrary perturbation or structural failure. `certificate ≠ proof-of-everything`;
`bounded-here ≠ safe-everywhere`.

---

## 5. Pattern C — Compliance-as-code provenance **sidecar** (regulated / high-consequence telemetry)

**The adaptation (L1 + L4).** Run `ursprung-gateway` as an isolated, asynchronous validator over a telemetry
dump (O(1)-memory streaming). L1 lifts each obligation into one of the five `ObligationStatus` states; L4 audits
buyer-facing claims against a **single-source manifest** (`ledger.tsv` + `obligations.tsv`) cross-checked against
a fresh build receipt (`.verify_receipt.tsv`). If a claim is asserted but its backing suite did not `PASS` this
cycle (`unverified_live`), or the prose trips the HYPE lexicon, or a claim references an undischarged obligation —
the sidecar exits `1`.

**Required verification suite:** the existing `DVSM/verify.py` LIVE-gate discipline plus `tests/commercial_gate.rs`
— assert that an over-claim, an undischarged-support claim, a hype term, and a stale receipt each block; and that
`mirror ≠ source` (both languages load the *same* manifest, no drift).

**`does_not_show`.** It verifies the **structural form**, the absence of hype, and the provenance of the log; it
does **not** prove the underlying tests are complete, correct, or omniscient. `receipt ≠ proof`; `static-check ≠
live-execution` is *closed* (the live receipt), but `tested ≠ safe` remains.

---

## 6. The Epistemic Design Filter — the LLM-on-track protocol, grounded in real gates

The filter is not a metaphor; each step maps to an enforcing mechanism that already exists:

1. **Classify the layer.** Every change declares CORE / VIEW / ALLOCATOR / OBSERVER. Enforced *mechanically* at
   registration in `ursprung/registry.py` — a non-CORE system declaring `mutates_core=True` is rejected.
2. **Enforce the invariance gate.** The committed hash trajectory must be byte-identical with the observer active
   and deliberately corrupted (`ursprung/verify.py::view_perturbation_invariance`). A change that moves it crossed
   the membrane and is wrong by definition.
3. **Execute parity verification.** `cargo test` (88) + `python DVSM/verify.py` (12 suites + LIVE gate). New
   schemas/filters must hold **bit-identical `to_bits()` value-parity** *or* exact **decision-parity** against the
   Python reference (the `differential_*` / `*_ingest` pattern). Zero tolerance: a parity break drops the change.
4. **Refuse the fused scalar.** Never optimize a flattened average; a panel of witnesses stays plural
   (`orchestrator.panel` / `no_fused_scalar`). Report the timing profile (§6 parameters) and the explicit blind
   spots; **preserve failed branches** as architectural data.

`ALL GATES GREEN → bank the milestone (no prose drift). ANY GATE BREAKS → drop the change (it exposed a hype
hypothesis).`

---

## 7. The adoption gap (state it in every product)

None of these runs for a stranger out of the box. Each pattern requires the buyer to:

- **supply the domain adapter** — its `(x, y, z0)` mapping (A), its κ/scalar telemetry encoder (B), its `Claim`
  set + proof oracle (C);
- **calibrate the envelope on real data** — the false-positive rate (A), the noise margin `σ_max` (B), the suite
  completeness (C). Until calibrated, the constructed numbers are illustrative.
- **keep the separators** — they travel with the product: `integrity ≠ truth`, `residual-CMI ≠ channel`,
  `certificate ≠ proof-of-everything`, `receipt ≠ proof`, `observation ≠ authority`, `tested ≠ safe`,
  `measured ≠ guaranteed`. A product that drops them is the inflation this repo exists to detect.

**The defensible one-line for any of them:** *a deterministic, fail-closed validator that reports what it checked,
by which estimator/condition, with what coverage boundary — and refuses to act, grade, or claim beyond it.*
