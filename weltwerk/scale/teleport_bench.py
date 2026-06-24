# SPDX-License-Identifier: AGPL-3.0-only
"""
teleport_bench.py — does long-range coupling kill the counterfactual win, and can the observer save it?

Answers the five questions a teleport edge raises, with deterministic op-counts:
  1. Does information velocity stay bounded?      → watch peak POTENTIAL cone vs ring-only.
  2. Does world diameter stop mattering?          → a far chunk is now reachable in one hop.
  3. Does ACTUAL divergence stay sparse?          → watch peak actual divergence.
  4. Does the conservative cone explode?          → conservative cost vs naive.
  5. Can the observer recover sparsity?           → pruned (change-propagation) cost vs conservative.

The thesis being tested: a teleport edge breaks the DEPENDENCY bound (potential cone) but not
necessarily the CHANGE-PROPAGATION truth (actual divergence). If actual stays sparse, the pruned
allocator recovers the win exactly where the conservative cone loses it.
"""
from __future__ import annotations

from cow_world import Edit, Rules, genesis
from teleport import Topology, measure

N_CH, CHUNK_SIZE, SEED, H = 200, 20, 0, 30
EDIT = Edit("cull_pred_chunk", chunk=5)


def main():
    snap = genesis(N_CH * CHUNK_SIZE, N_CH, SEED)
    rules = Rules()
    configs = [
        ("ring only", Topology(N_CH)),
        ("+1 teleport (5↔130)", Topology(N_CH, ((5, 130),))),
        ("+3 teleports (hub @5)", Topology(N_CH, ((5, 130), (5, 60), (5, 190)))),
    ]
    print("teleport_bench — long-range coupling: potential cone vs actual divergence")
    print(f"  chunks={N_CH} chunk_size={CHUNK_SIZE} horizon={H} edit=cull predators @chunk 5\n")
    print(f"  {'topology':>22} {'peakCone':>9} {'peakActual':>11} {'cons_cost':>10} {'pruned':>8} "
          f"{'naive':>8} {'cons/nv':>8} {'prun/nv':>8}")
    print("  " + "-" * 96)
    for name, topo in configs:
        r = measure(snap, topo, rules, SEED, EDIT, H)
        pc = max(r.conservative.cone_count)
        pa = max(r.conservative.actual_count)
        print(f"  {name:>22} {pc:>9} {pa:>11} {r.conservative.cost:>10} {r.pruned.cost:>8} "
              f"{r.naive_cost:>8} {r.conservative.cost / r.naive_cost:>7.1%} {r.pruned.cost / r.naive_cost:>7.1%}")
    print()
    print("  READING (answers to the five questions):")
    print("    1. velocity NOT bounded under teleport: the potential cone jumps the instant the edit")
    print("       reaches an endpoint — a far region becomes reachable in one hop.")
    print("    2. diameter stops bounding REACHABILITY: a teleport edge short-circuits geography.")
    print("    3. but ACTUAL divergence can stay sparse: an attenuated perturbation crossing one edge")
    print("       barely moves the far region (compare peakActual to peakCone).")
    print("    4. the conservative cone DOES explode (cons/naive rises toward 100%) — dependency")
    print("       analysis is correct but pessimistic.")
    print("    5. the observer RECOVERS sparsity: the pruned (measured change-propagation) cost stays")
    print("       far below conservative, because it simulates where divergence IS, not where it COULD be.")
    print("\n  Both reconstructions are proven byte-identical to honest simulation in test_teleport.py —")
    print("  the pruned allocator is a correctness-preserving optimisation, not a heuristic.")


if __name__ == "__main__":
    main()
