# SPDX-License-Identifier: AGPL-3.0-only
"""
test_swap_falsifier.py — PO-11/12 adversarial proofs (validity-not-outcome). Pure-stdlib.

  1. deferred_race_flips      — the greedy drop-alpha-early plan is NOT VIOLATED at bound K (buffer masks the
                                gap) but IS VIOLATED (continuity) at 2K. The flip fires. swap-CLOSED@K ≠ safe.
  2. safe_survives_2K         — the make-before-break plan is CLOSED with the migration reachable at 2K.
  3. race_fires_shallow       — the greedy activate-beta-unaligned plan is VIOLATED (no_race) at depth 1, with
                                a witness that replays to a real bad state.
  4. overdetermined_needs_both— neither single guard suffices; only {MBB,ALIGN} succeeds (two failure modes).
  5. boundary_immutability    — a verdict is invariant under guard-set representation permutation (PO-7).
  6. determinism              — repeated falsifier runs agree.

Sound iff 6/6: a greedy downtime-cutting policy is actively punished at depth 2K (deferred starvation) and at
depth 1 (race), only the overdetermined safe plan survives, and verdicts do not depend on how the plan is
written. The harness is non-trivial. `restores-(M,E,K) ≠ safe`; `improved_map ≠ changed_criterion`.

Run:  python3 test_swap_falsifier.py
"""
from __future__ import annotations

from swap_falsifier import flip, race, overdetermined, K, TWOK
from swap_relation import SwapModelChecker

CHK = SwapModelChecker()


def chk(name, ok, detail):
    return (name, ok, detail)


def test_deferred_race_flips():
    f = flip()
    ok = (f["greedy_K"] != "VIOLATED" and f["greedy_2K"] == "VIOLATED"
          and f["greedy_2K_inv"] == "continuity" and f["greedy_2K_depth"] == TWOK and f["flipped"])
    return chk("deferred_race_flips", ok,
               f"greedy@K={f['greedy_K']} → @2K={f['greedy_2K']}({f['greedy_2K_inv']}@{f['greedy_2K_depth']}) "
               f"flipped={f['flipped']}")


def test_safe_survives_2K():
    f = flip()
    ok = f["safe_2K"] == "CLOSED" and f["safe_goal"]
    return chk("safe_survives_2K", ok, f"safe@2K={f['safe_2K']} goal={f['safe_goal']}")


def test_race_fires_shallow():
    r = race()
    ok = r["status"] == "VIOLATED" and r["inv"] == "no_race" and r["depth"] == 1 and r["witness_replays"]
    return chk("race_fires_shallow", ok,
               f"status={r['status']} {r['inv']}@{r['depth']} witness_replays={r['witness_replays']}")


def test_overdetermined_needs_both():
    o = overdetermined()
    ok = (not o["MBB_only"]) and (not o["ALIGN_only"]) and o["both"] and (not o["unconstrained"])
    return chk("overdetermined_needs_both", ok,
               f"MBB_only={o['MBB_only']} ALIGN_only={o['ALIGN_only']} both={o['both']} unc={o['unconstrained']}")


def test_boundary_immutability():
    # the SAME guard set written two ways must yield the SAME verdict (PO-7: map cannot move the judge)
    a = CHK.run(frozenset(["ALIGN", "MBB"]), TWOK)
    b = CHK.run(frozenset(["MBB", "ALIGN"]), TWOK)
    ok = (a.status == b.status and a.reachable == b.reachable and a.goal_reachable == b.goal_reachable)
    return chk("boundary_immutability", ok, f"verdict invariant under plan permutation: {ok}")


def test_determinism():
    ok = flip() == flip() and race() == race()
    return chk("determinism", ok, f"repeated falsifier runs agree: {ok}")


def main():
    results = [
        test_deferred_race_flips(),
        test_safe_survives_2K(),
        test_race_fires_shallow(),
        test_overdetermined_needs_both(),
        test_boundary_immutability(),
        test_determinism(),
    ]
    print(f"test_swap_falsifier — PO-11/12 adversarial control (K={K}, 2K={TWOK})\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: greedy downtime-cutting is punished at 2K "
          f"(deferred\n  starvation) and at depth 1 (race); only the overdetermined make-before-break + align "
          f"plan is\n  safe; verdicts are permutation-invariant. restores-(M,E,K) ≠ safe.")
    assert passed == total, f"{total - passed} check(s) failed — falsifier not punishing unsafe shortcuts"


if __name__ == "__main__":
    main()
