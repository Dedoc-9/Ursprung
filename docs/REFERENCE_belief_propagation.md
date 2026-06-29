<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Reference case (CLOSED): belief-propagation tensor-network gauging vs the Ursprung stack

An **adjacent reference architecture**, recorded so the adjacency is mapped honestly and the boundaries are
explicit. **Decision: do NOT vendor or merge any tensor-network / BP code into `ursprung-gateway` or the
`ursprung` crate.** This is a conceptual note, not a dependency. `adjacent ≠ on-mission`.

## The external work

Joseph Tindall & Matthew Fishman, *Gauging tensor networks with belief propagation* (SciPost Phys. 15, 222,
2023; arXiv:2306.17837), plus the recent line: generalized-BP approximate contraction (arXiv:2604.24760) and
rigorous BP+tensor-network cluster-expansion limits (arXiv:2604.03228). Belief propagation — message passing
for marginal inference on a factor graph — is **exact on trees, approximate (loopy) fixed points on graphs
with cycles**. A BP fixed point yields a canonical bond gauge that re-conditions truncation/contraction.
`approximation ≠ exact contraction`.

## Genuine adjacencies (not forced)

1. **Information locality — but duals.** BP passes messages along the Markov-blanket conditional-independence
   boundaries of a graphical model; the DVSM firewall uses `I(X;Y|Z)` to test dependence across a designated
   boundary. The deep distinction: **BP *assumes* the graph and computes marginals given it; the firewall
   *audits* whether a claimed conditional-independence edge actually holds.** `assumes-the-graph ≠
   audits-the-edge`. Direction of any future bridge is fixed by this: BP could *propose* candidate edges for
   the firewall to *test*; the firewall can never consume a BP fixed point as evidence.

2. **Local structural normalization — but invariance vs projection.** TN gauging refactors bond indices
   locally to make truncation well-conditioned **without altering the global scalar** (an exact gauge
   *invariance*). κ-remediation (`κ ← (κ−κᵀ)/2`, giving `max|κ+κᵀ|=0`) also normalizes locally so a downstream
   certificate is well-conditioned — **but it discards the symmetric part and therefore changes the operator's
   dynamics** (a corrective *projection* that establishes the energy-law premise). Same *role* (precondition a
   certificate), opposite *nature*. `gauge ≠ projection`; `value-preserving ≠ premise-correcting`.

## The membrane — where they do NOT connect

- **`heuristic ≠ proof`.** A loopy BP fixed point is an approximate heuristic, not a mechanically-checkable
  deductive certificate. It cannot enter a `Grounded[T]` value or back a `CLOSED` claim — those come from
  symbolic model checking / SMT / explicit BFS reachability in `weltwerk/verify`. A heuristic fixed point is
  exactly the kind of thing the action chokepoint refuses.
- **Different domains.** The gateway parses discrete, deterministic, fixed-record real telemetry frames to
  map *physical-system trajectories*. BP+TN cluster expansions model *high-dimensional disordered quantum
  many-body states*. Separate mathematical objects; no shared runtime.
- **Zero-dependency posture.** The `ursprung` crate is `std`-only by design. A real TN/BP capability is a
  large numerical dependency; importing it would break the posture and the audit story. Refused.

## If ever extended (the graded-blind-spot rule)

Should the CMI firewall one day need to estimate conditional-independence boundaries on **loopy** graphs, BP
*may* be used as a fast local **estimator** — but, per the "every instrument reports its blind spot" rule, its
output must be graded **SPECULATIVE** / **UNDERDETERMINED** on cyclic structures, with the BP loop error
logged as a **permanent boundary ghost** (a residual that allocates investigation, never certifies a verdict).
`estimate ≠ property`; `salience ≠ importance`.

## Status

**CLOSED reference case.** No code, no dependency, no roadmap commitment — a mapped adjacency with its
boundaries stated. `integrity ≠ truth`.

Sources: arXiv:2306.17837 · SciPost Phys. 15, 222 (2023) · arXiv:2604.24760 · arXiv:2604.03228.
