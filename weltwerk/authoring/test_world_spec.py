# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_spec.py — validity-not-outcome for the text → causal-topology layer.

It proves the parse and the measured topology are correct over the DECLARED graph; it does not assert any
spec is "good". Load-bearing checks: transitive-closure reachability matches a hand-computed example, and
cycle detection is sound (a DAG has none; adding one back-edge creates one).

  1. parse_roundtrip      — every declared edge appears in the graph; node set is complete
  2. reachability_exact   — influence() == hand-computed transitive closure on a known spec
  3. cycle_detection      — a DAG ⇒ no cyclic nodes; a back-edge ⇒ exactly the loop flagged
  4. determinism          — same spec ⇒ identical influence sets

Run:  PYTHONHASHSEED=0 python3 test_world_spec.py
"""
from __future__ import annotations

from world_spec import parse_spec

DAG = """
a r b
b r c
b r d
"""
CYC = DAG + "d r a\n"     # back-edge closes a loop a→b→d→a


def check(name, ok, detail):
    return (name, ok, detail)


def test_parse_roundtrip():
    g = parse_spec(DAG)
    ok = g.nodes == {"a", "b", "c", "d"} and g.edges["a"] == {"b"} and g.edges["b"] == {"c", "d"} \
        and g.edges["c"] == set() and g.edges["d"] == set()
    return check("parse_roundtrip", ok, f"nodes+edges parsed exactly: {ok}")


def test_reachability_exact():
    g = parse_spec(DAG)
    # a reaches b,c,d; influence(a) = {a,b,c,d}; influence(b)={b,c,d}; influence(c)={c}
    ok = (g.influence("a") == {"a", "b", "c", "d"} and g.influence("b") == {"b", "c", "d"}
          and g.influence("c") == {"c"} and g.blast_radius("a") == 4 and g.blast_radius("c") == 1)
    return check("reachability_exact", ok,
                 f"influence == hand-computed transitive closure: {ok}")


def test_cycle_detection():
    dag = parse_spec(DAG)
    cyc = parse_spec(CYC)
    dag_ok = dag.cyclic_nodes() == set() and dag.regime().startswith("DAG")
    # the loop is a→b→d→a ; c is a leaf, not in the cycle
    cyc_ok = cyc.cyclic_nodes() == {"a", "b", "d"} and "CYCLE" in cyc.regime().upper()
    return check("cycle_detection", dag_ok and cyc_ok,
                 f"DAG→no cycles={dag_ok}; back-edge→loop {{a,b,d}} flagged={cyc_ok}")


def test_determinism():
    a = parse_spec(CYC)
    b = parse_spec(CYC)
    ok = all(a.influence(n) == b.influence(n) for n in a.nodes)
    return check("determinism", ok, f"identical influence sets across parses: {ok}")


def main():
    results = [
        test_parse_roundtrip(),
        test_reachability_exact(),
        test_cycle_detection(),
        test_determinism(),
    ]
    print("test_world_spec — text → causal topology renders the declared graph faithfully\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:20s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Faithful iff {total}/{total}: the parse is exact, Potential reachability"
          f"\n  is the true transitive closure, and feedback loops are detected soundly. The spec is a declared"
          f"\n  input; its causal consequences are measured here — geometry is downstream.")
    assert passed == total, f"{total - passed} check(s) failed — the spec layer is not faithful"


if __name__ == "__main__":
    main()
