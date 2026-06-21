<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Reality Kernel — assembling the organism, not adding an organ

A consolidation phase, not a new theory. The runtime had reached the point where consolidation is
worth more than expansion: the scattered objects that survived every layer are gathered into one
minimal surface with four immutable concepts.

```
RealityKernel
  Artifact   a thing that exists or is claimed     declared provenance required
  Event      how it changed                         a named source required (no silent mutation)
  Commit     an accepted transition receipt         a record, never an authorization
  Query      provenance-aware observation           existence AND absence
```

The inversion that makes this a runtime rather than an engine: most engines store `object → history
(optional)`; here **`history → object`** — an object without lineage is incomplete.

## It reuses, it does not reimplement

The old experiments do not disappear; they become **evidence modules**. `_evidence.py` loads the
verified Reality Authoring `World`/`Edit` and the `failure_taxonomy` diagnosis, so the kernel's
behaviour is the same code that earned those results — which is what makes the migration differential
identical by construction rather than by paraphrase. The history stays visible and executable.

```
provenance_runtime/Artifact   reality_authoring/Edit,World   failure_taxonomy/NonRecovery diagnosis
live_latent_provenance/CommitChannel,ResolveRing
                                   ↓  consolidated into
reality_kernel/  artifact.py · event.py · commit.py · query.py · kernel.py
```

## Run

```bash
python3 experiments/reality_kernel/run.py     # stdlib only; deterministic; 7/7
```

## The one genuinely new capability — a unified Query

`Query(target)` answers existence *and* absence, with provenance and a resolution path:

```
gravity                → present     · lineage: developer edit (gameplay_constraint) · resolution: none_needed
relation_R             → absent      · severance        · resolution: none           (absolute; no remedy)
relation_S             → unresolved  · assumption_limit · resolution: declare:instrument_validity_A
relation_T             → unresolved  · resource_limit   · resolution: allocate
relation_NEVER_ASKED   → unaccounted ·                  · resolution: investigate    (the silent gap)
```

This is a strict **refinement** of the Reality Authoring `explain()`: that bench merged absent and
unresolved into one `absent_or_unresolved` status; the kernel splits them by tier — an ABSOLUTE
failure is *absent* with no remedy, a RELATIVE one is *unresolved* with a path. No information lost;
one distinction gained.

## The first benchmark is not speed — it is whether consolidation preserves distinctions (7 checks)

```
an Artifact without provenance fails              (identity includes provenance)
an Event without a source fails                   (no transition without lineage)
a commit without a receipt fails                  (no digest → no receipt; a severed prerequisite → refused,
                                                   and state does NOT advance)
Query distinguishes present / absent / unresolved / unaccounted   (four categories stay four)
compression preserves resolvability               (the receipt carries a digest; full lineage recoverable)
migration reproduces the old diagnoses and refines existence   (real differential vs the imported old bench)
a receipt is a record, not an authorization       (fields are what/prior/source/deps/digest — never 'allowed?')
```

The kernel earns existence by **not collapsing categories**. The migration check is a real differential
against the imported `WorldWithIgnorance`: same scenario, identical diagnoses, existence a faithful
refinement of the old three-way status.

## Honest bounds

The kernel's strongest claim is also its ceiling:

> nothing exists here without a trace of how it entered;
> nothing is missing here without a trace of why it is missing.

It does not certify that any structure is **fundamental** — it remains a notary (`declared ≠
verified`; `attestation ≠ authority`). And it proves *what must be true*, not *what survives under
pressure*: this is stdlib and single-threaded, so allocation behaviour, lock-free commits, cache cost
of digest→graph resolution at scale, and many-producer concurrency are untouched — that is the Rust
substrate's job. The kernel is the contract Rust must preserve, which is exactly why it comes first:
**Python defines what must be true; Rust defines what must remain true under pressure.**
