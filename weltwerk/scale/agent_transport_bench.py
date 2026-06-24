# SPDX-License-Identifier: AGPL-3.0-only
"""
agent_transport_bench.py — the verdict: does the sparsity that powered every cheap result survive
identities moving?

Reports the divergence trajectory and the sparsity ratio under transport, at several horizons, and
states the verdict plainly. Reference point: under resource DIFFUSION the ratio was ~0.08 (sparse) — the
attenuation that made the pruned allocator cheap. Transport carries full state with no attenuation, so
this is where it could collapse.

  sparsity = peak_actual / peak_cone
    ≪ 1  → SPARSE: the win survives transport; divergence-aware allocation/replication stays cheap.
    ≈ 1  → DENSE:  the economic thesis FAILS under transport (pruned ≈ conservative). Correctness is
                   untouched (reconstruction stays exact) — only the cost advantage dies.
Either outcome updates SCOPE.md honestly; neither is spun.
"""
from __future__ import annotations

from agent_transport import naive_cost, reconstruct
from cow_world import Edit, Rules, genesis

N_CH, CHUNK_SIZE, SEED = 200, 20, 0
EDIT = Edit("cull_pred_chunk", chunk=5)


def main():
    snap = genesis(N_CH * CHUNK_SIZE, N_CH, SEED)
    rules = Rules()
    print("agent_transport_bench — does divergence stay sparse when identities MOVE?")
    print(f"  chunks={N_CH} chunk_size={CHUNK_SIZE} edit=cull predators @5  coupling=rightward migration\n")
    print(f"  {'horizon':>8} {'peakCone':>9} {'peakActual':>11} {'sparsity':>9} "
          f"{'pruned':>8} {'conservative':>13} {'naive':>8} {'prun/cons':>10}")
    print("  " + "-" * 84)
    last = None
    for H in (10, 20, 40, 80):
        pru = reconstruct(snap, rules, SEED, EDIT, H, prune=True)
        cons = reconstruct(snap, rules, SEED, EDIT, H, prune=False)
        nv = naive_cost(snap, H)
        spar = pru.peak_actual / cons.peak_cone if cons.peak_cone else 0.0
        print(f"  {H:>8} {cons.peak_cone:>9} {pru.peak_actual:>11} {spar:>9.2f} "
              f"{pru.cost:>8} {cons.cost:>13} {nv:>8} {pru.cost / cons.cost:>9.1%}")
        last = spar
    print()
    print("  REFERENCE: resource diffusion gave sparsity ~0.08 (attenuating) — that is what made the")
    print("  pruned allocator cheap. Transport carries full state with no attenuation.")
    print()
    if last is None:
        verdict = "no data"
    elif last < 0.5:
        verdict = ("SPARSE — divergence stays local even under transport. The economic thesis SURVIVES "
                   "moving identities; divergence-aware allocation/replication remains cheap.")
    else:
        verdict = ("DENSE — transport spreads divergence across the cone (pruned ≈ conservative). The "
                   "ECONOMIC thesis FAILS for transport-dominated worlds. Correctness is untouched "
                   "(reconstruction stays byte-identical); only the cost advantage dies. SCOPE updates: "
                   "'sparsity persists under agent transport' moves from Unknown to a measured NO.")
    print(f"  VERDICT (sparsity≈{last:.2f}): {verdict}")


if __name__ == "__main__":
    main()
