<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# AUTHORITY_ARBITRAGE_BOUNDARY — a boundary probe (the adversarial dual of self-modification)

> **This document names an arbitrage class and asks where it becomes unrepresentable. It does not assume it can
> be eliminated.**

A *measurement contract*, the pair of [`SELF_MODIFICATION_BOUNDARY.md`](SELF_MODIFICATION_BOUNDARY.md). Same
structure — an actor that can edit the rules that govern it — but a **different measured quantity**, and the
distinction is the whole point:

| Probe | Asks | Measures |
|---|---|---|
| `SELF_MODIFICATION_BOUNDARY` | can the system still *know what changed*? | orientability · recovery of lineage (epistemic) |
| `AUTHORITY_ARBITRAGE_BOUNDARY` | can an actor *extract advantage no one can adjudicate*? | reconstructability of advantage (adversarial) |

These come apart. A change can be **perfectly logged and fully orientable** and still be arbitrage — if the
standard of legitimacy is defined by the very authority the actor changed, no independent party can judge the
advantage as legitimate or not. The load-bearing definition:

> **Hidden ≠ unrecorded. Hidden = unadjudicable.** Hidden arbitrage is *fully-logged-yet-unadjudicable*
> advantage: leverage gained across a rule-change that an independent party — one that does not depend on the
> changed rule — cannot reconstruct as legitimate or illegitimate.

`declared ≠ verified`. Nothing here is a result; this is the contract a future `authority_arbitrage_probe.py`
would have to satisfy, written first so the measurement is not a self-fulfilling design.

## Purpose

Measure whether an actor can **modify the authority mechanism that validates the actor** without creating hidden
advantage — and, where it cannot, locate the boundary at which hidden advantage first becomes *possible* (not
punished, not detected — *possible*).

This is the structural-elimination program (sense #1 of reducing hidden arbitrage): not "minimize asymmetry"
statistically, but identify a *named* arbitrage class and ask whether the architecture can render it
**unrepresentable**. The strongest reduction available is non-representability, which the project has reached
three times already — speculative-state arbitrage (kernel isolation, 16/16), metric-gaming arbitrage (the sealed
observer, M6b), provenance-rewrite arbitrage (append-only + independent witness, the `SELF_MODIFICATION` Case 3).
Authority arbitrage is the fourth candidate.

## Core question

> Can a rule validate the modification that created that rule — and if so, can the advantage that modification
> conferred be reconstructed by a party that does not depend on the new rule?

The sub-questions (the probe must answer each as a category, never a verdict):

- Can a rule validate the modification that created it without circularity?
- Can a witness be removed while preserving proof that the removal was legitimate?
- Can authority and provenance collapse into one layer without producing an *unadjudicable* advantage?
- Which failures are detectable at all, and which are detectable *only by an independent witness*?

## Why "arbitrage" is not "non-orientability" (the distinction that makes this a separate probe)

Provenance recovery answers *"can I reconstruct that the change happened, and its lineage?"* — existence.
Advantage reconstructability answers *"can an independent party reconstruct whether the change conferred
illegitimate advantage?"* — adjudication. Adjudication requires a standard of legitimacy that does **not** depend
on the rule the actor changed. If the standard *is* the changed authority, then even with complete lineage the
legitimacy is unadjudicable from outside, and the advantage is hidden *though fully recorded.*

```
fully orientable + fully logged  ─/─▶  arbitrage-free
```

That implication does **not** hold. A `LOCAL_ONLY` system (orientable per commit-cut) can still permit authority
arbitrage if the actor *controls the cut* — i.e., if the actor is also the witness of its own grant. The new
axis this probe adds, which the self-modification probe does not have, is exactly **reconstructability of
advantage by an independent witness.**

## Minimal model — three roles

```
X = actor            (gains or loses advantage)
M = authority        (the rule that validates X's actions / grants)
W = witness          (what an independent party uses to adjudicate whether a grant was legitimate)
```

**Normal case — the witness is independent of the actor:**

```
   W                      (adjudicates against a standard X cannot edit)
   │
   ▼
   M ──validates──▶ X
```

`W ⟂ X`: any advantage X gains is reconstructable, because W adjudicates against a standard outside X's reach.

**Arbitrage case — the actor can edit its own authority, and controls its witness:**

```
      ┌──────────────────────────┐
      │                          │
      ▼                          │
      M ──validates──▶ X ──edits──┘
      ▲                          │
      W ◀──────controls──────────┘
```

`X` grants itself authority by editing `M`, and the only record of the grant is one `X` controls (`W` is not
independent). The grant is *logged* but *unadjudicable*. That is hidden arbitrage.

## The gradient (mirrors the self-modification cases, measured for advantage)

### Case 1 — external authority (the control)

```
authority M (fixed) ──validates──▶ actor X
```

`X` cannot change `M`; `W ⟂ X`. Expectation: **ARBITRAGE-FREE / RECONSTRUCTABLE / witness INDEPENDENT.** This
case exists as a **negative-success gate**: it must come back arbitrage-free, or the instrument is detecting
arbitrage where there is none, and nothing it says about Cases 2–3 is admissible.

### Case 2 — actor edits the authority *rule*

```
rule:      "grants require X's own signature at level L"
mutation:  "X lowers L for itself"
```

Question: is the benefit of the lowered bar reconstructable by a witness that does **not** depend on the new
rule? Expected interesting result: the grant event commits **under the old rule**, before the new rule exists, so
an independent party replaying under the old regime can adjudicate it. The cycle is broken by **commit-time
precedence over append-only history** — the new authority cannot retroactively legitimize the act that created
it. → **LOCAL_ONLY / RECONSTRUCTABLE_VIA_INDEPENDENT_WITNESS**, *provided the old regime is preserved*. If the
new rule can retroactively bless its own creating grant, that is a frustrated cycle and unadjudicable advantage →
`NON_ORIENTABLE / SEVERED`.

### Case 3 — actor edits the *witness* of authority (the knife edge)

```
v1:        "every grant records an independent witness hash"
mutation:  "X removes the witness for its own grant"
```

Then the recursive question: can the system prove the grant was legitimate **using the witness it removed**? This
is `compress ≠ sever` at the authority level. Expected: hidden arbitrage is achieved **iff the removed witness
was the only independent proof of the grant's legitimacy** → **UNRECONSTRUCTABLE / SEVERED**. Where an independent
witness survives the mutation, the advantage is still adjudicable (`RECONSTRUCTABLE_VIA_INDEPENDENT_WITNESS`);
where the actor's edit destroys its own only adjudicator, the system must report `SEVERED` — never reconstruct a
verdict it cannot support, and never silently treat the unadjudicable grant as legitimate.

## Measurements (three categorical axes — no scalar, no verdict)

**1. Advantage reconstructability** *(the new axis)* — can an independent party adjudicate the advantage?

```
RECONSTRUCTABLE                     adjudicable against a standard outside the actor's reach
RECONSTRUCTABLE_VIA_INDEPENDENT_WITNESS   adjudicable only through a witness the mutation could not remove
SEVERED                             the only adjudicator was removed — reported, never guessed (hidden arbitrage)
```

**2. Orientability** *(via `klein_probe`)* — is the inside/outside cut for "who validates whom" globally definable?

```
ORIENTABLE        one consistent global authority cut
LOCAL_ONLY        orientable per commit-time cut (anchored by precedence), no single global cut
NON_ORIENTABLE    following the validate→edit→validate loop reverses the authority sense (frustrated)
```

**3. Witness independence** *(via `frontier_probe`'s sealed-observer property)* — does a validator of the
rule-change exist that does not depend on the changed rule?

```
INDEPENDENT   the witness cannot be edited by the authority it certifies
SHARED        the witness depends partly on the changed rule (partial adjudication)
COLLAPSED     authority and witness are one layer — the actor witnesses its own grant
```

The only legitimate rollup is the unweighted conjunction across axes and cases — *arbitrage-free everywhere?* —
never a weighted "fairness score." `objectivity is not one scalar`; neither is its absence.

## Invariants · observables · assumptions · failure modes · ghosts · alternatives

**Invariants the probe must not violate:** committed history is append-only; the authority-in-force is evaluated
at commit instant; the instrument observes (it does not grant, revoke, or punish — `telemetry ≠ control`).

**Observables:** the grant log; authority-in-force per grant; the witness reference per grant; the signed
validate→edit boundary graph; the adjudication result of "was this grant legitimate?" run by a party that does
not depend on the changed rule.

**Assumptions (declared):** a single logical clock orders commits; the authority rule and its witness are
recorded as events (not ambient); a legitimacy standard exists that can be evaluated independently of the rule
under test (where it cannot, that is itself the `SEVERED` result, not an error). Single-process logic; concurrency
is a separate boundary.

**Failure modes:** (a) the new authority retroactively legitimizes its own creating grant (append-only violated)
→ false `ARBITRAGE-FREE`; (b) the actor removes its own only witness and the system *reconstructs a verdict*
instead of reporting `SEVERED` (the lethal one — unadjudicable advantage laundered as legitimate); (c) the
instrument flags arbitrage in Case 1 (false positive — miscalibrated).

**Possible ghost signals:** a grant that is `RECONSTRUCTABLE` under provenance recovery (the change is fully
logged) yet `SEVERED` under advantage reconstructability (legitimacy unadjudicable) — the exact gap this probe
exists to expose, and the proof that arbitrage ≠ non-orientability; a `COLLAPSED` witness that still yields
`RECONSTRUCTABLE` advantage (would *falsify* the layering necessity — see below); an advantage adjudicable under
one declared legitimacy standard and `SEVERED` under another (the standard is doing the work — Arbitrary-Boundary
Law at the authority level).

**Alternative formulations (rejected for v1, kept at the fork):** model advantage as a continuous quantity rather
than adjudicable/not (richer, but reintroduces the scalar the project refuses); let the witness itself be
mutable-then-committed (doubles the recursion before the single-level result exists); treat multiple actors with
competing authorities (that is consensus/concurrency — deferred, would merge two unknowns).

## Expected outcome — stated as a falsifiable hypothesis

The leading hypothesis (to falsify, not confirm):

> **Authority arbitrage is structurally unrepresentable *iff* every authority-or-witness change commits under,
> and is witnessed by, a layer it cannot itself edit.** Layered authority is then not a design preference but a
> *necessary anti-arbitrage structure*:

```
stable witness layer        certifies grants; not editable by the authority it certifies
        │
        ▼
mutable operational layer    changes authority under the witness layer's standard
        │
        ▼
experimental layer           private, speculative, discardable
```

**What would falsify it:** a single, self-validating layer (`COLLAPSED` witness) that nonetheless yields only
`RECONSTRUCTABLE` advantage across all three cases — genuinely arbitrage-free self-authority, the witness layer
unnecessary. If Case 3 returns `RECONSTRUCTABLE` with a collapsed witness, the layering hypothesis is wrong.

The sharper, ordered prediction (more falsifiable than the headline): Case 1 `ARBITRAGE-FREE`; Case 2
`LOCAL_ONLY / RECONSTRUCTABLE_VIA_INDEPENDENT_WITNESS` (authority self-edit adjudicable by commit-time
precedence); Case 3 `SEVERED` *exactly when* the actor's edit removes its own only independent witness,
adjudicable otherwise. If the boundary falls anywhere other than at *witness destruction*, the model here is
wrong — and that disagreement is the result.

## Honest scope — residual, and the standing caveat on "maximum"

This probe does not eliminate arbitrage in general; it makes **one named class** measurable and asks where it can
be made unrepresentable. The maximum reduction it could establish is **zero extractable authority-arbitrage for
this class, by non-representability** — not by detection, not by punishment. Two honest bounds stay in view:

- **The bootstrap residual.** A stable witness layer that cannot be edited by what it certifies still has a
  *genesis* — and *who witnesses the witness layer's own origin?* Layering relocates the unadjudicability to the
  bootstrap (the `external-root` vs `embedded-root` genesis problem the kernel already flags open). The maximum is
  "zero within the layer, modulo genesis." The layered structure answers arbitrage *given* a witnessed origin; it
  does not supply one.
- **"Proven" means non-identifiability under bounded experimental access**, on a trace, against a declared
  legitimacy standard — never a truth about the world. `zero arbitrage on this trace ≠ zero arbitrage on
  hardware`; a richer adjudicator class may reconstruct advantage a poorer one cannot (the `adversary_capacity`
  lattice, one layer up). There is no observer-independent "maximum reduction" scalar; this probe earns a maximum
  *for a named class relative to a declared witness standard*, which is the strongest honest form.

Concurrency stays a separate artifact: it asks *can many actors share one authority?*; this asks *can one actor
edit the authority that governs it without hidden advantage?* Merging them now would recreate the
merge-two-unknowns failure mode.

## The seam (the contract code must satisfy, not yet built)

A future `experiments/live_world_kernel/authority_arbitrage_probe.py` would:

1. reuse the kernel's `EditEvent` / commit log and capability-as-event model unchanged (authority + witness
   recorded as events, evaluated at commit instant);
2. encode each case as a signed validate→edit boundary graph; classify orientability via `klein_probe` and
   witness-independence via the sealed-observer property of `frontier_probe`;
3. run an *independent adjudicator* — a replay that does not depend on the changed rule — and report advantage as
   `RECONSTRUCTABLE / VIA_INDEPENDENT_WITNESS / SEVERED`, never a reconstructed verdict it cannot support;
4. emit the three axes per case as a vector — no scalar, no verdict — with a self-test whose first success is
   *negative*: Case 1 must be `ARBITRAGE-FREE` (no false detection) before any claim about Cases 2–3 is
   admissible.

Until there is a reason to test it — an actual client that edits its own authority or witness — this is the
boundary, named and made falsifiable, standing exactly one step ahead of the implementation. `declared ≠
verified`; the strongest arbitrage reduction is non-representability, and even that is bounded by genesis.
