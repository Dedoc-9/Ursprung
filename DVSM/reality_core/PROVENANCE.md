<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# PROVENANCE — dvsm_reality_core

## Source

Derived from the external repository `github.com/Dedoc-9/dvsm-meta-kernel`, folder `2-Layer_Reality_Core`,
file **`Two_Layer_Reality_Core.rs`** (reviewed at `main`, ~20.7 KB). Sibling files in that folder
(`Engine_Core_1440.rs`, `DVSM_Gated_Steifel_Runtime.rs`, `Drop_In_3D_Core.rs`, `Gated_Steifel_Refined.rs`,
`Convex3D_AntiCheat.rs`, `3D_Games.rs`) are domain applications and were **not** reviewed in depth — `scope`
is the core file. `reviewed-one-file ≠ reviewed-the-folder`.

**The folder's `README.rs` was treated as NON-AUTHORITATIVE** (per explicit instruction). This product was
derived from the *source code*, not from prose claims. `claim ≠ code`.

## Findings on the source (from the code)

1. **Non-compiling concatenation.** `Two_Layer_Reality_Core.rs` contains three back-to-back copies of the
   engine: `Config` is defined 3×, `DVSMCore` 2×, plus a `ManifoldCore`, and free fns `project`/`residual`/
   `normalize` are redefined. As a single Rust module it would not compile (duplicate definitions). `file ≠ crate`.
2. **Three inconsistent dynamics in one file.** The copies disagree on the math:
   - State damping: copy 1 uses `(1-λ)·blend + λ·S` (raw, un-normalized `S`); copies 2–3 use `λ·Ŝ` (normalized).
   - Basis flow: `ManifoldCore` drives the frame with the **true residual** `R = z - Π_W(z)` (per-column
     `r_j = R - wⱼ(wⱼ·R)`); copies 1 and 3 drive it with a **residual-of-`z`** per column (`z - wⱼ(wⱼ·z)`),
     and differ again on normalize-then-add vs blend-then-retract.
   So the "immutable mathematics" is specified three ways. `comment-invariant ≠ code-invariant`.
3. **Wall-clock in the runtime.** Layer 2 keyed its cadence on `Instant::now()`, making execution
   non-deterministic and untestable.

## Decisions (canonical choices — rejected paths preserved)

- **State damping → `λ·Ŝ` (normalized).** Chosen because it keeps the damping term on the sphere, so the
  `‖S‖=1` invariant is robust even if `S` drifts. *Rejected:* `λ·S` (raw) from copy 1 — equivalent only while
  `S` is already unit, fragile otherwise.
- **Basis flow → true residual `R` driving `W ← orthonormalize(W + η·cⱼ·R̂)`.** Chosen to match the file's own
  header spec (`W ← QR(W + η·ΔR)`) and because `R ⊥ span(W)` by construction, so it rotates the frame toward
  genuinely unexplained signal. *Rejected:* the residual-of-`z` per-column variants (they re-derive a residual
  the projection already gives, and the three copies disagree on the blend).
- **Retraction → explicit modified Gram-Schmidt (std-only), shape pinned to `n×r`.** *Rejected:* `nalgebra`'s
  `qr().q()`, whose returned shape is implementation-dependent and a latent dimension bug.
- **Time → logical clock injected by the caller.** *Rejected:* `Instant::now()` — replaced for determinism
  and testability. `replay-determinism > wall-clock convenience`.
- **Dependencies → none (std-only).** *Rejected:* `nalgebra` — removed to cut the supply-chain surface, pin
  determinism (no BLAS dispatch), and keep the crate `no_std`-friendly.

## Honesty / status

- Grades are about THIS reformulation, not the upstream kernel. The invariants (`‖S‖=1`, `WᵀW=I`, `R⊥W`,
  `B∈[0,2]`) are **measured every step** and surfaced in `Observation`; they are not asserted by comment.
- The crate ships **compile-unverified** (no Rust toolchain in the build environment). Logic is hand-reviewed
  against the source; the user confirms with `cargo test`. `written ≠ compiled`; `tested ≠ safe`.
- This is a bounded dynamical codec/observer. It makes no physical or "reality" claim. `integrity ≠ truth`.
