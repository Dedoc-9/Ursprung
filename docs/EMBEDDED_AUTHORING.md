<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Embedded authoring — a design note (direction, not a verified result)

> **Status.** This is a *design synthesis*, not a built system and not a benchmark. It has no runnable
> evidence behind it yet — `declared ≠ verified`. It is deliberately kept *out of the README's contract
> surface* and recorded here, in the cold layer, because by its own conclusion the most-observed text should
> carry only the minimum stable contract. Read it as a stated direction for the Reality Authoring work
> (`experiments/reality_authoring/`, where "an edit is an event with identity" already lives), not as a claim.

## 1. The shift — editor as a capability of the world

Detached authoring treats the editor as an external program that produces a world file consumed by a runtime.
Embedded authoring inverts the dependency: **the world is an event history that exposes editing as one of its
native interactions.** The editor is not a separate phase; it is another causal participant in the same loop.

The naive version of this — put `if (EditorMode) EditorTools();` in the game loop and mutate live state —
gets the *experience* right and the *foundations* wrong. The foundations are below.

## 2. Scope — event-first is conditional, not universal

Event-sourcing the world is a powerful invariant, not a universal primitive. It is the right foundation only
for editors whose **world state is itself the audited object**. Forcing it everywhere is the over-capture the
rest of this note argues against.

| Context | Primary need | Right primitive |
|---|---|---|
| Solo blockout / VR sculpt | speed, iteration, low latency | direct mutation + local undo |
| Cinematic staging | reversible composition | lightweight command history |
| Shared persistent world | authority, replay, audit | event commit model |
| Simulation / experiment | reproducibility | event + provenance trajectory |

The mistake is turning "necessary at the far end" into "optimal everywhere."

## 3. The primitive — an edit is an Event, not a mutation

The cardinal law (`only CORE may move the committed trajectory`) forbids the editor from writing live state.
The editor is a **privileged Event source**: it *proposes* events, the kernel commits them
(`Event → CommitReceipt`), and the trajectory records them alongside physics and AI. State becomes a
projection: `Stateₜ = F(Event₁, …, Eventₜ)`.

Do this one thing and the usual "extra features" stop being features and become **consequences**:

- **undo** = the inverse event (also committed, never erased — `compress ≠ sever`);
- **provenance** = the trajectory read backward;
- **multiplayer editing** = event ordering on the commit channel;
- **replay** = free, because edits are inputs, not side effects.

This is why provenance and reversibility are the *substrate*, not steps 5 and 6 of a plan.

## 4. Three guarantees, three commit timings

"Capture the guarantee in the causal core, not as a later annotation" sounds singular but is three obligations
with *different* timing requirements. Conflating them is how it fails — make provenance hot and you rebuild
the over-engineered event-everything system; make authority lazy and you reopen the wallhack.

- **Authority** — pre-commit **enforced**. There is no retroactive authorization; a late check is a rollback
  policy, not a check. The gate must precede the transition. (`causal_access`, `capability`.)
- **Provenance** — pre-commit **captured**, lazily **materialized**. The commit needs identity + parent +
  causal handle + integrity marker; the full lineage resolves on demand. (The kernel's hot/cold split: digest
  hot, lineage cold.) The forbidden operation is not compression but `compress → destroy causal link`.
- **Recoverability** — pre-commit **sufficient-to-reconstruct**. You preserve the *ability to derive* the
  state (a seed, a determinism contract, an inverse), not the state itself: `∃R : R(captured) = state`, not
  `captured = full history`.

Same boundary, three different payloads.

## 5. The irreversibility frontier — "real" is relational

"Commit boundary" is still too implementation-centred; it assumes the system knows when reality changes. The
precise statement:

> **A guarantee must be established before the first dependency that would make its absence observable.**

A change becomes irreversible the moment something *depends on it* — an actor reads it, a replica replicates
it, a downstream computation commits against it, a human sees the result. Before that frontier, a rollback can
be invisible; after it, you can only *compensate*, and compensation becomes part of history. Different
observers cross the frontier at different times, which is exactly why distributed systems are hard: a local
write is not necessarily a reality event. *Real* is relational — there is no global "moment it became true,"
only a frontier of first dependencies.

## 6. Hyrum's Law and the conservatism premium

Hyrum's Law is the empirical dual: with enough observers, *every* observable behaviour becomes someone's
dependency, whether or not it was promised. So the dependency surface is only partly knowable:

```
known observers  +  anticipated observers  +  unknown emergent observers
```

Only the first is directly optimizable. This splits "minimum" in two:

- `M_ideal` — the smallest artifact that would preserve the property *if all dependencies were known*.
- `M_actual` — the smallest artifact that preserves it *under uncertainty about future observers*.

Usually `M_actual ≥ M_ideal`; the gap is the **conservatism premium**, and it scales with how hidden the
observer surface is:

| World | Observer surface | Target |
|---|---|---|
| Closed (internal sim, single-user, test harness) | controlled | approach `M_ideal` |
| Open (APIs, multiplayer, mod ecosystems) | unknown | budget for `M_actual` |
| Adversarial (security/sandbox, untrusted clients) | *exploratory* | premium grows; observers hunt dependencies |

The design target is not perfect minimality. It is **minimum under uncertainty**.

## 7. The ratchet — and why the answer is the sealed reserve

The conservatism premium is not a static insurance cost; it is a **feedback loop**. Every artifact you expose
to hedge against unknown observers (stable IDs, timestamps, metadata, version fields) is *itself observable*,
so by Hyrum's Law it too becomes depended-upon — the insurance policy becomes the infrastructure. Hedging
against Hyrum's Law manufactures new surface for Hyrum's Law.

The escape is the distinction the project is built on — **capture without expose**:

```
BAD : hedge leaks to surface → exposed metadata → accrues dependencies → ratchets M_actual
GOOD: capture without expose → sealed reserve   → pure recoverability  → stabilizes M_actual
```

The kernel's **hot/cold split** is exactly this: the digest is hot and observable (and therefore kept minimal,
because everything observable accrues obligations); the lineage is cold and sealed (preserved for recovery,
invisible, so it never becomes anyone's contract). *Observability is liability.* Minimize the observable
surface; maximize the recoverable-but-sealed reserve; never let the hedge leak into the contract.

## 8. Governance — the seal avoids Hyrum's Law but not authority

A sealed reserve is also a concentration of power: who can open it, under what conditions, can it be audited
without becoming public? That loops straight back into the authority recursion — capability grants are
themselves events, so "who authorized the authorizer?" has a genesis problem (an external trust anchor, or an
embedded root with a genesis rule). So the reserve is **not a database**; it is an **emergency instrument**:

```
prove failure condition → authorize recovery query → release bounded evidence
```

And the sharp open hazard: a break-glass query into the reserve **is itself observable** — its existence, its
timing, the fact that it *can* be invoked all leak, so Hyrum's Law applies to the recovery channel too. The
hard problem is not reading the cold layer during catastrophe; it is doing so without the recovery mechanism's
mere existence becoming a peacetime dependency or an adversarial target. The frontier principle, turned
recursively on the seal.

## 9. The three substrates

Forcing contract, runtime, and recovery into one representation is the root error. They optimize differently:

| Substrate | What it holds | Optimize |
|---|---|---|
| **Contract surface** | what outsiders may depend on | `min(observable commitments)` |
| **Operational substrate** (hot) | what the system needs to run *now* | `min(runtime cost)` |
| **Recovery substrate** (cold, sealed) | what is preserved for exceptional reconstruction | `max(recoverability per hidden bit)` |

The present requires coordination (which creates contracts); the past requires reconstruction (which need not).
Expose enough to participate in the present; preserve enough, hidden, to recover the past.

## 10. Connections, and what is *not* established

This note connects existing pieces rather than inventing: the kernel's `Artifact / Event / CommitReceipt /
Query` and its hot/cold `CommitChannel`/`ResolveRing`; `causal_access` / `capability` (authority);
`lineage_scale` (`compress ≠ sever` at scale); `experiments/reality_authoring/` (an edit is an event); and
[`BOUNDARY_MAP.md`](BOUNDARY_MAP.md) (the embedded-observer thread that runs underneath all of this).

Open, and honestly unbuilt:

- **Concurrency** — the common, lethal failure (many actors editing one region) arrives long before deep
  recursion; the single-trajectory ideal trades against scale, and sharding reintroduces the Arbitrary-Boundary
  Law (the seams are model constructs, not features of the world).
- **Reflection depth** — a meta-editor (tools editing tools) is `recorder ∈ recorded` at depth ≥ 2; whether the
  coherent depth is bounded (collapse) or unbounded (strict) is the same interpreter-relative question raised in
  `BOUNDARY_MAP.md`. The embedded editor is the *instrument* that could measure it, not a solution to it.
- **Break-glass observability** — §8's recovery-channel leak is unsolved.

## The principle it closes on

The architecture never found a way to *remove* boundaries. It found a way to *place them deliberately*:

> **Every boundary is a contract boundary. Choose which boundaries the world can see, and which exist only to
> preserve the possibility of repair.**

Which is the project's *first* law restated — the **Arbitrary-Boundary Law**: boundaries are deterministic,
declared, chosen, never truth claims. The arc closed on its origin, which for a project named *Ursprung*
(origin / source) is the right place for it to close.
