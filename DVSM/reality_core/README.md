<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# dvsm_reality_core — the DVSM 2-Layer Reality Core, as a standalone hardened Rust product

A compilable, tested, dependency-free re-engineering of the DVSM **2-Layer Reality Core**
(`Two_Layer_Reality_Core.rs` in the external `dvsm-meta-kernel` repo). It is a contractive projection
dynamical system on the product manifold `S^(n-1) × St(n, r)`, split into two layers whose boundary is
enforced by Rust's type system — and it ships with a **verification backend** that *measures* that boundary
and a **C-ABI** that makes it embeddable.

## The two layers

**Layer 1 — `GeometricCore` (immutable mathematics).** Per step, on input `z ∈ ℝⁿ`:

```text
z_proj = Π_W(z) = W Wᵀ z                 geometric observation of the input
R      = z - z_proj                       residual, ⟂ span(W) by construction
s      ← normalize((1-λ)(α ŝ + (1-α) ẑ) + λ ŝ)     contractive spherical state flow
W      ← orthonormalize(W + η · cⱼ · R̂)            residual-driven Stiefel retraction
B(t)   = 1 - clamp(⟨ŝ, ẑ_proj⟩, -1, 1) ∈ [0,2]     stress / angular divergence
```

Invariants `‖S‖=1`, `WᵀW=I`, `R⊥W`. The state (`s`, `w`) is **private**; the only mutation is `step`, and
even the seeded constructor (`GeometricCore::seeded`) routes the initial condition *through* the manifold
projections. There is no raw state setter.

**Layer 2 — `Runtime` (mutable execution).** Streaming ingestion, bounded FIFO backpressure, logical-clock
scheduling per `Mode` (Gaming/RF/Hybrid), mode switching. It holds a core privately and may **observe** it but
has no way to alter the geometry. `observation ≠ authority`; `mode ≠ geometry`.

## Two backends

**Verification backend** (closes the loop — the air-gap is *measured*, not just claimed).
`src/trace.rs` + `examples/dump_trace.rs` emit a telemetry CSV; the Python auditor
`../reality_core_probe.py` (reusing the DVSM `coupling_audit` / `invariant_ledger`) checks three things on the
real emitted trace:

- **invariants** — every frame: `stress ∈ [0,2]`, `‖s‖-1 ≈ 0`, `‖WᵀW-I‖ ≈ 0`, `‖Wᵀ R‖ ≈ 0` (graded);
- **air-gap** — does the diagnostic `stress(t)` leak into the next input `x0(t+1)` beyond the legitimate
  driver `x0(t)`? Confounder-conditioned CMI + shuffle null. A clean core ⇒ `AIR_GAP_HELD`; a `--leak` run
  (where a diagnostic steers the input) ⇒ `OBSERVER_CONTAMINATION`. This is the soft `observation ≠ authority`
  test the Rust type system can't see (it forbids *writes*, not *informational* feedback);
- **replay** — two traces from the same seed/schedule are bit-identical.

**FFI / embeddable backend.** `src/ffi.rs` is a C ABI — `rc_new` / `rc_step` / `rc_observe_state` / `rc_frame`
/ `rc_free` with a `repr(C) ObservationC`, all null/length-guarded (a bad call returns a negative code, never
unwinds across the boundary). Built as `cdylib`/`staticlib` (see `Cargo.toml`). The air-gap holds across the
ABI too: there is no exported setter for `s`/`w`.

## What this product adds over the upstream research file (hardening)

1. **It compiles.** The upstream `.rs` is three divergent variants concatenated into one file (duplicate
   `Config`/`DVSMCore`/`project`). `file ≠ crate`.
2. **One canonical update rule.** The upstream specified the dynamics three inconsistent ways (`λ·S` vs `λ·Ŝ`
   damping; true-residual vs residual-of-`z` basis flow). This fixes one and records the rejected variants in
   `PROVENANCE.md`. `comment-invariant ≠ code-invariant`.
3. **Invariants measured, not asserted.** Every `Observation` carries `sphere_residual`, `stiefel_residual`,
   `residual_ortho`, and a `Health` (Nominal / Degenerate / NonFinite). `invariant ≠ comment`.
4. **Deterministic & replayable.** No wall-clock. The runtime advances on a logical clock, so a given
   (stream, schedule) replays bit-for-bit. The upstream used `Instant::now()` (non-deterministic, untestable).
5. **Numeric hardening.** `eps` floors; non-finite input is rejected with state preserved; a collapsed basis
   column is reseeded; adversarial huge-norm input stays bounded by the sphere/Stiefel constraints; `Config`
   parameters are clamped to their valid ranges by `Config::validated`.
6. **Zero dependencies.** std-only linear algebra (the upstream used `nalgebra`) — no supply-chain surface,
   no BLAS nondeterminism, and the Stiefel-retraction shape is pinned (no library QR-shape ambiguity).

## Files

| Path | Role |
|------|------|
| `src/linalg.rs` | dependency-free dot/norm/projection + modified-Gram-Schmidt retraction, `Frame` |
| `src/core.rs` | Layer 1 `GeometricCore`; `Config`/`Observation`/`Health`; `seeded`, `step_many`, validation |
| `src/runtime.rs` | Layer 2 `Runtime` (logical-clock scheduling, FIFO backpressure, modes) |
| `src/trace.rs` | telemetry tracing + CSV writer (+ `--leak` fixture) for the verification backend |
| `src/ffi.rs` | C ABI (`rc_*`), `ObservationC` |
| `src/lib.rs` | crate root + re-exports |
| `examples/demo.rs` | runnable demo of the 2-layer pipeline |
| `examples/dump_trace.rs` | emit a telemetry CSV (`-- out.csv [--leak]`) |
| `tests/invariants.rs` | end-to-end invariant / boundedness / determinism |
| `tests/hardening.rs` | config validation, seeded-init invariants, `step_many`, health |
| `../reality_core_probe.py` | Python verification backend (audits the emitted trace) |

## Run / verify

```powershell
cd DVSM/reality_core          # from the repo root
cargo test                    # 24 Rust tests (core/linalg/runtime/trace/ffi + invariants + hardening)
cargo run --example demo

# verification backend: emit traces, then audit them
cargo run --example dump_trace -- clean.csv
cargo run --example dump_trace -- clean2.csv
cargo run --example dump_trace -- leak.csv --leak
cd ..
$env:PYTHONHASHSEED=0
python reality_core_probe.py reality_core/clean.csv reality_core/clean2.csv   # AIR_GAP_HELD + replay CLOSED
python reality_core_probe.py reality_core/leak.csv                            # OBSERVER_CONTAMINATION
python verify.py                                                              # full DVSM gate incl. this probe
```

`cargo test` asserts the apparatus (validity-not-outcome): invariants hold after thousands of steps, the
residual stays ⟂ the frame, stress stays in `[0,2]`, the state stays bounded under `1e7`-norm input, non-finite
input is rejected without poisoning the core, backpressure drops and counts, the C-ABI round-trips and rejects
bad handles, and the full pipeline replays deterministically.

## Use cases

Each carries the boundary it does **not** cross — the honest part of the pitch.

- **Online subspace / spectral tracking.** A bounded, low-rank adaptive representation of a high-dimensional
  stream (RF/SIGINT, sensor fusion, audio). The Stiefel frame `W` tracks the dominant subspace; `B(t)` flags
  when the input diverges from the tracked geometry. *Does not* do PCA/Kalman optimality — it is a contractive
  geometric tracker, not a minimum-variance estimator. `tracking ≠ optimal-estimation`.
- **Novelty / change-of-regime salience.** `B(t)` is an attention signal for non-stationary telemetry
  (health monitoring, drift detection). *Does not* classify the cause — `salience ≠ importance`; it allocates
  a look, it doesn't render a verdict.
- **Embeddable deterministic state core (via the C-ABI).** Drop into a host engine (game/sim/DSP) as a
  reproducible online tracker with a verified observe-only boundary. *Does not* expose geometry mutation — the
  host can drive and observe, never poke `s`/`w`. `embedded ≠ trusted-with-state`.
- **"Read-only diagnostic must stay read-only" boundaries.** Control loops, recsys/quant feature kernels, any
  pipeline where telemetry must not leak into the authoritative path. The verification backend *measures* that
  the diagnostic doesn't steer the dynamics. *Does not* prove the absence of every coupling — `undetected ≠
  absent`; it detects identifiable informational feedback.
- **Reproducibility / replay-audited pipelines.** The logical-clock runtime gives bit-exact replay; the probe
  checks parity. *Does not* assert correctness — `determinism ≠ validity`; `integrity ≠ truth`.

## For LLMs / contributors — how to extend this without breaking it

This crate is built under the Ursprung/Dentatus discipline. If you (or an LLM) modify it, preserve these
invariants; a change is not done until the gate below is green.

1. **Read the code, not the prose.** Treat any upstream README (and this one) as a claim; the source is the
   authority. `claim ≠ code`. If you change the dynamics, record the rejected alternatives in `PROVENANCE.md`.
2. **Keep the air-gap a type, not a comment.** Do **not** add a public setter for `s`/`w`, and do **not** let
   `Runtime` (or any observer) write geometry. The only mutation is `GeometricCore::step`. `observation ≠
   authority`; `mode ≠ geometry`.
3. **Measure invariants; never assert them in a comment.** Anything new that touches the geometry must surface
   its residual in `Observation` (or a probe), the way `sphere_residual`/`stiefel_residual`/`residual_ortho`
   already do. `invariant ≠ comment`.
4. **Stay deterministic.** No wall-clock, no thread-nondeterminism, no RNG without an explicit seed in the
   *core*. Timing belongs to Layer 2 on the logical clock. A change that breaks `full_pipeline_is_deterministic`
   is a regression. `determinism ≠ validity`, but losing it loses replay/audit.
5. **Stay std-only and numerically guarded.** No new dependencies; keep `eps` floors and the non-finite-input
   rejection. New linear algebra goes in `src/linalg.rs` with its own unit test.
6. **Verify the whole loop, not just the unit you touched.** Run, in order:
   `cargo test` → `cargo run --example dump_trace -- clean.csv` (+ a second, + `--leak`) →
   `python reality_core_probe.py …` → `python verify.py`. The DVSM gate (`python verify.py`) must read
   `GATE PASSED`. `tested ≠ safe`, but a red gate is decisive.
7. **Don't overclaim.** This is a bounded dynamical codec/observer. `B(t)` is angular divergence, not truth;
   boundedness is empirical on the run, not a certified guarantee. State what a change does **not** establish.

## Boundaries (load-bearing)

A **bounded dynamical codec/observer**, not a physics or "reality" claim. `integrity ≠ truth`;
`bounded ≠ correct`; `low-stress ≠ model-is-right`. `B(t)` is a salience signal that *allocates attention*, not
a verdict. `salience ≠ importance`. The upstream folder's README is treated as **non-authoritative**; this
product was derived from the source code (see `PROVENANCE.md`).

## Status

**Verified green** (commit `219959b`): `cargo test` passes (24 tests across core/linalg/runtime/trace/ffi +
`invariants` + `hardening`); the demo and `dump_trace` run; the verification backend separates a clean trace
(`AIR_GAP_HELD`, CMI ≈ 0.002) from a planted leak (`OBSERVER_CONTAMINATION`, CMI ≈ 0.26) and confirms replay
parity; and the full DVSM gate (`python verify.py`) is `8/8`. On the real emitted telemetry the leak shows at a
smaller effect size than the synthetic fixture — the firewall still caught it. `tested ≠ safe`;
`measured ≠ guaranteed`; `integrity ≠ truth`.
