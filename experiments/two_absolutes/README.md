<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Two Absolutes — severance and indistinguishability (and why erasure is not a third)

This bench records — and corrects — a proposed second class-independent guarantee. M21 established the *only*
absolute the project had named: **severance** (`I(secret ; observable) = 0` across every channel ⟹ no observer
of any capacity extracts it). The question was: what is the second?

A proposal came back as **"M22 — irreversible erasure."** Run through the framework's own discipline, it does
not stand as a new absolute:

- **Logical erasure** that reaches `I = 0` is not a new primitive — it *is* severance (M21). Same lemma
  (`zero MI ⟹ unrecoverable`), applied to the post-erasure residual instead of the pre-transmission channel.
- **Physical erasure** is **class-relative**: by Landauer, logically irreversible erasure *dissipates* the bit
  into the environment (heat / EM) rather than destroying it, so a richer observer who reads that reservoir
  recovers it. It belongs in the relative stack under `survived`, beside cryptographic hardness — `logical
  erasure ≠ physical erasure`.

The genuine **second absolute is indistinguishability**: distinct causes `{X, X'}` that induce identical
distributions over *every* observable, including every intervention (`P(Y|do(X)) = P(Y|do(X'))`), cannot be told
apart by an observer of infinite capacity. Severance hides by **absence**; indistinguishability hides by
**collision**. Those two exhaust the observer-independent boundaries.

## The correction this bench enforces

The two absolutes are symmetric as *boundaries* but **asymmetric in verifiability** — and a naive formalization
called both "Proved":

- **Severance** is often **constructively** witnessed (`I = 0` by construction is checkable).
- **Indistinguishability** generally **cannot be proved** — it needs identical distributions over every
  observable *and every intervention* across the whole admissibility set, which is the exhaustive intervention
  the project says you cannot run. So `indistinguishable` is almost always **declared**, not proved (`declared ≠
  verified`). In `latent_phase1` the confounder was *observationally* indistinguishable from the generator
  until `do(c)` broke it; true indistinguishability must survive all `do()`, and verifying that is the
  un-runnable thing.

## Run

```bash
python3 experiments/two_absolutes/run.py     # stdlib only; deterministic
```

## The status discipline (8 checks)

```
absolute tier:  M21_severed | indistinguishable     (observer-independent boundaries)
relative tier:  survived | assumed | unknown        (adversary-bounded; punctures against a richer observer)

physical erasure (M22_erased / physically_erased)   → REJECTED as an absolute (route to 'survived')
an absolute requires its declared licensing witness  → no free absolute
an absolute may not carry an adversary class         → an absolute is not relative to an observer
an absolute's witness is DECLARED, not verified       → declared ≠ verified
  severance        verifiability = constructive
  indistinguishable verifiability = requires_exhaustive_intervention  (the frontier)
```

This is the honest form of the proposed `Artifact.status` extension: it separates the two *absolutes* from the
relative survivals, but it refuses to let `indistinguishable` claim it was *proved* when the proof requires
interventions no one can run, and it refuses to let physical erasure pose as an absolute at all.
