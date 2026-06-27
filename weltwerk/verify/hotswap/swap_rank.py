# SPDX-License-Identifier: AGPL-3.0-only
"""
swap_rank.py — PO-12: hot-swapping as a candidate-ranking SEARCH-ACCELERATION policy under the frozen verifier.

A "swap plan" is a set of guards (transition restrictions). A plan SUCCEEDS iff the FROZEN checker says the
swap world is CLOSED (no stream violation reachable) AND a migrated state is reachable (the swap completes).
Success is the engine's verdict + the migrated goal — NEVER the policy's say-so. `candidate ≠ deployed-swap`;
no policy can declare a swap done; only CLOSED ∧ goal does. This forecloses a "false restore".

The policy only ORDERS which plans to try. It cannot change the invariants, the grading, or the goal —
`improved_map ≠ changed_criterion`. We measure verified work `w(π, W)` = number of frozen re-verifications a
policy performs until it finds a successful plan (the rsi_bench `work()` pattern). Two policies:

  • canonical  — uninformed: plans by (size, lexicographic).
  • learned    — ranks plans by how many guards each contains that the frozen evaluator shows REMOVE a
                 reachable violation (a "useful" guard), smallest plan first.

Expected, and stated honestly: the safe plan needs BOTH real guards (make-before-break fixes starvation;
align-first fixes the race) — an overdetermined target — so a single useful guard never suffices. The learned
ordering reaches success at far less work, at EQUAL budget (the PO-6 separation: gain is ordering, not compute).
The signal is one-shot (rank by usefulness) ⇒ bounded gain, not open-ended. `more-budget ≠ better-policy`.
"""
from __future__ import annotations

import os
import sys
from collections import deque
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from artifacts import AnalysisResult, Finding, Limitation          # noqa: E402  (honesty contract, reused)
from swap_relation import (GUARDS, INIT, INV_NAMES, SWAP_INVARIANTS, successors,   # noqa: E402
                           SwapModelChecker, swap_oracle, swap_check_certificate)

BOUND = 8
_CHK = SwapModelChecker()


# ---- the frozen success criterion (engine verdict + migrated goal; never the policy's claim) ------
def success(plan, bound: int = BOUND) -> bool:
    v = _CHK.run(plan, bound)
    return v.status == "CLOSED" and v.goal_reachable


def candidate_plans():
    plans = []
    for k in range(len(GUARDS) + 1):
        for combo in combinations(GUARDS, k):
            plans.append(frozenset(combo))
    return plans


# ---- features measured by the FROZEN evaluator (like restorer_set: measured, not invented) --------
def violated_set(plan) -> set:
    R = swap_oracle(plan)["reachable"]
    return {name for v in R for name in INV_NAMES if not SWAP_INVARIANTS[name].predicate(v)}


def useful_guards() -> set:
    """A guard is useful iff adding it to the empty plan removes at least one reachable violation type."""
    base = violated_set(frozenset())
    return {g for g in GUARDS if base - violated_set(frozenset({g}))}


def downtime(plan):
    """Migration downtime proxy: BFS depth to the first migrated state (None if unreachable)."""
    plan = frozenset(plan)
    seen = {INIT}
    q = deque([(INIT, 0)])
    while q:
        v, d = q.popleft()
        if v[1]:
            return d
        for _a, nv in successors(plan, v):
            if nv not in seen:
                seen.add(nv)
                q.append((nv, d + 1))
    return None


# ---- policies (orderings of candidate plans) ----------------------------------------------------
def order_canonical(plans):
    return sorted(plans, key=lambda p: (len(p), tuple(sorted(p))))


def order_learned(plans, useful):
    # most useful-guards first, then smallest, then lexicographic — concentrates the safe plan at the top
    return sorted(plans, key=lambda p: (-sum(g in useful for g in p), len(p), tuple(sorted(p))))


def work(order) -> int:
    """Verified work: number of frozen re-verifications until the first successful plan in `order`."""
    for i, plan in enumerate(order, 1):
        if success(plan):
            return i
    return len(order) + 1


def equal_budget() -> dict:
    plans = candidate_plans()
    useful = useful_guards()
    o_can = order_canonical(plans)
    o_lrn = order_learned(plans, useful)
    w_can, w_lrn = work(o_can), work(o_lrn)
    bmax = len(plans)
    curve = [(B, int(w_lrn <= B), int(w_can <= B)) for B in range(1, bmax + 1)]
    return {
        "useful": sorted(useful), "work_canonical": w_can, "work_learned": w_lrn,
        "anytime_dominance": all(l >= c for _B, l, c in curve),
        "strict_gain": any(l > c for _B, l, c in curve),
        "minimal_success": next((sorted(p) for p in order_learned(plans, useful) if success(p)), None),
        "curve": curve,
    }


# ---- the honesty-contract projection (scope + ≥1 limitation; PO-9 universal) ----------------------
def as_analysis(plan) -> AnalysisResult:
    v = _CHK.run(plan, BOUND)
    ok = v.status == "CLOSED" and v.goal_reachable
    cert_ok = swap_check_certificate(plan, v.certificate) if v.certificate is not None else False
    findings = (
        Finding("SWAP_PLAN", "bounded-swap",
                f"guards={sorted(plan)} status={v.status} goal={v.goal_reachable} success={ok}"),
        Finding("DOWNTIME", "bounded-swap", f"steps_to_migrated={downtime(plan)}"),
        Finding("CERTIFICATE", "bounded-swap", f"inductive_check={cert_ok} (PO-8 closure over swap states)"),
    )
    limitations = (
        Limitation("bounded-swap", "CLOSED is over the swap alphabet + bound; deeper deferred races are "
                                   "UNDERDETERMINED — CLOSED@K ≠ globally-safe"),
        Limitation("model", "stream discretized to {intact,broken}; offsets abstracted (Arbitrary-Boundary "
                            "Law) — holds-here ≠ true"),
        Limitation("swap", "a plan OBSERVED safe under (checker, bound); candidate ≠ deployed-swap"),
    )
    return AnalysisResult(source_trace=tuple(sorted(plan)), scope="bounded-swap",
                          findings=findings, limitations=limitations)


def main():
    print("swap_rank.py — PO-12: swap planning as candidate ranking (search-accel under the frozen verifier)\n")
    r = equal_budget()
    print(f"  useful guards (measured by the frozen evaluator): {r['useful']}")
    print(f"  minimal successful plan: {r['minimal_success']}")
    print(f"  verified work: learned={r['work_learned']}  vs  canonical={r['work_canonical']}")
    print(f"  anytime dominance (learned ≥ canonical ∀ budget): {r['anytime_dominance']}  "
          f"strict_gain={r['strict_gain']}")
    print("\n  the policy only reorders WHICH plans to try; CLOSED ∧ migrated decides success.")
    print("  gain is ordering, not compute. improved_map ≠ changed_criterion; candidate ≠ deployed-swap.")


if __name__ == "__main__":
    main()
