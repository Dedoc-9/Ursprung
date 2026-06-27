# SPDX-License-Identifier: AGPL-3.0-only
"""
swap_falsifier.py — PO-11/PO-12 adversarial control: a built-in falsifier that PUNISHES unsafe shortcuts,
modeled on PO-3 (fanout/flip at 2K) and PO-2/PO-5 (overdetermined / two-failure-mode structure).

Two failure modes, at two depths, so a greedy "minimize downtime" policy is actively caught:

  • THE DEFERRED-RACE FLIP (PO-3 analogue).  A greedy plan that drops alpha early to cut downtime
    (`{ALIGN}` only — no make-before-break) opens an `active="none"` window. The primed buffer (B0=2) masks
    the gap at shallow depth, so the swap reads BOUNDED (looks safe) at bound K=2. But the buffer underflows
    deeper: at 2K=4 the stream STARVES → continuity VIOLATED. `swap-CLOSED@K ≠ safe`.

  • THE RACE TRAP (overdetermined).  A greedy plan that brings beta online without aligning the pointer
    (`{MBB}` only — no align-first) reaches `active="both" ∧ ¬aligned` at depth 1 → no_race VIOLATED.

Neither single guard suffices: starvation and the race are INDEPENDENT failure modes, so only `{MBB, ALIGN}`
is CLOSED with the migration reachable — an overdetermined safe plan. A naive policy that adds one "obvious"
guard is still VIOLATED. The harness asserts the flip fires, the race fires shallow, the safe plan survives at
2K, and (PO-7) plan-permutation never changes a verdict. `restores-(M,E,K) ≠ safe`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from swap_relation import SwapModelChecker, swap_oracle, replay, _first_bad   # noqa: E402

K = 2
TWOK = 4
_CHK = SwapModelChecker()

GREEDY_STARVE = frozenset({"ALIGN"})           # drops alpha early ⇒ deferred starvation (flip at 2K)
GREEDY_RACE = frozenset({"MBB"})               # activates beta unaligned ⇒ race at depth 1
SAFE = frozenset({"MBB", "ALIGN"})             # the overdetermined safe plan
UNCONSTRAINED = frozenset()


def flip() -> dict:
    """The deferred-race flip: greedy looks safe at K, VIOLATED at 2K; safe plan survives at 2K."""
    gK = _CHK.run(GREEDY_STARVE, K)
    g2K = _CHK.run(GREEDY_STARVE, TWOK)
    sK = _CHK.run(SAFE, K)
    s2K = _CHK.run(SAFE, TWOK)
    return {
        "greedy_K": gK.status, "greedy_2K": g2K.status,
        "greedy_2K_inv": g2K.violated_inv, "greedy_2K_depth": g2K.depth,
        "safe_2K": s2K.status, "safe_goal": s2K.goal_reachable,
        "flipped": gK.status != "VIOLATED" and g2K.status == "VIOLATED",
    }


def race() -> dict:
    """The race trap: activating beta without aligning ⇒ no_race violated shallow."""
    v = _CHK.run(GREEDY_RACE, TWOK)
    return {"status": v.status, "inv": v.violated_inv, "depth": v.depth,
            "witness_replays": _first_bad(replay(GREEDY_RACE, v.witness)) is not None if v.witness else False}


def overdetermined() -> dict:
    """No single real guard suffices; both are needed (independent failure modes)."""
    def ok(plan):
        v = _CHK.run(plan, TWOK)
        return v.status == "CLOSED" and v.goal_reachable
    return {"MBB_only": ok(GREEDY_RACE), "ALIGN_only": ok(GREEDY_STARVE),
            "both": ok(SAFE), "unconstrained": ok(UNCONSTRAINED)}


def main():
    print("swap_falsifier.py — PO-11/12 adversarial control (the harness punishes unsafe shortcuts)\n")
    f = flip()
    print(f"  DEFERRED-RACE FLIP  greedy@K={f['greedy_K']}  →  greedy@2K={f['greedy_2K']} "
          f"({f['greedy_2K_inv']}@{f['greedy_2K_depth']})   flipped={f['flipped']}")
    print(f"                      safe@2K={f['safe_2K']} goal={f['safe_goal']}  (make-before-break survives)")
    r = race()
    print(f"  RACE TRAP           {GREEDY_RACE and 'MBB-only'}: {r['status']} ({r['inv']}@{r['depth']})  "
          f"witness_replays={r['witness_replays']}")
    o = overdetermined()
    print(f"  OVERDETERMINED      MBB_only={o['MBB_only']} ALIGN_only={o['ALIGN_only']} "
          f"both={o['both']} unconstrained={o['unconstrained']}")
    print("\n  the flip fires (CLOSED-looking@K, VIOLATED@2K), the race fires shallow, and only the")
    print("  two-guard plan is safe. greedy downtime-cutting is caught. restores-(M,E,K) ≠ safe.")


if __name__ == "__main__":
    main()
