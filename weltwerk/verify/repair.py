# SPDX-License-Identifier: AGPL-3.0-only
"""
repair.py — Phase C.2: repair *candidates* (bounded intervention), not repairs.

A RepairCandidate represents: "this edit was OBSERVED to remove this failure mode under these conditions" —
NOT "this fixes the model". So there is deliberately no `fixed` / `safe` / `correct` field. Two separated
pieces of evidence instead:

  • restores_trace — removing the event clears THIS ghost (cheap replay; counterfactual-level).
  • restores_world — forbid that action from the alphabet and RE-VERIFY; the result carries the exact
    experiment `(engine, bound, status)`. It is an enum, never a bare bool:
        RESTORED_PROVEN        — CLOSED with the action forbidden (exhaustive over the restricted alphabet)
        RESTORED_WITHIN_BOUND  — BOUNDED, no ghost up to the bound (beyond is UNDERDETERMINED)
        STILL_VIOLATED         — a different ghost remains
        NOT_CHECKED            — restores_world was not computed
    `restores-under-(M,E,K) ≠ world-safe`; `candidate ≠ repair`.

DISCIPLINE: the system stays an explanation/proposal engine, not an autonomous modifier. Candidates are
SEEDED ONLY from existing evidence (the counterfactual critical set) — repair does not invent edits. The
flow is auditable: VerificationResult → ghost trace → counterfactual critical events → RemoveEvent candidate.

This module edits no core file: it forbids an action by SUBCLASSING `TransitionRelation` and filtering its
alphabet, then re-verifies through the ordinary engine + contract. (Differential check across engines is
available in `main()` when z3 is present — a repair that only works in one engine is likely an encoding bug.)
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from transition import TransitionRelation                    # noqa: E402
from engine import WorldModel, VerificationOptions, ExplicitStateBFSEngine   # noqa: E402
from artifacts import normalize_invariants, AnalysisResult, Finding, Limitation  # noqa: E402
from kernel_check import DEFAULT_INVARIANTS                   # noqa: E402
import counterfactual                                         # noqa: E402


# ---- types --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class RepairChange:
    kind: str                        # "REMOVE_EVENT" (v1); "MODIFY_ACTION" / "ADD_CONSTRAINT" reserved
    target: tuple                    # the event/action, e.g. ("destroy", "reactor")


@dataclass(frozen=True)
class WorldRepairEvidence:
    """The exact experiment behind a restores_world claim. Carrying (engine, bound, status) is the point —
    a bare 'restores_world=True' is the false confidence the honesty layer exists to prevent."""
    engine: str
    bound: int
    status: str                      # CLOSED | BOUNDED | VIOLATED, with the action forbidden
    violation_count: int

    @property
    def restores_world(self) -> str:
        if self.status == "CLOSED":
            return "RESTORED_PROVEN"
        if self.status == "BOUNDED":
            return "RESTORED_WITHIN_BOUND"
        return "STILL_VIOLATED"


@dataclass(frozen=True)
class RepairCandidate:
    change: RepairChange
    restores_trace: bool             # removing the event clears THIS ghost
    world_evidence: Optional[WorldRepairEvidence] = None    # None ⇒ NOT_CHECKED

    @property
    def restores_world(self) -> str:
        return self.world_evidence.restores_world if self.world_evidence is not None else "NOT_CHECKED"

    def as_analysis(self) -> AnalysisResult:
        scope = "bounded-world" if self.world_evidence is not None else "trace"
        findings = (Finding("REPAIR_CANDIDATE", scope,
                            f"{self.change.kind} {self.change.target} → "
                            f"restores_trace={self.restores_trace}, restores_world={self.restores_world}"),)
        lims = [Limitation("trace", "a candidate, not a fix: removing the event prevents THIS ghost only")]
        if self.world_evidence is not None:
            e = self.world_evidence
            lims.append(Limitation("bounded-world",
                                   f"restores_world={self.restores_world} under engine={e.engine}, "
                                   f"bound={e.bound}; NOT a global-safety claim"))
        else:
            lims.append(Limitation("world", "restores_world NOT_CHECKED"))
        return AnalysisResult(source_trace=(self.change.target,), scope=scope,
                              findings=findings, limitations=tuple(lims))


# ---- forbid-an-action relation (no core edit; just a filtered alphabet) --------------------------
class _ForbidRelation(TransitionRelation):
    """A TransitionRelation with specific actions removed from its alphabet — i.e. those edits can never
    happen. Used to ask: 'if this action were forbidden, is the world still reachable-to-a-ghost?'"""
    def __init__(self, world_text: str, forbid_args, include_capture: bool = False):
        super().__init__(world_text, include_capture)
        forb = {tuple(a) for a in forbid_args}
        self._alphabet = tuple(a for a in self._alphabet if a.as_args() not in forb)


def _forbid_and_verify(world_text, event, invariants, engine, bound) -> WorldRepairEvidence:
    engine = engine or ExplicitStateBFSEngine()
    bound = 8 if bound is None else bound
    rel = _ForbidRelation(world_text, {tuple(event)})
    model = WorldModel(initial_state=rel.initial(), transition_relation=rel,
                       invariants=invariants, action_alphabet=rel.actions())
    vr = engine.verify(model, VerificationOptions(depth_bound=bound))
    return WorldRepairEvidence(engine=vr.engine, bound=bound, status=vr.status,
                               violation_count=len(vr.violations))


# ---- the API ------------------------------------------------------------------------------------
def evaluate_removal(world_text, trace, event, invariants=None, *,
                     check_world=False, engine=None, bound=8) -> RepairCandidate:
    """Evaluate removing one (arbitrary) event from a trace. `restores_trace` is computed honestly by
    replay — so a NON-critical event yields `restores_trace=False`, not a fabricated candidate."""
    invs = invariants or DEFAULT_INVARIANTS
    nz = normalize_invariants(invs)
    events = tuple(tuple(e) for e in trace)
    ev = tuple(event)
    reduced = tuple(e for e in events if e != ev)
    restores_trace = not counterfactual._trajectory_violates(world_text, reduced, nz)
    evidence = _forbid_and_verify(world_text, ev, invs, engine, bound) if check_world else None
    return RepairCandidate(RepairChange("REMOVE_EVENT", ev), restores_trace, evidence)


def propose(world_text, source, invariants=None, *, check_world=True, engine=None, bound=8) -> list:
    """Propose repair candidates for a VIOLATED result (or a raw ghost trace). Candidates are seeded ONLY
    from the counterfactual CRITICAL set — repair does not invent edits. Each is a REMOVE_EVENT candidate
    with restores_trace and (optionally) restores_world evidence."""
    invs = invariants or DEFAULT_INVARIANTS
    trace = source.witness if hasattr(source, "witness") else tuple(tuple(e) for e in source)
    if not trace:
        return []
    cf = counterfactual.analyze(world_text, trace, invs)
    return [evaluate_removal(world_text, trace, ev, invs, check_world=check_world, engine=engine, bound=bound)
            for ev in cf.critical]


def main():
    from kernel_check import check, DEMO_WORLD
    print("repair.py — Phase C.2: repair CANDIDATES (bounded intervention, not fixes)\n")
    nt = {"north_ok": (lambda s: s.runtime["north_territory"]["status"] != "disabled")}
    g = check(DEMO_WORLD, max_depth=3, invariants=nt).ghost
    for cand in propose(DEMO_WORLD, g.path, nt, bound=8):
        print(f"  {cand.change.kind} {cand.change.target}: restores_trace={cand.restores_trace}, "
              f"restores_world={cand.restores_world} "
              f"(engine={cand.world_evidence.engine}, bound={cand.world_evidence.bound})")
    print("\n  a candidate is observed-to-help under (engine, bound), not a proven fix. candidate ≠ repair.")


if __name__ == "__main__":
    main()
