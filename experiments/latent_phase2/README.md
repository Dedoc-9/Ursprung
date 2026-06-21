<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Phase 2 — topology discovery (where in the intervention graph does a factor sit?)

Phase 1 caught the **confounder** with the intervention gate, but its own honest bound exposed the next gap:
the gate answers *"is this factor causally relevant?"*, and a **mediator** on `g → x → y` passes that gate too
(`do(x)` moves the outcome). So "survives intervention" yields a *causal candidate*, not a root. Phase 2 is the
answer — treated, deliberately, as a **topology-discovery** problem rather than a score-improvement one.

It slots Tier 3 into the benchmark hierarchy:

```
Tier 1  reconstruction         (entry gate)
Tier 2  intervention relevance  (causally relevant?)        — Phase 1
Tier 3  topology recovery       (WHERE in the graph?)       — here
Tier 4  robustness across 𝓕
Tier 5  gauge invariance
```

## Run

```bash
PYTHONHASHSEED=0 python3 experiments/latent_phase2/run.py    # needs numpy; seeded → replayable
```

## What it does

`world.py` is a structural causal model — `g` (root) → `x` (mediator) → `y` (sink), plus `c` (observed but
isolated from the chain) — with a `do()` that resamples a node and propagates downstream. `topology.py` recovers
the partial order from intervention **asymmetries** alone: `moves(i, j)` = "does `do(i)` move `j`?", read as a
response matrix, then as roles (root / mediator / sink / isolated).

## The measured result (seed 0)

```
do(g) → moves x and y          do(x) → moves y, NOT g
do(y) → moves nothing          do(c) → moves nothing
roles: g=root  x=mediator  y=sink  c=isolated
Tier 2 (relevant to outcome y): g=True, x=True, c=False
```

`g` and `x` are **both** relevant to the outcome — Tier 2 cannot separate them. **Topology** does: `do(g)` moves
`x` but `do(x)` does not move `g`, so `g` is the root and `x` is a mediator beneath it. The mediator passes
Tier 2 and is correctly placed below the root. `survives intervention ≠ root generator`.

## Honest bounds

- **`recovered topology ≠ discovered ontology`** — even a perfectly recovered graph is a graph over *latent
  variables created by a particular representation family*; it is a surviving explanation under a declared
  model class `𝓕`, not a final description of reality. Relabel the factors and you relabel the graph.
- The recovery assumes a **real `do()`** is available and the world is known. With an unknown causal graph and
  no free intervention operator, topology recovery is the open frontier (`observation ≠ intervention`), not a
  solved step. What transfers is the **procedure**: read asymmetries, not effect magnitudes; report the graph
  with its declared `𝓕`, never as ground truth.

The clean progression the project now follows:
`observation → intervention → causal candidate → causal topology → robustness across model classes → declared floor`.
