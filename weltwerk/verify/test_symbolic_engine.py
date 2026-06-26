# SPDX-License-Identifier: AGPL-3.0-only
"""
test_symbolic_engine.py — Phase A.2 Step 5 proofs (validity-not-outcome): the symbolic engine is a faithful
second engine behind the same contract. SKIPS cleanly if the optional solver is absent.

  1. engine_labelled            — names a symbolic backend (so consumers/differential can tell engines apart)
  2. no_z3_in_engine            — symbolic_engine.py does not import z3 (solver is confined to the adapter)
  3. violated_witness_extracted — VIOLATED yields a witness + a Trace
  4. witness_replays_to_violation — the witness replays to its trace terminal, which violates an invariant
  5. witness_is_shortest        — symbolic witness length == explicit shortest ghost length
  6. closed_equivalence         — CLOSED status + explored count match the explicit engine
  7. bounded_equivalence        — a shallow bound is BOUNDED in both engines
  8. no_unsat_status            — status is only ever CLOSED/BOUNDED/VIOLATED (no new epistemic class)

Run:  python3 test_symbolic_engine.py
"""
from __future__ import annotations

import solver_adapter

if not solver_adapter.HAVE_SOLVER:
    print("test_symbolic_engine — SKIPPED: optional solver not installed. `pip install z3-solver` to run.")
    raise SystemExit(0)

import symbolic_engine
from symbolic_engine import SymbolicEngine
from engine import build_model, VerificationOptions, ExplicitStateBFSEngine
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

NEVER = {"nothing_ever_destroyed": (lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime))}


def chk(name, ok, detail):
    return (name, ok, detail)


def _violated():
    return SymbolicEngine().verify(build_model(SMALL, invariants=NEVER), VerificationOptions(depth_bound=3))


def test_engine_labelled():
    vr = SymbolicEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=8))
    ok = vr.engine.startswith("symbolic-bmc")
    return chk("engine_labelled", ok, f"engine={vr.engine!r}")


def test_no_z3_in_engine():
    ok = not hasattr(symbolic_engine, "z3")          # solver confined to solver_adapter
    return chk("no_z3_in_engine", ok, f"symbolic_engine imports no z3: {ok}")


def test_violated_witness_extracted():
    vr = _violated()
    ok = vr.status == "VIOLATED" and isinstance(vr.witness, tuple) and len(vr.witness) >= 1 and vr.trace is not None
    return chk("violated_witness_extracted", ok, f"status={vr.status} witness={vr.witness}")


def test_witness_replays_to_violation():
    vr = _violated()
    sig = replay_path(SMALL, list(vr.witness))
    ok = sig == vr.trace.terminal_state and len(vr.violations) >= 1
    return chk("witness_replays_to_violation", ok, f"replay==terminal: {sig == vr.trace.terminal_state}; viol={vr.violations}")


def test_witness_is_shortest():
    sy = _violated()
    ex = check(SMALL, max_depth=3, invariants=NEVER)
    ok = len(sy.witness) == len(ex.ghost.path)
    return chk("witness_is_shortest", ok, f"symbolic len {len(sy.witness)} == explicit len {len(ex.ghost.path)}")


def test_closed_equivalence():
    sy = SymbolicEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=8))
    ex = ExplicitStateBFSEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=8))
    ok = sy.status == ex.status == "CLOSED" and sy.explored_states == ex.explored_states
    return chk("closed_equivalence", ok, f"both CLOSED, explored {sy.explored_states}=={ex.explored_states}")


def test_bounded_equivalence():
    sy = SymbolicEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=1))
    ex = ExplicitStateBFSEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=1))
    ok = sy.status == ex.status == "BOUNDED"
    return chk("bounded_equivalence", ok, f"both BOUNDED: {ok}")


def test_no_unsat_status():
    statuses = set()
    for d, inv in [(8, None), (1, None), (3, NEVER)]:
        statuses.add(SymbolicEngine().verify(build_model(SMALL, invariants=inv), VerificationOptions(depth_bound=d)).status)
    ok = statuses <= {"CLOSED", "BOUNDED", "VIOLATED"}
    return chk("no_unsat_status", ok, f"statuses seen: {sorted(statuses)}")


def main():
    results = [
        test_engine_labelled(),
        test_no_z3_in_engine(),
        test_violated_witness_extracted(),
        test_witness_replays_to_violation(),
        test_witness_is_shortest(),
        test_closed_equivalence(),
        test_bounded_equivalence(),
        test_no_unsat_status(),
    ]
    print("test_symbolic_engine — Phase A.2 Step 5: SMT-backed second engine (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a second (SMT) engine, z3 confined to the "
          f"adapter,\n  returns the same public status, extracts a shortest witness that REPLAYS through the "
          f"proven relation,\n  matches the explicit engine on CLOSED/BOUNDED, and introduces no new status. "
          f"engine ≠ semantics.")
    assert passed == total, f"{total - passed} check(s) failed — the symbolic engine is not faithful"


if __name__ == "__main__":
    main()
