# SPDX-License-Identifier: AGPL-3.0-only
"""
test_world_validate.py — Phase 6 pre-play gate proofs (validity-not-outcome).

Verdicts come from measured structure; the gate is deterministic and honest.

  1. undeclared_cycle_blocks   — a feedback loop with no declared feedback relation ⇒ BLOCK, can_play False
  2. declared_feedback_allowed — declaring a feedback relation (regulates) in the loop ⇒ no BLOCK, can_play True
  3. acyclic_can_play          — a DAG has no BLOCK and can play
  4. sparse_info_compression   — a sparse world reports INFO compression available
  5. high_blast_warns          — a world where a node reaches ≥50% reports WARN high coupling
  6. determinism               — same world ⇒ identical validation

Run:  PYTHONHASHSEED=0 python3 test_world_validate.py
"""
from __future__ import annotations

from world_format import build_causal_graph, parse_world
from world_validate import validate

CYCLE = """
world "C"
entity a:
  depends_on b
entity b:
  depends_on a
"""
DECLARED = """
world "D"
entity a:
  depends_on b
entity b:
  regulates a
"""
SPARSE = """
world "S"
entity tree:
  health 10
entity rock:
  health 10
entity hut:
  health 10
entity water:
  health 10
entity path:
  health 10
entity hill:
  health 10
entity generator:
  emits power
entity lamp:
  powered_by generator
"""
CHAIN = """
world "Chain"
entity g:
  feeds a
entity a:
  feeds b
entity b:
  feeds c
entity c:
  health 1
"""


def check(name, ok, detail):
    return (name, ok, detail)


def _v(text):
    return validate(build_causal_graph(parse_world(text)))


def test_undeclared_cycle_blocks():
    v = _v(CYCLE)
    blocked = any(x["level"] == "BLOCK" for x in v["validations"])
    return check("undeclared_cycle_blocks", blocked and not v["can_play"],
                 f"undeclared loop blocks={blocked}, can_play={v['can_play']}")


def test_declared_feedback_allowed():
    v = _v(DECLARED)
    no_block = not any(x["level"] == "BLOCK" for x in v["validations"])
    return check("declared_feedback_allowed", no_block and v["can_play"],
                 f"declared feedback ⇒ no block={no_block}, can_play={v['can_play']}")


def test_acyclic_can_play():
    v = _v(SPARSE)
    return check("acyclic_can_play", v["can_play"], f"DAG can play: {v['can_play']}")


def test_sparse_info_compression():
    v = _v(SPARSE)
    ok = any(x["kind"] == "compression_available" for x in v["validations"])
    return check("sparse_info_compression", ok, f"sparse ⇒ INFO compression available: {ok}")


def test_high_blast_warns():
    v = _v(CHAIN)   # g reaches a,b,c = 3 of 4 = 75% ≥ 50%
    ok = any(x["kind"] == "high_blast" for x in v["validations"])
    return check("high_blast_warns", ok, f"chain root high coupling ⇒ WARN: {ok}")


def test_determinism():
    a = _v(CYCLE); b = _v(CYCLE)
    return check("determinism", a == b, f"same world ⇒ identical validation: {a == b}")


def main():
    results = [
        test_undeclared_cycle_blocks(),
        test_declared_feedback_allowed(),
        test_acyclic_can_play(),
        test_sparse_info_compression(),
        test_high_blast_warns(),
        test_determinism(),
    ]
    print("test_world_validate — Phase 6 pre-play gate (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: an undeclared feedback loop blocks play,"
          f"\n  declaring it unblocks, DAGs/sparse worlds play with INFO compression, high coupling WARNs,"
          f"\n  and the gate is deterministic. Verdicts from measured structure only.")
    assert passed == total, f"{total - passed} check(s) failed — the validation gate is not sound"


if __name__ == "__main__":
    main()
