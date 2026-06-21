<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Phase R — Provenance Runtime

Not another research phase — a **consolidation**. The implementation arc produced many objects that were all
the same shape: a value bound to the conditions of its own existence. The unifying runtime object is the
**provenance-bearing artifact**, and every prior phase becomes an artifact *type*, not a separate project.

```
Artifact
 ├── identity      content hash  +  CLAIM hash (what is asserted, separate from how it is represented)
 ├── provenance    creator manifest · transformation history · dependencies (a DAG) · declared assumptions
 ├── evidence      observations · interventions · model family 𝓕 · admissibility set 𝓐
 └── status        verified | survived | assumed | unknown
```

The inversion: a normal ML runtime asks *"what output did the model produce?"* This one asks *"what object
exists, under what transformations, and what licenses its existence?"* — the model output is just one artifact.

## Run

```bash
python3 experiments/provenance_runtime/run.py     # stdlib only; deterministic
```

## The prior phases, migrated

```
GroundedClaim     claim   + floor              CausalEdge       edge   + support
Coordinate        value   + ledger             EstimatorOutput  inference + identification cost + domain
Representation     latent  + manifest + claim
```

All become `Artifact(kind, content, provenance, evidence, status)` with one `digest()` and one `claim_digest()`.

## The primitives

- `transform(operation, **changes)` — a NEW artifact with inherited provenance (a dependency on its parent + an
  extended history). The encoder/model/estimator is a plugin; the artifact contract is not.
- `compare(other)` — compares **claims, not representations**: two artifacts can be claim-equivalent while
  differing in full identity (Phase-5 humility, generalized).
- `audit()` — exposes what was **demonstrated** (interventions/observations) vs **assumed** (declared
  assumptions), and whether the artifact is unverified.

## The test that matters (and the runtime invariants)

```
developer can swap the representation WITHOUT losing the history of what made the result admissible
identity includes provenance      same content, different provenance → different object
transform inherits provenance      child depends on parent; history is extended, never erased
compare is over claims             not over representations
audit separates assumed from demonstrated
creator is a provenance source     changing a creator constraint changes the identity (named, not hidden)
status is typed                    verified | survived | assumed | unknown
all phases migrate to one identity system
```

The headline: swap the encoder via `transform("swap_encoder", ...)` → the **claim digest is preserved**, the
full digest changes, and the new artifact records a dependency on its parent. The developer changed the model
without losing what made the result admissible.

## Honest bounds

The runtime **records and audits** declared provenance; it does not **validate** it — `declared cost ≠ verified
cost`. The creator is neither hidden nor sovereign: a named provenance source, one causal input among the
transformation chain and the survival tests. The runtime only ever says *this artifact persisted under these
declared transformations and constraints* — blocking both anthropomorphism ("it discovered because it thinks
like us") and technological projection ("it discovered because it is outside us"). `identity includes
provenance` — including the provenance of the creator.
