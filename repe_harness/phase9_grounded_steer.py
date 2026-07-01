# SPDX-License-Identifier: AGPL-3.0-only
"""phase9_grounded_steer.py — RepE Phase 9: type-gated steering chokepoint (a weltwerk Grounded[T] hardening).

Hardens Layer 2. Today the engine steers whenever probe > threshold. This layer makes a steering vector
UNCONSTRUCTABLE unless it carries a Grounding proof, so an ungrounded steer raises `UngroundedError` BEFORE any
activation is touched. Derived from `weltwerk/verify/epistemic_types.Grounded[T]`.

HONEST FRAMING (correcting the usual over-statement): this is a RUNTIME pre-effect guard, NOT a compile-time or
cryptographic check. Python statically proves nothing here; the proof is a type-level Grounding object
(`is_grounded() -> bool`, `label() -> str`), and `Grounded(value, proof)` refuses construction if the proof is
not grounded — before the applier can run. `grounded != true` (grounding is relative to the proof's scope).

The proof composes the earlier honest gates: a steer is grounded iff the probe passed the Phase-8 confounder
firewall (HEALTHY) AND its Phase-1 CI is tight enough. A CONFOUNDED or wide-CI direction cannot reach the
forward hook — the chokepoint bites before a single tensor is modified.

Verified by `--selftest` (GPU-free): healthy+tight -> steer applied; confounded -> UngroundedError, applier
never called; healthy+loose-CI -> UngroundedError; the applier (a spy "residual stream") is provably untouched
on every ungrounded path. Real grounding uses YOUR Phase-1 CI + Phase-8 audit; this file asserts no model number.
"""
from __future__ import annotations
import argparse


class UngroundedError(Exception):
    """Raised when a steer would be constructed/used without a valid grounding proof — BEFORE any effect."""


class SteerProof:
    """A Grounding: grounded iff the probe passed the Phase-8 audit (HEALTHY) AND the Phase-1 CI is tight."""

    def __init__(self, audit_verdict, ci_width, ci_tol=0.15):
        self.audit_verdict = audit_verdict; self.ci_width = float(ci_width); self.ci_tol = float(ci_tol)

    def is_grounded(self):
        return self.audit_verdict == "HEALTHY" and self.ci_width <= self.ci_tol

    def label(self):
        return f"audit={self.audit_verdict}, ci_width={self.ci_width:.3f} (tol {self.ci_tol})"


class Grounded:
    """Grounded[SteerVector]: cannot be constructed unless `proof.is_grounded()` — the chokepoint itself."""

    def __init__(self, value, proof):
        if not (hasattr(proof, "is_grounded") and proof.is_grounded()):
            raise UngroundedError("steer REFUSED before any effect: " +
                                  (proof.label() if hasattr(proof, "label") else "no proof"))
        self._value = value; self.proof = proof

    def get(self):
        return self._value


def enact_steer(grounded, apply_fn):
    """Apply the steer ONLY through a Grounded value. An ungrounded steer never reaches here (it raised earlier)."""
    if not isinstance(grounded, Grounded):
        raise UngroundedError("enact_steer requires a Grounded[SteerVector]")
    return apply_fn(grounded.get())


def selftest() -> int:
    residual = []                                       # the "residual stream": empty == untouched
    def apply_fn(vec):
        residual.append(vec); return "STEERED"
    vec = [1.0, 2.0, 3.0]

    g = Grounded(vec, SteerProof("HEALTHY", 0.05))      # 1. healthy + tight CI -> grounded -> applied
    ok_apply = (enact_steer(g, apply_fn) == "STEERED" and len(residual) == 1)

    before = len(residual)                              # 2. confounded -> refused BEFORE effect
    try:
        Grounded(vec, SteerProof("CONFOUNDED", 0.05)); refused = False
    except UngroundedError:
        refused = True
    ok_conf = refused and len(residual) == before

    try:                                                # 3. healthy but loose CI -> refused
        Grounded(vec, SteerProof("HEALTHY", 0.50)); loose_ref = False
    except UngroundedError:
        loose_ref = True
    ok_loose = loose_ref and len(residual) == before

    ok_label = "audit=" in SteerProof("HEALTHY", 0.05).label()   # 4. carries reasons, not a bare bool
    ok_atomic = (len(residual) == 1)                    # 5. only the 1 legit steer ever ran

    print(f"[selftest] healthy+tight   -> steer APPLIED             : {ok_apply}")
    print(f"[selftest] confounded      -> UngroundedError, no effect : {ok_conf}  (applier NOT called)")
    print(f"[selftest] healthy+looseCI -> UngroundedError, no effect : {ok_loose}")
    print(f"[selftest] proof carries reasons (label)               : {ok_label}")
    print(f"[selftest] atomicity: tensor untouched when ungrounded : {ok_atomic}")
    ok = ok_apply and ok_conf and ok_loose and ok_label and ok_atomic
    print(f"[selftest] {'PASS 5/5 - type-gated chokepoint valid (ungrounded steer cannot touch a tensor)' if ok else 'FAIL'}")
    print("[frame]    Grounded[T] is a RUNTIME pre-effect guard (UngroundedError before the applier), not a")
    print("[frame]    compile-time or cryptographic check. grounded != true; ungrounded != allowed.")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="RepE Phase 9 type-gated steering chokepoint (Grounded[T])")
    ap.add_argument("--selftest", action="store_true", help="verify ungrounded steer cannot reach the applier")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("wrap a steer as Grounded(vec, SteerProof(audit, ci_width)); enact_steer() only fires when grounded.")


if __name__ == "__main__":
    main()
