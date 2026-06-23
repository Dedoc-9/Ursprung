# SPDX-License-Identifier: AGPL-3.0-only
"""
collatz_reconcile.py — structural ("reconcilable") analysis of a Collatz-like piecewise map, with the Ursprung
no-upgrade discipline: it computes DENSITY / ALMOST-ALL / EXPECTED results and REFUSES to upgrade them to the
universal ("all n") claim.

Forward iteration of a Collatz-like map is a pseudo-random walk (like SHA-256 diffusion). The reconcilable shift
is to test ALGEBRAIC / p-ADIC structure instead. This implements four such tests for a GENERAL map
    f(n) = (a_r · n + b_r) / d_r        for  n ≡ r (mod m),   valid when d_r | (a_r·n + b_r)
(standard accelerated Collatz: m=2; r=0 → n/2 = (1,0,2); r=1 → (3n+1)/2 = (3,1,2)):

  1. INVERSE ORBIT TREE  — backward BFS from a target; enumerates the basin. `MEASURED` per integer reached;
     a depth-k tree is a FINITE basin — it does NOT establish universality.
  2. TERRAS / 2-adic BIJECTION — the k-step branch vector depends only on n mod m^k; for the standard map the
     map (n mod 2^k) → parity vector is a bijection (Terras 1976) ⇒ density-1 stopping time (almost all n
     decrease). `MEASURED` (verified for finite k; proven asymptotically). Proves ALMOST ALL, never ALL.
  3. LOG-DRIFT / MARTINGALE — E[log(f(n)/n)] over the branches. < 0 ⇒ supermartingale ⇒ *statistical* (not
     deterministic) convergence. The drift VALUE is `MEASURED`; the implication "converges" is a `DECLARED`
     HEURISTIC — it cannot exclude a single divergent orbit or a hidden cycle (cf. Tao 2019: *almost all*
     orbits attain *almost bounded* values — still not the conjecture).
  4. TRANSFER / DENSITY — the branch-frequency distribution over residues; a density/invariant-measure result,
     not the universal claim.

THE DISCIPLINE: this tool corners the uncertainty into a named, measure-zero residual (exceptional set + possible
cycles + possible divergent orbit); it never prints "conjecture proved". `density 1 ≠ all`; `expected ≠ worst
case`; `heuristic ≠ proof`. (Why this works on Collatz but not SHA-256: Collatz HAS the 2-adic bijection /
negative drift this exploits; SHA-256's avalanche is the engineered ABSENCE of exactly that structure.)

Run:  python3 collatz_reconcile.py
"""
from __future__ import annotations

import math
from collections import deque

# A map spec: (modulus m, {residue r: (a, b, d)} meaning f(n)=(a*n+b)//d for n≡r (mod m)).
STD_COLLATZ = (2, {0: (1, 0, 2), 1: (3, 1, 2)})          # accelerated Collatz (believed convergent)
FIVE_N_1 = (2, {0: (1, 0, 2), 1: (5, 1, 2)})              # 5n+1 variant (believed to diverge for some seeds)


def forward(n: int, spec) -> int:
    m, rules = spec
    a, b, d = rules[n % m]
    val = a * n + b
    assert val % d == 0, f"map ill-defined: {d} ∤ {a}*{n}+{b}"
    return val // d


def branch_vector(n: int, spec, k: int) -> tuple:
    """The k-step itinerary (sequence of residue classes / branches taken). Depends only on n mod m^k."""
    m, _ = spec
    v, x = [], n
    for _ in range(k):
        v.append(x % m)
        x = forward(x, spec)
    return tuple(v)


def terras_injective(spec, k: int) -> bool:
    """Verify the (n mod m^k) → k-step branch-vector map is INJECTIVE (⇒ bijective, the Terras structure).
    True for the standard map; False reveals a map LACKING the clean p-adic structure."""
    m, _ = spec
    seen = {branch_vector(n, spec, k) for n in range(m ** k)}
    return len(seen) == m ** k


def stopping_density(spec, k: int) -> float:
    """Density of integers whose trajectory drops below its start within ≤ k steps = Terras' STOPPING TIME ≤ k.
    MONOTONE non-decreasing in k, → 1 (almost all). `MEASURED` for this k; the limit '= 1' is proven (almost
    all), the universal 'all' is NOT.
    (Correction: an earlier version counted 'decreased at EXACTLY step k' — a NON-monotone proxy that did not
    match the Terras stopping-time density and dipped with k. Caught by combing the output; fixed.)"""
    m, _ = spec
    hi = m ** k
    stopped = 0
    for n in range(1, hi):
        x = n
        for _ in range(k):
            x = forward(x, spec)
            if x < n:                 # first drop below the start = stopping time ≤ k
                stopped += 1
                break
    return stopped / (hi - 1)


def drift(spec) -> float:
    """E[log(f(n)/n)] estimated by the per-branch multiplier a_r/d_r, uniform over residues (first-order
    heuristic). < 0 ⇒ supermartingale ⇒ statistical convergence (a HEURISTIC, not a proof)."""
    m, rules = spec
    return sum(math.log(a / d) for (a, b, d) in rules.values()) / m


def predecessors(n: int, spec) -> list:
    """Branch-inverses: every m with f(m)=n. m = (d*n - b)/a, integer, > 0, and m ≡ r (mod m_mod)."""
    m_mod, rules = spec
    out = []
    for r, (a, b, d) in rules.items():
        num = d * n - b
        if a != 0 and num % a == 0:
            mm = num // a
            if mm > 0 and mm % m_mod == r:
                out.append(mm)
    return sorted(set(out))


def inverse_basin(targets, spec, depth: int) -> set:
    """Backward BFS from `targets` to `depth` — the deterministic basin enumerated so far. FINITE: reaching a
    number reconciles IT; it does not establish universality."""
    basin, frontier = set(targets), deque((t, 0) for t in targets)
    while frontier:
        n, d = frontier.popleft()
        if d >= depth:
            continue
        for p in predecessors(n, spec):
            if p not in basin:
                basin.add(p)
                frontier.append((p, d + 1))
    return basin


def report(spec, k: int = 10, basin_depth: int = 12) -> dict:
    inj = terras_injective(spec, k)
    return {
        "terras_injective_at_k": (inj, "MEASURED (verified for this k; proven asymptotically for standard map)"),
        "stopping_density_at_k": (round(stopping_density(spec, k), 4), "MEASURED stopping-time≤k (monotone ↑, → 1 = ALMOST ALL proven; ≠ ALL)"),
        "log_drift": (round(drift(spec), 4), "value MEASURED; 'converges' is a DECLARED heuristic, NOT a proof"),
        "supermartingale": (drift(spec) < 0, "DECLARED heuristic (negative drift ⇏ no divergent orbit / no cycle)"),
        "basin_size_to_depth": (len(inverse_basin([1], spec, basin_depth)), "MEASURED (finite enumeration only)"),
        "universal_all_n": "OPEN — NOT established by any of these (density 1 ≠ all; expected ≠ worst case)",
        "residual": "the measure-zero exceptional set + possible nontrivial cycles + a possible divergent orbit",
        "note": "structural tests CORNER the uncertainty into a named residual; they never prove the universal "
                "claim. Works on Collatz because it HAS 2-adic/drift structure — the structure a cryptographic "
                "hash (SHA-256 avalanche) is designed to remove.",
    }


def main() -> None:
    print("collatz_reconcile — algebraic/p-adic structure tests; DENSITY/ALMOST-ALL, never the universal claim.\n")

    rep = report(STD_COLLATZ)
    print("  standard accelerated Collatz (3n+1)/2:")
    for key, val in rep.items():
        print(f"    {key:<24} {val}")
    print()

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. Terras bijection holds for the standard map (the exploitable 2-adic structure)
    check("terras_bijection_standard", all(terras_injective(STD_COLLATZ, k) for k in (1, 4, 8, 11)),
          "(n mod 2^k) → k-step parity vector is bijective — the structure forward iteration hides")

    # 2. stopping-time≤k density rises MONOTONICALLY toward 1 (almost all) — but never asserted to BE 1
    d3, d10, d14 = (stopping_density(STD_COLLATZ, k) for k in (3, 10, 14))
    check("stopping_density_monotone_rises", 0 < d3 <= d10 <= d14 < 1.0,
          f"stopping-time≤k density {d3:.3f} ≤ {d10:.3f} ≤ {d14:.3f} < 1 — monotone ↑ toward ALMOST ALL, stays < 1")

    # 3. drift is negative for standard Collatz = 0.5·ln(3/4); positive for the 5n+1 variant
    check("drift_sign_discriminates",
          abs(drift(STD_COLLATZ) - 0.5 * math.log(0.75)) < 1e-12 and drift(STD_COLLATZ) < 0 < drift(FIVE_N_1),
          f"std drift={drift(STD_COLLATZ):.4f}<0 (supermartingale); 5n+1 drift={drift(FIVE_N_1):.4f}>0 (no convergence heuristic)")

    # 4. the drift heuristic is DECLARED, not a proof — the report says so and keeps the universal OPEN
    check("heuristic_not_proof",
          "heuristic" in rep["log_drift"][1].lower() and rep["universal_all_n"].startswith("OPEN"),
          "negative drift ⇏ proof; the universal 'all n' is reported OPEN, never upgraded")

    # 5. inverse basin is a finite enumeration that reconciles members but not universality
    basin = inverse_basin([1], STD_COLLATZ, 12)
    check("inverse_basin_finite_reconciles",
          1 in basin and 5 in basin and 16 in basin and len(basin) < 10 ** 9,
          f"basin from 1 (depth 12) reconciles its {len(basin)} members (1,5,16,… present); universality NOT established")

    # 6. a map LACKING the structure is detected (discrimination, not assumption)
    no_struct = (2, {0: (1, 0, 1), 1: (1, 0, 1)})   # identity map: branch vector all-same → not injective for k>1
    check("detects_missing_structure", not terras_injective(no_struct, 3),
          "a map with no real branching fails the Terras-injectivity test — structure is verified, not assumed")

    # 7. THE no-upgrade discipline: the report NEVER claims the conjecture proved
    blob = " ".join(str(v) for v in rep.values()).lower()
    check("no_universal_upgrade",
          "open" in rep["universal_all_n"].lower() and "proved" not in blob and "solved" not in blob,
          "no field claims the conjecture proved/solved; only density/almost-all + a named residual")

    print(f"\n  {passed}/{total} checks. The structural tests turn a chaotic forward walk into a CORNERED residual:")
    print("  the 2-adic bijection + negative drift give density-1 / almost-all convergence (MEASURED), and the")
    print("  universal 'all n' stays OPEN — the uncertainty is named (measure-zero exceptional set + possible")
    print("  cycles + possible divergent orbit), not eliminated. `density 1 ≠ all`; `expected ≠ worst case`;")
    print("  `heuristic ≠ proof`. This works because Collatz HAS the algebraic structure SHA-256 removes by design.")
    assert passed == total, "collatz_reconcile failed its own self-test"


if __name__ == "__main__":
    main()
