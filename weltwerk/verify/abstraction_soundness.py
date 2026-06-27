# SPDX-License-Identifier: AGPL-3.0-only
"""
abstraction_soundness.py — Proof Obligation PO-10: a reusable harness for the one property every abstraction
must satisfy — **`abstract-CLOSED ⇒ exact-CLOSED`** (no false CLOSED).

An abstraction trades exactness for scale by collapsing concrete states into blocks and reasoning over the
quotient. The only thing that makes that safe for *safety* properties is that the abstract system
**over-approximates** the concrete one: every concrete reachable state has an abstract image, and every
concrete bad state is marked bad abstractly. When that holds, an abstract proof of `CLOSED` (no abstract-
reachable abstract-bad state) entails the exact `CLOSED`. When it does **not** hold, the abstraction can report
`CLOSED` while a concrete violation exists — a **false CLOSED**, the single failure mode that would let an
optimization silently launder unsoundness into the verdict. `over-approx ≠ exact`; `abstract-CLOSED ⇒ exact-CLOSED`
is a *theorem only under admissibility*, never by default.

This module provides the harness, not a particular abstraction:

  • `build_concrete(world, invariants, observe, bound)` — the exact reachable graph (states, edges, bad set)
    from the real `TransitionRelation` (pure-stdlib BFS; no solver), plus a per-state coarse observation used
    to define abstractions.
  • `lift(graph, alpha)` — the canonical SOUND abstraction: the existential image of the concrete graph under
    a partition `alpha` (a *quotient* is always an over-approximation).
  • `admissible(graph, alpha, abstract)` — checks a CANDIDATE abstract system over-approximates the lift
    (init/edges/bad each ⊇ the existential image). This is the checkable premise of the theorem.
  • `no_false_closed(graph, abstract)` — the conclusion, checked directly: it is never the case that the
    abstract verdict is `CLOSED` while the exact verdict is `VIOLATED`.

The guarantee the harness mechanizes: **admissible ⇒ no_false_closed.** Its falsifier is exactly a false
CLOSED — and the test deliberately builds an *inadmissible* abstraction (one that drops a bad block, as a
buggy/over-eager optimization would) to show the harness catches it. `gates: CEGAR / Approach-B CLOSED`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from transition import TransitionRelation               # noqa: E402
from artifacts import normalize_invariants              # noqa: E402


# ---- exact reachable graph (the ground truth the abstraction must over-approximate) --------------
def build_concrete(world: str, invariants, observe, bound: int = 6) -> dict:
    """Exact reachable graph via the real relation. `observe(sim)->hashable` defines the coarse attribute
    abstractions partition on. Returns init/edges/bad/states/coarse and whether the frontier stayed open."""
    rel = TransitionRelation(world)
    inv = normalize_invariants(invariants)

    def info(state):
        sim = rel.materialize(state)                     # read immediately (shared base)
        bad = any(not inv[k].predicate(sim) for k in inv)
        return bad, observe(sim)

    s0 = rel.initial()
    b0, o0 = info(s0)
    states = {s0.sig: s0}
    depth = {s0.sig: 0}
    coarse = {s0.sig: o0}
    bad = {s0.sig} if b0 else set()
    edges = set()
    queue = [s0]
    qi = 0
    while qi < len(queue):
        s = queue[qi]
        qi += 1
        if depth[s.sig] >= bound:
            continue
        for tr in rel.successors(s):
            edges.add((s.sig, tr.target.sig))
            if tr.target.sig not in states:
                states[tr.target.sig] = tr.target
                depth[tr.target.sig] = depth[s.sig] + 1
                b, o = info(tr.target)
                coarse[tr.target.sig] = o
                if b:
                    bad.add(tr.target.sig)
                queue.append(tr.target)
    frontier_open = any(depth[x] >= bound for x in states)   # True ⇒ truncated, verdict is BOUNDED not exact
    return {"init": s0.sig, "edges": edges, "bad": bad, "states": set(states),
            "coarse": coarse, "frontier_open": frontier_open}


# ---- reachability + verdict (shared by concrete and abstract) -----------------------------------
def _reach(init_set, edges) -> set:
    adj = {}
    for u, v in edges:
        adj.setdefault(u, []).append(v)
    seen = set(init_set)
    stack = list(init_set)
    while stack:
        x = stack.pop()
        for y in adj.get(x, ()):
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return seen


def verdict(init_set, edges, bad) -> str:
    """CLOSED iff no reachable state is bad (exact only when the graph is closed — see frontier_open)."""
    return "VIOLATED" if (_reach(init_set, edges) & set(bad)) else "CLOSED"


def concrete_verdict(graph) -> str:
    return verdict({graph["init"]}, graph["edges"], graph["bad"])


def abstract_verdict(abstract) -> str:
    return verdict(abstract["init"], abstract["edges"], abstract["bad"])


# ---- abstraction (the quotient) -----------------------------------------------------------------
def alpha_from_observation(graph) -> dict:
    """A partition that maps each concrete state to its coarse observation block. Any function of `coarse`."""
    return {sig: graph["coarse"][sig] for sig in graph["states"]}


def lift(graph, alpha) -> dict:
    """The canonical SOUND abstraction: existential image of the concrete graph under `alpha`. A quotient is
    always an over-approximation, so `lift` is admissible by construction (test 1 verifies this)."""
    return {
        "init": {alpha[graph["init"]]},
        "edges": {(alpha[u], alpha[v]) for (u, v) in graph["edges"]},
        "bad": {alpha[s] for s in graph["bad"]},
    }


# ---- the harness: premise (admissible) and conclusion (no_false_closed) --------------------------
def admissible(graph, alpha, abstract) -> bool:
    """The checkable premise: the candidate abstract over-approximates the existential image on all three
    components. init/edges/bad of `abstract` must each ⊇ the lifted image. Missing any ⇒ inadmissible."""
    li = {alpha[graph["init"]]}
    le = {(alpha[u], alpha[v]) for (u, v) in graph["edges"]}
    lb = {alpha[s] for s in graph["bad"]}
    return li <= abstract["init"] and le <= abstract["edges"] and lb <= abstract["bad"]


def no_false_closed(graph, abstract):
    """The conclusion checked directly: never (abstract CLOSED ∧ exact VIOLATED). Returns (ok, exact, abstract)."""
    cv = concrete_verdict(graph)
    av = abstract_verdict(abstract)
    return (not (av == "CLOSED" and cv == "VIOLATED")), cv, av


# ---- worlds for the demonstrator ----------------------------------------------------------------
STAR = ('world "AS1"\n'
        'entity fac:\n  position 0 0 0\n  controls hub\n'
        'entity hub:\n  position 1 0 0\n  health 10\n  powers tail\n'
        'entity tail:\n  position 2 0 0\n  health 10\n')
ISO = ('world "AS2"\n'
       'entity fac:\n  position 0 0 0\n  controls a\n'
       'entity a:\n  position 1 0 0\n  health 10\n'
       'entity tail:\n  position 2 0 0\n  health 10\n')          # tail isolated ⇒ never disabled

TAIL_OK = {"tail_ok": (lambda s: s.runtime["tail"]["status"] != "disabled")}
OBSERVE = (lambda s: s.runtime["tail"]["status"] == "disabled")  # coarse: is tail disabled?


def main():
    print("abstraction_soundness.py — PO-10: a harness for `abstract-CLOSED ⇒ exact-CLOSED` (no false CLOSED)\n")
    for label, w in (("violable star", STAR), ("isolated tail", ISO)):
        g = build_concrete(w, TAIL_OK, OBSERVE)
        a = alpha_from_observation(g)
        sound = lift(g, a)
        ok_s, cv, av = no_false_closed(g, sound)
        print(f"  {label:14s} concrete={cv:8s} | sound-abstract: admissible={admissible(g, a, sound)} "
              f"verdict={av:8s} no_false_closed={ok_s}  ({len(g['states'])} states → {len(sound['init']|{x for e in sound['edges'] for x in e})} blocks)")
        if cv == "VIOLATED":                       # demonstrate the failure mode on a world that can fail
            unsound = {**sound, "bad": set()}      # a buggy abstraction that dropped the bad block
            ok_u, _cv, av_u = no_false_closed(g, unsound)
            print(f"  {'':14s} UNSOUND (bad dropped): admissible={admissible(g, a, unsound)} "
                  f"verdict={av_u} no_false_closed={ok_u}  ← harness catches the FALSE CLOSED")
    print("\n  admissible ⇒ no_false_closed (the theorem, mechanized). A non-over-approximating abstraction is")
    print("  flagged inadmissible AND would have reported a false CLOSED. over-approx ≠ exact.")


if __name__ == "__main__":
    main()
