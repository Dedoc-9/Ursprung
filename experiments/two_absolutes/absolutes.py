# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/two_absolutes/absolutes.py — the two class-independent guarantees, with the verifiability correction.

There are exactly two observer-independent ways an observer's capacity is zeroed out — the only boundaries that
do NOT puncture against a richer adversary. An observer extracts a cause X iff some available observable Y has
I(X;Y) > 0, so it fails absolutely in exactly two ways:

    M21_severed         ABSENCE.    I(X;Y)=0 for every possible Y. The signal is not in the observable universe.
    indistinguishable   COLLISION.  distinct causes {X, X'} induce identical distributions over every Y,
                                    including every interventional one: P(Y|do(X)) = P(Y|do(X')). The signal is
                                    present but undecidable for an observer of infinite capacity.

Everything else — cryptographic hardness, physical erasure, behavioral non-identifiability, generator-privacy —
is **class-relative**: it holds against a stated observer class and dissolves against a richer one.

THE CORRECTION this module enforces (where a naive formalization overclaims): the two absolutes are symmetric as
*boundaries* but **asymmetric in verifiability**.
  · Severance is often **constructively** witnessed — the system is built so no channel carries the secret;
    I=0 by construction is checkable.
  · Indistinguishability generally **cannot be proved** — it needs identical distributions over every observable
    AND every intervention across the whole admissibility set, i.e. the exhaustive intervention the project says
    you cannot run (intervention scarcity, unknown graph). So `indistinguishable` is almost always a DECLARED
    status, not a proved one — `declared ≠ verified`. (In latent_phase1 the confounder was *observationally*
    indistinguishable from the generator until `do(c)` broke it; true indistinguishability must survive all
    `do()`, and verifying that is the un-runnable thing.)

So this guard: rejects physical erasure as an absolute (it is class-relative — logical erasure that reaches I=0
simply *is* severance); requires every absolute to carry its licensing witness (no free absolute); forbids an
absolute from being conditioned on an adversary class (an absolute is not relative); and records that an
absolute's witness is DECLARED, never verified by the runtime — flagging indistinguishability as
`requires_exhaustive_intervention` (the frontier). Separators: severance ≠ indistinguishability; logical erasure
≠ physical erasure; absolute-as-boundary ≠ absolute-as-verified; declared ≠ verified.
"""
from __future__ import annotations

ABSOLUTE = ("M21_severed", "indistinguishable")          # the two class-independent boundaries
RELATIVE = ("survived", "assumed", "unknown")            # adversary-bounded; punctures against a richer observer
ERASURE_ABSOLUTE_CLAIMS = ("M22_erased", "physically_erased", "irreversibly_erased")  # rejected as absolutes

WITNESS_REQUIRED = {
    "M21_severed": "severance_witness",                  # e.g. I(secret; observable)=0 by construction
    "indistinguishable": "interventional_identity_witness",  # P(Y|do(X))=P(Y|do(X')) across 𝓐
}
VERIFIABILITY = {
    "M21_severed": "constructive",                       # checkable: no channel carries it
    "indistinguishable": "requires_exhaustive_intervention",  # the frontier: all do() over all 𝓐 — un-runnable
}


class StatusClaim:
    """A claim that an artifact has a given status, with its licensing witness and (if relative) its class."""
    __slots__ = ("status", "witness", "adversary_class")

    def __init__(self, status, witness=None, adversary_class=None):
        self.status = status
        self.witness = witness                            # {"kind": ..., ...} — DECLARED, not proved here
        self.adversary_class = adversary_class            # only legitimate for a RELATIVE status

    def __repr__(self):
        return "<StatusClaim %s witness=%s class=%s>" % (self.status, (self.witness or {}).get("kind"), self.adversary_class)


def validate(claim):
    """Enforce the two-absolutes discipline. Returns a record; raises on a discipline violation."""
    # physical erasure can never be an absolute — it dissipates into a reservoir a richer observer reads
    if claim.status in ERASURE_ABSOLUTE_CLAIMS:
        raise TypeError("physical erasure is class-relative (route to 'survived'); "
                        "logical erasure that reaches I=0 IS M21_severed, not a new absolute")
    if claim.status in ABSOLUTE:
        if claim.adversary_class is not None:
            raise ValueError("an absolute guarantee cannot be conditioned on an observer/adversary class")
        need = WITNESS_REQUIRED[claim.status]
        if not (claim.witness and claim.witness.get("kind") == need):
            raise ValueError("absolute %r requires a declared %r — no free absolute" % (claim.status, need))
        # the boundary is absolute; the runtime still does NOT verify the witness — declared != verified
        return {"status": claim.status, "tier": "absolute", "verified_by_runtime": False,
                "declared_witness": claim.witness["kind"], "verifiability": VERIFIABILITY[claim.status]}
    if claim.status in RELATIVE:
        return {"status": claim.status, "tier": "relative", "relative_to": claim.adversary_class}
    raise ValueError("unknown status %r" % (claim.status,))
