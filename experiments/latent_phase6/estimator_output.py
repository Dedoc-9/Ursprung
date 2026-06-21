# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase6/estimator_output.py — the inference contract: no edge without its price.

Phases 3–5 attached provenance to the OBJECT being learned (edge → support, representation → claim). Phase 6
moves the constraint to the ACT OF INFERENCE itself: an estimator cannot produce a result without declaring
what made the result possible. The atomic output is not "an edge with an accuracy" — it is an edge bound to the
**price paid to identify it**.

The inversion (same architectural move as Phase 3): accuracy answers *"does this fit the regime I have?"*; it
does NOT answer *"what alternative worlds did I rule out?"* Those are different axes, so `accuracy ≠
identifiability`. A model can be 99% accurate and weakly identified, because the 99% may exist only inside a
narrow assumption set. The contract therefore makes the *cost* mandatory and the *accuracy* optional and
secondary — and accuracy is not part of the output's identity.

The cost is a **structured ledger, never a scalar** (the guard the project keeps relearning: a cheap assumption
and a rare intervention are not on one axis; collapsing them recreates the one-dimensional confidence object
trajectory/ledgers dismantled). Two inferences of the same edge with different prices are different objects;
two with the same total but a different *kind* of cost are also different. The graph-level `InferenceBudget`
composes edge costs into a breakdown of intervention-purchased vs assumption-purchased — a ledger, not a score.

This is the discipline layer, built before any estimator (no estimator required; a real one later either
satisfies the type or fails against it). It would EARN the separator `accuracy ≠ identifiability`. HONEST: it
records the *declared* price; it does not verify the price was paid in valid coin — that (running the IV,
checking the invariance under scarcity) is the research-grade frontier. `prediction ≠ inference identity`.
"""
from __future__ import annotations

import hashlib
import json


class IdentificationCost:
    """What was SPENT to identify an edge — a structured ledger across four kinds, never a single number.

      interventions           — the do() operations actually run (the cheap, grounded coin)
      assumptions             — identification assumptions drawn down (instrument validity, invariance, …)
      domain_restrictions     — the regime the identification is confined to
      unverified_dependencies — debts: things relied on but not checked (the most expensive, most hidden)
    """
    __slots__ = ("interventions", "assumptions", "domain_restrictions", "unverified_dependencies")

    def __init__(self, interventions=(), assumptions=(), domain_restrictions=(), unverified_dependencies=()):
        self.interventions = list(interventions)
        self.assumptions = list(assumptions)
        self.domain_restrictions = list(domain_restrictions)
        self.unverified_dependencies = list(unverified_dependencies)

    def is_empty(self):
        return not (self.interventions or self.assumptions or self.domain_restrictions or self.unverified_dependencies)

    def kind(self):
        """A coarse classification for the budget — NOT a collapse of the ledger, just a routing label."""
        if self.interventions and not self.assumptions:
            return "intervention_purchased"
        if self.assumptions and not self.interventions:
            return "assumption_purchased"
        return "free" if self.is_empty() else "mixed"

    def as_dict(self):
        return {"interventions": self.interventions, "assumptions": self.assumptions,
                "domain_restrictions": self.domain_restrictions,
                "unverified_dependencies": self.unverified_dependencies}

    def digest(self):
        return hashlib.sha256(json.dumps(self.as_dict(), sort_keys=True).encode()).hexdigest()[:10]


class EstimatorOutput:
    """An inferred edge that cannot exist without its price. Identity = edge + cost + confidence_domain.
    `accuracy` is optional, secondary, and NOT part of identity — it can never substitute for the cost."""
    __slots__ = ("edge", "cost", "domain", "accuracy")

    def __init__(self, edge, identification_cost, confidence_domain, accuracy=None):
        if identification_cost is None or identification_cost.is_empty():
            raise ValueError("no free inference: declare the identification cost (what you spent) for %r — "
                             "accuracy cannot substitute for it" % (tuple(edge),))
        self.edge = tuple(edge)
        self.cost = identification_cost
        self.domain = tuple(sorted(confidence_domain))      # the regime the claim holds over — part of identity
        self.accuracy = accuracy                            # optional, secondary, excluded from identity

    def digest(self):
        return hashlib.sha256(json.dumps(
            {"edge": self.edge, "cost": self.cost.digest(), "domain": self.domain},
            sort_keys=True).encode()).hexdigest()[:10]

    def __repr__(self):
        return "<%s→%s price=%s domain=%s>" % (self.edge[0], self.edge[1], self.cost.kind(), list(self.domain))


class InferenceBudget:
    """Graph-level composition of edge prices — the hidden economy of inference made into a ledger."""

    def __init__(self, outputs):
        self.outputs = list(outputs)

    def composition(self):
        out = {"intervention_purchased": [], "assumption_purchased": [], "mixed": []}
        for o in self.outputs:
            out[o.cost.kind()].append(o.edge)
        return out

    def composed_cost(self):
        """The aggregate ledger: the union of every kind of cost across all edges (a composed ledger, not a sum)."""
        agg = {"interventions": set(), "assumptions": set(), "domain_restrictions": set(), "unverified_dependencies": set()}
        for o in self.outputs:
            for k in agg:
                agg[k].update(getattr(o.cost, k))
        return {k: sorted(v) for k, v in agg.items()}

    def report(self):
        comp = self.composition()
        n = len(self.outputs)
        return {"intervention_purchased": len(comp["intervention_purchased"]),
                "assumption_purchased": len(comp["assumption_purchased"]),
                "mixed": len(comp["mixed"]),
                "intervention_fraction_secondary": round(len(comp["intervention_purchased"]) / n, 3) if n else 0.0,
                "composed_cost": self.composed_cost(), "ledger": comp}
