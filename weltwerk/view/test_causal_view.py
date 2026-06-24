# SPDX-License-Identifier: AGPL-3.0-only
"""
test_causal_view.py — validity-not-outcome: the VIEW renders the real measured partition, nothing else.

It guarantees the debugger cannot lie about the four sets: the proven nesting holds, every chunk gets
exactly one colour, and the rendered counts equal the engine's. It does not assert any scenario looks a
particular way — only that the colouring is a faithful projection of committed measurements.

  1. nesting_holds        — changed ⊆ allocated ⊆ potential (∀ scenario)
  2. partition_is_total   — the four colour classes partition all N chunks (counts sum to N, no overlap)
  3. counts_match_engine  — panel counts == independently recomputed |sets|
  4. determinism          — same seed ⇒ identical classification

Run:  PYTHONHASHSEED=0 python3 test_causal_view.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scale"))

from causal_view import N, classify                                # noqa: E402
from cow_world import Edit, Rules, genesis                         # noqa: E402
from teleport import Topology, full_sim_traced, reconstruct        # noqa: E402

CS, SEED, H = 10, 0, 20
SCENARIOS = [
    ("ring local", Topology(N), Edit("cull_pred_chunk", chunk=5)),
    ("teleport", Topology(N, ((5, 40),)), Edit("cull_pred_chunk", chunk=5)),
    ("global", Topology(N), Edit("set_rule", rule_field="predation_enabled", rule_value=False)),
]


def check(name, ok, detail):
    return (name, ok, detail)


def _sets(snap, topo, rules, edit):
    line_a = full_sim_traced(snap, topo, rules, SEED, H)[0][H]
    cons = reconstruct(snap, topo, rules, SEED, edit, H, prune=False)
    pru = reconstruct(snap, topo, rules, SEED, edit, H, prune=True)
    changed = frozenset(c for c in line_a if line_a[c] != pru.line_b[c])
    return changed, pru.touched, cons.touched


def test_nesting_holds():
    snap, rules = genesis(N * CS, N, SEED), Rules()
    ok = True
    for _, topo, edit in SCENARIOS:
        changed, allocated, potential = _sets(snap, topo, rules, edit)
        ok = ok and (changed <= allocated <= potential)
    return check("nesting_holds", ok, f"changed ⊆ allocated ⊆ potential ∀ scenario: {ok}")


def test_partition_is_total():
    snap, rules = genesis(N * CS, N, SEED), Rules()
    ok = True
    for _, topo, edit in SCENARIOS:
        d = classify(snap, topo, rules, SEED, edit, H)
        cl = d["classes"]
        counts = {k: cl.count(k) for k in ("committed", "potential", "alloc", "actual")}
        ok = ok and (len(cl) == N) and (sum(counts.values()) == N)
    return check("partition_is_total", ok, f"4 classes partition all {N} chunks ∀ scenario: {ok}")


def test_counts_match_engine():
    snap, rules = genesis(N * CS, N, SEED), Rules()
    ok = True
    for _, topo, edit in SCENARIOS:
        changed, allocated, potential = _sets(snap, topo, rules, edit)
        d = classify(snap, topo, rules, SEED, edit, H)
        c = d["counts"]
        ok = ok and c["potential"] == len(potential) and c["allocated"] == len(allocated) \
            and c["actual"] == len(changed) and c["transmit"] == len(changed)
        # and the classes counts match the set differences
        cl = d["classes"]
        ok = ok and cl.count("actual") == len(changed) \
            and cl.count("alloc") == len(allocated) - len(changed) \
            and cl.count("potential") == len(potential) - len(allocated) \
            and cl.count("committed") == N - len(potential)
    return check("counts_match_engine", ok, f"panel counts == |sets| and class partition matches ∀: {ok}")


def test_determinism():
    snap, rules = genesis(N * CS, N, SEED), Rules()
    topo, edit = Topology(N, ((5, 40),)), Edit("cull_pred_chunk", chunk=5)
    a = classify(snap, topo, rules, SEED, edit, H)
    b = classify(snap, topo, rules, SEED, edit, H)
    return check("determinism", a == b, f"identical classification across runs: {a == b}")


def main():
    results = [
        test_nesting_holds(),
        test_partition_is_total(),
        test_counts_match_engine(),
        test_determinism(),
    ]
    print("test_causal_view — the VIEW renders the real measured partition (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Faithful iff {total}/{total}: the four colours are a true partition"
          f"\n  obeying changed ⊆ allocated ⊆ potential, and the rendered counts equal the engine's. The VIEW"
          f"\n  cannot merge what the proofs keep separate.")
    assert passed == total, f"{total - passed} check(s) failed — the VIEW is not faithful to the engine"


if __name__ == "__main__":
    main()
