# SPDX-License-Identifier: AGPL-3.0-only
"""
kappa_remediation.py — the κ fix, as audit + remediation + measured proof-it-closes.

The DVSM kernel initializes the Lie-coupling tensor as κ[k,j] = sin(k·1.37 − j·1.73). That matrix is neither
HOLLOW (the diagonal sin(−0.36·k) ≠ 0) nor SKEW-symmetric (skew would need 1.37 = 1.73) — which is the
VIOLATED obligation `invariant_ledger.obl_kappa_skew` already records. The energy law `d‖Z‖²/dt = −2λ‖Z‖²`
leans on κ being skew; a non-skew κ breaks the premise.

The remediation is one operator: antisymmetrize, `κ ← (κ − κᵀ)/2`. This is **hollow and skew by
construction** (diagonal cancels; `κ[j,i] = −κ[i,j]`), so the skew residual `max|κ+κᵀ|` is exactly 0.

We keep BOTH side by side: the audit of the broken upstream κ (VIOLATED) and the remediated κ (CLOSED). The
auditor still tells the truth about the shipped kernel; the fix is offered and *measured*, not asserted.
`claimed-skew ≠ actual-skew`, until you antisymmetrize — then `code-skew = claimed-skew`, and it is checked.
"""
from __future__ import annotations

import os
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))
from dvsm_reference import kappa_matrix, R                          # noqa: E402  (the broken κ = sin(...))
from invariant_ledger import ObligationResult, CLOSED, VIOLATED, obl_kappa_skew  # noqa: E402

Matrix = List[List[float]]


def antisymmetrize(m: Matrix) -> Matrix:
    """κ ← (κ − κᵀ)/2 — the hollow, skew-symmetric part of any square matrix."""
    n = len(m)
    return [[(m[i][j] - m[j][i]) / 2.0 for j in range(n)] for i in range(n)]


def kappa_skew(r: int = R) -> Matrix:
    """The remediated coupling: the antisymmetrized DVSM κ."""
    return antisymmetrize(kappa_matrix(r))


def skew_residual(m: Matrix) -> float:
    n = len(m)
    return max(abs(m[i][j] + m[j][i]) for i in range(n) for j in range(n))


def hollow_residual(m: Matrix) -> float:
    return max(abs(m[i][i]) for i in range(len(m)))


def obl_kappa_skew_remediated(r: int = R) -> ObligationResult:
    """The remediated κ satisfies the skew obligation: max|κ+κᵀ| = 0 (and hollow)."""
    k = kappa_skew(r)
    sres = skew_residual(k)
    hres = hollow_residual(k)
    status = CLOSED if (sres < 1e-12 and hres < 1e-12) else VIOLATED
    return ObligationResult(
        "kappa_skew_remediated",
        "the antisymmetrized κ = (κ−κᵀ)/2 is hollow and skew-symmetric",
        status,
        f"max|κ+κᵀ|={sres:.2e}, max|diag|={hres:.2e}  (0 ⇒ hollow + skew, by construction)",
        "that the SHIPPED upstream kernel uses this κ — only that the remediated matrix satisfies the premise",
        "an entry where κ[i,j] + κ[j,i] ≠ 0 after antisymmetrization (a coding error in the remediation)")


def audit(r: int = R):
    """Return (original-audit, remediated) side by side: the broken κ stays VIOLATED, the fix is CLOSED."""
    return obl_kappa_skew(r), obl_kappa_skew_remediated(r)


def main():
    print("kappa_remediation — audit of the broken κ + the antisymmetrized fix\n")
    orig, fixed = audit()
    print(f"  [{orig.status:9s}] {orig.id:24s} {orig.witness}")
    print(f"  [{fixed.status:9s}] {fixed.id:24s} {fixed.witness}")
    print("\n  the fix is one operator (κ ← (κ−κᵀ)/2); the obligation flips VIOLATED → CLOSED, measured.")
    print("  claimed-skew ≠ actual-skew (upstream) → code-skew = claimed-skew (remediated).")


if __name__ == "__main__":
    main()
