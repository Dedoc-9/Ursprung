<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Reality Authoring Runtime — an edit is an event with identity

Not a game engine, not a world simulator. The layer where **`identity includes provenance` (Law 6) stops being
an epistemic discipline and becomes an architecture.** The question is no longer "can the system preserve
provenance?" (established) but:

> Can a world remain **editable** while preserving the distinction between **authored**, **learned**, and
> **discovered** structure?

An edit is not a mutation. Instead of `world.gravity = 0.5`, the runtime records an **event with identity**:

```
Edit(target="gravity", old=1.0, new=0.5, source="developer",
     justification="gameplay_constraint", scope="world_v12", survival_tests=[...])
```

The world remembers not just what it is, but how it became that way — a World Artifact Graph:
`intent → edit → world-state change → observed behaviour → survival tests → current world claim`.

## Run

```bash
python3 experiments/reality_authoring/run.py     # stdlib only; deterministic
```

## The reality-layer statement of Law 6

> **A world object is not fully defined by its current state; its identity includes the transformations,
> constraints, and sources that produced that state.** It applies to a rock, a physics rule, a creature
> behaviour, a learned latent, and a developer edit alike — everything becomes a historical object.

## The non-anthropocentric invariant (the correction)

The goal is **not** "the developer stays legible." It is that **the source of structure remains inspectable**,
where a source is one of `{developer, algorithm, learned_model, external_data, environment}`. The runtime does
**not** privilege the human: machine authoring is authoring, an emergent pattern names its environment, a
learned factor names its model. No origin is allowed to disappear into consistency.

## What it answers that ordinary engines cannot (7 checks)

```
an edit is an event with identity        (old→new, source, justification, survival — not a silent mutation)
the source of structure spans all origins; no origin disappears
designed vs emerged                       gravity (developer) is designed; flocking (environment) emerged
machine authoring is authoring            an algorithm-tuned rule is 'designed' too — the human is not privileged
remove an edit → dependents collapse      removing the gravity edit collapses jump_height (derived from it)
stable under the world's own transformations = discovered   momentum_conservation survives; flocking does not
```

The last one is the bridge to generated worlds: **discovered** constraints are what survive the world's own
transformations, as opposed to **authored** rules (tied to a removable edit) and **emergent** patterns (appeared
under a perturbation, fragile). A developer can author and generate a world and still read, at any time, which
of its regularities they made, which a model learned, which the environment produced, and which survive
everything — so the world cannot quietly start to look autonomous.

## Provenance of non-recovery — ignorance as a first-class object (`nonrecovery.py`)

`run_nonrecovery.py` closes the symmetry: a world makes *absent* and *unresolved* structure provenance-bearing
too, not just present structure. `provenance_of(target)` answers "why does gravity exist? → developer edit";
`provenance_of_nonrecovery(target)` answers "why is relation R *absent*? → severance" and "why is relation S
*unresolved*? → assumption_limit, missing condition A" — reusing the failure taxonomy as the diagnosis. A
`NonRecovery` is a historical object (digest + source) parallel to an `Edit`. The one thing forbidden is the
silent gap: a structure neither present-with-provenance nor absent-with-a-diagnosis is `UNACCOUNTED`. Built
object-first: the diagnosis is *stored*; `recommended_action()` (stop / declare / allocate) is a *derived view*
over it — the object survives, the policy is replaceable (`preserve provenance first, derive behaviour second`).
8/8 (`python3 experiments/reality_authoring/run_nonrecovery.py`). `identity includes provenance` — now for what
cannot presently be known, as well as for what exists.

## Honest bounds

This is the authoring and provenance layer, not a renderer or a physics solver: it records and classifies the
*origin* and *survival* of world structure; it does not simulate at fidelity, and it does not verify a survival
test was run in good faith (`declared ≠ verified`). A real-time, high-fidelity, learned-world version needs the
real substrate — the un-faked frontier. `edit ≠ mutation`; `designed ≠ emerged`; `authored ≠ discovered`;
source-of-structure stays inspectable — no origin privileged, none erased.
