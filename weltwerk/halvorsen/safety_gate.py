# SPDX-License-Identifier: AGPL-3.0-only
"""
safety_gate.py — the edge safety gate, as a HONEST two-part job.

  PART A (this file, BUILT & tested): the MECHANISM. Given a trapping certificate, membership in the certified
  region is a single O(1) check (one V-evaluation), so an edge controller can refuse any move that would leave
  the safe set WITHOUT running a forward trajectory simulation. The gate is wired through `require_grounded`:
  a next-state is committed only if it is `Grounded` by `InsideCertifiedRegion`. `verify ≠ simulate`.

  PART B (OPEN, NOT in this file): a SOUND certificate. The guarantee holds ONLY if the certificate is valid.
  For the Halvorsen attractor the quadratic-V ball is REJECTED (`trapping_certificate.certify_ball`), so there
  is no sound certificate here yet — obtaining one needs higher-degree V via SOS / interval arithmetic. Until
  Part B exists, the gate is **fail-closed**: with an uncertified certificate it refuses EVERY move (no safety
  ⇒ no permission). `unsound-certificate ≠ safety`; `integrity ≠ truth`.

So this module delivers the enforcement mechanism and makes the missing piece impossible to ignore: run it on
Halvorsen and it correctly permits nothing; run it on a system that HAS a sound certificate (a contracting
toy) and it permits inside-region moves at O(1) cost.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field as dc_field
from typing import List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
from epistemic_types import Grounded, Grounding, UngroundedError, require_grounded   # noqa: E402
from trapping_certificate import certify_ball, contracting_field                     # noqa: E402
from flow import field, norm, A                                                      # noqa: E402


@dataclass(frozen=True)
class TrappingCertificate:
    """A trapping ball of radius R for V=‖s‖². `certified` MUST come from a sound check (here: certify_ball over
    sampled directions — itself sampling, not a proof; a rigorous gate would require an SOS/interval proof)."""
    name: str
    R: float
    certified: bool


def make_certificate(name: str, field_fn, a: float = A, R: float = 8.0) -> TrappingCertificate:
    r = certify_ball(field_fn, a, R)
    return TrappingCertificate(name, R, r.certified)


@dataclass(frozen=True)
class InsideCertifiedRegion:
    """Grounding proof: a state is safe iff the certificate is SOUND and the state lies inside the certified
    ball. An unsound certificate grounds NOTHING (fail-closed). This is the O(1) check — one norm, no simulation."""
    cert: TrappingCertificate
    state: tuple

    def is_grounded(self) -> bool:
        return self.cert.certified and norm(self.state) <= self.cert.R

    def label(self) -> str:
        return f"cert={self.cert.name} certified={self.cert.certified} ‖s‖={norm(self.state):.2f} (R={self.cert.R})"


@dataclass
class SafetyGate:
    """A control gate: a proposed next-state is committed only if grounded inside the certified region."""
    cert: TrappingCertificate
    committed: List = dc_field(default_factory=list)
    refused: int = 0

    @require_grounded("move")
    def _apply(self, move: "Grounded"):
        self.committed.append(move.value)
        return move.value

    def permit(self, next_state) -> bool:
        """Try to ground and commit a move. Returns False (refused, no commit) if not inside a sound region —
        the gate fail-closes when the certificate is unsound."""
        try:
            g = Grounded.ground(next_state, InsideCertifiedRegion(self.cert, next_state))
        except UngroundedError:
            self.refused += 1
            return False
        self._apply(move=g)
        return True


def membership_is_o1(cert: TrappingCertificate, state) -> bool:
    """The cheap check, made explicit: safety = (certified AND ‖s‖≤R). One norm evaluation, NO integration —
    the verify-cheaper-than-simulate asymmetry (valid only when `cert.certified`)."""
    return cert.certified and norm(state) <= cert.R


def main():
    print("safety_gate.py — edge safety gate (Part A mechanism; Part B sound certificate OPEN)\n")
    sound = make_certificate("contracting-toy", contracting_field, R=5.0)
    halv = make_certificate("halvorsen-quadV", field, R=8.0)
    print(f"  certificates: contracting certified={sound.certified} ; halvorsen certified={halv.certified}\n")

    g_sound = SafetyGate(sound)
    print(f"  SOUND cert: permit (0,0,1) [inside] → {g_sound.permit((0.0, 0.0, 1.0))}")
    print(f"              permit (10,0,0) [outside] → {g_sound.permit((10.0, 0.0, 0.0))}   refused={g_sound.refused}")

    g_halv = SafetyGate(halv)
    print(f"  HALVORSEN cert (REJECTED): permit (0,0,1) [inside] → {g_halv.permit((0.0, 0.0, 1.0))}  "
          f"(fail-closed: no sound certificate ⇒ nothing permitted)")
    print("\n  Part A works: O(1) membership replaces forward simulation WHEN the certificate is sound.")
    print("  Part B (a sound Halvorsen certificate via SOS/intervals) is OPEN. unsound-certificate ≠ safety.")


if __name__ == "__main__":
    main()
