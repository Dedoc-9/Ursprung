# SPDX-License-Identifier: AGPL-3.0-only
"""
test_engine.py — Phase A.2 Step 3 proofs (validity-not-outcome): the engine abstraction preserves
semantics and keeps the three roles separate.

The existing suites (test_kernel_check / test_interfaces / test_transition / test_diagnose) are the real
regression guard — if they stay green, `check()`'s delegation changed no behavior. These add the new
engine surface:

  1. verify_returns_contract  — engine.verify(model, options) returns a VerificationResult, engine-labelled
  2. engine_matches_shim      — engine.run(...) equals kernel_check.check(...) (status/states/transitions)
  3. closed_case              — a tiny world closes: CLOSED, exhaustive, known state count
  4. bounded_case             — a shallow bound on a big world is BOUNDED (truncated), not a false CLOSED
  5. violated_case            — a false invariant yields VIOLATED with a witness via the contract
  6. model_options_shape      — WorldModel carries the 4 fields; VerificationOptions defaults; both frozen
  7. relation_unaware         — TransitionRelation exposes no search concerns (no god object)
  8. determinism              — two verify() calls produce equal contracts

Run:  python3 test_engine.py
"""
from __future__ import annotations

import dataclasses

from engine import (ExplicitStateBFSEngine, WorldModel, VerificationOptions, build_model)
from interfaces import VerificationResult
from kernel_check import check, DEMO_WORLD

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


def test_verify_returns_contract():
    vr = ExplicitStateBFSEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=8))
    ok = isinstance(vr, VerificationResult) and vr.engine == "explicit-state-bfs"
    return chk("verify_returns_contract", ok, f"VerificationResult engine={vr.engine!r} status={vr.status}")


def test_engine_matches_shim():
    eng = ExplicitStateBFSEngine()
    re_closed = eng.run(build_model(SMALL), VerificationOptions(depth_bound=8))
    sh_closed = check(SMALL, max_depth=8)
    re_viol = eng.run(build_model(SMALL, invariants=NEVER_DESTROYED), VerificationOptions(depth_bound=3))
    sh_viol = check(SMALL, max_depth=3, invariants=NEVER_DESTROYED)
    ok = ((re_closed.status, re_closed.states_explored, re_closed.transitions)
          == (sh_closed.status, sh_closed.states_explored, sh_closed.transitions)
          and (re_viol.status, len(re_viol.violations)) == (sh_viol.status, len(sh_viol.violations)))
    return chk("engine_matches_shim", ok,
               f"engine.run == check(): closed {re_closed.status}/{re_closed.states_explored}, viol {re_viol.status}")


def test_closed_case():
    r = ExplicitStateBFSEngine().run(build_model(SMALL), VerificationOptions(depth_bound=8))
    ok = r.status == "CLOSED" and r.states_explored == 5 and not r.truncated
    return chk("closed_case", ok, f"{r.status}, {r.states_explored} states, truncated={r.truncated}")


def test_bounded_case():
    vr = ExplicitStateBFSEngine().verify(build_model(DEMO_WORLD), VerificationOptions(depth_bound=1))
    ok = vr.status == "BOUNDED" and not vr.frontier_exhausted
    return chk("bounded_case", ok, f"{vr.status}, frontier_exhausted={vr.frontier_exhausted}")


def test_violated_case():
    vr = ExplicitStateBFSEngine().verify(build_model(SMALL, invariants=NEVER_DESTROYED),
                                         VerificationOptions(depth_bound=3))
    ok = vr.status == "VIOLATED" and isinstance(vr.witness, tuple) and len(vr.witness) >= 1
    return chk("violated_case", ok, f"{vr.status}, witness={vr.witness}")


def test_model_options_shape():
    m = build_model(SMALL)
    o = VerificationOptions()
    has_fields = all(hasattr(m, f) for f in ("initial_state", "transition_relation", "invariants", "action_alphabet"))
    defaults = (o.depth_bound == 6 and o.stop_on_first is True)
    frozen = 0
    for obj, fld, val in [(m, "invariants", {}), (o, "depth_bound", 1)]:
        try:
            setattr(obj, fld, val)
        except dataclasses.FrozenInstanceError:
            frozen += 1
    ok = has_fields and defaults and frozen == 2
    return chk("model_options_shape", ok, f"fields={has_fields} defaults={defaults} frozen={frozen == 2}")


def test_relation_unaware():
    tr = build_model(SMALL).transition_relation
    search_attrs = ["queue", "visited", "frontier", "verify", "run", "depth_bound"]
    ok = not any(hasattr(tr, x) for x in search_attrs) and hasattr(tr, "successors")
    return chk("relation_unaware", ok, f"relation has no search concerns: {ok}")


def test_determinism():
    a = ExplicitStateBFSEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=8))
    b = ExplicitStateBFSEngine().verify(build_model(SMALL), VerificationOptions(depth_bound=8))
    ok = a.reachability == b.reachability and a.violations == b.violations
    return chk("determinism", ok, f"identical contracts: {ok}")


def main():
    results = [
        test_verify_returns_contract(),
        test_engine_matches_shim(),
        test_closed_case(),
        test_bounded_case(),
        test_violated_case(),
        test_model_options_shape(),
        test_relation_unaware(),
        test_determinism(),
    ]
    print("test_engine — Phase A.2 Step 3: engine abstraction (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the engine returns the public contract, "
          f"its\n  results match the legacy shim exactly, CLOSED/BOUNDED/VIOLATED reproduce, the model/options "
          f"objects\n  hold the bundle, and TransitionRelation carries NO search concerns — one BFS, behind one "
          f"interface.\n  engine ≠ semantics; moved ≠ changed.")
    assert passed == total, f"{total - passed} check(s) failed — the engine abstraction changed behavior"


if __name__ == "__main__":
    main()
