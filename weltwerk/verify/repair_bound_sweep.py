# SPDX-License-Identifier: AGPL-3.0-only
"""
repair_bound_sweep.py — Proof Obligation PO-3: is a bounded "restored" claim stable when you look deeper?

A RepairCandidate's `restores_world` is one of two epistemic grades (see repair.py):
  • RESTORED_PROVEN        — forbidding the action made the model checker CLOSE at bound K (frontier emptied;
                             exhaustive over the *restricted* alphabet).
  • RESTORED_WITHIN_BOUND  — forbidding the action found no ghost UP TO bound K, but the frontier was not
                             exhausted (deeper is UNDERDETERMINED).

This sweep re-verifies every restored candidate at **2K** and asks whether the grade survives. It is the
executable form of the question PO-3 poses, and it is built to be able to FAIL — a candidate that is
restored@K but VIOLATED@2K is the *valuable* negative `restores-(M,E,K) ≠ world-safe`.

TWO SCENARIOS, by construction:
  1. star/proven — a tiny world; forbidding the cause CLOSES (RESTORED_PROVEN). Deepening cannot introduce a
     state an exhaustive search already ruled out, so this MUST remain restored at 2K. This is the deductive
     guarantee: `CLOSED is bound-monotone`. The sweep checks the guarantee empirically.
  2. fanout/flip — a hub fans out to four leaves; the invariant is "fewer than 3 entities disabled".
     Forbidding `destroy hub` removes the depth-1 violation, and at K=2 only ≤2 leaves can be destroyed, so
     it reads RESTORED_WITHIN_BOUND. But at 2K=4 the sequence `destroy a; destroy b; destroy c` reaches 3
     disabled — a violation strictly DEEPER than K. The bounded "restored" claim FLIPS to VIOLATED.

So the sweep simultaneously demonstrates: PROVEN is safe to deepen; WITHIN_BOUND is NOT. `bounded ≠ proven`.
The grade is not cosmetic; it is exactly the line between a claim that survives more compute and one that may not.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
import repair                                          # noqa: E402
from kernel_check import check                         # noqa: E402
from engine import ExplicitStateBFSEngine             # noqa: E402

ENGINE = ExplicitStateBFSEngine()

# ---- worlds -------------------------------------------------------------------------------------
SMALL = ('world "Smin"\n'
         'entity fac:\n  position 0 0 0\n  controls hub\n'
         'entity hub:\n  position 1 0 0\n  health 10\n  powers tail\n'
         'entity tail:\n  position 2 0 0\n  health 10\n')

# hub fans out to four independent leaves; destroying hub disables all four (cascade), but destroying a leaf
# disables only itself — so the count invariant is reachable only by accumulating destroys over depth.
CAP = ('world "Cap"\n'
       'entity fac:\n  position 0 0 0\n  controls hub\n'
       'entity hub:\n  position 1 0 0\n  health 10\n  powers a\n  powers b\n  powers c\n  powers d\n'
       'entity a:\n  position 2 0 0\n  health 10\n'
       'entity b:\n  position 2 1 0\n  health 10\n'
       'entity c:\n  position 2 2 0\n  health 10\n'
       'entity d:\n  position 2 3 0\n  health 10\n')

TAIL_OK = {"tail_ok": (lambda s: s.runtime["tail"]["status"] != "disabled")}


def _n_disabled(s) -> int:
    return sum(1 for e in s.runtime if (not s.runtime[e]["alive"]) or s.runtime[e]["status"] == "disabled")


COUNT_OK = {"few_disabled": (lambda s: _n_disabled(s) < 3)}

# (label, world, invariants, K) — K chosen so star CLOSES (PROVEN) and fanout truncates (WITHIN_BOUND@2)
SUITE = [
    ("star/proven", SMALL, TAIL_OK, 6),
    ("fanout/flip", CAP, COUNT_OK, 2),
]


def sweep():
    """For each scenario: derive candidates at bound K, then RE-VERIFY each at 2K. Records the grade@K and
    whether the restored claim survives at 2K. The whole point is that a WITHIN_BOUND claim is allowed to die."""
    records = []
    for label, world, inv, K in SUITE:
        g = check(world, max_depth=K, invariants=inv).ghost
        if g is None:
            continue
        for c in repair.propose(world, g.path, inv, check_world=True, bound=K):
            grade_k = c.restores_world                     # RESTORED_PROVEN / RESTORED_WITHIN_BOUND / ...
            if grade_k not in ("RESTORED_PROVEN", "RESTORED_WITHIN_BOUND"):
                continue                                   # not a restored candidate; nothing to deepen
            ev2 = repair._forbid_and_verify(world, c.change.target, inv, ENGINE, 2 * K)
            records.append({
                "label": label, "target": c.change.target, "K": K,
                "grade_K": grade_k, "status_K": c.world_evidence.status,
                "status_2K": ev2.status, "restored_2K": ev2.status != "VIOLATED",
            })
    proven = [r for r in records if r["grade_K"] == "RESTORED_PROVEN"]
    within = [r for r in records if r["grade_K"] == "RESTORED_WITHIN_BOUND"]
    return {
        "records": records,
        "proven": proven,
        "within": within,
        "proven_stable": all(r["restored_2K"] for r in proven),
        "within_flips": [r for r in within if not r["restored_2K"]],
    }


def main():
    print("repair_bound_sweep.py — PO-3: does a bounded 'restored' claim survive at 2K?\n")
    s = sweep()
    for r in s["records"]:
        flip = "" if r["restored_2K"] else "   ← FLIP (restored@K, VIOLATED@2K)"
        print(f"  {r['label']:13s} forbid {str(r['target']):20s} grade@{r['K']}={r['grade_K']:21s} "
              f"@2K={r['status_2K']:8s} restored_2K={r['restored_2K']}{flip}")
    print(f"\n  RESTORED_PROVEN stable at 2K: {s['proven_stable']}  (CLOSED is bound-monotone — a guarantee)")
    print(f"  RESTORED_WITHIN_BOUND flips:  {len(s['within_flips'])} of {len(s['within'])}  "
          f"(bounded ≠ proven — a measured limit, not a bug)")
    print("\n  The two grades are not cosmetic: PROVEN survives more compute; WITHIN_BOUND may not.")
    print("  restores-(M,E,K) ≠ world-safe.")


if __name__ == "__main__":
    main()
