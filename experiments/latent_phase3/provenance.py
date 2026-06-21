# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase3/provenance.py — edge provenance: support is part of a causal graph's identity.

Phase 2 recovered topology *given* a real `do()` and a known world. Under **intervention scarcity** (the real
frontier), most edges cannot be intervened on — they are recovered only by *assuming* structure (an instrument
is valid, an invariance holds across environments, a natural experiment is as-if-random). So the graph's floor
grows as intervention access shrinks. This module is the **discipline-first** layer that frontier needs, built
*before* any estimator: it does not solve causal discovery, it records *what kind of support each edge claims*.

The principle, the graph-level analogue of `grounded_claim`'s "a claim is never emitted without its floor":

    An edge is never emitted without the admissibility boundary that made it recoverable.

So an edge carries its **support**: either `intervention_grounded` (a `do()` moved the child) or
`assumption_load_bearing` (recovered only under a declared identification assumption). Support is folded into
the edge's content hash, and the graph's digest is taken over edges *including* their support — so two graphs
with an identical adjacency matrix but different provenance are **different objects** (just as `floor_digest`
made the floor part of a claim's identity). And the model-relativity symmetry holds one level down: as an
explanation survives only relative to a declared model class `𝓕`, an **edge survives only relative to a
declared assumption set `𝓐`** — change `𝓐` and a different graph survives; the `𝓐`-invariant core (edges
surviving *every* admissible `𝓐`) is exactly the intervention-grounded subgraph, the `⋂ over 𝓐` analogue of
the model-robust generator.

CLASSIFICATION: discipline / bookkeeping (stdlib only — no estimator, no numpy; deterministic). HONEST BOUND:
this records the *claimed* support; it does not verify that an assumption holds (that is the estimator's job and
the open problem). It guarantees only that an `assumption_load_bearing` edge can never wear an
`intervention_grounded` edge's confidence, and that every assumed edge names and content-addresses its
assumption. Separators: recovered topology ≠ discovered ontology; intervention-grounded ≠ assumption-backed;
edge survives relative to 𝓐 ≠ edge holds absolutely; chosen ≠ derived (at the level of a single arrow).
"""
from __future__ import annotations

import hashlib
import json

INTERVENTION_GROUNDED = "intervention_grounded"
ASSUMPTION_LOAD_BEARING = "assumption_load_bearing"
MODES = (INTERVENTION_GROUNDED, ASSUMPTION_LOAD_BEARING)

# the declared identification-assumption vocabulary (each is a trade: an intervention you could not run)
ASSUMPTION_TYPES = {"instrument_validity", "faithfulness", "invariance", "as_if_random"}


class CausalEdge:
    """A directed edge that carries its support. An assumption-load-bearing edge MUST declare its assumption
    (the admissibility boundary that made it recoverable); an intervention-grounded edge carries none."""
    __slots__ = ("src", "dst", "mode", "assumption")

    def __init__(self, src, dst, mode, assumption=None):
        if mode not in MODES:
            raise ValueError("unknown support mode %r" % mode)
        if mode == ASSUMPTION_LOAD_BEARING and not assumption:
            raise ValueError("an assumption_load_bearing edge must declare its assumption — "
                             "never emit an edge without the admissibility boundary that made it recoverable")
        if mode == INTERVENTION_GROUNDED and assumption is not None:
            raise ValueError("an intervention_grounded edge carries no assumption")
        if assumption and assumption.get("type") not in ASSUMPTION_TYPES:
            raise ValueError("undeclared assumption type %r" % (assumption.get("type"),))
        self.src, self.dst, self.mode, self.assumption = src, dst, mode, assumption

    def assumption_type(self):
        return self.assumption["type"] if self.assumption else None

    def support_label(self):
        """The confidence label, tied to the mode — an assumed edge can never report 'intervention_grounded'."""
        return self.mode

    def digest(self):
        return hashlib.sha256(json.dumps(
            {"src": self.src, "dst": self.dst, "mode": self.mode, "assumption": self.assumption},
            sort_keys=True).encode()).hexdigest()[:12]

    def __repr__(self):
        tag = self.mode if self.mode == INTERVENTION_GROUNDED else "%s:%s" % (self.mode, self.assumption_type())
        return "<%s→%s [%s]>" % (self.src, self.dst, tag)


class ProvenanceGraph:
    """A causal graph whose identity includes the support of every edge."""

    def __init__(self, edges):
        self.edges = list(edges)

    def surviving(self, admissible_assumptions):
        """Edges that survive under a declared assumption set 𝓐: intervention-grounded edges always survive;
        assumption-load-bearing edges survive only if their assumption is admitted."""
        A = set(admissible_assumptions)
        return [e for e in self.edges if e.mode == INTERVENTION_GROUNDED or e.assumption_type() in A]

    def digest(self, admissible_assumptions=None):
        """Content address over edges INCLUDING their support — provenance is part of identity."""
        es = self.edges if admissible_assumptions is None else self.surviving(admissible_assumptions)
        return hashlib.sha256(json.dumps(sorted(e.digest() for e in es)).encode()).hexdigest()[:12]

    def intervention_subgraph(self):
        return [e for e in self.edges if e.mode == INTERVENTION_GROUNDED]

    def assumption_subgraph(self):
        return [e for e in self.edges if e.mode == ASSUMPTION_LOAD_BEARING]

    def A_invariant_core(self, admissible_sets):
        """Edges surviving EVERY admissible assumption set — the ⋂ over 𝓐, the analogue of the model-robust
        generator. Equals the intervention-grounded subgraph: the part that needs no assumption to survive."""
        return [e for e in self.edges if all(e in self.surviving(A) for A in admissible_sets)]

    def report(self, admissible_assumptions):
        """How much of the (surviving) graph is intervention-backed vs assumption-backed. The provenance
        accounting — never collapse the two."""
        surv = self.surviving(admissible_assumptions)
        ig = [e for e in surv if e.mode == INTERVENTION_GROUNDED]
        ab = [e for e in surv if e.mode == ASSUMPTION_LOAD_BEARING]
        n = len(surv)
        return {"surviving": n, "intervention_backed": len(ig), "assumption_backed": len(ab),
                "intervention_fraction": round(len(ig) / n, 3) if n else 0.0,
                "assumption_load": sorted({e.assumption_type() for e in ab})}
