# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/trajectory.py — motion through confidence space (a coordinate moves; the motion is the story).

`ledgers.py` made confidence a coordinate `(integrity, adequacy)` with four quadrants instead of a scalar. Two
consequences follow, and a third object falls out naturally.

1. **The coordinate allocates work.** Each quadrant implies a different next action — the position is not merely
   descriptive, it is a recommendation:

       accounted_and_supported   → preserve, extend, stress-test
       reproducible_error        → challenge the assumptions / model
       under_documented_success  → improve provenance / accounting
       neither                   → gather evidence before investing effort

2. **A coordinate has no total order.** A scalar imposes `0.95 > 0.75`; a coordinate does not. `A = (1.0, 0.2)`
   and `B = (0.2, 1.0)` are Pareto-**incomparable** — "which is better?" is unanswerable without naming a goal
   (auditability favours `A`, correspondence favours `B`, scientific maturity favours neither). So a ranking
   problem has become a **geometry** problem: dominance is partial, and the goal picks the axis.

3. **The dispute is often about the direction of motion, not the point.** A hypothesis with weak evidence but
   rapidly accumulating support, a reproducible result whose adequacy is steadily declining, a rumor becoming
   documented, a mature theory entering crisis — these are not positions, they are **vectors**:

       state    = (integrity, adequacy)
       velocity = (Δintegrity, Δadequacy)

   And the path matters: `rumor → under_documented_success → accounted_and_supported` and `rumor →
   reproducible_error` can share the *same net integrity gain* yet be completely different events — the first
   earned its accounting on top of real support; the second hardened a wrong answer. A static coordinate cannot
   tell them apart; a trajectory can. Note especially that **crisis is declining adequacy regardless of
   integrity** — a perfectly reproducible result can be entering crisis; integrity does not shield against it.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: the velocity and motion labels are kinematic
bookkeeping over the two ledgers — they describe *what is happening to a claim's coordinate*, not why, and they
inherit the toy adequacy axis of `ledgers.py` (`simulation ≠ physics`). The classifier names the direction; it
does not certify the cause of the motion. Separators: position ≠ ranking (a coordinate has no total order);
integrity-gain ≠ progress (the destination quadrant decides); reproducible ≠ safe-from-crisis.
"""
from __future__ import annotations

from . import ledgers

# Each quadrant implies a different next action — the coordinate allocates work, it does not merely describe.
ACTION = {
    "accounted_and_supported": "preserve, extend, stress-test",
    "reproducible_error": "challenge the assumptions / model",
    "under_documented_success": "improve provenance / accounting",
    "neither": "gather evidence before investing effort",
}

_EPS = 0.05  # the dead-band below which a component of motion counts as "flat"


def recommended_action(integrity, adequacy):
    """The position is a recommendation: which quadrant you are in dictates what to do next."""
    return ACTION[ledgers.quadrant(integrity, adequacy)]


def velocity(state0, state1):
    """The vector between two coordinates: (Δintegrity, Δadequacy). The motion, not the point."""
    return (round(state1[0] - state0[0], 3), round(state1[1] - state0[1], 3))


def dominates(a, b):
    """Pareto dominance: a is at least as good on both axes and strictly better on one. A *partial* order."""
    return a[0] >= b[0] and a[1] >= b[1] and (a[0] > b[0] or a[1] > b[1])


def incomparable(a, b):
    """Neither dominates the other — the case a scalar hides by forcing a ranking."""
    return a != b and not dominates(a, b) and not dominates(b, a)


def better_for_goal(a, b, goal):
    """Ranking requires a declared goal; the coordinate alone does not order. Returns 'A' / 'B' / 'tie' /
    'incomparable'."""
    if goal == "auditability":      # only integrity matters
        return "A" if a[0] > b[0] else "B" if b[0] > a[0] else "tie"
    if goal == "correspondence":    # only adequacy matters
        return "A" if a[1] > b[1] else "B" if b[1] > a[1] else "tie"
    # "maturity" wants both — it is Pareto, and may leave the pair incomparable
    if incomparable(a, b):
        return "incomparable"
    return "A" if dominates(a, b) else "B" if dominates(b, a) else "tie"


def classify_motion(v):
    """Name the vector. Crisis (declining adequacy) takes priority and is independent of integrity."""
    di, da = v
    if da < -_EPS:
        return "entering_crisis"                       # adequacy falling — regardless of how reproducible it is
    if di > _EPS and da > _EPS:
        return "maturing"                              # both rising
    if abs(di) <= _EPS and da > _EPS:
        return "accumulating_support"                  # evidence growing, accounting flat
    if di > _EPS and abs(da) <= _EPS:
        return "becoming_documented"                   # provenance improving, adequacy flat
    return "static"


def trajectory_velocities(path):
    """Step-by-step velocity along a path of coordinates, plus the net displacement."""
    steps = [velocity(path[i], path[i + 1]) for i in range(len(path) - 1)]
    net = velocity(path[0], path[-1])
    return {"steps": steps, "net": net, "end_action": recommended_action(*path[-1])}


# --- the crucible -----------------------------------------------------------------------------------

# the two trajectories that share an integrity gain but not a destination
PATH_SUPPORTED = [(0.0, 0.05), (0.0, 0.90), (1.0, 0.90)]   # rumor → under-documented success → accounted
PATH_ERROR = [(0.0, 0.05), (1.0, 0.05)]                     # rumor → reproducible error
A, B = (1.0, 0.2), (0.2, 1.0)                               # the incomparable pair


def crucible():
    out = {}
    # the coordinate allocates work — four quadrants, four distinct actions
    out["quadrant_allocates_distinct_actions"] = len(set(ACTION.values())) == 4
    # a coordinate has no total order: A and B are Pareto-incomparable
    out["coordinates_have_no_total_order"] = incomparable(A, B)
    # ranking requires a declared goal, and the goal can flip the winner
    out["goal_decides_winner"] = (better_for_goal(A, B, "auditability") == "A"
                                  and better_for_goal(A, B, "correspondence") == "B"
                                  and better_for_goal(A, B, "maturity") == "incomparable")
    # velocity is a vector
    out["velocity_is_a_vector"] = velocity((0.0, 0.05), (0.0, 0.90)) == (0.0, 0.85)
    # same net integrity gain (+1.0), different destination quadrant → different event
    ts, te = trajectory_velocities(PATH_SUPPORTED), trajectory_velocities(PATH_ERROR)
    out["same_integrity_gain_different_destination"] = (ts["net"][0] == te["net"][0] == 1.0
                                                        and ledgers.quadrant(*PATH_SUPPORTED[-1]) != ledgers.quadrant(*PATH_ERROR[-1]))
    # the named vectors
    out["accumulating_support"] = classify_motion(velocity((0.0, 0.10), (0.0, 0.80))) == "accumulating_support"
    out["becoming_documented"] = classify_motion(velocity((0.0, 0.05), (0.90, 0.05))) == "becoming_documented"
    out["entering_crisis"] = classify_motion(velocity((1.0, 0.90), (1.0, 0.40))) == "entering_crisis"
    # crisis is declining adequacy even when integrity stays maxed — integrity does not shield against crisis
    out["crisis_independent_of_integrity"] = classify_motion(velocity((1.0, 0.90), (1.0, 0.30))) == "entering_crisis"
    # the endpoint quadrant dictates the next action
    out["endpoint_dictates_action"] = (te["end_action"] == "challenge the assumptions / model"
                                       and ts["end_action"] == "preserve, extend, stress-test")
    out["_supported"] = ts
    out["_error"] = te
    return out


def demo():
    r = crucible()
    print("Trajectory — motion through confidence space (the vector, not the point)\n")
    print("  position allocates work:")
    for q, act in ACTION.items():
        print("    %-26s → %s" % (q, act))
    print()
    print("  no total order: A=(1.0,0.2) vs B=(0.2,1.0) — incomparable; the goal picks the winner")
    print("    auditability → A · correspondence → B · maturity → neither dominates")
    print()
    print("  same +1.0 integrity gain, different destination:")
    print("    rumor → under-documented success → accounted&supported : ends '%s'" % r["_supported"]["end_action"])
    print("    rumor → reproducible error                              : ends '%s'" % r["_error"]["end_action"])
    print()
    print("  motion is the story: accumulating_support / becoming_documented / maturing / entering_crisis")
    print("  · crisis = declining adequacy even at integrity 1.0 — reproducibility does not shield: %s"
          % r["crisis_independent_of_integrity"])
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.trajectory", OBSERVER, mutates_core=False,
                          note="motion through confidence space: state=(integrity,adequacy), "
                               "velocity=(Δintegrity,Δadequacy). The coordinate allocates work (each quadrant "
                               "→ a different action); it has no total order (A=(1,.2) and B=(.2,1) are "
                               "incomparable — the goal picks the axis); the same integrity gain can reach "
                               "different destinations; and crisis is declining adequacy regardless of "
                               "integrity. position != ranking; integrity-gain != progress")
    except LayerViolation:
        pass
