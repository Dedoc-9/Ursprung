# SPDX-License-Identifier: AGPL-3.0-only
"""
test_swap_relation.py — PO-11 proofs (validity-not-outcome). Pure-stdlib.

  1. checker_matches_oracle   — the bounded swap checker agrees with the INDEPENDENT unbounded-fixpoint oracle
                                on status (and reachable set when CLOSED). (PO-4 pattern, swap domain.)
  2. shortest_violation_match — on VIOLATED plans, the checker's witness depth == the oracle's shortest.
  3. certificate_inductive    — a CLOSED swap's ReachabilityCertificate passes the no-search closure check;
                                tampering (drop a state / inject a bad one) is rejected. (PO-8 logic reused.)
  4. conformance_contract     — status ∈ {CLOSED,BOUNDED,VIOLATED}; a VIOLATED witness REPLAYS to the named
                                bad invariant; runs are deterministic. (conformance contract, swap domain.)
  5. positive_safe_swap       — the safe plan {MBB,ALIGN} is CLOSED with the migration reachable.
  6. failure_unconstrained    — the unconstrained swap is VIOLATED (no false CLOSED on an unsafe world).

Sound iff 6/6: the swap domain is judged by the frozen grading + certificate + an independent oracle, exactly
as the core engine is. `re-encoded ≠ verified` until the oracle agrees; `integrity ≠ truth`.

Run:  python3 test_swap_relation.py
"""
from __future__ import annotations

import dataclasses

from swap_relation import (SwapModelChecker, swap_oracle, swap_check_certificate, replay, _first_bad,
                           INIT, INV_NAMES)

CHK = SwapModelChecker()
PLANS = [frozenset(), frozenset({"MBB"}), frozenset({"ALIGN"}), frozenset({"MBB", "ALIGN"})]


def chk(name, ok, detail):
    return (name, ok, detail)


def test_checker_matches_oracle():
    bad = []
    for p in PLANS:
        v = CHK.run(p, bound=8)
        o = swap_oracle(p)
        if v.status == "BOUNDED":
            bad.append(f"{sorted(p)}:checker BOUNDED@8 (raise bound)")
            continue
        if v.status != o["status"]:
            bad.append(f"{sorted(p)}:{v.status}!={o['status']}")
        elif v.status == "CLOSED" and v.reachable != o["reachable"]:
            bad.append(f"{sorted(p)}:reachable set mismatch")
    return chk("checker_matches_oracle", not bad, f"checker≡oracle except: {bad or 'none'}")


def test_shortest_violation_match():
    bad = []
    for p in PLANS:
        v = CHK.run(p, bound=8)
        if v.status == "VIOLATED":
            o = swap_oracle(p)
            if v.depth != o["shortest"]:
                bad.append(f"{sorted(p)}:{v.depth}!={o['shortest']}")
    return chk("shortest_violation_match", not bad, f"witness depth == oracle shortest except: {bad or 'none'}")


def test_certificate_inductive():
    safe = frozenset({"MBB", "ALIGN"})
    v = CHK.run(safe, bound=8)
    valid = v.certificate is not None and swap_check_certificate(safe, v.certificate)
    # tamper: drop a reachable state ⇒ closure breaks
    dropped = next(s for s in v.certificate.explored_state_sigs if s != INIT)
    cert_drop = dataclasses.replace(v.certificate,
                                    explored_state_sigs=v.certificate.explored_state_sigs - {dropped})
    drop_rejected = not swap_check_certificate(safe, cert_drop)
    # tamper: inject a fabricated BAD state ⇒ invariants fail on S
    cert_inj = dataclasses.replace(v.certificate,
                                   explored_state_sigs=v.certificate.explored_state_sigs | {("none", False, False, 0, True)})
    inj_rejected = not swap_check_certificate(safe, cert_inj)
    ok = valid and drop_rejected and inj_rejected
    return chk("certificate_inductive", ok,
               f"valid={valid}, drop_rejected={drop_rejected}, inject_rejected={inj_rejected}")


def test_conformance_contract():
    bad = []
    for p in PLANS:
        v1 = CHK.run(p, bound=8)
        v2 = CHK.run(p, bound=8)
        if v1.status not in ("CLOSED", "BOUNDED", "VIOLATED"):
            bad.append(f"{sorted(p)}:bad status {v1.status}")
        if (v1.status, v1.depth, v1.violated_inv) != (v2.status, v2.depth, v2.violated_inv):
            bad.append(f"{sorted(p)}:nondeterministic")
        if v1.status == "VIOLATED":
            reached = replay(p, v1.witness)
            if _first_bad(reached) is None:                 # witness must reach an actually-bad state
                bad.append(f"{sorted(p)}:witness does not replay to a violation")
    return chk("conformance_contract", not bad, f"status set + determinism + replayable witness: {bad or 'none'}")


def test_positive_safe_swap():
    v = CHK.run(frozenset({"MBB", "ALIGN"}), bound=8)
    ok = v.status == "CLOSED" and v.goal_reachable
    return chk("positive_safe_swap", ok, f"safe plan status={v.status} goal={v.goal_reachable}")


def test_failure_unconstrained():
    v = CHK.run(frozenset(), bound=8)
    ok = v.status == "VIOLATED"
    return chk("failure_unconstrained", ok, f"unconstrained status={v.status} ({v.violated_inv}@{v.depth})")


def main():
    results = [
        test_checker_matches_oracle(),
        test_shortest_violation_match(),
        test_certificate_inductive(),
        test_conformance_contract(),
        test_positive_safe_swap(),
        test_failure_unconstrained(),
    ]
    print("test_swap_relation — PO-11: swap domain under frozen grading + oracle + certificate\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the swap checker agrees with an independent "
          f"oracle,\n  its CLOSED certificate is independently inductive (tamper-rejecting), the contract holds, "
          f"and\n  the safe plan is CLOSED+migrating while the unconstrained swap is VIOLATED. re-encoded ≠ verified.")
    assert passed == total, f"{total - passed} check(s) failed — swap domain not engine-faithful"


if __name__ == "__main__":
    main()
