<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# bench_gpu — the measurement contract, executable (the benchmark is NOT built)

The verifiable core of [`docs/REAL_SILICON_BENCHMARK.md`](../../docs/REAL_SILICON_BENCHMARK.md): the part
of the GPU benchmark that can be made executable **without a GPU**, so the discipline is locked before the
harness exists. It makes no fidelity claim and produces no pixels.

```bash
python3 experiments/bench_gpu/run.py     # stdlib only; deterministic; 9/9
```

## What it enforces (so the future harness cannot quietly violate it)

```
RunRecord            a benchmark run is an Artifact — full run-provenance + digest, or it is UNACCOUNTED
TemporalErrorProfile a vector (reconstruction · motion · boundary · perceptual); NO .score()/.total()
dominates/pareto     a Pareto verdict (pareto_win / pareto_nondominated / dominated) — never a scalar rank
fidelity_compare     refuses a result without provenance; measures every policy at the SAME GPU-tick budget
GpuBudgetBackend     a seam: RealBackend.measure() raises NotImplementedError — measurements are not faked
```

The four invariants, made mechanical: *the thing that licenses a number travels with it* (UNACCOUNTED
without provenance); *the GPU clock is the shared ruler* (identical tick budget per policy); *four failure
modes never average into one* (no scalar collapse — the same discipline as `integrity ⟂ adequacy`); and the
benchmark is a *measurement boundary, not a courtroom* (a dominated candidate is a recorded result, not a
verdict on the hypothesis).

## What is built vs the frontier

```
built + verified (no GPU):   RunRecord · TemporalErrorProfile · dominates/pareto_front/compare · equal-budget
                             guard · the seam interface · MockBackend (a deterministic FIXTURE, not a result)
the un-faked frontier:       RealBackend — Vulkan/DX12/wgpu on real silicon (e.g. the Z2 Extreme), with GPU
                             timestamp queries and present-to-photon capture. Running it is the next stage.
```

`MockBackend` exists only to exercise the comparator's logic; its numbers are a fixture, not a measurement.
When the real backend lands on the device, the *only* thing that changes is where the profiles come from —
the contract (provenance, equal budget, Pareto profile) is already fixed and tested. Substrate ≠ benchmark;
`declared ≠ verified`.
