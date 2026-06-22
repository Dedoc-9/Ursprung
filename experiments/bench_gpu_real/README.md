<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# bench_gpu_real — the GPU-interval ruler on real silicon (M1 ✓, M2 ✓)

The smallest non-faked claims in the project, and the first ones that did **not** expire on silicon —
because they were measured on silicon. `src/main.rs` is currently the **M2** program (real workload
timing); the M1 empty-pass program is preserved in git history. No window, no swapchain, no pixels, no
fidelity claim.

```bash
cd experiments/bench_gpu_real && cargo run --release
```

## Milestone 2 — the ruler measures real work ✓ (verified on the Ally X)

A trivial WGSL compute shader (an LCG iterated 256× per element, written to storage so it can't be
optimized away) is timed across three workload sizes, 7 runs each. The observation is the contract
shape, serialized to JSON.

```
n=16384     median    880 ns      (min 840,  max 2320)   ← overhead-bound: launch cost dominates
n=262144    median   6800 ns      (min 6560, max 7080)
n=1048576   median  30760 ns      (min 6720, max 32880)  ← work-bound: ~linear with the step above
```

What M2 proves: the ruler **scales with work** (880 ns → 30760 ns), not just bracket overhead, and a
real measurement binds to its conditions (the JSON `BenchmarkObservation`). Two honest notes recorded
rather than smoothed over: (1) the small end is *overhead-bound* — 16× the elements but only ~8× the
time — while 262k→1M is nearly linear, the genuine work signal; (2) the spread is real — the 1M
`min 6720` is an **outlier** (a measurement-origin ghost: clock boost or a partial-capture run), which
is exactly why acceptance used the **median**, never the min. Single GPU numbers lie; distributions
don't — `timing is an event, not an identity`. Still no FPS / latency / PFAL / TCFF / "4.13 ms" claim.

## Milestone 1 — the ruler exists ✓

Times an empty GPU compute pass and prints `(end − begin) × timestamp_period` ns with provenance.

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
M1 ✓  the ruler exists on silicon                         (empty pass, 40 ns)
M2 ✓  the ruler measures real work + BenchmarkObservation  (compute LCG, 880→30760 ns, contract JSON)
M3    FrameArtifact digest → wgpu submission → GpuInterval  (feed the contract a real interval)
M4    PFAL/TCFF shaders · pixel capture · present-to-photon latency · thermal runs
```

The pinned `wgpu = "22.1"` resolved cleanly (`wgpu v22.1.0`) and compiled first try on the device; the
crate is std-Rust + wgpu + pollster only. The machine that ran it is the verifier — this README records
what it observed, with the conditions that produced it.
