<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# ADJUDICATION_THROUGHPUT_BOUNDARY — a boundary probe (can commitment outrun verification?)

> **This document names a boundary about *timing*, not authority. It does not assume the boundary resolves.**

A *measurement contract*, the third in the boundary-probe family and deliberately **separate** from its
neighbours — split first, unify only if measurement forces it:

| Probe | Asks | Object |
|---|---|---|
| [`SELF_MODIFICATION_BOUNDARY`](SELF_MODIFICATION_BOUNDARY.md) | can the system *know what changed*? | orientability · recovery (epistemic) |
| [`AUTHORITY_ARBITRAGE_BOUNDARY`](AUTHORITY_ARBITRAGE_BOUNDARY.md) | can an independent party *adjudicate the advantage*? | reconstructability (adversarial) |
| **`ADJUDICATION_THROUGHPUT_BOUNDARY`** | can it be adjudicated *in time*? | verification throughput (temporal) |

The first two ask whether reconstruction is *possible*. This asks whether reconstruction arrives *before the
consequences are load-bearing*. A system can pass both neighbours and still fail here, which is the whole reason
the probe is separate: **a witness can exist and still fail operationally.**

The origin is Brandolini's Law — refuting nonsense costs an order of magnitude more than producing it — but the
law as stated is a rhetorical observation, not a theorem (cold-layer). What survives reduction is a measurable
asymmetry: **verification cost vs production cost**, and what it does to a finite verifier under load.

`declared ≠ verified`. This is the contract a future `adjudication_throughput_probe.py` must satisfy, written
first.

## Purpose

Measure when a system that is **reconstructable in principle** becomes **effectively non-reconstructable**
because verification cannot keep pace with production — and locate the regime boundaries between *cheap to
check*, *floodable*, and *checkable only by intervention*.

## Core question

> Can a claim become **load-bearing** — cross the irreversibility frontier, acquire a committed dependent —
> faster than it can be verified against its declared floor?

A note on words, because the project earns it: it is not "truth" that races verification (`integrity ≠ truth`).
What races is **commitment**. The question is whether *commitment outruns verification*, the temporal sibling of
`frontier_probe`'s "dependency outruns commitment."

## The three states (witness existence × throughput)

| Witness exists | Can keep up | Result |
|---|---|---|
| Yes | Yes | **RECONSTRUCTABLE** |
| Yes | No | **FLOODED** (Brandolini zone) |
| No | — | **SEVERED** |

The middle row is the contribution. `SEVERED` (no witness, information lost) the family already had;
`FLOODED` — *witness present, reconstruction cannot keep up* — is the new failure mode this probe exists to
isolate.

## The measured quantity — verification latency vs the irreversibility frontier

The other probes ask *whether* a claim can be verified. This one measures *when* verification completes relative
to *when the claim becomes load-bearing*, both already objects in the kernel:

- `t_verified` — when verification against the declared floor completes for a claim.
- `t_dep` — the kernel's irreversibility frontier: the first committed event that depends on the claim.

```
FLOODED  ⟺  ∃ claim with  t_dep < t_verified  under the production load
           (it acquired a committed dependent before it was verified)
```

That is `concurrency_probe`'s divergence condition pointed at verification instead of reconciliation: a backlog
settles only if `verify_rate ≥ produce_rate`; under overload it diverges, and the divergence window is exactly
the set of claims that cross irreversibility unverified. The harm is not lost information (nothing is severed) —
it is **commitment forming on the unverified.**

## The axis — verification cost regime

```
CHEAP_TO_CHECK     verification_cost ≪ production_cost
                   verification keeps pace structurally — refutation is a check, not a re-derivation.
                   Achieved by PROOF-CARRYING production (floor-at-construction: grounded_claim, the
                   CommitReceipt, provenance captured AT the frontier): the producer pays the cost, so the
                   verifier only checks. This is the Brandolini asymmetry REVERSED.

BUDGET_BOUND       verification possible, but verify-throughput < produce-throughput.
                   The flood zone. This is where the throughput boundary MEETS concurrency: a finite verifier,
                   an adversary (or merely a fast producer) minting claims faster than they can be checked.

INTERVENTION_ONLY  verification requires an active experiment — observation is insufficient (`observation ≠
                   intervention`). No production discipline makes this cheap; the cost is a do(·), not a check.
```

## Three distinct failure modes → three root causes

The probe's deeper payoff is a clean decomposition the other boundaries blur together:

| Failure | Witness | Root cause | Existing project object |
|---|---|---|---|
| **SEVERED** | none | information loss | `compress ≠ sever`, `NonRecovery` |
| **FLOODED** | exists | throughput deficit | `concurrency_probe` divergence (`new > budget`) |
| **INTERVENTION_ONLY** | exists | identifiability limit | `observation ≠ intervention` (latent/causal arc) |

These are materially different and must not be summed. A system can be `SEVERED` on one claim, `FLOODED` on
another, and `INTERVENTION_ONLY` on a third — the rollup is a **vector across claims**, never a scalar
"reconstructability score." `objectivity is not one scalar`.

## Reused probes (this invents no new machinery)

```
witness existence       →  AUTHORITY_ARBITRAGE / provenance boundary  (is there an independent witness at all?)
dependency formation    →  frontier_probe                              (when does a claim acquire a dependent?)
divergence under load   →  concurrency_probe                           (does the verification backlog settle?)
irreversibility crossing→  kernel (t_dep)                              (when does the claim become load-bearing?)
```

The probe's contribution is the **encoding** — pairing verification latency against the irreversibility frontier
under a declared production rate — not the instruments. Encoding is a declared model (`declared ≠ verified`).

## Measurements (categorical — no scalar, no verdict)

**1. Cost regime** (per claim class): `CHEAP_TO_CHECK / BUDGET_BOUND / INTERVENTION_ONLY`.

**2. Race outcome** (per claim, under the declared load):

```
VERIFIED_BEFORE_LOADBEARING       t_verified ≤ t_dep — verification won the race
LOADBEARING_BEFORE_VERIFIED       t_dep < t_verified — commitment formed on the unverified (FLOODED)
VERIFICATION_REQUIRES_INTERVENTION   no t_verified is reachable by observation alone
```

**3. Backlog behaviour** (system, under load): `SETTLES / DIVERGES` (the `concurrency_probe` quiescent-vs-overload
distinction, applied to the verification queue).

The only legitimate rollup is the unweighted conjunction across claims — *did anything become load-bearing
before it was verified?* — never a weighted throughput number.

## Invariants · observables · assumptions · failure modes · ghosts · alternatives

**Invariants:** committed history is append-only; verification is evaluated against a *declared* floor recorded
as an event; the probe observes the race, it does not throttle production or block commitment (`telemetry ≠
control`).

**Observables:** per-claim `t_produced`, `t_verified`, `t_dep`; the production rate; the verification rate /
cost per claim class; the verification backlog over time.

**Assumptions (declared):** a single logical clock orders production, verification, and dependency; verification
cost per claim is stable within a class; "load" is a declared production rate, **not** measured wall-clock (see
scope). Single-process logic.

**Failure modes:** (a) the probe reports `FLOODED` when `verify_rate ≥ produce_rate` (false positive — the
negative-success gate must catch this); (b) `CHEAP_TO_CHECK` claimed for a class whose check is not actually
O(1) (a hidden re-derivation masquerading as a check — the floor isn't really carried); (c) treating an
`INTERVENTION_ONLY` claim as merely `BUDGET_BOUND` (no amount of verifier throughput will ever close it — a
category error that would waste budget forever).

**Possible ghost signals:** a claim that is `RECONSTRUCTABLE` under the authority probe yet
`LOADBEARING_BEFORE_VERIFIED` here (fully adjudicable, just not in time — the exact gap this probe exists to
expose); a backlog that `SETTLES` in quiescence but `DIVERGES` under a burst (the Brandolini zone is
load-dependent, like `concurrency_probe`'s `GAUGE_WITH_COST` vs `SEMANTIC_LEAK`); a class that flips
`BUDGET_BOUND → CHEAP_TO_CHECK` purely by adding floor-at-construction (evidence the proof-carrying reversal is
real for that class).

**Alternative formulations (rejected for v1, kept at the fork):** model verification as continuous-rate queueing
(richer, but reintroduces scalar throughput before the categorical regimes are earned); let the verifier itself
be adversarially starved (merges with concurrency before this boundary has a measurement); per-observer
verification cost (merges with the `adversary_capacity` lattice — deferred).

## Expected outcome — stated as a falsifiable hypothesis

> **Proof-carrying production (floor-at-construction) is the only general way to keep verification ahead of
> commitment for the check-adjudicable class.** Where claims must carry their own floor, refutation collapses to
> checking and the throughput race is structurally won (`CHEAP_TO_CHECK`). Where they do not, a sufficient
> production burst always wins the race (`FLOODED`). And for the `INTERVENTION_ONLY` class, *no* production
> discipline suffices — the race is unwinnable by observation alone, because verification is a do(·), not a check.

**What would falsify it:** a check-adjudicable claim class that *still* floods despite full proof-carrying — i.e.
checking turns out not to be cheap relative to production after all (the floor doesn't actually collapse
refutation cost). That would mean the Brandolini reversal is illusory for that class, and the boundary is
elsewhere.

The sharper, ordered prediction: with proof-carrying, the check-adjudicable class is `VERIFIED_BEFORE_LOADBEARING`
at any production rate; without it, there exists a burst rate that forces `LOADBEARING_BEFORE_VERIFIED`; and the
intervention-only class is `VERIFICATION_REQUIRES_INTERVENTION` regardless of either. If the boundary falls
anywhere other than at "is the floor carried at production?", the model here is wrong — and that disagreement is
the result.

## Honest scope — and why concurrency still stays separate

Three bounds stay in view:

- **Throughput here is a *declared-rate* model, not measured wall-clock.** A real throughput claim needs the
  concurrency / silicon substrate — the deferred frontier the project keeps arriving at. This probe establishes
  the *logical* boundary (does commitment outrun verification under a declared rate); the *physical* one is a
  later rung. `declared ≠ verified`.
- **`integrity ≠ truth`** still holds: what wins or loses the race is *verification against a declared floor*,
  never truth. A claim verified before it became load-bearing is *accounted*, not *true*; `tested ≠ safe`.
- **Brandolini's Law is the cold-layer origin, not the measurement.** The instrument measures
  `t_verified` vs `t_dep` under a declared load; the law is the intuition that pointed at it.

This boundary is *where* the throughput question and concurrency genuinely overlap — `FLOODED` is a finite
verifier losing a race, which is a concurrency phenomenon. It is kept a **separate probe** anyway, on the
discipline that has paid off repeatedly: when a new idea appears to unify two boundaries, **split it first and
make it prove the unification later.** Merge with `concurrency_probe` only if measurement shows verification
throughput and reconciliation throughput are inseparable.

## The seam (the contract code must satisfy, not yet built)

A future `experiments/live_world_kernel/adjudication_throughput_probe.py` would:

1. reuse the kernel's commit log + `t_dep` (irreversibility) and the floor/`grounded_claim` verification
   unchanged;
2. drive a declared production rate and a declared per-class verification cost; record `t_produced`,
   `t_verified`, `t_dep` per claim;
3. classify each claim's race outcome and each class's cost regime; report the backlog as `SETTLES / DIVERGES`;
4. emit a **vector across claims** — no scalar, no verdict — with a self-test whose first success is *negative*:
   the control (verify_rate ≥ produce_rate, proof-carrying) must come back `VERIFIED_BEFORE_LOADBEARING` /
   not-`FLOODED`, or the instrument is crying flood where there is none, and nothing it says about the
   overloaded cases is admissible.

Until a real client produces claims faster than it can verify them, this is the boundary, named and made
falsifiable, standing one step ahead of the implementation.

> The maze thread here is not authority and not orientability. It is: **can commitment outrun verification?**
> A reconstructable system that cannot reconstruct *in time* is, operationally, not reconstructable — and that
> is a different, and surprisingly fundamental, boundary.
