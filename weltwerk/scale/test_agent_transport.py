# SPDX-License-Identifier: AGPL-3.0-only
"""
test_agent_transport.py — validity-not-outcome self-test for the transport falsifier.

It proves the apparatus is CORRECT under transport and that the edit genuinely propagates by migration —
so the sparsity number the bench reports is trustworthy. It does NOT assert sparse or dense: that is the
experiment's outcome, delivered by the bench, and either answer is informative.

  1. equivalence_pruned        — pruned line_b == brute full sim (transport)   ← the crux (correctness)
  2. equivalence_conservative  — conservative line_b == brute full sim
  3. actual_within_cone        — ∀t actual ≤ cone; pruned cost ≤ conservative cost (structural)
  4. non_vacuous_transport     — the edit diverges at source AND spreads beyond it by MIGRATION
                                 (else the probe is vacuous and the verdict is meaningless)
  5. determinism               — same seed ⇒ identical line_b

Run:  PYTHONHASHSEED=0 python3 test_agent_transport.py
"""
from __future__ import annotations

from agent_transport import brute_force_edit_future, reconstruct
from cow_world import Edit, Rules, genesis, snapshot_hash

N_CH, CHUNK_SIZE, SEED, H = 200, 20, 0, 40
EDIT = Edit("cull_pred_chunk", chunk=5)


def check(name, ok, detail):
    return (name, ok, detail)


def _world():
    return genesis(N_CH * CHUNK_SIZE, N_CH, SEED), Rules()


def test_equivalence_pruned():
    snap, rules = _world()
    r = reconstruct(snap, rules, SEED, EDIT, H, prune=True)
    brute = brute_force_edit_future(snap, rules, SEED, EDIT, H)
    ok = snapshot_hash(r.line_b) == snapshot_hash(brute)
    return check("equivalence_pruned", ok, f"pruned B == brute (transport): {ok}")


def test_equivalence_conservative():
    snap, rules = _world()
    r = reconstruct(snap, rules, SEED, EDIT, H, prune=False)
    brute = brute_force_edit_future(snap, rules, SEED, EDIT, H)
    ok = snapshot_hash(r.line_b) == snapshot_hash(brute)
    return check("equivalence_conservative", ok, f"conservative B == brute (transport): {ok}")


def test_actual_within_cone():
    snap, rules = _world()
    pru = reconstruct(snap, rules, SEED, EDIT, H, prune=True)
    cons = reconstruct(snap, rules, SEED, EDIT, H, prune=False)
    within = all(a <= c for a, c in zip(pru.actual_count, cons.cone_count))
    cheaper = pru.cost <= cons.cost
    return check("actual_within_cone", within and cheaper,
                 f"actual ≤ cone ∀t={within}; pruned cost {pru.cost} ≤ conservative {cons.cost}={cheaper}")


def test_non_vacuous_transport():
    snap, rules = _world()
    r = reconstruct(snap, rules, SEED, EDIT, H, prune=True)
    source = r.actual_count[0] >= 1
    spreads = max(r.actual_count) > 1
    return check("non_vacuous_transport", source and spreads,
                 f"edit diverges at source={source}; divergence spreads by migration "
                 f"(peak actual={max(r.actual_count)})={spreads}")


def test_determinism():
    snap, rules = _world()
    a = reconstruct(snap, rules, SEED, EDIT, H, prune=True)
    b = reconstruct(snap, rules, SEED, EDIT, H, prune=True)
    ok = snapshot_hash(a.line_b) == snapshot_hash(b.line_b)
    return check("determinism", ok, f"identical line_b across runs: {ok}")


def main():
    results = [
        test_equivalence_pruned(),
        test_equivalence_conservative(),
        test_actual_within_cone(),
        test_non_vacuous_transport(),
        test_determinism(),
    ]
    print("test_agent_transport — validity-not-outcome (apparatus correct; verdict is the bench's)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: reconstruction is byte-identical under"
          f"\n  transport, the edit genuinely propagates by migration, and the cost bound holds. Whether the"
          f"\n  divergence is SPARSE or DENSE is measured by the bench — this test does not presume it.")
    assert passed == total, f"{total - passed} check(s) failed — the transport probe is not sound"


if __name__ == "__main__":
    main()
