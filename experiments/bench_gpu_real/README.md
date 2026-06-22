<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# bench_gpu_real — Milestone 1: the GPU-interval ruler exists on real silicon ✓

The smallest non-faked claim in the project, and the first one that did **not** expire on silicon —
because it was measured on silicon. Times an empty GPU compute pass with timestamp queries and prints
`(end − begin) × timestamp_period` nanoseconds, with provenance. No window, no pixels, no fidelity.

```bash
cargo run            # cargo run --release for realistic CPU-side timing in later milestones
```

## First recorded observation (a benchmark run is an artifact)

```
device:              ASUS ROG Xbox Ally X
backend:             Vulkan
adapter:             AMD Radeon(TM) 890M Graphics  (RDNA 3.5)
driver:              AMD proprietary driver 25.30.27.05 (LLPC)
timestamp_period_ns: 10.0          # GPU timestamp granularity = 10 ns/tick
empty-pass interval: 40.0 ns       # 4 ticks; bracket overhead, NOT work and NOT a fidelity number
ruler invariant:     end > begin   # monotonic — the ruler ticks
```

## What this proves — and what it does not

```
proves:        the GPU-interval ruler EXISTS on this device, is monotonic, and reports its period;
               TIMESTAMP_QUERY is real here (required, not silently dropped); provenance travels with it.
does NOT prove: any fidelity claim, any frame budget, any PFAL/TCFF result. 40 ns is the empty-pass
               bracket cost, not work. One device, one driver, one run — `benchmark gain ≠ universal`.
```

The 10 ns granularity is the load-bearing device fact for later: a 4.13 ms frame ≈ 41,300 ticks, so the
ruler has ample resolution for frame-scale timing.

## Guardrails honoured

- `TIMESTAMP_QUERY` is a **required** device feature — the program fails hard if the adapter can't do it,
  never silently falling back (the benchmark question is specifically about the ruler).
- the **raw primitive** is used (QuerySet → `resolve_query_set` → map/read), no `wgpu-profiler` layer yet.
- the output is provenanced (backend / adapter / driver / period), never a bare number — a bare number
  would already violate the measurement contract.

## The ladder from here (one rung at a time)

```
M1 ✓  the ruler exists on silicon                         (this crate)
M2    add the Rust-side BenchmarkObservation               (bind the number to its conditions in Rust)
M3    FrameArtifact digest → wgpu submission → GpuInterval  (feed the contract a real interval)
M4    PFAL/TCFF shaders · pixel capture · present-to-photon latency · thermal runs
```

The pinned `wgpu = "22.1"` resolved cleanly (`wgpu v22.1.0`) and compiled first try on the device; the
crate is std-Rust + wgpu + pollster only. The machine that ran it is the verifier — this README records
what it observed, with the conditions that produced it.
