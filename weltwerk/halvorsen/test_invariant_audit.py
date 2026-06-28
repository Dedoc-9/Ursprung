# SPDX-License-Identifier: AGPL-3.0-only
"""
test_invariant_audit.py — MEASURED invariants + chaos-ghost audit (validity-not-outcome). Pure-stdlib.
(Numerically heavier — integration loops; ~tens of seconds.)

  1. lyapunov_positive        — λ_max > 0 (the system is chaotic), measured by Benettin.
  2. lyapunov_sign_robust     — the SIGN of λ_max is the same at dt and dt/2 (integrator-robust).
  3. dissipation              — ∇·f = -3a exactly; the numerical average reproduces it.
  4. fp_ghost                 — ε-different inputs diverge (amplification ≫ 1, rate > 0): the determinism ≠
                               reproducibility ghost, classified as sensitive-dependence.
  5. measures_agree_paths_diverge — two integrators agree on λ_max sign + dissipation but their PATHS diverge.
  6. determinism              — λ_max is reproducible for fixed inputs.

Sound iff 6/6: chaos is measured and integrator-robust in sign, dissipation matches the exact invariant, the
FP ghost is sensitive-dependence (not a defect), and differential testing works on MEASURES not PATHS.
`agreement-on-measure ≠ agreement-on-path`; `determinism ≠ reproducibility`; `measure ≠ cite-authority`.

Run:  python3 test_invariant_audit.py
"""
from __future__ import annotations

from invariant_audit import (lyapunov_max, dissipation_numeric, fp_divergence,
                             measures_agree_paths_diverge)
from flow import divergence, A


def chk(name, ok, detail):
    return (name, ok, detail)


def test_lyapunov_positive():
    lam = lyapunov_max()
    return chk("lyapunov_positive", lam > 0.2, f"λ_max ≈ {lam:.3f} (> 0 ⇒ chaotic)")


def test_lyapunov_sign_robust():
    a, b = lyapunov_max(dt=0.01), lyapunov_max(dt=0.005)
    return chk("lyapunov_sign_robust", a > 0 and b > 0, f"λ(dt)={a:.3f}, λ(dt/2)={b:.3f} (both > 0)")


def test_dissipation():
    num = dissipation_numeric()
    ok = abs(divergence(A) - (-4.2)) < 1e-12 and abs(num - (-4.2)) < 0.1
    return chk("dissipation", ok, f"∇·f=-4.2 (exact); numeric avg={num:.4f}")


def test_fp_ghost():
    g = fp_divergence()
    ok = g.amplification > 100 and g.rate > 0
    return chk("fp_ghost", ok, f"amplification={g.amplification:.1e} rate={g.rate:.3f} λ={g.lyap:.3f}")


def test_measures_agree_paths_diverge():
    m = measures_agree_paths_diverge()
    ok = m["lyap_sign_agree"] and m["dissipation_agree"] and m["path_separation_at_T"] > 1.0
    return chk("measures_agree_paths_diverge", ok,
               f"sign_agree={m['lyap_sign_agree']} dissip_agree={m['dissipation_agree']} "
               f"path_sep={m['path_separation_at_T']:.2f}")


def test_determinism():
    ok = lyapunov_max() == lyapunov_max()
    return chk("determinism", ok, f"λ_max reproducible: {ok}")


def main():
    results = [test_lyapunov_positive(), test_lyapunov_sign_robust(), test_dissipation(),
              test_fp_ghost(), test_measures_agree_paths_diverge(), test_determinism()]
    print("test_invariant_audit — MEASURED invariants + chaos ghost audit\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: chaos measured + integrator-robust in sign; "
          f"dissipation matches the\n  exact invariant; the FP ghost is sensitive-dependence; differential works "
          f"on MEASURES not PATHS.\n  agreement-on-measure ≠ agreement-on-path; determinism ≠ reproducibility.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
