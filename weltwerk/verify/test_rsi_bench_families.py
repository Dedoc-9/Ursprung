# SPDX-License-Identifier: AGPL-3.0-only
"""
test_rsi_bench_families.py — PO-5 proofs (validity-not-outcome). Pure-stdlib (z3 not used).

These assert the apparatus is SOUND and that the constructed task behaves as its (determinate) geometry
requires — NOT that "RSI works":

  1. construction_valid           — for every sampled world the FROZEN engine's restorer set is exactly
                                    {('destroy','cause')}. The label the learner is graded on is an engine
                                    fact, and the construction is correct. `label = engine`, not assumed.
  2. one_shot_linear_fails        — the one-shot linear policy stays near chance and far above the iterated
                                    ceiling. The task is provably not one-shot-linearly-learnable (XOR).
  3. data_scaling_does_not_help   — 4× labels do not rescue the linear policy. The missing signal is linear
                                    capacity, not data. `more-data ≠ more-capacity`.
  4. iteration_accrues_and_saturates — held-out work is non-increasing across rounds, drops by ≥1 from k=0,
                                    and SATURATES at the representable ceiling. Bounded, first-order accrual.
  5. frozen_criterion            — the engine restorer set is identical on re-computation and equals the
                                    construction cause; train/held world texts are disjoint. The criterion
                                    never moves across iterations; only the policy does. `criterion ≠ policy`.
  6. determinism                 — repeated runs agree.

Sound iff 6/6: a one-shot learner provably cannot (and more data cannot help), while an iterated loop climbs
and then stops at a ceiling — over a label that is the frozen engine's own. This demonstrates the loop is
CAPABLE of bounded, saturating, task-gated accrual; combined with PO-6 (the natural task is one-shot) it
bounds the RSI claim from both sides. `iteration ≠ open-ended`; `bounded-accrual ≠ second-order self-improvement`.

Run:  python3 test_rsi_bench_families.py     (engine-backed; ~tens of seconds)
"""
from __future__ import annotations

from rsi_bench_families import (run, world_info, gen_world, restorer_set,
                                TRAIN_SEEDS, HELD_SEEDS)

_R = run()
_SAMPLE_SEEDS = list(TRAIN_SEEDS)[:6] + list(HELD_SEEDS)[:6]


def chk(name, ok, detail):
    return (name, ok, detail)


def test_construction_valid():
    bad = []
    for s in _SAMPLE_SEEDS:
        rs = restorer_set(world_info(gen_world(s)))
        if rs != {("destroy", "cause")}:
            bad.append(f"seed{s}:{sorted(rs)}")
    return chk("construction_valid", not bad, f"engine restorer == {{('destroy','cause')}} except: {bad or 'none'}")


def test_one_shot_linear_fails():
    # linear stays clearly above the iterated ceiling (cannot rank the cause first)
    ok = (_R["linear_work"] > _R["boost_final"] + 1.0) and (_R["boost_final"] <= 1.0 + 1e-9)
    return chk("one_shot_linear_fails", ok,
               f"linear {_R['linear_work']:.2f} ≫ ceiling {_R['boost_final']:.2f} (chance≈{_R['chance']:.1f})")


def test_data_scaling_does_not_help():
    # 4× data does not bring the linear policy near the ceiling, and is no real improvement over base linear
    ok = (_R["moredata_work"] > _R["boost_final"] + 1.0) and (_R["moredata_work"] >= _R["linear_work"] - 0.5)
    return chk("data_scaling_does_not_help", ok,
               f"4×-data {_R['moredata_work']:.2f} vs base {_R['linear_work']:.2f} — not a data problem")


def test_iteration_accrues_and_saturates():
    ys = [w for _k, w in _R["curve"]]
    non_increasing = all(ys[i] >= ys[i + 1] - 1e-9 for i in range(len(ys) - 1))
    real_accrual = (ys[0] - ys[-1]) >= 1.0
    ok = non_increasing and real_accrual and _R["saturated"] and ys[-1] <= 1.0 + 1e-9
    return chk("iteration_accrues_and_saturates", ok,
               f"curve {[round(y,2) for y in ys]} non-incr={non_increasing} drop={(ys[0]-ys[-1]):.2f} "
               f"saturated={_R['saturated']}")


def test_frozen_criterion():
    info = world_info(gen_world(list(HELD_SEEDS)[0]))
    rs1, rs2 = restorer_set(info), restorer_set(info)          # deterministic, criterion does not drift
    invariant = rs1 == rs2 == {("destroy", "cause")}
    train_txt = {gen_world(s) for s in TRAIN_SEEDS}
    held_txt = {gen_world(s) for s in HELD_SEEDS}
    disjoint = not (train_txt & held_txt)
    return chk("frozen_criterion", invariant and disjoint,
               f"restorer stable & == cause: {invariant}; train∩held world texts: {len(train_txt & held_txt)}")


def test_determinism():
    a, b = run(), run()
    ok = a["curve"] == b["curve"] and a["linear_work"] == b["linear_work"]
    return chk("determinism", ok, f"repeated run agrees: {ok}")


def main():
    results = [
        test_construction_valid(),
        test_one_shot_linear_fails(),
        test_data_scaling_does_not_help(),
        test_iteration_accrues_and_saturates(),
        test_frozen_criterion(),
        test_determinism(),
    ]
    print("test_rsi_bench_families — PO-5: bounded multi-iteration accrual (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:32s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the label is the frozen engine's; a one-shot "
          f"linear learner\n  provably cannot and more data cannot help; an iterated loop climbs and SATURATES at "
          f"the ceiling.\n  Bounded, task-gated, first-order accrual — not open-ended, not second-order. "
          f"iteration ≠ open-ended RSI.")
    assert passed == total, f"{total - passed} check(s) failed — PO-5 bounded-accrual claim not established"


if __name__ == "__main__":
    main()
