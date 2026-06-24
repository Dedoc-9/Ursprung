# SPDX-License-Identifier: AGPL-3.0-only
"""
test_amplify.py — validity-not-outcome self-test for the amplifying-dynamics gate.

It proves the apparatus is sound; it does NOT assert sparse or dense — that is the experiment's outcome,
delivered by the bench. The load-bearing check is `divergence_within_cone`: even under chaos, divergence
cannot spread faster than the coupling (no superluminal causality) — if it did, the model or the cone
would be wrong and any sparsity number meaningless.

  1. determinism            — same params ⇒ identical trajectory (a CML is deterministic, no RNG)
  2. divergence_within_cone — ∀t the τ-diverged set ⊆ reachability ball radius t (causality bounded)
  3. non_vacuous            — the perturbation actually diverges somewhere (peak actual ≥ 1)
  4. sparsity_well_defined  — sparsity ∈ [0, 1] across the regime sweep

Run:  PYTHONHASHSEED=0 python3 test_amplify.py
"""
from __future__ import annotations

from amplify import cone, diverged, initial, measure, perturb, run

N, EPS, C, DELTA, TAU, H = 200, 0.25, 100, 1e-3, 1e-6, 60
RS = (2.8, 3.3, 3.5, 3.7, 3.9, 4.0)


def check(name, ok, detail):
    return (name, ok, detail)


def test_determinism():
    s0 = initial(N)
    a = run(s0, 3.9, EPS, H)
    b = run(s0, 3.9, EPS, H)
    return check("determinism", a == b, f"identical trajectory across runs (chaotic r): {a == b}")


def test_divergence_within_cone():
    ok = True
    for r in RS:
        s0 = initial(N)
        a = run(s0, r, EPS, H)
        b = run(perturb(s0, C, DELTA), r, EPS, H)
        ok = ok and all(diverged(a[t], b[t], TAU) <= cone(C, N, t) for t in range(H + 1))
    return check("divergence_within_cone", ok,
                 f"τ-divergence ⊆ reachability ball ∀t, ∀r (no superluminal spread): {ok}")


def test_non_vacuous():
    # at a chaotic r the perturbation must actually propagate (else the gate is vacuous)
    m = measure(N, 3.9, EPS, C, DELTA, TAU, H)
    return check("non_vacuous", m["peak_actual"] >= 1,
                 f"perturbation diverges (peak actual={m['peak_actual']}): {m['peak_actual'] >= 1}")


def test_sparsity_well_defined():
    ok = True
    for r in RS:
        m = measure(N, r, EPS, C, DELTA, TAU, H)
        ok = ok and (0.0 <= m["sparsity_vs_world"] <= 1.0)
    return check("sparsity_well_defined", ok, f"sparsity ∈ [0,1] across the sweep: {ok}")


def main():
    results = [
        test_determinism(),
        test_divergence_within_cone(),
        test_non_vacuous(),
        test_sparsity_well_defined(),
    ]
    print("test_amplify — validity-not-outcome (apparatus sound; verdict is the bench's)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: deterministic, causality bounded by the"
          f"\n  cone, the perturbation propagates, sparsity well-defined. Whether divergence stays SPARSE or"
          f"\n  goes DENSE as the gain rises is measured by amplify_bench — this test does not presume it.")
    assert passed == total, f"{total - passed} check(s) failed — the amplification gate is not sound"


if __name__ == "__main__":
    main()
