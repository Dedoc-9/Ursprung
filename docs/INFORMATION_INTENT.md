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

## 7. What to build first (empirical, not another law)

The seams are already pre-wired. Concrete, falsifiable first experiments — each an *instrument or substrate*,
never a new invariant:

1. **A `DisclosurePolicy` object** — the committed signaling scheme `π`, as a content-addressed convention with
   per-observer scope, resolution, purpose, and a leakage ceiling. (The generative dual of
   `capability.py`/`causal_access.py`.)
2. **A `participation_utility` term** — value-of-information for a toy POMDP observer (bits that change the
   optimal action), so the §3 objective is benchable with a negative control, like every prior milestone.
3. **The privacy-funnel bench** — solve `maximize U − λL s.t. cost` over a constructed world; show the frontier,
   and that foveated-style allocation is the `λ=0` corner. Honest bound: constructed; expires on real workloads.
4. **Lower one non-pixel backend** — an *agent observation vector* for an RL/active-perception observer, proving
   the engine produces a privacy-bounded observation with no rendering at all (the "narrow aspect" made literal).
5. **Verify with the first half** — run channel discovery over the realized disclosure to confirm leakage ≤ `π`'s
   budget, under a stated estimator class.

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
