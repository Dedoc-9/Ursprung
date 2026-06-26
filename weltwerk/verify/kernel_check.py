# SPDX-License-Identifier: AGPL-3.0-only
"""
kernel_check.py — a bounded explicit-state MODEL CHECKER over the causal kernel (WorldSim).

Provenance: the *idea* (systematically explore all reachable states and check invariants, returning a
shortest counterexample trace) is reimplemented clean-room from explicit-state model-checking literature
— the discipline NASA's Java Pathfinder embodies for Java. No JPF source is used; JPF checks Java
bytecode, this checks an authored causal world. See ../../docs/PROVENANCE.md.

WHY IT FITS WELTWERK (the novel use):
  • The kernel's reachable state-set under a bounded set of edits IS the **Actual**.
  • The combinatorial space of all action sequences up to the depth bound IS the **Potential**.
  • A reached state that violates an invariant is a **ghost**: the checker returns the *shortest* event
    path to it — a replayable witness, not a guess.
This turns "validity-not-outcome" testing into actual exhaustive verification of the world's transition
relation, while staying 100% original code (own copyright → dual-license-safe).

EPISTEMIC STATES (honest grading of the result):
  • CLOSED  — the frontier emptied before the depth bound: the explored set is the COMPLETE reachable
              set for this action alphabet ⇒ invariants are PROVEN over it. `state-space-closed = proof`.
  • BOUNDED — expansion was cut off by the depth bound: invariants hold on what was explored but the
              rest is UNDERDETERMINED. `depth-limited ≠ proof`.
  • VIOLATED — at least one invariant fails; a counterexample ghost trace is attached.

MODEL BOUNDARIES (Arbitrary-Boundary Law — stated, not hidden):
  • The action alphabet is a MODEL CHOICE. Default = {destroy, repair} over every non-faction entity
    (a finite kill/revive lattice). `damage(amount)` is excluded by default because unbounded amounts
    make the state space infinite; include_capture adds {capture→faction}. Different alphabet ⇒ different
    Potential. The checker proves nothing about edits outside its alphabet. `alphabet ≠ all-edits`.
  • State identity = (per-node alive/status/health) + explicit captures. It deliberately EXCLUDES the
    event log, so two different paths to the same world are ONE state (that is what makes closure finite).
    `path ≠ state`.
  • Invariants are predicates we chose; passing them is `consistent-with-our-invariants`, not `correct`.
    `holds-here ≠ true`.

NOT a substitute for: testing concrete gameplay, performance, or any property outside the alphabet.

PHASE A.2 STEP 3: the SEARCH ALGORITHM has moved to `engine.ExplicitStateBFSEngine`. This module is now
the compatibility API — `check()` (a shim that delegates to the engine), the `CheckResult` / `Violation`
result types, `replay_path`, the kernel state helpers (`_snapshot_state`/`_restore_state`/`_sig`/
`build_alphabet`), and `DEFAULT_INVARIANTS`. No search algorithm remains here. `compat-layer ≠ algorithm`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim, DEMO_WORLD   # noqa: E402

# A state = ({entity: {alive,status,health,max}}, {entity: faction}). Hashable signature excludes events.
State = tuple


def _snapshot_state(sim: WorldSim) -> tuple:
    return ({k: dict(v) for k, v in sim.runtime.items()}, dict(sim.captured))


def _restore_state(sim: WorldSim, st: tuple) -> None:
    runtime, captured = st
    sim.runtime = {k: dict(v) for k, v in runtime.items()}
    sim.captured = dict(captured)
    sim.events = []


def _sig(st: tuple):
    runtime, captured = st
    return (tuple((k, runtime[k]["alive"], runtime[k]["status"], runtime[k]["health"])
                  for k in sorted(runtime)),
            tuple(sorted(captured.items())))


def build_alphabet(sim: WorldSim, include_capture: bool = False) -> list:
    """The action set explored. Each action is an apply_event arg tuple. MODEL CHOICE (see header)."""
    targets = [n for n in sorted(sim.cg.nodes) if n not in sim.factions]
    alpha = []
    for t in targets:
        alpha.append(("destroy", t))
        alpha.append(("repair", t))
    if include_capture:
        for t in targets:
            for f in sim.factions:
                alpha.append(("capture", t, 0, f))
    return alpha


# ---- invariants: predicate(sim_restored_to_state) -> bool (True = holds) -----------------------
def _inv_health_in_bounds(sim: WorldSim) -> bool:
    return all(0 <= sim.runtime[e]["health"] <= sim.runtime[e]["max"] for e in sim.runtime)


def _inv_dead_implies_destroyed(sim: WorldSim) -> bool:
    return all(sim.runtime[e]["alive"] or
               (sim.runtime[e]["health"] == 0 and sim.runtime[e]["status"] == "destroyed")
               for e in sim.runtime)


def _inv_controller_total(sim: WorldSim) -> bool:
    valid = set(sim.factions) | {"contested", "neutral"}
    return all(sim.controller(e) in valid for e in sim.cg.nodes)


DEFAULT_INVARIANTS = {
    "health_in_bounds": _inv_health_in_bounds,
    "dead_implies_destroyed": _inv_dead_implies_destroyed,
    "controller_total": _inv_controller_total,
}


@dataclass
class Violation:
    invariant: str
    sig: tuple
    path: list                       # the shortest event path (ghost) to the violating state
    kind: str                        # "state" or "transition"


@dataclass
class CheckResult:
    status: str                      # CLOSED | BOUNDED | VIOLATED
    states_explored: int             # |Actual|
    transitions: int
    max_depth: int
    truncated: bool                  # True ⇒ the depth bound cut off real frontier (⇒ BOUNDED)
    potential_bound: int             # sum_{i=0..D} |A|^i  (|Potential| upper bound at search level)
    alphabet_size: int
    violations: list = field(default_factory=list)

    @property
    def ghost(self):
        """The first (shortest) counterexample trace, or None. A ghost ALLOCATES investigation."""
        return self.violations[0] if self.violations else None

    def report(self) -> str:
        comp = (self.states_explored / self.potential_bound) if self.potential_bound else 0.0
        lines = [
            f"  status: {self.status}",
            f"  states explored (Actual): {self.states_explored}",
            f"  potential bound (|A|<=D):  {self.potential_bound}   (Actual/Potential = {comp:.4g})",
            f"  transitions: {self.transitions}   alphabet: {self.alphabet_size}   max_depth: {self.max_depth}",
        ]
        if self.status == "CLOSED":
            lines.append("  ⇒ reachable set is COMPLETE for this alphabet: invariants PROVEN over it. "
                         "(state-space-closed = proof; alphabet ≠ all-edits)")
        elif self.status == "BOUNDED":
            lines.append("  ⇒ depth bound cut the frontier: invariants hold on what was explored, the "
                         "rest is UNDERDETERMINED. (depth-limited ≠ proof)")
        else:
            g = self.ghost
            lines.append(f"  ⇒ VIOLATED: '{g.invariant}' ({g.kind}). shortest ghost trace ({len(g.path)} "
                         f"events): {g.path}")
        return "\n".join(lines)


def check(world_text: str, *, max_depth: int = 6, include_capture: bool = False,
          invariants: dict = None, stop_on_first: bool = True) -> CheckResult:
    """Compatibility shim (Phase A.2 Step 3): the legacy entry point. NO search algorithm lives here.

    It assembles a `WorldModel` + `VerificationOptions` and delegates to the single search implementation,
    `engine.ExplicitStateBFSEngine`, returning the same `CheckResult` as before. The BFS moved out; behavior
    did not. Imports are deferred to keep this module free of an engine/transition import cycle.
    `compat-layer ≠ algorithm`.
    """
    from engine import ExplicitStateBFSEngine, VerificationOptions, build_model   # deferred (no cycle)
    model = build_model(world_text, include_capture=include_capture, invariants=invariants)
    options = VerificationOptions(depth_bound=max_depth, stop_on_first=stop_on_first)
    return ExplicitStateBFSEngine().run(model, options)


def replay_path(world_text: str, path: list) -> tuple:
    """Re-apply a ghost path on a FRESH world; return its state signature. A witness must be replayable —
    if replay_path(...) of a violation's path doesn't reproduce the violating signature, the ghost is an
    artifact of the checker, not of the world. `trace ≠ truth` until it replays."""
    sim = WorldSim(world_text)
    for action in path:
        sim.apply_event(*action)
    return _sig(_snapshot_state(sim))


def main():
    print("kernel_check.py — bounded explicit-state model checker over the causal kernel\n")
    res = check(DEMO_WORLD, max_depth=4)
    print(res.report())
    print()
    # demonstrate a ghost: an invariant the world WILL violate (something does get destroyed),
    # and show the shortest counterexample is a real, replayable trace.
    never_destroyed = {"nothing_ever_destroyed":
                       lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime)}
    g = check(DEMO_WORLD, max_depth=2, invariants=never_destroyed)
    print(g.report())
    if g.ghost:
        replayed = replay_path(DEMO_WORLD, g.ghost.path) == g.ghost.sig
        print(f"  ghost replays faithfully on a fresh world: {replayed}  (trace ≠ truth until it replays)")


if __name__ == "__main__":
    main()
