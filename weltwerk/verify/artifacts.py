# SPDX-License-Identifier: AGPL-3.0-only
"""
artifacts.py — Phase A.2, Step 4: the durable, reusable verification artifacts.

This is the base of the verify/ dependency graph: it imports none of the other verify modules at load
time (only deferred imports inside factories/verifiers), so `transition.py`, `engine.py`, and the
consumers (`diagnose.py`, future phases) can all depend on *artifacts* as the common language.

Step 4 enriches OUTPUTS, not engines. Everything here is ADDITIVE — existing fields/views (`witness`,
`CheckResult.ghost.path`, `Violation.invariant`) remain valid; these are richer views alongside them.

  • Trace        — a first-class, immutable execution path (events + states + terminal_state).
  • Invariant    — a named predicate plus DESCRIPTIVE metadata (explanation, severity). `label ≠ control`:
                   the engine evaluates `.predicate` only; it never branches on `severity`.
  • Violation    — moved here; gains optional `explanation`/`severity` (defaults preserve old call sites).
  • ReachabilityCertificate — an independently-checkable RECORD of a verification run. For the explicit
                   engine it is NOT a cheaper proof object: producing and verifying both explore the graph.
                   Its value is reproducibility / auditability / portability. A verify-cheaper-than-prove
                   asymmetry may emerge in a future *symbolic* certificate but is NOT assumed here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple


@dataclass(frozen=True)
class Invariant:
    """A named state predicate with descriptive metadata. The engine uses `predicate` ONLY; explanation
    and severity are for human-facing layers (reports, diagnosis). `label ≠ control`."""
    name: str
    predicate: Callable = field(compare=False)        # predicate(WorldSim) -> bool
    explanation: Optional[str] = None
    severity: Optional[str] = None


def normalize_invariants(d: Dict) -> Dict:
    """Accept a dict of {name: predicate} OR {name: Invariant} and return {name: Invariant}. This is what
    lets the engine treat bare predicates (e.g. a test's lambda) and rich Invariants uniformly."""
    out = {}
    for name, val in d.items():
        out[name] = val if isinstance(val, Invariant) else Invariant(name, val)
    return out


@dataclass
class Violation:
    """A failed property at a state (or transition). `invariant` stays the NAME string for back-compat;
    `explanation`/`severity` are descriptive additions (default None ⇒ old `Violation(name, sig, path, kind)`
    call sites are unchanged)."""
    invariant: str
    sig: tuple
    path: list
    kind: str                                         # "state" or "transition"
    explanation: Optional[str] = None
    severity: Optional[str] = None


@dataclass(frozen=True)
class Trace:
    """An immutable execution path. `events` is the same action-tuple sequence the witness already was
    (so it is a superset, not a replacement); `states` is the signature after each step including the
    initial; `terminal_state` is what was true immediately after the trace — answerable WITHOUT replay.

    Invariant: a trace of N events visits N+1 states ⇒ `len(events) == length - 1` and
    `states[-1] == terminal_state`. This catches a common class of replay/off-by-one bugs early."""
    events: Tuple
    states: Tuple                                     # sig after each step, states[0] = initial
    length: int                                       # number of states (= len(events) + 1)
    terminal_state: Any                               # states[-1]

    def __post_init__(self):
        if len(self.events) != self.length - 1:
            raise ValueError(f"Trace invariant violated: len(events)={len(self.events)} != length-1={self.length - 1}")
        if not self.states or self.states[-1] != self.terminal_state:
            raise ValueError("Trace invariant violated: terminal_state must equal states[-1]")

    @classmethod
    def build(cls, world_text: str, events) -> "Trace":
        """Replay `events` on a fresh world, capturing the signature after each step. Deferred imports keep
        this module free of a load-time dependency on the kernel."""
        from world_sim import WorldSim
        from kernel_check import _snapshot_state, _sig
        sim = WorldSim(world_text)
        sigs = [_sig(_snapshot_state(sim))]
        ev = tuple(tuple(e) for e in events)
        for e in ev:
            sim.apply_event(*e)
            sigs.append(_sig(_snapshot_state(sim)))
        states = tuple(sigs)
        return cls(events=ev, states=states, length=len(states), terminal_state=states[-1])


@dataclass(frozen=True)
class ReachabilityCertificate:
    """An independently-checkable record of a CLOSED verification run: the exact reachable state set, how
    many transitions were taken, and which invariants were checked over every state.

    `verify(model, options)` re-derives the run and confirms the facts reproduce. NOTE (honesty): for the
    explicit-state engine this is NOT a cheaper proof check — verifying re-explores the graph exactly as
    producing did. The value is reproducibility/auditability/portability, and a stable target a future
    symbolic certificate (with its own, possibly cheaper, `verify`) can also satisfy. `recompute ≠ cheaper-check`."""
    explored_state_sigs: frozenset
    transition_count: int
    invariant_names: Tuple
    status: str = "CLOSED"

    def verify(self, model, options) -> bool:
        """Re-run the explicit engine on the same model/options; True iff the recorded facts reproduce."""
        from engine import ExplicitStateBFSEngine
        r = ExplicitStateBFSEngine().run(model, options)
        c = r.certificate
        return (c is not None
                and r.status == self.status
                and c.explored_state_sigs == self.explored_state_sigs
                and c.transition_count == self.transition_count
                and c.invariant_names == self.invariant_names)


# ---- the analysis reporting boundary (the shared honesty contract) ------------------------------
# AnalysisResult is a REPORTING boundary, not a domain supertype: GhostReport / CounterfactualReport /
# (future) RepairCandidate are NOT subclasses of it — each computes its own thing and *projects* into an
# AnalysisResult via an `as_analysis()` adapter. The common thing is the honesty contract, not the
# computation. `reporting-boundary ≠ domain-supertype`.

@dataclass(frozen=True)
class Finding:
    """One result item. Metadata DESCRIBES the result; it never decides it (no confidence/severity/
    recommendation fields — those become hidden control paths). `finding-metadata ≠ control`."""
    type: str                    # e.g. "CRITICAL_EVENT", "FAULT_HYPOTHESIS", "OVERDETERMINED"
    scope: str                   # the domain this finding is about, e.g. "trace", "observed-entities"
    detail: str


@dataclass(frozen=True)
class Limitation:
    """A structured honesty boundary (not a freeform string, so it composes as consumers multiply)."""
    scope: str                   # e.g. "trace", "observed-entities", "bounded-world"
    claim: str                   # e.g. "does not prove global safety"


@dataclass(frozen=True)
class AnalysisResult:
    """What every artifact consumer (diagnosis, counterfactual, repair, …) emits. The honesty travels WITH
    the result: a non-empty `scope` and at least one `Limitation` are REQUIRED — an analysis that claims no
    limitation is a smell, not a default. `analysis ≠ proof`."""
    source_trace: Tuple          # the trace/events analyzed (may be empty for observation-based analyses)
    scope: str                   # the analysis domain — REQUIRED (e.g. observed-entities / trace / bounded-world)
    findings: Tuple              # tuple[Finding]
    limitations: Tuple           # tuple[Limitation] — REQUIRED, ≥1

    def __post_init__(self):
        if not self.scope:
            raise ValueError("AnalysisResult requires a non-empty scope")
        if not self.limitations:
            raise ValueError("AnalysisResult requires ≥1 Limitation — honesty travels with the result")
