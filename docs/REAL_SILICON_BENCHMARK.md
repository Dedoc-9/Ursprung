<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Real-Silicon Benchmark Plan (NOT built — a plan, not a result)

This document fixes the discipline of the real-silicon benchmark **before** any implementation, so that
"we have interesting silicon" can never quietly become "we have a validated result." It is the gate that
would move the Causal Continuity Hypothesis from `supported_constructed` toward a **law** — and nothing in
here is run yet.

## The reframing (the load-bearing distinction)

```
Z2 Extreme (or any device)  =  measurement substrate
PFAL / TCFF GPU harness     =  the missing artifact
numbers                     =  exist only after the harness exists
```

The strongest honest statement is **not** "the Z2 Extreme proves the runtime." It is: *the device is a
substrate where the runtime's untested fidelity assumptions become observable.* This stays deliberately
separate from the kernel result. The kernel proved the **contract** survives a substrate transition
(`reality_kernel/core_rs`, verified). This benchmark would test whether the **fidelity claims** survive
contact with a substrate. Two different questions; keep them apart. (For a distributed product release this
separation is the asset: a contract that travels, and fidelity numbers that are honestly device-scoped.)

## 1 — The device is a constrained ORACLE, not a target to optimize around

A handheld is valuable precisely because it creates pressure the constructed benches could not:

- **unified CPU/GPU memory (LPDDR5X)** makes copies, residency, and bandwidth *visible* — the
  cache/bandwidth frontier the lineage bench's Python dict hid;
- **thermal limits** expose whether timing assumptions survive clock drift;
- **battery / TDP modes** make the *same algorithm* produce *different observed timings*.

Therefore every run records its world as provenance — `timing is an event, not an identity`:

```
run:
  device:            Z2 Extreme (Radeon 890M, RDNA 3.5, 16 CU)
  power_profile:     <TDP / mode>
  driver:            <version>
  backend:           <Vulkan | DX12 | wgpu>
  resolution:        <WxH>
  temperature_state: <cold | sustained / throttled>
  algorithm_commit:  <git sha>
```

Without this, a later comparison is "same code, different invisible world." This is the kernel's
`identity includes provenance` applied to a measurement: a number without its run-provenance is an
`UNACCOUNTED` result.

## 2 — "Equal GPU time" needs a strict definition (the GPU clock is the shared ruler)

"Equal GPU time" can silently mean equal wall time, equal GPU-timestamp interval, equal frame deadline, or
equal energy — and a technique can "win" by simply spending more under a loose definition. The honest form:

```
fixed GPU timestamp budget (N GPU ticks, via timestamp queries)
        ↓
PFAL gets N ticks  ·  TCFF gets N ticks  ·  each control gets N ticks
        ↓
compare the temporal-error PROFILE (below) at that fixed budget
```

The GPU timestamp is the shared ruler; wall time and energy are *recorded as provenance* (§1) but are not
the budget. Energy-equal and deadline-equal are separate, later questions — named, not conflated.

## 3 — The provenance kernel sits ABOVE the renderer, never in the timing path

The same lesson as live/latent compression: do not make the renderer walk the artifact graph to justify
itself every frame — that turns provenance into a per-frame cost center and violates `compress ≠ sever`.

```
hot path (per frame):   frame state · transform · provenance_digest · GPU command buffer
cold path (on demand):  digest → artifact graph → full edit / assumption / failure lineage
```

The frame carries the digest (O(1)); the lineage resolves off the frame budget. The benchmark must measure
the renderer's frame cost with the digest carried but the graph **not** walked — otherwise it measures the
wrong thing and slanders the contract the kernel already verified.

## 4 — Causal Continuity enters as a MEASUREMENT, not a claim

The water-filling re-specification (`promotion_gate.py`, `supported_constructed`) is exactly where this
harness earns its place. The question is **not** "does Causal Continuity work?" — it is:

```
Given a fixed GPU-time budget: does the proposed allocation reduce MEASURED temporal error,
                               and does dropping present-perception S still help on real pixels?
```

The weighting scheme (`√(U·C·P · resistance)`) remains a **model choice whose performance is measured**, not
a law promoted by a model world. A pass here (real pixels, real motion, equal GPU time, across power states)
is what `supported_constructed → law` requires; a loss demotes it back to a hypothesis and is kept as
architectural information. `declared ≠ verified`.

## 5 — The missing piece is THREE harnesses, not one (they fail differently)

```
bench_gpu/
  ├── fidelity_compare    PFAL vs TCFF vs controls at equal GPU-timestamp budget
  ├── latency_capture     input → photon (real input, real 120 Hz panel)
  └── thermal_stability   sustained frame behaviour under throttling
```

A technique can reconstruct well **but** add latency; hit latency **but** degrade under heat; look stable
**but** spend impossible energy. Collapsing these into one score would recreate exactly the
multiplicative-convenience the fidelity-laws audit just removed (`model ≠ verified structure`).

**The temporal-error PROFILE is a vector, never a sum.** Report it as separate axes —

```
temporal_error_profile = {
  reconstruction_error,
  motion_instability,
  boundary_discontinuity,
  perceptual_artifact_score,
}
```

— and an allocation "wins" only if it is **Pareto-better** or wins per-axis, never by a summed scalar. This
is the same discipline as `integrity ⟂ adequacy` (two ledgers, not one confidence) and the resistance
tensor's peak-preserving composite: do not let four distinct failure modes average into a misleading single
number. (This reconciles §4's convenience of writing `error = a+b+c+d` with §5's rule: the four terms are a
profile, not a total.)

## Honest bounds (what a green benchmark would and would not establish)

- **One silicon point.** Results are scoped to RDNA 3.5 on this APU — `benchmark gain ≠ universal
  improvement`. A real measurement beats a constructed one; it is still device-relative.
- **The 120 Hz panel caps presentation at 8.33 ms**, so a 4.13 ms (242 fps) figure is a *compute*-budget
  claim, not a display one; presentation cadence is panel-limited.
- **The Windows timer-granularity question is live** (the live/latent probe): hitting a sub-granularity
  deadline by spinning a full core burns battery and thermal headroom on a handheld — pin a power profile and
  report p50/p99 distributions, not single numbers.
- **This is a plan.** `raster.py` emits a hashable reference framebuffer, not GPU pixels; a real
  Vulkan/DX12/wgpu backend and GPU-timestamp + present-to-photon instrumentation are the build. The device
  can host it; it is not the missing piece.

> The kernel proved the contract survives a substrate transition. This benchmark tests whether the fidelity
> claims survive contact with a substrate. The two stay separate — and that separation is what lets the
> runtime be released as a distributed product: a contract that travels, fidelity numbers that are honestly
> device-scoped.
