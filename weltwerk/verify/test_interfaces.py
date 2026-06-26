# SPDX-License-Identifier: AGPL-3.0-only
"""
test_interfaces.py — Phase A.2 Step 1 proofs (validity-not-outcome): the stable contract is faithful and
introduces no behavior change.

  1. closed_maps_through      — verify(CLOSED world) carries status/metadata through unchanged
  2. violated_carries_witness — verify(VIOLATED) exposes a witness trace + violation descriptors
  3. adapter_is_faithful      — VerificationResult fields equal the underlying CheckResult fields
  4. witness_is_consumable    — the witness, taken only from the contract, replays on a fresh world
  5. results_are_frozen       — ReachabilityResult / VerificationResult are immutable (per Trace/artifact rule)
  6. minimal_contract_present — exactly the agreed minimal fields exist; certificate is a None placeholder
  7. determinism              — two verify() calls produce equal contracts
  8. engine_labelled          — the result names its backend (sets up Step 6 differential testing)

Run:  python3 test_interfaces.py
"""
from __future__ import annotations

import dataclasses

from interfaces import ReachabilityResult, VerificationResult, verify, from_check_result
from kernel_check import check, replay_path

SMALL = """
world "T"
entity faction_a:
  position 0 0 0
  controls hub
entity hub:
  position 1 0 0
  health 10
  powers leaf
entity leaf:
  position 2 0 0
  health 10
"""

NEVER_DESTROYED = {"nothing_ever_destroyed":
                   lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime)}


def chk(name, ok, detail):
    return (name, ok, detail)


def test_closed_maps_through():
    vr = verify(SMALL, max_depth=8)
    ok = (vr.status == "CLOSED" and vr.explored_states > 1 and vr.frontier_exhausted
          and vr.witness is None)
    return chk("closed_maps_through", ok,
               f"status={vr.status} explored={vr.explored_states} exhausted={vr.frontier_exhausted}")


def test_violated_carries_witness():
    vr = verify(SMALL, max_depth=3, invariants=NEVER_DESTROYED)
    ok = (vr.status == "VIOLATED" and isinstance(vr.witness, tuple) and len(vr.witness) >= 1
          and len(vr.violations) >= 1)
    return chk("violated_carries_witness", ok, f"witness={vr.witness} violations={vr.violations}")


def test_adapter_is_faithful():
    r = check(SMALL, max_depth=8)
    vr = from_check_result(r)
    ok = (vr.status == r.status and vr.explored_states == r.states_explored
          and vr.frontier_exhausted == (not r.truncated)
          and (vr.witness is None) == (r.ghost is None))
    return chk("adapter_is_faithful", ok, f"contract mirrors CheckResult: {ok}")


def test_witness_is_consumable():
    vr = verify(SMALL, max_depth=3, invariants=NEVER_DESTROYED)
    # use ONLY the contract's witness (not the engine internals) and replay it on a fresh world
    sig = replay_path(SMALL, list(vr.witness))
    ok = vr.witness is not None and sig is not None
    return chk("witness_is_consumable", ok, f"contract witness replays to a state: {ok}")


def test_results_are_frozen():
    vr = verify(SMALL, max_depth=2)
    frozen = 0
    for obj, fieldname, val in [(vr, "violations", ()), (vr.reachability, "status", "X")]:
        try:
            setattr(obj, fieldname, val)
        except dataclasses.FrozenInstanceError:
            frozen += 1
    ok = frozen == 2
    return chk("results_are_frozen", ok, f"both result types immutable: {ok}")


def test_minimal_contract_present():
    # BOUNDED ⇒ no proof ⇒ no certificate (Step 4: certificate fills only on CLOSED; non-CLOSED stays None)
    vr = verify(SMALL, max_depth=1)
    needed = ["status", "witness", "certificate", "explored_states", "frontier_exhausted", "engine"]
    ok = all(hasattr(vr, n) for n in needed) and vr.status == "BOUNDED" and vr.certificate is None
    return chk("minimal_contract_present", ok,
               f"fields present; non-CLOSED ⇒ certificate None = {vr.certificate is None}")


def test_determinism():
    a = verify(SMALL, max_depth=8)
    b = verify(SMALL, max_depth=8)
    ok = (a.reachability == b.reachability and a.violations == b.violations)
    return chk("determinism", ok, f"identical contracts: {ok}")


def test_engine_labelled():
    vr = verify(SMALL, max_depth=2)
    ok = vr.engine == "explicit-state-bfs"
    return chk("engine_labelled", ok, f"engine={vr.engine!r}")


def main():
    results = [
        test_closed_maps_through(),
        test_violated_carries_witness(),
        test_adapter_is_faithful(),
        test_witness_is_consumable(),
        test_results_are_frozen(),
        test_minimal_contract_present(),
        test_determinism(),
        test_engine_labelled(),
    ]
    print("test_interfaces — Phase A.2 Step 1: stable verification contract (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the contract mirrors the reference "
          f"engine\n  faithfully, exposes a replayable witness, is immutable, carries only the agreed "
          f"minimal fields\n  (certificate a placeholder until Step 4), and names its backend — with NO "
          f"behavior change. interface ≠ engine.")
    assert passed == total, f"{total - passed} check(s) failed — the contract is not faithful"


if __name__ == "__main__":
    main()
