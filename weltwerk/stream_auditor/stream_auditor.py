# SPDX-License-Identifier: AGPL-3.0-only
"""
stream_auditor.py — the first true backend CLIENT of weltwerk/verify/orchestrator.py: a domain-agnostic
Causal Stream Auditor (routing profile **C**).

It consumes a multi-dimensional stream (rows = `(…columns…)` — simulated physics, telemetry, or financial /
ad-attribution time-series), windows it, and makes the orchestrator's two chokepoints an inescapable runtime
reality:

  • ANSWER chokepoint — each window is conditioned by `residual_channel` (confounder-conditioned CMI + shuffle
    null + a refine-with-W mis-specification stress) and emitted as an `AnalysisResult`. Windows are reported
    **side by side — never fused into one confidence scalar** (the disagreement across windows IS the finding).
    Each window's structural finding is also registered as a graded `claim_ledger.Claim`.
  • ACTION chokepoint — a downstream act ("promote this window's signal to a live decision") runs ONLY through
    `orchestrator.enact`, grounded by `ChannelEstablished` (decision == `RESIDUAL_MISSPEC_STABLE`). A `HEALTHY`
    or `FRAGILE` window raises `UngroundedError` **before** the action body — atomic refusal, state pristine.

  • METRIC DEFLATION — `frontier_gate` reads the window-over-window coverage multiplier; when it goes
    subcritical the auditor emits a **bounded** PIVOT (re-window / re-baseline / widen the confounder set),
    never "the stream keeps improving". Type-B frontier exhaustion is tracked, not denied.

Decision → meaning: `CONSISTENT_WITH_NULL` = **HEALTHY** (all X–Y coupling explained by the modeled Z);
`RESIDUAL_MISSPEC_STABLE` = **CHANNEL** (a real inter-channel dependence that survives conditioning on (Z,W));
`RESIDUAL_MISSPEC_FRAGILE` = **MISSPEC** (a missing-confounder artifact that dissolves under (Z,W)).

`router ≠ verifier`; `composition ≠ capability`; `residual-CMI ≠ channel`; `proves-the-procedure ≠
proves-the-phenomenon`; `integrity ≠ truth`. The auditor grants no truth; it routes, grades, and gates.
Profiles **A** (SMT trapping) and **B** (code-synthesis linter) inherit `OrchestratedBackend` as alternative
routing profiles — not built here.
"""
from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
from orchestrator import default_orchestrator, EpistemicRuntimeOrchestrator    # noqa: E402
from residual_channel import audit                                             # noqa: E402
from epistemic_types import ChannelEstablished, NoHiddenChannel                # noqa: E402
from claim_ledger import Claim                                                 # noqa: E402
from frontier_gate import FrontierGate, EXPLOIT                                # noqa: E402
from artifacts import AnalysisResult                                           # noqa: E402

K = 3                  # discretization levels (continuous streams must be binned by the caller)
REPS = 60              # shuffle-null reps per window (tight enough at window>=2000)
MARGIN = 0.03


# ---- the base backend: two chokepoints via the orchestrator (A and B inherit this) ---------------
class OrchestratedBackend:
    """A backend whose every answer passes the AnalysisResult chokepoint and every action passes the
    Grounded[T] chokepoint, both via the orchestrator. It adds no authority. `router ≠ verifier`."""
    PROFILE = "base"

    def __init__(self, orch: Optional[EpistemicRuntimeOrchestrator] = None):
        self.orch = orch or default_orchestrator()

    def answer(self, tool: str, request: dict) -> AnalysisResult:
        return self.orch.analyze(tool, request)      # honesty contract enforced at the boundary

    def act(self, value: Any, proof, action: Callable[[Any], Any]) -> Any:
        return self.orch.enact(value, proof, action)  # runs only if Grounded; else UngroundedError


@dataclass(frozen=True)
class ChannelSpec:
    """Which stream columns are X, Y, the modeled confounder Z, and the candidate confounder W."""
    x: int
    y: int
    z: int
    w: int


@dataclass(frozen=True)
class WindowResult:
    index: int
    decision: str                 # HEALTHY | CHANNEL | MISSPEC
    raw_decision: str             # residual_channel's enum
    analysis: AnalysisResult
    claim: Claim
    proof: Any                    # a ChannelEstablished Grounding (grounded iff CHANNEL)
    coverage_new: int
    m_novel: Optional[float]
    frontier: Optional[str]       # frontier_gate action (EXPLOIT/PIVOT/HOLD) once a previous window exists


_LABEL = {"CONSISTENT_WITH_NULL": "HEALTHY",
          "RESIDUAL_MISSPEC_STABLE": "CHANNEL",
          "RESIDUAL_MISSPEC_FRAGILE": "MISSPEC",
          "RESIDUAL_DEPENDENCE": "MISSPEC"}     # no misspec test ran ⇒ treat as not-yet-confirmed


def _claim_for(idx: int, decision: str, r) -> Claim:
    if decision == "CHANNEL":
        return Claim(f"W{idx}", "a residual inter-channel dependence survives conditioning on (Z,W).",
                     "MEASURED",
                     f"I(X;Y|Z)={r.cmi:.3f} > null and stable under the W mis-spec stress.",
                     "causality beyond the MODELED state; the complete confounder set is unattainable.",
                     "the residual vanishes under a further candidate confounder, or under finer windowing.")
    if decision == "MISSPEC":
        return Claim(f"W{idx}", "an apparent residual dissolves under (Z,W): a modeled-confounder artifact, "
                                "not an inter-channel channel.", "MEASURED",
                     "I(X;Y|Z) elevated but I(X;Y|Z,W) ≈ null.",
                     "that the streams are independent — only that this residual is confounder-explained.",
                     "the residual survives every candidate confounder (⇒ promote to CHANNEL).")
    return Claim(f"W{idx}", "no residual dependence beyond the modeled confounder Z.", "MEASURED",
                 f"I(X;Y|Z)={r.cmi:.3f} ≈ shuffle null.",
                 "absence of any channel — only that none is visible at this window/conditioning.",
                 "a residual appears under finer windowing or a richer Z.")


class CausalStreamAuditor(OrchestratedBackend):
    """Profile C: window a stream, audit each window for an unobserved-confounder channel, grade it, track
    coverage attrition, and gate any downstream promotion behind the Grounded chokepoint."""
    PROFILE = "C"

    def __init__(self, spec: ChannelSpec, window: int = 4000, delta: float = 1.0,
                 orch: Optional[EpistemicRuntimeOrchestrator] = None):
        super().__init__(orch)
        self.spec = spec
        self.window = window
        self.delta = delta
        self.gate = FrontierGate()
        self._seen_cells = set()
        self._prev_new = None
        self._claims: List[Claim] = []

    def _audit_window(self, idx: int, rows: List[tuple]) -> WindowResult:
        s = self.spec
        samples_xyz = [(row[s.x], row[s.y], row[s.z]) for row in rows]

        def refine_w(_samples):                       # re-condition on (Z, W): the decisive mis-spec stress
            return [(row[s.x], row[s.y], (row[s.z], row[s.w])) for row in rows]

        r = audit(samples_xyz, reps=REPS, seed=idx, misspec_fns=(refine_w,))
        decision = _LABEL.get(r.decision, "MISSPEC")
        analysis = r.as_analysis()                    # native AnalysisResult (answer chokepoint contract)
        assert isinstance(analysis, AnalysisResult) and analysis.scope and analysis.limitations, \
            "window answer violated the honesty contract"
        claim = _claim_for(idx, decision, r)
        self._claims.append(claim)
        proof = ChannelEstablished(r)                 # grounded iff decision == CHANNEL

        # coverage attrition (metric deflation)
        new = 0
        for row in rows:
            cell = (round(row[s.x] / self.delta), round(row[s.y] / self.delta))
            if cell not in self._seen_cells:
                self._seen_cells.add(cell); new += 1
        m_novel = None if self._prev_new is None else new / max(1, self._prev_new)
        frontier = None
        if m_novel is not None:
            frontier = self.gate.decide(m_novel, (m_novel * 0.9, m_novel * 1.1)).action
        self._prev_new = new
        return WindowResult(idx, decision, r.decision, analysis, claim, proof, new, m_novel, frontier)

    def audit_stream(self, stream: List[tuple]) -> List[WindowResult]:
        """Window the stream and return one WindowResult per window — side by side, NO fused scalar."""
        out = []
        for i in range(len(stream) // self.window):
            out.append(self._audit_window(i, stream[i * self.window:(i + 1) * self.window]))
        return out

    def promote(self, wr: WindowResult, action: Callable[[Any], Any]) -> Any:
        """ACTION chokepoint: run `action` only if the window is a grounded CHANNEL; else UngroundedError
        before any effect. Promotion of a HEALTHY or MISSPEC window is refused atomically."""
        return self.act(wr, wr.proof, lambda w: action(w))

    def ledger(self) -> Tuple[Claim, ...]:
        return tuple(self._claims)


# ---- synthetic streams (each row = (x, y, z, w)) -------------------------------------------------
def _noisy(v, rng, p=0.3):
    return v if rng.random() >= p else rng.randrange(K)


def gen_healthy(n: int, seed: int = 1):
    rng = random.Random(seed)
    return [(_noisy(z, rng), _noisy(z, rng), z, rng.randrange(K)) for z in (rng.randrange(K) for _ in range(n))]


def gen_channel(n: int, seed: int = 2):
    rng = random.Random(seed); out = []
    for _ in range(n):
        z, w = rng.randrange(K), rng.randrange(K)
        x = _noisy(z, rng)
        out.append((x, _noisy((z + x) % K, rng), z, w))      # Y depends on X ⇒ survives (Z,W) ⇒ CHANNEL
    return out


def gen_fragile(n: int, seed: int = 3):
    rng = random.Random(seed); out = []
    for _ in range(n):
        z, w = rng.randrange(K), rng.randrange(K)
        m = (z + w) % K
        out.append((_noisy(m, rng), _noisy(m, rng), z, w))   # X,Y share hidden W ⇒ dissolves under (Z,W)
    return out


SPEC = ChannelSpec(x=0, y=1, z=2, w=3)


def main():
    print("stream_auditor.py — Causal Stream Auditor (profile C): orchestrator chokepoints on a live stream\n")
    aud = CausalStreamAuditor(SPEC, window=4000)
    stream = gen_healthy(4000) + gen_channel(4000) + gen_fragile(4000)
    results = aud.audit_stream(stream)
    print("  per-window witnesses (side by side, no fused scalar):")
    for wr in results:
        print(f"    window {wr.index}: {wr.decision:8s} (raw={wr.raw_decision})  "
              f"m_novel={wr.m_novel}  frontier={wr.frontier}")
    log: List = []
    for wr in results:
        try:
            aud.promote(wr, lambda w: log.append(w.index))
            verdict = "PROMOTED"
        except Exception as e:
            verdict = f"REFUSED ({type(e).__name__})"
        print(f"    promote window {wr.index} → {verdict}")
    from claim_ledger import audit_ledger
    print(f"\n  ledger audit: {audit_ledger(aud.ledger())['honest']}  (every window finding graded + falsifiable)")
    print(f"  promoted windows: {log}  (only grounded CHANNELs reach the action; HEALTHY/MISSPEC refused atomically)")
    print("  router ≠ verifier; residual-CMI ≠ channel; the panel stays plural; integrity ≠ truth.")


if __name__ == "__main__":
    main()
