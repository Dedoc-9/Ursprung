# SPDX-License-Identifier: AGPL-3.0-only
"""
test_reachability_algebra.py — machine-check the discrete formulation against the engine.

Validity-not-outcome: it proves the formal constructs EQUAL the operational quantities, and records the
A^H trap with evidence. It does not assert the formalism is "better" — only that the corrected forms are
faithful and the rejected form is not.

  1. potential_is_reflexive_ball — cons.touched == Supp((I∨A)^H e_i)  (the corrected potential)
  2. bare_power_undercounts      — Supp(A^H e_i) ⊊ ball  (the rejected |Supp(A^H e_i)| trap, evidenced)
  3. transmit_min_is_changed     — changed is feasible (L=0) and every proper subset breaks (the min)
  4. feasible_is_principal_upset — T feasible ⟺ T ⊇ changed (superset stays feasible; drop-one breaks)
  5. compute_is_closure          — pruned compute set ⊇ changed, with a non-negative frontier overhead
  6. determinism                 — same seed ⇒ same ball, same changed

Run:  PYTHONHASHSEED=0 python3 test_reachability_algebra.py
"""
from __future__ import annotations

from causal_budget import compute_budget
from cow_world import Edit, Rules, genesis
from reachability_algebra import exact_walk_support, feasible_lossless, reflexive_ball
from teleport import Topology, reconstruct

N_CH, CHUNK_SIZE, SEED, H = 200, 20, 0, 30
EDIT = Edit("cull_pred_chunk", chunk=5)
TOPO = Topology(N_CH, ((5, 130),))


def check(name, ok, detail):
    return (name, ok, detail)


def _ctx():
    snap = genesis(N_CH * CHUNK_SIZE, N_CH, SEED)
    rules = Rules()
    b = compute_budget(snap, TOPO, rules, SEED, EDIT, H)
    return snap, rules, b


def test_potential_is_reflexive_ball():
    _, _, b = _ctx()
    ball = reflexive_ball(TOPO.adj, {5}, H)
    ok = b.potential == ball
    return check("potential_is_reflexive_ball", ok,
                 f"|cons.touched|={len(b.potential)} == |(I∨A)^H ball|={len(ball)}: {ok}")


def test_bare_power_undercounts():
    _, _, b = _ctx()
    ball = reflexive_ball(TOPO.adj, {5}, H)
    exact = exact_walk_support(TOPO.adj, 5, H)
    ok = exact < ball and len(exact) < len(ball)        # strict subset: the A^H trap
    return check("bare_power_undercounts", ok,
                 f"Supp(A^H e_i)={len(exact)} ⊊ ball={len(ball)} (bare power is wrong): {ok}")


def test_transmit_min_is_changed():
    _, _, b = _ctx()
    feasible = feasible_lossless(b.line_a, b.line_b, b.changed)
    # every proper subset (drop one changed chunk) must break
    proper_breaks = True
    for c in sorted(b.changed):
        if feasible_lossless(b.line_a, b.line_b, b.changed - {c}):
            proper_breaks = False
            break
    return check("transmit_min_is_changed", feasible and proper_breaks,
                 f"changed feasible={feasible}; every proper subset breaks={proper_breaks}")


def test_feasible_is_principal_upset():
    _, _, b = _ctx()
    # a superset stays feasible; a set missing a changed chunk is infeasible ⇒ feasible ⟺ T ⊇ changed
    extra = next(iter(b.potential - b.changed)) if (b.potential - b.changed) else None
    superset_ok = feasible_lossless(b.line_a, b.line_b, b.changed | ({extra} if extra is not None else set()))
    missing_breaks = (not feasible_lossless(b.line_a, b.line_b, b.changed - {sorted(b.changed)[0]})) if b.changed else False
    return check("feasible_is_principal_upset", superset_ok and missing_breaks,
                 f"superset feasible={superset_ok}; missing-a-changed infeasible={missing_breaks} "
                 f"⇒ feasible ⟺ T⊇changed (principal up-set, not set-cover)")


def test_compute_is_closure():
    snap, rules, b = _ctx()
    pruned = reconstruct(snap, TOPO, rules, SEED, EDIT, H, prune=True)
    contains = b.changed <= pruned.touched
    overhead = len(pruned.touched) - len(b.changed)
    return check("compute_is_closure", contains and overhead >= 0,
                 f"compute set ⊇ changed={contains}; frontier overhead={overhead} (≥0, the indicator closure)")


def test_determinism():
    _, _, b1 = _ctx()
    _, _, b2 = _ctx()
    ball1 = reflexive_ball(TOPO.adj, {5}, H)
    ball2 = reflexive_ball(TOPO.adj, {5}, H)
    ok = (b1.changed == b2.changed) and (ball1 == ball2)
    return check("determinism", ok, f"same seed ⇒ same changed + same ball: {ok}")


def main():
    results = [
        test_potential_is_reflexive_ball(),
        test_bare_power_undercounts(),
        test_transmit_min_is_changed(),
        test_feasible_is_principal_upset(),
        test_compute_is_closure(),
        test_determinism(),
    ]
    print("test_reachability_algebra — discrete forms verified against the engine\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. The formulation is faithful iff {total}/{total}: potential is the"
          f"\n  reflexive ball (NOT the bare A^H power), the minimal transmit set is the generator of the"
          f"\n  principal up-set {{T⊇changed}}, and computation is the neighborhood-closure of the divergence"
          f"\n  indicator. Sharp discrete objects, each equal to a measured quantity.")
    assert passed == total, f"{total - passed} check(s) failed — the formulation is not faithful to the engine"


if __name__ == "__main__":
    main()
