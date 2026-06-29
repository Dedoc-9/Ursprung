# SPDX-License-Identifier: AGPL-3.0-only
"""
dvsm_backend.py — the DVSM backend CLIENT of weltwerk/verify/orchestrator.py (routing profile **D**): it
treats a DVSM telemetry trace as a READ-ONLY research object and makes the orchestrator's two chokepoints an
inescapable reality over it. It reuses `OrchestratedBackend` (the stream_auditor base) UNCHANGED and adds no
authority. `router ≠ verifier`; `composition ≠ capability`; `integrity ≠ truth`.

  • ANSWER chokepoint — each window is run through the forbidden-coupling firewall (`coupling_audit`); each
    coupling's verdict is an `AnalysisResult`, reported **side by side — never fused into one scalar**. The
    plurality across couplings and windows IS the finding.
  • ACTION chokepoint — the only side-effect offered is "certify this window's telemetry as air-gap-clean so
    a downstream control loop may trust it". It runs ONLY through `orchestrator.enact`, grounded by
    `NoHiddenChannel` (verdict == AIR_GAP_HELD). A window with OBSERVER_CONTAMINATION (or a CONFOUNDED /
    UNSTRESSED / UNIDENTIFIABLE verdict) raises `UngroundedError` **before** the action body — atomic refusal.
    You may not feed contaminated telemetry to a controller. `observation ≠ authority`.
  • METRIC DEFLATION — `frontier_gate` reads window-over-window novelty-cell coverage; when it goes
    subcritical the backend emits a **bounded** PIVOT (re-window / re-baseline / widen the modeled drivers),
    never "the trace looks healthy now".

`borrow-checker-clean ≠ air-gap-sound`; `residual-CMI ≠ channel`; `undetected ≠ absent`. Profiles A (SMT
trapping for the discrete-kernel boundedness certificate, OPEN) and B inherit the same base elsewhere.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, fields
from typing import Any, Callable, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "weltwerk", "verify"))
sys.path.insert(0, os.path.join(_HERE, "..", "weltwerk", "stream_auditor"))
from stream_auditor import OrchestratedBackend                       # noqa: E402  (reused base, unchanged)
from epistemic_types import NoHiddenChannel                          # noqa: E402
from frontier_gate import FrontierGate                               # noqa: E402
from claim_ledger import Claim, audit_ledger                         # noqa: E402
from artifacts import AnalysisResult                                 # noqa: E402

from coupling_audit import audit_all, COUPLINGS, CouplingResult
from dvsm_reference import StepRecord, gen_clean, gen_contaminated

WINDOW = 6000


@dataclass(frozen=True)
class WindowResult:
    index: int
    couplings: Tuple[CouplingResult, ...]      # one per manifest coupling — side by side, NO scalar
    analyses: Tuple[AnalysisResult, ...]
    claims: Tuple[Claim, ...]
    coverage_new: int
    m_novel: Optional[float]
    frontier: Optional[str]                    # EXPLOIT / PIVOT / HOLD once a previous window exists

    def air_gap_held(self) -> bool:
        """True iff every IDENTIFIABLE coupling read AIR_GAP_HELD (the certifiable condition)."""
        return all(c.verdict == "AIR_GAP_HELD" for c in self.couplings if c.identifiable)

    def contamination(self) -> Tuple[str, ...]:
        """Confirmed contamination = IDENTIFIABLE couplings reading OBSERVER_CONTAMINATION. An unidentifiable
        coupling's positive CMI is NOT reported as contamination (it cannot be told from confounding)."""
        return tuple(c.name for c in self.couplings
                     if c.identifiable and c.verdict == "OBSERVER_CONTAMINATION")

    def unidentifiable(self) -> Tuple[str, ...]:
        return tuple(c.name for c in self.couplings if c.verdict == "UNIDENTIFIABLE")


class DvsmTraceAuditor(OrchestratedBackend):
    """Profile D: window a DVSM telemetry trace, audit each window for forbidden diagnostic→dynamics
    couplings, grade them, track novelty attrition, and gate any 'trust this telemetry' action behind the
    Grounded chokepoint. The kernel's state is never touched — replay/observe only (shadow evaluation)."""
    PROFILE = "D"

    def __init__(self, window: int = WINDOW, delta: float = 0.02, orch=None):
        super().__init__(orch)
        self.window = window
        self.delta = delta
        self.gate = FrontierGate()
        self._seen_cells = set()
        self._prev_new = None
        self._claims: List[Claim] = []

    def _audit_window(self, idx: int, rows: List[StepRecord]) -> WindowResult:
        results = audit_all(rows, seed=idx)                     # answer chokepoint, one AnalysisResult each
        analyses = tuple(r.as_analysis() for r in results)
        for a in analyses:
            assert isinstance(a, AnalysisResult) and a.scope and a.limitations, \
                "window answer violated the honesty contract"
        claims = tuple(r.as_claim() for r in results)
        self._claims.extend(claims)

        # novelty-cell coverage attrition (metric deflation) over the (z0, omega0) telemetry plane
        new = 0
        for r in rows:
            cell = (round(r.z0 / self.delta), round(r.omega0 / self.delta))
            if cell not in self._seen_cells:
                self._seen_cells.add(cell); new += 1
        m_novel = None if self._prev_new is None else new / max(1, self._prev_new)
        frontier = None
        if m_novel is not None:
            frontier = self.gate.decide(m_novel, (m_novel * 0.9, m_novel * 1.1)).action
        self._prev_new = new
        return WindowResult(idx, tuple(results), analyses, claims, new, m_novel, frontier)

    def audit_stream(self, stream: List[StepRecord]) -> List[WindowResult]:
        """Window the trace; return one WindowResult per window — side by side, NO fused scalar."""
        return [self._audit_window(i, stream[i * self.window:(i + 1) * self.window])
                for i in range(len(stream) // self.window)]

    def certify_clean(self, wr: WindowResult, coupling_name: str, action: Callable[[Any], Any]) -> Any:
        """ACTION chokepoint: run `action` ONLY if the named coupling is AIR_GAP_HELD in this window; else
        UngroundedError before any effect. You cannot certify contaminated telemetry as controller-safe."""
        cr = next(c for c in wr.couplings if c.name == coupling_name)
        return self.act(wr, NoHiddenChannel(cr.result), lambda w: action(w))

    def ledger(self) -> Tuple[Claim, ...]:
        return tuple(self._claims)


# ---- synthetic telemetry stream (clean windows then a contaminated window) ------------------------
def demo_stream() -> List[StepRecord]:
    return (gen_clean(WINDOW, seed=1)
            + gen_clean(WINDOW, seed=9)
            + gen_contaminated("omega_to_v", WINDOW, seed=2))


def main():
    print("dvsm_backend.py — DVSM Trace Auditor (profile D): orchestrator chokepoints on telemetry\n")
    aud = DvsmTraceAuditor()
    results = aud.audit_stream(demo_stream())
    print("  per-window witnesses (side by side, no fused scalar):")
    for wr in results:
        print(f"    window {wr.index}: air_gap_held={wr.air_gap_held()}  contamination={wr.contamination()}  "
              f"unidentifiable={wr.unidentifiable()}  frontier={wr.frontier}")
        for c in wr.couplings:
            print(f"        {c.name:20s} {c.verdict}")
    log: List = []
    print("\n  certify telemetry as controller-safe (only AIR_GAP_HELD windows may be certified):")
    for wr in results:
        try:
            aud.certify_clean(wr, "omega_to_v", lambda w: log.append(w.index))
            verdict = "CERTIFIED"
        except Exception as e:
            verdict = f"REFUSED ({type(e).__name__})"
        print(f"    window {wr.index} → {verdict}")
    print(f"\n  certified windows: {log}  (a contaminated window is refused atomically)")
    print(f"  ledger honest: {audit_ledger(aud.ledger())['honest']}")
    print("  router ≠ verifier; observation ≠ authority; the panel stays plural; integrity ≠ truth.")


if __name__ == "__main__":
    main()
