# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/causal_surface.py — Causal Surface Area: how many futures depend on an object (the multiplayer axis).

A solo renderer asks "where will fidelity fail?" A multiplayer renderer must also ask "where can independent
futures collide?" The new quantity is not complexity — it is **how many possible futures depend on an
object**:

    Causal Surface Area (Shared Transition Pressure)
        = agents_that_can_affect  ×  expected_state_divergence  ×  representation_cost

A shared object (a wall two players can both reach and affect) is a *convergence point for multiple
trajectories*; it deserves representation readiness because multiple futures may collapse onto it — not
because it is visually important.

THE MOAT (the invariant this module exists to protect): **the renderer forecasts REPRESENTATIONS, never
REALITY.** It may prepare the *possible* future representations of an object (destruction assets, particle
systems, animation states, shaders) BEFORE an action resolves; it may never assert the OUTCOME.

    "this wall has high transition cost if it changes → prepare destruction representation"   ALLOWED
    "this wall WILL break because Player A is shooting it"                                     FORBIDDEN

The first is a representation forecast (preparation). The second turns prediction into authority — only the
simulation (CORE) decides whether the wall breaks. The renderer should never become prophetic; it should
become better prepared.

CLASSIFICATION: OBSERVER (mutates_core=False). It counts possible futures and ranks objects for *preparation*;
it allocates readiness, never commits world state, and asserts no outcome. `observation → allocation`, never
`observation → truth`. integrity ≠ truth.
"""
from __future__ import annotations

from . import resistance_tensor as rt


def causal_surface_area(obj):
    """How many futures depend on this object. agents × expected_divergence × representation_cost. A shared,
    contested, expensive-to-rebuild object scores high — independent of how visible it is."""
    agents = max(1, int(obj.get("agents_can_affect", 1)))
    divergence = max(1, int(obj.get("expected_divergence", 1)))   # expected state spread if agents act
    rep_cost = rt.miss_cost(obj)                                  # cost of being unprepared (resistance tensor)
    return agents * divergence * rep_cost


# alias — the same quantity, named for the multiplayer framing
shared_transition_pressure = causal_surface_area


# --- the prepare-≠-decide guard (the moat, mechanical) ----------------------------------------------

class ProphecyViolation(Exception):
    """Raised when the renderer tries to forecast REALITY (assert an outcome) rather than a REPRESENTATION."""


class Forecast:
    """A forecast is admissible iff it PREPARES a representation and does NOT commit an outcome."""
    __slots__ = ("target", "prepares_representation", "commits_outcome", "detail")

    def __init__(self, target, prepares_representation=False, commits_outcome=False, detail=""):
        self.target = target
        self.prepares_representation = prepares_representation
        self.commits_outcome = commits_outcome
        self.detail = detail

    def admissible(self):
        return self.prepares_representation and not self.commits_outcome


def representation_forecast(target, representation):
    """ALLOWED: prepare a possible future representation for `target` (e.g. destruction assets, a shader)."""
    return Forecast(target, prepares_representation=True, commits_outcome=False,
                    detail="prepare '%s' for %s" % (representation, target))


def reality_forecast(target, outcome):
    """FORBIDDEN: assert an OUTCOME. The renderer must not decide what becomes true — that is the simulation's
    authority. Constructing one is fine for classification; asserting it via `assert_prepared` fails closed."""
    return Forecast(target, prepares_representation=False, commits_outcome=True,
                    detail="assert outcome '%s' for %s" % (outcome, target))


def assert_prepared(forecast):
    """Fail closed on a reality forecast. Readiness systems route every forecast through this."""
    if not forecast.admissible():
        raise ProphecyViolation(
            "reality forecast rejected (%s): the renderer prepares representations, it never decides outcomes"
            % forecast.detail)
    return forecast


# --- multiplayer artifact classification (different layers, not one bucket) -------------------------

def classify_multiplayer_artifact(kind):
    """Route a multiplayer artifact to the correct layer — the mistake is treating prediction error as a
    world error. (visual snap → perceptual ghost; bad hit result → CORE/network; missing shader → rep debt.)"""
    return {
        "visual_snap": ("perceptual_ghost", "VIEW — smoothing/reconciliation, never a world error"),
        "rubber_band": ("perceptual_ghost", "VIEW — interpolation correction from CORE"),
        "incorrect_hit": ("core_network", "CORE — authority/netcode, NOT a renderer concern"),
        "missing_destruction_shader": ("representation_debt", "ALLOCATOR — prepare the representation earlier"),
        "lod_pop": ("representation_debt", "ALLOCATOR — readiness / transition debt"),
    }.get(kind, ("unclassified", "investigate"))


# --- bench: CSA vs proximity/visibility for readiness on shared objects -----------------------------

def _scene(n=40, seed=1):
    import random
    rng = random.Random(seed)
    objs = {}
    for i in range(n):
        # one class of objects is SHARED+contested (high CSA) but far/low-visibility (proximity/vis miss them)
        shared = (i % 7 == 0)
        objs["o%02d" % i] = {
            "id": "o%02d" % i,
            "agents_can_affect": rng.randint(2, 5) if shared else 1,
            "expected_divergence": rng.randint(4, 9) if shared else rng.randint(1, 2),
            "lighting_sensitivity": rng.randint(6, 9) if shared else rng.randint(1, 3),
            "reconstruction_sensitivity": rng.randint(5, 9) if shared else rng.randint(1, 3),
            "distance": rng.randint(70, 100) if shared else rng.randint(1, 60),   # shared objects are FAR
            "visibility": rng.randint(1, 20) if shared else rng.randint(40, 100), # ...and low on-screen
            "will_change": shared,    # the future collapses onto the shared objects (CORE decides this; bench truth)
        }
    return objs


def _hamilton(weights, budget):
    keys = sorted(weights); tot = sum(max(0, weights[k]) for k in keys)
    if budget <= 0 or not keys:
        return {k: 0 for k in keys}
    if tot == 0:
        base, rem = divmod(budget, len(keys)); return {k: base + (1 if i < rem else 0) for i, k in enumerate(keys)}
    raw = {k: max(0, weights[k]) * budget / tot for k in keys}; fl = {k: int(raw[k]) for k in keys}
    for k in sorted(keys, key=lambda k: (-(raw[k] - fl[k]), k))[:budget - sum(fl.values())]:
        fl[k] += 1
    return fl


def run(seed=1, budget=400):
    objs = _scene(seed=seed)
    # readiness debt = for objects that CHANGE (future collapses onto them), the unprepared cost:
    #   miss_cost × (1 - prepared_fraction). Lower = better prepared where futures actually converged.
    def debt(alloc):
        tot = 0
        for oid, o in objs.items():
            if o["will_change"]:
                got = alloc.get(oid, 0)
                prepared = min(1.0, got / 30.0)            # 30 units = fully prepared
                tot += int(rt.miss_cost(o) * (1.0 - prepared))
        return tot
    pol = {
        "proximity": lambda o: max(1, 1_000_000 // (o["distance"] + 1)),
        "visibility": lambda o: o["visibility"],
        "causal_surface_area": lambda o: causal_surface_area(o),
    }
    return {name: debt(_hamilton({oid: wf(o) for oid, o in objs.items()}, budget)) for name, wf in pol.items()}


def demo(seed=1, budget=400):
    res = run(seed=seed, budget=budget)
    print("Causal Surface Area — readiness for SHARED objects (futures collapse onto them), budget=%d" % budget)
    print("  metric = unprepared representation debt where futures actually converged (lower better)\n")
    for name in ("proximity", "visibility", "causal_surface_area"):
        tag = "  ← counts how many futures depend on the object" if name == "causal_surface_area" else ""
        print("  %-22s %d%s" % (name, res[name], tag))
    best = min(res, key=lambda k: res[k])
    print("\n  best readiness signal: %s" % best)
    print("  forecast guard: prepare representations (ALLOWED), never assert outcomes (FORBIDDEN).")
    print("  Honest bound: constructed world; CSA ranks PREPARATION, never decides the future. integrity ≠ truth.")
    return res


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("causal_surface", OBSERVER, mutates_core=False,
                          note="Causal Surface Area = agents × divergence × representation_cost; ranks objects "
                               "for PREPARATION (representation forecast), never asserts outcomes (prepare ≠ decide)")
    except LayerViolation:
        pass
