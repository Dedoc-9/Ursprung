# SPDX-License-Identifier: AGPL-3.0-only
"""
oracle_reference.py — Proof Obligation PO-4: an INDEPENDENT ground-truth reachability oracle.

`differential.py` shows two engines AGREE; agreement is necessary but not sufficient for correctness
(a shared bug would pass). This module discharges that gap on tiny worlds: it computes the *exact* reachable
set by an UNBOUNDED fixpoint, with its own state-signature, its own alphabet construction, and its own search
loop — none of the engine's search code. The companion test asserts the engine's verdict equals this oracle.

What is shared vs independent (stated honestly):
  • SHARED (correctly): `WorldSim.apply_event` — the kernel's transition *semantics* is the single spec both
    the engine and this oracle must obey. Re-implementing it would test a different system. We are validating
    the engine's *search / verdict* logic, not re-deriving the kernel's meaning.
  • INDEPENDENT: the signature (`_osig`), the alphabet (`_oalphabet`), the fixpoint search, and the verdict.

The oracle is ground truth only because the worlds are tiny enough to reach a full fixpoint (no depth bound),
so it returns `CLOSED` (exhaustive, true) or `VIOLATED` with the true shortest counterexample length —
never `BOUNDED`. `oracle ≠ engine-code`; `agreement-with-oracle ⇒ engine search is sound on this world`.
"""
from __future__ import annotations

import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                       # noqa: E402  (the shared semantics spec)
from artifacts import normalize_invariants           # noqa: E402


def _oalphabet(sim):
    """Independent alphabet: all destroys, then all repairs, over non-faction nodes (order-agnostic for a set)."""
    targets = sorted(n for n in sim.cg.nodes if n not in sim.factions)
    return [("destroy", t) for t in targets] + [("repair", t) for t in targets]


def _osig(sim):
    """Independent canonical signature (different construction from kernel_check._sig)."""
    body = tuple(sorted((k, sim.runtime[k]["alive"], sim.runtime[k]["status"], sim.runtime[k]["health"])
                        for k in sim.cg.nodes))
    return (body, tuple(sorted(sim.captured.items())))


def oracle(world_text, invariants):
    """Exact verdict by unbounded fixpoint. Returns (status, shortest_violation_len_or_None, reachable_count)."""
    invs = normalize_invariants(invariants)
    sim = WorldSim(world_text)
    alpha = _oalphabet(sim)

    def snap():
        return ({k: dict(v) for k, v in sim.runtime.items()}, dict(sim.captured))

    def restore(st):
        sim.runtime = {k: dict(v) for k, v in st[0].items()}
        sim.captured = dict(st[1])
        sim.events = []

    def violates():
        for _name, inv in invs.items():
            try:
                ok = inv.predicate(sim)
            except Exception:
                ok = False
            if not ok:
                return True
        return False

    init = snap()
    init_sig = _osig(sim)
    states = {init_sig: init}
    dist = {init_sig: 0}
    shortest_viol = 0 if violates() else None       # sim is at init here
    q = deque([init_sig])
    while q:
        sg = q.popleft()
        d = dist[sg]
        for act in alpha:
            restore(states[sg])
            try:
                sim.apply_event(*act)
            except Exception:
                continue
            nsig = _osig(sim)
            if nsig not in dist:
                dist[nsig] = d + 1
                states[nsig] = snap()
                if shortest_viol is None and violates():     # BFS order ⇒ first found is shortest
                    shortest_viol = d + 1
                q.append(nsig)
    if shortest_viol is not None:
        return ("VIOLATED", shortest_viol, len(states))
    return ("CLOSED", None, len(states))


def main():
    print("oracle_reference.py — PO-4: independent ground-truth reachability oracle\n")
    small = ('world "T"\n'
             'entity faction_a:\n  position 0 0 0\n  controls hub\n'
             'entity hub:\n  position 1 0 0\n  health 10\n  powers leaf\n'
             'entity leaf:\n  position 2 0 0\n  health 10\n')
    never = {"nothing_ever_destroyed": (lambda s: all(s.runtime[e]["alive"] for e in s.runtime))}
    from kernel_check import DEFAULT_INVARIANTS, check
    o1 = oracle(small, DEFAULT_INVARIANTS)
    e1 = check(small, max_depth=12)
    print(f"  default invariants:   oracle={o1}   engine=({e1.status}, states={e1.states_explored})")
    o2 = oracle(small, never)
    e2 = check(small, max_depth=12, invariants=never)
    print(f"  never_destroyed:      oracle={o2}   engine=({e2.status}, ghost_len={len(e2.ghost.path) if e2.ghost else None})")
    print("\n  PO-4 discharged iff engine verdicts match the oracle across the test suite (agreement ≠ soundness).")


if __name__ == "__main__":
    main()
