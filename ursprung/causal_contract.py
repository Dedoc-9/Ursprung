# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/causal_contract.py — the Causal Contract (a map of possible causality, not a prediction) + CSA decay.

Milestone 7 introduced Causal Surface Area but created a subtle failure mode: **causal authority leakage** —
the renderer preparing so hard it accidentally becomes a second simulation. The Causal Contract is the
artifact that makes preparation safe: it states **what relationships exist**, never **what will happen**.

    ALLOWED (a relationship map):                FORBIDDEN (a prediction / authority):
      Door affected_by: [collision, explosion,     Door: "will break at tick 400"
                         scripted, net_authority]
      possible_representations: [intact, cracked,
                                 debris, particles]

A contract lists the agents/causes that *could* affect an object and the representations it *could* take. It
contains no outcome and no tick. This makes CSA much harder to game (you declare structure, not a self-serving
prediction) and keeps the moat intact: **the renderer may prepare for possible futures; it may never select
the future.**

It also fixes a real leak: a static CSA value is a memory leak (a wall that had 20 nearby players 10 s ago
stays "hot" forever). CSA must DECAY with temporal distance — near-future causality is expensive, distant
possibility is cheap:

    CSA(t) = agents × divergence × representation_cost × temporal_relevance(Δt)

CLASSIFICATION: OBSERVER / reference (mutates_core=False). It declares possible causality and decays
readiness; it commits no state and asserts no outcome. integrity ≠ truth.
"""
from __future__ import annotations

from . import causal_surface as cs


class CausalAuthorityLeak(cs.ProphecyViolation):
    """Raised when a 'contract' smuggles in an OUTCOME — i.e. the renderer trying to decide the future."""


class CausalContract:
    """A map of possible causality for one object: who can affect it, and what it can become. No outcome."""
    __slots__ = ("target", "affected_by", "possible_representations")

    def __init__(self, target, affected_by, possible_representations):
        self.target = target
        self.affected_by = list(affected_by)
        self.possible_representations = list(possible_representations)

    def admissible(self):
        """A contract is admissible iff it declares relationships + possible representations and NO outcome."""
        return bool(self.affected_by) and bool(self.possible_representations)

    def csa_inputs(self):
        """Derive CSA inputs from the contract: # agents/causes and the representation spread (divergence)."""
        return {"agents_can_affect": len(self.affected_by),
                "expected_divergence": max(1, len(self.possible_representations))}


def make_contract(target, affected_by, possible_representations):
    """Build an admissible causal contract (relationships + possible representations)."""
    c = CausalContract(target, affected_by, possible_representations)
    if not c.admissible():
        raise ValueError("a contract must declare affected_by and possible_representations")
    return c


def reject_outcome(target, outcome, at_tick=None):
    """A contract may NOT assert an outcome ('door will break at tick 400'). Fails closed — that is the
    simulation's authority, not the renderer's. (Constructing the attempt is fine; this rejects it.)"""
    raise CausalAuthorityLeak(
        "contract for %s asserted an outcome %r%s — a contract maps possible causality, it never predicts; "
        "only CORE decides outcomes" % (target, outcome, "" if at_tick is None else " at tick %s" % at_tick))


# --- CSA temporal decay (fixes the readiness memory-leak) -------------------------------------------

def temporal_relevance(dt, coherence=30):
    """Near-future causality is expensive, distant possibility is cheap. Returns a 0..100 relevance that
    decays with temporal distance Δt (dt=0 → 100; dt≫coherence → →0). Deterministic integer."""
    if dt < 0:
        dt = 0
    return max(0, 100 * coherence // (coherence + dt))


def decayed_csa(obj, dt, coherence=30):
    """CSA scaled by temporal relevance — so a stale convergence point cools off instead of leaking budget."""
    return cs.causal_surface_area(obj) * temporal_relevance(dt, coherence) // 100


def csa_from_contract(contract, obj_resistance, dt=0):
    """CSA for a contracted object: contract supplies agents/divergence, the object supplies resistance dims,
    Δt supplies decay. Keeps the prediction-free path: structure × cost × recency, never an outcome."""
    obj = dict(obj_resistance)
    obj.update(contract.csa_inputs())
    return decayed_csa(obj, dt)


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("causal_contract", OBSERVER, mutates_core=False,
                          note="Causal Contract — a map of possible causality (affected_by + possible "
                               "representations), never an outcome; CSA temporal decay fixes the readiness leak")
    except LayerViolation:
        pass
