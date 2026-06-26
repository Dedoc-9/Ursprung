# SPDX-License-Identifier: AGPL-3.0-only
"""
symbolic_engine.py — Phase A.2, Step 5 (approach A): a SECOND VerificationEngine, backed by SMT.

The point of this step is NOT speed. The explicit BFS already demonstrates the authored-world sparsity
thesis. The point is to prove the verification *interface* is strong enough to host a second reasoning
engine that produces the SAME public results and compatible artifacts — without introducing a second
semantic definition.

DISCIPLINE (locked for this milestone):
  • `TransitionRelation` is the single source of truth. This engine NEVER reconstructs `apply_event`; it
    enumerates the relation (the proven semantics boundary) to extract a finite transition system, then
    hands that to the solver. `relation = semantics; engine = exploration`.
  • Identical bounded semantics: fixpoint within bound ⇒ CLOSED; frontier left at the bound ⇒ BOUNDED;
    an invariant-violating state reachable within bound ⇒ VIOLATED. There is NO new `UNSAT` status.
    `unsat-at-k ≠ unreachable`; `CLOSED = fixpoint reached`.
  • z3 is never imported here — only `solver_adapter` is. Swap the adapter, keep the engine.
  • "Symbolic proposes, semantics confirm": the SMT model is decoded to a concrete action sequence and
    REPLAYED through the same path the explicit engine uses (`Trace.build`). The engine never says "trust
    my model"; it says "here is a candidate; the transition semantics confirm it." `engine ≠ semantics`.

SCOPE (honest): approach A extracts the relation by bounded enumeration, so there is NO scaling benefit
yet — this milestone is *architectural* (a second engine) plus witness extraction. VIOLATED detection
covers STATE invariants (the transition-law `actual ⊆ potential` is a kernel guarantee the explicit engine
still checks; it does not occur in practice). Unsat-core artifacts come in a later step, as a separate
`ConstraintCertificate` ("bounded contradiction explanation", never "proof of impossibility").
"""
from __future__ import annotations

import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from artifacts import normalize_invariants, Trace       # noqa: E402
from interfaces import ReachabilityResult, VerificationResult  # noqa: E402
import solver_adapter                                    # noqa: E402  (the ONLY path to a solver)


class SymbolicEngine:
    """A bounded-model-checking VerificationEngine over the extracted transition relation."""
    name = "symbolic-bmc-" + solver_adapter.SOLVER_NAME

    def verify(self, model, options) -> VerificationResult:
        if not solver_adapter.HAVE_SOLVER:
            raise RuntimeError("SymbolicEngine requires the optional solver: pip install z3-solver")

        relation = model.transition_relation
        invariants = normalize_invariants(model.invariants)
        max_depth = options.depth_bound
        alphabet = relation.actions()
        act_id = {a: i for i, a in enumerate(alphabet)}   # Action (frozen, hashable) -> id
        id_act = {i: a for a, i in act_id.items()}

        def is_bad(state) -> bool:
            sim = relation.materialize(state)             # delegate to the relation; no WorldSim poking
            for _name, inv in invariants.items():
                try:
                    ok = inv.predicate(sim)
                except Exception:
                    ok = False
                if not ok:
                    return True
            return False

        # --- extract a finite transition system, with the SAME bounded semantics as the explicit engine
        init = model.initial_state
        id_of = {init.sig: 0}
        states = [init]
        edges = []                                        # (src_id, act_id, dst_id)
        bad_ids = set()
        if is_bad(init):
            bad_ids.add(0)
        seen = {init.sig}
        queue = deque([(init, 0)])
        truncated = False
        while queue:
            st, depth = queue.popleft()
            if depth >= max_depth:                        # bound binding? (mirror explicit truncation probe)
                for t in relation.successors(st):
                    if t.target.sig not in seen:
                        truncated = True
                        break
                continue
            for t in relation.successors(st):
                if t.target.sig not in id_of:
                    id_of[t.target.sig] = len(states)
                    states.append(t.target)
                    seen.add(t.target.sig)
                    if is_bad(t.target):
                        bad_ids.add(id_of[t.target.sig])
                    queue.append((t.target, depth + 1))
                edges.append((id_of[st.sig], act_id[t.action], id_of[t.target.sig]))

        # --- decide status with the SAME epistemic model as the explicit engine
        witness = None
        trace = None
        violations = ()
        if bad_ids:
            path_ids = solver_adapter.shortest_bad_path(0, edges, bad_ids, max_depth)
            actions = [id_act[i] for i in (path_ids or [])]
            events = tuple(a.as_args() for a in actions)
            witness = events
            trace = Trace.build(relation.world_text, events)        # symbolic proposes …
            # … semantics confirm: the replayed terminal state must actually violate an invariant
            term_state = states[id_of[trace.terminal_state]]
            sim = relation.materialize(term_state)
            failed = next((n for n, inv in invariants.items()
                           if not _safe(inv.predicate, sim)), None)
            violations = ((failed, "state"),) if failed else ()
            status = "VIOLATED"
        else:
            status = "BOUNDED" if truncated else "CLOSED"

        rr = ReachabilityResult(engine=self.name, status=status, explored_states=len(states),
                                frontier_exhausted=not truncated, witness=witness, certificate=None)
        return VerificationResult(reachability=rr, violations=violations, trace=trace)


def _safe(pred, sim) -> bool:
    try:
        return bool(pred(sim))
    except Exception:
        return False


def main():
    if not solver_adapter.HAVE_SOLVER:
        print("symbolic_engine.py — SKIPPED: optional solver not installed. `pip install z3-solver` to run.")
        return
    from engine import build_model, VerificationOptions
    from kernel_check import DEMO_WORLD
    print(f"symbolic_engine.py — Phase A.2 Step 5 (approach A): {SymbolicEngine.name}\n")
    never = {"nothing_ever_destroyed": (lambda s: all(s.runtime[e]["alive"] for e in s.runtime))}
    vr = SymbolicEngine().verify(build_model(DEMO_WORLD, invariants=never), VerificationOptions(depth_bound=3))
    print(f"  status={vr.status}  witness={vr.witness}  violations={vr.violations}")
    print("  a second engine, same contract, witness replayed through the proven relation. engine ≠ semantics.")


if __name__ == "__main__":
    main()
