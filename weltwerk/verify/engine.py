# SPDX-License-Identifier: AGPL-3.0-only
"""
engine.py — Phase A.2, Step 3: the verification engine abstraction.

ONE architectural boundary, three roles kept separate (no god object):
  • TransitionRelation  → SEMANTICS: "from this state, what transitions are possible?" (nothing else)
  • VerificationEngine  → SEARCH:    queue/frontier, visited set, depth bound, termination policy,
                                      witness reconstruction, and enforcing per-transition properties
  • VerificationResult  → CONTRACT:  the only object downstream consumes; it never learns which engine ran

`ExplicitStateBFSEngine` is the only implementation today; a `SymbolicEngine` will later satisfy the same
`VerificationEngine` protocol and return the same `VerificationResult`, so no consumer changes. `engine ≠ semantics`.

This is the step where the BFS algorithm leaves `kernel_check.py`. After Step 3 there is exactly ONE search
implementation — here — and `kernel_check.check()` is a compatibility shim that delegates to it. The engine
sources successors only from `TransitionRelation` (Step 2, differential-tested equivalent) and evaluates
invariants via `relation.materialize(state)`, so the kernel's semantics are not re-encoded.

Step 3 deliberately does NOT introduce first-class `Invariant` objects, certificates, predecessor
relations, or a symbolic backend — those are Step 4+. `invariants` stays the existing name→predicate dict.
One axis at a time. `engine-abstraction ≠ artifact-enrichment`.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, Protocol, Tuple

from transition import TransitionRelation, State
from kernel_check import CheckResult, DEFAULT_INVARIANTS
from artifacts import Violation, Trace, ReachabilityCertificate, normalize_invariants


@dataclass(frozen=True)
class WorldModel:
    """Everything a verification engine needs about a world, bundled so the engine signature does not grow
    a new positional argument per feature. `model ≠ options` (what to verify vs how to search)."""
    initial_state: State
    transition_relation: TransitionRelation
    invariants: Dict            # name → predicate(WorldSim) -> bool  (existing representation; Invariant is Step 4)
    action_alphabet: Tuple


@dataclass(frozen=True)
class VerificationOptions:
    """How to search. One field today; room to grow (frontier limits, stopping policy, witness/certificate
    level, engine diagnostics) without changing the engine signature."""
    depth_bound: int = 6
    stop_on_first: bool = True


class VerificationEngine(Protocol):
    """The stable engine interface. Any engine (explicit, symbolic, hybrid) satisfies this and returns the
    same contract; consumers depend on the result, never on the algorithm."""
    def verify(self, model: WorldModel, options: VerificationOptions):    # -> VerificationResult
        ...


def build_model(world_text: str, *, include_capture: bool = False, invariants: Dict = None) -> WorldModel:
    """Convenience: assemble a WorldModel from world text (relation + initial + invariants + alphabet)."""
    rel = TransitionRelation(world_text, include_capture)
    return WorldModel(initial_state=rel.initial(), transition_relation=rel,
                      invariants=invariants or DEFAULT_INVARIANTS, action_alphabet=rel.actions())


class ExplicitStateBFSEngine:
    """Breadth-first explicit-state search. Owns ALL search concerns; sources transitions from the relation.

    `run()` produces the rich legacy `CheckResult` (so `kernel_check.check()` is a thin shim and the
    existing suite is unchanged). `verify()` projects that into the minimal public `VerificationResult`.
    The reachable-set/closure semantics are identical to the pre-Step-3 checker — only the *home* of the
    algorithm changed. `moved ≠ changed`.
    """
    name = "explicit-state-bfs"

    def run(self, model: WorldModel, options: VerificationOptions) -> CheckResult:
        relation = model.transition_relation
        invariants = normalize_invariants(model.invariants)   # {name: Invariant}; engine uses .predicate only
        alphabet = model.action_alphabet
        a = len(alphabet)
        max_depth = options.depth_bound
        stop_on_first = options.stop_on_first
        potential_bound = sum(a ** i for i in range(max_depth + 1))

        init = model.initial_state
        parent = {init.sig: None}                  # sig -> (parent_sig, Action) for path reconstruction
        states = {init.sig: init}                  # sig -> State
        queue = deque([(init, 0)])
        violations = []
        transitions = 0
        truncated = False
        reached_depth = 0

        def path_to(sig):
            out = []
            while parent[sig] is not None:
                psig, action = parent[sig]
                out.append(action.as_args())       # minimal-arity tuple == legacy path element
                sig = psig
            return list(reversed(out))

        def result(status):
            # CLOSED ⇒ an independently-checkable certificate; VIOLATED ⇒ a first-class ghost Trace.
            cert = None
            if status == "CLOSED":
                cert = ReachabilityCertificate(explored_state_sigs=frozenset(states),
                                               transition_count=transitions,
                                               invariant_names=tuple(sorted(invariants)),
                                               status="CLOSED")
            trace = Trace.build(relation.world_text, violations[0].path) if violations else None
            return CheckResult(status, len(states), transitions, reached_depth, truncated,
                               potential_bound, a, violations, certificate=cert, trace=trace)

        def check_state(state):
            sim = relation.materialize(state)      # a WorldSim positioned at `state`
            for name, inv in invariants.items():
                try:
                    ok = inv.predicate(sim)
                except Exception:                  # an invariant that throws is a violation, not a crash
                    ok = False
                if not ok:
                    violations.append(Violation(name, state.sig, path_to(state.sig), "state",
                                                explanation=inv.explanation, severity=inv.severity))
                    return False
            return True

        if not check_state(init) and stop_on_first:
            return result("VIOLATED")

        while queue:
            state, depth = queue.popleft()
            reached_depth = max(reached_depth, depth)
            if depth >= max_depth:
                # is the bound genuinely binding? (would expansion discover anything new?)
                for t in relation.successors(state):
                    if t.target.sig not in states:
                        truncated = True
                        break
                continue
            for t in relation.successors(state):
                transitions += 1
                # transition property: the central law actual ⊆ potential, enforced by the engine.
                if not set(t.metadata["actual"]) <= set(t.metadata["potential"]):
                    if t.target.sig not in parent:
                        parent[t.target.sig] = (state.sig, t.action)
                    violations.append(Violation("potential_superset_actual", t.target.sig,
                                                path_to(t.target.sig), "transition",
                                                explanation="actual ⊆ potential must hold for every transition.",
                                                severity="critical"))
                    if stop_on_first:
                        return result("VIOLATED")
                if t.target.sig not in states:
                    states[t.target.sig] = t.target
                    parent[t.target.sig] = (state.sig, t.action)
                    if check_state(t.target) is False and stop_on_first:
                        return result("VIOLATED")
                    queue.append((t.target, depth + 1))

        if violations:
            status = "VIOLATED"
        elif truncated:
            status = "BOUNDED"
        else:
            status = "CLOSED"
        return result(status)

    def verify(self, model: WorldModel, options: VerificationOptions):
        """Public contract: run the search, project to the minimal VerificationResult."""
        from interfaces import from_check_result
        return from_check_result(self.run(model, options))


def main():
    from kernel_check import DEMO_WORLD
    print("engine.py — Phase A.2 Step 3: ExplicitStateBFSEngine over TransitionRelation\n")
    model = build_model(DEMO_WORLD)
    eng = ExplicitStateBFSEngine()
    vr = eng.verify(model, VerificationOptions(depth_bound=4))
    print(f"  engine={vr.engine!r}  status={vr.status}  explored_states={vr.explored_states}  "
          f"frontier_exhausted={vr.frontier_exhausted}")
    print("  the BFS now lives here; kernel_check.check() is a compatibility shim that delegates to it.")
    print("  a SymbolicEngine will satisfy the same protocol and return the same VerificationResult.")


if __name__ == "__main__":
    main()
