# SPDX-License-Identifier: AGPL-3.0-only
"""
test_compute_control.py — PO-6 proofs (validity-not-outcome). Pure-stdlib (reuses rsi_bench_scale).

  1. anytime_dominance   — at EVERY equal budget B, learned hit-rate ≥ baseline (a budget never helps baseline
                           catch up). Equivalent to: learned's cost distribution stochastically dominates.
  2. strict_gain         — learned hit-rate is strictly greater than baseline at some B (a real gain exists).
  3. gain_at_small_budget— the gain appears at a SMALL budget (≤ ⌈bmax/2⌉), not only after near-exhaustive
                           search — so it is ordering, not "search longer". more-budget ≠ better-policy.
  4. mean_cost_lower     — mean tries-to-first-restorer is lower for learned (the headline, at equal apparatus).
  5. determinism         — repeated runs agree.

Sound iff 5/5: the learned advantage is present at equal compute and at the cheap end of the budget, so it
cannot be explained by being allowed to search more. `equal-B gain ⇒ not-compute`.

Run:  python3 test_compute_control.py
"""
from __future__ import annotations

from compute_control_bench import run


def chk(name, ok, detail):
    return (name, ok, detail)


_R = run()


def test_anytime_dominance():
    bad = [B for B, l, b in _R["curve"] if l < b]
    return chk("anytime_dominance", _R["anytime_dominance"] and not bad,
               f"learned ≥ baseline at all B (budgets where baseline leads: {bad or 'none'})")


def test_strict_gain():
    return chk("strict_gain", _R["strict_gain"],
               f"learned strictly ahead at some B: {_R['strict_gain']}")


def test_gain_at_small_budget():
    cutoff = max(1, _R["bmax"] // 2)
    early = [B for B, l, b in _R["curve"] if B <= cutoff and l > b]
    return chk("gain_at_small_budget", bool(early),
               f"gain present at B≤{cutoff}: {early or 'none'} (cheap-end gain ⇒ ordering, not compute)")


def test_mean_cost_lower():
    ok = _R["mean_cost_learned"] < _R["mean_cost_baseline"]
    return chk("mean_cost_lower", ok,
               f"mean tries: learned {_R['mean_cost_learned']:.2f} < baseline {_R['mean_cost_baseline']:.2f} = {ok}")


def test_determinism():
    a, b = run(), run()
    ok = a["curve"] == b["curve"]
    return chk("determinism", ok, f"repeated run agrees: {ok}")


def main():
    results = [
        test_anytime_dominance(),
        test_strict_gain(),
        test_gain_at_small_budget(),
        test_mean_cost_lower(),
        test_determinism(),
    ]
    print("test_compute_control — PO-6: gain at equal budget, not more compute (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the learned policy dominates the baseline at "
          f"every\n  equal budget and wins at the cheap end of the sweep — so the improvement is better ORDERING "
          f"of the\n  same candidate actions, not a larger compute allowance. equal-B gain ⇒ not-compute.")
    assert passed == total, f"{total - passed} check(s) failed — PO-6 compute-control not established"


if __name__ == "__main__":
    main()
