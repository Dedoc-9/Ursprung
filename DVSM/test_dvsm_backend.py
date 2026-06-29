# SPDX-License-Identifier: AGPL-3.0-only
"""
test_dvsm_backend.py — the backend makes both chokepoints inescapable over a DVSM telemetry trace.
Validity-not-outcome. Pure-stdlib (~a minute — windowed CMI + nulls over multiple couplings).

  1. clean_window_certifies      — a clean window is air-gap-held ⇒ certify_clean() runs.
  2. contaminated_refused_atomic — an Ω→V window ⇒ certify_clean() raises UngroundedError, action NOT run.
  3. contamination_surfaced      — the contaminated window reports 'omega_to_v' in contamination().
  4. windows_emit_analysis       — every window emits AnalysisResults (scope + ≥1 limitation), one per coupling.
  5. panel_no_scalar             — WindowResult carries NO fused confidence/score field; couplings side by side.
  6. ledger_honest               — the per-window claims form an honest claim_ledger.
  7. frontier_tracked            — windows after the first carry a bounded frontier decision (EXPLOIT/PIVOT/HOLD).
  8. determinism                 — re-auditing a stream agrees.

Sound iff 8/8: only an air-gap-held window may be certified controller-safe; a contaminated window is refused
atomically; answers are AnalysisResults; the panel stays plural. `observation ≠ authority`; `router ≠ verifier`.
"""
from __future__ import annotations

from dataclasses import fields

from dvsm_backend import DvsmTraceAuditor, WindowResult, WINDOW
from dvsm_reference import gen_clean, gen_contaminated
from epistemic_types import UngroundedError
from artifacts import AnalysisResult, Limitation
from claim_ledger import audit_ledger


def chk(name, ok, detail):
    return (name, ok, detail)


def _clean_window():
    a = DvsmTraceAuditor(window=WINDOW)
    return a, a.audit_stream(gen_clean(WINDOW, seed=1))[0]


def _contaminated_window():
    a = DvsmTraceAuditor(window=WINDOW)
    return a, a.audit_stream(gen_contaminated("omega_to_v", WINDOW, seed=2))[0]


def test_clean_window_certifies():
    a, wr = _clean_window()
    log = []
    ran = False
    try:
        a.certify_clean(wr, "omega_to_v", lambda w: log.append(w.index)); ran = True
    except UngroundedError:
        ran = False
    ok = wr.air_gap_held() and ran and log == [0]
    return chk("clean_window_certifies", ok, f"air_gap_held={wr.air_gap_held()} certified={ran}")


def test_contaminated_refused_atomic():
    a, wr = _contaminated_window()
    log = []
    raised = False
    try:
        a.certify_clean(wr, "omega_to_v", lambda w: log.append(w.index))
    except UngroundedError:
        raised = True
    ok = raised and log == []
    return chk("contaminated_refused_atomic", ok, f"refused={raised} log={log}")


def test_contamination_surfaced():
    _a, wr = _contaminated_window()
    ok = "omega_to_v" in wr.contamination()
    return chk("contamination_surfaced", ok, f"contamination={wr.contamination()}")


def test_windows_emit_analysis():
    a = DvsmTraceAuditor(window=WINDOW)
    results = a.audit_stream(gen_clean(WINDOW, seed=1) + gen_contaminated("omega_to_v", WINDOW, seed=2))
    bad = []
    for wr in results:
        for an in wr.analyses:
            if not (isinstance(an, AnalysisResult) and an.scope and len(an.limitations) >= 1
                    and all(isinstance(l, Limitation) for l in an.limitations)):
                bad.append(wr.index)
    return chk("windows_emit_analysis", not bad, f"non-honest windows: {sorted(set(bad)) or 'none'}")


def test_panel_no_scalar():
    a = DvsmTraceAuditor(window=WINDOW)
    results = a.audit_stream(gen_clean(WINDOW, seed=1) + gen_clean(WINDOW, seed=9))
    names = {f.name for f in fields(WindowResult)}
    ok = isinstance(results, list) and len(results) == 2 and not (names & {"score", "confidence", "fused"})
    return chk("panel_no_scalar", ok, f"{len(results)} windows; no scalar field={not (names & {'score','confidence','fused'})}")


def test_ledger_honest():
    a = DvsmTraceAuditor(window=WINDOW)
    a.audit_stream(gen_clean(WINDOW, seed=1) + gen_contaminated("omega_to_v", WINDOW, seed=2))
    ok = audit_ledger(a.ledger())["honest"]
    return chk("ledger_honest", ok, f"claim ledger honest={ok}")


def test_frontier_tracked():
    a = DvsmTraceAuditor(window=WINDOW)
    results = a.audit_stream(gen_clean(WINDOW, seed=1) + gen_clean(WINDOW, seed=9) + gen_clean(WINDOW, seed=3))
    late = [wr.frontier for wr in results[1:]]
    ok = all(f in ("EXPLOIT", "PIVOT", "HOLD") for f in late) and len(late) >= 1
    return chk("frontier_tracked", ok, f"late-window frontier decisions={late}")


def test_determinism():
    a1 = DvsmTraceAuditor(window=WINDOW); r1 = a1.audit_stream(gen_contaminated("omega_to_v", WINDOW, seed=2))[0]
    a2 = DvsmTraceAuditor(window=WINDOW); r2 = a2.audit_stream(gen_contaminated("omega_to_v", WINDOW, seed=2))[0]
    ok = r1.contamination() == r2.contamination()
    return chk("determinism", ok, f"repeated contamination agrees: {ok}")


def main():
    results = [
        test_clean_window_certifies(),
        test_contaminated_refused_atomic(),
        test_contamination_surfaced(),
        test_windows_emit_analysis(),
        test_panel_no_scalar(),
        test_ledger_honest(),
        test_frontier_tracked(),
        test_determinism(),
    ]
    print("test_dvsm_backend — DVSM Trace Auditor (both chokepoints inescapable over telemetry)\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. only an air-gap-held window may be certified; contamination is refused\n"
          f"  atomically; answers are AnalysisResults; the panel stays plural. observation ≠ authority.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
