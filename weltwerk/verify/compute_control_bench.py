# SPDX-License-Identifier: AGPL-3.0-only
"""
compute_control_bench.py — Proof Obligation PO-6: is the learned gain real, or just more compute?

A policy that "improves" only by being allowed to search longer has learned nothing — it has been handed a
bigger budget. PO-6 controls for that. We measure, on HELD-OUT worlds, how often each policy has found a
restorer within an EQUAL budget B (B engine re-verifications), and sweep B from 1 upward:

    hit_rate(policy, B) = fraction of held-out worlds whose first restorer the policy reaches within B tries.

If the learned policy's advantage were "more compute", it would vanish at equal B. Instead we look for
**anytime dominance**: learned hit-rate ≥ baseline at *every* B, and strictly greater at small B — including
B=1, the minimum possible compute. A gain that is already present at B=1 cannot be a budget effect; it is
better *ordering* of the same candidate actions. `more-budget ≠ better-policy`; the gain is in the ranking.

This reuses the verified `rsi_bench_scale` machinery (same world generator, features, engine, BOUND) so the
control shares the apparatus it controls. The baseline is the canonical (unlearned) order; the learned order
is the mean-difference linear policy fit on TRAIN only. Held-out seeds are disjoint from TRAIN by construction.

What it does NOT claim: not that the policy generalizes beyond this world family (PO-5), not that the gain is
unbounded (it saturates — see the RSI proof doc). Only: at equal compute, the learned ordering wins. `equal-B ⇒ gain ⇒ not-compute`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from rsi_bench_scale import (gen_world, world_info, fit_learned, work,   # noqa: E402
                             _canonical, _learned, N_TRAIN)

HELD_OFFSET = 100_000     # disjoint from TRAIN seeds [0, N_TRAIN)


def run(n_train: int = N_TRAIN, n_held: int = 40) -> dict:
    train = [world_info(gen_world(s)) for s in range(n_train)]
    held = [world_info(gen_world(s)) for s in range(HELD_OFFSET, HELD_OFFSET + n_held)]
    w = fit_learned(train)

    # lazy search COST (number of engine re-verifications to the first restorer) per held world, per policy
    cost_learned = [work(i, _learned(i, w)) for i in held]
    cost_base = [work(i, _canonical(i)) for i in held]

    bmax = max(max(cost_learned), max(cost_base))
    curve = [(B, sum(c <= B for c in cost_learned), sum(c <= B for c in cost_base))
             for B in range(1, bmax + 1)]

    dominance = all(l >= b for _B, l, b in curve)            # learned never below baseline at equal budget
    strict = any(l > b for _B, l, b in curve)                # learned strictly ahead somewhere
    b1 = next((l, b) for B, l, b in curve if B == 1)         # the minimum-compute slice
    return {
        "n_held": n_held, "bmax": bmax, "curve": curve,
        "anytime_dominance": dominance, "strict_gain": strict,
        "b1_learned": b1[0], "b1_baseline": b1[1],
        "mean_cost_learned": sum(cost_learned) / len(cost_learned),
        "mean_cost_baseline": sum(cost_base) / len(cost_base),
    }


def main():
    print("compute_control_bench.py — PO-6: learned gain at EQUAL search budget (not more compute)\n")
    r = run()
    print(f"  held-out worlds: {r['n_held']}   budget sweep B=1..{r['bmax']}\n")
    print("    B   learned-hits   baseline-hits")
    for B, l, b in r["curve"]:
        mark = "  ◀ gain" if l > b else ""
        print(f"   {B:2d}      {l:3d}            {b:3d}{mark}")
    print(f"\n  anytime dominance (learned ≥ baseline ∀B): {r['anytime_dominance']}")
    print(f"  strict gain somewhere:                     {r['strict_gain']}")
    print(f"  B=1 (minimum compute): learned {r['b1_learned']} vs baseline {r['b1_baseline']} hits "
          f"— a gain at B=1 is ORDERING, not budget")
    print(f"  mean search cost: learned {r['mean_cost_learned']:.2f} vs baseline {r['mean_cost_baseline']:.2f}")
    print("\n  equal-budget gain ⇒ the improvement is better ranking of the same actions. more-budget ≠ better-policy.")


if __name__ == "__main__":
    main()
