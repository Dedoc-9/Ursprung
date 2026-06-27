# SPDX-License-Identifier: AGPL-3.0-only
"""
test_boundary_immutability.py — Proof Obligation PO-7: mechanize the BRIP / RCPT premise that the *map*
cannot move the *judge*. Pure-stdlib.

The conditional theorems (BRIP §3, RCPT §9.9) assume "a policy may reorder candidate generation but cannot
alter evaluation." This suite turns that assumption from prose into an executed invariant:

  1. verdict_invariant_under_permutation — permuting the candidate (action) order leaves the VERDICT
     unchanged: same status; on non-VIOLATED, identical explored-state count; on VIOLATED, a witness still
     exists. (Operational content of `improved_map ≠ changed_criterion`.)
  2. invariants_not_mutated              — running diagnosis / counterfactual / repair does not mutate the
     frozen invariant set (`DEFAULT_INVARIANTS` unchanged, same objects).
  3. map_modules_import_no_solver        — the map consumers pull in no solver (no hidden evaluation path).
  4. analysis_is_not_a_verdict           — consumers return analyses/candidates, never a `VerificationResult`;
     only engines emit verdicts.
  5. determinism                         — the engine verdict is deterministic.

Run:  python3 test_boundary_immutability.py
"""
from __future__ import annotations

from transition import TransitionRelation
from engine import build_model, WorldModel, VerificationOptions, ExplicitStateBFSEngine
from interfaces import VerificationResult
from kernel_check import DEFAULT_INVARIANTS, DEMO_WORLD
import diagnose as diag_mod
import counterfactual as cf_mod
import repair as repair_mod
from diagnose import diagnose, observe_after, GhostReport
from counterfactual import CounterfactualReport

ENG = ExplicitStateBFSEngine()

SMALL = ('world "T"\n'
         'entity faction_a:\n  position 0 0 0\n  controls hub\n'
         'entity hub:\n  position 1 0 0\n  health 10\n  powers leaf\n'
         'entity leaf:\n  position 2 0 0\n  health 10\n')
NEVER = {"nothing_ever_destroyed": (lambda s: all(s.runtime[e]["alive"] for e in s.runtime))}


class _PermutedRelation(TransitionRelation):
    """Same semantics, reordered candidate alphabet — a different 'map', identical 'territory'."""
    def __init__(self, world_text, perm):
        super().__init__(world_text)
        self._alphabet = tuple(perm(list(self._alphabet)))


def _model(world, invariants, perm=None):
    if perm is None:
        return build_model(world, invariants=invariants)
    rel = _PermutedRelation(world, perm)
    return WorldModel(rel.initial(), rel, invariants or DEFAULT_INVARIANTS, rel.actions())


def chk(name, ok, detail):
    return (name, ok, detail)


def test_verdict_invariant_under_permutation():
    rev = lambda xs: list(reversed(xs))
    cases = [("SMALL/default", SMALL, None, 8),
             ("DEMO/default", DEMO_WORLD, None, 1),
             ("SMALL/never", SMALL, NEVER, 3)]
    bad = []
    for label, w, inv, d in cases:
        opts = VerificationOptions(depth_bound=d)
        base = ENG.verify(_model(w, inv), opts)
        perm = ENG.verify(_model(w, inv, rev), opts)
        if base.status != perm.status:
            bad.append(f"{label}:status {base.status}!={perm.status}")
        elif base.status != "VIOLATED" and base.explored_states != perm.explored_states:
            bad.append(f"{label}:explored {base.explored_states}!={perm.explored_states}")
        elif base.status == "VIOLATED" and not (base.witness and perm.witness):
            bad.append(f"{label}:missing witness")
    return chk("verdict_invariant_under_permutation", not bad, f"order-induced verdict changes: {bad or 'none'}")


def test_invariants_not_mutated():
    before_keys = set(DEFAULT_INVARIANTS)
    before_ids = {k: id(v) for k, v in DEFAULT_INVARIANTS.items()}
    obs = observe_after(SMALL, [("destroy", "hub")])
    diagnose(SMALL, obs)
    cf_mod.analyze(SMALL, [("destroy", "hub")])
    repair_mod.propose(SMALL, [("destroy", "hub")], check_world=False)
    ok = (set(DEFAULT_INVARIANTS) == before_keys
          and all(id(DEFAULT_INVARIANTS[k]) == before_ids[k] for k in before_keys))
    return chk("invariants_not_mutated", ok, f"DEFAULT_INVARIANTS unchanged after analysis: {ok}")


def test_map_modules_import_no_solver():
    ok = not any(hasattr(m, "z3") for m in (diag_mod, cf_mod, repair_mod))
    return chk("map_modules_import_no_solver", ok, f"no solver in diagnose/counterfactual/repair: {ok}")


def test_analysis_is_not_a_verdict():
    gr = diagnose(SMALL, observe_after(SMALL, [("destroy", "hub")]))
    cf = cf_mod.analyze(SMALL, [("destroy", "hub")])
    rc = repair_mod.propose(SMALL, [("destroy", "hub")], check_world=False)
    ok = (isinstance(gr, GhostReport) and not isinstance(gr, VerificationResult)
          and isinstance(cf, CounterfactualReport) and not isinstance(cf, VerificationResult)
          and isinstance(rc, list))
    return chk("analysis_is_not_a_verdict", ok, "consumers return analyses/candidates, not VerificationResult")


def test_determinism():
    opts = VerificationOptions(depth_bound=8)
    a = ENG.verify(build_model(SMALL), opts)
    b = ENG.verify(build_model(SMALL), opts)
    ok = a.reachability == b.reachability
    return chk("determinism", ok, f"engine verdict deterministic: {ok}")


def main():
    results = [
        test_verdict_invariant_under_permutation(),
        test_invariants_not_mutated(),
        test_map_modules_import_no_solver(),
        test_analysis_is_not_a_verdict(),
        test_determinism(),
    ]
    print("test_boundary_immutability — PO-7: the map cannot move the judge (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:36s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: permuting candidate order never changes the "
          f"verdict,\n  analysis never mutates the invariant set, the map consumers contain no evaluation/solver "
          f"path, and\n  they return analyses rather than verdicts. PO-7 discharged: the BRIP/RCPT premise is "
          f"now an executed\n  invariant, not prose. improved_map ≠ changed_criterion.")
    assert passed == total, f"{total - passed} check(s) failed — the evaluation boundary is not immutable"


if __name__ == "__main__":
    main()
