# SPDX-License-Identifier: AGPL-3.0-only
"""
light_cone_bench.py — the decisive number: how fast does a coupled edit's blast radius grow, and
when does the counterfactual win die?

Two views, deterministic op-counts as the verdict:
  TABLE 1 — vary WORLD SIZE at a fixed short horizon. Information velocity should be ~constant (set by
            coupling, not by N), so the saturation horizon GROWS with the world and the win at a fixed
            preview length gets BETTER in bigger worlds.
  TABLE 2 — vary HORIZON at a fixed world. Cone volume grows (~quadratically) until it fills the world;
            cf/naive climbs toward 100%. This locates the 'safe preview horizon'.

Honest framing: the win is now CONDITIONAL on preview length vs world diameter. A short counterfactual
in a large coupled world is cheap; a long one is not. Velocity is the invariant that decides the line.
"""
from __future__ import annotations

from cow_world import Edit, Rules, genesis
from light_cone import counterfactual_lightcone

CHUNK_SIZE = 20


def main():
    print("light_cone_bench — coupled-world blast radius & where the counterfactual win dies")
    print(f"  chunk_size={CHUNK_SIZE}  coupling=ring nearest-neighbour resource diffusion\n")

    print("  TABLE 1 — vary world size, fixed horizon=15 (velocity is ~size-independent)")
    print(f"  {'entities':>9} {'chunks':>7} {'velocity':>9} {'saturates@':>11} {'cf_cost':>9} {'naive':>9} {'cf/naive':>9}")
    print("  " + "-" * 72)
    for nc in (50, 100, 200, 400, 800):
        snap = genesis(CHUNK_SIZE * nc, nc, 0)
        r = counterfactual_lightcone(snap, Rules(), 0, Edit("cull_pred_chunk", chunk=nc // 2), horizon=15)
        sat = r.saturation_tick if r.saturation_tick >= 0 else ">15"
        print(f"  {CHUNK_SIZE*nc:>9} {nc:>7} {r.information_velocity:>9.2f} {str(sat):>11} "
              f"{r.cf_cost:>9} {r.naive_cf_cost:>9} {r.cf_cost / r.naive_cf_cost:>8.1%}")
    print()

    print("  TABLE 2 — vary horizon, fixed world (chunks=200, N=4000): the cone fills, the win dies")
    print(f"  {'horizon':>8} {'max radius':>11} {'cf_cost':>9} {'naive':>9} {'cf/naive':>9}")
    print("  " + "-" * 52)
    nc = 200
    snap = genesis(CHUNK_SIZE * nc, nc, 0)
    for H in (5, 20, 50, 100, 150):
        r = counterfactual_lightcone(snap, Rules(), 0, Edit("cull_pred_chunk", chunk=100), horizon=H)
        print(f"  {H:>8} {max(r.radius):>11} {r.cf_cost:>9} {r.naive_cf_cost:>9} "
              f"{r.cf_cost / r.naive_cf_cost:>8.1%}")
    print()

    print("  READING:")
    print("    · information velocity is ~constant (~2 chunks/tick) — set by COUPLING, not world size.")
    print("    · therefore the saturation horizon grows with world diameter: bigger worlds give a")
    print("      LONGER safe-preview window before a counterfactual costs as much as a full re-sim.")
    print("    · the win is CONDITIONAL: short previews in large coupled worlds are cheap; long previews")
    print("      are not. This is the honest replacement for cow_world's unconditional flat cost.")
    print("    · correctness under coupling is proven byte-identical in test_light_cone.py — the cost")
    print("      numbers mean something only because the reconstructed future is provably unchanged.")


if __name__ == "__main__":
    main()
