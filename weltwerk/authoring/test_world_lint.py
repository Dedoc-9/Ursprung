# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_lint.py — validity-not-outcome for the causal design linter.

It proves the structural analyses are correct over the declared graph; it does not assert any design is
good or bad. Load-bearing checks: SCC partition is exact, and criticality correctly identifies a chain's
middle node as a bottleneck (removing it costs reach) while a leaf costs nothing.

  1. scc_exact          — DAG ⇒ all singletons; a back-edge ⇒ the loop grouped as one SCC
  2. criticality_chain  — on a→b→c, removing b costs reach (>0); removing the leaf c costs 0
  3. load_bearing_rank  — the source of a chain has the largest blast radius
  4. isolated_detected  — an entity with no edges is flagged isolated
  5. determinism        — same spec ⇒ identical diagnostics

Run:  PYTHONHASHSEED=0 python3 test_world_lint.py
"""
from __future__ import annotations

from world_lint import criticality, lint, sccs
from world_spec import parse_spec

DAG = "a r b\nb r c\nb r d\n"
CYC = DAG + "d r a\n"
CHAIN = "a r b\nb r c\n"


def check(name, ok, detail):
    return (name, ok, detail)


def test_scc_exact():
    dag = sccs(parse_spec(DAG))
    cyc = sccs(parse_spec(CYC))
    dag_singletons = all(len(c) == 1 for c in dag)
    cyc_loop = sorted(next(c for c in cyc if len(c) > 1)) == ["a", "b", "d"]
    return check("scc_exact", dag_singletons and cyc_loop,
                 f"DAG all singletons={dag_singletons}; cycle SCC={{a,b,d}}={cyc_loop}")


def test_criticality_chain():
    g = parse_spec(CHAIN)
    cb, cc = criticality(g, "b"), criticality(g, "c")
    return check("criticality_chain", cb > 0 and cc == 0,
                 f"removing middle b costs {cb}(>0); removing leaf c costs {cc}(=0)")


def test_load_bearing_rank():
    g = parse_spec(CHAIN)
    ok = g.blast_radius("a") == 3 and g.blast_radius("c") == 1
    return check("load_bearing_rank", ok,
                 f"chain source a blast={g.blast_radius('a')} (max); leaf c={g.blast_radius('c')}")


def test_isolated_detected():
    g = parse_spec(CHAIN + "entity lonely\n")
    kinds = [(d.kind, d.subject) for d in lint(g)]
    ok = ("isolated", "lonely") in kinds
    return check("isolated_detected", ok, f"'lonely' flagged isolated: {ok}")


def test_determinism():
    a = lint(parse_spec(CYC))
    b = lint(parse_spec(CYC))
    return check("determinism", a == b, f"identical diagnostics across runs: {a == b}")


def main():
    results = [
        test_scc_exact(),
        test_criticality_chain(),
        test_load_bearing_rank(),
        test_isolated_detected(),
        test_determinism(),
    ]
    print("test_world_lint — the causal linter's structural analyses are exact (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:20s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: SCC partition exact, criticality finds the"
          f"\n  bottleneck, blast radius ranks load-bearing nodes, isolated nodes flagged. Structural facts"
          f"\n  over the declared graph — risks, not behavioral verdicts.")
    assert passed == total, f"{total - passed} check(s) failed — the linter is not sound"


if __name__ == "__main__":
    main()
