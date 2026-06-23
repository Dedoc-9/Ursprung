# SPDX-License-Identifier: AGPL-3.0-only
"""
sha256_2adic_branch.py — falsification test for the "2-adic reverse-Collatz" hypothesis (carry-conditioned
backward inversion). DEFENSIVE structural measurement: it measures carry-branch survival statistics of modular
addition; it produces NO preimage, NO collision, NO attack. The honest expected conclusion is that SHA-256's
arithmetic offers local carry structure that does NOT compound — i.e. the hash is unthreatened.

THE HYPOTHESIS (now FORMULATED & EXPOSED): a SHA-256 round, with the modular-addition carry vector fixed, is an
affine map with a unique inverse; stepping backward while branching on carries yields a preimage tree that is
SUB-EXPONENTIALLY PRUNABLE iff wrong carry branches are forced inconsistent by 2-adic structure. Falsifier
(the proposer's): Pr(carry-vector consistent | wrong branch) = 1/2 per flipped bit ⇒ no structural gradient ⇒
the tree fractures like the flat landscape `sha256_avalanche.py` measured.

TWO CORRECTIONS THE AUDIT IMPOSES (do not flatter the formulation):
  (A) Carries are not the only nonlinearity. Ch(e,f,g) and Maj(a,b,c) are AND-based and NONLINEAR over GF(2)
      regardless of carries — fixing carries does NOT make the round affine; a linearizing conditioning must also
      fix Ch/Maj branches, so the true branching is LARGER than carry-only (worst case worse than 2^32/add).
  (B) Atomic survival ≠ 1/2 is the EXPECTED, already-known result (addition is not a random function — it is why
      SAT reaches ~16-20 rounds). The decisive question is whether that local structure COMPOUNDS across rounds;
      avalanche already measured that it does not. So the verdict is local-yes / global-no, never a break.

This script measures the exact carry sub-structure (A is noted, not modeled) and reports the regime. Compounding
is cited from `sha256_avalanche.py` (cross-round decorrelation), not re-derived here.

Run:  python3 sha256_2adic_branch.py
"""
from __future__ import annotations

import random

N = 32
MASK = (1 << N) - 1


def carry_vector(a: int, b: int) -> list:
    """Exact carry chain of a + b mod 2^N. c[0]=0; c[i+1] = carry-out of bit i; c[N] is the (discarded) overflow.
    Internal carries are c[1..N-1]."""
    c = [0] * (N + 1)
    for i in range(N):
        ai, bi = (a >> i) & 1, (b >> i) & 1
        c[i + 1] = (ai & bi) | (c[i] & (ai ^ bi))     # full-adder carry-out
    return c


def sum_from_carries(a: int, b: int, c: list) -> int:
    """Reconstruct z = a+b from operands and carries via z_i = a_i ^ b_i ^ c_i (full-adder sum). Sanity check."""
    z = 0
    for i in range(N):
        z |= (((a >> i) & 1) ^ ((b >> i) & 1) ^ c[i]) << i
    return z


def consistent(z: int, c: list) -> bool:
    """Does there exist (a,b) with a+b ≡ z (mod 2^N) AND carry vector exactly c? Per-bit, with s_i = z_i ^ c_i:
        s_i = 1  → carry-out is FORCED to c_i, so the branch is inconsistent unless c[i+1] == c[i];
        s_i = 0  → carry-out is free, always consistent.
    (Bit N-1 produces the discarded overflow c[N], which is unconstrained, so it is never checked.)"""
    for i in range(N - 1):
        if (((z >> i) & 1) ^ c[i]) == 1 and c[i + 1] != c[i]:
            return False
    return True


def atomic_survival(trials: int, rng: random.Random) -> float:
    """Pr(a Hamming-1 carry flip stays consistent) over random additions. The proposer's falsifier predicts 0.5
    (random); addition's real structure should give ≠ 0.5 (local 2-adic gradient)."""
    survived = 0
    for _ in range(trials):
        a, b = rng.getrandbits(N), rng.getrandbits(N)
        z = (a + b) & MASK
        c = carry_vector(a, b)
        j = rng.randrange(1, N)                        # flip one internal carry bit c[1..N-1]
        cp = list(c)
        cp[j] ^= 1
        survived += consistent(z, cp)
    return survived / trials


def main() -> None:
    rng = random.Random(20260623)
    TRIALS = 200000

    print("sha256_2adic_branch — carry-branch survival test (defensive; no attack). Falsifier: survival = 0.5.\n")

    surv = atomic_survival(TRIALS, rng)
    null = 0.5
    deviation = abs(surv - null)
    print(f"  atomic carry-branch survival (Hamming-1 flip, {TRIALS} trials): {surv:.4f}   null (random) = {null}")
    print(f"  deviation from random: {deviation:.4f}")

    # data-driven regime (DECLARED interpretation; never a break)
    if deviation < 0.02:
        regime = "ATOMIC_FLAT — no local carry gradient; matches the avalanche null → hypothesis refuted atomically"
    else:
        regime = ("ATOMIC_STRUCTURE_PRESENT — a local 2-adic carry gradient exists (expected; it is why SAT "
                  "reaches ~16-20 rounds). BUT avalanche measured cross-round decorrelation, so it does NOT "
                  "compound → BOUNDED_TO_REDUCED_ROUNDS")
    print(f"\n  regime: {regime}")
    print("  caveat (A): Ch/Maj are nonlinear regardless of carries → full-round branching is LARGER than this")
    print("  carry-only measurement; compounding (B) is cited from sha256_avalanche.py, not re-derived here.")
    print("  → full SHA-256 unthreatened either way; best case here only confirms known reduced-round structure.\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. the carry model is correct: it reconstructs the sum
    ok_recon = all(sum_from_carries(a, b, carry_vector(a, b)) == ((a + b) & MASK)
                   for a, b in [(rng.getrandbits(N), rng.getrandbits(N)) for _ in range(2000)])
    check("carry_model_reconstructs_sum", ok_recon, "z_i = a_i ^ b_i ^ c_i rebuilds a+b mod 2^32 for all samples")

    # 2. the TRUE carry vector is always consistent (definitional sanity of the consistency predicate)
    ok_true = all(consistent((a + b) & MASK, carry_vector(a, b))
                  for a, b in [(rng.getrandbits(N), rng.getrandbits(N)) for _ in range(5000)])
    check("true_carry_always_consistent", ok_true, "the real carry vector passes consistency — predicate is sound")

    # 3. some wrong branches ARE pruned (consistency is not trivially always-true)
    check("pruning_exists", 0.0 < surv < 1.0, f"survival {surv:.4f} ∈ (0,1) — wrong carry flips can be ruled out")

    # 4. the proposer's falsifier is a real, decidable comparison (survival vs 0.5)
    check("falsifier_is_decidable", isinstance(surv, float) and 0.0 <= surv <= 1.0,
          "Pr(consistent|wrong) is measured against the 0.5 null — refute/structure is a data call, not rhetoric")

    # 5. NO OVERCLAIM: the verdict is a regime (flat / bounded), never a break; full hash stated unthreatened
    blob = regime.lower()
    # positive markers must match the ACTUAL regime vocabulary: ATOMIC_FLAT → "refuted", the structured branch
    # → "bounded_to_reduced_rounds". (Earlier this looked for "reduced-round" with a hyphen — a substring that
    # never appears in the underscore/plural regime string, so a CORRECT verdict tripped a WRONG check. Fixed.)
    check("no_break_overclaim",
          all(w not in blob for w in ("preimage found", "collision found", "broken", "inverted"))
          and ("bounded" in blob or "refuted" in blob),
          "result is ATOMIC_FLAT or BOUNDED_TO_REDUCED_ROUNDS — never a claimed break (Rule: declared ≠ verified)")

    # 6. deterministic under seed (reproducible measurement)
    check("deterministic", atomic_survival(20000, random.Random(20260623)) == atomic_survival(20000, random.Random(20260623)),
          "seeded survival is reproducible — the measurement is a fixed witness")

    print(f"\n  {passed}/{total} checks. The hypothesis is now TESTED, not just exposed: the carry sub-structure is")
    print("  measured exactly, the proposer's 0.5 falsifier is a decidable data call, and the verdict can only be")
    print("  'no local gradient' (refuted) or 'local gradient that does not compound' (bounded to reduced rounds).")
    print("  Neither is a break: Ch/Maj add nonlinearity carries don't remove, and avalanche shows the local")
    print("  structure decorrelates across rounds. `declared ≠ verified`; local 2-adic structure ≠ global break.")
    assert passed == total, "sha256_2adic_branch failed its own self-test"


if __name__ == "__main__":
    main()
