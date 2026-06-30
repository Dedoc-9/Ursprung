<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The information-mediation runtime — closed-loop QIF-bounded representation (spec note)

**Status: design specification — SCOPED. The primitives are built and tested; the closed loop is specified, not
assembled.** This note frames what Ursprung's `ursprung/` + Rust core *already is* as a single product surface —
a QIF-bounded, provenance-grounded information-mediation runtime — and states honestly what is built, what is
framing, and what is open. It supersedes the separate `CONDUIT_PROVENANCE_SPEC.md` recommendation: provenance is
*one axis* of what this runtime measures, not a separate product. `claim ≠ code`; `composition, not invention`;
`integrity ≠ truth`.

> **Why this surface, and why its failure mode is benign.** If the channel-capacity estimate is wrong, the
> system leaks *slightly more than intended* — an inference **overshoot** that is measurable (the residual
> channel quantifies it), bounded, and recoverable (re-estimate, re-allocate, re-render). That is auditable, not
> catastrophic — unlike a broken DP mechanism (silent breach) or a kinetic safety gate (injury). Consequence
> matched to guarantee. **Caveat:** "the loop re-converges" is a *design* property today, not a measured one —
> see §2/§5.

---

## 1. Prior art (verified) — two distinct genealogies, and what is genuinely additive

The field splits into **two lineages that must not be conflated** — a qualitative one and a quantitative one —
and Ursprung uses both. Getting the order right matters: the quantitative result *presupposes* the qualitative
foundation, not the reverse.

**Genealogy A — qualitative / binary noninterference (the foundation).**
**Goguen & Meseguer, "Security Policies and Security Models," IEEE S&P 1982** established *noninterference*: for a
state machine with users/states/commands/outputs, a group G does not interfere with G′ iff what G′ observes is
independent of G's actions. Binary — interference occurs or it doesn't. Every lattice-based IFC type system
descends from this: **LIO** (Haskell), **Jif** (Java), **FlowCaml**. The question is *does S reach O?*

**Genealogy B — quantitative capacity (built *on top of* A).**
**Mestel, CSF 2019** takes Goguen–Meseguer's *transducer model* and proves the QIF **capacity dichotomy**: for
deterministic interactive systems, information flow grows **either logarithmically or linearly** with interaction
steps, the regime is **polynomial-time decidable**, and capacity = the antichain-growth "width" of a regular
language. **Alvim et al., *The Science of QIF*, 2020** give the operational meaning via **g-vulnerability / gain
functions** (the best adversary's expected gain). The question is *how many bits, how fast?* — and Mestel
**presupposes** Goguen–Meseguer; it is an extension, not a replacement. *(The earlier draft of this note treated
Mestel as foundational — a factual error, corrected here.)*

| Lineage / component | What exists (settled / built elsewhere) | What this runtime adds |
|---|---|---|
| **A — Noninterference (foundation)** | **Goguen–Meseguer 1982** — the binary condition for confidentiality. | The structural channel topology it defines, carried in Rust types (§3, static). |
| **A — IFC type systems** | LIO, Jif, FlowCaml — lattice labels, **binary** enforcement (`does S reach O?`). | The **quantitative** dimension (`how many bits?`) layered on the structural one. |
| **B — QIF theory for interactive systems** | **Mestel, CSF 2019** (log-or-linear dichotomy, poly-time decidable); **Alvim et al. 2020** (g-vulnerability). | QIF as a *control* input to representation, not post-hoc analysis. |
| **B — QIF analysis tools** | CHIEF (Chen–Malacaria), SAT/model-counting leakage quantifiers — **measure** leakage in existing code. | A **closed loop**: measure → compare to budget → adapt representation → re-measure (§2). |
| **Adaptive rendering** | Temporal/spatial adaptive rendering — optimizes **visual quality under compute** constraints. | Allocates fidelity by **information-leakage cost**, not compute cost (`R=U×C×P×S`; `Debt=A×P×C`). |
| **Provenance semirings** | GProM, Perm (Glavic) — semiring provenance via query rewriting on DBMSs. | Provenance grounded in a Rust type (`Grounded<T>`) as an affine lifecycle guarantee, treated as *one axis* of an information channel — not the whole story. |

**Honest novelty:** none of the *primitives* is new, and neither lineage is new. The contribution is the
**composition + the closed loop**: Genealogy-A structure (typed) + Genealogy-B capacity (measured) +
leakage-cost fidelity allocation + a provenance-grounded runtime, wired into *measure → allocate → render →
re-measure*. No deployed system closes that loop for representation. The repo says this of itself —
"composition, not invention" — and that framing survives the sieve.

---

## 2. The contribution: the closed loop (specified; components built, integration not)

```
        authoritative world state  (the thing that is true)
                     │
                     ▼
        ┌───────── fidelity allocation ─────────┐   allocate detail by FUTURE FAILURE COST
        │   R = U×C×P×S ; Debt = A×P×C            │   against a MEASURED leakage budget
        └───────────────────┬────────────────────┘
                            ▼
                 representation / render            (observable output O)
                            │
                            ▼
        ┌──────── residual_channel ──────────┐      measure I(S;O) leakage on this window
        │   CMI estimate vs within-Z null      │      (the QIF instrument)
        └───────────────────┬──────────────────┘
                            ▼
              measured leakage  ≤  budget ?
                     │yes              │no
                     ▼                 ▼
               emit / commit     tighten allocation, re-render  (fail-closed)
```

**Built and tested (88 Rust tests; Python benches):** `residual_channel` (confounder-conditioned CMI), the
coupling firewall, `Grounded<T>` (the action chokepoint), the fidelity-allocation laws, `channel_discovery` /
`perception/fidelity.py` (the privacy-funnel + Perception Fidelity Condition). **Not assembled:** an end-to-end
controller that drives a *live* renderer from the measured budget and re-measures. The renderer today is a
hashable **reference** rasterizer (not GPU pixels) and the harnesses are simulated. So the loop is a **design
with built parts**, not a running integrated system. `primitives-built ≠ loop-closed`.

---

## 3. The static / runtime boundary (the load-bearing honesty)

- **STATIC (type-level, Rust).** *Channel topology* — which secrets connect to which observers through which
  paths — is structural and expressible in types: `Grounded<T>` carries provenance lineage; a channel type
  encodes the secret→observable path; composition rules track which pipelines merge which channels. Token
  lifecycle is affine + `#[must_use]` (consumed once, never silently dropped). Whether the pipeline is a
  *deterministic transducer* (Mestel's precondition) and how it composes (sequential/parallel) is a structural
  property. `Grounded<T>` proves *provenance lineage*, not capacity.
- **RUNTIME (measured, not typed).** *Actual capacity* `I(S;O)` depends on the joint distribution of secrets and
  observations — runtime data. No type system computes mutual information; `residual_channel` **measures** it.
  *Per-observer g-vulnerability* depends on the adversary model and prior — runtime/contextual. The
  fidelity-allocation decision (LOD, what to reveal, disclosure timing) is a runtime control action.

The boundary in the repo's own grammar: **`Grounded<T>` proves the token's provenance lineage (static);
`residual_channel` measures the channel's leakage (runtime); the loop allocates fidelity to keep measured ≤
budgeted (runtime, fail-closed).** `static ≠ runtime`; `provenance ≠ capacity`; `structure ≠ measurement`.

**The split maps exactly onto the two genealogies (§1):** the *static* tier is **Genealogy A** — the
Goguen–Meseguer noninterference *structure*, the binary "does this channel exist / connect S→O?" that lattice
IFC expresses and that Rust types can carry. The *runtime* tier is **Genealogy B** — Mestel/Alvim *capacity*,
the "how many bits flow through an existing channel?" that no type system computes and `residual_channel` must
measure. Confusing the two is the category error the whole exercise guards against: *structure is typeable;
capacity is measurable.*

**A second, sharper limit on the theorem itself:** Mestel's dichotomy and its polynomial-time decidability hold
for an **idealized deterministic finite-state transducer**. A GPU renderer or a learned agent-policy — with
floating-point, nondeterminism, and unbounded state — is **not** that object. So Mestel supplies the
*architectural reasoning frame for the abstract channel*; the deployed pipeline's capacity must be **measured**,
never **derived** from the theorem. `model ≠ system`; `decidable-on-the-abstraction ≠ known-on-the-deployment`.

---

## 4. The open problem (stated as open): scaling the leakage estimate

`residual_channel` estimates conditional mutual information with a **discrete binner over a window**. That is
sound as an instrument but it is the bottleneck for a real product, on three measured axes (each `UNMEASURED`
until run):

- **Continuity / dimensionality.** Binned discrete CMI degrades on high-dimensional, continuous observation
  channels (real pixel/feature spaces). A continuous estimator (k-NN / kernel / neural MI) trades bias for
  variance and determinism — and any estimator is itself a hypothesis class (`I=0 under estimator E ≠ I=0`).
- **Throughput.** §6 of the gateway measured the CMI firewall at **~9.7 MB/s** (vs ~700 MB/s parse) — the audit
  is the latency driver. A per-frame closed loop at interactive rates is **not** demonstrated; the honest design
  is a *windowed periodic* leakage audit, not a per-pixel inline filter.
- **Adaptivity.** If the observer chooses the next query from the noisy answer to the last, the leakage
  accounting is the *adaptive composition* regime; an ε-counter analogue under-accounts. The repo's
  `session_accounting` is the start; the general adaptive case is open.
- **Loop convergence (unproven).** The closed loop *measure → allocate → render → re-measure* is asserted to
  "re-converge" below budget, but there is **no convergence proof and no measured convergence rate** — it could
  oscillate, overshoot, or fail to settle for some allocation policies. Treating the loop as a control system
  (stability, convergence rate, the analogue of the L2 contraction certificate applied to the *allocation
  dynamics themselves*) is open. `asserted-re-convergence ≠ proven-stable`.
- **Adversarial observers.** Capacity is defined against an observer/adversary class; a richer adversary than
  the modeled one (sequence vs marginal estimator, side-channel reader) sees more (`secure-against-this-observer
  ≠ secure`, the repo's own M21 result). Bounding leakage against an *adaptive, learning* adversary — not a fixed
  class — is open, and the honest output names the class on every number.

This is the genuine research/engineering frontier — and, crucially, its failure mode is **measurable** (estimate
error, throughput, a bias/variance curve), not silent mis-attribution.

---

## 5. Architecture & build path (compose; sharpen what exists)

```
┌──────────────────────────────────────────────┐
│  Observer-facing layer (Python) — renderer /   │
│  agent observation / viz; standard outputs     │
├──────────────────────────────────────────────┤
│  Fidelity allocator (Python) — R=U×C×P×S,      │
│  Debt=A×P×C; allocates detail by failure cost  │
│  against the measured leakage budget           │
├──────────────────────────────────────────────┤
│  Verification core (Rust, built) —             │
│   Grounded<T> (static provenance/chokepoint);  │
│   residual_channel (runtime CMI measurement);  │
│   coupling firewall; ursprung-gateway          │
├──────────────────────────────────────────────┤
│  Authoritative world model — the truth the     │
│  representation is a lens on (never mutated)    │
└──────────────────────────────────────────────┘
```

**Build path (honest order):**

1. **Close one loop on one toy world end-to-end** — the smallest real artifact: wire the allocator → reference
   renderer → `residual_channel` → budget check → re-allocate, on a single seeded scene. Demonstrate
   *measure→adapt→re-measure* runs and converges. This is what turns "framing" into "running." Grade
   `MEASURED` only after it runs.
2. **Replace the binned CMI estimator** with a continuous one behind the same interface, differential-tested for
   decision-parity against the binned reference (the established `decisions match, floats need not` pattern).
3. **Windowed cadence, not inline** — design the leakage audit as a periodic background pass (per §4 throughput),
   with the fast per-frame path doing only the O(1) structural checks.
4. **Name the adversary class on every result** — a leakage number is "found by estimator E, over trace D,
   against observer class A," never "safe."

---

## 6. Honest status ledger

| Component | Status |
|---|---|
| `residual_channel` (CMI instrument), `Grounded<T>`, coupling firewall, gateway | **IMPLEMENTED / MEASURED** (88 Rust tests) |
| Fidelity-allocation laws, perception benches (`channel_discovery`, `fidelity.py`) | **IMPLEMENTED** as separate benches |
| The closed *measure→allocate→render→re-measure* controller, end-to-end | **SCOPED / not assembled** (`primitives ≠ loop-closed`) |
| Capacity of the *deployed* pipeline derived from Mestel | **REJECTED** — Mestel decides the *abstraction*; the deployment is measured (`model ≠ system`) |
| Per-frame inline leakage filtering at interactive rates | **UNMEASURED / likely infeasible** — the audit is the latency driver (~9.7 MB/s); use windowed cadence |
| Continuous / adaptive leakage estimation at scale | **OPEN** — the genuine frontier (§4) |

**Defensible one-line:** *a provenance-grounded, QIF-bounded information-mediation runtime that allocates
representation fidelity by future-failure cost against a measured leakage budget — structural channel topology
typed statically (`Grounded<T>`), actual capacity measured at runtime (`residual_channel`), the control loop
fail-closed — of which a renderer is one backend. The primitives are built and tested; closing the loop
end-to-end and scaling the estimator are the build targets.*

**Second surface, held:** the verification kernel (`weltwerk/` + DVSM contraction-cert + proof-obligations
ledger) is the same discipline turned on world-model verification. More developed, but a more crowded field
(KeYmaera X, dReal, Coq dynamical-systems verification) and a more specialized customer — the natural deepening
*after* the mediation runtime has users who need verified world models, not the lead.

---

Sources: Goguen & Meseguer, "Security Policies and Security Models," **IEEE Symposium on Security and Privacy
1982** (noninterference — the qualitative foundation) — by name/venue ·
[Mestel, "Quantifying information flow in interactive systems," CSF 2019 (arXiv 1905.04332)](https://arxiv.org/abs/1905.04332) ·
[Mestel, CSF camera-ready (Oxford)](https://www.cs.ox.ac.uk/people/david.mestel/quantflow.pdf) ·
[Alvim, Chatzikokolakis, McIver, Morgan, Palamidessi & Smith, *The Science of Quantitative Information Flow*, Springer 2020](https://link.springer.com/book/10.1007/978-3-319-96131-6) ·
[Measuring Information Leakage Using Generalized Gain Functions (g-leakage, CSF 2012)](https://inria.hal.science/hal-00734044/en) ·
LIO / Jif / FlowCaml (lattice IFC); CHIEF (Chen–Malacaria, QIF for C) — by name ·
[GProM provenance middleware (TaPP 2014)](https://www.usenix.org/system/files/conference/tapp2014/tapp14_paper_arab.pdf).
