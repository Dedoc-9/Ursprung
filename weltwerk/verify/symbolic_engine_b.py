# SPDX-License-Identifier: AGPL-3.0-only
"""
symbolic_engine_b.py — Phase A.2 Approach B (CANDIDATE): a VerificationEngine that re-encodes apply_event
DIRECTLY into SMT constraints (via solver_adapter_b) and does symbolic bounded model checking.

Status: CANDIDATE / [OPEN]. This is a SECOND expression of the kernel semantics (the divergence risk), so it
is not a supported engine until `test_symbolic_b.py` confirms it matches the explicit engine. It is a
violation *accelerator*: it returns VIOLATED (with a replayable witness) or BOUNDED (no violation within the
depth bound). It does NOT return CLOSED — proving unreachability needs k-induction (deferred).
`unsat-at-k ≠ unreachable`; `re-encoded ≠ verified`.

Invariants here are SYMBOLIC (`SymbolicInvariant`) — Python-lambda invariants are not SMT-translatable, so
Approach B requires the property in a form the solver can encode. Supported fragment: `{destroy, repair}`
over per-entity `(alive, disabled)`; invariants over those (`not_disabled` / `not_destroyed`).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                                # noqa: E402
from kernel_check import build_alphabet                       # noqa: E402
from artifacts import Trace                                   # noqa: E402
from interfaces import ReachabilityResult, VerificationResult # noqa: E402
import solver_adapter_b                                       # noqa: E402  (the ONLY path to z3 here)


@dataclass(frozen=True)
class SymbolicInvariant:
    """A property the solver can encode. kind ∈ {'not_disabled','not_destroyed'} over a single entity."""
    kind: str
    entity: str

    @property
    def name(self) -> str:
        return f"{self.kind}:{self.entity}"


class SymbolicDirectEngine:
    """Approach B: direct apply_event→SMT bounded model checking. Construct with the symbolic invariant."""
    name = "symbolic-direct-bmc-" + solver_adapter_b.SOLVER_NAME

    def __init__(self, sym_invariant: SymbolicInvariant):
        self.inv = sym_invariant

    def verify(self, model, vopts) -> VerificationResult:
        if not solver_adapter_b.HAVE_SOLVER:
            raise RuntimeError("SymbolicDirectEngine requires the optional solver: pip install z3-solver")
        world = model.transition_relation.world_text
        sim = WorldSim(world)
        nodes = list(sim.cg.nodes)
        reach = {e: set(sim.cg.reach_ge1(e)) for e in nodes}
        upstream = {e: {u for u in nodes if e in reach[u]} for e in nodes}
        options = [tuple(a) for a in build_alphabet(sim)]      # {destroy, repair} tuples
        bad_spec = (self.inv.kind, self.inv.entity)

        path = solver_adapter_b.shortest_violation(nodes, reach, upstream, options, bad_spec, vopts.depth_bound)

        if path is not None:
            events = tuple(options[i] for i in path)
            trace = Trace.build(world, events)
            rr = ReachabilityResult(engine=self.name, status="VIOLATED", explored_states=0,
                                    frontier_exhausted=False, witness=events, certificate=None)
            return VerificationResult(reachability=rr, violations=((self.inv.name, "state"),), trace=trace)

        # no violation within the bound — BOUNDED (NOT closed: k-induction not implemented)
        rr = ReachabilityResult(engine=self.name, status="BOUNDED", explored_states=0,
                                frontier_exhausted=False, witness=None, certificate=None)
        return VerificationResult(reachability=rr, violations=(), trace=None)


def main():
    if not solver_adapter_b.HAVE_SOLVER:
        print("symbolic_engine_b.py — SKIPPED: optional solver not installed. `pip install z3-solver` to run.")
        return
    from engine import build_model, VerificationOptions
    star = ('world "B"\n'
            'entity fac:\n  position 0 0 0\n  controls hub\n'
            'entity hub:\n  position 1 0 0\n  health 10\n  powers tail\n'
            'entity tail:\n  position 2 0 0\n  health 10\n')
    print(f"symbolic_engine_b.py — Approach B (CANDIDATE): {SymbolicDirectEngine.name}\n")
    eng = SymbolicDirectEngine(SymbolicInvariant("not_disabled", "tail"))
    vr = eng.verify(build_model(star), VerificationOptions(depth_bound=4))
    print(f"  status={vr.status}  witness={vr.witness}  violations={vr.violations}")
    print("  CANDIDATE: a direct SMT re-encoding of apply_event; gated by test_symbolic_b.py (differential).")


if __name__ == "__main__":
    main()
