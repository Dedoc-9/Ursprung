# SPDX-License-Identifier: AGPL-3.0-only
"""
test_observers.py — validity-not-outcome self-test for the observer-on-fork merge.

It asserts the LENS is sound and honestly typed — never that an edit produced a "better" orbit:

  1. observer_determinism   — same fork ⇒ identical Observation (the lens is a function, not a roll)
  2. identity_zero_delta     — do(nothing) ⇒ both legs identical ⇒ orbit delta is exactly zero
  3. no_trajectory_ghost     — a FROZEN leg (enough samples, zero motion) classifies NO_TRAJECTORY,
                               NOT CONVERGED, and raises the ghost (the dead-start trap, refused)
  4. evidence_is_estimate    — an Observation is ESTIMATE, never EXACT_UNDER_MODEL (no borrowed authority)
  5. classifier_distinguishes— a moving leg classifies EXPLORING/CONVERGED, not NO_TRAJECTORY; and
                               per_leg geometry matches an independent hand recomputation

`experiment-ran ≠ hypothesis-confirmed`.  Run:  PYTHONHASHSEED=0 python3 test_observers.py
"""
from __future__ import annotations

from fork import cull_species, fork, identity
from observers import (CONVERGED, ESTIMATE, EXPLORING, NO_TRAJECTORY,
                       SETTLE_EPS, Observation, OrbitObserver)
from world import genesis


def check(name, ok, detail):
    return (name, ok, detail)


def test_observer_determinism():
    w = genesis(seed=4).run(6)
    o1 = fork(w, cull_species("predator"), horizon=25).observe(OrbitObserver())
    o2 = fork(w, cull_species("predator"), horizon=25).observe(OrbitObserver())
    return check("observer_determinism", o1 == o2,
                 f"two identical forks give identical Observation: {o1 == o2}")


def test_identity_zero_delta():
    w = genesis(seed=2).run(6)
    obs = fork(w, identity(), horizon=25).observe(OrbitObserver())
    numeric_zero = all(v == 0 for k, v in obs.delta.items() if isinstance(v, (int, float)))
    same_class = obs.leg_a["classification"] == obs.leg_b["classification"]
    return check("identity_zero_delta", numeric_zero and same_class,
                 f"do(nothing): all numeric deltas zero={numeric_zero}, classifications equal={same_class}")


def test_no_trajectory_ghost():
    ob = OrbitObserver()
    f = (5, 2, 3, 0, 7, 6, 4)               # one frozen feature vector
    frozen = (f, f, f, f, f)                 # 4 transitions (>= MIN_STEPS), but zero motion
    leg = ob.per_leg(frozen)
    is_no_traj = leg["classification"] == NO_TRAJECTORY
    not_converged = leg["classification"] != CONVERGED
    ghost = leg.get("_ghost") == NO_TRAJECTORY
    return check("no_trajectory_ghost", is_no_traj and not_converged and ghost,
                 f"frozen leg → NO_TRAJECTORY={is_no_traj} (not CONVERGED={not_converged}), ghost raised={ghost}")


def test_evidence_is_estimate():
    w = genesis(seed=8).run(6)
    obs = fork(w, cull_species("predator"), horizon=20).observe(OrbitObserver())
    return check("evidence_is_estimate",
                 obs.evidence_class == ESTIMATE and obs.evidence_class != "EXACT_UNDER_MODEL",
                 f"Observation.evidence_class == ESTIMATE: {obs.evidence_class == ESTIMATE}")


def test_classifier_distinguishes():
    ob = OrbitObserver()
    # a moving, escaping leg: steps [2, 8], path 10, displacement 10 ⇒ straightness 1.0; late_speed 8 > eps
    moving = ((0,), (2,), (10,))
    mleg = ob.per_leg(moving)
    explores = mleg["classification"] == EXPLORING
    # independent hand recomputation of the geometry
    straight_ok = abs(mleg["straightness"] - 1.0) < 1e-9
    path_ok = mleg["path_length"] == 10.0 and mleg["displacement"] == 10.0
    late_ok = mleg["late_speed"] > SETTLE_EPS
    return check("classifier_distinguishes", explores and straight_ok and path_ok and late_ok,
                 f"moving leg→EXPLORING={explores}; geometry matches hand-calc "
                 f"(straightness={mleg['straightness']}, path={mleg['path_length']}, late={mleg['late_speed']})")


def main():
    results = [
        test_observer_determinism(),
        test_identity_zero_delta(),
        test_no_trajectory_ghost(),
        test_evidence_is_estimate(),
        test_classifier_distinguishes(),
    ]
    print("test_observers — validity-not-outcome (the lens is sound + honestly typed; not 'edit was good')\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. The observer merge is REAL iff this is {total}/{total}: a lens that"
          f"\n  is deterministic, zero on the null edit, refuses to call an unmoved world 'converged', and"
          f"\n  is typed ESTIMATE so it can never borrow the authority of an exact-under-model delta.")
    assert passed == total, f"{total - passed} check(s) failed — observer slice is not yet real"


if __name__ == "__main__":
    main()
