# SPDX-License-Identifier: AGPL-3.0-only
"""
transition.py — Phase A.2, Step 2: the transition relation T(s, a, s'), extracted.

A *declarative* description of the kernel's dynamics — NOT a new search API. It knows nothing about
queues, visited sets, or depth bounds; it only answers "from state s, action a leads to state s'." Both
the explicit-state engine and any future symbolic engine consume the same relation, so the kernel's
semantics live in ONE place instead of being re-encoded per engine. `relation ≠ search`.

DISCIPLINE: the meaning is unchanged. This relation drives the kernel's single mutation path
(`WorldSim.apply_event`) using the *same* state snapshot/restore/signature and the *same* action alphabet
(in the *same* deterministic order) as `kernel_check.py`. `test_transition.py` differential-checks that the
extracted relation reproduces the legacy inline successor behavior exactly — before any engine consumes it.

STAGING: this step only *introduces* T. It does NOT rewire `kernel_check.check()` to consume it — that is
Step 3 (engine abstraction), where the current BFS becomes `ExplicitStateEngine` over this relation. So
`kernel_check.py` stays untouched and the existing suites stay green. `extracted ≠ rewired`.

MODEL BOUNDARIES (stated, not hidden):
  • The action alphabet is currently state-independent (`actions(state)` returns the same set for every
    state); `state` is accepted now so preconditions can filter it later without changing the interface.
    `alphabet-now ≠ precondition-filtered-later`.
  • `Transition` carries only source/action/target today. Optional metadata (preconditions, effects, cost,
    labels, provenance) can be added later WITHOUT changing consumers. `minimal-record ≠ final-record`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

# Reuse the reference engine's semantics verbatim so the extraction cannot drift from it.
from kernel_check import (WorldSim, build_alphabet,        # noqa: E402
                          _snapshot_state, _restore_state, _sig)


@dataclass(frozen=True)
class Action:
    """A kernel edit, as a value (not a bare string) so metadata can be added later without churn."""
    kind: str
    target: str
    amount: int = 0
    faction: str = ""
    dtype: str = ""

    def as_args(self) -> Tuple:
        """Arguments for `WorldSim.apply_event(*args)`. Defaults match apply_event's own defaults."""
        return (self.kind, self.target, self.amount, self.faction, self.dtype)

    @classmethod
    def from_tuple(cls, t: Tuple) -> "Action":
        """Build from a `build_alphabet` tuple like ('destroy', x) or ('capture', x, 0, f)."""
        return cls(t[0], t[1],
                   t[2] if len(t) > 2 else 0,
                   t[3] if len(t) > 3 else "",
                   t[4] if len(t) > 4 else "")

    def __str__(self) -> str:
        s = f"{self.kind} {self.target}"
        if self.amount:
            s += f" {self.amount}"
        if self.faction:
            s += f" -> {self.faction}"
        return s


@dataclass(frozen=True)
class State:
    """A kernel state. Identity (eq/hash) is the canonical signature; the raw snapshot rides along for
    application but is excluded from equality so two paths to the same world are ONE state. `path ≠ state`."""
    sig: Tuple
    snapshot: Any = field(compare=False, repr=False)


@dataclass(frozen=True)
class Transition:
    """One T(s, a, s') fact. Minimal today; extensible (preconditions/effects/cost/labels) later."""
    source: State
    action: Action
    target: State
    # reserved for later, without changing consumers:
    metadata: Optional[dict] = field(default=None, compare=False, repr=False)


class TransitionRelation:
    """Declarative dynamics over one world. No search state lives here."""

    def __init__(self, world_text: str, include_capture: bool = False):
        self.world_text = world_text
        self.include_capture = include_capture
        self._base = WorldSim(world_text)                       # reused engine; every call restores it first
        self._alphabet = tuple(Action.from_tuple(a)
                               for a in build_alphabet(self._base, include_capture))

    def initial(self) -> State:
        snap = _snapshot_state(WorldSim(self.world_text))
        return State(_sig(snap), snap)

    def actions(self, state: State = None) -> Tuple:
        """The actions available from `state`. State-independent today (see MODEL BOUNDARIES)."""
        return self._alphabet

    def step(self, state: State, action: Action) -> Transition:
        """The single T(s, a, s') fact for one (state, action). Raises if the action is inapplicable."""
        _restore_state(self._base, state.snapshot)
        self._base.apply_event(*action.as_args())
        snap = _snapshot_state(self._base)
        return Transition(state, action, State(_sig(snap), snap))

    def successors(self, state: State) -> list:
        """All T(s, a, s') from `state`, in deterministic alphabet order. Inapplicable actions are skipped
        (matching the reference engine's try/except-continue), producing no transition."""
        out = []
        for a in self._alphabet:
            _restore_state(self._base, state.snapshot)
            try:
                self._base.apply_event(*a.as_args())
            except Exception:
                continue
            snap = _snapshot_state(self._base)
            out.append(Transition(state, a, State(_sig(snap), snap)))
        return out


def main():
    from kernel_check import DEMO_WORLD
    print("transition.py — Phase A.2 Step 2: the transition relation T(s, a, s')\n")
    tr = TransitionRelation(DEMO_WORLD)
    s0 = tr.initial()
    succ = tr.successors(s0)
    print(f"  alphabet size: {len(tr.actions())}   successors of initial: {len(succ)}")
    print("  first few transitions from the initial state:")
    for t in succ[:4]:
        changed = t.source.sig != t.target.sig
        print(f"    {str(t.action):28s} -> {'new state' if changed else 'no-op (same state)'}")
    print("\n  T knows nothing about BFS, queues, or depth. Engines (Step 3) consume it; semantics live here once.")


if __name__ == "__main__":
    main()
