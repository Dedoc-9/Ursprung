# SPDX-License-Identifier: AGPL-3.0-only
"""
test_abstraction_soundness.py — PO-10 proofs (validity-not-outcome). Pure-stdlib.

  1. sound_lift_is_admissible      — the existential-image lift (a quotient) is admissible on every world.
  2. admissible_implies_no_false_closed — for the sound lift, the conclusion `abstract-CLOSED ⇒ exact-CLOSED`
                                     holds (never abstract-CLOSED while exact-VIOLATED).
  3. unsound_abstraction_is_caught — a candidate that DROPS a bad block (a buggy/over-eager optimization) is
                                     flagged INADMISSIBLE *and* would have reported a FALSE CLOSED — the exact
                                     failure mode PO-10 names, detected by the harness.
  4. abstraction_is_a_quotient     — the abstract state set is no larger than the concrete one, and the abstract
                                     reachable set OVER-approximates the image of the concrete reachable set.
  5. determinism                   — rebuilding the graph + lift agrees.

Sound iff 5/5: the harness verifies the premise (over-approximation), confirms the conclusion (no false CLOSED)
under it, and *catches* an abstraction that violates the premise before it can launder a false CLOSED into the
verdict. `over-approx ≠ exact`; `abstract-CLOSED ⇒ exact-CLOSED` holds only under admissibility.

Run:  python3 test_abstraction_soundness.py
"""
from __future__ import annotations

from abstraction_soundness import (build_concrete, alpha_from_observation, lift, admissible,
                                    no_false_closed, concrete_verdict, abstract_verdict, _reach,
                                    STAR, ISO, TAIL_OK, OBSERVE)

WORLDS = [("star", STAR), ("iso", ISO)]


def _graph(w):
    return build_concrete(w, TAIL_OK, OBSERVE)


def chk(name, ok, detail):
    return (name, ok, detail)


def test_sound_lift_is_admissible():
    bad = []
    for label, w in WORLDS:
        g = _graph(w)
        a = alpha_from_observation(g)
        if not admissible(g, a, lift(g, a)):
            bad.append(label)
    return chk("sound_lift_is_admissible", not bad, f"existential-image lift admissible except: {bad or 'none'}")


def test_admissible_implies_no_false_closed():
    bad = []
    for label, w in WORLDS:
        g = _graph(w)
        a = alpha_from_observation(g)
        ok, cv, av = no_false_closed(g, lift(g, a))
        if not ok:
            bad.append(f"{label}:exact={cv},abs={av}")
    return chk("admissible_implies_no_false_closed", not bad, f"no false CLOSED under sound lift: {bad or 'none'}")


def test_unsound_abstraction_is_caught():
    g = _graph(STAR)                                   # a world that actually violates
    a = alpha_from_observation(g)
    assert concrete_verdict(g) == "VIOLATED", "STAR must be violable for this test to mean anything"
    unsound = {**lift(g, a), "bad": set()}             # buggy abstraction: dropped the bad block
    is_adm = admissible(g, a, unsound)
    ok, cv, av = no_false_closed(g, unsound)
    # the harness must (a) flag it inadmissible AND (b) confirm it WOULD false-close (av CLOSED while cv VIOLATED)
    caught = (is_adm is False) and (ok is False) and (av == "CLOSED" and cv == "VIOLATED")
    return chk("unsound_abstraction_is_caught", caught,
               f"inadmissible={not is_adm}, would_false_close={not ok} (abs={av}, exact={cv})")


def test_abstraction_is_a_quotient():
    bad = []
    for label, w in WORLDS:
        g = _graph(w)
        a = alpha_from_observation(g)
        ab = lift(g, a)
        ab_states = ab["init"] | {x for e in ab["edges"] for x in e}
        smaller = len(ab_states) <= len(g["states"])
        # over-approx: image of concrete reachable ⊆ abstract reachable
        c_reach = _reach({g["init"]}, g["edges"])
        a_reach = _reach(ab["init"], ab["edges"])
        overapprox = {a[s] for s in c_reach} <= a_reach
        if not (smaller and overapprox):
            bad.append(f"{label}:smaller={smaller},overapprox={overapprox}")
    return chk("abstraction_is_a_quotient", not bad, f"quotient + over-approx except: {bad or 'none'}")


def test_determinism():
    g1, g2 = _graph(STAR), _graph(STAR)
    ok = (g1["edges"] == g2["edges"] and g1["bad"] == g2["bad"] and g1["init"] == g2["init"])
    return chk("determinism", ok, f"rebuilt graph agrees: {ok}")


def main():
    results = [
        test_sound_lift_is_admissible(),
        test_admissible_implies_no_false_closed(),
        test_unsound_abstraction_is_caught(),
        test_abstraction_is_a_quotient(),
        test_determinism(),
    ]
    print("test_abstraction_soundness — PO-10: abstract-CLOSED ⇒ exact-CLOSED (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:34s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a quotient over-approximates and never false-"
          f"closes; an\n  abstraction that drops a bad block is flagged inadmissible AND shown to produce a false "
          f"CLOSED.\n  admissible ⇒ no_false_closed; `over-approx ≠ exact`.")
    assert passed == total, f"{total - passed} check(s) failed — PO-10 admissibility harness not established"


if __name__ == "__main__":
    main()
