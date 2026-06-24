# SPDX-License-Identifier: AGPL-3.0-only
"""
test_teleport.py — validity-not-outcome self-test for long-range coupling + the two-layer reconstruction.

The crux is doubled: BOTH the conservative (dependency) reconstruction AND the pruned (change-propagation,
allocator) reconstruction must be byte-identical to a full honest sim of the edited coupled world — under
a teleport topology. The pruned one is the load-bearing claim: an observer that re-simulates only where
divergence is MEASURED is still correct (a chunk diverges only if an input diverged).

  1. equivalence_conservative — conservative line_b == brute (teleport topology)
  2. equivalence_pruned        — pruned line_b == brute (teleport topology)  ← the allocator is CORRECT
  3. pruned_within_conservative— ∀t pruned cone ⊆ conservative cone; pruned cost ≤ conservative cost
  4. teleport_explodes_cone    — a teleport edge enlarges the conservative (potential) cone vs ring-only
  5. teleport_transmits        — the edit's effect actually crosses the long edge (far chunk diverges)
  6. pruned_cheaper_than_naive — pruned cost < a full re-sim (structural sanity)
  7. determinism               — both reconstructions stable across runs

Run:  PYTHONHASHSEED=0 python3 test_teleport.py
"""
from __future__ import annotations

from cow_world import Edit, Rules, genesis, snapshot_hash
from teleport import Topology, brute_force_edit_future, full_sim_traced, measure, reconstruct

N_CH, CHUNK_SIZE, SEED, H = 200, 20, 0, 30
N = N_CH * CHUNK_SIZE
EDIT = Edit("cull_pred_chunk", chunk=5)
TELE = ((5, 130),)


def check(name, ok, detail):
    return (name, ok, detail)


def _world():
    return genesis(n_entities=N, n_chunks=N_CH, seed=SEED), Rules()


def test_equivalence_conservative():
    snap, rules = _world()
    topo = Topology(N_CH, TELE)
    r = reconstruct(snap, topo, rules, SEED, EDIT, H, prune=False)
    brute = brute_force_edit_future(snap, topo, rules, SEED, EDIT, H)
    ok = snapshot_hash(r.line_b) == snapshot_hash(brute)
    return check("equivalence_conservative", ok, f"conservative B == brute (teleport): {ok}")


def test_equivalence_pruned():
    snap, rules = _world()
    topo = Topology(N_CH, TELE)
    r = reconstruct(snap, topo, rules, SEED, EDIT, H, prune=True)
    brute = brute_force_edit_future(snap, topo, rules, SEED, EDIT, H)
    ok = snapshot_hash(r.line_b) == snapshot_hash(brute)
    return check("equivalence_pruned", ok, f"pruned (allocator) B == brute (teleport): {ok}")


def test_pruned_within_conservative():
    snap, rules = _world()
    topo = Topology(N_CH, TELE)
    rep = measure(snap, topo, rules, SEED, EDIT, H)
    cone_ok = all(p <= c for p, c in zip(rep.pruned.cone_count, rep.conservative.cone_count))
    cost_ok = rep.pruned.cost <= rep.conservative.cost
    return check("pruned_within_conservative", cone_ok and cost_ok,
                 f"pruned cone ⊆ conservative ∀t={cone_ok}; pruned cost {rep.pruned.cost} ≤ "
                 f"conservative {rep.conservative.cost}={cost_ok}")


def test_teleport_explodes_cone():
    snap, rules = _world()
    ring = measure(snap, Topology(N_CH), rules, SEED, EDIT, H)
    tele = measure(snap, Topology(N_CH, TELE), rules, SEED, EDIT, H)
    ok = max(tele.conservative.cone_count) > max(ring.conservative.cone_count)
    return check("teleport_explodes_cone", ok,
                 f"peak conservative cone: ring={max(ring.conservative.cone_count)} → "
                 f"teleport={max(tele.conservative.cone_count)} (larger={ok})")


def test_teleport_transmits():
    snap, rules = _world()
    topo = Topology(N_CH, TELE)
    # SAME topology, edit vs no-edit — isolates the EDIT's effect crossing the long edge from the
    # topology's own influence on line A.
    tele_a = full_sim_traced(snap, topo, rules, SEED, H)[0][H]
    tele_b = reconstruct(snap, topo, rules, SEED, EDIT, H, prune=True)
    far_diverged = tele_b.line_b[130] != tele_a[130]
    return check("teleport_transmits", far_diverged,
                 f"edit at chunk 5 reached far endpoint 130 via the long edge (same-topology A vs B): {far_diverged}")


def test_pruned_cheaper_than_naive():
    snap, rules = _world()
    rep = measure(snap, Topology(N_CH, TELE), rules, SEED, EDIT, H)
    ok = rep.pruned.cost < rep.naive_cost
    return check("pruned_cheaper_than_naive", ok,
                 f"pruned cost {rep.pruned.cost} < naive {rep.naive_cost} "
                 f"({rep.pruned.cost / rep.naive_cost:.1%})={ok}")


def test_determinism():
    snap, rules = _world()
    topo = Topology(N_CH, TELE)
    a = measure(snap, topo, rules, SEED, EDIT, H)
    b = measure(snap, topo, rules, SEED, EDIT, H)
    ok = (snapshot_hash(a.conservative.line_b) == snapshot_hash(b.conservative.line_b)
          and snapshot_hash(a.pruned.line_b) == snapshot_hash(b.pruned.line_b))
    return check("determinism", ok, f"both reconstructions stable across runs: {ok}")


def main():
    results = [
        test_equivalence_conservative(),
        test_equivalence_pruned(),
        test_pruned_within_conservative(),
        test_teleport_explodes_cone(),
        test_teleport_transmits(),
        test_pruned_cheaper_than_naive(),
        test_determinism(),
    ]
    print("test_teleport — validity-not-outcome (both reconstructions CORRECT; not 'pruning is good')\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: both the conservative (dependency) and the"
          f"\n  pruned (measured change-propagation) reconstructions are byte-identical to honest simulation,"
          f"\n  the long edge demonstrably enlarges the potential cone and transmits real divergence, and the"
          f"\n  pruned allocator stays within the conservative bound. Cost claims are meaningful only because"
          f"\n  both answers are provably unchanged.")
    assert passed == total, f"{total - passed} check(s) failed — the teleport probe is not sound"


if __name__ == "__main__":
    main()
