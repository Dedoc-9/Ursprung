# SPDX-License-Identifier: AGPL-3.0-only
"""
test_conformance.py — the UNIVERSAL calibration contract every registered observer must satisfy.

This is the test that turns "observer" from an idea into a constrained type. It runs the same two
checks against every observer in observers.OBSERVERS, so a future Generativity / Cost / Fairness lens
inherits the contract for free — and a lens that quietly tries to become a scoring/optimizing/truth
function fails to register.

THE CONTRACT (per observer):
  1. null calibration   — do(nothing) ⇒ a zero difference. For a pure deterministic observer this is a
                          theorem (identity ⇒ trace_a == trace_b). NECESSARY.
  2. non-degeneracy     — the observer moves on at least one real cause. Guards the trivial observer
                          that returns zero for everything (which would pass #1 vacuously).

HONEST LIMIT (stated, not hidden): passing this contract means an observer is *calibrated at the null
and non-trivial*. It does NOT mean the observer measures what it claims — `green-check ≠ correctness`.
Validating Orbit's geometry against the CI-bearing orbit_estimator is a separate, still-open job.

Run:  PYTHONHASHSEED=0 python3 test_conformance.py
"""
from __future__ import annotations

from fork import cull_species, remove_resource, set_param
from observers import OBSERVERS, is_nontrivial, null_delta_is_zero
from world import genesis

# A small battery of real causes. An observer must be non-degenerate on AT LEAST ONE of these.
STRESSORS = [
    cull_species("predator"),
    remove_resource("forest"),
    set_param("predation_enabled", False),
    set_param("regen_rate", 0),
]


def main():
    w = genesis(seed=11).run(6)
    print("test_conformance — the universal observer calibration contract\n")
    print(f"  registered observers: {[o.__name__ for o in OBSERVERS]}\n")
    passed, total = 0, 0
    for ObsCls in OBSERVERS:
        ob = ObsCls()
        null_ok = null_delta_is_zero(ob, w)
        moved = [iv.kind for iv in STRESSORS if is_nontrivial(ob, w, iv)]
        nontrivial_ok = len(moved) > 0
        ok = null_ok and nontrivial_ok
        total += 1
        passed += int(ok)
        print(f"  [{'PASS' if ok else 'FAIL'}] {ob.name:14s} "
              f"null-calibrated(identity→0)={null_ok}; non-degenerate on={moved or 'NOTHING'}")
    print(f"\n  {passed}/{total} observers conform. Contract = calibrated-at-null AND non-trivial.")
    print("  This does NOT certify any observer measures what it claims (green-check ≠ correctness);")
    print("  it certifies the platform boundary: an observer cannot silently become a truth source.")
    assert passed == total, f"{total - passed} observer(s) failed the calibration contract"


if __name__ == "__main__":
    main()
