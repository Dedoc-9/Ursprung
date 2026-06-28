# SPDX-License-Identifier: AGPL-3.0-only
"""
test_stream_auditor.py — the backend makes both chokepoints inescapable (validity-not-outcome). Pure-stdlib.

  1. channel_promotes          — a real inter-channel stream (survives (Z,W)) → CHANNEL → promote() runs.
  2. fragile_refused_atomic    — a missing-confounder stream → MISSPEC → promote() raises UngroundedError,
                                action NOT run (state pristine).
  3. healthy_refused           — a confounder-explained stream → HEALTHY → promote() refused (nothing to act on).
  4. windows_emit_analysisresults — every window's answer is an AnalysisResult with scope + ≥1 limitation.
  5. panel_no_scalar           — audit_stream returns one witness per window and carries NO fused confidence
                                scalar field (disagreement reported side by side).
  6. ledger_honest             — the per-window findings form an honest claim_ledger (graded + falsifiable).
  7. frontier_attrition        — coverage depletes window-over-window → a late window's frontier ≠ EXPLOIT
                                (bounded PIVOT, metric deflation honored).
  8. determinism               — re-auditing a window agrees.

Sound iff 8/8: answers are AnalysisResults, actions pass the Grounded gate (only a confirmed CHANNEL promotes;
HEALTHY/MISSPEC are refused atomically), the panel stays plural, and coverage attrition is tracked.
`router ≠ verifier`; `residual-CMI ≠ channel`; `proves-the-procedure ≠ proves-the-fault`.

Run:  python3 test_stream_auditor.py     (~tens of seconds — windowed CMI + nulls)
"""
from __future__ import annotations

from dataclasses import fields

from stream_auditor import (CausalStreamAuditor, ChannelSpec, SPEC, WindowResult,
                            gen_healthy, gen_channel, gen_fragile)
from epistemic_types import UngroundedError
from claim_ledger import audit_ledger
from artifacts import AnalysisResult, Limitation


def chk(name, ok, detail):
    return (name, ok, detail)


def _one(stream):
    a = CausalStreamAuditor(SPEC, window=len(stream))
    return a, a.audit_stream(stream)[0]


def test_channel_promotes():
    a, wr = _one(gen_channel(4000))
    log = []
    ran = False
    try:
        a.promote(wr, lambda w: log.append(w.index)); ran = True
    except UngroundedError:
        ran = False
    ok = wr.decision == "CHANNEL" and ran and log == [0]
    return chk("channel_promotes", ok, f"decision={wr.decision} promoted={ran}")


def test_fragile_refused_atomic():
    a, wr = _one(gen_fragile(4000))
    log = []
    raised = False
    try:
        a.promote(wr, lambda w: log.append(w.index))
    except UngroundedError:
        raised = True
    ok = wr.decision == "MISSPEC" and raised and log == []
    return chk("fragile_refused_atomic", ok, f"decision={wr.decision} refused={raised} log={log}")


def test_healthy_refused():
    a, wr = _one(gen_healthy(4000))
    raised = False
    try:
        a.promote(wr, lambda w: w)
    except UngroundedError:
        raised = True
    ok = wr.decision == "HEALTHY" and raised
    return chk("healthy_refused", ok, f"decision={wr.decision} refused={raised}")


def test_windows_emit_analysisresults():
    a = CausalStreamAuditor(SPEC, window=4000)
    results = a.audit_stream(gen_healthy(4000) + gen_channel(4000))
    bad = [wr.index for wr in results if not (isinstance(wr.analysis, AnalysisResult)
           and wr.analysis.scope and len(wr.analysis.limitations) >= 1
           and all(isinstance(l, Limitation) for l in wr.analysis.limitations))]
    return chk("windows_emit_analysisresults", not bad, f"non-honest windows: {bad or 'none'}")


def test_panel_no_scalar():
    a = CausalStreamAuditor(SPEC, window=4000)
    results = a.audit_stream(gen_healthy(4000) + gen_channel(4000))
    names = {f.name for f in fields(WindowResult)}
    ok = isinstance(results, list) and len(results) == 2 and not (names & {"score", "confidence", "fused"})
    return chk("panel_no_scalar", ok, f"{len(results)} witnesses; no scalar field present={not (names & {'score','confidence','fused'})}")


def test_ledger_honest():
    a = CausalStreamAuditor(SPEC, window=4000)
    a.audit_stream(gen_healthy(4000) + gen_channel(4000) + gen_fragile(4000))
    ok = audit_ledger(a.ledger())["honest"]
    return chk("ledger_honest", ok, f"per-window claim ledger honest={ok}")


def test_frontier_attrition():
    a = CausalStreamAuditor(SPEC, window=2000)
    results = a.audit_stream(gen_healthy(8000))          # small (x,y) support ⇒ coverage saturates fast
    late = [wr.frontier for wr in results[1:]]
    ok = any(f != "EXPLOIT" for f in late)               # depletion detected (PIVOT/HOLD), bounded
    return chk("frontier_attrition", ok, f"late-window frontier decisions={late}")


def test_determinism():
    _a, wr1 = _one(gen_channel(4000))
    _b, wr2 = _one(gen_channel(4000))
    ok = wr1.decision == wr2.decision
    return chk("determinism", ok, f"repeated decision agrees: {ok}")


def main():
    results = [
        test_channel_promotes(),
        test_fragile_refused_atomic(),
        test_healthy_refused(),
        test_windows_emit_analysisresults(),
        test_panel_no_scalar(),
        test_ledger_honest(),
        test_frontier_attrition(),
        test_determinism(),
    ]
    print("test_stream_auditor — Causal Stream Auditor (both chokepoints inescapable)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: only a confirmed CHANNEL promotes; HEALTHY/"
          f"MISSPEC are refused\n  atomically; answers are AnalysisResults; the panel stays plural; coverage "
          f"attrition is tracked.\n  router ≠ verifier; residual-CMI ≠ channel; integrity ≠ truth.")
    assert passed == total, f"{total - passed} check(s) failed — backend chokepoints not enforced"


if __name__ == "__main__":
    main()
