# SPDX-License-Identifier: AGPL-3.0-only
"""
test_kappa_remediation.py — the audit still flags the broken κ, and the antisymmetrized κ closes the
obligation (hollow + skew, by construction). Validity-not-outcome.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))

from kappa_remediation import (antisymmetrize, kappa_skew, skew_residual, hollow_residual,
                               obl_kappa_skew_remediated, audit)
from dvsm_reference import kappa_matrix, R


def chk(name, ok, detail):
    return (name, ok, detail)


def test_original_violated():
    orig, _fixed = audit()
    return chk("original_violated", orig.status == "VIOLATED", f"status={orig.status}")


def test_remediated_closed():
    o = obl_kappa_skew_remediated()
    return chk("remediated_closed", o.status == "CLOSED", f"status={o.status} witness={o.witness}")


def test_skew_is_hollow_and_antisymmetric():
    k = kappa_skew(R)
    sres, hres = skew_residual(k), hollow_residual(k)
    return chk("skew_hollow_antisym", sres < 1e-12 and hres < 1e-12, f"skew={sres:.1e} hollow={hres:.1e}")


def test_antisymmetrize_reduces_or_keeps_frob():
    import math
    fro = lambda m: math.sqrt(sum(x * x for row in m for x in row))
    k_sin = kappa_matrix(R)
    k_skew = antisymmetrize(k_sin)
    # antisymmetrization is an orthogonal projection ⇒ never increases Frobenius norm; strict here (κ not skew)
    return chk("frob_not_increased", fro(k_skew) < fro(k_sin) + 1e-12, f"skew={fro(k_skew):.3f} sin={fro(k_sin):.3f}")


def main():
    results = [
        test_original_violated(),
        test_remediated_closed(),
        test_skew_is_hollow_and_antisymmetric(),
        test_antisymmetrize_reduces_or_keeps_frob(),
    ]
    print("test_kappa_remediation — audit (VIOLATED) + remediation (CLOSED)\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. claimed-skew ≠ actual-skew → fixed: code-skew = claimed-skew.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
