# SPDX-License-Identifier: AGPL-3.0-only
"""
discrete_certificate.py — a SOUND, NARROW, checkable discrete-time stability certificate for the corrected
DVSM Lie step, plus the corrected (hollow-skew κ) reference kernel it certifies. NOT a blanket "proven safe":
it is a sufficient condition with an explicit boundary. `certificate ≠ proof-of-everything`; `grade ≠ truth`.

THE MAP (decoupled Z dynamics, fixed S — explicit Euler):
    Z' = Z + dt·([Z,S]_κ − λZ),   [Z,S]_κ,k = Σ_j κ_kj (Z_k S_j − Z_j S_k)
The bracket is linear in Z: [Z,S]_κ = M(S)·Z with M(S) = diag(κS) − diag(S)κ. Hence
    Z' = [(1 − dtλ)I + dt·M(S)]·Z,   so   ‖Z'‖ ≤ (1 − dtλ + dt·‖M(S)‖)·‖Z‖   for dtλ ≤ 1.

THE CERTIFICATE (closed-form sufficient condition for contraction ‖Z'‖ ≤ ρ‖Z‖, ρ<1):
    ‖M(S)‖₂ ≤ ‖M(S)‖_F ≤ 2·‖κ‖_F·‖S‖₂   (a provable Frobenius bound).
    With σ = sup‖S‖₂, the condition is   2·‖κ‖_F·σ < λ   and   0 < dtλ ≤ 1,
    giving the contraction factor   ρ = 1 − dt·(λ − 2‖κ‖_F·σ) ∈ [0,1).
The admissible noise margin is  σ_max = λ / (2·‖κ‖_F).

WHY THE κ FIX MATTERS: antisymmetrization `κ ← (κ−κᵀ)/2` is an orthogonal projection in the Frobenius inner
product, so `‖κ_skew‖_F ≤ ‖κ_sin‖_F` (strict when κ is not already skew). A smaller ‖κ‖_F WIDENS the margin
σ_max, so the corrected κ certifies on strictly more operating regimes than the broken `sin(...)` κ. The fix
is not cosmetic — it is the precondition that makes this certificate satisfiable.

DOES NOT SHOW (the honest boundary): behavior for ‖S‖ > σ; the fixed-point CLAMPS in the shipped kernel; the
full coupled Z–S–W system; anything outside explicit-Euler with these parameters. `bounded-here ≠ safe-everywhere`.
"""
from __future__ import annotations

import math
import os
import random
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))
from dvsm_reference import kappa_matrix, R                          # noqa: E402  (broken κ = sin(...))
from kappa_remediation import kappa_skew                            # noqa: E402  (remediated κ)
from invariant_ledger import ObligationResult, CLOSED, BOUNDED, UNDERDETERMINED  # noqa: E402

Matrix = List[List[float]]
Vec = List[float]


def frob(m: Matrix) -> float:
    return math.sqrt(sum(x * x for row in m for x in row))


def _matvec(m: Matrix, v: Vec) -> Vec:
    return [sum(m[k][j] * v[j] for j in range(len(v))) for k in range(len(m))]


def step(z: Vec, s: Vec, kappa: Matrix, lam: float, dt: float) -> Vec:
    """One decoupled corrected Lie step: Z' = (1−dtλ)Z + dt·M(S)Z, M(S)Z = diag(κS)Z − diag(S)(κZ)."""
    kz = _matvec(kappa, z)
    a = _matvec(kappa, s)  # κS
    mz = [a[k] * z[k] - s[k] * kz[k] for k in range(len(z))]
    return [(1.0 - dt * lam) * z[k] + dt * mz[k] for k in range(len(z))]


def _norm(v: Vec) -> float:
    return math.sqrt(sum(x * x for x in v))


def sigma_max(kappa: Matrix, lam: float) -> float:
    """The admissible ‖S‖ margin: σ_max = λ / (2‖κ‖_F)."""
    f = frob(kappa)
    return float("inf") if f == 0.0 else lam / (2.0 * f)


def certify(kappa: Matrix, lam: float, dt: float, sigma: float, *, samples: int = 2000, seed: int = 0) -> dict:
    """Evaluate the certificate and cross-check it against measured worst-case growth."""
    f = frob(kappa)
    cond = (dt > 0.0) and (dt * lam <= 1.0) and (2.0 * f * sigma < lam)
    rho = 1.0 - dt * (lam - 2.0 * f * sigma)
    # measured: random unit Z, random S scaled to ‖S‖ = σ (the worst case the bound assumes)
    rng = random.Random(seed)
    n = len(kappa)
    max_ratio = 0.0
    for _ in range(samples):
        z = [rng.gauss(0, 1) for _ in range(n)]
        zn = _norm(z)
        if zn == 0:
            continue
        z = [x / zn for x in z]
        s = [rng.gauss(0, 1) for _ in range(n)]
        sn = _norm(s)
        s = [x / sn * sigma for x in s] if sn > 0 else [0.0] * n
        ratio = _norm(step(z, s, kappa, lam, dt))  # ‖Z'‖ / ‖Z‖ with ‖Z‖=1
        if ratio > max_ratio:
            max_ratio = ratio
    decision = "CONTRACTIVE_CERT" if (cond and max_ratio <= 1.0 + 1e-9) else "NOT_CERTIFIED"
    return {
        "frob": f, "cond": cond, "rho": rho, "sigma": sigma, "sigma_max": sigma_max(kappa, lam),
        "max_ratio": max_ratio, "decision": decision,
    }


def as_obligation(result: dict) -> ObligationResult:
    if result["decision"] == "CONTRACTIVE_CERT":
        status, stmt = CLOSED, "the discrete Lie step contracts ‖Z‖ under the certificate condition"
    elif result["cond"]:
        status, stmt = BOUNDED, "the condition holds but measured worst-case growth was not below 1 (sampling)"
    else:
        status, stmt = UNDERDETERMINED, "the sufficient condition 2‖κ‖_F·σ < λ (with dtλ≤1) is not satisfied"
    return ObligationResult(
        "discrete_contraction", stmt, status,
        f"2‖κ‖_F·σ={2 * result['frob'] * result['sigma']:.4f} vs λ; ρ={result['rho']:.4f}; "
        f"measured max‖Z'‖={result['max_ratio']:.4f}; σ_max={result['sigma_max']:.4f}",
        "stability for ‖S‖>σ, the fixed-point clamps, or the full coupled Z–S–W system — a SUFFICIENT "
        "condition, not a global proof",
        "a sampled max‖Z'‖ exceeding the analytic ρ (would falsify the bound), or growth within the certified σ")


def main():
    print("discrete_certificate — sound, narrow contraction certificate for the corrected DVSM Lie step\n")
    lam, dt = 0.5, 0.1
    k_sin = kappa_matrix(R)
    k_skew = kappa_skew(R)
    sm_sin, sm_skew = sigma_max(k_sin, lam), sigma_max(k_skew, lam)
    print(f"  ‖κ_sin‖_F={frob(k_sin):.4f}  σ_max(sin)={sm_sin:.4f}")
    print(f"  ‖κ_skew‖_F={frob(k_skew):.4f}  σ_max(skew)={sm_skew:.4f}   (fix widens the margin: {sm_skew > sm_sin})")
    sigma = (sm_sin + sm_skew) / 2.0  # between the two margins
    rs = certify(k_skew, lam, dt, sigma)
    rn = certify(k_sin, lam, dt, sigma)
    print(f"\n  at σ={sigma:.4f}:")
    print(f"    skew κ : {rs['decision']}  (ρ={rs['rho']:.4f}, measured max‖Z'‖={rs['max_ratio']:.4f})")
    print(f"    sin  κ : {rn['decision']}  (measured max‖Z'‖={rn['max_ratio']:.4f})")
    print("\n  the κ fix is the precondition: the corrected κ certifies where the broken κ does not.")
    print("  certificate ≠ proof-of-everything; SUFFICIENT condition with an explicit boundary.")


if __name__ == "__main__":
    main()
