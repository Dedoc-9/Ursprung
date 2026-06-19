# Predictive fidelity — prediction → membrane → PFAL

This is Ursprung's pioneering direction: a renderer that spends computation not where the polygons are, but
**where its own approximation is most likely to fail, weighted by the cost of being wrong** — while never
letting that judgment touch what is true. It is the synthesis of the Dini observer, the consequence field,
`lockstep`, and rasterization, all under `observation → allocation`, never `observation → truth`.

> **Status: a measurable hypothesis, not a result.** The benchmark below runs on a *constructed* workload.
> Its numbers `expire_if` measured on real GPU silicon. A benchmark measures the benchmark's world; it does
> not prove universal superiority. `integrity ≠ truth`.

## The discretization hierarchy (where arbitrary boundaries come from)

```
Reality / intended domain
    → Model assumptions
        → Discrete representation
            → Implementation
                → Rendered / measured output
```

Each downward step introduces necessary choices — grid size, tick rate, float format, sampling pattern,
culling threshold, compression, cache strategy, interpolation. The rule (the Arbitrary-Boundary Law):
**when symmetry is impossible, choose a deterministic asymmetry and record it** (`ursprung/conventions.py`).
`determinism → integrity of process`, `determinism ↛ correctness of outcome`.

## Three classes of difference (the debugging language)

`ursprung/divergence.py` forces every observed artifact through a classifier before it is called a bug:

1. **WORLD divergence** — CORE changed. Invalid for any VIEW/ALLOCATOR/OBSERVER change.
2. **REPRESENTATION divergence** — same CORE, different projection/approximation/convention. Expected; measure it.
3. **OBSERVATION divergence** — same representation, different measured behavior. Investigate the ghost.

This is the LLM guardrail in structural form: "replace the rasterizer because this artifact exists" must
first answer *which class* the artifact is (boundary convention / approximation / implementation error /
missing causal model). That is hard to hand-wave.

## A frame is a prediction (the Dini observer)

`ursprung/prediction.py`. A frame is not just an image — it is a prediction about how the world should
continue to appear (TAA predicts history, motion vectors predict correspondence, upscalers predict detail,
reprojection predicts where samples belong). We make that observable and self-auditing:

```
ghost = max(0, observed − predicted)
```

**ghost ≠ error.** It means "the current representation failed to predict this region." It says *"your
model's coverage here is weak"* — never *"this object is important."* The combined law:

> Prediction creates expectations. Determinism preserves the experiment. Ghosts reveal where the model and
> observation diverge. None of them alone define reality.

## The Temporal Prediction Membrane (4 ghost types → allocation responses)

`ursprung/temporal_membrane.py`. Classify the cause of a render ghost; each class maps to an allocation
response, never a world change:

| Ghost | Means | Response | Never |
|---|---|---|---|
| **Temporal** | prediction failed over time (TAA trails, disocclusion, fast camera) | raise temporal samples / reweight history | change world state |
| **Spatial** | representation lost geometry (LOD pop, occlusion miss) | allocate geometry / LOD budget | "this object is less real" |
| **Numerical** | representation boundary showing (z-fight, fp drift, interp) | change representation / precision | ascribe semantic meaning |
| **Causal** | small/barely-visible but affects gameplay/AI/future (the FPS killer) | raise observation budget where confidence is low **and** consequence is high | "this object is important" |

The **Temporal Reality Budget**: a fixed per-frame budget allocated by `uncertainty × consequence` instead
of visible complexity (integer Hamilton apportionment; a `floor` keeps hard-gated regions — e.g. anti-cheat
occlusion — funded). Consequence is an **input** (from `causal_runtime`), never computed as truth here.

## PFAL — the closed-loop perceptual error budget

`ursprung/pfal_bench.py`. The full score:

```
R = U × C × P × S
    U uncertainty   — how wrong is the prediction likely to be?   (the ghost)
    C consequence   — if wrong, how noticeable / gameplay-relevant? (input)
    P persistence   — will the error last across frames?
    S sensitivity   — human/perceptual sensitivity to the artifact
```

R does not say "important object"; it says "this approximation deserves more observation." The carefully
worded claim:

> The renderer spends computation where its current approximation has the **highest expected failure cost** —
> not "the renderer knows what matters."

**Why this is a responsiveness win, not just FPS.** Perceived response ≈ `input_latency + prediction_error +
visual_update_error`. PFAL spends budget on the most damaging temporal errors first — disocclusion zones,
motion boundaries, the weapon sight, moving targets, the view model — so you get **higher perceived
responsiveness at the same FPS**, not merely more pixels. The wall stays cheap; the uncertain, consequential,
fast-moving target gets temporal samples, shadow quality, LOD, and the low-latency path.

## The benchmark (where philosophy becomes engine advantage)

Three allocators split the **same** fixed budget; metric = fraction of true expected failure-cost
(`M = U·C·P·S·needed`) funded (higher better). Measured on the constructed scene (`pfal_bench.demo()`):

```
uniform                  0.587      (safe floor / negative-control reference)
distance_visibility      0.046      (what engines do — budget follows pixels)
pfal (U×C×P×S)           0.897      (≈19× distance/visibility on this world)
drifted_pfal (control)   0.501      (< uniform floor → the bench CAN falsify a bad policy)
```

Distance/visibility loses even to uniform here — by construction the high-failure-cost regions are
small/far/low-visibility (the "tiny moving object behind foliage"), which a pixel-following budget is blind
to. The negative control losing to the floor is the Goodhart guard: a scrambled estimate must not win.

**The real-silicon benchmark** (the honest target, not yet run): compare uniform vs distance/visibility-LOD
vs PFAL at **equal GPU time**, measuring temporal artifacts, input-to-photon latency, reconstruction error,
perceptual quality, and stability during motion.

## TCFF — adding τ (proactive, not reactive)

`ursprung/tcff.py`. PFAL asks "where will the approximation fail, and how expensive is that?" The Temporal
Causal Fidelity Field adds **when**:

```
F = U × C × P × S × τ        τ = temporal proximity — HOW SOON the error becomes observable
```

τ is what moves the renderer from reactive to proactive:

```
reactive : artifact appears → detect → fix → player sees the hitch
proactive: predict instability → allocate ahead of time → the artifact never becomes visible
```

A tiny object 200 m away has low current value — but if it is about to enter view, a motion vector predicts
a collision, a LOD transition is imminent, or temporal reconstruction will amplify the mistake, **τ spikes**
and the renderer prepares before the frame demands it. Three concrete proactive gains (each an allocation
response, never a world change):

- **TAA** — more samples where *history* will break (low history confidence), not everywhere.
- **LOD** — pre-warm + blend the representation *before* the threshold crossing, so the pop becomes an
  invisible deterministic convention instead of a visible event.
- **input→photon** — prioritize what an imminent player action will touch (weapon view, crosshair, collision
  surfaces, moving targets); a 1-pixel enemy-silhouette error while aiming costs more than a perfect
  background shadow. Higher *perceived responsiveness at the same FPS*, because perceived response ≈
  `input_latency + prediction_error + visual_update_error`.

### Perceptual Continuity per Joule (the honest metric)

```
PCJ = avoided perceptual discontinuities / compute budget
```

A 240 fps renderer with visible temporal ghosts can be worse than a 120 fps one that maintains causal
continuity — so the natural metric is continuity per unit compute, not raw FPS. The PCJ bench compares
reactive (visibility) vs PFAL (τ-blind) vs TCFF (τ-aware) at equal budget, with a negative control. Measured
on the constructed scene (`tcff.demo()`):

```
reactive (visibility)   PCJ 0.105     (funds what's already on screen — cannot pre-warm)
pfal (U×C×P×S)          PCJ 0.245     (failure cost, but blind to WHEN)
tcff (U×C×P×S×τ)        PCJ 0.287     (pre-warms imminent high-cost failures)
drifted (control)       PCJ 0.170     (< tcff → bench can falsify a bad estimate)
```

Same honest bound: a constructed-world hypothesis that **expires on real GPU silicon** (real PCJ needs
measured discontinuities and measured joules). It reframes the whole project: the renderer never discovers
truth — it manages *where the arbitrary boundary fails*, so it fails where failure is least perceptually
destructive.

## One world, many lenses

Because allocation never touches truth, the same committed world can feed a cinematic renderer, a
competitive low-latency renderer, a VR renderer, a handheld-power renderer, and a debug scientific renderer —
none fighting over what the world "really is." The world stays the world; each renderer admits it is a lens.

## The chain, and the line it never crosses

```
prediction failure → ghost → attention increase → more samples / fidelity → less visible error
```

```
ghost → change world          FORBIDDEN
observation → allocation      ALLOWED
observation → truth           FORBIDDEN
```
