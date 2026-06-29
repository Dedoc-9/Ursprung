<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# GATEWAY_SPEC.md — `ursprung-gateway` design specification (NOT YET BUILT)

A design for collapsing the verification apparatus into a single command-line / sidecar binary that sits
between raw AI infrastructure and a model/compliance registry, and **fails closed** when a check fails. This
is a **specification**, held to the repo's discipline: every component is mapped to what exists today and the
boundary it carries. Nothing here is built as one binary yet, and no performance number is measured.
`described ≠ built`; `spec ≠ product`; `claim ≠ proof`.

**What "guarantee" means here.** A guarantee in this package is a *mechanically-checkable, mathematically-bounded
sufficient condition that always ships beside an explicit `does_not_show`.* It is never a promise of absolute
safety, never a prediction of real-world outcomes, and never "absolute elimination" of anything — that phrasing
is exactly the hype the §4 gate rejects. The gate eliminates unverified claims **within its checked scope**, not
absolutely. `undetected ≠ absent`; `bounded ≠ conservative`; `certificate ≠ proof-of-everything`.

## 0. Status & honest scope (read first)

- **Status: BUILT (frame path), cargo-green.** The single binary `ursprung-gateway` exists and runs the
  L1 ingest+lift → L4 proof-gate path (see *Build status* below; `cargo test` green, binary builds). The
  **full** monolith — collapsing L2 (contraction certifier) and L3 (CMI firewall) into the *same* binary — is
  NOT built: those layers need typed inputs a public frame dump cannot carry (see §3). `parts ≠ whole`.
- **Not a regulatory certification.** The gateway emits a *checkable commitment + scoped claims*. What counts
  as "compliance" is defined by standards bodies and counsel, not by this tool naming it so.
- **Value is SPECULATIVE.** No users, no benchmark, no deployment. This is infrastructure to *operate
  honestly*, not realized value. `built ≠ adopted`.
- **All throughput/latency figures are UNMEASURED** until §6's benchmark plan is run on a real build.
- **Build status.** Ported to Rust and `cargo test`-green in the `ursprung` crate, each differential-tested
  against the Python reference: the CMI firewall + coupling taxonomy (L3), the proof-gated claim gate (L4,
  `commercial_obligations.rs`), and the BinaryFrame **ingestion** (L1 — parser/1A *plus* obligation-lift/1B over
  the ported `invariant_ledger`, in `binframe_adapter.rs`). The parser is a *deterministic fixed-record reader*,
  byte-for-byte matched to the Python — **not** zero-copy (it decodes into typed fields). The L4 ledger now has
  a **single source of truth** (`DVSM/commercial/ledger.tsv` + `obligations.tsv`), loaded by both the Python and
  the Rust gate, so `mirror ≠ source` is closed by construction. The Python gate now also **binds to live test
  execution** (Obligation B): `verify.py` emits a fresh receipt and a supported claim counts discharged only if
  its backing suite PASSED this run — with the honest ceiling `receipt ≠ proof`. **Now also built: the single
  binary `ursprung-gateway`** (`Rust/src/bin/gateway.rs`) **streams** L1 ingest+lift → L4 proof-gate **with the
  Rust-side live receipt read** (bounded memory, `streaming ≡ whole-file`), emitting a fail-closed verdict + a
  disclaimer-first report. **L3 now also runs from a dump:** `--schema cmi` ingests **Schema D** (stratified
  `x,y,z0,w0` CMI samples) and runs the forbidden-coupling firewall end-to-end — OBSERVER_CONTAMINATION fails
  closed, AIR_GAP_HELD passes. **L2 now has a Rust validator too:** `contraction_cert.rs` ports the discrete
  contraction certificate (`2‖κ‖_F·σ<λ ∧ dtλ≤1 ⇒ ρ<1`) + the `κ←(κ−κᵀ)/2` remediation, differential-tested
  against the Python (frob/σ_max/ρ/step value-parity + CONTRACTIVE_CERT/NOT_CERTIFIED decision-parity).
  Honest boundary that REMAINS: the certifier is a **library API, not yet wired to a κ-block (Schema C) ingest
  path**, so the *binary* still can't certify L2 from a dump (`ported ≠ ingested`); and from a *public telemetry
  frame* (TELEM/ABI) the Ω→V / ν→λ air-gaps stay **non-liftable** (a frame carries neither κ nor (X,Y,Z)).
  Confirmed by `cargo test` (green; re-run for the count) + `cargo build --bin ursprung-gateway`. `parts ≠
  whole`; the verdict is a commitment, not a certification of model safety.

## 1. Position

```
[ Raw AI infra: model logs, feature stores, telemetry ] → ursprung-gateway → [ gate-approved artifact / non-zero exit ]
```

The gateway is a **fail-closed validation step**, not an authority over the model. `observation ≠ authority`;
it certifies *that checks ran and their stated bounds held*, never that the model is correct or safe.

## 2. Layers → existing components (with the boundary each carries)

| Layer | Existing component | Grade | The boundary it MUST carry in any output |
|-------|--------------------|-------|------------------------------------------|
| 1. Ingestion | `DVSM/commercial/binframe_adapter.py` (record parse + layout/NaN validation) | VERIFIED | `parsed ≠ correct`; the on-disk layout must be pinned per build (the adapter flags a record-size/endianness mismatch rather than emit garbage) |
| 2a. Skew remediation | `DVSM/kappa_remediation.py` (`κ ← (κ−κᵀ)/2`); **fixed-point port stores the upper triangle and sets `κ_ji := −κ_ij` by construction** | VERIFIED (Python) / SPEC (fixed-point) | corrects the matrix used downstream; says nothing about the *shipped* upstream κ. `max\|κ+κᵀ\|=0` is a **structural** invariant once built by construction — see note below |
| 2b. Contraction certifier | `DVSM/discrete_certificate.py` (`2‖κ‖_F·σ < λ ∧ dtλ≤1 ⇒ ρ<1`) | VERIFIED | **sufficient condition, not a stability proof**; `does_not_show`: ‖S‖>σ, clamps, the coupled system. `certificate ≠ proof-of-everything` |
| 3. CMI firewall | `DVSM/coupling_audit.py` (confounder-conditioned MI + shuffle null + (Z,W) stress) | VERIFIED | `residual-CMI ≠ channel`; `undetected ≠ absent`; **UNIDENTIFIABLE ⇒ quarantine-for-review, NOT silent drop** |
| 4. Proof-gated ledger | `DVSM/commercial/commercial_obligations.py` + `compliance_doc.py` | VERIFIED | a claim ships only if a discharged obligation backs it and it contains no hype; `warranty ≠ proof`; `generated ≠ executed` |
| Hardened math kernels | `Rust/menger_telemetry`, `DVSM/reality_core` | VERIFIED | `bounded-by-clamp ≠ stable-dynamics`; `bounded-by-normalization ≠ globally-stable` |

**Note on the skew invariant (constructed, not asserted).** `max|κ+κᵀ|=0` is exact in real/float arithmetic by
symmetry, but **not** under naive Q32.32: floor-halving `(a−b)/2` rounds, so for an odd difference `d`,
`floor(d/2)+floor(−d/2) = −1 ULP` and the antisymmetric sum is `−1`, not `0`. The port therefore **does not
compute both halves**: it computes the upper triangle `κ_ij := (a−b)/2`, sets `κ_ji := −κ_ij`, and zeroes the
diagonal — making `max|κ+κᵀ|=0` a **structural** invariant of the data layout rather than a numerical claim to
be re-measured each run. `asserted-invariant ≠ constructed-invariant`; the port's test must assert the
construction, not a lucky rounding.

## 2.1 Spec-vs-reality posture (caveats the grading pass surfaced)

Two places where earlier spec prose ran ahead of the code; recorded so the blueprint does not inflate itself.

- **Ingestion is float-native, not fixed-point.** The real DVSM frames are emitted as native `f32`/`f64`
  (`struct '<QffffffffBBBB'` / `'<QdddBBQ'`), so the parser reads floats as emitted. The parse is
  deterministic (fixed record layout, in-order read), but a Q32.32 conversion would be a **downstream
  transform**, not an intrinsic property of ingestion. "Fixed-point ingestion eliminates float drift" overstates
  layer 1 — what layer 1 guarantees is *deterministic, validated parsing*, not fixed-point arithmetic.
  `parsed ≠ fixed-point`. Status: the parser (Sub-Slice 1A — `parse_frames` + `ParseReport`, with the two
  reference anomalies `layout_mismatch` and `nonfinite`) is now in Rust (`Rust/src/binframe_adapter.rs`,
  differential-tested against Python-`struct`-packed fixtures). The obligation-lift half (1B) is now wired too:
  `invariant_ledger` (`ObligationResult` + the five statuses `CLOSED/BOUNDED/VIOLATED/REJECTED_AS_PROOF/
  UNDERDETERMINED` — **no `OPEN`**, faithful to the source) is ported, and `lift()` grades containment +
  replay-parity from a dump while honestly declaring the Ω→V / ν→λ air-gaps non-liftable (differential-tested).
  The invented "ForbiddenSetViolation" was excluded (not in the reference).
- **Live execution binding (Obligation B, Python-side).** Layer 4's static audit verifies that each warranted
  claim *names* a discharged obligation, with no overclaim/hype and boundary fields present. The **Python** gate
  now additionally binds this to execution: `verify.py` runs every suite, emits a fresh, run-id-stamped receipt
  (`.verify_receipt.tsv`: `suite ⇥ PASS|FAIL ⇥ run-id`), and `audit_commercial_ledger(..., live_receipts=)` marks
  a supported claim `unverified_live` unless its backing suite (the `suite` column in `obligations.tsv`) reads
  `PASS`; a missing / stale / failed suite ⇒ non-zero exit. **Honest ceiling, recorded not papered over:** this
  lifts the gate from "a test is *named*" to "a test *ran and passed in this build*" — **not** "the test is
  correct" (`tested ≠ safe`); the receipt is a trusted, freshness-bounded but forgeable build artifact, so the
  regress terminates at the build environment's trust root (`receipt ≠ proof`). The **Rust** gate now ALSO
  carries the receipt-reading path (`CommercialLedger::audit_live`, exercised by the `ursprung-gateway`
  binary), so live binding is available standalone in Rust; the compliance-doc renderer is not ported (need not
  be in the fail-closed binary).

## 3. The single-binary reality (the actual work)

**Status: largely discharged.** L1 (ingest+lift), L3 (CMI firewall + coupling taxonomy) and L4 (proof-gated
ledger) are now ported to Rust and `cargo`-green; the math kernels (Q32.32, in-tree SHA-256, Menger mask) were
already Rust (`menger_telemetry`). The `ursprung-gateway` binary composes the **L1→L4 frame path** in one
dependency-free executable — so the fork below resolved to **(A) port the Python to Rust**, done incrementally
and differential-tested (CMI value+decision parity; lift verdicts; commercial-gate verdicts).

What a *full* single-binary monolith still lacks splits cleanly now. **L3 got its typed-input channel:**
**Schema D** (`--schema cmi`, `x,y,z0,w0` samples) feeds the already-ported CMI firewall + coupling taxonomy
end-to-end. **L2 got its validator:** `contraction_cert.rs` ports the discrete contraction certificate + κ
remediation (differential-tested vs Python). What L2 still lacks is the **κ-block (Schema C) ingest path** that
would feed the certifier from a dump — the certifier is a library API today (`ported ≠ ingested`); a fixed
compile-time `n` κ-block reader (mirroring Schema D) is the remaining wiring. From a *public telemetry frame*
the Ω→V / ν→λ air-gaps stay **non-liftable** (the frame carries neither κ nor `(X,Y,Z)`). `monolith ≠ free`;
`parts ≠ whole`. (Rejected at the fork: **(B) embed CPython** — not dependency-free, ships a Python runtime.)

## 4. Output contract (what a "gate-approved artifact" actually asserts)

Every emitted artifact is the `compliance_doc` output: §1 warranted scope (each claim + discharged obligation
+ `does_not_show` + falsifier), §2 explicit non-warranties, §3–5 disclaimer-first warranty/liability/indemnity
*templates* with `[PLACEHOLDER]` figures. The gateway refuses to emit unless `audit_commercial_ledger` passes.
It is a **commitment, not a signature** (no PKI); add real key management before using the word "signed".

## 5. CLI / deployment posture

As built (`Rust/src/bin/gateway.rs`):

```
ursprung-gateway --telemetry ai-telemetry.bin [--schema telem|abi] [--receipt .verify_receipt.tsv]
                 [--u-max 100.0] [--header-lines 1] [--output gate_report.md] [--strict]
```

- Exit `0`: parse clean (no layout-mismatch / non-finite), no VIOLATED obligation, and the proof-gated ledger
  honest (live-bound when `--receipt` is given) → the disclaimer-first gate report is written. Exit non-zero:
  any of those fails → **blocks the CI/CD step**, fail-closed.
- `--strict` makes a missing/stale receipt itself a failure (forces live binding). Without `--receipt`, only
  the static ledger audit runs and the report says so.
- It does **not** run the CMI firewall, so there is no `UNIDENTIFIABLE`-window quarantine here; the firewall's
  air-gap obligations are instead reported **non-liftable** from a public frame dump (`undetected ≠ absent`).
  `parts ≠ whole`; the verdict is a commitment, not a certification of model safety.

## 6. Ingestion & performance design (HYPOTHESES — all figures UNMEASURED)

This is the mmap/latency mapping, framed as *what to design for and what to measure* — not claimed numbers.

- **Memory-mapped fixed-record framing.** Frames are fixed-size `repr(C)` records (`binframe_adapter`
  already validates `len(body) % rec_size == 0`). `mmap` the file; iterate records in place (no copy). A
  trailing partial record at a page boundary is buffered across windows. Resident memory is `O(1)` in file
  size (the OS pages on demand) — *expected*, to be confirmed.
- **The latency driver is the firewall, not ingestion.** Parse + fixed-point is `O(bytes)` and cheap; the CMI
  audit is `reps × strata × window` (hundreds of shuffle-nulls). So "real-time" is achievable only as a
  **two-tier gate**: (i) a **line-rate fast path** — per-record bounded/finite/commitment checks (already
  `O(1)`); (ii) a **windowed slow path** — the CMI firewall on a sliding window at a lower cadence (mirroring
  the runtime's logical-clock cadence). Treat the CMI as a periodic audit, not a per-packet filter.
  `validated-offline ≠ real-time`.
- **Determinism — scoped, not flat.** The ingest + fixed-point matrix path is bit-replayable across hardware
  (Q32.32 + in-order mmap read ⇒ same digest). But the **CMI estimator is still float (Python)**; until it is
  ported to fixed-point its cross-architecture bit-identity is **OPEN**, not guaranteed. So today: determinism
  is `BOUNDED` (fixed-point path) / `OPEN` (CMI firewall). The flat claim "identical reports on any hardware"
  is only true once §8.1 lands. `determinism ≠ validity`, and here it is not yet fully achieved.
- **Backpressure.** Bounded ring buffer with explicit `dropped`/`quarantined` counters (the `reality_core`
  runtime pattern), surfaced in the output so loss is accounted, not hidden.
- **Benchmark plan (the obligations to discharge before any "low-latency" claim):**
  1. per-record parse latency (ns) vs record size;
  2. CMI-window latency vs `(window, reps, strata)` — the real cost curve;
  3. max sustained frame-rate at which the slow path keeps up without unbounded quarantine;
  4. resident memory vs file size (confirm `O(1)`).
  Until these are measured, the gateway makes **no** throughput claim. `measured ≠ guaranteed`.

## 7. Failure modes / ghosts to watch

- CMI false-positives under nonstationarity → over-quarantine (tune window/cadence; report rate).
- Schema/layout drift between producer and gateway → the parser must reject, not coerce (`parsed ≠ correct`).
- Python↔Rust decision divergence during the port → guard with a differential test on planted cases.
- Scope creep: a gateway that grows verdicts it can't back. Every new output needs a discharged obligation.

## 8. Build sequence (honest order)

1. Port the CMI core to Rust + differential-test against the Python (the gating risk).
2. Port the claim-ledger gate + compliance generator to Rust.
3. Wire the two-tier ingestion (fast path + windowed firewall) over the existing `menger_telemetry` parse.
4. Single-binary CLI + fail-closed exit codes.
5. Run §6's benchmark plan; only then attach any latency claim — graded, with `does_not_show`.

`spec ≠ product`; `written ≠ true` — verify each step against its gate as it lands.
