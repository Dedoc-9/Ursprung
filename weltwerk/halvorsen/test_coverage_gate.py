# SPDX-License-Identifier: AGPL-3.0-only
"""
test_coverage_gate.py — box-coverage saturation read by the frontier gate (validity-not-outcome). Pure-stdlib.
(Heavier — a long integration.)

  1. coverage_saturates    — new-boxes-per-window falls sharply (last window ≪ first): the frontier depletes.
  2. gate_detects_depletion— the final-window decision is NOT EXPLOIT (the gate recognizes a depleted frontier).
  3. bounded_finite_boxes  — the total occupied-box count is finite and positive (finite-measure attractor).
  4. determinism           — the coverage run is reproducible.

Sound iff 4/4: discovery saturates on a finite attractor and the frontier gate reads the depletion; this is
bounded coverage, not unbounded novelty. `estimate ≠ property`; `coverage-saturation ≠ nothing-left-anywhere`.

Run:  python3 test_coverage_gate.py
"""
from __future__ import annotations

from coverage_gate import coverage_windows, gate_trace
from frontier_gate import EXPLOIT


def chk(name, ok, detail):
    return (name, ok, detail)


_COV = coverage_windows(n=40000, windows=10)


def test_coverage_saturates():
    npw = _COV["new_per_window"]
    ok = npw[0] > npw[-1] and npw[-1] < npw[0] / 2
    return chk("coverage_saturates", ok, f"new boxes first={npw[0]} last={npw[-1]} (depleting)")


def test_gate_detects_depletion():
    final = gate_trace(_COV)[-1]
    ok = final[2] != EXPLOIT and final[0] < 1.0     # final multiplier below 1 ⇒ not still expanding
    return chk("gate_detects_depletion", ok, f"final window: m_novel={final[0]} {final[1]} → {final[2]}")


def test_bounded_finite_boxes():
    ok = 0 < _COV["total_boxes"] < 10 ** 7
    return chk("bounded_finite_boxes", ok, f"total occupied boxes = {_COV['total_boxes']} (finite)")


def test_determinism():
    a = coverage_windows(n=40000, windows=10)
    ok = a["new_per_window"] == _COV["new_per_window"]
    return chk("determinism", ok, f"repeated coverage agrees: {ok}")


def main():
    results = [test_coverage_saturates(), test_gate_detects_depletion(),
              test_bounded_finite_boxes(), test_determinism()]
    print("test_coverage_gate — box-coverage saturation + frontier gate\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: discovery saturates on a finite attractor and "
          f"the gate reads the\n  depletion — bounded coverage, not unbounded novelty. estimate ≠ property; "
          f"coverage-saturation ≠ nothing-left-anywhere.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
