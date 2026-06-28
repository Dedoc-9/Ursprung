# SPDX-License-Identifier: AGPL-3.0-only
"""
test_safety_gate.py — the safety-gate MECHANISM is sound and honest (validity-not-outcome). Pure-stdlib.

  1. sound_permits_inside   — with a SOUND certificate, an in-region move is permitted (committed).
  2. sound_refuses_outside  — with a sound certificate, an out-of-region move is refused (no commit).
  3. unsound_refuses_all    — with an UNSOUND certificate (Halvorsen quadratic-V is rejected), EVERY move is
                             refused (fail-closed). The KEY honesty test: no safety ⇒ no permission.
  4. membership_is_o1       — the safety check is exactly (certified ∧ ‖s‖≤R): one norm, NO simulation.
  5. gate_blocks_raw_move   — the require_grounded-gated applier refuses a raw (non-Grounded) move.
  6. determinism            — repeated decisions agree.

Sound iff 6/6: the gate permits only grounded, in-region moves under a SOUND certificate at O(1) cost, and
fail-closes when the certificate is unsound — so it can never confer safety it does not have.
`unsound-certificate ≠ safety`; `verify ≠ simulate`.

Run:  python3 test_safety_gate.py
"""
from __future__ import annotations

from safety_gate import (SafetyGate, make_certificate, membership_is_o1, InsideCertifiedRegion,
                         contracting_field, field)
from epistemic_types import UngroundedError
from flow import norm

SOUND = make_certificate("contracting", contracting_field, R=5.0)
HALV = make_certificate("halvorsen-quadV", field, R=8.0)


def chk(name, ok, detail):
    return (name, ok, detail)


def test_sound_permits_inside():
    g = SafetyGate(SOUND)
    ok = SOUND.certified and g.permit((0.0, 0.0, 1.0)) and g.committed == [(0.0, 0.0, 1.0)]
    return chk("sound_permits_inside", ok, f"certified={SOUND.certified} committed={g.committed}")


def test_sound_refuses_outside():
    g = SafetyGate(SOUND)
    permitted = g.permit((10.0, 0.0, 0.0))
    ok = (not permitted) and g.committed == [] and g.refused == 1
    return chk("sound_refuses_outside", ok, f"permitted={permitted} refused={g.refused}")


def test_unsound_refuses_all():
    g = SafetyGate(HALV)
    inside = g.permit((0.0, 0.0, 1.0))          # inside R, but the certificate is REJECTED
    ok = (not HALV.certified) and (not inside) and g.committed == []
    return chk("unsound_refuses_all", ok, f"halvorsen certified={HALV.certified}; inside-move permitted={inside} (fail-closed)")


def test_membership_is_o1():
    s = (0.0, 0.0, 1.0)
    ok = (membership_is_o1(SOUND, s) == (SOUND.certified and norm(s) <= SOUND.R)
          and membership_is_o1(HALV, s) is False)        # unsound ⇒ never safe, regardless of position
    return chk("membership_is_o1", ok, "safety == (certified ∧ ‖s‖≤R); one norm, no simulation")


def test_gate_blocks_raw_move():
    g = SafetyGate(SOUND)
    raised = False
    try:
        g._apply(move=(0.0, 0.0, 1.0))          # raw tuple, not Grounded
    except UngroundedError:
        raised = True
    ok = raised and g.committed == []
    return chk("gate_blocks_raw_move", ok, f"raw move blocked before commit: {raised}")


def test_determinism():
    a = SafetyGate(SOUND); b = SafetyGate(SOUND)
    ok = a.permit((0.0, 0.0, 1.0)) == b.permit((0.0, 0.0, 1.0))
    return chk("determinism", ok, f"repeated decision agrees: {ok}")


def main():
    results = [test_sound_permits_inside(), test_sound_refuses_outside(), test_unsound_refuses_all(),
              test_membership_is_o1(), test_gate_blocks_raw_move(), test_determinism()]
    print("test_safety_gate — edge safety-gate mechanism (fail-closed without a sound certificate)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: O(1) membership permits in-region moves under "
          f"a SOUND certificate\n  and fail-closes when unsound (Halvorsen). The mechanism is built; a sound "
          f"Halvorsen certificate is OPEN.\n  unsound-certificate ≠ safety; verify ≠ simulate.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
