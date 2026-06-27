# SPDX-License-Identifier: AGPL-3.0-only
"""
test_differential_b.py — PO-1 proofs (validity-not-outcome). SKIPS cleanly if z3 is absent.

Extends the two-world `test_symbolic_b` gate to a generated *distribution* of acyclic {destroy,repair} worlds:

  1. full_agreement        — on every generated world, Approach B and the explicit engine agree on status,
                             shortest-witness length, and B's witness replays to a real disabled tail.
  2. distribution_nontrivial — the distribution contains BOTH violable and clean worlds (the test is not
                             vacuously passing on one class).
  3. determinism           — a re-run agrees.

Sound iff 3/3: the direct-SMT re-encoding matches the explicit reference across topologies it claims to cover,
so Approach B is faithful on the acyclic {destroy,repair}/not_disabled fragment — the precondition for it to be
a supported engine there. `re-encoded ≠ verified` outside this fragment.

Run:  python3 test_differential_b.py     (needs z3: pip install z3-solver)
"""
from __future__ import annotations

import solver_adapter_b

if not solver_adapter_b.HAVE_SOLVER:
    print("test_differential_b — SKIPPED: optional solver not installed. `pip install z3-solver` to run.")
    raise SystemExit(0)

from differential_b import run


def chk(name, ok, detail):
    return (name, ok, detail)


_R = run()


def test_full_agreement():
    ok = not _R["disagreements"]
    return chk("full_agreement", ok,
               f"{_R['agreements']}/{_R['n']} agree; disagreements: "
               f"{[d['seed'] for d in _R['disagreements']] or 'none'}")


def test_distribution_nontrivial():
    ok = _R["n_violated"] >= 1 and _R["n_clean"] >= 1
    return chk("distribution_nontrivial", ok,
               f"violated={_R['n_violated']}, clean={_R['n_clean']} (both classes present)")


def test_determinism():
    r2 = run()
    ok = (r2["agreements"] == _R["agreements"] and r2["n"] == _R["n"]
          and len(r2["disagreements"]) == len(_R["disagreements"]))
    return chk("determinism", ok, f"re-run agrees: {ok}")


def main():
    results = [
        test_full_agreement(),
        test_distribution_nontrivial(),
        test_determinism(),
    ]
    print("test_differential_b — PO-1: Approach-B faithfulness over a world distribution (CANDIDATE → gate)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: Approach B agrees with the explicit engine "
          f"on every\n  generated world (status + shortest length + replayable witness), over a distribution "
          f"with both\n  violable and clean worlds. Faithful on the acyclic {{destroy,repair}} fragment; "
          f"re-encoded ≠ verified beyond it.")
    assert passed == total, f"{total - passed} check(s) failed — Approach B not faithful over the distribution"


if __name__ == "__main__":
    main()
