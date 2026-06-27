# SPDX-License-Identifier: AGPL-3.0-only
"""
test_oracle_conformance.py — PO-4 proofs: the explicit engine's verdict equals an INDEPENDENT ground-truth
oracle on tiny worlds. This converts "the engines agree" into "the engine is correct on these worlds",
discharging Proposition P2 (agreement ≠ soundness) for the tested set. Pure-stdlib.

  1. no_false_closed     — no world where engine=CLOSED while oracle=VIOLATED
  2. no_false_violated   — no world where engine=VIOLATED while oracle=CLOSED
  3. reachable_set_match — on CLOSED worlds, engine explored-state count == oracle reachable count
  4. shortest_len_match  — on VIOLATED worlds, engine ghost length == oracle shortest-violation length
  5. determinism         — the oracle is deterministic

Run:  python3 test_oracle_conformance.py
"""
from __future__ import annotations

from oracle_reference import oracle
from kernel_check import check, DEFAULT_INVARIANTS

DEPTH = 14   # large enough that these tiny worlds close (engine returns CLOSED, not BOUNDED)

WORLDS = {
    "chain": ('world "C"\n'
              'entity fa:\n  position 0 0 0\n  controls a\n'
              'entity a:\n  position 1 0 0\n  health 10\n  powers b\n'
              'entity b:\n  position 2 0 0\n  health 10\n'),
    "star": ('world "S"\n'
             'entity fa:\n  position 0 0 0\n  controls hub\n'
             'entity hub:\n  position 1 0 0\n  health 10\n  powers tail\n'
             'entity tail:\n  position 2 0 0\n  health 10\n'),
    "two": ('world "T2"\n'
            'entity fa:\n  position 0 0 0\n  controls x\n'
            'entity x:\n  position 1 0 0\n  health 10\n'
            'entity y:\n  position 2 0 0\n  health 10\n'),
}

NEVER = {"nothing_ever_destroyed": (lambda s: all(s.runtime[e]["alive"] for e in s.runtime))}
NOT_DISABLED_TAIL = {"tail_ok": (lambda s: s.runtime.get("tail", {}).get("status") != "disabled")}


def chk(name, ok, detail):
    return (name, ok, detail)


def _cases():
    cases = []
    for label, w in WORLDS.items():
        cases.append((f"{label}/default", w, DEFAULT_INVARIANTS))
        cases.append((f"{label}/never", w, NEVER))
    cases.append(("star/tail_ok", WORLDS["star"], NOT_DISABLED_TAIL))
    return cases


def test_no_false_closed():
    bad = []
    for label, w, inv in _cases():
        o = oracle(w, inv)
        e = check(w, max_depth=DEPTH, invariants=inv)
        if e.status == "CLOSED" and o[0] == "VIOLATED":
            bad.append(label)
    return chk("no_false_closed", not bad, f"engine-CLOSED-but-oracle-VIOLATED: {bad or 'none'}")


def test_no_false_violated():
    bad = []
    for label, w, inv in _cases():
        o = oracle(w, inv)
        e = check(w, max_depth=DEPTH, invariants=inv)
        if e.status == "VIOLATED" and o[0] == "CLOSED":
            bad.append(label)
    return chk("no_false_violated", not bad, f"engine-VIOLATED-but-oracle-CLOSED: {bad or 'none'}")


def test_reachable_set_match():
    mism = []
    for label, w, inv in _cases():
        o = oracle(w, inv)
        e = check(w, max_depth=DEPTH, invariants=inv)
        if o[0] == "CLOSED" and e.status == "CLOSED" and o[2] != e.states_explored:
            mism.append(f"{label}:{o[2]}!={e.states_explored}")
    return chk("reachable_set_match", not mism, f"reachable-count mismatches: {mism or 'none'}")


def test_shortest_len_match():
    mism = []
    for label, w, inv in _cases():
        o = oracle(w, inv)
        e = check(w, max_depth=DEPTH, invariants=inv)
        if o[0] == "VIOLATED" and e.status == "VIOLATED":
            elen = len(e.ghost.path) if e.ghost else None
            if o[1] != elen:
                mism.append(f"{label}:{o[1]}!={elen}")
    return chk("shortest_len_match", not mism, f"shortest-length mismatches: {mism or 'none'}")


def test_determinism():
    a = oracle(WORLDS["star"], NEVER)
    b = oracle(WORLDS["star"], NEVER)
    return chk("determinism", a == b, f"oracle deterministic: {a == b}")


def main():
    results = [
        test_no_false_closed(),
        test_no_false_violated(),
        test_reachable_set_match(),
        test_shortest_len_match(),
        test_determinism(),
    ]
    print("test_oracle_conformance — PO-4: engine verdict vs independent ground-truth oracle\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the engine never falsely reports CLOSED or "
          f"VIOLATED\n  against an independent unbounded-fixpoint oracle, the reachable-set sizes match on CLOSED, "
          f"and the\n  shortest counterexample lengths match on VIOLATED. PO-4 discharged: agreement ⇒ soundness "
          f"on these worlds.")
    assert passed == total, f"{total - passed} check(s) failed — engine disagrees with ground truth (a real bug)"


if __name__ == "__main__":
    main()
