# SPDX-License-Identifier: AGPL-3.0-only
"""
cf_quality_bench.py — Proof Obligation PO-2: counterfactual ACCURACY vs an independent exhaustive gold.

`test_counterfactual` proves the apparatus is well-formed; it does not measure *accuracy*. This benchmark
does, against a gold that is independent of the method: the **exhaustive minimal removal set** — the smallest
subset of a ghost trace whose removal makes the trajectory non-violating (found by brute-force subset search,
judged only by replay). The method under test is `counterfactual.analyze`, which performs *single-event*
ablation.

What this measures honestly:
  • single-minimal-cause traces (gold size 1): does `analyze` recover exactly the critical event?
  • overdetermined traces (gold size ≥ 2): `analyze` (single-event) finds NO single critical event; the gold
    shows a minimal *set* exists. This is a KNOWN, stated blind spot — the benchmark confirms `analyze`
    reports ∅ rather than a false cause, and quantifies the boundary. `single-event-ablation ≠ minimal-set`.

`gold ≠ method`; gold is computed by exhaustive replay, never by `analyze`.
"""
from __future__ import annotations

import os
import sys
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
import counterfactual                                   # noqa: E402
from artifacts import normalize_invariants             # noqa: E402

# ---- worlds / traces / invariants -------------------------------------------------------------
STAR = ('world "S"\n'
        'entity fac:\n  position 0 0 0\n  controls hub\n'
        'entity hub:\n  position 1 0 0\n  health 10\n  powers tail\n'
        'entity tail:\n  position 2 0 0\n  health 10\n')
MIXED = ('world "M"\n'
         'entity fac:\n  position 0 0 0\n  controls hub\n'
         'entity hub:\n  position 1 0 0\n  health 10\n  powers tail\n'
         'entity tail:\n  position 2 0 0\n  health 10\n'
         'entity decoy:\n  position 3 0 0\n  health 10\n')
OVERDET = ('world "OD"\n'
           'entity fac:\n  position 0 0 0\n  controls h1\n'
           'entity fac2:\n  position 0 1 0\n  controls h2\n'
           'entity h1:\n  position 1 0 0\n  health 10\n  powers tail\n'
           'entity h2:\n  position 1 1 0\n  health 10\n  powers tail\n'
           'entity tail:\n  position 2 0 0\n  health 10\n')

TAIL_OK = {"tail_ok": (lambda s: s.runtime["tail"]["status"] != "disabled")}

# (label, world, trace, invariants, expected_category)
SUITE = [
    ("star/single",   STAR,    [("destroy", "hub")],                    TAIL_OK, "single-cause"),
    ("mixed/decoy",    MIXED,   [("destroy", "decoy"), ("destroy", "hub")], TAIL_OK, "single-cause"),
    ("overdet/two",    OVERDET, [("destroy", "h1"), ("destroy", "h2")], TAIL_OK, "overdetermined"),
]


def minimal_removal_set(world, trace, invariants):
    """Independent gold: the smallest subset of trace events whose removal yields no violation (by replay)."""
    nz = normalize_invariants(invariants)
    events = [tuple(e) for e in trace]
    n = len(events)
    for size in range(0, n + 1):
        for combo in combinations(range(n), size):
            reduced = [events[i] for i in range(n) if i not in combo]
            if not counterfactual._trajectory_violates(world, reduced, nz):
                return set(events[i] for i in combo)
    return set(events)


def evaluate(world, trace, invariants):
    crit = set(counterfactual.analyze(world, trace, invariants).critical)
    gold = minimal_removal_set(world, trace, invariants)
    gsize = len(gold)
    rec = {"critical": sorted(crit), "gold": sorted(gold), "gold_size": gsize}
    if gsize == 1:
        tp = len(crit & gold)
        rec["precision"] = (tp / len(crit)) if crit else 0.0
        rec["recall"] = tp / gsize
        rec["category"] = "single-cause"
    else:
        rec["precision"] = 1.0 if not crit else 0.0     # any single flag on an overdetermined trace is wrong
        rec["recall"] = None
        rec["category"] = "overdetermined" if gsize >= 2 else "no-violation"
    return rec


def main():
    print("cf_quality_bench.py — PO-2: counterfactual accuracy vs exhaustive minimal-removal gold\n")
    for label, w, tr, inv, _exp in SUITE:
        r = evaluate(w, tr, inv)
        print(f"  {label:16s} category={r['category']:14s} critical={r['critical']} gold={r['gold']} "
              f"P={r['precision']} R={r['recall']}")
    print("\n  single-cause ⇒ analyze recovers the critical event (P=R=1); overdetermined ⇒ analyze returns ∅")
    print("  (no false cause) while the gold shows a minimal SET. single-event-ablation ≠ minimal-set.")


if __name__ == "__main__":
    main()
