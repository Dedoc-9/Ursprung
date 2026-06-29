# SPDX-License-Identifier: AGPL-3.0-only
"""
test_dvsm_reference.py — the reference is deterministic, bounded, read-only in its diagnostics, and it
faithfully carries the κ skew-symmetry GHOST. Validity-not-outcome. Pure-stdlib.

  1. determinism            — same seed ⇒ identical hash sequence (reproducibility, not correctness).
  2. empirical_boundedness  — a clean run keeps ‖Z‖ < U_MAX (EMPIRICAL; not a certified bound).
  3. kappa_ghost_present    — the actual κ init is NOT skew-symmetric (max|κ+κᵀ| > 0.1): the ghost is real.
  4. contamination_changes  — planting a forbidden coupling changes the trajectory (the knob does something).
  5. records_finite         — every StepRecord field is finite (no NaN/inf leaking into telemetry).

`reference-model ≠ authoritative-kernel`: everything asserted is about THIS reduced reference.
"""
from __future__ import annotations

import math

from dvsm_reference import (DvsmReference, kappa_matrix, gen_clean, gen_contaminated, U_MAX, R, StepRecord)
from dataclasses import fields


def chk(name, ok, detail):
    return (name, ok, detail)


def test_determinism():
    a = [r.hash for r in DvsmReference(seed=7).run(500)]
    b = [r.hash for r in DvsmReference(seed=7).run(500)]
    return chk("determinism", a == b, f"hash sequences identical: {a == b}")


def test_empirical_boundedness():
    en = [r.energy for r in gen_clean(3000)]
    ok = max(en) < U_MAX
    return chk("empirical_boundedness", ok, f"max‖Z‖={max(en):.3f} < U_MAX={U_MAX} (EMPIRICAL only)")


def test_kappa_ghost_present():
    k = kappa_matrix(R)
    skew = max(abs(k[i][j] + k[j][i]) for i in range(R) for j in range(R))
    ok = skew > 0.1
    return chk("kappa_ghost_present", ok, f"max|κ+κᵀ|={skew:.3f} (claimed skew-symmetric; it is not)")


def test_contamination_changes():
    clean = [r.v0_next for r in gen_clean(1500, seed=2)]
    dirty = [r.v0_next for r in gen_contaminated("omega_to_v", 1500, seed=2)]
    ok = clean != dirty
    return chk("contamination_changes", ok, f"planted Ω→V alters v trajectory: {ok}")


def test_records_finite():
    bad = []
    for r in gen_clean(800):
        for f in fields(StepRecord):
            v = getattr(r, f.name)
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                bad.append((r.t, f.name))
    return chk("records_finite", not bad, f"non-finite fields: {bad[:3] or 'none'}")


def main():
    results = [
        test_determinism(),
        test_empirical_boundedness(),
        test_kappa_ghost_present(),
        test_contamination_changes(),
        test_records_finite(),
    ]
    print("test_dvsm_reference — reduced DVSM reference (deterministic, bounded, ghost-faithful)\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. reference-model ≠ authoritative-kernel; integrity ≠ truth.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
