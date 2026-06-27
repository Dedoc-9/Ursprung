# SPDX-License-Identifier: AGPL-3.0-only
"""
test_swap_translate.py — PO-11 (state-translation) proofs (validity-not-outcome). Pure-stdlib.

  1. good_preserves      — a stream-preserving μ satisfies π∘μ = π on every reachable α-state (no mismatch).
  2. drop_caught         — a μ that truncates the stream is caught (stream_preserving False, witness found).
  3. reorder_caught      — a μ that reorders the stream is caught (False, witness found).
  4. commute_is_exact    — for the good μ, π(μ(s)) == π(s) pointwise; for a bad μ, some state differs.
  5. preserves_non_stream_freedom — the good μ MAY change non-stream state (it does) while preserving π.
  6. determinism         — repeated checks agree.

Sound iff 6/6: the migration is accepted only when it preserves the stream projection exactly (π∘μ=π), and a
stream-corrupting μ is rejected with an auditable witness rather than passing as a false restore. This is
PO-10's admissibility (over-approximation) reinstantiated with π as the preserved property. `refinement ≠ identity`.

Run:  python3 test_swap_translate.py
"""
from __future__ import annotations

from swap_translate import (pi, mu_good, mu_drop, mu_reorder, stream_preserving,
                            mismatch_witness, reachable_alpha_states)

STATES = reachable_alpha_states()


def chk(name, ok, detail):
    return (name, ok, detail)


def test_good_preserves():
    ok = stream_preserving(mu_good, STATES) and mismatch_witness(mu_good, STATES) is None
    return chk("good_preserves", ok, f"π∘μ=π on all {len(STATES)} states; witness=None")


def test_drop_caught():
    ok = (not stream_preserving(mu_drop, STATES)) and mismatch_witness(mu_drop, STATES) is not None
    return chk("drop_caught", ok, f"truncating μ rejected; witness={mismatch_witness(mu_drop, STATES) is not None}")


def test_reorder_caught():
    ok = (not stream_preserving(mu_reorder, STATES)) and mismatch_witness(mu_reorder, STATES) is not None
    return chk("reorder_caught", ok, f"reordering μ rejected; witness found")


def test_commute_is_exact():
    good_ok = all(pi(mu_good(s)) == pi(s) for s in STATES)
    bad_has_diff = any(pi(mu_drop(s)) != pi(s) for s in STATES)
    return chk("commute_is_exact", good_ok and bad_has_diff,
               f"good pointwise-equal={good_ok}; bad differs somewhere={bad_has_diff}")


def test_preserves_non_stream_freedom():
    # the good μ is genuinely non-identity on non-stream state, yet preserves π (refinement, not identity)
    changed_internal = any(mu_good(s)["internal"] != s["internal"] for s in STATES)
    ok = changed_internal and stream_preserving(mu_good, STATES)
    return chk("preserves_non_stream_freedom", ok,
               f"internal changed={changed_internal} while π preserved (refinement ≠ identity)")


def test_determinism():
    ok = stream_preserving(mu_good, STATES) == stream_preserving(mu_good, STATES)
    return chk("determinism", ok, f"repeated check agrees: {ok}")


def main():
    results = [
        test_good_preserves(),
        test_drop_caught(),
        test_reorder_caught(),
        test_commute_is_exact(),
        test_preserves_non_stream_freedom(),
        test_determinism(),
    ]
    print("test_swap_translate — PO-11: stream-preserving migration μ (π∘μ=π; PO-10 commute reused)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: μ is accepted only when it preserves the stream "
          f"projection\n  exactly; a corrupting μ is caught with a witness. Non-stream state may change freely. "
          f"refinement ≠ identity.")
    assert passed == total, f"{total - passed} check(s) failed — stream-preservation not established"


if __name__ == "__main__":
    main()
