<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Phase 3 — edge provenance (discipline-first; support is part of a causal graph's identity)

Phase 2 recovered topology *given* a real `do()` and a known world. The frontier is **intervention scarcity**:
most edges can't be intervened on, so they are recovered only by *assuming* structure — and the graph's floor
grows as intervention access shrinks. This phase is the discipline that frontier needs, built **before any
estimator**: it does not solve causal discovery, it records *what kind of support each edge claims*.

The inversion this encodes: most causal-discovery work optimizes **recovery** (how much graph, given limited
interventions) and treats assumptions as means. Here, **provenance is the objective** and recovery is secondary
— *how much of the graph is intervention-grounded, and what assumptions carry the rest.*

## Run

```bash
python3 experiments/latent_phase3/run.py     # stdlib only; deterministic
```

## The object

An edge carries its **support** — `intervention_grounded` (a `do()` moved the child) or
`assumption_load_bearing` (recovered only under a declared identification assumption: `invariance`,
`instrument_validity`, `faithfulness`, `as_if_random`). The principle, the graph-level analogue of
`grounded_claim`'s "a claim is never emitted without its floor":

> An edge is never emitted without the admissibility boundary that made it recoverable.

Support is folded into the edge's content hash, so a graph's `digest` covers edges *including* their support:

```
A → B   [intervention_grounded]          two graphs with an identical adjacency matrix
B → C   [assumption_load_bearing:invariance]   but different support are DIFFERENT objects
```

just as `floor_digest()` made the floor part of a claim's identity.

## The 𝓐 / 𝓕 symmetry

| explanation layer | causal layer |
|---|---|
| admissible model class `𝓕` | admissible assumption set `𝓐` |
| explanation survives relative to `𝓕` | edge survives relative to `𝓐` |
| robustness = `⋂` over `𝓕` | robustness = `⋂` over `𝓐` |
| knife edge when changing `𝓕` | knife edge when changing `𝓐` |

The `𝓐`-invariant core (edges surviving *every* admissible `𝓐`) is exactly the **intervention-grounded
subgraph** — the part that needs no assumption to survive, the analogue of the model-robust generator.

## Verified (the provenance benchmark, not an estimator benchmark)

```
1. provenance changes identity      same adjacency, different support → different digest
2. removing an assumption from 𝓐    can remove an edge (drop invariance → z→y disappears)
3. subgraphs distinguishable        intervention-grounded ⊔ assumption-load-bearing = all edges, disjoint
4. report quantifies provenance     intervention_backed=2, assumption_backed=2, intervention_fraction=0.5
+  an assumption edge cannot be constructed without a declared assumption
+  the 𝓐-invariant core = the intervention-grounded subgraph
+  no assumption-backed edge can wear an intervention-grounded label
```

## Honest bounds

This records the **claimed** support; it does **not** verify that an assumption holds (that is the estimator's
job, and the open problem). It guarantees only that an assumption-backed edge can never wear an
intervention-backed edge's confidence, and that every assumed edge names and content-addresses its assumption.
`recovered topology ≠ discovered ontology`; `chosen ≠ derived`, now at the level of a single arrow. The
estimator questions (which IV, which invariance test, which counterfactual model) are intentionally left open —
the provenance object does not depend on solving them.
