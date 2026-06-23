# SPDX-License-Identifier: AGPL-3.0-only
"""
carry_anf.py — EXACT algebraic normal form (ANF) and algebraic degree of the modular-addition carry bits over
GF(2). The "no-statistics" Option 3: formalize the local structure that drives SHA-256's degree growth, and
VERIFY the hand-derivation rather than accept it.

The carry recurrence (X + Y mod 2^n, ripple carry):
    C_0 = 0,   C_{i+1} = (X_i · Y_i) ⊕ ((X_i ⊕ Y_i) · C_i)
and the proposed closed form:
    C_{i+1} = ⊕_{j=0}^{i} ( X_j · Y_j · ∏_{k=j+1}^{i} (X_k ⊕ Y_k) ).

This script computes both EXACTLY (truth table over the 2(i+1) inputs), extracts the ANF via the Möbius
transform, and measures the algebraic degree. It is a verifier: it confirms the closed form equals the
recurrence, prints the ANF monomials (matching the hand expansion of C₂/C₃), and pins the degree law.

CAUGHT SLIP (the reason to verify, not accept): the proposed summary `deg(C_{i+1}) = i+1` contradicts its own
worked examples (C₁ has degree 2, not 1). The exact law is **deg(C_{i+1}) = i + 2** (equivalently: the carry
into bit m has degree m+1). The closed form's j=0 term, X₀·Y₀·∏(X_k⊕Y_k), is two variables times i linear
factors = degree i+2. The mechanism is right; the exponent was off by one.

Run:  python3 carry_anf.py
"""
from __future__ import annotations


def carry(v: int, i: int) -> int:
    """C_{i+1} evaluated at input assignment v, where bit 2j of v = X_j and bit 2j+1 = Y_j. Pure recurrence."""
    c = 0
    for t in range(i + 1):
        x, y = (v >> (2 * t)) & 1, (v >> (2 * t + 1)) & 1
        c = (x & y) ^ ((x ^ y) & c)
    return c


def carry_closed(v: int, i: int) -> int:
    """The proposed closed form C_{i+1} = ⊕_j X_j Y_j ∏_{k>j} (X_k ⊕ Y_k), evaluated at v."""
    acc = 0
    for j in range(i + 1):
        term = ((v >> (2 * j)) & 1) & ((v >> (2 * j + 1)) & 1)
        for k in range(j + 1, i + 1):
            term &= (((v >> (2 * k)) & 1) ^ ((v >> (2 * k + 1)) & 1))
        acc ^= term
    return acc


def truth_table(i: int) -> list:
    n = 2 * (i + 1)
    return [carry(v, i) for v in range(1 << n)]


def anf(tt: list) -> list:
    """Möbius transform: ANF coefficients. a[m]=1 ⇔ the monomial ∏_{b∈bits(m)} var_b is present."""
    a, N = tt[:], len(tt)
    step = 1
    while step < N:
        for base in range(0, N, 2 * step):
            for j in range(base, base + step):
                a[j + step] ^= a[j]
        step <<= 1
    return a


def _var(b: int) -> str:
    return f"{'X' if b % 2 == 0 else 'Y'}{b // 2}"


def monomials(tt: list) -> set:
    """Set of monomials (as frozensets of variable names) present in the ANF."""
    a = anf(tt)
    out = set()
    for m, coeff in enumerate(a):
        if coeff:
            out.add(frozenset(_var(b) for b in range(m.bit_length()) if (m >> b) & 1))
    return out


def algebraic_degree(tt: list) -> int:
    a = anf(tt)
    return max((bin(m).count("1") for m, coeff in enumerate(a) if coeff), default=0)


def main() -> None:
    K = 6
    print("carry_anf — exact ANF / algebraic degree of modular-addition carries over GF(2) (no statistics).\n")

    print("  carry bit      algebraic degree     (proposed i+1)   (exact i+2)")
    for i in range(K + 1):
        d = algebraic_degree(truth_table(i))
        print(f"  C_{i + 1:<2}           deg = {d:<14} {i + 1:<16} {i + 2}")
    print()

    print("  ANF monomials (lowest carries — match the hand expansion):")
    for i in (0, 1, 2):
        monos = sorted(("·".join(sorted(m)) for m in monomials(truth_table(i))), key=lambda s: (s.count("·"), s))
        print(f"    C_{i + 1} = {' ⊕ '.join(monos)}")
    print()

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. the worked examples are correct: C1 deg 2, C2 deg 3, C3 deg 4
    check("worked_examples_degrees",
          algebraic_degree(truth_table(0)) == 2 and algebraic_degree(truth_table(1)) == 3
          and algebraic_degree(truth_table(2)) == 4,
          "C1=2, C2=3, C3=4 — the hand-derived example degrees are right")

    # 2. the EXACT degree law is i+2 (not the stated i+1)
    check("degree_law_is_i_plus_2", all(algebraic_degree(truth_table(i)) == i + 2 for i in range(K + 1)),
          "deg(C_{i+1}) = i+2 for i=0..6 — the closed form's j=0 term is 2 vars × i linear factors")

    # 3. the proposed summary formula i+1 is off by exactly one (its own examples prove it)
    check("stated_formula_off_by_one",
          all(algebraic_degree(truth_table(i)) == (i + 1) + 1 for i in range(K + 1)),
          "deg = (i+1)+1, so 'deg = i+1' undercounts by 1 — C1=X0·Y0 is degree 2, not 1")

    # 4. the closed form equals the recurrence, exactly, over all inputs
    check("closed_form_equals_recurrence",
          all(carry_closed(v, i) == carry(v, i) for i in range(K + 1) for v in range(1 << (2 * (i + 1)))),
          "⊕_j X_j Y_j ∏(X_k⊕Y_k) reproduces the carry recurrence on every input — the formula is correct")

    # 5. degree grows by exactly 1 per bit position (the monotone 'degree multiplier')
    check("degree_grows_by_one",
          all(algebraic_degree(truth_table(i + 1)) - algebraic_degree(truth_table(i)) == 1 for i in range(K)),
          "each higher carry bit adds exactly one to the algebraic degree — monotone, deterministic")

    # 6. the ANF of C2 matches the hand expansion exactly (X1Y1 ⊕ X1X0Y0 ⊕ Y1X0Y0)
    expected_c2 = {frozenset({"X1", "Y1"}), frozenset({"X1", "X0", "Y0"}), frozenset({"Y1", "X0", "Y0"})}
    check("anf_C2_matches_hand", monomials(truth_table(1)) == expected_c2,
          "C2 ANF = {X1·Y1, X1·X0·Y0, Y1·X0·Y0} — the hand expansion is exact")

    print(f"\n  {passed}/{total} checks. The carry recurrence's closed form is verified exact, and its ANF degree")
    print("  is deg(C_{i+1}) = i+2 — monotone, +1 per bit (the worked C1=2,C2=3,C3=4 confirm it; the summary")
    print("  'i+1' was off by one). This is the concrete, local mechanism: modular addition natively multiplies")
    print("  algebraic degree by bit position, and composing it with rotations + Ch/Maj in Round 1 drives the")
    print("  deterministic avalanche toward saturation — no continuum analogy required. `verify, don't accept`.")
    assert passed == total, "carry_anf failed its own self-test"


if __name__ == "__main__":
    main()
