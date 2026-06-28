# SPDX-License-Identifier: AGPL-3.0-only
"""
trapping_certificate.py — the continuous analog of the inductive `ConstraintCertificate` (verify/certificate_
compiler.py), applied to boundedness of a flow.

A positively-invariant ("trapping") region is the continuous version of "Inv closed under T": pick a
Lyapunov-like `V(s)`; if `dV/dt < 0` everywhere outside a ball of radius R, then no trajectory can leave that
ball — boundedness proven by a LOCAL boundary condition, with NO trajectory integrated. This is where the
verify-cheaper-than-simulate asymmetry is real: checking the certificate is a max over a sphere; finding the
bounded set otherwise is unbounded integration. `verify ≠ simulate`.

THE HONEST FINDING (this is the point). For the Halvorsen field the natural candidate `V = x²+y²+z²` is
**REJECTED**: `dV/dt = 2⟨s, f(s)⟩` contains the cubic term `-2(xy²+yz²+zx²)`, which is NOT sign-definite, so for
large ‖s‖ there are directions with `dV/dt ≥ 0`. The checker returns a concrete witness — it refuses to certify
boundedness with an inadequate V, EVEN THOUGH the attractor is empirically bounded (see invariant_audit.py).
`empirical-boundedness ≠ certified-boundedness`; `integrity ≠ truth`. A genuine certificate needs a
higher-degree V / non-ball region (sum-of-squares or interval methods) — **PLAUSIBLE-UNVERIFIED / OPEN**.

GRADING:
  • The checker (and its rejection of a bad V with a witness): **DEMONSTRATED**.
  • A `CERTIFIED` verdict here = "no violation found over the sampled directions" — sampling, **not a proof**;
    rigor needs interval arithmetic / SOS. The positive case is shown on a toy contracting field.
  • Auto-deriving a valid V for Halvorsen: **OPEN**. `checking ≠ finding`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Optional

from flow import field, dot, scale, norm, A


def dVdt_quadratic(s, field_fn: Callable, a: float) -> float:
    """For V(s)=‖s‖², dV/dt = ⟨∇V, f⟩ = 2⟨s, f(s)⟩."""
    return 2.0 * dot(s, field_fn(s, a))


def _fib_sphere(n: int):
    """Deterministic near-uniform unit directions (Fibonacci sphere) — no RNG, fully reproducible."""
    out = []
    ga = math.pi * (1 + 5 ** 0.5)
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n
        r = max(0.0, 1 - z * z) ** 0.5
        th = ga * i
        out.append((r * math.cos(th), r * math.sin(th), z))
    return out


@dataclass(frozen=True)
class TrappingResult:
    certified: bool
    witness: Optional[tuple]          # a state with ‖s‖>R and dV/dt ≥ 0 (a counterexample), if rejected
    max_dVdt: float                   # worst (largest) dV/dt found outside R; certified ⇒ < 0
    radii: tuple
    n_dirs: int


def certify_ball(field_fn: Callable, a: float = A, R: float = 8.0, n_dirs: int = 600,
                 radii_mult=(1.0, 2.0, 4.0)) -> TrappingResult:
    """Check whether V=‖s‖² certifies the ball of radius R as positively invariant: dV/dt < 0 on every sampled
    point with ‖s‖ ≥ R. Returns a witness if any sampled point has dV/dt ≥ 0 (⇒ NOT certified by this V)."""
    dirs = _fib_sphere(n_dirs)
    worst = -math.inf
    witness = None
    radii = tuple(R * m for m in radii_mult)
    for rad in radii:
        for u in dirs:
            s = scale(u, rad)
            d = dVdt_quadratic(s, field_fn, a)
            if d > worst:
                worst = d
                if d >= 0:
                    witness = s
    return TrappingResult(witness is None, witness, worst, radii, n_dirs)


# a toy contracting field where V=‖s‖² IS a valid trapping certificate (the positive case)
def contracting_field(s, a: float = A):
    return (-s[0], -s[1], -s[2])


def main():
    print("trapping_certificate.py — boundedness as a continuous inductive certificate (honest)\n")
    hal = certify_ball(field, A, R=8.0)
    print(f"  Halvorsen, V=‖s‖²:   certified={hal.certified}  max dV/dt outside R = {hal.max_dVdt:.1f}")
    if hal.witness:
        print(f"     witness (‖s‖>R, dV/dt≥0): {tuple(round(c,2) for c in hal.witness)}  ‖s‖={norm(hal.witness):.1f}")
    toy = certify_ball(contracting_field, A, R=1.0)
    print(f"  contracting toy, V=‖s‖²: certified={toy.certified}  max dV/dt outside R = {toy.max_dVdt:.1f}")
    print("\n  the quadratic-V ball does NOT certify Halvorsen boundedness (cubic term breaks dV/dt<0) — the")
    print("  checker refuses with a witness, though the attractor IS empirically bounded. A valid certificate")
    print("  needs SOS/interval methods (OPEN). empirical-boundedness ≠ certified-boundedness; integrity ≠ truth.")


if __name__ == "__main__":
    main()
