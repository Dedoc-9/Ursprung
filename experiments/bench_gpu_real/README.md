<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# bench_gpu_real — the GPU benchmark on real silicon (M1 ✓ … M6c ✓; M6d/T1–T4 ✓ — the temporal arc)

The smallest non-faked claims in the project, and the first ones that did **not** expire on silicon —
because they were measured on silicon. `src/main.rs` is currently the **M6d/T4** program (the hidden-future
importance sweep); M1–M5 (the timing ladder), M6a (the perceptual ruler), M6b (the Causal Continuity gate),
M6c (the alignment × budget × exponent sweep), M6d/T1 (the temporal apparatus), M6d/T2 (the temporal ruler),
and M6d/T3 (the temporal causal gate) are preserved in git history.

```bash
cd experiments/bench_gpu_real && cargo run --release
```

## Milestone 6d / T4 — the hidden-future scene + precursor sweep (the deep temporal test) ✓ (Ally X)

T3's monotone scene had no hidden future (the prophet collapsed). T4 builds the scene where a sealed policy
can genuinely fail, so the prophet finally becomes informative — and the deliverable is a *curve*, not a winner.

**The hidden channel is importance, not difficulty** — chosen so it is exploitable under the *fixed* T2
coupling. A content-difficulty spike would reset history (T3's tautology again); instead every tile's content
is **stable** (no reset, accumulation survives), but a TF-time event makes some tiles **matter** more (the
ruler weights per-tile error by `future_importance`, invisible in present pixels). Pre-accumulating a soon-to-
be-important stable tile survives to TF — but only the prophet knows which. **Precursor knob ρ ∈ [0,1]**:
each tile carries `precursor = ρ·importance + (1−ρ)·noise`; ρ=0 hides the future, ρ=1 fully signals it. Sealed
policies see only the precursor; the prophet sees true importance. Coupling fixed; scene the only variable.

Importance-weighted future error (Ally X), the curve `gap(ρ) = causal_future − prophet`:

```
ρ      uniform   precursor_pfal  causal_future   prophet    gap(causal−prophet)   causal⪯uniform?
0.00   0.00552   0.00822         0.00722         0.00480    +0.00242 (≈32× ε)     false
0.25   0.00552   0.00601         0.00583         0.00480    +0.00102              false
0.50   0.00552   0.00522         0.00520         0.00480    +0.00039              true
0.75   0.00552   0.00493         0.00491         0.00480    +0.00011              true
1.00   0.00552   0.00500         0.00480         0.00480    +0.00000              true
ε floor (pixel/struct) = 0.000076 / 0.000137
```

Three findings: (1) **the channel is real** — at ρ=0 the prophet ε-dominates every sealed policy by ~32× ε;
the first scene in the arc where the oracle is informative, and `gap(ρ)` *measures the value of inaccessible
future information* (0.00242 → 0 as the present begins to signal it). (2) **a weak signal is worse than none**
— at ρ < 0.5 both `causal_future` and `precursor_pfal` are *worse than uniform* (acting on a noisy precursor
*starves* the truly-important tiles more than spreading does); `causal ⪯ uniform` only flips true at ρ ≥ 0.5.
There is a **recoverability threshold**: below it, "trying to be causal" backfires; above it, it pays — a real
cautionary boundary for any predictive allocator with an unreliable signal. (3) **sealed reaches the ceiling
exactly at ρ=1** (gap 0.00000): when the precursor *is* the importance signal (up to scale), the sealed policy
*is* the oracle; and `causal_future` consistently edges `precursor_pfal`, so deficit water-fill-in-time still
adds a little over pure-proportional.

The temporal arc as one measured story: **present predicts future (T3)** → causal allocation works, reaches
the ceiling; **future hidden (T4)** → recoverable only above a precursor threshold, and a weak signal is
harmful. `benchmark gain ≠ universal`; the prophet is a ceiling, never a contender.

## Milestone 6d / T3 — the temporal causal gate (a conditional POSITIVE, calibration baseline) ✓ (Ally X)

The first time the project's own preferred hypothesis **won** on a neutral ruler — and the same apparatus that
*falsified* the spatial causal claim (M6b) is the one that now *supports* the temporal one, which is the
strongest evidence it is not biased either way.

Five **sealed** policies (present state + own accumulation only — never the future or the ruler) allocate the
per-frame budget under **equal budget** (3072 samples), scored on the T2 temporal ruler against future
references; plus a **non-admissible prophet** (sees the future) as a calibration ceiling. The only legitimate
temporal lever under T2's coupling: among already-revealed tiles serve the **under-accumulated** ones (future-
causal deficit) and **waste nothing on occluded content that will be reset** — pre-warming is impossible, so
this is the honest temporal form of "drop present-perception S, allocate by future causal loss."

```
policy             future_pixel  future_struct   (equal budget 3072 samples; lower = better)
uniform            0.00599       0.00875         budget-blind — wastes on soon-reset occluded tiles
present_pfal       0.00511       0.00754         avoids occluded waste, but history-blind among revealed
causal_future_d1   0.00486       0.00694    ← ε-frontier
causal_future_d23  0.00486       0.00694    ← ε-frontier
drifted(ctrl)      0.00809       0.01155         negative control behaves (clearly worst)
prophet            0.00486       0.00694         oracle COLLAPSES onto causal (gap 0.00000)
ε floor (pixel/struct) = 0.000053 / 0.000079
```

Four findings: (1) **the temporal lever pays off** — `causal_future` ε-dominates *both* uniform (Δpixel ≈ 21× ε)
and `present_pfal` (Δpixel ≈ 5× ε), on both axes; beating `present_pfal` (which also avoids occluded waste)
means the win is the genuine **future-causal deficit signal**, not mere culling. (2) **the exponent did NOT
matter here** — `d1 ≡ d23` exactly, unlike M6c: that scene had heterogeneous spatial difficulty (the exponent
governs concentration), here every revealed tile is equally hard and only *timing* differs, so the exponent
has nothing to bite on. (3) **the prophet collapsed** (gap exactly 0) — this monotone scene holds *no hidden-
future opportunity*: present state already predicts future relevance, so reaching the ceiling means "present
info suffices," not "universally optimal." (4) **contrast with spatial M6**: spatial causal allocation was
falsified/conditional, *temporal* causal allocation clearly helps — the temporal lever is a real efficiency
(don't spend on content that resets; feed the freshly-revealed deficit) the budget-blind policies miss.

**Honest scope:** supported *under the declared TAA+disocclusion coupling, on this monotone scene*, where the
oracle ceiling is uninformative by construction. The discriminating test — a scene whose future relevance is
**hidden** from present state, where the prophet genuinely separates from sealed policies — is **T4**.
`benchmark gain ≠ universal`.

## Milestone 6d / T2 — the temporal RULER (apparatus, no verdict) ✓ (Ally X)

T1 proved the temporal apparatus; T2 builds the *ruler* T3 will score policies on, and proves it fair first —
the M6a discipline, lifted into time.

**The coupling model is a DECLARED boundary condition, not "the temporal law."** For "spend now to reduce
error later" to be measurable, work at frame *t* must persist to frame *t+k*. The model: **TAA-style history
accumulation with explicit disocclusion invalidation** — a tile's samples accumulate across frames while its
content is stable, and **reset** the frame its content changes (the occlusion edge passes). This is the
*weakest* coupling that still exists in real renderers: present work can genuinely survive, history can
genuinely become wrong, future benefit is *earned* not assumed, and it arises from scene dynamics, not oracle
foresight. It is the rendering analogue of the project's recurring lesson — carried information has a cost and
is valid only until its assumptions change (disocclusion reset ≈ provenance invalidation; `compress ≠ sever`
in time). A different reuse model would change the numbers: `declared ≠ verified`. So the claim T2 earns is
scoped — *under a history-accumulation renderer with explicit disocclusion invalidation, future consequence
is measurable* — enough to make T3 legitimate, never a universal temporal law.

**The isolation that makes check 4 honest:** `future_penalty = error(tf | accumulation WITH disocclusion
resets) − error(tf | accumulation WITHOUT resets)`, same future content and budget — so it measures *exactly*
the cost of history becoming invalid, nothing else.

Five checks, **no policy compared** (Ally X, Vulkan, Radeon 890M):

```
future_error_monotonic    future err @b2 0.01165 > @b8 0.00599 > 0   (less accumulated work → more future error)
negative_control_zero     future reference vs itself = 0.000000
reproducibility_floor      ε(future) = 0.000053 across 4 seeds
temporal_sensitivity       future penalty: emergence 0.00169 (≈32× ε) vs static 0.000000 (exactly 0)
identity_preservation     same kernel world-history (6 commits) → identical future reference
```

**The result that matters:** the ruler **distinguishes present error from future consequence** — the sweeping
world's disocclusions cost 0.00169 (32× the noise floor), while a world with no content change costs *exactly
zero* — and it does so **without looking inside any policy**. That is the precondition T3 needed. No verdict
here. `benchmark gain ≠ universal`.

## Milestone 6d / T1 — the temporal apparatus, on the RealityKernel (apparatus, no verdict) ✓ (Ally X)

M6a–M6c lived in a single frame, so they could only test allocation against *present* render difficulty —
never the **original** Causal Continuity claim, which is about *future* consequence (drop present-perception
`S`; spend now to reduce error *later*). That needs a world that **evolves across frames**. T1 builds only the
apparatus and proves it trustworthy first — the same discipline as M6a.

**The world runs through the kernel.** Each frame's state transition is a `reality_core::Event` committed by
`Core::apply`, chained by `requires` (frame *t* requires frame *t−1*'s digest). So this is also the first
**world-loop client**: the RealityKernel stops being a verified substrate and starts *carrying a world*, its
replay-identity and lineage now operating across **time**, not within a frame.

**The decoupling is emergent, not declared** (the sealed-observer rule, lifted into time). The scene is an
occlusion edge sweeping the tile grid: a tile ahead of the edge is flat (cheap *now*) and turns
high-frequency the frame the edge reaches it (expensive *later*). "Future consequence" is a *consequence of
the world's dynamics*, never an authored per-tile importance map — the precondition for T3 to ask its question
honestly.

Seven checks, **no policy compared** (Ally X, Vulkan, Radeon 890M):

```
world_evolves                  8 distinct states over 8 frames
temporal_replay_identity       commit-digest chain byte-identical across 2 runs (8 commits; head 34d29a70…)
commit_path_severance          an orphan transition (uncommitted prerequisite) is REFUSED; legit chain refused 0
future_reference_reproducible  frame 5 hi-fi render reproduced bit-identically across 2 calls UNDER THE TESTED
                               STACK (RDNA 3.5 / AMD Vulkan / release) — an implementation result, not a portability claim
temporal_error_measurable      future-frame error @4spp 0.01368 > @64spp 0.00376 > 0 (responds to samples)
present≠future decoupling      24 tiles easy@T0=2 but hard@frame5 — EMERGENT from the sweep, not authored
identity ⟂ render budget       commit chain unchanged by rendering at 2 budgets; T0 lineage resolves (compress≠sever)
```

The temporal apparatus reproduced identically **under the tested conditions**: the world evolves through the
kernel, replays identically, refuses severed transitions, renders reproducible futures, measures future
error, and **can pose the present≠future question** with the decoupling emerging from dynamics. (Bit-exact
replay is an implementation result under this hardware/driver/compiler stack, not part of the scientific
claim — the claim is reproducibility under the stated conditions, which is all the ruler needs.) **No verdict** — that is T2 (the temporal ruler) then
T3 (the temporal causal gate). `benchmark gain ≠ universal`.

## Milestone 6c — the alignment × budget × exponent sweep (M6b's flat loss → a measured boundary) ✓ (Ally X)

M6b found causal-waterfill beaten by uniform at one budget — but left three questions open: was the
*exponent* wrong, the *budget* too high, or the *priors* simply uninformative? M6c sweeps all three and
turns the flat loss into a boundary. It runs two causal exponents side by side — `causal_d1`
(∝√(U·C·P·resistance) ≈ difficulty¹, the M6b policy) and `causal_d23` (∝(U·C·P·resistance)^(1/3) ≈
difficulty^(2/3), the **variance-optimal** exponent for SSAA error) — against `uniform` and a `drifted`
control, across budget {2,4,8,16,64} avg samples/tile × alignment α {+1,+0.5,0,−0.5,−1}. Policies stay
sealed (`fn(&TilePriors,u32)->Vec<u32>`); ε is re-measured **per cell** (noise grows as budget shrinks).

Three findings (Ally X):

```
(1) WRONG EXPONENT      causal_d1 over-concentrates: on the ε-frontier ONLY at b2 (lowest budget);
                        dominated elsewhere, usually BY causal_d23. M6b's loss was largely a wrong exponent.
(2) GENUINE NARROW WINS at α=+1, causal_d23 is the SOLE ε-frontier member (ε-DOMINATES uniform) at b8 & b64.
                        b8/α+1: d23 beats uniform on all 3 axes, each beyond ε
                        (pixel .00009>ε.00005, struct .00046>ε.00014, temporal .00008>ε.00005) — real, sub-1%.
(3) NO ROBUSTNESS       at α≤0 (uninformative / inverted priors) uniform ε-dominates everywhere; the
                        allocator does not detect that its own priors are wrong.
```

**Result.** The **strong** claim — "causal importance weighting generally beats neutral allocation at equal
budget" — stays **falsified**. A **conditional** claim is **supported on silicon**: causal allocation helps
only when the priors are informative (α≈+1) *and* the concentration exponent matches the convergence regime
(difficulty^(2/3), not difficulty¹). `ursprung/causal_continuity.py` STATUS is now
`conditional_on_neutral_ruler`. **Ghosts kept** (not smoothed): a non-monotonic **b4 dip** (d23 loses at b4
but wins at b8 — likely Hamilton integer-rounding × the convergence curve), and a **b2 scatter regime**
where even `drifted` reaches the frontier via tradeoffs (frontier membership is weak evidence at extreme
scarcity). HONEST CEILING: one device, one synthetic scene family, SSAA proxy, wins are sub-1% and need
near-perfect priors — `benchmark gain ≠ universal`, and neither does a benchmark loss.

## Milestone 6b — the Causal Continuity gate (a falsification-grade result) ✓ (verified on the Ally X)

M6b is the rung with teeth: it finally compares allocation **policies** on M6a's neutral ruler, under
equal measured budget — the gate that can move Causal Continuity past `supported_constructed` *or falsify
it*. It falsified it (partially), and that is a real result, kept.

**The load-bearing design is the SEALED OBSERVER.** Each policy's signature is `fn(&TilePriors, u32) ->
Vec<u32>`: it allocates the per-tile sample budget from *declared priors only*. The rendered pixels, the
reference, and the scene's ground-truth difficulty are **not arguments** — a policy cannot read the ruler
it is judged by. "Optimize the metric" is structurally unrepresentable, not merely discouraged (that loop
is the Goodhart failure the project exists to detect). Six policies — uniform, distance, visibility, PFAL
(√(U·C·P·S·resistance)), causal-waterfill (√(U·C·P·resistance)), and a drifted negative control — each
distribute the SAME 1024-sample budget (~16/tile over 8×8 tiles), differing only in *where* the samples go.

Two scenes probe the boundary: `aligned` (declared causal priors track real per-tile difficulty) and
`adversarial` (they anti-track it). The Pareto frontier uses **ε-dominance**, where ε is the per-axis
reproducibility floor *measured from the data itself* — you cannot claim dominance below your own noise.

Measured on the Ally X (256×256, per-tile SSAA budget):

```
                  pixel     struct    temporal     (lower = better; equal budget = 1024 samples)
aligned   uniform 0.00538   0.00779   0.00721      ← ε-frontier (sole member)
          causal  0.00542   0.00788   0.00735      ← OFF frontier: ties on pixel/struct (<ε), WORSE on temporal
          drifted 0.00734   0.01033   0.00966      ← clearly worst (control behaves)
adversarial uniform 0.00538 0.00779   0.00721      ← ε-frontier (sole member)
          causal  0.00687   0.00990   0.00949      ← OFF frontier: worse on every axis (~28%, far above ε)
measured noise floor ε (pixel/struct/temporal) = 0.000083 / 0.000133 / 0.000090
```

**The result.** Under ε-dominance, **uniform allocation ε-dominates causal-waterfill in BOTH scenes.** Even
with *perfectly aligned* priors, causal buys no measurable spatial accuracy (pixel/structural within ε) and
is measurably *worse* on temporal stability (gap 0.00014 > ε 0.00009): at ~16 samples/tile every tile is
already near-converged, so concentrating samples starves de-prioritized tiles into flicker while gaining
nothing. Under misalignment it is worse on every axis. So causal allocation has an **asymmetric, downside-
only profile** here — no upside at any alignment tested, real downside under misalignment. This **partially
falsifies** the constructed gate's blessing (`promotion_gate.py` → `supported_constructed`): that gate's
metric was U·C·P-weighted — the thing being optimized — and the circularity does not survive a neutral
ruler. (M6c later REFINED this flat loss into a conditional result — see above — by correcting the
allocation exponent and sweeping alignment/budget; STATUS is now `conditional_on_neutral_ruler`.)

**Explicit limits / the open ghost.** One device, one synthetic scene, one budget (16 samples/tile), SSAA
as the quality proxy. The variance-optimal allocation for SSAA error scales as ∝ difficulty^(2/3); causal
weights ∝ difficulty, so it likely **over-concentrates**. Whether a *lower* budget — tiles genuinely
unconverged, real error to reallocate — ever lets causal reach the frontier is unanswered, and is the
M6c alignment×budget sweep. `benchmark gain ≠ universal`, and neither does a benchmark *loss* generalize.

## Milestone 6a — a fair PERCEPTUAL ruler (apparatus, no verdict) ✓ (verified on the Ally X)

M1–M5 proved the *timing* ruler is fair. M6a proves a *perceptual-error* ruler is fair, against a frozen
high-quality ground-truth reference (256-sample SSAA), **before any policy is compared** (that is M6b).
Error is a **policy-neutral vector**, computed from pixels only (blind), never a scalar winner:

```
pixel_error      mean |approx − reference|     (reconstruction error)
structural_error mean |∇approx − ∇reference|    (edges / meaningful scene change)
temporal_error   mean |approx(seedA) − approx(seedB)|   (instability / flicker)
```

Measured on the Ally X (256×256, SSAA as the quality knob):

```
S=4   pixel_error 0.00981     S=16  0.00501     S=64  0.00274     (fewer samples → measurably worse)
negative control  pixel_error(reference, reference) = 0.000000
reproducibility   |pe(seedA) − pe(seedB)| = 0.000039
error vector (S=16)  pixel/structural/temporal = 0.00497 / 0.00714 / 0.00668
```

Seven checks: the ruler **responds to real degradation** (error falls monotonically as samples rise),
the **negative control reads exactly zero** (it doesn't invent error), it is **reproducible/blind** (two
independent renders agree, the metric sees only pixels), error is a **vector not a scalar**, **identity is
preserved** (sample budget is an execution condition, not the scene's identity), each render carries its
GPU-tick budget with **ghost handling** (the first/cold render's zero interval is flagged and excluded,
pixels unaffected), and the profile JSON round-trips. **Explicit limits:** one device, one synthetic
scene (high-frequency + edge), SSAA as the quality proxy, whole-frame aggregates (per-tile allocation is
M6b). **M6a declares no policy superior** — that is M6b's question, the actual Causal Continuity gate.

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
M6a ✓ a fair perceptual ruler vs a frozen reference         (pixel/structural/temporal vector; blind; limits stated)
M6b ✓ the Causal Continuity gate, sealed + equal budget     →  uniform ε-dominates causal in both scenes at 16 spp
                                                               (flat loss — but the policy used the wrong exponent)
M6c ✓ alignment × budget × exponent sweep                   →  REFINED: strong claim FALSIFIED, conditional claim
                                                               SUPPORTED — causal_d23 (∝difficulty^2/3) ε-dominates
                                                               uniform at α=+1, b8 & b64 → conditional_on_neutral_ruler
M6d/T1 ✓ temporal apparatus on the RealityKernel            →  world evolves THROUGH the kernel, replays identically,
                                                               present≠future decoupling emerges; 7/7, no verdict
M6d/T2 ✓ temporal ruler (TAA accum + disocclusion reset)    →  future error responds, neg-control 0, ε measured,
                                                               emergence penalty 32× ε vs static 0; 5/5, no verdict
M6d/T3 ✓ temporal causal gate (5 sealed + prophet)          →  POSITIVE (conditional): causal_future ε-dominates
                                                               uniform & present_pfal; prophet collapses (no hidden
                                                               future here); exponent didn't matter (homogeneous diff)
M6d/T4 ✓ hidden-future importance + precursor sweep ρ       →  channel REAL (prophet separates 32× ε at ρ=0);
                                                               gap(ρ) measures un-recoverable future info → 0 by ρ=1;
                                                               THRESHOLD: a weak precursor (ρ<0.5) is WORSE than uniform
```

The pinned `wgpu = "22.1"` resolved cleanly (`wgpu v22.1.0`) and compiled first try on the device; the
crate is std-Rust + wgpu + pollster only. The machine that ran it is the verifier — this README records
what it observed, with the conditions that produced it.
