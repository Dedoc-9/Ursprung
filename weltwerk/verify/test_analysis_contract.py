# SPDX-License-Identifier: AGPL-3.0-only
"""
test_analysis_contract.py — the shared honesty-contract proofs for AnalysisResult and the as_analysis()
adapters. Pure-stdlib.

  1. requires_limitation        — an AnalysisResult with no Limitation is rejected at construction
  2. requires_scope             — an AnalysisResult with empty scope is rejected
  3. records_frozen             — Finding / Limitation / AnalysisResult are immutable
  4. counterfactual_adapter     — CounterfactualReport.as_analysis() preserves the source trace, scope "trace", ≥1 limitation
  5. diagnosis_adapter          — GhostReport.as_analysis() has scope "observed-entities", findings, ≥1 limitation
  6. adapters_dont_mutate       — as_analysis() does not change the originating report
  7. every_adapter_has_limitation — both adapters carry ≥1 Limitation (honesty travels with the result)
  8. limitations_structured     — limitations are Limitation objects (scope + claim), not freeform strings

Run:  python3 test_analysis_contract.py
"""
from __future__ import annotations

import dataclasses

from artifacts import AnalysisResult, Finding, Limitation
from counterfactual import analyze
from diagnose import diagnose, observe_after
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

NEVER = {"nothing_ever_destroyed": (lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime))}


def chk(name, ok, detail):
    return (name, ok, detail)


def _cf_analysis():
    g = check(SMALL, max_depth=3, invariants=NEVER).ghost
    return analyze(SMALL, g.path, NEVER), g


def _dx_report():
    obs = observe_after(DEMO_WORLD, [("destroy", "reactor")])
    return diagnose(DEMO_WORLD, obs)


def test_requires_limitation():
    raised = False
    try:
        AnalysisResult(source_trace=(), scope="trace", findings=(), limitations=())
    except ValueError:
        raised = True
    return chk("requires_limitation", raised, f"empty limitations rejected: {raised}")


def test_requires_scope():
    raised = False
    try:
        AnalysisResult(source_trace=(), scope="", findings=(), limitations=(Limitation("trace", "x"),))
    except ValueError:
        raised = True
    return chk("requires_scope", raised, f"empty scope rejected: {raised}")


def test_records_frozen():
    a = AnalysisResult(source_trace=(), scope="trace", findings=(), limitations=(Limitation("trace", "x"),))
    f = Finding("T", "trace", "d")
    frozen = 0
    for obj, fld, val in [(a, "scope", "y"), (f, "type", "Z"), (a.limitations[0], "claim", "z")]:
        try:
            setattr(obj, fld, val)
        except dataclasses.FrozenInstanceError:
            frozen += 1
    return chk("records_frozen", frozen == 3, f"AnalysisResult/Finding/Limitation immutable: {frozen == 3}")


def test_counterfactual_adapter():
    rep, _g = _cf_analysis()
    a = rep.as_analysis()
    ok = (a.source_trace == rep.ghost_trace and a.scope == "trace" and len(a.limitations) >= 1
          and len(a.findings) >= 1)
    return chk("counterfactual_adapter", ok, f"scope={a.scope} trace-preserved={a.source_trace == rep.ghost_trace}")


def test_diagnosis_adapter():
    a = _dx_report().as_analysis()
    ok = a.scope == "observed-entities" and len(a.findings) >= 1 and len(a.limitations) >= 1
    return chk("diagnosis_adapter", ok, f"scope={a.scope} findings={len(a.findings)} limits={len(a.limitations)}")


def test_adapters_dont_mutate():
    rep, _g = _cf_analysis()
    before = (rep.critical, rep.redundant, rep.input_violates)
    rep.as_analysis()
    after = (rep.critical, rep.redundant, rep.input_violates)
    dx = _dx_report()
    n_before = len(dx.diagnoses)
    dx.as_analysis()
    ok = before == after and len(dx.diagnoses) == n_before
    return chk("adapters_dont_mutate", ok, f"originating reports unchanged: {ok}")


def test_every_adapter_has_limitation():
    cf, _g = _cf_analysis()
    ok = len(cf.as_analysis().limitations) >= 1 and len(_dx_report().as_analysis().limitations) >= 1
    return chk("every_adapter_has_limitation", ok, f"both adapters carry ≥1 limitation: {ok}")


def test_limitations_structured():
    a = _cf_analysis()[0].as_analysis()
    ok = all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations)
    return chk("limitations_structured", ok, f"limitations are structured (scope+claim): {ok}")


def main():
    results = [
        test_requires_limitation(),
        test_requires_scope(),
        test_records_frozen(),
        test_counterfactual_adapter(),
        test_diagnosis_adapter(),
        test_adapters_dont_mutate(),
        test_every_adapter_has_limitation(),
        test_limitations_structured(),
    ]
    print("test_analysis_contract — shared honesty contract for analysis consumers (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: every AnalysisResult requires a scope and "
          f"≥1 structured\n  Limitation, the records are immutable, and the diagnosis/counterfactual adapters "
          f"project into the\n  contract without mutating their reports. The honesty layer is shared, not "
          f"duplicated. analysis ≠ proof.")
    assert passed == total, f"{total - passed} check(s) failed — the analysis contract is not sound"


if __name__ == "__main__":
    main()
