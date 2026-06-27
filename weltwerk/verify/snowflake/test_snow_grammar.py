# SPDX-License-Identifier: AGPL-3.0-only
"""
test_snow_grammar.py — the grammar is well-formed AND reduces to physics (validity-not-outcome). Pure-stdlib.

  1. grammar_generates_tree    — a branching schedule yields a non-trivial parse tree (compositional structure).
  2. decoder_recovers_regimes  — `decode_levels` recovers the branch-per-level decisions == the regime
                                 trajectory; the parse adds no information the field did not carry.
  3. every_symbol_has_mechanism— no orphan symbol: every alphabet symbol maps to a physical mechanism.
  4. no_mdl_gain               — encoding by the grammar never beats the physical description; the difference
                                 is a CONSTANT rule table (no per-flake compression gain). `grammar ≠ explanation`.
  5. determinism               — generation is deterministic.

Sound iff 5/5: a snowflake admits a context-free grammar (claims #1/#2/#3/#6 are formally true), but each
production reduces to a known mechanism and the encoding gives no bits beyond physics — so the grammar is a
RE-ENCODING, not new predictive content. `representation ≠ explanation`.

Run:  python3 test_snow_grammar.py
"""
from __future__ import annotations

from snow_grammar import (generate, decode_levels, preorder, orphan_symbols, ALPHABET,
                          RULE_TO_MECHANISM, branch, mdl_gain_per_flake, physics_bits, grammar_bits,
                          RULE_TABLE_BITS)

TEMP = -15


def chk(name, ok, detail):
    return (name, ok, detail)


def test_grammar_generates_tree():
    tree = generate([3, 3, 0], TEMP)            # high supersat ⇒ branch, branch, then facet
    pre = preorder(tree)
    ok = "B" in pre and len(pre) >= 3
    return chk("grammar_generates_tree", ok, f"preorder={pre}")


def test_decoder_recovers_regimes():
    sched = [3, 3, 0, 3, 0]
    tree = generate(sched, TEMP)
    decoded = decode_levels(tree)
    expected = [branch(TEMP, s) for s in sched]
    # leftmost path branches while branch(regime) holds, then a terminal False
    trimmed = expected[:len(decoded) - 1] + [False]
    ok = decoded == trimmed
    return chk("decoder_recovers_regimes", ok, f"decoded={decoded} matches regime trajectory={ok}")


def test_every_symbol_has_mechanism():
    ok = not orphan_symbols() and all(s in RULE_TO_MECHANISM for s in ALPHABET)
    return chk("every_symbol_has_mechanism", ok, f"orphan symbols: {orphan_symbols() or 'none'}")


def test_no_mdl_gain():
    corpus = [[3, 3, 0], [0, 3, 0, 3], [3, 0], [0, 0, 0, 0]]
    gain = mdl_gain_per_flake(corpus)               # mean(physics_bits − grammar_bits)
    per_flake_constant = all(abs((physics_bits(s) - grammar_bits(s)) + RULE_TABLE_BITS) < 1e-9 for s in corpus)
    ok = gain <= 0 and per_flake_constant
    return chk("no_mdl_gain", ok, f"mean(physics−grammar)={gain:.1f} ≤ 0; gap is the constant rule table")


def test_determinism():
    ok = generate([3, 3, 0, 3], TEMP) == generate([3, 3, 0, 3], TEMP)
    return chk("determinism", ok, f"repeated generation agrees: {ok}")


def main():
    results = [
        test_grammar_generates_tree(),
        test_decoder_recovers_regimes(),
        test_every_symbol_has_mechanism(),
        test_no_mdl_gain(),
        test_determinism(),
    ]
    print("test_snow_grammar — a snowflake grammar that reduces to physics\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the grammar is a faithful re-encoding — every "
          f"symbol\n  reduces to a mechanism, the decoder recovers only the field trajectory, and the encoding "
          f"gives no\n  bits beyond physics. representation ≠ explanation.")
    assert passed == total, f"{total - passed} check(s) failed — grammar claim not as stated"


if __name__ == "__main__":
    main()
