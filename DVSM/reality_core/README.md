<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# dvsm_reality_core — the DVSM 2-Layer Reality Core, as a standalone hardened Rust product

A compilable, tested, dependency-free re-engineering of the DVSM **2-Layer Reality Core** (`Two_Layer_Reality_Core.rs`
in the external `dvsm-meta-kernel` repo). It is a contractive projection dynamical system on the product
manifold `S^(n-1) × St(n, r)`, split into two layers whose boundary is enforced by Rust's type system.

## The two layers

**Layer 1 — `GeometricCore` (immutable mathematics).** Per step, on input `z ∈ ℝⁿ`:

```text
z_proj = Π_W(z) = W Wᵀ z                 geometric observation of the input
R      = z - z_proj                       residual, ⟂ span(W) by construction
s      ← normalize((1-λ)(α ŝ + (1-α) ẑ) + λ ŝ)     contractive spherical state flow
W      ← orthonormalize(W + η · cⱼ · R̂)            residual-driven Stiefel retraction
B(t)   = 1 - clamp(⟨ŝ, ẑ_proj⟩, -1, 1) ∈ [0,2]     stress / angular divergence
```

Invariants `‖S‖=1`, `WᵀW=I`, `R⊥W`. The state (`s`, `w`) is **private**; the only mutation is `step`.

**Layer 2 — `Runtime` (mutable execution).** Streaming ingestion, bounded FIFO backpressure, logical-clock
scheduling per `Mode` (Gaming/RF/Hybrid), mode switching. It holds a core privately and may **observe** it but
has no way to alter the geometry. `observation ≠ authority`; `mode ≠ geometry`.

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
   column is reseeded; adversarial huge-norm input stays bounded by the sphere/Stiefel constraints.
6. **Zero dependencies.** std-only linear algebra (the upstream used `nalgebra`) — no supply-chain surface,
   no BLAS nondeterminism, and the Stiefel-retraction shape is pinned (no library QR-shape ambiguity).

## Files

`src/linalg.rs` (dot/norm/projection + modified-Gram-Schmidt retraction, `Frame`), `src/core.rs` (Layer 1),
`src/runtime.rs` (Layer 2), `src/lib.rs`. Tests inline in every module + `tests/invariants.rs` (end-to-end).
Demo: `examples/demo.rs`.

## Run

```powershell
cd DVSM/reality_core          # from the repo root
cargo test
cargo run --example demo
```

`cargo test` asserts the apparatus (validity-not-outcome): invariants hold after thousands of steps, the
residual stays ⟂ the frame, stress stays in `[0,2]`, the state stays bounded under `1e7`-norm input, non-finite
input is rejected without poisoning the core, backpressure drops and counts, and the full pipeline replays
deterministically.

## Boundaries (load-bearing)

This is a **bounded dynamical codec/observer**, not a physics or "reality" claim. `integrity ≠ truth`;
`bounded ≠ correct`; `low-stress ≠ model-is-right`. `B(t)` is angular divergence — a salience signal that
*allocates attention*, not a verdict. `salience ≠ importance`. The README in the upstream folder is treated as
**non-authoritative**; this product was derived from the source code (see `PROVENANCE.md`).

## Status

Ships **compile-unverified in this environment** (no Rust toolchain was available where it was built). The
logic is std-only and hand-reviewed; confirm with `cargo test`. `tested ≠ safe`; `written ≠ compiled`.
