# SPDX-License-Identifier: AGPL-3.0-only
"""
counterfactual.py — Phase C: "if event X had not occurred…" over a ghost trace.

Given a VIOLATED result's ghost trace (the event sequence reaching a bad state — from *either* engine; this
consumes the artifact, not the algorithm), this finds which events are CRITICAL to that counterexample by
single-event ablation: remove event e_i, replay the rest, and ask whether a violating state is still
reached. It is pure-stdlib (replay only) — no solver needed.

WHAT "CRITICAL" MEANS — AND DOES NOT (Dentatus discipline):
  • An event is **critical** iff removing it from THIS trace makes the reduced trajectory reach NO violating
    state. It is **redundant** iff the violation persists without it.
  • This is trace-level: `critical-for-this-trace ≠ globally-necessary`. Removing a critical event prevents
    THIS ghost, not all ghosts — a different event sequence might still violate. Proving the world is safe
    after *forbidding an action entirely* is a STRONGER, separate question (re-run the model checker with a
    restricted alphabet, or the symbolic `assert NOT(action)`); those are documented follow-ups, not this.
    `prevents-this-ghost ≠ makes-world-safe`.
  • An **overdetermined** ghost (e.g. two independent destroys, each sufficient) has NO single critical
    event — every single removal leaves the violation. That is reported honestly (critical set empty), not
    hidden. `no-single-cause ≠ no-cause`.
  • Ablation only removes events; it does not reorder or substitute. `ablation ≠ full-counterfactual-space`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                       # noqa: E402  (replay only)
from artifacts import normalize_invariants           # noqa: E402
from kernel_check import DEFAULT_INVARIANTS, DEMO_WORLD   # noqa: E402


@dataclass(frozen=True)
class Counterfactual:
    index: int                       # position in the original trace
    removed_event: tuple             # the event removed
    prevents_violation: bool         # True ⇒ removing it makes the reduced trajectory reach NO violation


@dataclass(frozen=True)
class CounterfactualReport:
    ghost_trace: Tuple               # the original event sequence
    input_violates: bool             # did the given trace actually reach a violation? (sanity)
    critical: Tuple                  # events whose removal PREVENTS the violation (necessary for this ghost)
    redundant: Tuple                 # events whose removal LEAVES the violation
    analyses: Tuple                  # tuple[Counterfactual]
    note: Optional[str] = None

    def report(self) -> str:
        if not self.input_violates:
            return ("Counterfactual: the supplied trace reaches no violation — nothing to explain.\n"
                    "  (a counterfactual explains a VIOLATED trace; this one is clean.)")
        lines = [f"Counterfactual over ghost trace ({len(self.ghost_trace)} events):"]
        for a in self.analyses:
            tag = "CRITICAL " if a.prevents_violation else "redundant"
            lines.append(f"  [{tag}] e{a.index}: {a.removed_event}")
        if self.critical:
            lines.append(f"  → critical (removing prevents THIS ghost): {list(self.critical)}")
        else:
            lines.append("  → no single event is critical: the violation is OVERDETERMINED "
                         "(multiple sufficient causes). no-single-cause ≠ no-cause.")
        lines.append("  trace-level only: prevents-this-ghost ≠ makes-world-safe.")
        return "\n".join(lines)


def _any_violation(sim, invariants) -> bool:
    for _name, inv in invariants.items():
        try:
            ok = inv.predicate(sim)
        except Exception:
            ok = False
        if not ok:
            return True
    return False


def _trajectory_violates(world_text: str, events, invariants) -> bool:
    """Replay `events` on a fresh world; True iff ANY visited state (incl. initial) violates an invariant.
    Inapplicable events after ablation are skipped (they no-op), matching honest replay semantics."""
    sim = WorldSim(world_text)
    if _any_violation(sim, invariants):
        return True
    for ev in events:
        try:
            sim.apply_event(*ev)
        except Exception:
            continue
        if _any_violation(sim, invariants):
            return True
    return False


def analyze(world_text: str, ghost_trace, invariants=None) -> CounterfactualReport:
    """Single-event ablation over `ghost_trace`. Returns which events are critical vs redundant for the
    violation this trace produces. `invariants` defaults to DEFAULT_INVARIANTS (name→predicate or Invariant)."""
    invs = normalize_invariants(invariants or DEFAULT_INVARIANTS)
    events = tuple(tuple(e) for e in ghost_trace)

    input_violates = _trajectory_violates(world_text, events, invs)
    if not input_violates:
        return CounterfactualReport(events, False, (), (), (),
                                    note="supplied trace reaches no violation")

    analyses = []
    for i in range(len(events)):
        reduced = events[:i] + events[i + 1:]
        prevents = not _trajectory_violates(world_text, reduced, invs)
        analyses.append(Counterfactual(i, events[i], prevents))

    critical = tuple(a.removed_event for a in analyses if a.prevents_violation)
    redundant = tuple(a.removed_event for a in analyses if not a.prevents_violation)
    note = None
    if not events:
        note = "empty trace — the initial state itself violates (unconditional)."
    elif not critical:
        note = "overdetermined: no single event is critical."
    return CounterfactualReport(events, True, critical, redundant, tuple(analyses), note=note)


def from_result(world_text: str, result, invariants=None) -> CounterfactualReport:
    """Convenience: analyze a VIOLATED VerificationResult (uses its witness). Engine-agnostic."""
    witness = getattr(result, "witness", None) or ()
    return analyze(world_text, witness, invariants)


def main():
    from kernel_check import check
    print("counterfactual.py — Phase C: critical events in a ghost trace (trace-level ablation)\n")
    never = {"nothing_ever_destroyed": (lambda s: all(s.runtime[e]["alive"] for e in s.runtime))}
    g = check(DEMO_WORLD, max_depth=2, invariants=never).ghost
    rep = analyze(DEMO_WORLD, g.path, never)
    print(rep.report())
    print("\n  trace-level: it explains THIS counterexample, not the safety of the whole world.")


if __name__ == "__main__":
    main()
