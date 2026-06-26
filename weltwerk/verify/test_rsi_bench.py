# SPDX-License-Identifier: AGPL-3.0-only
"""
test_rsi_bench.py — validity-not-outcome proofs for the RSI benchmark.

These assert the APPARATUS is sound — that it measures honestly and can DISTINGUISH learned capability from
memorization on a benchmark with a *planted, learnable* structural signal. They do NOT assert that recursive
self-improvement is real in general; that is an empirical outcome, not a theorem. The only outcome-flavored
checks (learned transfers, memorizer does not) are properties of the harness on a known-signal world set —
i.e. "the discriminator works" — which is exactly what an honest RSI harness must demonstrate first.

  1. heldout_disjoint      — TRAIN and HELD-OUT world texts share no instance (no leakage)
  2. worlds_violated       — generation yields VIOLATED worlds, each with ≥1 engine-defined restorer
  3. no_false_restore      — every action counted as a restorer re-verifies as non-VIOLATED (frozen check)
  4. verdict_invariance    — restorer set / verdict are policy-independent (improved_map ≠ changed_criterion)
  5. recall_preserved      — the learned policy still finds a restorer for every held-out world that has one
  6. headroom_present      — the task is non-trivial: baseline expected work > 1 (else REG is vacuous)
  7. memorizer_detected    — transfer_memorizer < transfer_learned (the harness tells capability from memo)
  8. determinism           — two runs produce identical metrics

Run:  python3 test_rsi_bench.py
"""
from __future__ import annotations

from rsi_bench import (run, precompute, gen_world, order_baseline, order_learned, fit_weights, work,
                       TAIL_OK, ENGINE, TRAIN_PARAMS, HELDOUT_PARAMS)
from repair import _forbid_and_verify
from kernel_check import check

R = run(verbose=False)        # one shared run (heavy); determinism test does a second


def chk(name, ok, detail):
    return (name, ok, detail)


def test_heldout_disjoint():
    tr = {gen_world(nd, ne) for (nd, ne) in TRAIN_PARAMS}
    he = {gen_world(nd, ne) for (nd, ne) in HELDOUT_PARAMS}
    ok = tr.isdisjoint(he) and len(tr) == len(TRAIN_PARAMS) and len(he) == len(HELDOUT_PARAMS)
    return chk("heldout_disjoint", ok, f"train {len(tr)} ∩ held {len(he)} = {len(tr & he)}")


def test_worlds_violated():
    pcs = [precompute(gen_world(nd, ne)) for (nd, ne) in (TRAIN_PARAMS[:2] + HELDOUT_PARAMS[:2])]
    ok = all(pc["violated"] and len(pc["restorers"]) >= 1 for pc in pcs)
    return chk("worlds_violated", ok, f"violated+restorer on sample: {ok}")


def test_no_false_restore():
    w = gen_world(3, 0)
    pc = precompute(w)
    bound = 8
    ok = all(_forbid_and_verify(w, a, TAIL_OK, ENGINE, bound).status != "VIOLATED" for a in pc["restorers"])
    ok = bool(ok and len(pc["restorers"]) >= 1)
    return chk("no_false_restore", ok,
               f"{len(pc['restorers'])} restorer(s) re-verify as non-VIOLATED: {ok}")


def test_verdict_invariance():
    # restorer set is engine-defined and policy-independent; the world stays VIOLATED regardless of policy
    w = gen_world(4, 2)
    pc = precompute(w)
    weights = fit_weights([precompute(gen_world(nd, ne)) for (nd, ne) in TRAIN_PARAMS[:3]])
    set_base = set(a for a in order_baseline(pc) if a in pc["restorers"])
    set_learn = set(a for a in order_learned(pc, weights) if a in pc["restorers"])
    verdict_same = check(w, max_depth=4, invariants=TAIL_OK).status == "VIOLATED"
    ok = (set_base == set_learn == pc["restorers"]) and verdict_same and R["verdict_invariance"]
    return chk("verdict_invariance", ok, f"restorers policy-independent={set_base == set_learn}; verdict stable={verdict_same}")


def test_recall_preserved():
    ok = R["recall_preserved"]
    return chk("recall_preserved", ok, f"learned policy finds a restorer for every held-out world: {ok}")


def test_headroom_present():
    pc = precompute(gen_world(8, 4))                 # large world ⇒ real search headroom
    wb = work(order_baseline(pc), pc["restorers"])
    ok = wb > 1 and len(pc["alphabet"]) >= 8
    return chk("headroom_present", ok, f"baseline work={wb} over |A|={len(pc['alphabet'])} (non-trivial)")


def test_memorizer_detected():
    ok = (R["transfer_memorizer"] < R["transfer_learned"]
          and R["reg_memorizer_heldout"] < R["reg_learned_heldout"])
    return chk("memorizer_detected", ok,
               f"transfer learned={R['transfer_learned']} > memorizer={R['transfer_memorizer']}; "
               f"REG_held learned={R['reg_learned_heldout']} > memo={R['reg_memorizer_heldout']}")


def test_determinism():
    R2 = run(verbose=False)
    keys = ["reg_learned_heldout", "transfer_learned", "transfer_memorizer", "acceleration_curve_heldout_REG"]
    ok = all(R[k] == R2[k] for k in keys)
    return chk("determinism", ok, f"identical metrics across runs: {ok}")


def main():
    results = [
        test_heldout_disjoint(),
        test_worlds_violated(),
        test_no_false_restore(),
        test_verdict_invariance(),
        test_recall_preserved(),
        test_headroom_present(),
        test_memorizer_detected(),
        test_determinism(),
    ]
    print("test_rsi_bench — RSI benchmark apparatus validity (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: held-out is instance-disjoint, restorers are "
          f"engine-defined\n  and policy-independent, no false restore, recall preserved, the task has headroom, "
          f"and — decisively —\n  the harness SEPARATES a transferring learned policy from a non-transferring "
          f"memorizer. This validates\n  the apparatus, not a general RSI claim. improved_map ≠ changed_criterion.")
    assert passed == total, f"{total - passed} check(s) failed — the RSI apparatus is not sound"


if __name__ == "__main__":
    main()
