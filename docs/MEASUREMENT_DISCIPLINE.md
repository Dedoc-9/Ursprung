<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Measurement Discipline

The conceptual arc of Ursprung (M1–M21 plus Channel Discovery) does not end in a list of defenses. It ends in
a **measurement discipline** — a way of stating what was checked, by whom, and where the check stops. This
document is not a feature. It is a **boundary marker**: it records what the project is allowed to claim, and
what it spent twenty-one milestones refusing to claim.

## The last symmetry break

Early milestones carried an implicit assumption:

```
attacker has a model        defender has the truth
```

Channel Discovery broke it: the defender is *also* an observer, with a possibly-incomplete model of what
channels exist. M21 broke the next one: the defender's **detector is itself a hypothesis class** — an
adversary model wearing a defender badge. There is no omniscient measurement layer. There are only competing
observers under bounded model classes.

```
WORLD ─→ observable trace ─→ attacker representation ─→ inference ─→ actions ─┐
  ▲                                                                          │
  └──────────────────────────── new trace ──────────────────────────────────┘

WORLD ─→ defender telemetry ─→ defender estimator ─→ inference ─→ mitigation ─→ new trace
```

Both the attacker and the defender are doing inference under bounded model classes. The defender is not
outside the system; the defender is another participant trying to infer what is inferable.

## The measurement loop

The honest workflow is open-world:

```
discover  ─→  measure  ─→  classify observer  ─→  mitigate  ─→  re-measure
```

Not the closed-world one, which is how reviews miss things:

```
invent channel list  ─→  test the list  ─→  declare safe
```

## Closed-world failure

```
Known channels:   C1  C2  C3
Reality:          C1  C2  C3  C4  C5  ...
                              └────┴── where the surprises live
```

`checked channels ⊂ observable channels`, and the gap is where every real breach lives. In
`channel_discovery.py` the audited set caught `correction_events`, `frame_time`, `resource_events` and missed
`animation_events` (I ≈ 0.27) — an audit of only the enumerated set would have **passed** while the system
bled through the unlisted channel.

## What a result means

```
Observed:        "No leak found."

Does NOT mean:   "No leak exists."

Means:           "No leak was found by estimator E, over trace distribution D,
                  against observer class A, within budget N."
```

A `MeasurementResult` therefore never reports `channel_safe = true`. It reports:

```
MeasurementResult:
    channel               # what was measured
    estimator_class       # the hypothesis class of the detector (C_marginal, C_sequence, …)
    detected_information   # how much was found, by THIS class
    coverage_boundary      # what THIS class is blind to
```

The detector's reach is itself an Adversary Information Capacity choice (M21), one level up. A channel can read
as severed under one estimator and leak freely under a richer one. Demonstrated, not asserted: the same
`accumulation_events` channel reads **I = 0.00** under a marginal (per-sample) estimator and **I = 1.00** under
a sequence (windowed) estimator. "No leak" is always "no leak *under this observer class*."

Estimator classes and their blind spots:

| estimator class    | catches                                   | blind to                                  |
| ------------------ | ----------------------------------------- | ----------------------------------------- |
| histogram / marginal MI | obvious per-sample buckets           | temporal accumulation, cross-sample structure |
| frame classifier   | visual / behavioral separability          | cross-frame accumulation                  |
| sequence model     | temporal signatures                       | hardware / cache effects, horizons > W    |
| representation learner | discovered combinations               | its own embedding assumptions             |

## Two compressed lessons

The whole arc kept returning to one trap — *a thing can look like information without being information, and
look harmless while being information*:

```
integrity   ≠ truth
consensus   ≠ truth
authorization ≠ harmlessness
representation ≠ generator
correction  ≠ cause
correlation ≠ leakage
```

The XOR mistake during Channel Discovery is the miniature of all of them. `secret XOR uniform_noise =
uniform_noise`, so `I(animation; secret) = 0` — a signal that *looked* maximally related carried zero usable
information (a one-time pad). Its mirror: the `OR` construction carries only **0.27 bits**, which *sounds*
harmless — until M13 accumulation, M20 adaptive probing, or multiple observers turn a tiny channel into a
large one.

```
visible relationship ≠ usable information      (the XOR lesson)
small information     ≠ harmless information     (the OR lesson)
```

## The separators (what NOT to claim)

These are the load-bearing output of the project. Most security work fails by silently upgrading `tested` to
`safe`; this repo fences the upgrade off in code and in prose:

```
measured            ≠ guaranteed
tested              ≠ safe
simulation          ≠ physics
bounded observer    ≠ all observers
zero MI on trace    ≠ zero MI on hardware
identifiability     ≠ truth
integrity           ≠ truth
```

## The one absolute, and everything else

There is exactly one class-independent guarantee in the stack (M21):

> If the secret is transmitted through **no** observable channel — `I(secret ; observable) = 0` for every
> observable — then no observer, of any capacity, can extract it.

Everything else — the generator, the machine, the convergence, the behaviour — is non-identifiable only
*relative to a stated observer class*, and dissolves against a richer one. Severing the secret from the
channel is the only thing the project can promise absolutely; the rest it can only **bound, measure, and
attribute to an adversary class.**

## What the next phase is

Not another invariant. A **measurement environment**: ingest real telemetry, preserve replayability, run
Channel Discovery continuously, let adversary classes compete, and log where identifiability emerges. Its
commits read *"found a leak," "killed a false positive," "changed the estimator"* — not *"added a defense."*
The estimator-as-hypothesis-class point above is the first thing that environment's design must take
seriously: a better detector is a stronger observer class, with its own coverage boundary, not an oracle.

## The final question

The project's last question is no longer:

> How do we hide the world?

It is:

> What world does the observer actually receive — and which observer is asking?

The durable result is not "we built a perfect anti-wallhack system." It is: **we built a framework for
discovering where our own assumptions fail, and for stating exactly where each claim stops.**
