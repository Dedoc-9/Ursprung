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
