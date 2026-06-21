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
measurement         ≠ legitimacy     (a measurable dial reports what happened under a policy,
                                       never whether the policy was acceptable — see INFORMATION_INTENT.md §11)
consistency         ≠ correctness    (a system can coherently pursue a bad objective)
prediction          ≠ understanding  (predicting behaviour is not knowing why)
privacy             ≠ unpredictability
opacity             ≠ privacy
adaptation          ≠ inconsistency
learning            ≠ drift
non-identifiability ≠ freedom        (behaviour with no stable generator is not thereby autonomous;
                                       it is equally consistent with brokenness, noise, or deception)
unpredictability    ≠ agency
noise               ≠ ignorance      (even noise has structure; 'become noise' relocates the secret to the
                                       stochastic character — I(N;behaviour) — it does not remove it)
signal privacy      ≠ generator privacy   (hiding the content is not hiding the machine; the physical residue
                                            R — power/timing/EM — leaks the generator: I(G;A)=0 ⊅ I(G;A,O,R)=0)
unobserved          ≠ unknown        (a determined generator with no available channel is unobservable, not
                                       absent — the limit is observability, not computation)
adaptation          ≠ transformation (changing the projection ≠ changing the generator; CORE can stay invariant)
response            ≠ learning
personalization     ≠ self-change
observer-relative   ≠ observer-controlled  (the observer selects which projection it receives; it never
                                             becomes the author of the underlying policy)
mechanism           ≠ correlation     (a recoverable pattern can be a confounder, constraint, residue, or
                                        temporary equilibrium — not the generator)
fitted rule         ≠ causal source   (the generator is what stays INVARIANT when observer, projection, and
                                        context all change; identifying it requires varying the confounder)
ghost               ≠ hidden truth    (a residual G = Z − Π(Z) may be a projection artifact — the observer's
                                        shadow — not a generator component; test invariance across Π + necessity)
stable              ≠ causal          (invariance across projections is necessary but NOT sufficient; a stable
                                        artifact is invariant yet unnecessary — attribution needs invariance ∧ necessity)
integrity           = reproducibility, not causal validity   (a hash binds same-state→same-hash; it cannot tell
                                        a generator component from a confounder — a replayable system can replay
                                        the wrong explanation)
causal-under-a-model ≠ causal-across-models   (necessity is model-relative: G_F(F_model_1) ≠ G_F(F_model_2);
                                        a component can be necessary under a restricted model and redundant under
                                        a richer one that fits the same data — the robust generator is what
                                        survives the whole admissible model class. "necessary to WHICH F?")
causal-across-chosen-𝓕 ≠ causal-across-all-possible-F   (the dangerous edge: ⋂ G_F(F) is only as good as the
                                        admissible class 𝓕 you chose. Too narrow → confounders survive; too broad →
                                        every mechanism becomes optional and the intersection collapses to ∅
                                        (demonstrated: admitting an over-rich autoregressive model erases the
                                        generator). There is no purely internal certificate — "why is THIS the
                                        right space of models?" is epistemology, not a pipeline layer. The
                                        separator needs its own separator.)
derived boundary    ≠ declared boundary   (𝓕 cannot be derived from within the system without regress; it is
                                        DECLARED as an Arbitrary-Boundary convention — see conventions.py
                                        `admissible_model_class` — with its rejected alternatives and scope,
                                        the project's FIRST law answering its LAST problem)
declared boundary   ≠ truth          (a declared 𝓕 is an accountability object: it answers "why did attribution
                                        stop here?", never "why is this the uniquely correct place to stop?")
auditable           ≠ derived; derived ≠ true   (the stopping rule can be recorded, reproducible, content-
                                        addressed, contestable — and still not the uniquely correct explanatory
                                        boundary; a declared 𝓕 ALLOCATES investigation, it does not VALIDATE
                                        ontology. The framework makes the floor visible; it cannot remove the
                                        need for one.)
proven              ≠ surviving       ("the evidence proves X" is floor-hiding; "given observer class A,
                                        projection Π, model class 𝓕, evidence E, X is the best SURVIVING
                                        explanation" is floor-exposing — a different epistemic type. Confidence
                                        is conditional on the declared floor, not a scalar of the evidence:
                                        same E under a different declared 𝓕 yields a different conclusion. Made
                                        a runtime object in perception/grounded_claim.py — a conclusion that
                                        cannot be stated without declaring its floor and never asserts truth.)
integrity (epistemic) ≠ adequacy (ontological)   (two SEPARATE ledgers, not one "confidence": integrity =
                                        reproducible + fully-declared floor (how we arrived); adequacy =
                                        predicts + survives intervention + robust (does it match the world).
                                        They come apart — a buggy calculator is integrity 1.0 / adequacy 0.0;
                                        a single scalar launders reproducible-but-wrong into trustworthy.
                                        perception/ledgers.py. Confidence is a COORDINATE with no total order —
                                        ranking needs a declared goal.)
integrity           ≠ immunity       (a perfectly reproducible result whose adequacy is falling is ENTERING
                                        CRISIS — reproducibility does not shield against being overtaken; crisis
                                        is declining adequacy regardless of integrity. position ≠ ranking;
                                        integrity-gain ≠ progress — the destination quadrant decides, not the
                                        direction of integrity. perception/trajectory.py.)
observation         ≠ intervention   (THE pioneering result, architecture-independent: when a backdoor path is
                                        unobserved or the observation map is non-invertible, the causal question
                                        is NOT IDENTIFIABLE from observation alone — observationally
                                        underdetermined relative to the available variables/observation map (NOT
                                        "physically undecidable"; the limit is the data, not physics). No
                                        reconstruction, recoverability, correlation, or model-fit crosses it;
                                        only an active causal operation, do(·), can. Demonstrated in
                                        experiments/latent_phase1: a confounder that reconstructs, is recoverable
                                        across all encoders, is gauge-invariant, and correlates with the outcome
                                        at ≈0.6 still FAILS the gate because do(c) does not move the outcome.
                                        When the causal graph is UNKNOWN, the crossing needs a real intervention
                                        mechanism, not a ground-truth oracle — the open frontier.)
survives intervention ≠ (root) generator   (passing the intervention gate means causally-relevant ∧ robust ∧
                                        gauge-invariant — a "generator CANDIDATE", not the deepest cause. A
                                        mediator on g→x→y survives the outcome-intervention test too; telling
                                        root from mediator needs the intervention TOPOLOGY (do(g) moves x; do(x)
                                        does not move g), which a single outcome test does not capture. And the
                                        verdict is a GATE (pass/fail), never a confidence scalar — any composite
                                        is explicitly secondary, or the one-dimensional confidence object returns.)
causal relevance   ≠ causal position   (Phase 2's separation, the crisp form: "does changing this factor
                                        change the outcome?" (relevance) is a different question from "where
                                        does it sit in the graph?" (position). A root and a mediator are both
                                        relevant; only position distinguishes them. The intervention gate
                                        answers relevance; topology answers position.)
accuracy           ≠ identifiability   (Phase 6, the inference contract: accuracy answers "does this fit the
                                        regime I have?"; identifiability answers "what alternative worlds did I
                                        rule out?" — different axes. A model can be 99% accurate and weakly
                                        identified (the 99% holds only inside a narrow assumption set). So the
                                        estimator's atomic output binds the edge to the PRICE it paid to
                                        identify it (a structured IdentificationCost ledger — interventions /
                                        assumptions / domain_restrictions / unverified_dependencies, NEVER a
                                        scalar); cost is mandatory, accuracy optional+secondary and not part of
                                        identity. same edge + different price = different object;
                                        prediction ≠ inference identity. latent_phase6 — the contract; verifying
                                        the price was paid in valid coin is the estimator frontier.)
declared cost      ≠ verified cost   (the Phase-3↔Phase-6 calibration: a CausalEdge can require an assumption
                                        be DECLARED but cannot prove it is true; an EstimatorOutput can require
                                        an identification ledger but cannot prove the intervention/assumption
                                        trade was legitimate. The system records the epistemic receipt; it does
                                        NOT validate the currency. This is exactly what keeps the discipline
                                        layer from quietly becoming a theorem prover — declaration is a contract,
                                        not a proof. Verifying the coin is the estimator frontier, kept separate.)
latent coordinate ≠ the claim   (Phase 5, "representation is free, epistemic status is conserved": a learned
                                        representation's identity is NOT its latent vector but its
                                        provenance-qualified claim (the Phase-3 graph_digest). Two encoders with
                                        different latent coordinates but the same claim are EQUIVALENT
                                        (representation humility); one that cannot support the claims is not. The
                                        latent is the coordinate system through which a provenance-bearing claim
                                        is expressed, not the discovery. Standardizing the encoder input CLOSES
                                        an unintended scale gauge, so magnitude cannot manufacture coherence.
                                        latent_phase5.)
created coherence  ≠ discovered coherence   (the re-anthropomorphism / "provenance collapse" failure: a
                                        designer imposes a constraint, the system adapts coherently, and the
                                        AUTHORED coherence is re-read as DISCOVERED structure — the mirror
                                        mistaken for an observer. "behavior under declared constraints" ≠
                                        "invariant structure across constraints"; what survives a change of
                                        encoder/environment/intervention is discovered, what does not was
                                        authored. Demonstrated in latent_phase4: the confounder reconstructs and
                                        correlates with the outcome BECAUSE it was written that way, yet do(c)=0
                                        so its edge can only be assumption_load_bearing — the system cannot
                                        mistake what the developer imposed for what it found. identity includes
                                        provenance keeps the creator from disappearing into the creation.)
recovered topology  ≠ discovered ontology   (Phase 2: the intervention asymmetries recover a partial order
                                        (root/mediator/sink/isolated) that separates root from mediator — but
                                        even a perfectly recovered graph is a graph over LATENT FACTORS created
                                        by a declared representation family 𝓕, assuming a real do(). It is a
                                        surviving explanation under 𝓕, not a final description of reality;
                                        relabel the factors and you relabel the graph. experiments/latent_phase2.)
```

## The four questions (the spine the whole arc separates)

The project reads, end to end, as the progressive separation of four questions that are usually collapsed into
one word ("confidence"). Each is a different object, answered by a different layer, and a high score on one says
nothing about the others:

```
question                                         object        a system can fail it while passing the rest
─────────────────────────────────────────────── ───────────── ───────────────────────────────────────────
Can we replay the account?                       integrity     a deterministic replay can still be wrong
Does it correspond to the world?                 adequacy      a good predictor can still be a confounder
What caused it?                                  attribution   a causal fit can fail across model classes
What assumptions made the explanation possible?  floor         a robust explanation still rests on a 𝓕
```

A deterministic replay can fail adequacy; a good predictor can fail attribution; a causal explanation can fail
model robustness; a robust explanation can still depend on a declared floor. The common thread across every
layer is one move: refusing to let `chosen` be silently rewritten as `derived` and then mistaken for truth.

## The meta-invariant — identity includes provenance

Beneath every separator on this page is one mechanism, and it is the generator of all of them: **an object is
not fully specified until the thing that licenses it is attached to it.** The separations are its special cases.

```
claim       + floor            → claim identity      (grounded_claim.floor_digest)
coordinate  + ledger           → confidence identity (ledgers: integrity ⟂ adequacy)
graph edge  + support          → edge identity       (provenance: intervention-grounded vs assumption-backed)
graph       + edge provenance  → graph identity       (provenance.graph_digest)
```

So the project's question is not the usual one. Most systems ask *"what is true?"*; this one asks **"under what
declared conditions does this object continue to exist?"** — and the robust object is always an intersection
over the admissibility set: `robust claim = ⋂ over 𝓕`, `robust edge = ⋂ over 𝓐`. The center of gravity is
**epistemic provenance**, not epistemology: not eliminating assumptions, but refusing to let them detach from
the objects they license. This is the lens that generated the list above (it does not replace the individual
facts — `observation ≠ intervention` still stands on its own; this is *why* such facts kept appearing). The
contract is enforced as a type, not a convention: a `CausalEdge` recovered under an assumption cannot be
constructed without declaring it, so any estimator — present or future — emits `edge + provenance +
admissibility boundary` or it emits nothing. `identity includes provenance`.

## The floor (where the regress terminates)

Every attribution system has a floor; the floor is **assumed, not derived**; the assumption is **declared**; the
declaration is **auditable**. The regress (justify 𝓕 → derive 𝓕 → justify the derivation → …) does not vanish —
it **terminates at a declared boundary rather than being mistaken for a derivation.** This is the project's
opening move (the Arbitrary-Boundary Law: *arbitrary boundaries require deterministic handling, not claims of
truth*) applied to its deepest object — the admissible explanation space `𝓕` is registered in the Boundary
Ledger (`conventions.admissible_model_class`) exactly like pixel coverage or tick rate: explicit, deterministic,
content-addressed, carrying its rejected alternatives, `truth_claim = False`. The successor object is therefore
not a generator-finder but **an attribution system with an explicit, inspectable uncertainty boundary around its
admissible explanation space** — its one structural advantage over a floor that is merely lived-in (a grammar, a
culture, an axiom set) is that it can say *here is the model class, the observer class, the projection, the
evidence, and here is where we chose to stop.*

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
