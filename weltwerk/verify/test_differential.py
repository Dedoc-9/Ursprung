# SPDX-License-Identifier: AGPL-3.0-only
"""
test_differential.py — Phase A.2 Step 6 proofs (validity-not-outcome): explicit and symbolic engines agree
on every model in the suite. SKIPS cleanly if the optional solver is absent.

This is the threshold test: verification is no longer "an algorithm" but a family of interchangeable
engines producing equivalent, auditable results. `engine ≠ semantics`.

Run:  python3 test_differential.py
"""
from __future__ import annotations

import solver_adapter

if not solver_adapter.HAVE_SOLVER:
    print("test_differential — SKIPPED: optional solver not installed. `pip install z3-solver` to run.")
    raise SystemExit(0)

from differential import run_suite, agree


def main():
    print("test_differential — Phase A.2 Step 6: explicit vs symbolic equivalence (validity-not-outcome)\n")
    records = run_suite()
    passed = 0
    for label, rec in records:
        ok = agree(rec)
        passed += int(ok)
        detail = (f"{rec['status_explicit']}≡{rec['status_symbolic']}"
                  + (f" len {rec.get('len_explicit')}={rec.get('len_symbolic')}" if rec['status_explicit'] == 'VIOLATED'
                     else f" explored {rec.get('explored_explicit')}={rec.get('explored_symbolic')}"))
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:16s} {detail}")
    total = len(records)
    print(f"\n  {passed}/{total} models agree. Sound iff {total}/{total}: for every model both engines reach "
          f"the same\n  status; VIOLATED ⇒ same shortest witness length + the symbolic witness replays to a real "
          f"violation;\n  non-VIOLATED ⇒ same explored-state count. Two engines, one meaning. symbolic ≠ magic.")
    assert passed == total, f"{total - passed} model(s) disagree — the engines are not equivalent"


if __name__ == "__main__":
    main()
