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

## The seam plumbing (built + verified, no GPU) — `frame.py` · `timing.py` · `backends.py` · `observation.py`

The boring structure the real backend will fill, so on the device only the GPU calls remain:

```
frame.py        FrameArtifact (immutable; the backend CONSUMES it, never decides its validity) +
                GoldenReplay (a benchmark artifact, not a renderer format — a reproducible RECIPE for a frame,
                like an Event; carries identity only — scene/seed/policy/provenance — NOT the GPU budget)
timing.py       GpuInterval (gpu_end − gpu_begin = the equal-budget RULER) · CpuTiming (provenance, with the
                deliberately-ugly `cpu_observed_gpu_duration` so it can't be mistaken for the ruler) ·
                LatencyProfile (input→photon, a SEPARATE instrument; it MAY sum — a physical chain — unlike
                the fidelity profile, whose axes may not)
backends.py     FixtureBackend (deterministic, no pixels — a FIXTURE that validates the contract, NOT a
                reference renderer) · RealGpuBackend (the seam — raises; four jobs only: submit · timestamp
                the GPU interval · keep determinism above the float boundary · capture present-to-photon)
observation.py  BenchmarkObservation — binds artifact_digest · run-provenance · backend · gpu_budget ·
                gpu_interval · temporal_profile · provenance · (optional) latency. The harness emits ONLY
                observations: a bare profile not bound to its conditions is UNACCOUNTED.
```

The architectural spine: `frame` defines *what* is measured, `backends` *who* measures, `timing` the
*rulers*, `contract` what *comparisons* mean, and `observation` binds the measurement to its *provenance* —
`TemporalErrorProfile without a BenchmarkObservation = UNACCOUNTED`. This maps to the intended layout
(`replay/`, `backends/`, `capture/`) — kept flat to stay runnable; the boundaries, not the folders, are the
point. `run.py` (11/11) verifies: the golden round-trips and derives a backend-agnostic frame; provenance
cannot be empty or a label; the **GPU budget is an execution condition, not identity** (same artifact, two
budgets → same identity, two observations); the GPU interval is the ruler; **a pixel difference is a
measurement, not an identity change, not an artifact mutation, and not a provenance replacement** — the image
hash is another receipt, never the lineage (`artifact_digest`, `temporal_profile`, and `provenance_digest`
stay three distinct fields); latency is optional and may sum while fidelity may not; an observation without
full provenance is UNACCOUNTED; and the real backend is an honestly-empty seam.

The determinism boundary, restated: `CORE` (artifact graph / transforms / digests) is deterministic and
above the float line; `GPU` (rendering implementation, performance observations, pixels) is below it.
Nothing a backend observes can move the world's identity. The deliberately-boring next step is the
`RealGpuBackend` body on the device — no new theory, just the API calls.
