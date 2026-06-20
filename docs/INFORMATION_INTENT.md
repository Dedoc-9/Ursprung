<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The Second Half — Information Intent and the Perception Compiler

*A research direction, not a built milestone. This is the world-side dual of the observer-side arc (M10–M21).
Everything here is design and grounding; nothing is implemented. The honest separators of
[`MEASUREMENT_DISCIPLINE.md`](MEASUREMENT_DISCIPLINE.md) apply to every claim below.*

## 1. The sandwich, and why the halves are duals

The arc Ursprung built is the **outward-facing** half:

```
WORLD → CORE → simulation → representation → execution → observable traces → observer inference
                                  "What does the system reveal, intentionally or accidentally?"
```

It is **defensive**. Its instrument measures leakage `L = I(S ; O)` — the mutual information between hidden
state `S` and the observable `O` (across channels, and recursively across estimator classes). Its one absolute:
*sever the secret from every channel.* Everything else is non-identifiable only relative to an observer class.

The missing half is the **inward-facing** one:

```
observer → questions / actions / probes → information requests → disclosure policy → representation → world
                                  "What SHOULD this observer receive — at what resolution, for what purpose?"
```

It is **generative**. And it is not a new pile of defenses; it is the *formal dual* of the first half. The
first half minimized one mutual information (`I(S;O)`, leakage). The second half adds the other one to keep
(`I(W_useful ; O)`, utility). The moment you write both, the whole project collapses onto a single, classical
optimization that already has a name (§2, §3):

```
        OBSERVER SIDE  (M10–M21, defensive)            "What can be inferred?"   minimize  I(S ; O)
                              ▲
                    [ INFORMATION BOUNDARY ]
                              ▼
        WORLD SIDE     (this document, generative)     "What should be inferable?" maximize  I(W_useful ; O)
```

A world can be perfectly private and perfectly useless (`hide everything`). It can be perfectly useful and
perfectly leaky (a traditional renderer / naïve telemetry). The interesting object lives on the frontier
between them — and that frontier is not new mathematics. It is the **privacy funnel** (§3).

## 2. The four disciplines that already occupy the second half

The second half is not unexplored. Four mature fields each own one face of it; the contribution is *composing*
them over a verified world, not inventing them.

### (a) Information intent + commitment — Bayesian persuasion / information design

Kamenica & Gentzkow's *Bayesian persuasion* is exactly "what should this observer receive." A **sender**
commits, publicly and in advance, to a **signaling scheme** — a map from world state to the distribution of
messages the receiver sees — chosen to govern the receiver's *beliefs and actions*. The commitment is the
whole trick: the sender does not lie (the messages are truthful given the scheme), but it chooses *how much
structure of the world to expose*.

> Map to Ursprung: a **disclosure policy** `π : world_state → per-observer observable` is a signaling scheme.
> And commitment is something this project already knows how to do honestly: `π` is a **declared, deterministic,
> content-addressed convention** (`conventions.py` discipline) — carrying its rejected alternatives and
> `not_a_truth_claim = True`. *The renderer is a committed sender.* `image ≠ generator` (M15) is the statement
> that the scheme may reveal messages but not the scheme itself; Bayesian persuasion is the generative theory of
> choosing that scheme on purpose rather than by accident.

### (b) The observer's genuine need — POMDP active perception / belief-space planning

A player or agent is not only an adversary; it is a **participant under partial observability** that must act.
Active-perception / belief-space planning formalizes this: an agent holds a *belief* over world state and
selects actions (including *sensing* actions) by **expected information gain** toward a task. The relevant
quantity is not raw bits but **value of information** — bits that change the optimal action.

> Map to Ursprung: "hide everything" is wrong because the receiver must reach a belief good enough for
> *competent participation*. The disclosure target is therefore **decision-relevant** information: the
> observer's belief `b(O)` must support a near-optimal action `a*`. This is the inverse of M20's adversary —
> the *same* belief-space machinery, pointed at the player's legitimate need instead of the cheat's illegitimate
> one. The active-perception literature is, almost verbatim, the M18–M20 harness with a cooperative reward.

### (c) The unified objective — information bottleneck / privacy funnel / rate-distortion

The privacy-utility tradeoff is solved (as a frontier) by the **privacy funnel**, the dual of Tishby's
**information bottleneck**: release `O` to *maximize* `I(Y ; O)` (utility about useful variable `Y`) while
*minimizing* `I(S ; O)` (leakage about sensitive `S`). With log-loss, both faces reduce to mutual information,
and the optimum is found with rate-distortion / convex methods.

> Map to Ursprung: this *is* the missing currency the second half needs. The first half had many debts
> (ambiguity, transition, convergence, reconstruction) but no **utility** term — and a world can be perfectly
> private and unusable. The privacy funnel supplies it. The unified objective (§3) is a privacy funnel over a
> committed world, with the renderer as transport and the M10–M21 instrument as the leakage meter.

### (d) The narrowest deployed instance — foveated / perceptual rendering

Foveated rendering already does a tiny, shipping version of the whole second half: it allocates fidelity by
**perceptual need**, rendering the fovea sharply and the periphery coarsely, achieving *perceptually lossless*
output at 50–70% less cost. It answers "what should this observer receive?" — for the special case of one
cooperative observer (the human eye), zero adversary (`L = 0`), and one channel (pixels).

> Map to Ursprung: foveated rendering is the **degenerate corner** of the unified objective — single observer,
> no leakage term, one backend. Generalize all three: many observers (some adversarial → `L > 0`), many
> channels (audio, UI, netcode, AI behaviour), and a *participation* sufficiency criterion instead of a
> *perceptual* one, and you have the second half. The fidelity engine is this corner; the second half is the
> whole room.

## 3. The unified objective (both halves, one equation)

Let `W` be the committed world (the Weltlinie), `S ⊆ W` the parts an observer must not infer, `Y ⊆ W` the
parts it needs for competent participation, and `π` a committed disclosure policy producing observable `O = π(W,
observer, purpose)`. The two halves fuse into one constrained optimization — a privacy funnel with a budget:

```
choose disclosure policy π to

    maximize    ParticipationUtility(π)  −  λ · Leakage(π)

    subject to  Leakage(π)  =  I(S ; O)            ≤  leakage_budget       (the first half: the meter)
                Utility(π)   =  VoI_observer(Y ; O) ≥  participation_floor  (the second half: the need)
                Cost(π)      =  Σ_channels fidelity  ≤  compute_budget      (M5/M16 transition + execution)
```

- `Leakage` is exactly what `channel_discovery.py` measures — and, per the recursive mirror, it is measured
  *by an estimator class with its own coverage boundary*, so `leakage_budget` is always "under observer class
  A." (`secure-against-class ≠ secure`.)
- `ParticipationUtility` is **value of information** in the observer's POMDP — bits that change its optimal
  action, not raw bits. This is the currency the first half lacked: *comprehension value*.
- `Cost` is the existing three-currency fidelity budget (fidelity + transition + execution-surface leakage),
  so the *first* arc (rendering economics, M1–M9) and the side-channel arc (M10–M21) are both already inside
  this objective as the `Cost` and `Leakage` terms.

This single line subsumes the whole project: rendering economics is the `Cost` term, the information firewall
is the `Leakage` term, and information intent is the `Utility` term plus the choice of `π`. Foveated rendering
is the special case `λ = 0`, one observer, one channel.

```
   Utility ↑
          ╲
           ╲___ the frontier (the only interesting policies live here)
           ╱
          ╱
   Leakage ↓
```

## 4. The next-gen fidelity engine is a *Perception Compiler* (pixels are one backend)

The user's framing — *the fidelity engine as a narrow aspect of all final uses* — is the load-bearing one.
The next-generation object is **not** "more photorealism." It is a **Perception Compiler**: a stage that lowers

```
( committed world W,  observer purpose/role P,  committed disclosure policy π,  budgets )
        │
        ▼   solve the §3 objective for this observer
   minimal-sufficient PERCEPT  (a target belief to induce, with a leakage ceiling)
        │
        ▼   lower onto a backend
   one of:  raster · 3D Gaussian splatting · neural radiance field · neural world model   (pixels)
            spatial audio · haptics                                                         (other senses)
            agent observation vector                                                        (AI / RL / robotics)
            scientific / telemetry visualization · accessibility transform · training sim   (non-game uses)
```

Rendering pixels is **one lowering target**. The same committed world + disclosure policy lowers to:

- **Games / VR** — foveated radiance fields, Gaussian splatting; the deployed corner (§2d). *Today's frontier:
  3DGS hitting hundreds of FPS, hybrid Gaussian-mesh, diffusion-inpainted occlusions.*
- **Multiplayer netcode** — the disclosure policy *is* the anti-cheat surface; reconciliation/convergence (M17)
  is its temporal lowering. "What this client should receive" is literally `π`.
- **AI agents / RL / robotics** — the "observer" is a policy network; `O` is its observation vector; active
  perception (§2b) is native here. A Perception Compiler that bounds leakage is *privacy-preserving observation
  design* for learned agents — the same engine, no pixels at all.
- **Neural world models** (Genie-3-class real-time generative worlds) — here the renderer *is* a learned
  generator, which makes `image ≠ generator` (M15) urgent: the model must expose a world without exposing the
  weights/rules that produce it. The Perception Compiler is the governor that sits in front of the world model.
- **Scientific viz, accessibility, training simulators** — "minimum information for competent participation" at
  a chosen resolution and for a chosen purpose, with sensitive fields severed. No game at all.

The thesis: **fidelity (photoreal pixels) is one backend of a perception compiler whose real job is
intent-governed disclosure.** A high-fidelity frame and a privacy-preserving agent observation and an
accessible audio description are the *same* §3 solution lowered to different substrates.

## 5. Why this preserves the discipline (the two halves close the loop)

This is not a new philosophy bolted on. It reuses every invariant:

- **Commitment = convention.** `π` is declared, deterministic, content-addressed, carries rejected alternatives,
  `not_a_truth_claim = True`. A disclosure policy is a Boundary-Ledger entry, not a truth claim.
- **The first half verifies the second.** The generative engine *proposes* a disclosure; the M10–M21 instrument
  (channel discovery + MI + adversary classes) *measures* whether realized leakage stayed within `π`'s budget,
  under a stated observer class. The defensive half becomes the **verifier** of the generative half — so the
  engine can never silently disclose more than it committed to. (`observation → allocation` ALLOWED;
  `observation → truth` FORBIDDEN; now also: `intent → disclosure` ALLOWED, `disclosure > committed policy`
  FORBIDDEN.)
- **The separators still bind.** `ParticipationUtility` and `Leakage` are *measured under an estimator class*;
  the engine reports what it can and cannot see (`MEASUREMENT_DISCIPLINE.md`). It never declares an experience
  "safe and sufficient," only "sufficient for purpose P and below leakage budget under observer class A."
- **The receiver has an intent class — the mirror of M21.** M21 found that a *detector* has a hypothesis class,
  and a channel reads differently across classes. Symmetrically, a *receiver* has an **intent class** — novice
  player, expert, spectator, teammate, AI agent, accessibility tool, cheat developer — and **useful to one is
  not safe for another.** So the compiler cannot optimize against a single observer: it optimizes disclosure for
  the *intended* classes and the firewall verifies against the *unintended* ones.
  `trust = optimize disclosure for intended observers  ∧  verify against unintended observers.` (M21's
  detector-hypothesis-class and this receiver-intent-class are the two faces of the same object.)
- **CORE is still sealed.** The Perception Compiler is VIEW/ALLOCATOR/OBSERVER. It governs *what is shown*; it
  never moves the Weltlinie. `integrity ≠ truth` is untouched.

## 6. Rejected / alternative framings (preserved forks)

- **Pure privacy ("hide everything").** Rejected: yields an unusable world; `Utility → 0`. The funnel exists
  precisely because this corner is degenerate.
- **Pure utility ("show everything, defend after").** Rejected: this is the traditional renderer + bolt-on
  anti-cheat the whole project argued against; `Leakage` unbounded, defenses always reactive.
- **Deception (emit false world facts).** Rejected on the CORE invariant — *CORE cannot lie*. The second half is
  about *what to disclose*, never *disclosing falsehood*. (Decoys that assert no world fact, `representation_
  privacy.decoy_admissible`, are the admissible boundary.)
- **A single scalar "quality" score.** Rejected for the same reason privacy was not a scalar (M21): utility is a
  vector over purposes/observers, and leakage is a vector over channels and estimator classes.

**A caution that outranks the rejected framings.** The privacy-funnel / information-bottleneck language is a
*lens*, not the hard part. Minimizing `I(S ; O)` is mechanical *once the variables are fixed*; the difficult,
recursive question is **choosing the right variables to measure usefulness and leakage in the first place.**
The detector was an observer with a blind spot (M21); the **perception compiler is also an observer** — its
choice of utility and leakage variables *is* its hypothesis class, with its own coverage boundary. So the
compiler, too, must report what it cannot see. The recursion does not bottom out — "have I chosen the right
variables?" is the permanent condition of the system, not a step to be completed. This is why the build order
in §7 is *instruments and substrates*, never a closed-form "optimal disclosure."

## 7. What to build first (empirical, not another law)

The seams are already pre-wired. Concrete, falsifiable first experiments — each an *instrument or substrate*,
never a new invariant:

1. **A `DisclosurePolicy` object** — the committed signaling scheme `π`, as a content-addressed convention with
   per-observer scope, resolution, purpose, and a leakage ceiling. (The generative dual of
   `capability.py`/`causal_access.py`.) **— STARTED:** the embarrassingly-small first brick exists as
   `ursprung/disclosure.py` (`DisclosurePolicy` + a toy compiler + the M10–M21 firewall as auditor: *policy
   says reveal X; did the output contain only X?*). Still toy; the compiler is a lookup, not yet a funnel solve.
2. **A `participation_utility` term** — value-of-information for a toy observer (measured task success), so the
   §3 objective is benchable with a negative control. **— DONE:** `ursprung/perception/utility.py`.
3. **The privacy-funnel bench** — show the (utility, leakage) frontier over a constructed world. **— DONE:**
   `ursprung/perception/` is the first one — `world → DisclosurePolicy → compiled observation → agent → task →
   leakage`, with the result that only the *compiled* policy preserves full task success (U=1.0) under the
   leakage budget while `raw` over-discloses (L=6 bits) and `blind` under-serves (U=0.56). Honest bound:
   constructed; expires on real workloads.
4. **Lower one non-pixel backend** — an *agent observation vector* (a dict, no rendering). **— DONE in toy
   form:** the compiled observation in `perception/observation_compiler.py` is exactly a non-pixel observer
   view; the "narrow aspect" is now literal.
5. **Verify with the first half** — leakage is measured by `channel_discovery`'s QIF estimator inside the loop;
   the `MeasurementResult` carries its observer-class coverage boundary (`compliant ≠ safe`). **— DONE.**

6. **Adversarial benchmark — leakage ≠ exploitability. — DONE, and it FALSIFIED the static metric (the valuable
   outcome).** `ursprung/perception/adversary.py` points a *learning* observer at the compiled disclosure: a
   persistent secret, a mobile observer, one policy-compliant `threat` bit per frame. A per-frame leakage
   estimate of **0.79 bits** (and a single frame recovers only **0.39 bits**, 49 candidates) is broken by an
   **accumulating multilateration learner that recovers the EXACT secret (6 bits)** across the session. This
   does not contradict the per-observation MI bound (the single frame stays within it — the data-processing
   inequality holds); it shows the per-frame leakage budget is the **wrong budget for a session**. Exactly the
   M13 (accumulation) / M19 (temporal) / M21 (richer observer class) lesson, biting the perception loop.

7. **Session Leakage Accounting — DONE; the first GENERAL result.** `ursprung/perception/session_accounting.py`
   answers the falsification: account leakage over the *session*, not the frame. A `SessionLeakageBudget` caps
   accumulated bits; the `AccumulationAwareCompiler` selects channels by committed worst-case *session* leakage,
   keeping the stable task band and dropping the per-frame channel that triangulates. Re-running the *exact*
   `adversary.py` learner: the naive session policy still recovers the exact secret (6 bits, busts the 2-bit
   budget); **accumulation-aware keeps utility at 1.0 while exploitability collapses to 0.83 bits — the exact
   cell is never recovered**, for every secret; blind under-serves. That is **purpose-preserving disclosure
   under an accumulating observer** — the first result general across games, agents, dashboards, and robotics.
   Honest bound: holds against the *modeled* observer class and only because the task channel is *separable*
   from the leak channel; a richer class or a non-separable task changes it (`secure-against-class ≠ secure`).

8. **The non-separable frontier — DONE; the free lunch removed.** `ursprung/perception/frontier.py` tests the
   hidden assumption session accounting rested on (*task information and secret are separable*) by violating it:
   an **exact-interception** task where utility *is* the secret. Disclosing `k` of 6 bits → `2^(6−k)` candidates
   → centroid aim → exact-hit utility. The result is a genuine **privacy–utility frontier**: utility ≈
   `2^(leakage−6)`, **doubling per disclosed bit** (0.016 → 0.031 → … → 1.00), and **full utility strictly
   requires full leakage**. The separable session win (U=1.0 at <1 bit) was a *special case*, not the rule. When
   the task needs the secret, the framework's job is not to *eliminate* the tradeoff but to **measure** it — to
   publish *the cost of knowledge* so the policy author's choice (more utility / less leakage) is explicit and
   contestable. *That* visibility is the contribution, not a free lunch.

9. **The Perception Fidelity Condition — DONE; the unifying test.** `ursprung/perception/fidelity.py` folds the
   frontier, the threshold, and inverse-leakage into one Dini-style *sufficient* condition: a representation is
   **task-faithful** (`utility ≥ U_min`) AND **inference-bounded** (`session recovery < τ` — the cascade-aware,
   accumulated quantity, *not* per-frame). It HOLDS for the separable task (utility 1.0, recovery 0.83, ~5 bits
   of residual uncertainty preserved) and is provably **infeasible** for the non-separable one (the only level
   meeting `U_min` busts `τ`). The reconstruction bound is best read as an *upper Dini derivate* of accumulated
   recovery (worst-case cascade slope); the regime split (faithful-bounded / irreducible / cascade-collapse)
   echoes **Denjoy–Saks–Young**'s almost-everywhere classification — a "DSY for perception" is the honest,
   theorem-shaped target, not proved here. Sufficient, not necessary; under the modeled observer class.

10. **Leakage(C) — DONE; the capacity axis made explicit.** `ursprung/perception/observer_capacity.py` turns
    M21's class-relativity into a *curve*: against one FIXED representation, recovery rises monotonically with
    observer capacity (memory horizon W) — 0.39 bits at W=1 (memoryless) up to the full 6 bits once the observer
    can accumulate the session. The same disclosure leaks differently to different observers, so leakage is
    `Leakage(C)`, never a scalar — the VC-dimension bridge as a measurable curve. It only **defines the axis**;
    scaling `C` to a real model on a non-toy world is the genuine frontier (a different *kind* of build), not
    attempted here.

The remaining honest gaps (so this is not over-read): the compiler is still a *lookup / greedy channel select*,
not a continuous funnel *solve*; the world, the learner, and the leakage estimator are constructed; the utility
models are declared conventions; the capacity axis is a memory-horizon *proxy*, not real model capacity. The "participation *rarely* needs full knowledge" claim is now a *per-task
empirical question* (separable → free lunch; non-separable → an irreducible measured frontier), not a settled
thesis. The next increments are empirical — a real learner class, a real trace — not another conceptual layer.

## 8. The one-line shift

```
First half  (built):   "What does the system accidentally SAY?"        — leakage, measured.
Second half (this):    "What should it MEAN to say?"                    — intent, committed.
Together:              a TRUSTWORTHY INTERACTIVE SYSTEM —
                       (what reality emits) + (what observers should receive) = controlled experience.
```

The renderer was always a special case. Its real category is a **committed, intent-governed, leakage-bounded
perception compiler** over a verified world — of which a beautiful frame is one lowering, an agent's
observation another, an accessible description a third. The fidelity engine is the narrowest, most visible
aspect of a much larger object: the deliberate composition of perception under a budget, against observers
whose model classes we can only ever bound.

## 9. Prior art — where this sits, and the category question

This is **composition, not invention.** Naming a category is itself a claim, and the discipline forbids
overclaiming, so the honest statement is that Ursprung sits at the intersection of three established fields,
applied over a *verified, deterministic interactive world*:

- **Information Flow Control — the tightest home for the M10–M21 half.** The "sever the secret from every
  channel" absolute *is* **noninterference** (hidden state must not affect observable output; Goguen–Meseguer).
  But the quantitative, observer-relative treatment here is the subfield **Quantitative Information Flow (QIF)**
  — leakage measured in bits (mutual information / min-entropy), which is exactly `channel_discovery.py`, and
  the AIC lattice (`adversary_capacity.py`) is QIF made *relative to an observer's model class*. And
  `DisclosurePolicy` is precisely **declassification** — committed, controlled release. (Accurate phrase:
  *noninterference + declassification + quantitative information flow.*)
- **Privacy engineering — the second half's objective.** The privacy-utility tradeoff / privacy funnel (§2c),
  with **differential privacy** as the adjacent rigorous budget mechanism.
- **Information design / Bayesian persuasion — the under-named join.** Choosing the *minimum representation
  sufficient for an observer's purpose without enabling unintended inference* is information design lifted to
  interactive systems (§2a). This is the part with no settled industry name.
- **Trustworthy-AI / agent-observation design — a real but looser adjacency.** The §4 agent-observation backend
  ("what an agent may observe vs infer") touches AI-safety eval framing; it is an analogy, not a home field,
  and is ranked last in tightness.

**The distinction that is actually novel** is the abstraction-boundary shift the whole project encodes:

```
access control / authorization asks:   "Is this observer ALLOWED to receive this?"
this category asks:                     "What is the MINIMUM representation that lets this observer achieve
                                         its purpose WITHOUT learning unintended state?"
```

The contribution is the *combination* — quantitative, observer-class-relative, side-channel-inclusive,
intent-driven, and with the defender admitting it is itself a bounded observer (the recursive caution of §6) —
not any one of the fields above. If a name is needed, **Intent-Aware Information Mediation (an Information
Mediation Layer / IML)** is a reasonable proposal, presented as *"composes IFC/QIF + privacy engineering +
information design,"* never as a freshly-invented discipline. (Analogy: an API gateway controls service
*access*; an IML controls meaningful *disclosure*.)

## 10. A Perception Operating System — the long-horizon vision (not built)

*This is the north star, not a roadmap and not a claim. It is recorded so the ambition is on the record,
bounded by the same separators as everything else: `vision ≠ built`, `simulation ≠ physics`, and the prize
below is real only with its boundary attached.*

Taken as one trajectory — Reality Engine (*what is true*) → Ursprung (*what this observer should perceive*) →
the LLM (the observer that finally forces the question) — the destination is not a game engine, a database, a
simulator, or an AI framework; those are special cases. It is a new computing layer that sits between reality
and every observer (human, agent, organization, robot, analyst) and computes:

> *What is the minimum representation this observer needs to achieve its purpose, while preventing unintended
> inference?*

```
Reality Engine → committed world state → DisclosurePolicy → Perception Compiler → observer-specific reality → human / agent / org
```

**The breakthrough is making truth and perception separate first-class objects.** Almost every system today
conflates them (`truth = what gets sent`); this architecture asserts `truth ≠ perception; perception is compiled
from truth`. An operating system is the apt analogy: an OS allocates memory, CPU, storage — this allocates
something deeper, **access to truth** (not truth itself — *access* to it). In an LLM-native world that may
become as fundamental as memory management was in the early computer era.

**Why the LLM forces it.** Before LLMs, observers were mostly human — noisy, slow, inconsistent. An LLM agent
remembers, probes, accumulates, builds latent models, and coordinates, so *every LLM is born an adaptive
adversary* (M20/M21) — not malicious, just epistemically aggressive. The question every API, dashboard, game,
robot feed, and workflow now inherits: **what can a learning observer infer after 10,000 interactions?** Most
systems have no answer. This is the load-bearing, fully-defensible part of the vision.

**The prize: computable epistemics** — a system that can answer, per interaction: *what is true? what did this
observer see? what could it infer? what remains unknowable? what leakage budget was consumed? what utility was
gained?* — for every observer at once.

**The boundary that keeps the prize honest** (the repo's `secure-against-class ≠ secure`): of those six, only
*"what remains unknowable"* is answerable **absolutely**, and only via the one absolute the project proved — the
secret severed from every channel. *"What could it infer / what escaped"* is answerable **quantitatively but
class-relatively** (QIF under a stated estimator). So the true capability is **bound-and-attribute**, never
**prove-omnisciently**. Still foundational — almost no system answers any of the six today — but the *true*
version carries its observer class with it.

**Where it would reshape things** (truth stays singular; perception becomes contextual): AI agents get a
purpose-compiled observation with a measured leakage bound instead of the whole database; multiplayer anti-cheat
becomes *information architecture* (compile observations that preserve play while minimizing inference) rather
than detect-and-ban; enterprise access shifts from "may Alice view row X?" to "what representation of row X is
sufficient for Alice's task?"; robots get actionable state (navigable corridor, obstacle confidence, goal
affordances) instead of raw sensor streams; one scientific simulation serves researchers, students,
policymakers, and agents different views of a single committed reality.

**Still composition, not invention.** The pieces exist and are fragmented — quantitative information flow,
information design, differential privacy, active perception, world models, multi-agent systems, access control.
The synthesis is: *treat observer-specific perception as a **compilable artifact over a committed world model**,
then **measure what can be inferred** from it.* That combination has no settled industry category;
"Perception Operating System" / "Computational Epistemics Infrastructure" / "Intent-Aware Information Mediation"
are candidate names.

**Three things that are unsolved, not merely unbuilt** (so this stays honest direction): (1) defining
*participation utility / value of information* for real tasks — the §6 variable-choice recursion; (2) solving the
privacy-funnel objective *at runtime, per observer, at scale* — minimal disclosure for thousands of simultaneous
agents is a hard systems/optimization problem; (3) the estimator-is-a-hypothesis-class recursion means "prove
what escaped" is forever class-relative. None is closed by another invariant; all three are empirical. The
smallest *true* cell of this vision is buildable now — one agent, one task, one `DisclosurePolicy`, a measured
leakage bound (§7 step 4) — and that cell, not the platform, is the honest next step.

## 11. Governance — the boundary the code cannot cross

*This is a boundary statement, not a solution. It belongs here because `Leakage(C)` is the point where the
architecture stops being a security primitive and becomes a socially-situated measurement system.*

The deepest issue is not controlling information; it is **controlling who can verify the control**. Once the
disclosure dial is computable, the load-bearing variable is not *who owns the model* but *who can check the
curve* — **verifiability, not ownership**.

**The epistemic asymmetry (why this is structural, not a flaw).** Auditing leakage requires a relationship to
the secret `S` itself: to confirm `I(S;O) ≤ τ` you need `S`, which the observer by definition lacks. So every
arrangement is a choice about how to allocate trust across a triangle —

```
              truth-holder (has S)
                    /   \
                   /     \
            verifier ───── observer
```

— and no design removes that triangle; it only decides who sits where. A purely *local, user-controlled*
observer model audits the *output* it can see, not the *withholding* it cannot; a purely *public/regulated*
auditor can check the curve but centralizes a different power and must be trusted with `S`. The defensible
direction is to regulate the **protocol of proof** rather than the ownership of the model: **verifiable
disclosure attestation** — prove a *behavioral* statement about a hidden world without revealing it
(`∀ C ∈ class X: recovery(S, O) < τ ∧ utility > U_min`), the zero-knowledge shape of the iO connection in §9.
That is a hard frontier: the verifier is not checking a checksum, it is checking a property of a system, over
an observer class, without `S`. It does not exist in usable form; naming it is the point.

**What the parts actually govern.** The compiler decides *what representation exists*; the `MeasurementResult`
decides *what claims may be made about it* — different powers. A dangerous system says "policy = X, therefore
safe." A disciplined one reports the observer class, horizon, task, and estimator it tested, the measured
utility and recovery, and the **coverage boundary** (unknown observers `> C`, unknown horizons `> t`). It does
not solve trust; it exposes the boundary. That refusal — never the word "safe" — is the accountability
primitive.

**The failure mode: a measurable dial can manufacture false legitimacy.** A number is not a justification.
`leakage_budget = 0.1 bits` may be a reasonable privacy floor, an impossible restriction, or a buried policy
choice — the measurement reports *what happened under a policy*, never *whether the policy was acceptable*.
Hence the separator that belongs beside the others: **`measurement ≠ legitimacy`** (alongside `simulation ≠
physics`, `secure-against-class ≠ secure`, `integrity ≠ truth`).

**The category this names.** The stack — Reality Engine → truth model → disclosure compiler → observer
experience → inference measurement → **attestation / audit** — ends not in *security* but in *accountability*.
The honest contribution:

> A representation system cannot remove the governance question. It can only transform hidden disclosure
> choices into explicit, measurable, contestable parameters. The remaining question — *who controls the policy,
> who can verify it, and who is empowered to challenge the result* — is political, and the code can inform it
> but must not pretend to settle it. Making the dial visible is the contribution; setting it is not the code's
> to do.

The next conceptual frontier after `Leakage(C)` is therefore the place the technical and governance problems
**become the same problem**: *verifiable claims about adaptive observers without revealing the protected state.*

---

## References (grounding; current as of June 2026)

- Kamenica & Gentzkow, *Bayesian Persuasion* (NBER w15540) — [pdf](https://www.nber.org/system/files/working_papers/w15540/w15540.pdf);
  *Bayesian Persuasion and Information Design*, Annual Review of Economics —
  [annualreviews](https://www.annualreviews.org/content/journals/10.1146/annurev-economics-080218-025739).
- Belief-space planning / active perception — *Decision-Making for Path Planning Under Uncertainty* (MDPI Robotics, 2025)
  [mdpi](https://www.mdpi.com/2218-6581/14/9/127); *Multi-Modal Active Perception for Information Gathering*
  [arXiv:1712.09716](https://arxiv.org/pdf/1712.09716).
- Privacy funnel / information bottleneck — *From the Information Bottleneck to the Privacy Funnel*
  [arXiv:1402.1774](https://arxiv.org/abs/1402.1774); *Optimal Privacy-Utility Trade-off under a Rate Constraint*
  [Imperial IPC-Lab](https://www.imperial.ac.uk/media/imperial-college/research-centres-and-groups/ipc-lab/PUT_isit2019.pdf).
- 3D Gaussian Splatting / neural rendering (state of the art) — *A Survey on 3D Gaussian Splatting*
  [arXiv:2401.03890](https://arxiv.org/pdf/2401.03890); *When Gaussian Meets Surfel* [arXiv:2504.17545](https://arxiv.org/pdf/2504.17545).
- Neural world models — *Genie 3* [Wikipedia](https://en.wikipedia.org/wiki/Genie_(AI_model));
  *A Hitchhiker's Guide to World Models* [arXiv:2510.20668](https://arxiv.org/pdf/2510.20668).
- Foveated / perceptual rendering — *Efficient VR rendering survey (foveated, stereo, cloud, low-power)*
  [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2096579625000580); *VR-Splatting*
  [arXiv:2410.17932](https://arxiv.org/pdf/2410.17932).
