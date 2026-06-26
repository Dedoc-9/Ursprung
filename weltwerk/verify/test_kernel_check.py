# SPDX-License-Identifier: AGPL-3.0-only
"""
test_kernel_check.py — validity-not-outcome proofs for the bounded model checker.

These assert the APPARATUS is sound, not that a particular world is "good":
  1. closes_within_bound        — on a tiny world the frontier empties ⇒ status CLOSED (exhaustive)
  2. potential_superset_actual  — the central law actual ⊆ potential holds on every transition
  3. state_invariants_hold      — health/dead/controller invariants never violated on a valid world
  4. counterexample_found       — a deliberately-false invariant yields the SHORTEST ghost trace
  5. ghost_replays_faithfully   — the ghost path, replayed on a fresh world, reproduces the violation
  6. determinism                — two runs give identical status / states / transitions
  7. potential_ge_actual        — reported Potential bound ≥ states explored (Actual)
  8. bounded_is_underdetermined — a too-shallow bound reports BOUNDED, not a false CLOSED/proof

Run:  python3 test_kernel_check.py
"""
from __future__ import annotations

from kernel_check import check, replay_path, DEFAULT_INVARIANTS
from world_sim import DEMO_WORLD

SMALL = """
world "T"
entity faction_a:
  position 0 0 0
  controls hub
entity hub:
  position 1 0 0
  health 10
  powers leaf
entity leaf:
  position 2 0 0
  health 10
"""

NEVER_DESTROYED = {"nothing_ever_destroyed":
                   lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime)}


def chk(name, ok, detail):
    return (name, ok, detail)


def test_closes_within_bound():
    r = check(SMALL, max_depth=8)
    ok = r.status == "CLOSED" and r.states_explored > 1 and not r.truncated
    return chk("closes_within_bound", ok, f"{r.status}, {r.states_explored} states, truncated={r.truncated}")


def test_potential_superset_actual():
    r = check(SMALL, max_depth=8)
    ok = not any(v.invariant == "potential_superset_actual" for v in r.violations)
    return chk("potential_superset_actual", ok, f"transition-law violations: "
               f"{[v.invariant for v in r.violations] or 'none'}")


def test_state_invariants_hold():
    r = check(SMALL, max_depth=8)
    ok = r.status == "CLOSED" and not r.violations
    names = set(DEFAULT_INVARIANTS)
    return chk("state_invariants_hold", ok, f"checked {sorted(names)} over {r.states_explored} states: "
               f"{'all hold' if ok else r.status}")


def test_counterexample_found():
    r = check(SMALL, max_depth=3, invariants=NEVER_DESTROYED)
    g = r.ghost
    ok = (r.status == "VIOLATED" and g is not None and len(g.path) == 1 and g.path[0][0] == "destroy")
    return chk("counterexample_found", ok,
               f"{r.status}; shortest ghost = {g.path if g else None}")


def test_ghost_replays_faithfully():
    r = check(SMALL, max_depth=3, invariants=NEVER_DESTROYED)
    g = r.ghost
    ok = g is not None and replay_path(SMALL, g.path) == g.sig
    return chk("ghost_replays_faithfully", ok,
               f"replay(ghost.path) reproduces violating state: {ok}")


def test_determinism():
    a = check(SMALL, max_depth=8)
    b = check(SMALL, max_depth=8)
    ok = (a.status, a.states_explored, a.transitions) == (b.status, b.states_explored, b.transitions)
    return chk("determinism", ok, f"({a.status},{a.states_explored},{a.transitions}) twice: {ok}")


def test_potential_ge_actual():
    r = check(SMALL, max_depth=8)
    ok = r.potential_bound >= r.states_explored
    return chk("potential_ge_actual", ok,
               f"Potential {r.potential_bound} ≥ Actual {r.states_explored}")


def test_bounded_is_underdetermined():
    r = check(DEMO_WORLD, max_depth=1)
    ok = r.status == "BOUNDED" and r.truncated and not r.violations
    return chk("bounded_is_underdetermined", ok,
               f"shallow bound ⇒ {r.status} (truncated={r.truncated}); not a false proof")


def main():
    results = [
        test_closes_within_bound(),
        test_potential_superset_actual(),
        test_state_invariants_hold(),
        test_counterexample_found(),
        test_ghost_replays_faithfully(),
        test_determinism(),
        test_potential_ge_actual(),
        test_bounded_is_underdetermined(),
    ]
    print("test_kernel_check — bounded model checker over the causal kernel (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: closed exploration is exhaustive "
          f"(= proof),\n  the actual ⊆ potential law holds on every transition, ghosts are shortest and "
          f"replayable,\n  and a shallow bound honestly reports BOUNDED rather than a false CLOSED. "
          f"closed = proof; depth-limited ≠ proof.")
    assert passed == total, f"{total - passed} check(s) failed — the model checker is not sound"


if __name__ == "__main__":
    main()
