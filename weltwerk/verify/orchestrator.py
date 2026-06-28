# SPDX-License-Identifier: AGPL-3.0-only
"""
orchestrator.py — a thin Epistemic Runtime Orchestrator: make the verified tools interchangeable behind two
chokepoints, adding NO new authority.

The tools (`residual_channel`, `claim_ledger`, `certificate_compiler`, `frontier_gate`, the engines) already
exist and are tested. This layer does one narrow thing: it standardizes how they are *called* and *composed*,
through exactly two type gates that the rest of the repo already enforces piecewise —

  • ANSWERS go through `AnalysisResult` — every registered tool's `analyze()` returns the honesty contract
    (scope + ≥1 limitation), checked again at the orchestration boundary. A tool that emits a bare verdict is
    rejected here.
  • ACTIONS go through `Grounded[T]` — `enact()` runs a side effect only if the value is `Grounded` by a
    verifier-issued proof; an ungrounded action raises `UngroundedError` before any effect.

What it deliberately is NOT: it is not a "platform" that makes the tools more capable, and it does not produce a
single confidence scalar. `panel()` returns *many witnesses on one request, side by side* — it never averages or
ranks them into one number (the project's standing refusal). The orchestrator is a *router + two chokepoints*; it
grants no truth the underlying tool did not. `orchestration ≠ authority`; `router ≠ verifier`;
`composition ≠ capability`; `integrity ≠ truth`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Protocol, Tuple, runtime_checkable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artifacts import AnalysisResult, Finding, Limitation                      # noqa: E402
from epistemic_types import Grounded, Grounding, UngroundedError               # noqa: E402


class UnknownToolError(KeyError):
    """Requested a tool that is not registered — a typed error, never a silent default."""


@runtime_checkable
class EpistemicTool(Protocol):
    name: str
    def analyze(self, request: dict) -> AnalysisResult: ...


# ---- adapters: wrap each existing tool to the uniform (request → AnalysisResult) interface --------
@dataclass(frozen=True)
class ResidualTool:
    """request: {'samples': [(x,y,z), …], optional 'misspec_fns'}. Wraps residual_channel.audit."""
    name: str = "residual_channel"
    def analyze(self, request: dict) -> AnalysisResult:
        from residual_channel import audit
        r = audit(request["samples"], misspec_fns=request.get("misspec_fns"))
        return r.as_analysis()


@dataclass(frozen=True)
class FrontierTool:
    """request: {'m_novel': float, 'ci': (lo,hi)}. Wraps frontier_gate.FrontierGate."""
    name: str = "frontier_gate"
    def analyze(self, request: dict) -> AnalysisResult:
        from frontier_gate import FrontierGate
        g = FrontierGate()
        return g.as_analysis(g.decide(request["m_novel"], request["ci"]))


@dataclass(frozen=True)
class LedgerTool:
    """request: {'ledger': (Claim, …)}. Wraps claim_ledger.audit_ledger into the honesty contract."""
    name: str = "claim_ledger"
    def analyze(self, request: dict) -> AnalysisResult:
        from claim_ledger import audit_ledger
        a = audit_ledger(request["ledger"])
        findings = (
            Finding("LEDGER_HONEST", "claim-ledger", f"honest={a['honest']} counts={a['counts']}"),
            Finding("VIOLATIONS", "claim-ledger",
                    f"off_ladder={a['off_ladder']} missing={a['missing_falsifier_or_boundary']}"),
        )
        limitations = (
            Limitation("claim-ledger", "the audit checks FORM (graded + falsifiable + bounded), not the truth "
                                       "of the claims; integrity ≠ truth"),
        )
        return AnalysisResult(source_trace=(), scope="claim-ledger", findings=findings, limitations=limitations)


@dataclass(frozen=True)
class CertificateTool:
    """request: {'init','successors','universe','cert'}. Wraps certificate_compiler.check_certificate."""
    name: str = "certificate_compiler"
    def analyze(self, request: dict) -> AnalysisResult:
        from certificate_compiler import check_certificate, minimal_reason
        r = check_certificate(request["init"], request["successors"], request["universe"], request["cert"])
        findings = (
            Finding("INDUCTIVE", "inductive-certificate", f"valid={r.valid} ({minimal_reason(r)})"),
            Finding("WITNESS", "inductive-certificate", f"{r.witness!r}" if not r.valid else "none"),
        )
        limitations = (
            Limitation("inductive-certificate", "checked over a supplied finite universe (pure-stdlib); the "
                                                "size-independent symbolic check is the z3 path. checking ≠ finding"),
            Limitation("inductive-certificate", "the checker verifies a GIVEN invariant; it does not derive one"),
        )
        return AnalysisResult(source_trace=(), scope="inductive-certificate", findings=findings, limitations=limitations)


# ---- the orchestrator: registry + the two chokepoints --------------------------------------------
@dataclass
class EpistemicRuntimeOrchestrator:
    tools: Dict[str, EpistemicTool] = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = {}

    def register(self, tool: EpistemicTool) -> "EpistemicRuntimeOrchestrator":
        if not isinstance(tool, EpistemicTool):
            raise TypeError(f"{tool!r} does not satisfy the EpistemicTool protocol (name + analyze)")
        self.tools[tool.name] = tool
        return self

    def analyze(self, tool_name: str, request: dict) -> AnalysisResult:
        """ANSWER chokepoint: dispatch, and enforce the honesty contract at the boundary."""
        if tool_name not in self.tools:
            raise UnknownToolError(f"no tool '{tool_name}' registered ({sorted(self.tools)})")
        r = self.tools[tool_name].analyze(request)
        if not isinstance(r, AnalysisResult):
            raise TypeError(f"tool '{tool_name}' did not return an AnalysisResult")
        if not r.scope or len(r.limitations) < 1:
            raise ValueError(f"tool '{tool_name}' emitted a result without the honesty contract")
        return r

    def panel(self, calls: List[Tuple[str, dict]]) -> Dict[str, AnalysisResult]:
        """Many witnesses on one question, side by side — NO aggregation, NO scalar, no global winner."""
        return {name: self.analyze(name, req) for name, req in calls}

    def enact(self, value: Any, proof: Grounding, action: Callable[[Any], Any]) -> Any:
        """ACTION chokepoint: run `action` only on a value GROUNDED by a verifier-issued proof; an ungrounded
        value raises UngroundedError before any effect. The orchestrator grants no authority — the proof does."""
        g = Grounded.ground(value, proof)        # raises UngroundedError if not grounded
        return action(g.value)


def default_orchestrator() -> EpistemicRuntimeOrchestrator:
    o = EpistemicRuntimeOrchestrator()
    for t in (ResidualTool(), FrontierTool(), LedgerTool(), CertificateTool()):
        o.register(t)
    return o


def main():
    print("orchestrator.py — Epistemic Runtime Orchestrator (router + two chokepoints, no new authority)\n")
    from residual_channel import demo_gen_channel
    from claim_ledger import Claim
    from certificate_compiler import ConstraintCertificate, chain
    from epistemic_types import Attested

    o = default_orchestrator()
    init, succ, uni = chain(6)
    calls = [
        ("residual_channel", {"samples": demo_gen_channel()}),
        ("frontier_gate", {"m_novel": 0.5, "ci": (0.42, 0.58)}),
        ("claim_ledger", {"ledger": (Claim("D1", "E reproduces", "ESTABLISHED", "M", "the magnitude", "a failed rep"),)}),
        ("certificate_compiler", {"init": init, "successors": succ, "universe": uni,
                                  "cert": ConstraintCertificate("ok", lambda i: 0 <= i <= 6, lambda i: True)}),
    ]
    for name, res in o.panel(calls).items():
        print(f"  [{name}] scope={res.scope!r}  findings={len(res.findings)}  limitations={len(res.limitations)}")
        print(f"       → {res.findings[0].detail if res.findings else '(none)'}")

    log: List = []
    o.enact("apply", Attested(True, "verifier-grounded"), lambda v: log.append(v))
    try:
        o.enact("apply", Attested(False, "ungrounded"), lambda v: log.append(v))
    except UngroundedError:
        pass
    print(f"\n  enact: committed {log} (ungrounded action refused before effect)")
    print("  every answer is an AnalysisResult; every action passes the Grounded gate; the panel stays plural.")
    print("  orchestration ≠ authority; router ≠ verifier; composition ≠ capability; integrity ≠ truth.")


if __name__ == "__main__":
    main()
