<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SELF_MODIFICATION_BOUNDARY — a boundary probe (not a roadmap, not an architecture)

> **This document names a boundary. It does not assume the boundary resolves.**

A *measurement contract* in the spirit of [`REAL_SILICON_BENCHMARK.md`](REAL_SILICON_BENCHMARK.md) and
[`BOUNDARY_MAP.md`](BOUNDARY_MAP.md): it fixes the question and the instrument **before** any code, so that
whatever a future probe measures is a result and not a self-fulfilling design. It is explicitly **not** a
"self-governing runtime" — that phrase already contains the conclusion. It is the probe that would tell us
whether such a thing is even orientable.

`declared ≠ verified`. Nothing here is a result yet; this is the contract a `self_modification_probe.py` would
have to satisfy, written down first.

## Purpose

Measure whether a runtime can **modify its own modification mechanism while preserving the same provenance
guarantees** — and, where it cannot do so globally, locate exactly where the guarantee becomes *only locally*
definable.

The runtime in question already exists in the small: the live-world kernel
([`../experiments/live_world_kernel/`](../experiments/live_world_kernel/)) demonstrated, at 16/16 in
single-process logic, that live mutation + authority + provenance + rollback can coexist without making every
mutation immediately part of the external contract. That earned the right to ask the next question — **not** the
status of an answer.

## Core question

> When a system changes the mechanism that decides *what changes are committed*, where does the commit frontier
> remain **globally** definable, and where does it become **only locally** definable?

That is the exact point where

```
modifier ──> modified
```

stops being a clean separation, because the modifier becomes part of the modified state.

## Where this sits (and what it reuses)

This probe invents no new mathematics. It reuses three already-verified instruments, each 7/7:

- **orientability** — `klein_probe.py` (signed-cycle frustration; the `OBSERVER` constant
  `world → observer → event → world` is already classified `NON_ORIENTABLE` — "the recorder is in the recorded").
- **frontier locality** — `frontier_probe.py` (where possibility becomes obligation) and `concurrency_probe.py`
  (leakage / partition-local vs global).
- **recovery integrity** — the kernel's `resolve` / `NonRecovery` and the `compress ≠ sever` invariant, applied
  at the *recursive* level.

The contribution of this document is the **encoding** — which self-references become signed edges, which cases
to run — not the tests themselves. Encoding a boundary into a model is a *declared* model (`declared ≠
verified`).

## Minimal model — three actors

```
A = runtime state            (what the world currently is)
M = mutation mechanism       (the rule that decides which changes commit)
O = observer / validator     (the thing that can judge whether a change is authorized / recorded)
```

**Normal case — the validator is outside the thing being changed:**

```
   O
   │
   ▼
   M ──────▶ A
```

`O ⟂ (M, A)`: a clean dependency frontier, stable provenance, an identifiable rollback target. This is the
control — it must come back `ORIENTABLE`, or the instrument is hallucinating recursion everywhere.

**Self-modifying case — the mechanism becomes part of the modified state:**

```
      ┌───────────────┐
      │               │
      ▼               │
      M ────────────▶ A
      ▲               │
      └───────────────┘
```

Now `M ⊆ A` and `O` may have no vantage outside the loop. The question is not "is this forbidden?" but "where
does the loop stay orientable, and where does it frustrate?"

## The cycle, precisely — and the candidate that breaks it

The self-modifying loop is structurally the `klein_probe` `OBSERVER` cycle: a boundary followed through its own
consequences that may return with the side reversed. If it frustrates (sign-product −1), there is **no
consistent global "outside"** — no single experimental-vs-committed cut over the whole system.

There is one candidate that can break the cycle without magic, and the probe must test whether it actually does:
**commit-time anchoring over append-only history.** A modification commits *under the regime in force at its
commit instant*, before the new regime exists; and committed history is immutable. If that holds, the apparent
circularity is broken by **temporal precedence**, not by standing outside the system:

```
committed(old regime)
        │
        ▼
   mutation(event)          ← committed UNDER the old regime
        │
        ▼
   new regime               ← exists only AFTER, governs only later events
```

The mutation is *historical*; the new regime **cannot rewrite the conditions that produced itself.** The probe's
job is to find where this anchor holds (→ `LOCAL_ONLY`, orientable per-cut by commit order) and where it fails
(→ `NON_ORIENTABLE`, the anchor itself was the thing mutated).

## Probe cases

### Case 1 — external modifier (the control)

```
engine ──▶ world
```

Expectation: clean dependency frontier; provenance stable; rollback target identifiable; **`ORIENTABLE`**.
This case exists to confirm the instrument does **not** detect recursion where there is none.

### Case 2 — modifier edits an *authority* rule

```
rule:      "events require a signature"
mutation:  "change the signature requirement"
```

Questions:

- Does the **old** rule remain authoritative over the mutation that creates the new rule?
- Does the **new** rule retroactively re-classify the mutation that produced it?
- Can the system name a causal parent **without circularity**?

Expected interesting result: the mutation is historical, committed under the old rule; the new rule governs only
*subsequent* events. The cycle is broken by commit order → **`LOCAL_ONLY`** (orientable within each commit-time
cut, no single global cut needed). If instead the new rule *can* re-classify its own creating event, that is a
frustrated cycle → `NON_ORIENTABLE`, and append-only history was violated.

### Case 3 — modifier edits the *provenance* rule (the hard one)

```
v1:        "record parent hashes"
mutation:  "disable parent hashes"
```

Then ask the recursive severance question:

> Can the system prove the transition **using the very record it removed**?

This tests `compress ≠ sever` at the recursive level. Case 2 mutates *authority* (who may change what); Case 3
mutates *recording* (whether change is provable at all) — a different category. The sharper prediction the
recursion forces:

- **authority self-edit** can stay `LOCAL_ONLY`, anchored by commit-time precedence (Case 2);
- **provenance self-edit** goes `NON_ORIENTABLE` *iff the removed record was the only proof of its own removal's
  lineage* — the act of severing destroys the evidence that the severance was lawful.

The honest expected outcome is **not** "self-modification is impossible." It is that the provenance regime in
force at commit must itself be recoverable by a path **independent of the regime's later mutation** — the
recursive form of `durable = ∃ recovery path independent of the failure`. Where that independent path exists, the
transition is provable (`recoverable-via-independent-path`); where the mutation removes its own only witness, the
system must report **`SEVERED`, never a reconstructed guess.**

## Measurements (categorical — no scalar, no verdict)

Do not measure "intelligence," "safety," or a "self-governance score." Measure three independent axes, each as a
category, surfaced as an attention signal, never a directive (`observe ≠ enforce`).

**1. Orientability** *(via `klein_probe`)* — can the system define `inside = mechanism`, `outside = observed
state` **globally**?

```
ORIENTABLE      one consistent global cut exists
LOCAL_ONLY      orientable per commit-time cut, but no single global cut
NON_ORIENTABLE  following the loop reverses the experimental/committed sense (frustrated cycle)
```

**2. Frontier locality** *(via `frontier_probe` / `concurrency_probe`)* — where can the dependency frontier (the
point where a candidate becomes obligation) be detected?

```
global              detectable for the whole system at once
partition-local     detectable only within a sub-region / commit-time cut
observer-dependent   different validators disagree on where it is
unknown             not detectable with the available record
```

**3. Recovery integrity** *(via the kernel's `resolve` / severance)* — can it reconstruct *"why did this
modification exist?"* **without relying on the modified mechanism**?

```
recoverable                         the regime-at-commit is still directly resolvable
recoverable-via-independent-path    provable through a path the mutation could not also remove
SEVERED                             the only witness was removed — reported, never guessed
```

The only legitimate rollup is the unweighted conjunction across the three axes and the three cases; there is no
weighted "self-governance number," and there never will be (`objectivity is not one scalar` — not even for this
auditor).

## Invariants · observables · assumptions · failure modes · ghosts · alternatives

**Invariants the probe must not violate** (it observes; it does not enforce): committed history is append-only;
the regime-in-force is evaluated at commit instant; the instrument is a pure function over the log and never
mutates the world it measures (`telemetry ≠ control`).

**Observables:** the commit log; per-event regime-at-commit; the signed boundary graph for each case; the
resolve/severance result for each "why did this exist?" query.

**Assumptions (declared):** a single logical clock orders commits; the regime-at-commit is itself recorded as an
event (not ambient); single-process logic (concurrency is a *separate* boundary — see below). Each assumption is
a convenience to question, not an invariant to trust.

**Failure modes:** (a) the new regime re-classifies its own creating event (append-only violated) → false
`ORIENTABLE`; (b) provenance self-edit removes its own only witness and the system *guesses* instead of
reporting `SEVERED` (the lethal one — `compress ≠ sever` broken at the recursive level); (c) the instrument
detects recursion in Case 1 (false positive — instrument miscalibrated).

**Possible ghost signals:** a transition that resolves `recoverable` in Case 2 but `SEVERED` in Case 3 from the
*same* commit order (locates the authority/provenance asymmetry); an `observer-dependent` frontier where two
validators built from the same log disagree (the embedded-observer non-orientability made visible); a case that
is `LOCAL_ONLY` under one partition and `NON_ORIENTABLE` under another (the cut itself is doing the work —
Arbitrary-Boundary Law at the recursive level).

**Alternative formulations preserved (rejected for v1, kept at the fork):** model `O` as *multiple* validators
from the start (tests `observer-dependent` directly, but conflates self-modification with consensus — a
concurrency concern, deferred); allow regime mutation to be *itself* speculative-then-committed (richer, but
doubles the recursion before the single-level result exists); encode regimes as a lattice rather than a sequence
(anticipates the layered-authority outcome — but that would *assume* the conclusion this probe is meant to earn).

## Expected outcome — stated as a falsifiable hypothesis

The leading hypothesis (to be falsified, not confirmed):

> **Self-modifying systems require layered authority, because no single layer can both define and be governed by
> the same boundary.** The recursion would then *force* a stratification

```
kernel
  ├── stable authority substrate        (defines the regime; not mutable by the regime it defines)
  ├── mutable operational substrate     (changes under the stable substrate's regime)
  └── experimental substrate            (private, speculative, discardable)
```

— not because the architecture was chosen, but because a single-layer self-reference frustrates.

**What would falsify it:** a single layer that both *defines* and *is governed by* the same boundary and still
comes back `ORIENTABLE` with `recoverable` integrity across all three cases — i.e. genuinely orientable
self-reference, the commit-time anchor sufficing alone with no stratification. If Case 3 returns `ORIENTABLE` /
`recoverable` (provenance self-edit provable without any independent path), the layering hypothesis is wrong and
temporal precedence alone is enough.

The sharper, ordered prediction (more falsifiable than the headline): Case 1 `ORIENTABLE`; Case 2 `LOCAL_ONLY`
(authority self-edit anchored by commit order); Case 3 `NON_ORIENTABLE` / `SEVERED` *exactly when* the mutated
record was its own only witness, `LOCAL_ONLY` / `recoverable-via-independent-path` otherwise. If the boundary
falls anywhere other than between authority self-edit and witness-destroying provenance self-edit, the model
here is wrong — and that disagreement is the result.

## Honest scope — and why concurrency stays separate

This probe does **not** establish that a self-modifying runtime is intelligent, safe, or buildable at scale. It
tests one boundary: *can an observer modify the rules that define reality and still know what reality is?* It is
single-process logic; it issues categories, not verdicts; a clean result means "no frustration detected under
this declared encoding," never "safe" (`tested ≠ safe`).

The **concurrency** probe remains a different artifact, deliberately:

- concurrency asks: *can many observers share one reality?*
- self-modification asks: *can an observer modify the rules that define reality?*

They may eventually meet — a self-modifying system under concurrency is the union of two open boundaries — but
combining them now would recreate the exact failure mode the discipline forbids: **merging two unknowns into one
grand theory before either has a measurement.** Each boundary earns its map alone first.

## The seam (the contract code must satisfy, not yet built)

A future `experiments/live_world_kernel/self_modification_probe.py` would:

1. reuse the kernel's `EditEvent` / commit log unchanged (regime-at-commit recorded as an event);
2. encode each of the three cases as a signed boundary graph and classify orientability via `klein_probe`;
3. locate the dependency frontier via `frontier_probe` / `concurrency_probe`;
4. answer "why did this modification exist?" via the kernel's `resolve`, reporting `SEVERED` rather than guessing;
5. emit the three categorical axes per case as a vector — no scalar, no verdict — with a self-test whose first
   success is *negative*: Case 1 must be `ORIENTABLE` (no false recursion) before any positive claim about
   Cases 2–3 is admissible.

Until then this is the boundary, named and made falsifiable. `declared ≠ verified`; the map is not the territory;
the probe is not the proof.
