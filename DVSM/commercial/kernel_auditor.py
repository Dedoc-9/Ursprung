# SPDX-License-Identifier: AGPL-3.0-only
# Commercial use beyond AGPL-3.0 requires a separate license — see LICENSE-COMMERCIAL.md.
"""
kernel_auditor.py — the commercialised product surface of the DVSM audit stack: the **DVSM Kernel Telemetry
Auditor**. A buyer points it at THEIR deterministic kernel's telemetry (a stream of dict rows) with a probe
schema, and gets a graded, reproducible air-gap report through the orchestrator's two chokepoints.

It is a thin, stable PRODUCT facade over the verified open core (`../coupling_audit.py`,
`../../weltwerk/verify/`). It generalises the DVSM-specific firewall to **customer-defined probes** over
arbitrary telemetry columns — that generalisation is the commercial value. It adds NO authority:
`router ≠ verifier`; `composition ≠ capability`; `integrity ≠ truth`.

What the product guarantees and — explicitly — does NOT, is enumerated and proof-gated in
`commercial_obligations.py`. No buyer-facing claim there may exceed a discharged technical obligation.

Open core: AGPL-3.0-only. Closed/SaaS use: a separate commercial license (LICENSE-COMMERCIAL.md).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))                                   # DVSM/ (open core)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "verify"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "stream_auditor"))
from coupling_audit import CouplingSpec, audit_coupling, CouplingResult         # noqa: E402
from stream_auditor import OrchestratedBackend                                  # noqa: E402  (reused unchanged)
from epistemic_types import NoHiddenChannel                                     # noqa: E402
from frontier_gate import FrontierGate                                          # noqa: E402
from claim_ledger import Claim, audit_ledger                                    # noqa: E402
from artifacts import AnalysisResult                                            # noqa: E402

WINDOW = 6000


@dataclass(frozen=True)
class CouplingProbe:
    """A customer-defined air-gap probe over their telemetry columns. `x` = the diagnostic channel (read-only
    by contract), `y` = the future dynamics channel it must not influence, `z` = the LEGITIMATE drivers of `y`
    (empty ⇒ condition on a constant), `w` = candidate confounders for the mis-specification stress. Set
    `identifiable=False` when `x` is a near-deterministic function of `z` (the audit will then decline to rule)."""
    name: str
    description: str
    x: str
    y: str
    z: Tuple[str, ...] = ()
    w: Tuple[str, ...] = ()
    identifiable: bool = True
    note: str = ""

    def to_spec(self) -> CouplingSpec:
        return CouplingSpec(
            self.name, self.description,
            x=lambda r, f=self.x: r[f],
            y=lambda r, f=self.y: r[f],
            z=lambda r, fs=self.z: (tuple(r[f] for f in fs) if fs else (0.0,)),
            w=lambda r, fs=self.w: (tuple(r[f] for f in fs) if fs else (0.0,)),
            identifiable=self.identifiable, note=self.note)


# Shipped reference probes (over the DVSM reference's StepRecord field names). Customers supply their own.
DVSM_DEFAULT_PROBES: Tuple[CouplingProbe, ...] = (
    CouplingProbe("omega_to_v", "NO Ω→V", "omega0", "v0_next", ("drive", "v0"), ("s0",), True),
    CouplingProbe("novelty_to_lambda", "NO ν→λ", "novelty", "lambda_eff", (), ("z_energy",), True),
    CouplingProbe("stiffness_to_z", "NO Stiffness→Dynamics", "stiffness", "z0_next", ("drive", "z0"), ("s0",),
                  False, "stiffness ≈ 2|z₀| ⊂ conditioning set ⇒ unidentifiable."),
)


@dataclass(frozen=True)
class WindowAudit:
    index: int
    results: Tuple[CouplingResult, ...]
    analyses: Tuple[AnalysisResult, ...]
    claims: Tuple[Claim, ...]
    frontier: Optional[str]

    def posture(self) -> Dict[str, List[str]]:
        """The report posture — explicit epistemic states, NO fused scalar / single 'health score'. The
        plurality (certifiable vs contaminated vs confounded vs blind) IS the finding. `salience ≠ importance`."""
        return {
            "certifiable": [r.name for r in self.results if r.verdict == "AIR_GAP_HELD"],
            "contaminated": [r.name for r in self.results
                             if r.identifiable and r.verdict == "OBSERVER_CONTAMINATION"],
            "confounded": [r.name for r in self.results if r.verdict == "CONFOUNDED_ARTIFACT"],
            "blind": [r.name for r in self.results if r.verdict == "UNIDENTIFIABLE"],
        }


class KernelAuditor(OrchestratedBackend):
    """The DVSM Kernel Telemetry Auditor (product surface). Window a telemetry stream of dict rows, audit each
    probe for a forbidden diagnostic→dynamics leak (answer chokepoint → AnalysisResult, side by side, no
    scalar), and gate any 'certify this telemetry as controller-safe' action behind the Grounded chokepoint.
    The kernel's state is never touched — replay/observe only (shadow evaluation)."""
    PRODUCT = "DVSM Kernel Telemetry Auditor"

    def __init__(self, probes: Tuple[CouplingProbe, ...] = DVSM_DEFAULT_PROBES, window: int = WINDOW,
                 delta: float = 0.02, orch=None):
        super().__init__(orch)
        self.probes = probes
        self.window = window
        self.delta = delta
        self.gate = FrontierGate()
        self._seen = set()
        self._prev = None
        self._claims: List[Claim] = []

    def audit_window(self, idx: int, rows: List[dict]) -> WindowAudit:
        results = tuple(audit_coupling(rows, p.to_spec(), seed=idx) for p in self.probes)
        analyses = tuple(r.as_analysis() for r in results)
        for a in analyses:
            assert isinstance(a, AnalysisResult) and a.scope and a.limitations, "honesty contract violated"
        claims = tuple(r.as_claim() for r in results)
        self._claims.extend(claims)
        # novelty-coverage attrition over the first probe's (x, y) plane (metric deflation, bounded pivot)
        p0 = self.probes[0]
        new = 0
        for r in rows:
            cell = (round(r[p0.x] / self.delta), round(r[p0.y] / self.delta))
            if cell not in self._seen:
                self._seen.add(cell); new += 1
        m = None if self._prev is None else new / max(1, self._prev)
        frontier = self.gate.decide(m, (m * 0.9, m * 1.1)).action if m is not None else None
        self._prev = new
        return WindowAudit(idx, results, analyses, claims, frontier)

    def audit(self, rows: List[dict]) -> List[WindowAudit]:
        """Window the telemetry; return one WindowAudit per window — side by side, NO fused scalar."""
        return [self.audit_window(i, rows[i * self.window:(i + 1) * self.window])
                for i in range(len(rows) // self.window)]

    def certify(self, wa: WindowAudit, probe_name: str, action: Callable[[Any], Any]) -> Any:
        """ACTION chokepoint: run `action` only if the named probe is AIR_GAP_HELD; else UngroundedError
        before any effect. Contaminated / confounded / blind telemetry cannot be certified controller-safe."""
        cr = next(c for c in wa.results if c.name == probe_name)
        return self.act(wa, NoHiddenChannel(cr.result), lambda w: action(w))

    def ledger(self) -> Tuple[Claim, ...]:
        return tuple(self._claims)


def rows_from_reference(trace) -> List[dict]:
    """Adapter: the bundled reference trace → dict rows the product consumes (for the self-test/demo)."""
    from dataclasses import asdict
    return [asdict(r) for r in trace]


def main():
    from dvsm_reference import gen_clean, gen_contaminated
    print("kernel_auditor.py — DVSM Kernel Telemetry Auditor (product surface)\n")
    aud = KernelAuditor(window=WINDOW)
    stream = rows_from_reference(gen_clean(WINDOW, 1) + gen_contaminated("omega_to_v", WINDOW, 2))
    windows = aud.audit(stream)
    for wa in windows:
        print(f"  window {wa.index}: posture={wa.posture()}  frontier={wa.frontier}")
    log: List = []
    for wa in windows:
        try:
            aud.certify(wa, "omega_to_v", lambda w: log.append(w.index)); v = "CERTIFIED"
        except Exception as e:
            v = f"REFUSED ({type(e).__name__})"
        print(f"  certify omega_to_v window {wa.index} → {v}")
    print(f"  certified: {log}; ledger honest: {audit_ledger(aud.ledger())['honest']}")
    print("  observation ≠ authority; undetected ≠ absent; integrity ≠ truth.")


if __name__ == "__main__":
    main()
