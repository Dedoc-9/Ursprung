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

- **Status: SPEC.** Components are VERIFIED *individually* (see `method.md`); the **monolith is UNBUILT**. The
  single dependency-free binary requires a Python→Rust port (§3) that does not exist yet.
- **Not a regulatory certification.** The gateway emits a *checkable commitment + scoped claims*. What counts
  as "compliance" is defined by standards bodies and counsel, not by this tool naming it so.
- **Value is SPECULATIVE.** No users, no benchmark, no deployment. This is infrastructure to *operate
  honestly*, not realized value. `built ≠ adopted`.
- **All throughput/latency figures are UNMEASURED** until §6's benchmark plan is run on a real build.

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

## 3. The single-binary reality (the actual work)

Today layers 1, 3, 4 are **Python**; the math kernels are **Rust**. A single dependency-free binary requires
one of:

- **(A) Port the Python to Rust (recommended for "dependency-free").** Reimplement: the CMI core (entropy /
  conditional-MI / seeded within-stratum shuffle null / the (Z,W) mis-spec stress), the claim-ledger +
  no-overclaim gate, and the compliance-doc generator. The in-tree SHA-256, Q32.32 fixed-point, and the
  Menger mask are **already Rust** (`menger_telemetry`) and reusable. Risk: the CMI estimator must reproduce
  the Python decisions (validate by differential test Python↔Rust on the planted null/channel cases).
- **(B) Embed CPython.** Faster to assemble, but **not dependency-free** and ships a Python runtime — fails
  the stated posture. Reject unless the dependency-free requirement is dropped.

Honest cost: (A) is a multi-session port, not a packaging step. `monolith ≠ free`. Until it exists, the
"gateway" is an orchestration of the Python gate (`DVSM/verify.py`) over Rust artifacts — a real product, but
two-language, not one binary.

## 4. Output contract (what a "gate-approved artifact" actually asserts)

Every emitted artifact is the `compliance_doc` output: §1 warranted scope (each claim + discharged obligation
+ `does_not_show` + falsifier), §2 explicit non-warranties, §3–5 disclaimer-first warranty/liability/indemnity
*templates* with `[PLACEHOLDER]` figures. The gateway refuses to emit unless `audit_commercial_ledger` passes.
It is a **commitment, not a signature** (no PKI); add real key management before using the word "signed".

## 5. CLI / deployment posture

```
ursprung-gateway --stream /var/log/ai-telemetry.bin --schema dvsm_v20 --gate-strict --output ./COMPLIANCE.md
```

- Exit `0`: all checks passed; artifact written. Exit non-zero: a check failed, a leak was confirmed, or hype
  was found → **blocks the CI/CD step**. Fail-closed by default; `--gate-strict` makes warnings fatal too.
- Quarantine (not drop) for `UNIDENTIFIABLE` windows: emit them to a side channel with the reason, so a
  false-positive doesn't silently discard data. `undetected ≠ absent`.

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
