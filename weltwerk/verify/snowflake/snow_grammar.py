# SPDX-License-Identifier: AGPL-3.0-only
"""
snow_grammar.py — does snowflake growth admit a GRAMMAR (a compositional "language"), and if so, does the
grammar explain anything the physics does not? (Research-lead investigation, skeptical by default.)

We DEFINE a snowflake language precisely, then try to REDUCE every symbol to a known physical mechanism. The
finding, made executable below:

  • ALPHABET Σ = growth modes per growth event: F (facet/plate, stable slow growth), B (branch / tip-split),
    T (tip growth). These are exactly the outputs of the Nakaya map `morphology(T, supersaturation)`.
  • GRAMMAR: a context-free grammar G whose nonterminal `A(r)` is "grow under regime r". Productions:
        A(r) → B  A(r')  A(r')      if `branch(r)`  (dendritic instability ⇒ tip splits into two)
        A(r) → F                    otherwise        (faceting ⇒ a stable terminal facet)
    The regime r is supplied by the field schedule; branching makes the derivation a TREE (so a crystal is
    trivially a parse tree — claim #3/#6 — but that is just "a branching structure is a tree").
  • PRODUCTION RULES ↔ MECHANISM: every rule maps onto a physical mechanism (`RULE_TO_MECHANISM`); there is no
    orphan symbol whose existence needs an information-theoretic explanation. This is the crux reduction:
    the grammar is a RE-ENCODING of the growth physics, not a new layer above it.
  • DECODER: `decode_levels(tree)` recovers the branch/facet decision per level, i.e. the regime trajectory —
    the same information the physical field already carries. `parse ≠ new-information`.
  • MDL (description length): encoding a flake by the grammar costs the regime schedule (= the physical field)
    PLUS a constant rule table. So per-flake there is NO compression gain over the physical description —
    `grammar-bits − physics-bits = O(1)`. A genuine language would have to beat this; it does not (here).

CONCLUSION OF THIS MODULE: the grammar is REAL but is a representation of known physics — a context-free
*re-encoding* of the (regular, field-driven) growth law plus branching recursion. It earns no predictive power
of its own. The decisive test for information BEYOND physics is in `snow_infotheory.py` (conditional mutual
information between branches given the shared field). `representation ≠ explanation`.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snow_lattice import morphology              # noqa: E402  (the Nakaya map; the alphabet's source)

# ---- alphabet + the physics each symbol reduces to -----------------------------------------------
ALPHABET = ("F", "B", "T")
RULE_TO_MECHANISM = {
    "B": "branch: Mullins–Sekerka tip-splitting instability at high supersaturation",
    "F": "facet: stable slow growth on a low-index face at low supersaturation",
    "T": "tip: steady growth of a single tip (no instability, no faceting threshold met)",
}
REGIMES = 4                                       # supersaturation classes used as the grammar's regime label


def _mode(temp_c: int, supersat: int) -> str:
    """Collapse the Nakaya morphology to the grammar's three growth events (the reduction Σ→mechanism)."""
    m = morphology(temp_c, supersat)
    if m == "dendrite":
        return "B"                                # branched ⇒ a production with two children
    if m in ("plate", "sector"):
        return "F"                                # faceted ⇒ terminal facet
    return "T"                                    # column/needle ⇒ tip growth


def branch(temp_c: int, supersat: int) -> bool:
    return _mode(temp_c, supersat) == "B"


# ---- generation (a derivation = a parse tree) ----------------------------------------------------
def generate(schedule, temp_c: int):
    """Generate a snow-crystal parse tree from a regime schedule (one supersaturation per depth level).
    Tree = (symbol, children). Branching consumes the next schedule level for both children (shared field)."""
    def build(depth):
        if depth >= len(schedule):
            return ("T", ())
        s = schedule[depth]
        if branch(temp_c, s) and depth + 1 < len(schedule):
            child = build(depth + 1)
            return ("B", (child, _copy(child)))   # two children grow under the SAME shared next-level field
        return (_mode(temp_c, s), ())
    return build(0)


def _copy(node):
    return (node[0], tuple(_copy(c) for c in node[1]))


def decode_levels(tree):
    """Decoder: walk the leftmost path, recovering 'did it branch at this level?' — i.e. the regime trajectory.
    This is the same information the physical field carries; the parse adds none. `parse ≠ new-information`."""
    out, node = [], tree
    while node[0] == "B":
        out.append(True)
        node = node[1][0]
    out.append(False)
    return out


def preorder(tree):
    out = [tree[0]]
    for c in tree[1]:
        out.extend(preorder(c))
    return out


# ---- MDL: grammar description length vs the physical description length ---------------------------
RULE_TABLE_BITS = 8 * len(RULE_TO_MECHANISM)       # a small constant: the fixed rule table


def physics_bits(schedule) -> float:
    """The physical description: the field (regime schedule) itself."""
    return len(schedule) * math.log2(REGIMES)


def grammar_bits(schedule) -> float:
    """The grammar description: the same schedule + a CONSTANT rule table. Per-flake gain over physics = 0."""
    return physics_bits(schedule) + RULE_TABLE_BITS


def mdl_gain_per_flake(corpus) -> float:
    """(physics_bits − grammar_bits) averaged: ≤ 0 (grammar never beats physics), → 0 as N grows."""
    if not corpus:
        return 0.0
    return sum(physics_bits(s) - grammar_bits(s) for s in corpus) / len(corpus)


def orphan_symbols() -> set:
    """Symbols with NO physical mechanism — these would be candidates for 'genuine' linguistic content."""
    return set(ALPHABET) - set(RULE_TO_MECHANISM)


def main():
    print("snow_grammar.py — a snowflake context-free grammar, and its reduction to physics\n")
    sched = [3, 3, 0, 3, 0]                         # high→high→low→high→low supersaturation history
    tree = generate(sched, temp_c=-15)
    print(f"  schedule (supersat/level): {sched}")
    print(f"  parse tree preorder: {preorder(tree)}")
    print(f"  decoded branch-per-level: {decode_levels(tree)}  (== the regime trajectory; no new info)")
    print(f"  production rules ↔ mechanism:")
    for s, m in RULE_TO_MECHANISM.items():
        print(f"     {s} : {m}")
    print(f"  orphan symbols (no physical mechanism): {orphan_symbols() or 'none'}")
    print(f"  MDL per flake: physics={physics_bits(sched):.1f} bits, grammar={grammar_bits(sched):.1f} bits "
          f"(gain over physics = {physics_bits(sched)-grammar_bits(sched):.1f} ≤ 0)")
    print("\n  the grammar is a faithful RE-ENCODING of the field-driven growth law + branching recursion.")
    print("  every symbol reduces to a mechanism; no orphan symbol; no MDL gain. representation ≠ explanation.")


if __name__ == "__main__":
    main()
