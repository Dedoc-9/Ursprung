# SPDX-License-Identifier: AGPL-3.0-only
"""
test_orchestrator.py — the orchestrator is a router + two chokepoints, with no new authority (validity-not-outcome).

  1. every_tool_returns_analysisresult — each registered tool's analyze() returns an AnalysisResult carrying the
                                        honesty contract (scope + ≥1 limitation).
  2. panel_keeps_witnesses_separate    — panel() returns one AnalysisResult per call, never an aggregate/scalar.
  3. enact_requires_grounding          — enact runs the action only for a grounded value; an ungrounded value
                                        raises UngroundedError BEFORE any effect (no commit).
  4. no_authority_added                — the orchestrator cannot enact what isn't grounded; it forwards results
                                        and grounds via the existing gate — it manufactures no "supported" verdict.
  5. unknown_tool_is_typed_error       — requesting an unregistered tool raises UnknownToolError, not a default.
  6. honesty_contract_enforced         — a tool that returns a non-honest object is rejected at the boundary.
  7. determinism                       — repeated analysis agrees.

Sound iff 7/7: answers are uniformly AnalysisResults, actions uniformly pass the Grounded gate, the panel stays
plural, and the orchestrator adds no authority. `orchestration ≠ authority`; `router ≠ verifier`.

Run:  python3 test_orchestrator.py
"""
from __future__ import annotations

from orchestrator import (default_orchestrator, EpistemicRuntimeOrchestrator, UnknownToolError,
                          ResidualTool, FrontierTool, LedgerTool, CertificateTool)
from artifacts import AnalysisResult, Limitation
from epistemic_types import Attested, UngroundedError
from residual_channel import demo_gen_null
from claim_ledger import Claim
from certificate_compiler import ConstraintCertificate, chain

_O = default_orchestrator()
_INIT, _SUCC, _UNI = chain(6)
_CALLS = [
    ("residual_channel", {"samples": demo_gen_null()}),
    ("frontier_gate", {"m_novel": 0.5, "ci": (0.42, 0.58)}),
    ("claim_ledger", {"ledger": (Claim("D1", "E reproduces", "ESTABLISHED", "M", "the magnitude", "a failed rep"),)}),
    ("certificate_compiler", {"init": _INIT, "successors": _SUCC, "universe": _UNI,
                              "cert": ConstraintCertificate("ok", lambda i: 0 <= i <= 6, lambda i: True)}),
]


def chk(name, ok, detail):
    return (name, ok, detail)


def _honest(a):
    return (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
            and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations))


def test_every_tool_returns_analysisresult():
    bad = [n for n, req in _CALLS if not _honest(_O.analyze(n, req))]
    return chk("every_tool_returns_analysisresult", not bad, f"non-honest tools: {bad or 'none'}")


def test_panel_keeps_witnesses_separate():
    p = _O.panel(_CALLS)
    ok = len(p) == len(_CALLS) and all(isinstance(v, AnalysisResult) for v in p.values())
    return chk("panel_keeps_witnesses_separate", ok, f"{len(p)} witnesses, side by side (no scalar)")


def test_enact_requires_grounding():
    log = []
    _O.enact("apply", Attested(True), lambda v: log.append(v))
    raised = False
    try:
        _O.enact("apply2", Attested(False), lambda v: log.append(v))
    except UngroundedError:
        raised = True
    ok = log == ["apply"] and raised
    return chk("enact_requires_grounding", ok, f"committed={log} ungrounded_raised={raised}")


def test_no_authority_added():
    # the orchestrator cannot enact an ungrounded value — it manufactures no permission of its own
    refused = False
    try:
        _O.enact("x", Attested(False), lambda v: v)
    except UngroundedError:
        refused = True
    return chk("no_authority_added", refused, f"ungrounded enaction refused: {refused}")


def test_unknown_tool_is_typed_error():
    raised = False
    try:
        _O.analyze("does_not_exist", {})
    except UnknownToolError:
        raised = True
    return chk("unknown_tool_is_typed_error", raised, f"UnknownToolError raised: {raised}")


def test_honesty_contract_enforced():
    class _BadTool:
        name = "bad"
        def analyze(self, request):
            return "not an AnalysisResult"
    o = EpistemicRuntimeOrchestrator().register(_BadTool())
    raised = False
    try:
        o.analyze("bad", {})
    except TypeError:
        raised = True
    return chk("honesty_contract_enforced", raised, f"non-honest result rejected at boundary: {raised}")


def test_determinism():
    a = _O.analyze("frontier_gate", {"m_novel": 0.5, "ci": (0.42, 0.58)})
    b = _O.analyze("frontier_gate", {"m_novel": 0.5, "ci": (0.42, 0.58)})
    ok = a.scope == b.scope and len(a.findings) == len(b.findings)
    return chk("determinism", ok, f"repeated analysis agrees: {ok}")


def main():
    results = [
        test_every_tool_returns_analysisresult(),
        test_panel_keeps_witnesses_separate(),
        test_enact_requires_grounding(),
        test_no_authority_added(),
        test_unknown_tool_is_typed_error(),
        test_honesty_contract_enforced(),
        test_determinism(),
    ]
    print("test_orchestrator — Epistemic Runtime Orchestrator (router + two chokepoints)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:34s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: answers are uniformly AnalysisResults, actions "
          f"uniformly pass the\n  Grounded gate, the panel stays plural (no scalar), and the orchestrator adds no "
          f"authority. orchestration ≠ authority; router ≠ verifier.")
    assert passed == total, f"{total - passed} check(s) failed — orchestrator not sound"


if __name__ == "__main__":
    main()
