# SPDX-License-Identifier: AGPL-3.0-only
"""
test_certificate_checker.py — PO-8 proofs: a CLOSED certificate is an independently-checkable proof object,
and tampering is detected. Pure-stdlib.

  1. valid_certificate_passes      — a genuine CLOSED certificate passes the independent checker
  2. missing_state_fails           — dropping a recorded state breaks closure (or init) ⇒ rejected
  3. injected_violation_fails      — adding a state that violates an invariant ⇒ rejected
  4. non_closed_rejected           — a None / non-CLOSED certificate is rejected
  5. checker_is_independent        — the checker imports no engine/search symbol (no re-run of the prover)
  6. determinism                   — repeated checks agree

Run:  python3 test_certificate_checker.py
"""
from __future__ import annotations

import certificate_checker
from certificate_checker import check_certificate
from kernel_check import check, DEFAULT_INVARIANTS, _sig, _snapshot_state
from world_sim import WorldSim
from artifacts import ReachabilityCertificate

SMALL = ('world "T"\n'
         'entity faction_a:\n  position 0 0 0\n  controls hub\n'
         'entity hub:\n  position 1 0 0\n  health 10\n  powers leaf\n'
         'entity leaf:\n  position 2 0 0\n  health 10\n')

CERT = check(SMALL, max_depth=12).certificate
INIT_SIG = _sig(_snapshot_state(WorldSim(SMALL)))


def chk(name, ok, detail):
    return (name, ok, detail)


def test_valid_certificate_passes():
    ok = CERT is not None and check_certificate(SMALL, DEFAULT_INVARIANTS, CERT)
    return chk("valid_certificate_passes", ok, f"genuine CLOSED cert validates: {ok}")


def test_missing_state_fails():
    non_init = next(s for s in CERT.explored_state_sigs if s != INIT_SIG)
    tampered = ReachabilityCertificate(frozenset(set(CERT.explored_state_sigs) - {non_init}),
                                       CERT.transition_count, CERT.invariant_names, "CLOSED")
    ok = not check_certificate(SMALL, DEFAULT_INVARIANTS, tampered)
    return chk("missing_state_fails", ok, f"dropping a state ⇒ rejected: {ok}")


def test_injected_violation_fails():
    body = list(INIT_SIG[0])
    k, a, s, _h = body[0]
    body[0] = (k, a, s, 9999)                       # health > max ⇒ violates health_in_bounds
    bad = (tuple(body), INIT_SIG[1])
    tampered = ReachabilityCertificate(frozenset(set(CERT.explored_state_sigs) | {bad}),
                                       CERT.transition_count, CERT.invariant_names, "CLOSED")
    ok = not check_certificate(SMALL, DEFAULT_INVARIANTS, tampered)
    return chk("injected_violation_fails", ok, f"injected invariant-violating state ⇒ rejected: {ok}")


def test_non_closed_rejected():
    bounded = check(SMALL, max_depth=1)             # BOUNDED ⇒ certificate is None
    faux = ReachabilityCertificate(frozenset(CERT.explored_state_sigs),
                                   CERT.transition_count, CERT.invariant_names, "BOUNDED")
    ok = (not check_certificate(SMALL, DEFAULT_INVARIANTS, bounded.certificate)
          and not check_certificate(SMALL, DEFAULT_INVARIANTS, faux))
    return chk("non_closed_rejected", ok, f"None and non-CLOSED rejected: {ok}")


def test_checker_is_independent():
    # the checker module must not pull in the engine / the BFS entry point (no re-run of the prover)
    ok = not any(hasattr(certificate_checker, n) for n in ("check", "ExplicitStateBFSEngine", "SymbolicEngine"))
    return chk("checker_is_independent", ok, f"no engine/search symbol in checker: {ok}")


def test_determinism():
    ok = check_certificate(SMALL, DEFAULT_INVARIANTS, CERT) == check_certificate(SMALL, DEFAULT_INVARIANTS, CERT)
    return chk("determinism", ok, f"repeated checks agree: {ok}")


def main():
    results = [
        test_valid_certificate_passes(),
        test_missing_state_fails(),
        test_injected_violation_fails(),
        test_non_closed_rejected(),
        test_checker_is_independent(),
        test_determinism(),
    ]
    print("test_certificate_checker — PO-8: CLOSED certificate as an independently-checkable proof object\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a genuine CLOSED certificate validates via the "
          f"inductive-\n  invariant property (init∈S, invariants on S, S closed under T), and dropping or injecting "
          f"a state is\n  detected — without re-running the prover. PO-8 discharged: certificate = proof object, "
          f"not record.")
    assert passed == total, f"{total - passed} check(s) failed — the certificate is not soundly checkable"


if __name__ == "__main__":
    main()
