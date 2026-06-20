# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/disclosure.py — the intent → representation seam (the first brick of the perception compiler).

This is the missing boundary the second arc pointed at (see `docs/INFORMATION_INTENT.md`): not a renderer, not
a dev UI, not a chunk injector — those are downstream. The seam is the **policy/control plane that decides what
information should be materialized** for an observer with a purpose. It turns "what someone *should* know" into
"what the system emits," and then hands the realized emission to the M10–M21 machinery as an auditor:

    policy says:    reveal X                      (the generative half — INTENT, committed)
    measurement:    did the output contain only X? (the defensive half — the firewall, as VERIFIER)

It is deliberately, embarrassingly small. It adds NO new invariant; it is an *instrument* that composes the two
halves that already exist. A `DisclosurePolicy` is the generative dual of `capability.py`/`causal_access.py`,
and it is committed exactly the way every boundary in this project is committed — declared, deterministic,
content-addressed, `not_a_truth_claim = True` (the `conventions.py` discipline; Bayesian-persuasion commitment).

CLASSIFICATION: OBSERVER (mutates_core=False). It governs what VIEW *emits* and audits the result; it never
moves the Weltlinie and asserts no truth. The toy `compile_emission` here is a placeholder for the real
perception compiler (which would solve the privacy-funnel objective of `INFORMATION_INTENT.md` §3).

HONEST BOUND: this audits at the level of *declared channels* (symbolic names), and only the channels the
policy enumerates — the audit is itself a bounded observer with a coverage boundary. The deeper audit over a
realized *signal trace* (mutual information, unmodeled channels) is `channel_discovery.py`'s job; "compliant"
here means "w.r.t. the audited channel set," never "safe." `secure-against-audited-set ≠ secure`.
"""
from __future__ import annotations

import hashlib


# A toy model of what each PURPOSE genuinely needs (the participation floor / value-of-information, symbolic).
# The real compiler would derive this from the observer's POMDP; here it is a declared table.
PURPOSE_NEEDS = {
    "survival":   {"threat_direction", "timing_window"},
    "navigation": {"path_layout", "landmark_bearing"},
    "spectate":   {"threat_direction", "timing_window", "score_state"},
}


class DisclosurePolicy:
    """A committed signaling scheme: for this observer and purpose, these channels MAY be disclosed and these
    NEVER may. Content-addressed (the commitment is verifiable) and not a truth claim — it is a choice about
    *what to reveal*, never an assertion about the world. CORE cannot lie; this only chooses the projection."""

    __slots__ = ("observer", "purpose", "allowed", "forbidden", "_hash")

    def __init__(self, observer, purpose, allowed_channels, forbidden_channels):
        self.observer = observer
        self.purpose = purpose
        self.allowed = frozenset(allowed_channels)
        self.forbidden = frozenset(forbidden_channels)
        if self.allowed & self.forbidden:
            raise ValueError("a channel cannot be both allowed and forbidden: %s"
                             % sorted(self.allowed & self.forbidden))
        self._hash = self._content_hash()

    def _content_hash(self):
        canon = "|".join([self.observer, self.purpose,
                          ",".join(sorted(self.allowed)), ",".join(sorted(self.forbidden))])
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    @property
    def policy_hash(self):
        return self._hash

    @property
    def not_a_truth_claim(self):
        return True

    def permits(self, channel):
        return channel in self.allowed and channel not in self.forbidden

    def __repr__(self):
        return "<DisclosurePolicy %s/%s allow=%d forbid=%d %s>" % (
            self.observer, self.purpose, len(self.allowed), len(self.forbidden), self._hash[:8])


# --- the (toy) perception compiler: intent → the channels to materialize ----------------------------

def compile_emission(policy):
    """Lower (observer, purpose, policy) into the set of channels actually materialized: exactly what the
    purpose needs, intersected with what the policy allows, minus anything forbidden. A placeholder for the
    privacy-funnel solve — but already enough to drive the auditor loop."""
    needed = PURPOSE_NEEDS.get(policy.purpose, frozenset())
    return (needed & policy.allowed) - policy.forbidden


# --- the auditor: the M10–M21 firewall, pointed at the realized emission ----------------------------

class AuditResult:
    """Carries its own boundary (the MEASUREMENT_DISCIPLINE pattern): what was disclosed, whether it complied
    with the committed policy, whether it sufficed for the purpose — and what the audit could NOT see."""

    __slots__ = ("disclosed", "over_disclosure", "outside_allowed", "under_provision",
                 "compliant", "sufficient", "coverage_boundary")

    def __init__(self, disclosed, over_disclosure, outside_allowed, under_provision):
        self.disclosed = frozenset(disclosed)
        self.over_disclosure = frozenset(over_disclosure)     # forbidden channels that leaked out
        self.outside_allowed = frozenset(outside_allowed)     # emitted but never authorized by the policy
        self.under_provision = frozenset(under_provision)     # purpose needs the emission failed to provide
        self.compliant = not over_disclosure and not outside_allowed
        self.sufficient = not under_provision
        self.coverage_boundary = ("declared channels only — an unmodeled channel can still leak; "
                                  "realized-signal audit is channel_discovery.py's job")

    def __repr__(self):
        return "<AuditResult compliant=%s sufficient=%s over=%s outside=%s under=%s>" % (
            self.compliant, self.sufficient, sorted(self.over_disclosure),
            sorted(self.outside_allowed), sorted(self.under_provision))


def audit(emission, policy):
    """policy says reveal X → did the output contain only X (and enough of it)? Returns an AuditResult, never a
    bare boolean. `compliant` = no forbidden channel and nothing outside the allowed set; `sufficient` = the
    purpose's needs were met (the participation floor)."""
    emission = frozenset(emission)
    needed = PURPOSE_NEEDS.get(policy.purpose, frozenset())
    return AuditResult(
        disclosed=emission,
        over_disclosure=emission & policy.forbidden,
        outside_allowed=emission - policy.allowed,
        under_provision=needed - emission,
    )


# --- the crucible: the loop, with negative controls -------------------------------------------------

def crucible():
    out = {}
    policy = DisclosurePolicy(
        observer="player", purpose="survival",
        allowed_channels=["threat_direction", "timing_window"],
        forbidden_channels=["exact_position", "future_state"],
    )
    # 1. the committed compiler emits exactly the purpose-need ∩ allowed: compliant AND sufficient
    emitted = compile_emission(policy)
    good = audit(emitted, policy)
    out["compiled_channels"] = sorted(emitted)
    out["compiled_compliant"] = good.compliant
    out["compiled_sufficient"] = good.sufficient
    # 2. negative control — an over-discloser leaks a forbidden channel (exact_position)
    over = audit(emitted | {"exact_position"}, policy)
    out["over_disclosure_caught"] = (not over.compliant) and ("exact_position" in over.over_disclosure)
    # 3. negative control — an emission outside the allowed set (server_state was never authorized)
    outside = audit(emitted | {"server_state"}, policy)
    out["outside_allowed_caught"] = (not outside.compliant) and ("server_state" in outside.outside_allowed)
    # 4. negative control — under-provision: drop a needed channel → compliant but NOT sufficient
    under = audit({"threat_direction"}, policy)
    out["under_provision_flagged"] = under.compliant and (not under.sufficient) and ("timing_window" in under.under_provision)
    # 5. the policy is a committed, content-addressed convention (deterministic hash), not a truth claim
    same = DisclosurePolicy("player", "survival", ["threat_direction", "timing_window"],
                            ["exact_position", "future_state"])
    out["policy_hash_deterministic"] = policy.policy_hash == same.policy_hash
    out["policy_not_a_truth_claim"] = policy.not_a_truth_claim
    # 6. the audit carries its own coverage boundary (never a bare 'safe')
    out["audit_carries_boundary"] = bool(good.coverage_boundary)
    return out


def demo():
    r = crucible()
    print("Disclosure — the intent → representation seam (policy says reveal X; did the output contain only X?)\n")
    print("  policy: player / survival  allow={threat_direction, timing_window}  forbid={exact_position, future_state}")
    print("  compiled emission: %s  → compliant=%s, sufficient=%s"
          % (r["compiled_channels"], r["compiled_compliant"], r["compiled_sufficient"]))
    print("  negative controls:")
    print("     over-disclosure (leaks exact_position) caught: %s" % r["over_disclosure_caught"])
    print("     outside-allowed (emits server_state) caught:   %s" % r["outside_allowed_caught"])
    print("     under-provision (drops timing_window) flagged: %s" % r["under_provision_flagged"])
    print("  policy is a committed convention (deterministic hash)=%s, not_a_truth_claim=%s"
          % (r["policy_hash_deterministic"], r["policy_not_a_truth_claim"]))
    print("\n  the player needs 'can I dodge this?' — a threat direction + timing window — never exact position")
    print("  or future state. the compiler chooses the projection; the firewall verifies it. CORE cannot lie;")
    print("  this only chooses what to reveal. compliant ≠ safe (audited channels only). integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("disclosure", OBSERVER, mutates_core=False,
                          note="intent → representation seam: DisclosurePolicy (committed signaling scheme) + a "
                               "toy compiler + the M10–M21 firewall as auditor (policy says reveal X; did the "
                               "output contain only X?). instrument, not a law; compliant ≠ safe")
    except LayerViolation:
        pass
