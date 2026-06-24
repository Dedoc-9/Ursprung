<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk — a world laboratory you can edit from inside

> **Honest scope (declared, per the no-inflation rule).** Weltwerk is *not* an FPS, an MMO, or a
> "self-evolving world generator." It is **a deterministic simulation substrate where a developer can
> inspect a world, branch it, test interventions, and observe whether a change actually expands the
> world — under a declared model.** A game is a later *client* of this substrate, not its foundation.
> The first slice proves one thing only: *a running world can be forked, diffed, and edited without
> losing causal truth.* Everything past that is roadmap, marked as such.

`Welt` (world) + `Werk` (engineered work). The thing being engineered is not a game; it is the
**editable causal world** a game would later run on.

## Why this exists (and why it is not "AI makes worlds")

The repository spent its history separating *change* from *meaningful expansion*, and *measurement*
from *intervention*. The one-line lesson — **a measurement without an intervention boundary becomes a
claim generator** — is exactly what a world editor needs. `do()` supplies the boundary: the developer
does not edit numbers, they edit a **cause**, on a disposable shadow, and **see** the consequence
before committing. That is the product. The instruments are organs of it, not the point of it.

## The loop (the merge IS the product)

The wireframe is not a camera bolted onto a simulation — it is the human-facing surface of a causal
loop, and the place where the stack's declarations become *visible*.

```
            Intent  ── declared future layer (Phase 3+); NOT built. Building it now would be the
              │        "world optimizer" inflation we explicitly rejected.
              ▼
        Intervention ── do(cause)
              │
              ▼
       Shadow worlds ── line_A (unchanged)  vs  line_B (do(iv)), same dice
              │
              ▼
  ┌──── WORLD KERNEL (Weltlinie) ────┐   authoritative · deterministic · replayable
  │            │                     │
  │       observer fields            │   orbit · generativity · cost · counterfactual  (Phase 2)
  │            │                     │   READ truth; ALLOCATE attention; never define it
  └────────────┼─────────────────────┘
               ▼
             VIEW  ── wireframe = the spatial interface for interventions AND the
                      declared-boundary visualizer (below). Reveals the world; never defines it.
```

### The declared-boundary visual grammar (the VIEW contract, locked now; VIEW built in Phase 2)

The rarest thing a tool can show is *where its own model ends*. The wireframe will render epistemic
status as a first-class visual:

| Visual | Means |
|---|---|
| **solid edge** | committed world boundary (in the Weltlinie) |
| **dashed edge** | speculative / shadow boundary (a fork, not yet committed) |
| **ghost object** | counterfactual-only (exists in `line_B`, never committed) |
| **color field** | an observer *estimate* (allocation, not truth) — with its uncertainty |

So a developer can literally *see* "this is a model boundary, not reality." That is the
Arbitrary-Boundary Law made visible.

## What this slice contains (Phase 1 — built, **awaiting first run**)

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `world.py` | the **Weltlinie** — a minimal deterministic, bitwise-replayable authoritative world (agents, resources, rules) whose trajectory is a pure function of (seed, ruleset, steps) | IMPLEMENTED | awaiting run |
| `fork.py` | **`do()`** — "git diff for worlds": branch a shadow on the same dice, run unchanged vs intervened futures, compute a `WorldDiff`, `commit()` writes the *edit* (not the simulated horizon) / `discard()` evaporates the shadow | IMPLEMENTED | awaiting run |
| `test_weltwerk.py` | **validity-not-outcome** self-test: determinism/replay · shadow isolation · diff soundness · commit/discard semantics. Asserts the *apparatus is valid* — never that an edit was "good" | IMPLEMENTED | verified 4/4 (`66f3ecd`) |

### Phase 2 (begun) — observers as lenses on a Fork

The load-bearing realization: **a `Fork` is a *trajectory pair*, not an endpoint pair** — the declared
streamtube boundary around causation. Observers are lenses on it. An observer is a function of *one*
trajectory (`observe(leg)`); the **diff is the pairing** across the boundary (`diff(A, B)`). This
collapses orbit / generativity / cost / fairness into one shape: each becomes an `Observation` on a fork.

The non-negotiable discipline, enforced in code: **`WorldDiff` is `EXACT_UNDER_MODEL`; observer
readings are `ESTIMATE`.** An estimate can be wrong *inside* the model; it must never render as an
equal-looking number beside an exact delta (that is green-check blindness — the failure this repo
exists to catch). Every `Observation` carries its evidence class and any ghost flags
(`NO_TRAJECTORY ≠ CONVERGED`), and `Fork.report()` prints the two registers separately.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `fork.py` (extended) | a Fork now carries `trace_a`/`trace_b` (the trajectories) + `observe()`/`report()` | IMPLEMENTED | awaiting run |
| `observers.py` | `Observation` (evidence-typed) · `Observer` base · `OrbitObserver` — a **cheap live proxy** for "where is the world going" (the verified CI-bearing `orbit_estimator` is the slow-cadence upgrade) | IMPLEMENTED | awaiting run |
| `test_observers.py` | validity-not-outcome: observer determinism · identity→zero · `NO_TRAJECTORY` ghost · `evidence==ESTIMATE` · classifier distinguishes | IMPLEMENTED | awaiting run |

Run the observer slice:

```powershell
cd "C:\Users\dillb_lzxy763\Claude\Projects\Ursprung\weltwerk"; $env:PYTHONHASHSEED="0"; python test_observers.py; python observers.py
```

Run (PowerShell, folder-directed; `PYTHONHASHSEED=0` for the determinism guarantee):

```powershell
cd "C:\Users\dillb_lzxy763\Claude\Projects\Ursprung\weltwerk"; $env:PYTHONHASHSEED="0"; python test_weltwerk.py; python fork.py
```

## Genealogy — this composes verified pieces, it does not reinvent them

- **commit/speculative/recovery discipline** ← `experiments/live_world_kernel/live_world_kernel.py`
  (which already proved a running world can accept/reject/rewind edits without losing causal truth).
- **the four observer axes** ← `orbit_estimator` · `generativity_estimator` · `counterfactual_fairness`
  · `resource_accounting` (built + self-tested). Wired in at Phase 2 as *allocators*, not verdicts.
- **the VIEW + CORE/VIEW layer law** ← `ursprung/` (raster, view_layer). Reused as the spatial
  interface so multiple views (dev map, player camera, overlays) read one authoritative substrate.
- **the no-inflation invariant + claim lattice** ← `experiments/live_world_kernel/claim_lattice.py`
  governs every status word in this folder.

## Roadmap (each phase gated on the prior being real)

- **Phase 0 — foundation lock.** Authoritative, replayable, commit/revert world. *Mostly done; this
  slice supplies the world-state-granularity piece.* Open hardening: full replay-with-edit-events
  (commit currently mutates the present and logs it; deriving a clean replay log over edits is next).
- **Phase 1 — minimal active world + `do()`-diff.** ← **this slice.** Fork reality, see before/after,
  commit or discard.
- **Phase 2 — world debugger.** Observers as overlays on the wireframe (orbit field, generativity,
  cost), each rendered as *attention-with-uncertainty*, never a "dead zone" verdict.
- **Phase 3 — intervention engine + intent.** Richer `do()` vocabulary; the **Intent layer** (edit
  goals, not states) — explicitly the point where we must *not* become a world optimizer.
- **Phase 4 — creator-in-the-world.** The developer becomes an agent with permissions, editing from
  inside; edits still fork-and-diff before they commit.
- **Phase 5 — MMO scale.** Players as perturbations in a dynamical system. Only after the substrate holds.

## Epistemic stance (the separators this product keeps)

- `simulation-truth ≠ rendered-appearance` — the VIEW reveals the world; it never mutates it.
- `prediction ≠ causation` — the horizon run is a **preview**; only `commit()` writes a cause, and it
  writes the *edit*, not the simulated future. Only the committed trajectory records what occurred.
- `diff ≠ verdict` — a `WorldDiff` reports deltas *under a declared model*; whether an edit is "good"
  is the developer's judgment (or a later observer's allocation), never the substrate's.
- `metric ≠ truth` — observers allocate where to look; they do not certify what is there.
- `deterministic ≠ valid` — replay proves the *trajectory*, not that the rules model anything real.

## The five hard problems (named, not papered over)

1. **Batch estimators vs. a real-time loop.** Bootstrap CIs cannot run per frame. Plan: a cheap proxy
   renders live; the expensive verified estimate runs on a slow background shadow cadence
   (`resource_accounting`'s work-avoidance pattern). The live field is *allocation*, not verdict.
2. **`m_novel(S)` is trajectory-conditioned and its branching model has known break conditions**
   (pooled-vs-trajectory disagreement, already measured). Overlays must show uncertainty; beware
   `CONVERGED` vs `NO_TRAJECTORY` (under-sampling masquerading as convergence).
3. **Discretizing the world into zones/voxels is the Arbitrary-Boundary Law.** Cell edges are
   conveniences; `klein_probe.py` exists to orientation-check false global boundaries.
4. **Observer backreaction / Goodhart.** Tuning the world to maximize a metric stops the metric from
   measuring it (we measured this as naive-proxy-runaway in `rsi_engine`). Defense: the sealed-observer
   pattern from `bench_gpu_real` — the tuning loop must not read the ruler it is scored on.
5. **Determinism for replay.** The Weltlinie is bitwise-replayable (enforced in `world.py`); GPU/float
   nondeterminism lives only in the VIEW and never feeds back. CORE/VIEW law.
