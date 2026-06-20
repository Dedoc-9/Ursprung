# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/representation_futures.py — the Representation Futures Graph (prepare branches, never select one).

The shader cache's next abstraction is not a cache of assets — it is a graph of *possible futures* with the
representations each would need:

    wall intact
      ├─ damaged   → required: shader_A + debris_mesh + particles      (probability, readiness cost)
      └─ destroyed → required: fracture_cache + dust_sim + audio_proxy  (probability, readiness cost)

The renderer prepares the BRANCHES (makes possible futures cheap), gated by `P(transition) × Causal Surface
Area` and the fidelity derivative. It must preserve breadth — preparing *several* possibilities is the whole
point. The instant it collapses to a single committed branch, it has stopped preparing and started
predicting: that is **causal authority leakage**, and `select_future()` fails closed. Only CORE selects.

Rollback, reframed: when CORE commits an outcome, the prepared branch is already resident → the representation
*survives the truth correction* with no hitch; the non-selected branches are simply discarded. The renderer
never faked the world — it kept the image coherent while truth arrived. The particle fallback is the
continuity buffer (an error-correcting code for perception) for the unprepared case.

CLASSIFICATION: ALLOCATOR (mutates_core=False). It allocates preparation across possible branches and serves
fallbacks; it selects no future and commits no state. `observation → allocation`, never `→ truth`.

HONEST BOUND: declared probabilities/costs over a constructed graph; not a learned transition model. The
value is the structure (prepare-breadth, never-select), not the constants. integrity ≠ truth.
"""
from __future__ import annotations

from . import causal_surface as cs
from .causal_contract import CausalAuthorityLeak


class FuturesGraph:
    """States and the POSSIBLE transitions between them, each carrying the representation it would require."""

    def __init__(self):
        self.transitions = {}     # from_state -> list of dicts {to, probability, representation, fallback, cost}

    def add_transition(self, from_state, to_state, probability, representation, fallback="particle_proxy", cost=30):
        self.transitions.setdefault(from_state, []).append(
            {"to": to_state, "probability": int(probability), "representation": representation,
             "fallback": fallback, "cost": int(cost)})
        return self

    def branches(self, state):
        return list(self.transitions.get(state, []))


def prepare_branches(graph, state, csa, budget):
    """Prepare the high-readiness branches from `state` under `budget`. readiness = P(transition) × CSA, gated
    by benefit > cost. Every preparation is a representation forecast (prepare ≠ select) routed through the
    guard. Returns the set of prepared (to_state, representation) — plural by design (breadth preserved)."""
    cands = sorted(graph.branches(state), key=lambda b: -(b["probability"] * csa))
    prepared, spent = set(), 0
    for b in cands:
        if spent + b["cost"] > budget:
            break
        benefit = b["probability"] * csa // 100
        if benefit <= b["cost"]:
            continue
        # prepare the representation for a POSSIBLE branch — never an assertion that it will be taken
        cs.assert_prepared(cs.representation_forecast(b["to"], b["representation"]))
        prepared.add((b["to"], b["representation"])); spent += b["cost"]
    return prepared


def select_future(*_args, **_kwargs):
    """FORBIDDEN. The renderer may prepare every branch; it may never choose which becomes real. Collapsing
    the futures graph to one committed branch is causal authority leakage — only CORE selects."""
    raise CausalAuthorityLeak(
        "the renderer may prepare for possible futures, it may never SELECT the future — only CORE commits an outcome")


def survive_truth_correction(prepared, core_chosen_state):
    """CORE commits `core_chosen_state` (the truth correction / rollback resolution). If its representation was
    prepared → the image survives the correction with no hitch ('ready'); otherwise the continuity buffer
    (particle fallback) bridges while the real representation catches up ('fallback'). The renderer chose
    nothing — it was merely prepared."""
    for (to_state, _rep) in prepared:
        if to_state == core_chosen_state:
            return ("ready", 0)
    return ("fallback", 1)          # graceful: a perceptual bridge, never a full hitch, never a lie


def demo(budget=100):
    g = FuturesGraph()
    g.add_transition("intact", "damaged", probability=60, representation="shaderA+debris+particles", cost=30)
    g.add_transition("intact", "destroyed", probability=30, representation="fracture+dust+audio", cost=30)
    csa = cs.causal_surface_area({"agents_can_affect": 4, "expected_divergence": 6,
                                  "lighting_sensitivity": 8, "reconstruction_sensitivity": 7})
    prepared = prepare_branches(g, "intact", csa, budget)
    print("Representation Futures Graph — prepare branches, never select")
    print("  prepared %d possible branches (breadth preserved): %s" % (len(prepared), sorted(t for t, _ in prepared)))
    # CORE later commits a truth correction; the prepared representation survives it
    for outcome in ("damaged", "destroyed"):
        state, cost = survive_truth_correction(prepared, outcome)
        print("  CORE commits '%s' → representation %s (cost %d)" % (outcome, state, cost))
    try:
        select_future("intact", "destroyed"); print("  select_future: NOT blocked (BUG)")
    except CausalAuthorityLeak:
        print("  select_future('destroyed') → blocked (prepare ≠ select; only CORE decides)")
    print("  integrity ≠ truth — the renderer was prepared, it never chose.")
    return prepared


def register():
    from .registry import REGISTRY, ALLOCATOR, LayerViolation
    try:
        REGISTRY.register("representation_futures", ALLOCATOR, mutates_core=False,
                          note="Representation Futures Graph — prepare branches by P(transition)×CSA; "
                               "select_future() forbidden (prepare ≠ select); rollback = representation survives truth")
    except LayerViolation:
        pass
