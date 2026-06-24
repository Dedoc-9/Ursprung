# SPDX-License-Identifier: AGPL-3.0-only
"""
verified_improvement_theorem.py — the formal endpoint of the RSI arc, as an executable proof-check.

THEOREM (verified self-improvement is a branching process).
Model the stream of VERIFIED self-edits — edits that pass external + replicated + calibrated checks — as a
Bienaymé–Galton–Watson branching process: each verified edit independently produces a random number of verified
successor edits with mean `m` (the expected verified edits generated per verified edit) and offspring generating
function f(s) = Σ_k p_k s^k. Then the classical extinction criterion applies:

   (1) m ≤ 1 (non-degenerate)  ⇒  the verified-improvement stream goes extinct with probability 1.
                                   Recursion is IMPOSSIBLE — independent of self-modification power or compute.
   (2) m > 1                   ⇒  the stream survives with probability 1 − q, where q is the smallest fixed point
                                   of f in [0,1]; since q > 0 in general, survival is never certain for one run.

Two riders the rest of the stack forces:
   (3) m must be the VERIFIED mean. The proxy mean m̂ can exceed 1 while m ≤ 1 — that is exactly the runaway:
       it looks self-sustaining and still goes extinct. `m̂ > 1 ≥ m` is the formal signature of self-deception.
   (4) Open-endedness is ASYMPTOTIC: no finite trajectory proves it; the strongest finite evidence is
       "supercritical and surviving after N".

Corollary (measured): in the toy domain `rsi_engine` / `transfer_robustness` operate on, m < 1 (subcritical), so
the observed single-promotion plateau is almost-sure extinction, not a tuning artifact.

This file VERIFIES the theorem rather than asserts it: a Monte-Carlo branching simulation (Poisson offspring,
f(s)=exp(m(s−1))) is checked against the analytic extinction fixed point across sub/critical/supercritical
regimes, and the proxy>1≥verified runaway is demonstrated directly. The branching mathematics is classical; the
self-tests confirm the simulator reproduces it (validity), not that a hoped outcome occurred.

Run (from this directory):  PYTHONHASHSEED=0 python3 verified_improvement_theorem.py
"""
from __future__ import annotations

import math
import random

N_TRIALS = 4000
G_MAX = 160
POP_CAP = 300          # if a generation exceeds this, the line has clearly survived (supercritical explosion)
LAM_CAP = 700          # guard: Knuth Poisson underflows for lambda beyond ~745; treat as survival


def poisson(rng, lam):
    """Knuth's algorithm. (Sum of `pop` iid Poisson(m) is Poisson(pop*m), so one draw advances a whole generation.)"""
    L = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= L:
            return k - 1


def extinct_by_GMAX(rng, m):
    """Simulate one verified-edit lineage from a single root. Returns True iff it dies out within G_MAX gens."""
    pop = 1
    for _ in range(G_MAX):
        if pop == 0:
            return True
        if pop > POP_CAP or pop * m >= LAM_CAP:
            return False                          # exploded — surviving
        pop = poisson(rng, pop * m)               # next generation = Poisson(pop * m)
    return pop == 0


def empirical_extinction(m, seed, trials=N_TRIALS):
    rng = random.Random(seed)
    return sum(1 for _ in range(trials) if extinct_by_GMAX(rng, m)) / trials


def analytic_extinction(m, iters=20000):
    """Smallest fixed point q in [0,1] of q = f(q) = exp(m(q−1)) for Poisson offspring (extinction probability)."""
    q = 0.0
    for _ in range(iters):
        q = math.exp(m * (q - 1.0))
    return q


def main():
    print("verified_improvement_theorem — verified self-improvement is a branching process (extinction criterion).")
    print("THEOREM: verified mean m ≤ 1 ⇒ a.s. extinction; m > 1 ⇒ survives w.p. 1−q. proxy m̂>1≥m = the runaway.\n")

    regimes = [0.8, 1.0, 1.5, 2.0]
    print(f"   {'m (verified mean)':>18}{'analytic q':>12}{'empirical ext.':>16}{'survival':>11}   class")
    data = {}
    for m in regimes:
        q = analytic_extinction(m)
        e = empirical_extinction(m, seed=20260623 + int(m * 100))
        cls = "subcritical" if m < 1 else ("critical" if m == 1 else "supercritical")
        data[m] = (q, e)
        print(f"   {m:>18.2f}{q:>12.3f}{e:>16.3f}{1 - e:>11.3f}   {cls}"
              + ("  <- stream can persist" if m > 1 else "  <- stream dies out"))

    # the runaway: proxy mean > 1 (looks self-sustaining) but verified mean ≤ 1 (actually extinct)
    m_proxy, pass_rate = 2.0, 0.40
    m_verified = m_proxy * pass_rate                      # 0.80 — only 40% of proxy "improvements" verify
    ext_proxy = empirical_extinction(m_proxy, seed=777)
    ext_verified = empirical_extinction(m_verified, seed=778)
    print(f"\n  runaway demonstration: proxy m̂={m_proxy:.2f} (ext {ext_proxy:.3f}, SURVIVES) but only "
          f"{pass_rate:.0%} verify ⇒ verified m={m_verified:.2f} (ext {ext_verified:.3f}, DIES).")
    print("  the proxy stream looks like recursive self-improvement; the verified stream is subcritical. m̂>1≥m.\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. the simulation produced an extinction estimate and analytic q for every regime
    check("theorem_swept_all_regimes", set(data) == set(regimes) and all(0 <= v[1] <= 1 for v in data.values()),
          "extinction measured + analytic q computed for sub/critical/supercritical m")

    # 2. subcritical (m<1): extinction → 1 (the stream dies almost surely)
    check("subcritical_extincts", data[0.8][1] >= 0.95,
          f"m=0.8 empirical extinction {data[0.8][1]:.3f} ≈ 1 — verified improvement dies out")

    # 3. critical (m=1): extinction → 1 as well (slowly; still almost sure)
    check("critical_extincts", data[1.0][1] >= 0.90,
          f"m=1.0 empirical extinction {data[1.0][1]:.3f} ≈ 1 — critical also dies (just slower)")

    # 4. supercritical (m>1): empirical extinction matches the analytic fixed point q, and survival is positive
    ok4 = all(abs(data[m][1] - data[m][0]) <= 0.05 for m in (1.5, 2.0)) and (1 - data[2.0][1]) > 0.05
    check("supercritical_matches_fixed_point", ok4,
          f"m=2.0: empirical {data[2.0][1]:.3f} vs analytic q {data[2.0][0]:.3f}; survival {1-data[2.0][1]:.3f} > 0")

    # 5. the criterion itself: q is a genuine fixed point of f, and q=1 iff m≤1 (the extinction threshold)
    fixed_ok = all(abs(data[m][0] - math.exp(m * (data[m][0] - 1))) < 1e-6 for m in regimes)
    threshold_ok = all((data[m][0] > 0.999) == (m <= 1.0) for m in regimes)
    check("extinction_criterion_correct", fixed_ok and threshold_ok,
          "q = f(q) for every m, and q=1 ⇔ m≤1 — the m=1 critical threshold is exact")

    # 6. the runaway: proxy m̂>1 survives while verified m≤1 dies (self-deception, quantified)
    check("proxy_exceeds_verified_runaway", ext_proxy < 0.5 and ext_verified >= 0.95,
          f"proxy m̂=2.0 survives (ext {ext_proxy:.3f}) but verified m=0.8 dies (ext {ext_verified:.3f}) — m̂>1≥m")

    # 7. determinism: same seed ⇒ identical estimate (the measurement is reproducible)
    check("deterministic", empirical_extinction(1.5, seed=42, trials=500) == empirical_extinction(1.5, seed=42, trials=500),
          "seeded Monte-Carlo extinction estimate is reproducible")

    print(f"\n  {passed}/{total} checks. The simulator reproduces the Bienaymé–Galton–Watson extinction criterion,")
    print("  so the theorem is verified, not asserted: a verified-improvement stream with mean m ≤ 1 goes extinct")
    print("  almost surely (recursion impossible), m > 1 survives with probability 1−q (never certain per run), and")
    print("  a proxy mean above 1 with a verified mean below 1 is the runaway — it looks recursive and dies. RSI")
    print("  reduces to: is the VERIFIED branching mean > 1, robustly, with m itself externally estimated?")
    print("  `optimize ≠ evaluate`; `confidence ≠ capability`; open-endedness stays asymptotic — proved only 'after N'.")
    assert passed == total, "verified_improvement_theorem failed its own (theorem-validation) self-test"


if __name__ == "__main__":
    main()
