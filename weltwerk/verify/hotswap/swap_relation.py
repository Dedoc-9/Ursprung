# SPDX-License-Identifier: AGPL-3.0-only
"""
swap_relation.py — PO-11: the hot-swap domain (a NEW world behind the FROZEN verification contracts).

This models live "hot-swapping" of a running target (Program Alpha → Program Beta) while a data stream must
stay uncorrupted. It does NOT modify the engine, the grading (CLOSED/BOUNDED/VIOLATED), the certificate
checker, the oracle pattern, or the honesty contract — it AUTHORS a world those frozen mechanisms judge.
`engine ≠ semantics`: we add semantics, not authority.

WHY A DEDICATED RELATION (a recorded fork). The existing `{destroy, repair}` WorldSim cascade is "any upstream
death disables downstream", which cannot express *make-before-break* stream continuity or buffered gaps. So
the swap is its own small transition system. It reuses every ARTIFACT and CONTRACT unchanged: `Invariant`,
`Trace`, `ReachabilityCertificate` (and the PO-8 closure check), and is proven faithful by an independent
unbounded-fixpoint oracle (the PO-4 pattern). `re-encoded ≠ verified` until the oracle agrees.

STATE (finite by construction — the Arbitrary-Boundary Law made explicit). Absolute stream offsets are
unbounded ⇒ would be infinite ⇒ no CLOSED. So continuity is *latched* to a boolean computed per transition;
the stream is discretized to {intact, broken}. A SwapView is the 5-tuple:

    (active, migrated, aligned, buffer, broken)
      active   ∈ {"alpha","beta","both","none"}   who is currently serving the stream
      migrated : bool                              the swap completed (beta committed)
      aligned  : bool                              the migration pointer is aligned
      buffer   : 0..BMAX                            queued items that cover a producer gap
      broken   : bool                              LATCHED: a starvation (gap) has occurred

The view IS the signature (bijective) — so a certificate's state set is directly re-checkable. `holds-here ≠ true`.

THE TWO FROZEN INVARIANTS (pure functions of the view; passing = consistent-with-invariants, never truth):
    continuity  := ¬broken                          no skip/starve has ever occurred
    no_race     := ¬(active=="both" ∧ ¬aligned)     two writers without an aligned pointer = corruption
`integrity ≠ truth`; the engine evaluates `.predicate` only.

A "plan" is a set of GUARDS (transition restrictions) — the candidate-ranking surface in swap_rank.py. The
plan cannot touch the invariants or the grading; it only forbids transitions. `improved_map ≠ changed_criterion`.
"""
from __future__ import annotations

import os
import sys
from collections import deque
from dataclasses import dataclass
from typing import FrozenSet, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from artifacts import Invariant, Trace, ReachabilityCertificate   # noqa: E402  (reused unchanged)

# ---- domain constants ---------------------------------------------------------------------------
BMAX = 2
B0 = 2                                   # initial buffer (sets the deferred-race depth: starve at B0+2)
ACTIONS = ("ALIGN", "ACT_BETA", "STOP_ALPHA", "TICK", "COMMIT", "BUF_FILL")
GUARDS = ("MBB", "ALIGN", "DECOY_A", "DECOY_B")
INIT = ("alpha", False, False, B0, False)        # alpha serving; beta down; pointer unaligned; buffer primed
INV_NAMES = ("continuity", "no_race")


# ---- transition function (one SwapView → one SwapView under an action) ---------------------------
def step(v, a) -> tuple:
    active, migr, al, buf, brk = v
    if a == "ALIGN":
        al = True
    elif a == "ACT_BETA":
        active = "both" if active == "alpha" else ("beta" if active == "none" else active)
    elif a == "STOP_ALPHA":
        active = "beta" if active == "both" else ("none" if active == "alpha" else active)
    elif a == "TICK":                                  # environment pulls one item from the stream
        if active == "none":
            if buf > 0:
                buf -= 1                                # buffer covers the gap
            else:
                brk = True                              # starvation — LATCHED (irreversible discontinuity)
        # active != none ⇒ served by a live program, no state change
    elif a == "COMMIT":
        if active == "beta" and al:
            migr = True
    elif a == "BUF_FILL":
        buf = min(BMAX, buf + 1)
    return (active, migr, al, buf, brk)


# ---- guards (transition restrictions; a plan is a frozenset of these) ----------------------------
def _forbidden(guard: str, a: str, v) -> bool:
    active, migr, al, buf, brk = v
    if guard == "MBB":       return a == "STOP_ALPHA" and active == "alpha"   # make-before-break
    if guard == "ALIGN":     return a == "ACT_BETA" and not al                # align before any dual-writer
    if guard == "DECOY_A":   return a == "COMMIT" and buf < BMAX             # useless (does not fix a failure)
    if guard == "DECOY_B":   return a == "ALIGN" and active == "beta"        # useless
    return False


def successors(plan: FrozenSet[str], v) -> list:
    out = []
    for a in ACTIONS:
        if any(_forbidden(g, a, v) for g in plan):
            continue
        out.append((a, step(v, a)))
    return out


# ---- the two frozen invariants ------------------------------------------------------------------
def _continuity(v) -> bool:
    return not v[4]


def _no_race(v) -> bool:
    return not (v[0] == "both" and not v[2])


SWAP_INVARIANTS = {
    "continuity": Invariant("continuity", _continuity, "the stream is never starved (latched on first gap)", "critical"),
    "no_race":    Invariant("no_race", _no_race, "no dual-writer state without an aligned migration pointer", "critical"),
}


def _first_bad(v) -> Optional[str]:
    for name in INV_NAMES:
        if not SWAP_INVARIANTS[name].predicate(v):
            return name
    return None


# ---- the bounded checker (reuses the explicit engine's grading + artifacts, swap-native Trace) ---
@dataclass(frozen=True)
class SwapVerdict:
    status: str                         # CLOSED | BOUNDED | VIOLATED
    reachable: FrozenSet
    goal_reachable: bool                # a migrated state is reachable (success needs CLOSED ∧ this)
    witness: Optional[Tuple]            # action sequence to the first violation (VIOLATED only)
    violated_inv: Optional[str]
    depth: int
    trace: Optional[Trace]
    certificate: Optional[ReachabilityCertificate]


class SwapModelChecker:
    """Breadth-first explicit-state search over the swap relation — the same grading as the frozen engine
    (CLOSED = frontier emptied with invariants holding; BOUNDED = bound truncated; VIOLATED = a reachable
    bad state with a replayable witness). Faithfulness vs an independent oracle is asserted in the tests."""
    name = "swap-explicit-bfs"

    def run(self, plan, bound: int = 8) -> SwapVerdict:
        plan = frozenset(plan)
        init = INIT
        seen = {init}
        parent = {init: None}
        goal = bool(init[1])
        q = deque([(init, 0)])
        truncated = False
        trans = 0

        def path_to(sig):
            acts, sigs = [], [sig]
            while parent[sig] is not None:
                psig, a = parent[sig]
                acts.append(a)
                sigs.append(psig)
                sig = psig
            return tuple(reversed(acts)), tuple(reversed(sigs))

        bad = _first_bad(init)
        if bad:
            return SwapVerdict("VIOLATED", frozenset(seen), goal, (), bad, 0,
                               Trace((), (init,), 1, init), None)

        while q:
            v, d = q.popleft()
            if d >= bound:
                for _a, nv in successors(plan, v):
                    if nv not in seen:
                        truncated = True
                        break
                continue
            for a, nv in successors(plan, v):
                trans += 1
                if nv not in seen:
                    seen.add(nv)
                    parent[nv] = (v, a)
                    if nv[1]:
                        goal = True
                    bad = _first_bad(nv)
                    if bad:
                        acts, sigs = path_to(nv)
                        tr = Trace(acts, sigs, len(sigs), sigs[-1])
                        return SwapVerdict("VIOLATED", frozenset(seen), goal, acts, bad, len(acts), tr, None)
                    q.append((nv, d + 1))

        status = "BOUNDED" if truncated else "CLOSED"
        cert = None
        if status == "CLOSED":
            cert = ReachabilityCertificate(explored_state_sigs=frozenset(seen), transition_count=trans,
                                           invariant_names=tuple(sorted(INV_NAMES)), status="CLOSED")
        return SwapVerdict(status, frozenset(seen), goal, None, None, 0, None, cert)


# ---- independent ground-truth oracle (PO-4 pattern: unbounded fixpoint + separate shortest-path BFS) ---
def swap_oracle(plan) -> dict:
    plan = frozenset(plan)
    R = {INIT}
    stack = [INIT]
    while stack:                                    # full reachable set by fixpoint (no depth bound)
        v = stack.pop()
        for _a, nv in successors(plan, v):
            if nv not in R:
                R.add(nv)
                stack.append(nv)
    any_bad = any(_first_bad(v) for v in R)
    goal = any(v[1] for v in R)
    shortest = None
    if any_bad:                                     # shortest violation depth by an independent layered BFS
        seen = {INIT}
        q = deque([(INIT, 0)])
        if _first_bad(INIT):
            shortest = 0
        while q and shortest is None:
            v, d = q.popleft()
            for _a, nv in successors(plan, v):
                if nv not in seen:
                    seen.add(nv)
                    if _first_bad(nv):
                        shortest = d + 1
                        q.clear()
                        break
                    q.append((nv, d + 1))
    return {"status": "VIOLATED" if any_bad else "CLOSED", "reachable": frozenset(R),
            "goal": goal, "shortest": shortest, "count": len(R)}


# ---- independent certificate checker (PO-8 closure logic, swap-native) ----------------------------
def swap_check_certificate(plan, cert: ReachabilityCertificate) -> bool:
    """No-search inductive check: init ∈ S, invariants hold on every s∈S, and S is closed under the swap T.
    Then reachable ⊆ S ⇒ the CLOSED swap genuinely preserves the stream over the alphabet. Mirrors PO-8."""
    if cert is None or cert.status != "CLOSED":
        return False
    S = cert.explored_state_sigs
    if INIT not in S:
        return False
    plan = frozenset(plan)
    for v in S:
        if _first_bad(v):
            return False
        for _a, nv in successors(plan, v):
            if nv not in S:
                return False
    return True


def replay(plan, witness) -> tuple:
    """Replay an action sequence from INIT (guards enforced). Used to confirm a witness is real."""
    plan = frozenset(plan)
    v = INIT
    for a in witness:
        if any(_forbidden(g, a, v) for g in plan):
            continue
        v = step(v, a)
    return v


def main():
    print("swap_relation.py — PO-11: the hot-swap domain (frozen contracts judge it)\n")
    chk = SwapModelChecker()
    for label, plan in [("unconstrained", set()), ("MBB only", {"MBB"}),
                        ("ALIGN only", {"ALIGN"}), ("MBB+ALIGN (safe)", {"MBB", "ALIGN"})]:
        v = chk.run(plan, bound=8)
        o = swap_oracle(plan)
        extra = f" inv={v.violated_inv}@{v.depth}" if v.status == "VIOLATED" else f" goal={v.goal_reachable}"
        print(f"  {label:18s} checker={v.status:8s}{extra:18s} oracle={o['status']:8s} shortest={o['shortest']}")
    print("\n  unconstrained/MBB-only/ALIGN-only all VIOLATED (race or starvation); only MBB+ALIGN is CLOSED")
    print("  with the migration reachable. Two failure modes ⇒ both guards needed. candidate ≠ deployed-swap.")


if __name__ == "__main__":
    main()
