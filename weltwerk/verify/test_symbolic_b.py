# SPDX-License-Identifier: AGPL-3.0-only
"""
test_symbolic_b.py — differential gate for Approach B (CANDIDATE). SKIPS cleanly if z3 is absent.

Approach B re-encodes apply_event directly in SMT, so it is a SECOND expression of the semantics. This suite
is the gate that decides whether that re-encoding is faithful: it compares the direct-SMT engine against the
explicit reference, ONE-DIRECTIONALLY (B is a violation accelerator, it does not claim CLOSED).

  1. b_finds_violation         — on a violable world, B returns VIOLATED with a witness
  2. b_matches_explicit_length — B's shortest witness length == the explicit engine's shortest ghost length
  3. b_witness_replays         — replaying B's witness disables the target (the violation is real, not an artifact)
  4. b_no_false_violation      — on a world with no path to the violation, B returns no VIOLATED (BOUNDED)
  5. b_determinism             — two B runs agree on status and witness length

If these pass, Approach B is faithful on the tested fragment; only then is it a supported engine.

Run:  python3 test_symbolic_b.py
"""
from __future__ import annotations

import solver_adapter_b

if not solver_adapter_b.HAVE_SOLVER:
    print("test_symbolic_b — SKIPPED: optional solver not installed. `pip install z3-solver` to run.")
    raise SystemExit(0)

from symbolic_engine_b import SymbolicDirectEngine, SymbolicInvariant
from engine import build_model, VerificationOptions
from kernel_check import check
from world_sim import WorldSim

STAR = ('world "B1"\n'
        'entity fac:\n  position 0 0 0\n  controls hub\n'
        'entity hub:\n  position 1 0 0\n  health 10\n  powers tail\n'
        'entity tail:\n  position 2 0 0\n  health 10\n')

# tail is isolated ⇒ nothing can disable it ⇒ no violation reachable
NOVIO = ('world "B2"\n'
         'entity fac:\n  position 0 0 0\n  controls a\n'
         'entity a:\n  position 1 0 0\n  health 10\n  powers b\n'
         'entity b:\n  position 2 0 0\n  health 10\n'
         'entity tail:\n  position 3 0 0\n  health 10\n')

TAIL_OK = {"tail_ok": (lambda sim: sim.runtime["tail"]["status"] != "disabled")}
INV = SymbolicInvariant("not_disabled", "tail")
ENG = SymbolicDirectEngine(INV)


def chk(name, ok, detail):
    return (name, ok, detail)


def _replay_tail_status(world, events):
    sim = WorldSim(world)
    for e in events:
        sim.apply_event(*e)
    return sim.runtime["tail"]["status"]


def test_b_finds_violation():
    vr = ENG.verify(build_model(STAR), VerificationOptions(depth_bound=4))
    ok = vr.status == "VIOLATED" and isinstance(vr.witness, tuple) and len(vr.witness) >= 1
    return chk("b_finds_violation", ok, f"status={vr.status} witness={vr.witness}")


def test_b_matches_explicit_length():
    vr = ENG.verify(build_model(STAR), VerificationOptions(depth_bound=4))
    ex = check(STAR, max_depth=4, invariants=TAIL_OK)
    ok = ex.ghost is not None and len(vr.witness) == len(ex.ghost.path)
    return chk("b_matches_explicit_length", ok,
               f"B len={len(vr.witness)} == explicit len={len(ex.ghost.path) if ex.ghost else None}")


def test_b_witness_replays():
    vr = ENG.verify(build_model(STAR), VerificationOptions(depth_bound=4))
    ok = _replay_tail_status(STAR, list(vr.witness)) == "disabled"
    return chk("b_witness_replays", ok, f"replaying B witness ⇒ tail status = {_replay_tail_status(STAR, list(vr.witness))}")


def test_b_no_false_violation():
    vr = ENG.verify(build_model(NOVIO), VerificationOptions(depth_bound=4))
    ok = vr.status != "VIOLATED" and vr.witness is None
    return chk("b_no_false_violation", ok, f"isolated tail ⇒ status={vr.status} (no false VIOLATED)")


def test_b_determinism():
    a = ENG.verify(build_model(STAR), VerificationOptions(depth_bound=4))
    b = ENG.verify(build_model(STAR), VerificationOptions(depth_bound=4))
    ok = a.status == b.status and len(a.witness or ()) == len(b.witness or ())
    return chk("b_determinism", ok, f"identical status + witness length: {ok}")


def main():
    results = [
        test_b_finds_violation(),
        test_b_matches_explicit_length(),
        test_b_witness_replays(),
        test_b_no_false_violation(),
        test_b_determinism(),
    ]
    print("test_symbolic_b — Approach B (direct apply_event→SMT) differential gate (CANDIDATE)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the direct-SMT re-encoding finds the same "
          f"shortest\n  violations as the explicit engine, the witnesses REPLAY to a real disabled state, and it "
          f"raises no\n  false violation. Only then is Approach B faithful on this fragment. re-encoded ≠ verified.")
    assert passed == total, f"{total - passed} check(s) failed — Approach B is not faithful (do not promote)"


if __name__ == "__main__":
    main()
