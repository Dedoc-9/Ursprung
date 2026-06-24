# SPDX-License-Identifier: AGPL-3.0-only
"""
test_causal_scale_bench.py — Phase 10 proofs (validity-not-outcome): the envelope is measured correctly.

These assert the bench's INVARIANTS and DIRECTION, not a particular performance number.

  1. anchor_reach_authority   — the generated world's reach IS world_format's reach (no shadow graph)
  2. footprint_bounded        — avg_footprint ≤ N and headroom ∈ [0,1]
  3. causal_le_naive          — causal_ops ≤ naive_ops on every envelope row
  4. headroom_monotonic       — headroom is non-increasing as coupling rises (cheap iff Actual ≪ Potential)
  5. envelope_direction       — causal/naive is smaller at low coupling than at high coupling
  6. ai_work_linear           — AI work scales ~linearly in bot count (bots are independent)
  7. determinism              — same seed ⇒ identical envelope and identical AI scaling

Run:  PYTHONHASHSEED=0 python3 test_causal_scale_bench.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
from causal_scale_bench import (ai_scaling, ai_work, causal_envelope, gen_world_text, headroom_curve,
                                 measure_world)
from world_format import build_causal_graph, parse_world


def check(name, ok, detail):
    return (name, ok, detail)


def test_anchor_reach_authority():
    cg = build_causal_graph(parse_world(gen_world_text(4, 1.0)))   # e0→e1→e2→e3
    r = cg.reach_ge1("e0")
    return check("anchor_reach_authority", r == {"e1", "e2", "e3"},
                 f"reach(e0)={sorted(r)} (== world_format authority)")


def test_footprint_bounded():
    m = measure_world(1000, 0.6)
    ok = m["avg_footprint"] <= m["n"] and 0.0 <= m["headroom"] <= 1.0
    return check("footprint_bounded", ok, f"footprint={m['avg_footprint']} ≤ {m['n']}, headroom={m['headroom']}")


def test_causal_le_naive():
    ok = all(r["causal_ops"] <= r["naive_ops"] for r in causal_envelope())
    return check("causal_le_naive", ok, "causal_ops ≤ naive_ops on every row")


def test_headroom_monotonic():
    curve = headroom_curve()
    hs = [r["headroom"] for r in curve]
    ok = all(hs[i] >= hs[i + 1] - 1e-9 for i in range(len(hs) - 1))
    return check("headroom_monotonic", ok, f"headroom {hs[0]} → {hs[-1]} (non-increasing)")


def test_envelope_direction():
    lo = measure_world(1000, 0.05)["causal_over_naive"]
    hi = measure_world(1000, 1.0)["causal_over_naive"]
    return check("envelope_direction", lo < hi, f"causal/naive low={lo} < high={hi}")


def test_ai_work_linear():
    a, b = ai_work(50), ai_work(100)
    ratio = b["work_units"] / max(1, a["work_units"])
    ok = 1.6 <= ratio <= 2.4
    return check("ai_work_linear", ok, f"work(100)/work(50)={round(ratio,2)} (≈2 ⇒ linear in bots)")


def test_determinism():
    e1, e2 = causal_envelope(), causal_envelope()
    s1, s2 = ai_scaling(), ai_scaling()
    return check("determinism", e1 == e2 and s1 == s2, f"envelope stable={e1==e2}, ai stable={s1==s2}")


def main():
    results = [
        test_anchor_reach_authority(),
        test_footprint_bounded(),
        test_causal_le_naive(),
        test_headroom_monotonic(),
        test_envelope_direction(),
        test_ai_work_linear(),
        test_determinism(),
    ]
    print("test_causal_scale_bench — Phase 10: operating envelope (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the bench measures the REAL authority's reach,"
          f"\n  footprint is bounded, causal ≤ naive, headroom falls monotonically with coupling (cheap iff"
          f"\n  Actual ≪ Potential), the envelope points the right way, AI work is ~linear in bots, all deterministic.")
    assert passed == total, f"{total - passed} check(s) failed — the scale bench is not sound"


if __name__ == "__main__":
    main()
