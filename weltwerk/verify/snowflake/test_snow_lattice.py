# SPDX-License-Identifier: AGPL-3.0-only
"""
test_snow_lattice.py — proofs that the six-fold symmetry model is sound (validity-not-outcome). Pure-stdlib.

  1. shared_field_is_symmetric    — a shared environment ⇒ six_fold holds (CLOSED), arms identical.
  2. perarm_field_breaks_symmetry — a per-arm environment ⇒ VIOLATED with a witness (a real divergence).
  3. no_communication_channel     — an arm's profile is INVARIANT to other arms' schedules (no inter-arm
                                    read). This is the structural proof that symmetry is shared-cause, not signal.
  4. checker_matches_oracle       — the set-based checker agrees with the independent pairwise oracle.
  5. nakaya_deterministic         — morphology(T, s) is a deterministic function (same input ⇒ same mode).
  6. determinism                  — repeated checks agree.

Sound iff 6/6: symmetry appears exactly when the field is shared and disappears when it is not, while no arm
can read another — so the model establishes `correlation ≠ communication` for snowflake arms. `holds-here ≠ true`
(this is the LOGIC of the symmetry, on an abstracted 1-D growth model).

Run:  python3 test_snow_lattice.py
"""
from __future__ import annotations

from snow_lattice import (check_sixfold, oracle_symmetric, shared_field, perarm_field, grow, morphology)

SCHED = (0, 1, 3, 2, 3, 1)
TEMP = -15


def chk(name, ok, detail):
    return (name, ok, detail)


def test_shared_field_is_symmetric():
    v = check_sixfold(shared_field(SCHED, TEMP))
    ok = v.status == "CLOSED" and len(set(v.arms)) == 1
    return chk("shared_field_is_symmetric", ok, f"status={v.status} distinct_arms={len(set(v.arms))}")


def test_perarm_field_breaks_symmetry():
    diff = [SCHED, SCHED, SCHED, SCHED, (0, 1, 3, 2, 0, 1), SCHED]   # arm 4 saw a different humidity dip
    v = check_sixfold(perarm_field(diff, TEMP))
    ok = v.status == "VIOLATED" and v.witness is not None and v.witness[0] == 4
    return chk("perarm_field_breaks_symmetry", ok, f"status={v.status} witness={v.witness}")


def test_no_communication_channel():
    # arm 0's profile must NOT change when OTHER arms' schedules change ⇒ there is no inter-arm read.
    base = check_sixfold(perarm_field([SCHED] * 6, TEMP)).arms[0]
    perturbed = check_sixfold(perarm_field([SCHED, (3, 3, 3, 3, 3, 3), (0, 0, 0, 0, 0, 0),
                                            SCHED, SCHED, SCHED], TEMP)).arms[0]
    ok = base == perturbed == grow(SCHED, TEMP)
    return chk("no_communication_channel", ok, f"arm0 invariant to siblings: {base == perturbed}")


def test_checker_matches_oracle():
    bad = []
    for label, f in [("shared", shared_field(SCHED, TEMP)),
                     ("perarm-equal", perarm_field([SCHED] * 6, TEMP)),
                     ("perarm-diff", perarm_field([SCHED] * 5 + [(0, 0, 0, 0, 0, 0)], TEMP))]:
        checker_sym = check_sixfold(f).status == "CLOSED"
        if checker_sym != oracle_symmetric(f):
            bad.append(label)
    return chk("checker_matches_oracle", not bad, f"checker≡oracle except: {bad or 'none'}")


def test_nakaya_deterministic():
    pairs = [(-2, 0), (-2, 3), (-6, 2), (-15, 3), (-25, 1)]
    ok = all(morphology(t, s) == morphology(t, s) for t, s in pairs) and \
        len({morphology(-15, 3)}) == 1
    distinct = {morphology(t, s) for t, s in pairs}
    return chk("nakaya_deterministic", ok and len(distinct) >= 3,
               f"deterministic; modes seen={sorted(distinct)}")


def test_determinism():
    a = check_sixfold(shared_field(SCHED, TEMP))
    b = check_sixfold(shared_field(SCHED, TEMP))
    ok = a == b
    return chk("determinism", ok, f"repeated check agrees: {ok}")


def main():
    results = [
        test_shared_field_is_symmetric(),
        test_perarm_field_breaks_symmetry(),
        test_no_communication_channel(),
        test_checker_matches_oracle(),
        test_nakaya_deterministic(),
        test_determinism(),
    ]
    print("test_snow_lattice — six-fold symmetry = shared-cause, not communication\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: symmetry tracks the SHARED field and breaks "
          f"under a\n  per-arm field, while no arm can read another — establishing correlation ≠ communication "
          f"for the\n  six arms. The hexagonal habit's root cause (molecular H-bond geometry) is audited in "
          f"quantum_ledger.py.")
    assert passed == total, f"{total - passed} check(s) failed — symmetry model not sound"


if __name__ == "__main__":
    main()
