# SPDX-License-Identifier: AGPL-3.0-only
"""
solver_adapter.py — Phase A.2, Step 5: the ONLY module that imports the SMT solver.

The symbolic engine talks to *this* adapter, never to z3. That keeps the boundary the architecture needs:

    symbolic_engine.py  →  solver_adapter.py  →  z3

so a future `solver_adapter_pure.py` (or a different solver) can be swapped in without touching the engine.
`solver = engine dependency, NOT architecture dependency`: nothing else in Weltwerk imports z3, and the
core stays pure-stdlib. z3-solver is optional — if it is not installed, `HAVE_SOLVER` is False and callers
skip the symbolic backend cleanly. (Install: `pip install z3-solver`; z3 is MIT, AGPL-compatible.)

What it does (approach A): bounded model checking over a FINITE transition system that the engine extracted
from the proven `TransitionRelation`. It does NOT re-encode the kernel's semantics — it reasons over edges
the relation already produced. So this is a second *reasoning* engine, not a second *semantic* definition.
`unsat-at-depth-k ≠ unreachable`; the public CLOSED/BOUNDED meaning is decided by the engine, not here.
"""
from __future__ import annotations

try:
    import z3 as _z3
    HAVE_SOLVER = True
    SOLVER_NAME = "z3"
except Exception:                       # ImportError, or z3 present but broken
    _z3 = None
    HAVE_SOLVER = False
    SOLVER_NAME = "none"


def shortest_bad_path(init_id: int, edges, bad_ids, max_depth: int):
    """Bounded model checking: the SHORTEST action-id path from `init_id` to ANY state in `bad_ids`,
    within `max_depth` steps — or None if no bad state is reachable within the bound.

    `edges` is an iterable of (src_id, act_id, dst_id) integer triples (the extracted relation). Returns a
    list of action ids (empty list if `init_id` is itself bad). Iterates depth ascending and returns the
    first satisfiable length, so the path is shortest — mirroring the explicit engine's BFS witness.

    All z3 use is contained here. Raises if the solver is unavailable (callers should check HAVE_SOLVER)."""
    if not HAVE_SOLVER:
        raise RuntimeError("symbolic backend unavailable: pip install z3-solver")
    z3 = _z3
    bad = set(bad_ids)
    if init_id in bad:                  # k = 0: the initial state already violates
        return []
    edges = list(edges)
    if not edges:                       # no transitions ⇒ nothing else reachable
        return None
    for k in range(1, max_depth + 1):
        s = z3.Solver()
        S = [z3.Int(f"s_{i}") for i in range(k + 1)]
        A = [z3.Int(f"a_{i}") for i in range(k)]
        s.add(S[0] == init_id)
        for i in range(k):
            # (S[i], A[i], S[i+1]) must be one of the extracted edges
            s.add(z3.Or([z3.And(S[i] == src, A[i] == act, S[i + 1] == dst) for (src, act, dst) in edges]))
        s.add(z3.Or([S[k] == b for b in bad]))      # a bad state at exactly depth k (shortest by ascent)
        if s.check() == z3.sat:
            m = s.model()
            return [m.eval(A[i], model_completion=True).as_long() for i in range(k)]
    return None
