# SPDX-License-Identifier: AGPL-3.0-only
"""
solver_adapter_b.py — Phase A.2 Approach B (CANDIDATE): apply_event re-encoded DIRECTLY into SMT constraints.

Approach A (`solver_adapter.py`) reasons over the *extracted* relation (enumerate transitions, hand them to
the solver). Approach B encodes the transition relation ITSELF as SMT constraints and lets z3 search the
bounded unrolling symbolically — the scaling path. z3 lives only here.

SCOPE (a faithful FRAGMENT, stated honestly):
  • alphabet: {destroy, repair} only (the default; capture/damage excluded).
  • per-entity state: `alive` (Bool), `disabled` (Bool). status ok = alive ∧ ¬disabled; destroyed = ¬alive.
    health and controller are NOT modeled, so only invariants over alive/disabled are supported.
  • this is BOUNDED MODEL CHECKING: it finds the shortest VIOLATION within depth K, or reports none-within-K.
    It does NOT prove unreachability (CLOSED) — that needs k-induction (deferred). `unsat-at-k ≠ unreachable`.

This is a SECOND expression of the kernel's semantics, so it is the canonical divergence risk. It is a
CANDIDATE until the differential test confirms it matches the explicit engine. `re-encoded ≠ verified`.

Transition semantics encoded per step (mirroring world_sim.apply_event over the fragment):
  destroy(t): alive[t]'=F, disabled[t]'=F; for e ∈ reach(t): disabled[e]' = disabled[e] ∨ (alive[e] ∧ ¬disabled[e]),
              alive[e]'=alive[e]; all others unchanged.
  repair(t):  ua = ∧_{u ∈ upstream(t)} alive[u];  if ua: alive[t]'=T, disabled[t]'=F;  else: t unchanged;
              all others unchanged.
"""
from __future__ import annotations

try:
    import z3 as _z3
    HAVE_SOLVER = True
    SOLVER_NAME = "z3"
except Exception:
    _z3 = None
    HAVE_SOLVER = False
    SOLVER_NAME = "none"


def shortest_violation(entities, reach, upstream, options, bad_spec, max_depth):
    """Direct-encoding BMC. Returns the shortest list of option-indices reaching a `bad_spec` state within
    `max_depth`, or None.

      entities : list[str]                          all nodes (state vars are per entity)
      reach    : {entity: set(downstream entities)} static reach_ge1
      upstream : {entity: set(upstream entities)}   static {u : entity ∈ reach(u)}
      options  : list[(kind, target)]               the alphabet, kind ∈ {"destroy","repair"}
      bad_spec : ("not_disabled", X) | ("not_destroyed", X)   the invariant being sought-violated
    """
    if not HAVE_SOLVER:
        raise RuntimeError("approach-B symbolic backend unavailable: pip install z3-solver")
    z3 = _z3
    ents = list(entities)
    A = len(options)
    bad_kind, bad_entity = bad_spec

    def alive(e, i):
        return z3.Bool(f"alive_{e}_{i}")

    def dis(e, i):
        return z3.Bool(f"dis_{e}_{i}")

    def bad_at(i):
        return dis(bad_entity, i) if bad_kind == "not_disabled" else z3.Not(alive(bad_entity, i))

    def step_constraints(i):
        """Constraints linking state i → state i+1 under the symbolic action act_i."""
        act = z3.Int(f"act_{i}")
        cons = [act >= 0, act < A]
        for j, (kind, t) in enumerate(options):
            eff = []
            if kind == "destroy":
                eff.append(alive(t, i + 1) == z3.BoolVal(False))
                eff.append(dis(t, i + 1) == z3.BoolVal(False))
                affected = {t} | set(reach.get(t, ()))
                for e in reach.get(t, ()):
                    eff.append(alive(e, i + 1) == alive(e, i))
                    eff.append(dis(e, i + 1) == z3.Or(dis(e, i), z3.And(alive(e, i), z3.Not(dis(e, i)))))
            else:  # repair
                ua = z3.And([alive(u, i) for u in upstream.get(t, ())]) if upstream.get(t) else z3.BoolVal(True)
                eff.append(alive(t, i + 1) == z3.If(ua, z3.BoolVal(True), alive(t, i)))
                eff.append(dis(t, i + 1) == z3.If(ua, z3.BoolVal(False), dis(t, i)))
                affected = {t}
            for e in ents:                                   # frame: everything else is unchanged
                if e not in affected:
                    eff.append(alive(e, i + 1) == alive(e, i))
                    eff.append(dis(e, i + 1) == dis(e, i))
            cons.append(z3.Implies(act == j, z3.And(eff)))
        return act, cons

    # k = 0: is the initial state already bad? (init: all alive, none disabled ⇒ normally not)
    init = []
    for e in ents:
        init.append(alive(e, 0) == z3.BoolVal(True))
        init.append(dis(e, 0) == z3.BoolVal(False))
    s0 = z3.Solver(); s0.add(init); s0.add(bad_at(0))
    if s0.check() == z3.sat:
        return []

    acts = []
    for k in range(1, max_depth + 1):
        s = z3.Solver()
        s.add(init)
        acts = []
        for i in range(k):
            a, cons = step_constraints(i)
            acts.append(a)
            s.add(cons)
        s.add(bad_at(k))                                     # bad at exactly depth k ⇒ shortest by ascent
        if s.check() == z3.sat:
            m = s.model()
            return [m.eval(acts[i], model_completion=True).as_long() for i in range(k)]
    return None
