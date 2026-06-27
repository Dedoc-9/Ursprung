# SPDX-License-Identifier: AGPL-3.0-only
"""
test_analysis_conformance.py — Proof Obligation PO-9: the honesty contract is UNIVERSAL across consumers.

`AnalysisResult` enforces, at construction, that every analysis carries a non-empty `scope` and ≥1
`Limitation` (artifacts.py __post_init__). PO-9 asks the harder question: does *every consumer* that emits an
analysis actually route through that contract? A single consumer that returned a bare, limitation-free verdict
would be a hole in the discipline — the place where over-confidence re-enters. This test exercises all three
analysis-producing modules through one parametrized loop:

    diagnose.GhostReport.as_analysis        (observation-based)
    counterfactual.CounterfactualReport.as_analysis   (trace-based)
    repair.RepairCandidate.as_analysis      (bounded-world-based)

and asserts each yields a well-formed, honest AnalysisResult. It also re-asserts the construction guard so the
contract cannot be bypassed by building an AnalysisResult directly. `analysis ≠ verdict`; honesty travels with
the result, for every consumer, or the contract is decorative.

Run:  python3 test_analysis_conformance.py
"""
from __future__ import annotations

import diagnose
import counterfactual
import repair
from kernel_check import check, DEMO_WORLD
from artifacts import AnalysisResult, Finding, Limitation


# north_territory not disabled — a real, violable invariant on DEMO_WORLD (cf. repair.main)
NORTH_OK = {"north_ok": (lambda s: s.runtime["north_territory"]["status"] != "disabled")}


def _consumers():
    """One AnalysisResult from each producing module, built from real runs (not hand-stitched)."""
    out = []

    # 1) diagnose — observation after a known fault
    obs = diagnose.observe_after(DEMO_WORLD, [("destroy", "reactor")])
    out.append(("diagnose", diagnose.diagnose(DEMO_WORLD, obs, trace=[("destroy", "reactor")]).as_analysis()))

    # 2) counterfactual — over a real ghost trace
    g = check(DEMO_WORLD, max_depth=3, invariants=NORTH_OK).ghost
    out.append(("counterfactual", counterfactual.analyze(DEMO_WORLD, g.path, NORTH_OK).as_analysis()))

    # 3) repair — a candidate from the counterfactual critical set, with bounded-world evidence
    cands = repair.propose(DEMO_WORLD, g.path, NORTH_OK, bound=8)
    assert cands, "expected at least one repair candidate to exercise repair.as_analysis"
    out.append(("repair", cands[0].as_analysis()))
    return out


def chk(name, ok, detail):
    return (name, ok, detail)


def test_all_consumers_are_analysis_results():
    bad = [n for n, a in _consumers() if not isinstance(a, AnalysisResult)]
    return chk("all_are_analysis_results", not bad, f"non-AnalysisResult consumers: {bad or 'none'}")


def test_all_have_nonempty_scope():
    bad = [n for n, a in _consumers() if not a.scope]
    return chk("all_have_scope", not bad, f"empty-scope consumers: {bad or 'none'}")


def test_all_have_a_limitation():
    bad = [n for n, a in _consumers() if len(a.limitations) < 1]
    return chk("all_have_limitation", not bad, f"limitation-free consumers: {bad or 'none'}")


def test_limitations_are_well_formed():
    bad = []
    for n, a in _consumers():
        for lim in a.limitations:
            if not isinstance(lim, Limitation) or not lim.scope or not lim.claim:
                bad.append(n)
                break
    return chk("limitations_well_formed", not bad, f"malformed-limitation consumers: {bad or 'none'}")


def test_findings_present():
    # an honest analysis still states SOMETHING (even "no hypothesis"/"no violation" is a Finding)
    bad = [n for n, a in _consumers() if len(a.findings) < 1]
    return chk("findings_present", not bad, f"finding-free consumers: {bad or 'none'}")


def test_construction_guard():
    # the contract cannot be bypassed: no scope, or no limitation ⇒ refuses to construct
    raised_scope = raised_lim = False
    try:
        AnalysisResult(source_trace=(), scope="", findings=(),
                       limitations=(Limitation("x", "y"),))
    except ValueError:
        raised_scope = True
    try:
        AnalysisResult(source_trace=(), scope="trace",
                       findings=(Finding("F", "trace", "m"),), limitations=())
    except ValueError:
        raised_lim = True
    ok = raised_scope and raised_lim
    return chk("construction_guard", ok, f"refuses empty scope={raised_scope}, refuses no-limitation={raised_lim}")


def main():
    results = [
        test_all_consumers_are_analysis_results(),
        test_all_have_nonempty_scope(),
        test_all_have_a_limitation(),
        test_limitations_are_well_formed(),
        test_findings_present(),
        test_construction_guard(),
    ]
    print("test_analysis_conformance — PO-9: honesty contract is universal across consumers\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: diagnose, counterfactual, AND repair each route "
          f"through\n  the AnalysisResult contract (scope + ≥1 well-formed Limitation + a Finding), and the contract "
          f"cannot\n  be bypassed by direct construction. No consumer emits a limitation-free verdict. "
          f"analysis ≠ verdict.")
    assert passed == total, f"{total - passed} check(s) failed — honesty-contract universality not established"


if __name__ == "__main__":
    main()
