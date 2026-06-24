# SPDX-License-Identifier: AGPL-3.0-only
"""
test_cow.py — validity-not-outcome self-test for the scaling probe.

The CRUX is correctness, not speed: the cheap counterfactual-by-difference must reconstruct the same
future as a full honest simulation of the edited world — byte-identical. If that fails, every cost
number the bench prints is meaningless. (The cheaper mechanism may not change the answer.)

It asserts the apparatus is sound and the cost STRUCTURE is what we claim — never that an edit was
"good" or that "scaling is achieved":

  1. equivalence_local   — by-difference line_b == brute-force full sim of the edited world (LOCAL edit)
  2. equivalence_global  — same identity holds for a GLOBAL rules edit (dirty = all chunks)
  3. fork_is_O1          — COW fork_cost == 0; clone fork_cost == N (the thing COW removes)
  4. locality            — a local edit makes exactly ONE chunk dirty; actual diffs ⊆ dirty
  5. boundary_global     — a global edit makes ALL chunks dirty and cf_cost == naive (the win VANISHES,
                           correctly — coupling defeats locality)
  6. determinism         — same seed ⇒ identical line_a / line_b hashes

Run:  PYTHONHASHSEED=0 python3 test_cow.py
"""
from __future__ import annotations

from cow_world import (Edit, Rules, brute_force_edit_future, counterfactual,
                       genesis, snapshot_hash)


def check(name, ok, detail):
    return (name, ok, detail)


N, CHUNKS, H, SEED = 2000, 50, 20, 0


def _world():
    return genesis(n_entities=N, n_chunks=CHUNKS, seed=SEED), Rules()


def test_equivalence_local():
    snap, rules = _world()
    edit = Edit("cull_pred_chunk", chunk=7)
    r = counterfactual(snap, rules, SEED, edit, H)
    brute = brute_force_edit_future(snap, rules, SEED, edit, H)
    ok = snapshot_hash(r.line_b) == snapshot_hash(brute)
    return check("equivalence_local", ok,
                 f"by-difference B == full honest sim of edited world (LOCAL): {ok}")


def test_equivalence_global():
    snap, rules = _world()
    edit = Edit("set_rule", rule_field="predation_enabled", rule_value=False)
    r = counterfactual(snap, rules, SEED, edit, H)
    brute = brute_force_edit_future(snap, rules, SEED, edit, H)
    ok = snapshot_hash(r.line_b) == snapshot_hash(brute)
    return check("equivalence_global", ok,
                 f"by-difference B == full honest sim (GLOBAL rules edit): {ok}")


def test_fork_is_O1():
    snap, rules = _world()
    r = counterfactual(snap, rules, SEED, Edit("cull_pred_chunk", chunk=3), H)
    ok = (r.fork_cost_cow == 0) and (r.fork_cost_clone == N)
    return check("fork_is_O1", ok,
                 f"cow fork_cost={r.fork_cost_cow} (O(1)); clone fork_cost={r.fork_cost_clone} (=N)")


def test_locality():
    snap, rules = _world()
    r = counterfactual(snap, rules, SEED, Edit("cull_pred_chunk", chunk=12), H)
    one_dirty = len(r.dirty) == 1
    diffs_subset = set(r.diff_chunks()) <= set(r.dirty)
    cheaper = r.cf_cost < r.naive_cf_cost     # structural: dirty ⊊ all chunks ⇒ fewer entity-steps
    return check("locality", one_dirty and diffs_subset and cheaper,
                 f"dirty={sorted(r.dirty)} (one chunk={one_dirty}); diffs⊆dirty={diffs_subset}; "
                 f"cf_cost {r.cf_cost} < naive {r.naive_cf_cost} ({r.cf_cost / r.naive_cf_cost:.1%})")


def test_boundary_global():
    snap, rules = _world()
    r = counterfactual(snap, rules, SEED, Edit("set_rule", rule_field="regen_rate", rule_value=0), H)
    all_dirty = len(r.dirty) == CHUNKS
    no_win = r.cf_cost == r.naive_cf_cost
    return check("boundary_global", all_dirty and no_win,
                 f"global edit ⇒ all {CHUNKS} chunks dirty={all_dirty}; cf_cost==naive (no win)={no_win}")


def test_determinism():
    snap, rules = _world()
    edit = Edit("cull_pred_chunk", chunk=5)
    r1 = counterfactual(snap, rules, SEED, edit, H)
    r2 = counterfactual(snap, rules, SEED, edit, H)
    ok = (snapshot_hash(r1.line_a) == snapshot_hash(r2.line_a)
          and snapshot_hash(r1.line_b) == snapshot_hash(r2.line_b))
    return check("determinism", ok, f"identical line_a and line_b across runs: {ok}")


def main():
    results = [
        test_equivalence_local(),
        test_equivalence_global(),
        test_fork_is_O1(),
        test_locality(),
        test_boundary_global(),
        test_determinism(),
    ]
    print("test_cow — validity-not-outcome (the cheap mechanism is CORRECT; not 'scaling is good')\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:20s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. The probe is sound iff this is {total}/{total}: by-difference"
          f"\n  reconstruction is byte-identical to honest full simulation, the fork is O(1), effects are"
          f"\n  local, and the win correctly VANISHES under a global edit. Cost numbers are only meaningful"
          f"\n  because the answer is provably unchanged.")
    assert passed == total, f"{total - passed} check(s) failed — the scaling probe is not sound"


if __name__ == "__main__":
    main()
