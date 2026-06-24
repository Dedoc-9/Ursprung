<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk — hardened scope

This document fixes the scope of Weltwerk after the first arc of probes. It states the one principle the
experiments converged on, grades every claim by the repo's two axes (**maturity** × **evidence**), and
draws the boundaries. It is deliberately deflationary: the exciting framings ("causal operating system
for worlds", "observer = scheduler") are recorded as *direction*, with the part that is actually built
and verified marked off from the part that is declared.

## The central law — theorem, mechanism, ambition (kept distinct)

The arc converged on one principle. To keep it from inflating, it is split into a theorem (proven), a
mechanism (an algorithm property in tested regimes), and an ambition (direction). They are not the same
claim and must not be read as one.

### Theorem — `Potential ⊇ Actual`

This is the strongest claim currently supported by the repository.
**Potential** is topological reachability (dependency analysis): the set of chunks an edit *could*
affect under the declared model. **Actual** is measured change propagation: the set of chunks whose
state *did* change. The repository demonstrates `Actual ⊆ Potential` at every measured step.
**Maturity: IMPLEMENTED. Evidence: verified (`pruned ⊆ conservative` ∀t, exhaustive).** This is the
only part treated as a *structural* property.

### Mechanism — divergence-aware reconstruction

A counterfactual future can be reconstructed from a *partial* re-simulation. Two properties, kept
separate (see next section):
- it can be done **byte-identical** to a full honest simulation (correctness), and
- it **can** be cheaper than a full re-simulation (economics).
These are properties of the *current reconstruction algorithms and declared model* — not structural
truths. `dependency-reachability ≠ change-propagation`; `safe-upper-bound ≠ cheap`.

### Ambition — divergence-aware allocation as a scheduler

The direction the arc points at: *measured divergence could decide what gets computed* — across
simulation, networking, and rendering. This is **DECLARED / direction**, demonstrated only for
simulation allocation in toy models. It is the project's hypothesis, not a result.

**Explicitly, no claim is made that:** Actual remains sparse in general systems · Potential is
efficiently computable in arbitrary topologies · either result transfers unchanged beyond the tested
regimes.

## The proven ladder

| Layer | Question | Answer | Maturity | Evidence |
|---|---|---|---|---|
| Weltlinie | Fork reality without corrupting truth? | Yes | IMPLEMENTED | verified — `test_weltwerk` 4/4 (`66f3ecd`) |
| Observer | Measurement stays evidence, not authority? | Yes | IMPLEMENTED | verified — `test_observers` 5/5 + conformance (`735159d`) |
| Scaling (locality) | Counterfactual stays cheap? | Yes, *under locality* | IMPLEMENTED | measured — cf flat ~800 steps, byte-identical (`30313bb`) |
| Coupling (light-cone) | What breaks locality? | Finite information velocity (~2 chunks/tick) | IMPLEMENTED | measured — 8/8, saturation (`a704490`) |
| Allocation (pruned) | Can measured divergence reclaim locality? | Yes (toy) | IMPLEMENTED | verified+measured — `test_teleport` 7/7 (`979bb3b`) |
| Long-range topology | Does a teleport edge destroy the model? | No (toy): potential explodes, actual stays sparse, pruned recovers | IMPLEMENTED | measured — peakActual 5–18 vs peakCone 61–188 |

Every row is a *toy-model* result: the **procedure** transfers (fork→diff→measure→allocate); the
**numbers** do not. `experiment-ran ≠ hypothesis-confirmed`; `toy-measured ≠ production-true`.

## Correctness versus economics (two independent results)

The project contains two results that must not be conflated. One could fail while the other holds.

**Correctness result.** A counterfactual future can be reconstructed from a partial re-simulation while
remaining *byte-identical* to a full honest simulation. Established by equivalence tests; treated as
**verified**. Does **not** depend on divergence being sparse.

**Economics result.** The reconstructed future *can be cheaper* to compute than a full re-simulation.
Established **only** for the measured models — chunk-local coupling, diffusive coupling,
teleport-augmented diffusion — and it **depends on the observed sparsity of divergence**. A future model
may eliminate the economic advantage while leaving correctness fully intact.

> The repository currently proves that divergence-aware allocation can be **correct**. It does not yet
> prove that divergence remains **sparse** in the classes of worlds we ultimately care about.

## Transfer barriers

The repository intentionally separates three proofs that want to collapse into one:

1. **proof of correctness** — the mechanism computes the right answer;
2. **proof of efficiency** — it does so more cheaply than the naive baseline;
3. **proof of transfer** — the result still holds when the regime changes.

A result transfers **only when every assumption required by the measured regime remains true.** The
current scaling results depend on assumptions including: bounded local coupling; deterministic chunk
decomposition; static (or explicitly declared) topology; and divergence remaining sparse relative to
reachability.

**No evidence currently establishes that these assumptions hold for:** player-driven economies, social
coordination systems, faction warfare, migration-heavy simulations, persistent MMO populations, or
adversarial player behaviour.

**Therefore no MMO-scale performance claim is currently made.** The project demonstrates a *candidate
mechanism* whose transfer remains to be tested. `proof-of-correctness ≠ proof-of-transfer`;
`works-in-toy-regime ≠ transfers-to-production`.

### Claim status at a glance

| Claim | Status |
|---|---|
| Deterministic forked world | Strong |
| Byte-identical reconstruction | Strong |
| Observer / evidence separation | Strong |
| `Potential ⊇ Actual` | Strong *within declared models* |
| Divergence-aware allocation (correctness) | Strong *within declared models* |
| Sparsity persists under agent transport | Unknown |
| Sparsity persists under player economies | Unknown |
| MMO-scale scheduler | Direction only |
| World OS / causal substrate | Vision |

A healthy distribution is *weighted toward the top rows*. The rows that are "Unknown / Direction /
Vision" are named on purpose — they are where the next experiments go, not claims being leaned on.

## Known failure modes (what could still kill the thesis)

These mechanisms would invalidate the *economic* thesis **without** invalidating *correctness*. They are
recorded so the document tracks what could still break, not only what survived.

- **Divergence saturation** — if Actual approaches Potential rapidly, the pruned allocator converges to
  the conservative one and the cost advantage disappears.
- **Agent transport** — if agents migrate between chunks, divergence may propagate through *identity
  movement* rather than resource diffusion. Sparsity is unmeasured in this regime. *(This is the most
  important open falsifier — it is what real gameplay does.)*
- **Long-range coordination** — markets, guilds, global auctions, chat, shared objectives may create
  dense dependency graphs whose Actual divergence is *also* dense.
- **Positive feedback** — the measured models are dissipative. Amplifying dynamics may keep small edits
  significant, or grow them, defeating attenuation.
- **Observation overhead** — the pruned allocator does extra bookkeeping (per-chunk `== A`) to decide
  whether divergence exists. Wall-clock behaviour is unmeasured; op-count favours it, wall-clock may not.
- **Network dominance** — even if simulation allocation stays sparse, networking and latency
  (50–150 ms) may dominate overall system behaviour.

## Divergence-aware allocation — scope of the claim (not "observer = scheduler")

The tempting universal phrasing — *the observer is the scheduler* — is **avoided**; it is scoped to the
domains actually demonstrated:

- **Simulation allocation:** IMPLEMENTED — the pruned reconstruction *is* divergence-driven allocation,
  and it is correctness-preserving (in the tested models).
- **Network / render / replication allocation:** DECLARED — the same field *could* drive what is
  replicated and drawn (Phase B/D). Not built, not measured. Until then, "observer = scheduler" is an
  ambition, not an architecture.

## The converged stack (direction)

```
Authoritative World (Weltlinie)        ← deterministic, replayable, commit/discard
        ↓
Counterfactual Branching (Fork)        ← do(); a trajectory pair; the streamtube boundary
        ↓
Measured Divergence (Actual ⊆ Potential)
        ↓
Observer Allocation (the scheduler)    ← simulate where divergence IS  [sim: built; net/render: declared]
        ↓
Rendering / Networking                 ← not built
```

FPS, MMO, city-builder, RTS are *workloads* on this stack, not the stack. This reframing is the scope:
**Weltwerk is a causal substrate; a game is a later content pack.** (Direction — the substrate is real
at toy scale; "OS for worlds" is aspiration, not a delivered system.)

## Phase roadmap — status · gate · falsifier

- **Phase A — causal allocator.** Status: largely DONE (world, fork, observers, locality, light-cone,
  pruned allocator all verified). *Remaining:* benchmark the pruned allocator's **overhead** — it pays
  a per-chunk `== A` comparison each tick; op-count favours it, but wall-clock is unmeasured.
  *Gate to B:* allocator proven cheaper in *practice*, not just in entity-steps.
  *Falsifier:* if the comparison cost dominates, pruning is a wall-clock loss despite the op-count win.
- **Phase B — VIEW (causality renderer, not a game renderer).** Status: UNBUILT. Render the invisible
  structures: committed (solid/blue) · speculative branch (dashed) · potential cone (green) · actual
  divergence (red) · observer attention (yellow). Purpose: a debugger for causality, and a visual
  sanity check on every number above.
- **Phase C — agent worlds.** Status: UNBUILT. *The real stress test of the central law:* current
  coupling is resource diffusion with static chunk membership. *Falsifier (the important one):* if
  **agents migrating across chunks** make actual divergence *non-sparse*, the pruned allocator's
  economics collapse — the whole "Actual allocates" win is contingent on divergence staying sparse
  under realistic dynamics, which agent migration may break.
- **Phase D — networked Weltlinie.** Status: UNBUILT. One authority (server = Weltlinie), clients =
  VIEW; clients subscribe to *actual divergence* rather than map sectors. *Gate:* C must show divergence
  stays sparse under agents. *Falsifier:* network/latency constraints (50–150 ms) may dominate
  regardless of simulation cost — unmeasured.
- **Phase E — MMO / FPS workloads.** Status: UNBUILT. Only after fork, observer, allocator, and network
  correctness are each proven. At that point a game is a content pack, not the experiment.

## Networking carryover (candidate direction — one proven primitive, the rest declared)

The natural bridge to multiplayer is **causal replication**: replace *distance* ("send everyone within
500 m") with *causal relevance* ("send everyone whose future differs if this event exists"). The repo
supports exactly one piece of this rigorously:

- **The Causal Budget Theorem** (`causal_budget.py`, machine-checked `test_causal_budget.py`):
  transmitting the causal cut — the actual divergence, or the a-priori conservative envelope —
  reconstructs every client *byte-identical* to the authoritative future; cutting a chunk is safe **iff**
  it did not change (`cut(x,y) ⟹ Δ(y)=0`); and the criterion is *tight* (cutting a changed chunk breaks
  replication). Budget: `|changed| ≤ |potential| ≤ |broadcast|`. **Maturity: IMPLEMENTED. Evidence:
  verified.** This is the network analog of the simulation equivalence proof: a cheaper *transmission*
  may not change the answer.

Everything else multiplayer is **DECLARED / candidate**, not built: causal interest management, bandwidth
-aware rollback (reconcile only the causal cut), desync debugging (locate first divergence on a causal
wireframe), and a pre-launch network test harness (fork normal-vs-laggy, measure correction/bandwidth).

**Framing discipline (imported critique, applied):**
- The "state → causal sheaf" language is a **design metaphor**: the chunk graph + restriction maps form
  a *presheaf-like* discrete structure, but **no sheaf gluing condition is proven**. Say "resembles a
  finite discrete sheaf over a causal graph", not "is a causal sheaf architecture".
- A **fractal-cut rule** (`dim_H(∂U) > 2 ⟹ ρ → 0`) is **rejected**: a geometrically complex boundary
  does not imply low causal influence (wildfire fronts, market cascades, raid-boss state are complex
  *and* highly coupled). The operational criterion is `Δ(out_q | Δp) < ε` — cut when changing `p` no
  longer measurably changes downstream `q`; its lossless case `ε = 0` *is* the actual-divergence cut.
- **Wilder / wild-embedding** import is modest: a complicated boundary can wrap a *finite* effective
  support. That is precisely `peakCone = 60 ⊃ peakActual = 5` — the wild boundary is the conservative
  envelope; the object of interest is the finite change support.

**Where causal replication does NOT help (named):** it does not beat physics (100 000 players fighting
in one spot ⇒ causal radius = everything); it does not remove latency (100 ms is still 100 ms); it does
not make distributed authority, trust, or security easy. `replication ≠ networking`.

### Formal formulation (sharp discrete objects, each verified == a measured quantity)

`reachability_algebra.py` / `test_reachability_algebra.py` check these against the running engine — a
formalism is adopted only once shown equal to the operational quantity.

- **Potential** `= |Supp((I∨A)^H eᵢ)|` over the boolean semiring — the ball of radius `H`, verified ==
  `cons.touched`. The bare `|Supp(A^H eᵢ)|` (exactly-length-`H` walks) is **rejected**: on a bipartite
  ring it is parity-restricted and *undercounts* the ball (shown strictly smaller in test). Static
  topology only; dynamic teleport chords ⇒ a time-ordered product `∏ₜ(I∨Aₜ)`, not a power.
- **Selective computation** `= 𝒞(c) = c·𝕀(Δc≠0)` for *propagation*; the *computed* set is its
  **neighborhood-closure** `N(diverged)` (you must simulate c to learn `Δc`), i.e. the frontier-overhead
  ring — a measured `≥ 0` surplus over `|changed|`.
- **Selective transmission** `= T* = argmin_{T ⊆ R_H(x)} |T|` s.t. `L(T)=0`, with `L(T)=0 ⟺ T ⊇
  changed`. The feasible region is a **principal up-set**; its minimum is uniquely the generator
  `changed`. This is *not* a Sperner-family / set-cover problem (no combinatorial hardness) — the
  content is the necessity+sufficiency proof, not a search. Optimal Transport applies only to the
  declared *lossy* `Δ(out|Δp)<ε` extension, where fidelity is traded for bandwidth.

## Boundaries — what is NOT shown (consolidated, standing)

- **Line A is still `O(N·H)`.** Knowing actual reality is paid in full every step; only the
  *counterfactual* is marginal. `fork-cheap ≠ simulation-cheap`.
- **Coupling is resource diffusion on a static topology.** No agents cross chunks; chunk membership is
  fixed; no reproduction. The light-cone and teleport results are for this model only.
- **The pruned allocator's overhead is unbenchmarked** in wall-clock (the `== A` comparison).
- **No rendering, no networking, no client prediction, no latency** anywhere in the stack.
- **Toy ecology.** Numbers are non-transferable; the procedure is the asset.

## Discipline (how every claim here was graded)

Maturity (`UNDERCOMMITTED < SCOPED < IMPLEMENTED`) × evidence (`N/A < DECLARED < MEASURED <
MEASURED_BY_INTERVENTION`); `evidence ≤ maturity` (the no-inflation invariant, formalised in
`experiments/live_world_kernel/claim_lattice.py`). Every cost claim is gated behind a byte-identical
equivalence proof (the cheaper mechanism may not change the answer). Every self-test is
**validity-not-outcome**: it asserts the apparatus is sound, never that an edit was "good". Observer
readings are typed `ESTIMATE`; exact state deltas are `EXACT_UNDER_MODEL`; the two never render in the
same register. `green-check ≠ correctness`.

## Commit lineage (`main`)

`66f3ecd` Phase 1 (Weltlinie + do()-diff) → `72a9a9e` observers-on-fork → `735159d` conformance
contract → `30313bb` COW scaling → `a704490` light-cone (+ vacuous-cull ghost fix) → `979bb3b`
teleport / potential-vs-actual.
