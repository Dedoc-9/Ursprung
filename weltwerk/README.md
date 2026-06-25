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

> **Hardened scope + the central law live in [`SCOPE.md`](SCOPE.md).** One principle the probes
> converged on — *Potential ⊇ Actual* (theorem), divergence-aware reconstruction (mechanism),
> allocation-as-scheduler (ambition) — kept distinct, with every claim graded by maturity × evidence,
> the phase roadmap with gates and falsifiers, and a Known Failure Modes section.
>
> **The one sentence that bounds the project:** *the repository currently proves that divergence-aware
> allocation can be **correct**; it does not yet prove that divergence remains **sparse** in the classes
> of worlds we ultimately care about.* Confusing a proven reconstruction mechanism with a proven scaling
> strategy is the project's biggest future risk.

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

## The replaceable lens — and the two products

Because the renderer is honestly **downstream**, graphics are decoupled from existence. You can rip out
the reference rasterizer and swap in an un-optimized debug wireframe, a high-fidelity Vulkan path-tracer
running on an ASUS ROG Ally X, or a pure text stream for an AI agent. **The world does not care.** It
persists beneath the lens because its integrity is maintained by the **runtime, not the viewport** —
`observation ≠ authority`, machine-checked at the boundary (`render/geometry_boundary.py`: rendering
cannot change the authority hash; delete any renderer and the world remains).

That boundary splits the system into two products over one source of truth (`world.wrk` + the causal graph):

- **Product A — the World Author.** Authors the *topology*: `.wrk` text → `WorldSpec` → `CausalGraph`,
  with round-trip-stable serialization, design lint/health, and a pre-play validation gate. Topology is
  cheap to change, geometry expensive — so the topology is the durable artifact and meshes are a
  regenerable projection.
- **Product B — the World Profiler.** Tracks and profiles the *living state*: a deterministic simulation
  authority (events, graph-derived factions/territory), honest replication instrumentation, and the
  consequence **diff** that turns an edit into "what got safer, what got riskier, what became more
  coupled." *Git + Compiler + Profiler for living worlds.*

### The `.wrk` authoring → studio → sim → diff line (built, PowerShell-verified)

| File | Product | What it is | Grade |
|---|---|---|---|
| `authoring/world_format.py` | A | `.wrk` → WorldSpec → CausalGraph → Spatial → Runtime; deterministic round-trip serialize | MEASURED (round-trip) |
| `authoring/world_design.py` | A | design warnings, failure cascade, regime (coupling), timeline, health report | MEASURED |
| `authoring/world_validate.py` | A | pre-play gate: BLOCK undeclared feedback loops · WARN coupling · INFO compression | MEASURED (6/6) |
| `authoring/world_diff.py` | B | consequence diff: SPOF / blast / loops / regime deltas + resilience verdict (heuristic) | MEASURED (7/7) |
| `net/causal_net.py` · `net/causal_metrics.py` | B | naive ≡ causal replication equivalence; deterministic cost instrumentation | MEASURED (5/5) |
| `render/geometry_boundary.py` | — | CausalWorld → GeometryAdapter → Renderer; proves render can't mutate authority | MEASURED (7/7) |
| `sim/world_sim.py` | B | simulation authority: event vocabulary + graph-derived factions / territory | MEASURED (8/8) |
| `fps_demo/weltwerk_studio.html` | A | 3-pane World Studio IDE (editor / 3D / inspector + validation gate) | IMPLEMENTED |
| `fps_demo/weltwerk_world_prototype.html` | B | playable FPS slice; Potential/Actual readout, two-faction contest, hot reload | IMPLEMENTED |

Next on this line (dependency-ordered): **live-edit** (= continuous `world_diff` + re-derive, view held)
→ **runtime questions** (diff + sim trace: "why did blue lose territory?"). Both attach to the same
authority; neither introduces a second source of truth. NOT claimed: MMO / UE5 / networking performance /
latency / AI.

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
| `test_observers.py` | validity-not-outcome: observer determinism · identity→zero · `NO_TRAJECTORY` ghost · `evidence==ESTIMATE` · classifier distinguishes | IMPLEMENTED | verified 5/5 (`72a9a9e`) |

**The canonical platform interface** is `Observer.observe(fork) → Observation` — an observer consumes a
*fork* (a declared intervention + two replayable futures) and returns a typed estimate of the
difference. That is what produces *causal evidence* rather than a dashboard. `per_leg(trace)` stays the
*internal* mechanism (keeping the streamtube boundary around the pairing); a fork-aware observer such
as fairness overrides `observe()` to read `fork.intervention` / `fork.line_a` / `fork.line_b`.

**The universal calibration contract** (`test_conformance.py`): every registered observer must be
*null-calibrated* (`do(nothing) ⇒ zero difference` — a theorem for any pure deterministic observer,
which is why determinism is the prerequisite) **and** *non-degenerate* (moves on at least one real
cause). Honest limit: this is **necessary, not sufficient** — `green-check ≠ correctness`. It certifies
an observer cannot silently become a truth source; it does **not** certify it measures what it claims.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `test_conformance.py` | the universal observer contract: null-calibration + non-degeneracy, over the `OBSERVERS` registry | IMPLEMENTED | awaiting run |

Run the observer slice:

```powershell
cd "weltwerk"; $env:PYTHONHASHSEED="0"; python test_observers.py; python test_conformance.py; python observers.py
```

Run (PowerShell, folder-directed; `PYTHONHASHSEED=0` for the determinism guarantee):

```powershell
cd "weltwerk"; $env:PYTHONHASHSEED="0"; python test_weltwerk.py; python fork.py
```

### Scaling probe (`scale/`) — does fork-and-observe survive a 1000× larger world?

The kernel is scale-agnostic in *concept*; the unproven claim is **cost**. `scale/` is a contained
experiment that separates two cost claims so they can't be conflated:

- **Fork is O(1)** — copy-on-write: a fork shares an immutable base, empty overlay. (Measured.)
- **A counterfactual costs only its blast radius** — you pay `O(N·H)` *once* for the authoritative
  line A (reality is not free); the edit reuses A for every chunk it doesn't touch and re-simulates
  only the dirty region: `O(dirty·H)`, not a second `O(N·H)`.

The load-bearing finding: **locality of effect requires locality of randomness.** A single global RNG
couples every chunk, so a local edit desyncs the whole world and the dirty set explodes to N. With a
**positional** stream `seed(s, chunk, tick)` and chunk-local rules, the dirty set stays constant; the
bench shows a local counterfactual's marginal cost ~flat while N grows 256×. **Boundary, reported not
hidden:** cross-chunk coupling grows the dirty set as a light-cone, and a *global* edit erases the win
entirely (measured). The crux safety net (`test_cow.py`): the by-difference reconstruction is
byte-identical to a full honest simulation of the edited world — the cheaper mechanism may not change
the answer.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `scale/cow_world.py` | chunked world, positional RNG, counterfactual-by-difference (reuse A for clean chunks) | IMPLEMENTED | verified (test_cow 6/6) |
| `scale/test_cow.py` | crux: by-difference B == full honest sim (byte-identical) · O(1) fork · locality · global boundary · determinism | IMPLEMENTED | verified 6/6 |
| `scale/scale_bench.py` | marginal cost of a local counterfactual as N grows 1000× (deterministic op-counts) | IMPLEMENTED | measured: cf flat ~800 steps, cf/naive 4%→0.02% over N=1k→256k |

Not shown by this probe (still open): line A is still `O(N·H)`; no rendering, no network, no client
prediction. `fork-cheap ≠ simulation-cheap`.

```powershell
cd "weltwerk\scale"; $env:PYTHONHASHSEED="0"; python test_cow.py; python scale_bench.py
```

#### Light-cone (`scale/light_cone.py`) — when chunks are COUPLED, how fast does an edit travel?

`cow_world`'s flat marginal cost was mortgaged to chunk-local rules. This probe removes that
assumption: a ring of chunks with nearest-neighbour resource diffusion, so a local edit *propagates*.
It measures the consequence rather than assuming it away.

The finding: there is a finite **information velocity** (~2 chunks/tick on a ring, set by *coupling*,
not by world size), so the dirty cone grows ~linearly in radius and its volume ~quadratically in
horizon. Two honest consequences, both measured: (1) because velocity is size-independent, the
**saturation horizon grows with world diameter** — bigger worlds give a *longer* safe-preview window;
(2) the counterfactual win is now **conditional** — a short preview in a large coupled world is cheap,
a long one costs as much as a full re-sim (the cone fills the world). We also separate the
**conservative cone we pay to simulate** from the **actual divergence** (diffusion can round to an
identical value at the frontier), reporting both. Crux (`test_light_cone.py`): by-difference
reconstruction stays byte-identical to a full honest sim *under coupling* — the harder correctness case.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `scale/light_cone.py` | coupled ring world + cone reconstruction; measures radius / velocity / saturation / cf_cost | IMPLEMENTED | awaiting run |
| `scale/test_light_cone.py` | crux equivalence under coupling · actual⊆cone · monotone · velocity≤2 · cost==cone-volume · saturation · **non-vacuous-propagates** (ghost-guard) · determinism | IMPLEMENTED | awaiting run |
| `scale/light_cone_bench.py` | velocity vs world size; cf_cost vs horizon; the safe-preview window | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\scale"; $env:PYTHONHASHSEED="0"; python test_light_cone.py; python light_cone_bench.py
```

#### Teleport / two-layer cost (`scale/teleport.py`) — potential cone vs actual divergence

The light-cone run surfaced the real architectural distinction: the conservative cone reached 60 chunks
while **actual** divergence peaked at 5 — a ~12× gap between *what could be affected* and *what was*.
That is the difference between **dependency analysis** (potential reachability — a safe, pessimistic
upper bound, what a compiler computes) and **change propagation** (measured divergence — the truth).
This is a first-class principle for the project going forward:

```
World → Fork → POTENTIAL cone (safe upper bound) ⊇ ACTUAL divergence (measured lower bound)
```

A **teleport edge** (auction house, guild storage, portal, global market) is where the two layers come
apart: it makes the potential cone *explode* (a far chunk is reachable in one hop) but can leave actual
divergence *sparse* (an attenuated perturbation barely moves the far region). So an observer that
re-simulates only where divergence is **measured**, not merely **reachable**, recovers the win exactly
where the conservative cone loses it — and it is provably correct, because a chunk can diverge only if
one of its inputs actually diverged. **The observer stops being descriptive and becomes the allocator.**

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `scale/teleport.py` | ring+teleport topology; two reconstructions — conservative (dependency) and pruned (change-propagation/allocator) | IMPLEMENTED | awaiting run |
| `scale/test_teleport.py` | both reconstructions == brute (incl. the pruned allocator) · pruned⊆conservative · teleport explodes cone · transmits · pruned<naive · determinism | IMPLEMENTED | awaiting run |
| `scale/teleport_bench.py` | ring vs teleport: potential cone explosion vs actual sparsity; conservative vs pruned cost | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\scale"; $env:PYTHONHASHSEED="0"; python test_teleport.py; python teleport_bench.py
```

#### Causal Budget Theorem (`scale/causal_budget.py`) — replicate by causality, not distance

The one network-shaped primitive the proofs actually support (it is *not* networking). For a single
authoritative event: which chunk-deltas must be sent so every client ends *byte-identical* to the
authoritative future? **Theorem:** transmitting the causal cut (actual divergence, or the a-priori
conservative envelope) reconstructs the client exactly; cutting a chunk is safe **iff** it did not
change (`cut(x,y) ⟹ Δ(y)=0`); the criterion is *tight* (cutting a changed chunk breaks replication);
budget `|changed| ≤ |potential| ≤ |broadcast|`. Lossless (`ε=0`); the lossy `Δ(out|Δp)<ε` extension is
declared. Out of scope: latency, packet loss, distributed authority, security, prediction —
`replication ≠ networking`. See [`SCOPE.md`](SCOPE.md) for the framing critique (sheaf = metaphor;
fractal-cut rejected; Wilder import = wild boundary ⊃ finite support).

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `scale/causal_budget.py` | Causal Budget Theorem: transmit-by-causality, the budget object | IMPLEMENTED | awaiting run |
| `scale/test_causal_budget.py` | cut lossless (actual + conservative) · potential⊇changed · cut⇒Δ=0 · unsafe-cut-breaks (tight) · budget ordering · determinism | IMPLEMENTED | awaiting run |
| `scale/reachability_algebra.py` | discrete forms verified == engine: Potential=`Supp((I∨A)^H eᵢ)` (not bare `A^H`), transmit=principal-up-set min, compute=indicator closure | IMPLEMENTED | awaiting run |
| `scale/test_reachability_algebra.py` | potential==reflexive ball · bare-power-undercounts · transmit-min · feasible-is-up-set · compute-closure · determinism | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\scale"; $env:PYTHONHASHSEED="0"; python test_causal_budget.py; python causal_budget.py; python test_reachability_algebra.py; python reachability_algebra.py
```

#### Agent transport (`scale/agent_transport.py`) — the sparsity falsifier

The economic results all rode on divergence staying *sparse*, shown only for *attenuating* couplings.
This probe tests the worst case named in `SCOPE.md`: agents **migrate between chunks**, carrying full
state (directed, non-attenuating coupling) — the regime where proximity and causality diverge (real
gameplay). **Measured result: still sparse** — divergence is a bounded traveling pulse (~4 chunks) that
re-converges behind the front (sparsity 0.05 at H=80, *better* than diffusion's 0.08). **The reframing
that matters:** sparsity is a property of **dissipative dynamics**, not of the coupling channel — so the
open falsifier is no longer "transport" but **amplifying / positive-feedback dynamics**, which would go
dense regardless of how coupling is shaped. (`equivalence_pruned` byte-identical under transport, so the
count is exact, not an artifact.)

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `scale/agent_transport.py` | migrating identities; directed non-attenuating coupling; conservative+pruned reconstruction | IMPLEMENTED | verified (test 5/5) |
| `scale/test_agent_transport.py` | crux equivalence under transport · actual⊆cone · non-vacuous-by-migration · determinism | IMPLEMENTED | verified 5/5 |
| `scale/agent_transport_bench.py` | the verdict: sparsity vs horizon (measured 0.36→0.05 = sparse) | IMPLEMENTED | measured: SPARSE (dissipative) |

```powershell
cd "weltwerk\scale"; $env:PYTHONHASHSEED="0"; python test_agent_transport.py; python agent_transport_bench.py
```

### VIEW — the causal debugger (`view/causal_view.py`)

Phase B, begun. Not a game renderer — a **measurement instrument** that makes the four sets impossible
to accidentally merge. It runs the verified engine and emits a self-contained HTML wireframe of the
chunk ring (teleport edges as arcs), coloured by the proven nesting `changed ⊆ allocated ⊆ potential ⊆
all`: **BLUE** unaffected · **GREEN** potential (could differ) · **YELLOW** allocated (simulated, didn't
change) · **RED** actual divergence (= transmit set). The panel shows the four counts and the
transmit/broadcast saving; an edit switcher contrasts a local edit (small lit region) against a GLOBAL
edit (whole ring lit). VIEW reveals committed measurements; it does not recompute causality in the
browser.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `view/causal_view.py` | engine → self-contained HTML causal debugger (4-set colouring + counts) | IMPLEMENTED | awaiting run |
| `view/test_causal_view.py` | validity: nesting holds · 4 classes partition all chunks · counts == engine · determinism | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\view"; $env:PYTHONHASHSEED="0"; python test_causal_view.py; python causal_view.py
```

(`causal_view.py` writes `causal_view.html` — open it in a browser.)

**Regime-aware view** (`view/regime_view.py`) — the question the amplification gate left open is visual:
*where in a real world is reality sparse enough for the allocator to matter?* Renders a heterogeneous
world (mostly dissipative, with an embedded chaotic band); the **regime is measured** (perturb-and-watch,
not read off the gain) and coloured GREEN sparse (allocator works) / PURPLE marginal / ORANGE chaotic
(allocator fails). An edit-footprint overlay shows the contrast: a local edit in a green region stays a
small red pocket; an edit in the orange band floods the cone. The panel calls it: *allocator helps here:
YES/NO.*

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `view/regime_view.py` | regime map (measured) + edit-footprint over a heterogeneous CML world → HTML | IMPLEMENTED | awaiting run |
| `view/test_regime_view.py` | validity: regime measure deterministic · footprint ⊆ cone · well-defined · classes valid | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\view"; $env:PYTHONHASHSEED="0"; python test_regime_view.py; python regime_view.py
```

**Space-time causal field** (`view/causal_field.py`) — the capstone view, where the theory draws its own
picture. A space-time diagram (x = chunk, y = time downward), every cell coloured BLUE committed / GREEN
potential cone / YELLOW allocated frontier / RED actual divergence, over three real systems: **diffusion**
(thin red trace in a green triangle), **teleport** (the green cone forks to a far region), **chaos** (red
floods the triangle). The gap between green and red *is* the economic win, made visible in one glance.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `view/causal_field.py` | space-time diagram over diffusion/teleport/chaos → HTML (canvas + switcher) | IMPLEMENTED | awaiting run |
| `view/test_causal_field.py` | validity: red ⊆ potential ∀t (no superluminal divergence) · frames well-formed · cone monotone · determinism | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\view"; $env:PYTHONHASHSEED="0"; python test_causal_field.py; python causal_field.py
```

### Authoring (`authoring/`) — text → causal topology, before geometry

The thesis the project earned: work on a world's *causal structure* first; geometry and art are a later
projection. `world_spec.py` parses a declarative DSL (`<src> <relation> <dst>` = a directed "can-affect"
edge — e.g. `wall collapses_into courtyard`) into a named causal graph, then *measures* it: per-entity
**Potential influence** (reflexive reachability = blast radius — the same `(I∨A)*` closure as
`reachability_algebra`, over entities instead of chunks) and **feedback-cycle detection** (a structural
amplification *risk* flag). `topology_view.py` renders it as a node-link wireframe: click an entity →
green influence set; feedback loops outlined orange; panel shows blast radius + DAG/cycle regime.

Honest: the spec is a **declared authoring input** (untrusted until measured); a cycle is an amplification
**risk**, not a measured λ>0 (`structural-cycle ≠ measured-amplification` — confirm with `amplify.py`);
**geometry is downstream** and not produced here. Topology is cheap to change, geometry expensive — so the
causal topology is the durable artifact, meshes a regenerable projection.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `authoring/world_spec.py` | text DSL → causal graph; measured Potential blast radius + cycle-risk | IMPLEMENTED | awaiting run |
| `authoring/test_world_spec.py` | parse exact · reachability == transitive closure · cycle detection · determinism | IMPLEMENTED | awaiting run |
| `authoring/topology_view.py` | causal-topology wireframe (entities, edges, influence highlight) → HTML | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\authoring"; $env:PYTHONHASHSEED="0"; python test_world_spec.py; python world_spec.py; python topology_view.py
```

**Causal design linter** (`authoring/world_lint.py`) — the "World Author" core: a structural diagnostic
pass that does what no renderer can — *"show me where I've accidentally built feedback, runaway
influence, a bottleneck, or a dead zone."* Reports **feedback clusters** (SCCs — amplification risk),
**load-bearing** nodes (top blast radius), **exposure** (in-reach), **bottlenecks** (structural
criticality = influence lost on removal), and **isolated** nodes. It operates purely on **Potential**
(structural reachability), so it is **exact and regime-independent** — useful before any simulation,
assets, or networking exist. Structural *risks*, not behavioral verdicts (`structural-cycle ≠
measured-amplification`). This turns the fortress's one-off SCC catch into a repeatable pass.

| File | What it is | Maturity | Evidence |
|---|---|---|---|
| `authoring/world_lint.py` | causal design linter: feedback / load-bearing / bottleneck / dead-zone diagnostics | IMPLEMENTED | awaiting run |
| `authoring/test_world_lint.py` | SCC exact · criticality finds the bottleneck · load-bearing rank · isolated detected · determinism | IMPLEMENTED | awaiting run |

```powershell
cd "weltwerk\authoring"; $env:PYTHONHASHSEED="0"; python test_world_lint.py; python world_lint.py
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
