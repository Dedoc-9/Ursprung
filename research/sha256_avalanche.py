# SPDX-License-Identifier: AGPL-3.0-only
"""
sha256_avalanche.py — measure SHA-256's diffusion (the one genuinely runnable "stress test").

This is a textbook DEFENSIVE measurement, not an attack: it flips input bits and measures how the output bits
respond. For a strong hash the answer is "a one-bit input change is indistinguishable from a fresh random hash":
the output Hamming distance to the original is Binomial(256, 1/2) — mean 128, std ≈ 8 — and every output bit
flips with probability ≈ 1/2 (the Strict Avalanche Criterion).

WHY THIS IS THE RELEVANT TEST for the audited "GA + Hamming distance" proposal: a genetic / hill-climbing search
that scores candidate messages by Hamming distance to a target digest needs a GRADIENT — "closer in input" must
mean "closer in output." Avalanche is precisely the property that destroys that gradient. This harness MEASURES
the absence of the gradient (input→output Hamming correlation ≈ 0), which is `MEASURED` evidence that the fitness
landscape such a search would climb does not exist. Confirming strong diffusion is a POSITIVE control a good hash
must pass — never a vulnerability finding.

Run:  python3 sha256_avalanche.py
"""
from __future__ import annotations

import hashlib
import random
import statistics

N_OUT_BITS = 256


def _digest_bits(b: bytes) -> int:
    return int.from_bytes(hashlib.sha256(b).digest(), "big")


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def _flip_bit(msg: bytearray, bit: int) -> bytes:
    out = bytearray(msg)
    out[bit // 8] ^= 1 << (bit % 8)
    return bytes(out)


def single_bit_avalanche(trials: int, msg_len: int, rng: random.Random):
    """Flip ONE input bit at a time; record the output Hamming distance to the original digest."""
    distances, per_out_flips = [], [0] * N_OUT_BITS
    flips = 0
    for _ in range(trials):
        msg = bytearray(rng.randbytes(msg_len))
        base = _digest_bits(bytes(msg))
        bit = rng.randrange(msg_len * 8)
        d = _digest_bits(_flip_bit(msg, bit))
        x = base ^ d
        distances.append(bin(x).count("1"))
        flips += 1
        for j in range(N_OUT_BITS):          # accumulate per-output-bit flip frequency (Strict Avalanche)
            if (x >> j) & 1:
                per_out_flips[j] += 1
    return distances, [c / flips for c in per_out_flips]


def landscape_flatness(samples: int, msg_len: int, rng: random.Random):
    """Vary the INPUT Hamming distance between two messages; show the OUTPUT distance stays ≈128 regardless —
    i.e. no input→output correlation, so no gradient for a Hamming-guided (GA / hill-climb) search to exploit."""
    rows = []
    for d_in in (1, 2, 8, 32, 128):
        outs = []
        for _ in range(samples):
            a = bytearray(rng.randbytes(msg_len))
            b = bytearray(a)
            for bit in rng.sample(range(msg_len * 8), d_in):
                b[bit // 8] ^= 1 << (bit % 8)
            outs.append(_hamming(_digest_bits(bytes(a)), _digest_bits(bytes(b))))
        rows.append((d_in, statistics.mean(outs), statistics.pstdev(outs)))
    return rows


def main() -> None:
    rng = random.Random(20260623)           # fixed seed → reproducible
    TRIALS, MSG_LEN = 20000, 32

    print("sha256_avalanche — diffusion measurement (defensive; no attack). Expect mean ≈ 128, std ≈ 8.\n")

    distances, per_bit = single_bit_avalanche(TRIALS, MSG_LEN, rng)
    mean_d, std_d = statistics.mean(distances), statistics.pstdev(distances)
    print(f"  single-bit avalanche over {TRIALS} trials ({MSG_LEN}-byte msgs):")
    print(f"    output Hamming distance: mean={mean_d:.2f}  std={std_d:.2f}  min={min(distances)}  max={max(distances)}")
    print(f"    per-output-bit flip prob: min={min(per_bit):.3f}  mean={statistics.mean(per_bit):.3f}  max={max(per_bit):.3f}  (ideal 0.5)")
    print()

    print("  landscape flatness — output distance vs INPUT Hamming distance (no gradient if all ≈128):")
    rows = landscape_flatness(3000, MSG_LEN, rng)
    for d_in, m, s in rows:
        print(f"    d_in={d_in:>3}  →  d_out mean={m:.2f}  std={s:.2f}")
    print()

    # ---- sanity self-test (stochastic; loose tolerances around the Binomial(256,1/2) expectation) ----
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    check("mean_near_128", abs(mean_d - 128) < 2.0, f"single-bit flip → mean output distance {mean_d:.2f} ≈ 128")
    check("std_near_8", abs(std_d - 8) < 2.0, f"std {std_d:.2f} ≈ 8 (Binomial(256,1/2))")
    check("strict_avalanche", all(0.45 < p < 0.55 for p in per_bit),
          "every output bit flips with prob ≈ 0.5 — no privileged output bit")
    check("no_gradient", all(abs(m - 128) < 3.0 for _d, m, _s in rows),
          "output distance ≈128 for EVERY input distance ≥1 — the GA/Hamming gradient does not exist")

    print(f"\n  {passed}/{total} diffusion checks. SHA-256 shows full avalanche: a one-bit input change is")
    print("  indistinguishable from a fresh random hash, and input→output Hamming distance is uncorrelated.")
    print("  This is the POSITIVE control a strong hash must pass — and it is precisely why a Hamming-distance")
    print("  / genetic search has no gradient to climb. `MEASURED`; confirming diffusion ≠ finding a weakness.")
    assert passed == total, "avalanche measurement deviated from the Binomial(256,1/2) expectation"


if __name__ == "__main__":
    main()
