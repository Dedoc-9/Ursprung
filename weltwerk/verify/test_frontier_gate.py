# SPDX-License-Identifier: AGPL-3.0-only
"""
test_frontier_gate.py — the frontier gate is a sound sensor + trigger, and HONEST about being bounded.

  1. classify_regimes       — CI entirely above 1 → SUPERCRITICAL; entirely below → SUBCRITICAL; crossing → NEAR.
  2. gate_decisions         — SUPERCRITICAL→EXPLOIT, SUBCRITICAL→PIVOT, NEAR_CRITICAL→HOLD.
  3. gated_beats_ungated    — pivoting on subcriticality keeps the frontier productive far longer than the
                             ungated trajectory that chokes in one basin.
  4. bounded_not_unbounded  — the gated run is BOUNDED by the number of orthogonal dimensions and SATURATES
                             (final regime SUBCRITICAL once dimensions are exhausted). No unbounded escape.
  5. pivot_recovers_then_depletes — a pivot resets m_novel above 1 (recovery), and within each basin m_novel
                             monotonically depletes. Recovery is real but each basin is finite.
  6. as_analysis_honest     — a decision projects to an AnalysisResult with scope + ≥1 limitation.
  7. determinism            — the planted run is deterministic.

Sound iff 7/7: the gate correctly reads the regime from the CI and triggers a pivot only when depletion is
established, the pivot yields bounded multi-basin gain over choking, and the apparatus is explicit that the
escape is bounded (PO-5 saturation), not unbounded, and that 'orthogonal dimension' is a model construct.
`estimate ≠ property`; `pivot ≠ guaranteed-escape`.

Run:  python3 test_frontier_gate.py
"""
from __future__ import annotations

from frontier_gate import (FrontierGate, classify_regime, run, _m_novel_at,
                           SUPERCRITICAL, SUBCRITICAL, NEAR_CRITICAL, EXPLOIT, PIVOT, HOLD)
from artifacts import AnalysisResult, Limitation

GATE = FrontierGate()


def chk(name, ok, detail):
    return (name, ok, detail)


def test_classify_regimes():
    ok = (classify_regime(1.7, 2.3) == SUPERCRITICAL
          and classify_regime(0.61, 0.83) == SUBCRITICAL
          and classify_regime(0.85, 1.15) == NEAR_CRITICAL)
    return chk("classify_regimes", ok, "CI above/below/crossing 1 → SUPER/SUB/NEAR")


def test_gate_decisions():
    ok = (GATE.decide(2.0, (1.7, 2.3)).action == EXPLOIT
          and GATE.decide(0.72, (0.61, 0.83)).action == PIVOT
          and GATE.decide(1.0, (0.85, 1.15)).action == HOLD)
    return chk("gate_decisions", ok, "EXPLOIT / PIVOT / HOLD by regime")


def test_gated_beats_ungated():
    g, u = run(gated=True), run(gated=False)
    ok = g["productive_steps"] > u["productive_steps"]
    return chk("gated_beats_ungated", ok,
               f"gated productive={g['productive_steps']} > ungated={u['productive_steps']}")


def test_bounded_not_unbounded():
    g = run(gated=True, dims=3)
    ok = g["basins_used"] <= g["dims"] and g["final_regime"] == SUBCRITICAL
    return chk("bounded_not_unbounded", ok,
               f"basins_used={g['basins_used']}≤dims={g['dims']}; final={g['final_regime']} (saturated, no infinite escape)")


def test_pivot_recovers_then_depletes():
    g = run(gated=True)
    tr = g["trace"]
    # a pivot is followed by a fresh basin whose m_novel recovers above the pre-pivot value and is supercritical
    recovered = False
    for i in range(len(tr) - 1):
        if tr[i][4] == PIVOT and tr[i + 1][0] == tr[i][0] + 1:
            if tr[i + 1][2] > tr[i][2] and tr[i + 1][3] == SUPERCRITICAL:
                recovered = True
                break
    # within a basin, m_novel depletes monotonically (k=0 > k=1 > k=2)
    depletes = _m_novel_at(0, 2.0, 0.6) > _m_novel_at(1, 2.0, 0.6) > _m_novel_at(2, 2.0, 0.6)
    return chk("pivot_recovers_then_depletes", recovered and depletes,
               f"pivot recovers m_novel={recovered}; within-basin depletion={depletes}")


def test_as_analysis_honest():
    a = GATE.as_analysis(GATE.decide(0.72, (0.61, 0.83)))
    ok = (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
          and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations))
    return chk("as_analysis_honest", ok, f"scope={a.scope!r} limitations={len(a.limitations)}")


def test_determinism():
    ok = run(gated=True) == run(gated=True)
    return chk("determinism", ok, f"repeated run agrees: {ok}")


def main():
    results = [
        test_classify_regimes(),
        test_gate_decisions(),
        test_gated_beats_ungated(),
        test_bounded_not_unbounded(),
        test_pivot_recovers_then_depletes(),
        test_as_analysis_honest(),
        test_determinism(),
    ]
    print("test_frontier_gate — m_novel subcriticality sensor + bounded pivot\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the gate reads the regime from the CI and "
          f"pivots only on\n  established depletion; pivoting beats choking but is BOUNDED by the dimensions and "
          f"saturates. The escape\n  is bounded, not unbounded; 'orthogonal dimension' is a model construct. "
          f"estimate ≠ property; pivot ≠ guaranteed-escape.")
    assert passed == total, f"{total - passed} check(s) failed — frontier gate not sound/honest"


if __name__ == "__main__":
    main()
