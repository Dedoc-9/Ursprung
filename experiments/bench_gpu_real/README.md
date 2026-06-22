<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# bench_gpu_real — the GPU-interval ruler on real silicon (M1 ✓ … M5 ✓)

The smallest non-faked claims in the project, and the first ones that did **not** expire on silicon —
because they were measured on silicon. `src/main.rs` is currently the **M5** program (equal-budget
comparison harness); M1 (empty pass), M2 (real compute work), M3 (identity binding), M4 (render-pass
timing) are preserved in git history. No window, no swapchain, no pixels read back, no fidelity claim.

```bash
cd experiments/bench_gpu_real && cargo run --release
```

## Milestone 5 — equal-budget comparison is FAIR (metrology, not a verdict) ✓ (verified on the Ally X)

M5 proves exactly one thing and refuses to prove any more: **when two allocation policies consume the
same *measured* GPU-tick budget, the harness compares them fairly — vector-valued, replay-identity-
preserving — and it refuses to compare two policies whose measured budgets differ.** No policy is
declared superior; that is M6's question. The only thing varying between policies is the allocation
decision (a per-region effort vector); workload, replay, scene, ruler, and budget rule are held fixed.

Published budget rule (fixed before coding, policy-independent): *a comparison is admissible iff
`|median_ticks(policy) − target| ≤ 20% · target`; otherwise `budget_violation` and the comparison is
refused* — the M5 analogue of ghost exclusion.

```
A             391668 ticks  admissible ✓   peak/mean/imbal 0.029/0.009/0.009
B (perm of A) 391688 ticks  admissible ✓   peak/mean/imbal 0.030/0.009/0.009   ← within 0.005% of A
cheat (×1.4)  548156 ticks  admissible ✗   budget_violation → comparison REFUSED
A vs B: ADominates   (a Pareto RELATION, never a scalar winner)
```

A and B are **permutations of one effort multiset** — identical total work and scheduling, so they
measure the same budget — yet their error *profiles* differ because the same efforts land on different
base-weighted regions. The cheat uses a larger effort *sum* → ~1.4× the ticks → rejected for spending
more. Seven checks: equal-budget-pair-admitted, cheat-rejected, comparison-is-Pareto-not-scalar,
replay-identity-preserved, deterministic-policy-independent-rule, ghosts-excluded, no-winner-only-a-
relation. The error model is a *declared synthetic* one — **not** a fidelity claim; M5 tests the
apparatus, not the policy. Now when M6 names a winner, nobody can argue it simply spent more GPU time.

## Milestone 4 — a render pass times under the same contract as compute ✓ (verified on the Ally X)

A fullscreen-triangle render pass with a per-fragment work loop, rendered to an **offscreen texture**
(no swapchain), timed with `RenderPassTimestampWrites` — the identical machinery as the compute
milestones. The point is that the contract is **backend-agnostic across pass types**.

```
render pass (1080p, frag loop ×64): spread 700040–915160 ns  (~0.7–0.9 ms)
12 runs · identities seen: 1 · timing ok: 11 (1 ghost excluded) · 10 distinct timings
frame.digest = 4f1cb7c2495167e7   ← IDENTICAL to M3's compute run of the same GoldenReplay
```

The quiet result: the digest matches M3's exactly. Same `GoldenReplay` → same world identity, *whether
measured by a compute or a render pass*. Identity is the world's, not the pass's. The render-pass
timestamps worked via the in-pass path (no `write_timestamp` fallback needed on RDNA 3.5 / AMD Vulkan),
a real cold-start ghost fired again at run 1 (flagged, excluded, identity intact), and the magnitude
jumped two orders (≈10 µs compute → ≈0.8 ms render) because ~2M fragments × 64 sin/cos is real work.
Seven checks: render-pass timestamps function, duration positive, one-identity-many-timings,
observation-carries-digest, ghost-is-not-identity, headless-offscreen-no-swapchain, JSON round-trips.
Still no PFAL / TCFF / fidelity claim.

## Milestone 3 — the measurement is bound to the world identity ✓ (verified on the Ally X)

A `GoldenReplay` derives a `FrameArtifact` whose digest is the stable identity of *what is measured*;
every `BenchmarkObservation` carries that digest. The same frame is measured 12 times — identity stays
one, timing is an independent observation.

```
frame.digest() = 4f1cb7c2495167e7
12 runs · identities seen: 1 · timing ok: 11 (ghosts excluded: 1) · spread 9600–11720 ns
```

The headline is the lone identity over varying timing — `identity = stable; timing = observed`, the
same kernel distinction enforced everywhere else. And a **real ghost appeared**: run 1 returned a
zero interval (`begin == end == 0`, a cold-start timestamp the driver hadn't validated), was flagged
`timing_status: NonPositive`, excluded from the timing stats — yet its `artifact_digest` was still
`4f1cb7c2…`. A ghost interval changes the number, never the identity. This was the Q2 handling we
designed for the synthetic case firing on a genuine silicon anomaly. Six checks: same-replay→same-digest,
same-digest→same-dispatch, observation-carries-digest, JSON round-trips, one-identity-many-timings, and
non-positive-interval-is-a-ghost. Still no FPS / latency / PFAL / TCFF claim.

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
M3 ✓  measurement bound to world identity                  (GoldenReplay→FrameArtifact digest; ghost caught)
M4 ✓  render-pass timing under the same contract            (offscreen 1080p, ~0.8 ms; digest == M3's)
M5 ✓  equal-budget comparison is fair                       (perms admitted, cheat refused, Pareto vector)
M6    PFAL vs TCFF on silicon                               →  Causal Continuity: supported_constructed → law
```

The pinned `wgpu = "22.1"` resolved cleanly (`wgpu v22.1.0`) and compiled first try on the device; the
crate is std-Rust + wgpu + pollster only. The machine that ran it is the verifier — this README records
what it observed, with the conditions that produced it.
