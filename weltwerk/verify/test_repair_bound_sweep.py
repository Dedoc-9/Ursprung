# SPDX-License-Identifier: AGPL-3.0-only
"""
test_repair_bound_sweep.py — PO-3 proofs (validity-not-outcome). Pure-stdlib.

These assert the apparatus tells the truth about its own grades — NOT that repairs are good:

  1. proven_is_bound_monotone — every RESTORED_PROVEN candidate is still restored at 2K (CLOSED is exhaustive
     over the restricted alphabet; deepening cannot resurrect a ruled-out violation). The deductive guarantee.
  2. within_bound_can_flip    — at least one RESTORED_WITHIN_BOUND candidate is VIOLATED at 2K. PO-3's
     falsifier FIRES, by construction — a VALUABLE negative: `restores-(M,E,K) ≠ world-safe`.
  3. grades_are_distinguished — both PROVEN and WITHIN_BOUND occur (the apparatus separates the epistemic grades).
  4. flip_is_recorded         — the flip is surfaced in `within_flips`, not silently dropped (honesty).
  5. determinism              — repeated sweeps agree.

Sound iff 5/5: the PROVEN grade is a real (bound-monotone) guarantee, the WITHIN_BOUND grade is honestly
NOT one, and the apparatus reports the difference rather than collapsing both into a bare 'restored'.

Run:  python3 test_repair_bound_sweep.py
"""
from __future__ import annotations

from repair_bound_sweep import sweep


def chk(name, ok, detail):
    return (name, ok, detail)


_S = sweep()   # one sweep, shared (it is deterministic; test 5 re-runs to prove that)


def test_proven_is_bound_monotone():
    bad = [r["target"] for r in _S["proven"] if not r["restored_2K"]]
    ok = bool(_S["proven"]) and not bad
    return chk("proven_is_bound_monotone", ok,
               f"{len(_S['proven'])} PROVEN candidate(s); restored@2K all={not bad} (broke: {bad or 'none'})")


def test_within_bound_can_flip():
    ok = len(_S["within_flips"]) >= 1
    tgt = [r["target"] for r in _S["within_flips"]]
    return chk("within_bound_can_flip", ok,
               f"WITHIN_BOUND→VIOLATED@2K: {tgt or 'none'} (restores-(M,E,K) ≠ safe)")


def test_grades_are_distinguished():
    ok = bool(_S["proven"]) and bool(_S["within"])
    return chk("grades_are_distinguished", ok,
               f"PROVEN={len(_S['proven'])}, WITHIN_BOUND={len(_S['within'])} (both present)")


def test_flip_is_recorded():
    # every record whose claim died at 2K must appear in within_flips (nothing hidden)
    died = [r for r in _S["records"] if not r["restored_2K"]]
    ok = all(r in _S["within_flips"] for r in died) and len(_S["within_flips"]) == len(died)
    return chk("flip_is_recorded", ok, f"{len(died)} death(s), all surfaced in within_flips={ok}")


def test_determinism():
    a, b = sweep(), sweep()
    ok = a["records"] == b["records"]
    return chk("determinism", ok, f"repeated sweep agrees: {ok}")


def main():
    results = [
        test_proven_is_bound_monotone(),
        test_within_bound_can_flip(),
        test_grades_are_distinguished(),
        test_flip_is_recorded(),
        test_determinism(),
    ]
    print("test_repair_bound_sweep — PO-3: bounded-restored stability (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: RESTORED_PROVEN is bound-monotone (a real "
          f"guarantee),\n  RESTORED_WITHIN_BOUND can flip to VIOLATED when you deepen (a stated, now-demonstrated "
          f"limit),\n  and the apparatus distinguishes and records the two. bounded ≠ proven; "
          f"restores-(M,E,K) ≠ safe.")
    assert passed == total, f"{total - passed} check(s) failed — PO-3 stability claim not established"


if __name__ == "__main__":
    main()
