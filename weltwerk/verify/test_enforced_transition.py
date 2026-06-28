# SPDX-License-Identifier: AGPL-3.0-only
"""
test_enforced_transition.py — the gate is an INESCAPABLE runtime constraint (validity-not-outcome). Pure-stdlib.

  1. grounded_action_mutates    — apply(Grounded) advances state, increments transition_count, logs the commit.
  2. raw_action_rejected_atomic — apply(raw) raises UngroundedError BEFORE mutation; state + transition_count
                                  unchanged (atomic — the check precedes the effect, nothing to roll back).
  3. ungrounded_proposal_rejected— propose(value, ungrounded_proof) never mutates; rejected_count increments.
  4. only_grounded_commits      — a mixed proposal stream commits ONLY the grounded ones, in order.
  5. real_certificate_wiring    — grounding via a real EngineClosed(ReachabilityCertificate): CLOSED applies,
                                  VIOLATED/None is refused and the state stays pristine.
  6. commit_log_is_the_record   — the committed trajectory equals exactly the applied actions (Weltlinie).

Sound iff 6/6: the only path to mutation is a verifier-issued proof; raw/ungrounded actions are refused before
any effect with the state pristine; the commit log records only what actually occurred. The type gate is a
runtime constraint, not a floating library. `improved_map ≠ changed_criterion`; `grounded ≠ true`.

Run:  python3 test_enforced_transition.py
"""
from __future__ import annotations

from enforced_transition import EnforcedTransitionSystem
from epistemic_types import Grounded, UngroundedError, Attested, EngineClosed
from artifacts import ReachabilityCertificate

_INC = lambda s, a: s + a                 # a trivial step: add the action value


class _Cert:
    def __init__(self, status): self.status = status


def chk(name, ok, detail):
    return (name, ok, detail)


def test_grounded_action_mutates():
    sysm = EnforcedTransitionSystem(state=0, step_fn=_INC)
    sysm.apply(action=Grounded.ground(5, Attested(True, "ok")))
    ok = sysm.state == 5 and sysm.transition_count == 1 and len(sysm.commit_log) == 1
    return chk("grounded_action_mutates", ok, f"state={sysm.state} count={sysm.transition_count}")


def test_raw_action_rejected_atomic():
    sysm = EnforcedTransitionSystem(state=0, step_fn=_INC)
    raised = False
    try:
        sysm.apply(action=7)                          # raw primitive — must be refused before mutation
    except UngroundedError:
        raised = True
    ok = raised and sysm.state == 0 and sysm.transition_count == 0 and sysm.commit_log == []
    return chk("raw_action_rejected_atomic", ok,
               f"raised={raised} state pristine={sysm.state == 0} count={sysm.transition_count}")


def test_ungrounded_proposal_rejected():
    sysm = EnforcedTransitionSystem(state=0, step_fn=_INC)
    applied, _why = sysm.propose(9, Attested(False, "ungrounded"))
    ok = (not applied) and sysm.state == 0 and sysm.transition_count == 0 and sysm.rejected_count == 1
    return chk("ungrounded_proposal_rejected", ok,
               f"applied={applied} state={sysm.state} rejected={sysm.rejected_count}")


def test_only_grounded_commits():
    sysm = EnforcedTransitionSystem(state=0, step_fn=_INC)
    stream = [(1, Attested(True)), (2, Attested(False)), (3, Attested(True)), (4, Attested(False))]
    for val, proof in stream:
        sysm.propose(val, proof)
    ok = sysm.state == 4 and sysm.transition_count == 2 and sysm.rejected_count == 2     # only 1 and 3 applied
    return chk("only_grounded_commits", ok, f"state={sysm.state} applied={sysm.transition_count} rejected={sysm.rejected_count}")


def test_real_certificate_wiring():
    sysm = EnforcedTransitionSystem(state="alpha", step_fn=lambda _s, _a: "beta")
    closed = ReachabilityCertificate(explored_state_sigs=frozenset(), transition_count=0,
                                     invariant_names=(), status="CLOSED")
    applied_safe, _ = sysm.propose("swap", EngineClosed(closed))
    state_after_safe = sysm.state
    applied_unsafe, _ = sysm.propose("swap", EngineClosed(_Cert("VIOLATED")))    # VIOLATED ⇒ not grounded
    ok = (applied_safe and state_after_safe == "beta" and not applied_unsafe
          and sysm.transition_count == 1)
    return chk("real_certificate_wiring", ok,
               f"CLOSED→applied={applied_safe}; VIOLATED→applied={applied_unsafe}; count={sysm.transition_count}")


def test_commit_log_is_the_record():
    sysm = EnforcedTransitionSystem(state=0, step_fn=_INC)
    sysm.propose(10, Attested(True, "p1"))
    sysm.propose(99, Attested(False))             # rejected, not recorded
    sysm.propose(20, Attested(True, "p2"))
    logged = [v for v, _why in sysm.commit_log]
    ok = logged == [10, 20] and sysm.state == 30
    return chk("commit_log_is_the_record", ok, f"commit_log values={logged} (only committed)")


def main():
    results = [
        test_grounded_action_mutates(),
        test_raw_action_rejected_atomic(),
        test_ungrounded_proposal_rejected(),
        test_only_grounded_commits(),
        test_real_certificate_wiring(),
        test_commit_log_is_the_record(),
    ]
    print("test_enforced_transition — the epistemic gate as an inescapable runtime constraint\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the only path to mutation is a verifier-issued "
          f"proof; raw/\n  ungrounded actions are refused before any effect (state pristine, count unchanged); the "
          f"commit log\n  records only what occurred. improved_map ≠ changed_criterion; grounded ≠ true.")
    assert passed == total, f"{total - passed} check(s) failed — gate not enforced at the mutation boundary"


if __name__ == "__main__":
    main()
