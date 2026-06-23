# SPDX-License-Identifier: AGPL-3.0-only
"""
carry_markov_ck.py — the Chapman–Kolmogorov bridge from LOCAL carry structure to GLOBAL uniformity, computed
EXACTLY on the one place it is tractable: the carry chain of modular addition (the 2-adic dimension).

Context: `sha256_2adic_branch.py` measured local carry structure (atomic survival 0.38 ≠ 0.5); `sha256_avalanche.py`
measured global flatness (output ≈ uniform). Chapman–Kolmogorov is the formal link — BUT it gives only the
COMPOSITION law (the multi-step kernel is the product of single-step kernels); the FLATTENING is a separate
dynamical fact (a spectral gap / mixing), which the avalanche measured. This script shows both, exactly, on the
2-state carry chain, where the matrices are small enough to write down.

THE CARRY CHAIN. For modular addition with uniform random operand bits, the carry bit evolves across BIT
positions as a 2-state Markov chain c_{i+1} = maj(a_i, b_i, c_i):
    from c=0: P(c'=1) = P(a∧b) = 1/4        from c=1: P(c'=1) = P(a∨b) = 3/4
    K = [[3/4, 1/4],      (rows = current state 0/1; cols = next state 0/1)
         [1/4, 3/4]]
This single-step kernel is STRUCTURED (off-diagonal 1/4 ≠ the uniform 1/2 — the local 2-adic gradient, the cousin
of the 0.38 atomic survival). Chapman–Kolmogorov: K^(m+n) = K^m · K^n. Its eigenvalues are 1 (stationary) and
1/2 (the SPECTRAL GAP); K^n → the rank-1 uniform operator [[1/2,1/2],[1/2,1/2]] with deviation 0.5·(1/2)^n. So:
    local structure (K ≠ uniform)  ──CK composition──▶  K^n  ──spectral gap 1/2──▶  global uniformity.

HONEST BOUNDARY. This is the BIT-position carry chain (the 2-adic axis) — an EXACT illustration of the mechanism,
NOT the SHA-256 ROUND operator, which is 2^256-dimensional and is *measured* (avalanche), never computed. CK is
the scaffold; the spectral gap is the dynamical fact; avalanche is the measurement at full scale. SHA-256 rounds
are deterministic, so CK applies to the induced kernel on DISTRIBUTIONS (a declared model). `model ≠ the thing`;
`composition ≠ flattening`. Same CK language as Collatz (transfer operator) — there the limiting operator is a
structured invariant measure; here it is uniform.

Run:  python3 carry_markov_ck.py
"""
from __future__ import annotations

K = [[0.75, 0.25], [0.25, 0.75]]            # carry-chain single-step kernel (exact, from uniform operand bits)
UNIFORM = [[0.5, 0.5], [0.5, 0.5]]          # the rank-1 limiting operator


def matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]


def matpow(A, n):
    R = [[1.0, 0.0], [0.0, 1.0]]            # identity
    for _ in range(n):
        R = matmul(R, A)
    return R


def eigenvalues_2x2_symmetric(A):
    """Closed form for a symmetric 2x2: λ = (tr ± sqrt(tr² − 4·det)) / 2."""
    tr = A[0][0] + A[1][1]
    det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
    disc = (tr * tr - 4 * det) ** 0.5
    return sorted([(tr + disc) / 2, (tr - disc) / 2], reverse=True)


def deviation_from_uniform(M):
    return max(abs(M[i][j] - 0.5) for i in range(2) for j in range(2))


def main() -> None:
    print("carry_markov_ck — Chapman–Kolmogorov on the carry chain: local structure → uniform, computed exactly.\n")

    evals = eigenvalues_2x2_symmetric(K)
    gap = evals[1]                          # second eigenvalue = mixing rate
    print(f"  single-step kernel K = {K}")
    print(f"  eigenvalues: {evals[0]:.3f} (stationary), {gap:.3f} (spectral gap / mixing rate)")
    print(f"  off-diagonal {K[0][1]} ≠ uniform 0.5  →  LOCAL structure (the 0.38-survival cousin)\n")

    print("  Chapman–Kolmogorov composition K^n, and its deviation from the uniform operator:")
    for n in (1, 2, 4, 8, 16):
        Kn = matpow(K, n)
        print(f"    n={n:>2}  K^n[0]={[round(x, 5) for x in Kn[0]]}  deviation={deviation_from_uniform(Kn):.6f}  (= 0.5·{gap}^{n} = {0.5 * gap ** n:.6f})")
    print()

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. Chapman–Kolmogorov: the multi-step kernel IS the product of single-step kernels
    lhs, rhs = matpow(K, 5), matmul(matpow(K, 2), matpow(K, 3))
    check("chapman_kolmogorov_composition",
          all(abs(lhs[i][j] - rhs[i][j]) < 1e-12 for i in range(2) for j in range(2)),
          "K^5 = K^2 · K^3 exactly — the composition law that links single-round to multi-round")

    # 2. eigenvalues are 1 (stationary) and 1/2 (spectral gap)
    check("spectral_gap_one_half", abs(evals[0] - 1.0) < 1e-12 and abs(gap - 0.5) < 1e-12,
          "λ = {1.0, 0.5}; the gap 0.5 is the mixing rate")

    # 3. single-step kernel is STRUCTURED (local 2-adic carry gradient) — not already uniform
    check("single_step_structured", abs(K[0][1] - 0.5) > 0.1,
          "off-diagonal 0.25 ≠ 0.5 — local structure exists at one step (compose, don't assume uniform)")

    # 4. CK is COMPOSITION, not flattening: flattening is the SEPARATE spectral-gap fact
    devs = [deviation_from_uniform(matpow(K, n)) for n in (1, 2, 4, 8)]
    check("flattening_is_spectral_gap",
          all(abs(devs[i] - 0.5 * gap ** (2 ** i)) < 1e-9 for i in range(4)) and devs[-1] < devs[0],
          "deviation from uniform = 0.5·(spectral gap)^n — mixing is governed by λ₂, not by CK alone")

    # 5. the chain MIXES to the uniform (rank-1) operator
    check("mixes_to_uniform", deviation_from_uniform(matpow(K, 40)) < 1e-9,
          "K^40 ≈ [[0.5,0.5],[0.5,0.5]] — local structure dissolves into global uniformity")

    # 6. honest boundary: this is the bit-position carry chain, NOT the 2^256 round operator
    note = ("EXACT illustration on the carry (2-adic) axis; the SHA-256 ROUND operator is 2^256-dimensional, "
            "MEASURED by avalanche, not computed. CK = composition; spectral gap = flattening; model ≠ thing.")
    check("declares_toy_boundary", "2^256" in note and "MEASURED" in note and "not computed" in note,
          "the demo declares its scope — a mechanism illustration, never a full-scale computation")

    print(f"\n  {passed}/{total} checks. Chapman–Kolmogorov is the COMPOSITION law linking the local single-step")
    print("  carry kernel (structured: off-diagonal 0.25, the 0.38-survival cousin) to the multi-step kernel K^n —")
    print("  but the FLATTENING to uniform is the separate dynamical fact of a SPECTRAL GAP (λ₂ = 0.5), which is")
    print("  what avalanche measured at full 2^256 scale. Same CK language as Collatz's transfer operator; there")
    print("  it mixes to a structured invariant measure, here to the uniform (rank-1) operator. CK is the")
    print("  scaffold, the spectral gap is the beam; `composition ≠ flattening`; `model ≠ the thing`.")
    assert passed == total, "carry_markov_ck failed its own self-test"


if __name__ == "__main__":
    main()
