<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Failure Taxonomy — the provenance of ignorance

The downstream consequence of the two absolutes. An estimator that fails must not report a generic `unknown`;
it must name **why** the cause is unrecoverable — because the four kinds have completely different remedies, and
two of them have none. This types the *provenance of ignorance* and unifies the whole identifiability arc.

```
severance              ABSOLUTE   information ABSENT (I(X;O)=0) — an INDEPENDENCE relation — "no path remains"        (M21)
indistinguishability   ABSOLUTE   present but non-discriminating — an EQUIVALENCE relation X~X' — "paths collide"
assumption_limit       RELATIVE   not enough admissible structure — resolves under a richer 𝓐                       (model_relativity)
resource_limit         RELATIVE   observer boundedness — resolves under a richer observer class                     (adversary_capacity)
```

## Run

```bash
python3 experiments/failure_taxonomy/run.py     # stdlib only; deterministic
```

## The structure (10 checks)

| failure | relation | resolves under richer 𝓐? | resolves under richer observer? | remedy |
|---|---|---|---|---|
| severance | independence | no | no | none — information is absent |
| indistinguishability | equivalence | no | no | none — a distinct cause is observationally identical |
| assumption_limit | admissibility | **yes** | no | admit a stronger declared assumption |
| resource_limit | capacity | no | **yes** | upgrade the observer class |

The two **absolutes** resolve under *neither* axis — the failure is in the world's relation to the observables,
not in the observer. The two **relative** limits each resolve under exactly one axis, which is what tells them
apart. Severance and indistinguishability are different mathematical objects — *no signal* vs *ambiguous
signal* — and must never collapse into one verdict.

## Why it matters

Ordinary systems report a single failure mode: "not recoverable." This forces the failure to carry its
provenance, so the response is correct: keep looking with a richer observer (`resource_limit`), declare a
stronger assumption (`assumption_limit`), or **stop** — because no observer and no assumption will ever recover
it (`severance`, `indistinguishability`). It refuses to entrench against a vacuum it has already proved is
unbridgeable, and refuses to give up on one a richer observer would cross.

## Honest bounds

This classifies a **declared** situation — which kind of failure is *claimed*, and what would resolve it — not a
verified proof that no observable carries the signal (severance) or that an alternative cause matches across all
interventions (indistinguishability, the un-runnable check). `declared ≠ verified`. The value is the taxonomy
itself: ignorance must name its own provenance rather than hide behind a generic `unknown`.
