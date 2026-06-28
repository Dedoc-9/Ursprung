# SPDX-License-Identifier: AGPL-3.0-only
"""
frontier_gate.py — Leap 3: turn frontier depletion into a control signal, honestly.

The repo's generativity work (`experiments/live_world_kernel/generativity_estimator.py`) measures `m_novel` =
net-new reachable verified states per verified parent (a frontier-expansion multiplier), and classifies a
domain by whether the CI of `m_novel` sits above / below / across 1. A trajectory that consumes its own local
frontier drives `m_novel` toward and below 1 (subcritical) — it chokes in a basin.

This module is the SENSOR + TRIGGER: a `FrontierGate` reads an `m_novel` estimate with its CI and emits a
control decision —

    SUPERCRITICAL (CI entirely above 1)  → EXPLOIT   (frontier still expanding; keep going)
    SUBCRITICAL   (CI entirely below 1)  → PIVOT     (frontier depleting; switch to an orthogonal dimension)
    NEAR_CRITICAL (CI crosses 1)         → HOLD      (UNDERDETERMINED; do not over-react)

WHAT THIS IS AND IS NOT (honest grading, no overclaim):
  • The sensor + trigger (classify a CI vs 1, decide EXPLOIT/PIVOT/HOLD): **DEMONSTRATED** (tested).
  • "Escape the basin" is **PLAUSIBLE and BOUNDED**, never unbounded. Pivoting to a fresh orthogonal dimension
    can recover `m_novel` above 1, but each new basin ALSO depletes, and the number of orthogonal dimensions is
    finite — so the gate buys *bounded, multi-basin* exploration, then saturates. This is consistent with the
    PO-5 result (iterated improvement saturates). We explicitly do NOT claim an inevitable subcritical collapse
    nor a fixed `m_novel ≈ 0.53`; the planted model's numbers are illustrative, not a finding.
  • "Orthogonal, unconfounded dimension" is a MODEL CONSTRUCT (Arbitrary-Boundary Law): here a pivot is a
    declared switch to a fresh basin; whether real problem dimensions are orthogonal/unconfounded is its own
    (unsolved) question. `estimate ≠ property`; `pivot ≠ guaranteed-escape`.

The gate is signal-agnostic: feed it `generativity_estimator`'s `(m_novel, CI)` or any other frontier estimate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

SUPERCRITICAL = "SUPERCRITICAL"
SUBCRITICAL = "SUBCRITICAL"
NEAR_CRITICAL = "NEAR_CRITICAL"
EXPLOIT = "EXPLOIT"
PIVOT = "PIVOT"
HOLD = "HOLD"


def classify_regime(ci_lo: float, ci_hi: float, floor: float = 1.0) -> str:
    """Regime from the CI of m_novel vs the critical floor (mirrors generativity_estimator.informativeness)."""
    if ci_lo > floor:
        return SUPERCRITICAL
    if ci_hi < floor:
        return SUBCRITICAL
    return NEAR_CRITICAL                  # CI crosses the floor ⇒ underdetermined


@dataclass(frozen=True)
class Decision:
    regime: str
    action: str
    m_novel: float
    ci: Tuple[float, float]


class FrontierGate:
    """Reads (m_novel, CI) and decides EXPLOIT / PIVOT / HOLD. The pivot trigger fires only when the CI is
    entirely below the floor — depletion is established, not merely suspected. `pivot ≠ guaranteed-escape`."""
    def __init__(self, floor: float = 1.0):
        self.floor = floor

    def decide(self, m_novel: float, ci: Tuple[float, float]) -> Decision:
        regime = classify_regime(ci[0], ci[1], self.floor)
        action = {SUPERCRITICAL: EXPLOIT, SUBCRITICAL: PIVOT, NEAR_CRITICAL: HOLD}[regime]
        return Decision(regime, action, m_novel, ci)

    def as_analysis(self, decision: Decision):
        from artifacts import AnalysisResult, Finding, Limitation
        findings = (
            Finding("FRONTIER_REGIME", "frontier-regime", f"{decision.regime} (m_novel={decision.m_novel:.2f}, CI={decision.ci})"),
            Finding("CONTROL", "frontier-regime", decision.action),
        )
        limitations = (
            Limitation("frontier-regime", "regime is read from the CI of an ESTIMATE vs 1; estimate ≠ property"),
            Limitation("model", "'orthogonal dimension' is a model construct; pivoting buys BOUNDED multi-basin "
                                 "exploration, not unbounded escape (PO-5 saturation). pivot ≠ guaranteed-escape"),
        )
        return AnalysisResult(source_trace=(), scope="frontier-regime", findings=findings, limitations=limitations)


# ---- a planted depletion model (declared, illustrative — NOT a finding) --------------------------
def _m_novel_at(k: int, f0: float, r: float) -> float:
    """A basin's marginal novelty geometrically depletes as it is consumed: m_novel(k) = f0 · r^k (r < 1)."""
    return f0 * (r ** k)


def _ci(m: float, w: float) -> Tuple[float, float]:
    return (m * (1 - w), m * (1 + w))


def run(gated: bool, dims: int = 3, f0: float = 2.0, r: float = 0.6, w: float = 0.15,
        floor: float = 1.0, max_steps: int = 100) -> dict:
    """Walk a trajectory through basins. EXPLOIT/HOLD consume the current basin (k+1); PIVOT (if gated and a
    fresh dimension remains) resets into a new orthogonal basin, else the trajectory is stuck and stops.
    Returns productive steps (frontier still expanding), basins used, the final regime, and the trace."""
    gate = FrontierGate(floor)
    basin, k, productive, steps = 0, 0, 0, 0
    trace: List = []
    while steps < max_steps:
        m = _m_novel_at(k, f0, r)
        d = gate.decide(m, _ci(m, w))
        trace.append((basin, k, round(m, 3), d.regime, d.action))
        if d.action in (EXPLOIT, HOLD):
            productive += 1 if d.action == EXPLOIT else 0
            k += 1
        else:  # PIVOT
            if gated and basin + 1 < dims:
                basin += 1
                k = 0
            else:
                break                      # ungated, or no orthogonal dimension left ⇒ stuck (bounded)
        steps += 1
    return {"gated": gated, "productive_steps": productive, "basins_used": basin + 1,
            "final_regime": trace[-1][3], "dims": dims, "trace": trace}


def main():
    print("frontier_gate.py — Leap 3: m_novel subcriticality sensor + pivot trigger (honest, bounded)\n")
    g = run(gated=True)
    u = run(gated=False)
    print(f"  GATED   : productive_steps={g['productive_steps']}  basins_used={g['basins_used']}/{g['dims']}  "
          f"final={g['final_regime']}")
    print(f"  UNGATED : productive_steps={u['productive_steps']}  basins_used={u['basins_used']}/{u['dims']}  "
          f"final={u['final_regime']}")
    print(f"\n  gated trace (basin, k, m_novel, regime, action):")
    for row in g["trace"]:
        print(f"    {row}")
    print(f"\n  the gate detects subcriticality (CI below 1) and pivots to a fresh basin, beating the ungated")
    print(f"  trajectory that chokes in one. BUT it saturates after {g['dims']} dimensions ({g['final_regime']}):")
    print(f"  bounded multi-basin exploration, not unbounded escape. estimate ≠ property; pivot ≠ guaranteed-escape.")


if __name__ == "__main__":
    main()
