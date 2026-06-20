# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/capability.py — the Causal Capability Token (permissioned use of dependency knowledge).

The integrity layer (M10) answers "is this claim unforged / agreed?" — but a wallhack passes both: it is
real, agreed-upon information the observer is simply not *entitled* to use. So the question shifts from "do I
know this?" to **"am I permitted to use this knowledge, and only for this purpose?"** A capability token is
that permission slip:

    capability = { what: "prepare_representation",
                   subject: object_id,
                   scope:  "visual_only",
                   horizon: 200ms,
                   source: "physics_snapshot",
                   cannot: mutate / select_outcome / reveal_hidden }

A token authorizes USE of dependency information for a bounded purpose. It never grants authority: `mutate`,
`select_outcome`, `reveal_hidden`, and `grant_authority` are FORBIDDEN on every token by construction — the
prepare-≠-decide moat, now also prepare-≠-know-more-than-allowed. This is the difference between legitimate
readiness (shader warmup, particle prep, LOD prediction) and forbidden advantage (ESP / wallhack / outcome
leak).

CLASSIFICATION: OBSERVER / reference (mutates_core=False). It constrains how knowledge may be used; it commits
no state, selects nothing, and asserts no truth. integrity ≠ truth; authorized ≠ true.
"""
from __future__ import annotations

# powers a representation/readiness token may legitimately carry
ALLOWED_WHAT = frozenset({"prepare_representation", "observe", "allocate"})
# powers no token may EVER carry (the moat, baked into every token)
FORBIDDEN_ALWAYS = frozenset({"mutate", "select_outcome", "reveal_hidden", "grant_authority"})


class CapabilityViolation(Exception):
    """Raised when knowledge is used beyond its permission (wrong purpose, expired horizon, forbidden power)."""


class CausalCapabilityToken:
    __slots__ = ("what", "subject", "scope", "horizon", "source", "cannot")

    def __init__(self, what, subject, scope="visual_only", horizon=200, source="core", cannot=()):
        self.what = what
        self.subject = subject
        self.scope = scope
        self.horizon = horizon
        self.source = source
        self.cannot = frozenset(cannot) | FORBIDDEN_ALWAYS   # mutate/select/reveal_hidden always forbidden

    def permits(self, action, purpose, horizon_needed=0):
        """True iff this token grants `action` for `purpose` within `horizon_needed`, and `action` is neither
        forbidden nor outside the allowed-what set."""
        return (action == self.what
                and action in ALLOWED_WHAT
                and action not in self.cannot
                and purpose == self.scope
                and horizon_needed <= self.horizon)

    def __repr__(self):
        return "<Capability %s:%s scope=%s horizon=%s>" % (self.what, self.subject, self.scope, self.horizon)


def issue(what, subject, scope="visual_only", horizon=200, source="core", cannot=()):
    """Mint a capability token. A token granting a forbidden power is rejected at issue time."""
    if what not in ALLOWED_WHAT:
        raise CapabilityViolation("a token may not grant %r (allowed: %s)" % (what, sorted(ALLOWED_WHAT)))
    return CausalCapabilityToken(what, subject, scope, horizon, source, cannot)


def use(token, action, purpose, horizon_needed=0):
    """Consume a capability for an action+purpose. Fails closed (CapabilityViolation) if not permitted —
    the renderer asks 'am I permitted to use this knowledge, only for this purpose?', not 'is it true?'."""
    if not token.permits(action, purpose, horizon_needed):
        raise CapabilityViolation(
            "knowledge use denied: %r for %r within %sms not permitted by %r"
            % (action, purpose, horizon_needed, token))
    return True


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("capability", OBSERVER, mutates_core=False,
                          note="Causal Capability Token — permissioned USE of dependency knowledge for a "
                               "bounded purpose; mutate/select/reveal_hidden forbidden on every token")
    except LayerViolation:
        pass
