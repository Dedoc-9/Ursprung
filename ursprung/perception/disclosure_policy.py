# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/disclosure_policy.py — the funnel-oriented disclosure policy.

This is the loop-level evolution of the channel-list seam in `ursprung/disclosure.py`: a committed,
content-addressed signaling scheme that names the observer class, the features it may receive, the secret it
must protect, and the two budgets the privacy funnel trades between — a `utility_floor` (the participation
floor: enough to do the task) and a `leakage_budget` (the ceiling on what may be inferred about the secret).
`not_a_truth_claim = True`: a policy chooses what to reveal; it never asserts the world.
"""
from __future__ import annotations

import hashlib


class DisclosurePolicy:
    __slots__ = ("observer_class", "purpose", "allowed_features", "protected_secret",
                 "utility_floor", "leakage_budget", "_hash")

    def __init__(self, observer_class, purpose, allowed_features, protected_secret,
                 utility_floor, leakage_budget):
        self.observer_class = observer_class
        self.purpose = purpose
        self.allowed_features = frozenset(allowed_features)
        self.protected_secret = protected_secret
        self.utility_floor = utility_floor       # the participation floor (min task success)
        self.leakage_budget = leakage_budget      # bits of I(secret ; observation) permitted
        self._hash = self._content_hash()

    def _content_hash(self):
        canon = "|".join([self.observer_class, self.purpose, self.protected_secret,
                          ",".join(sorted(self.allowed_features)),
                          "u=%.4f" % self.utility_floor, "l=%.4f" % self.leakage_budget])
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

    @property
    def policy_hash(self):
        return self._hash

    @property
    def not_a_truth_claim(self):
        return True

    def __repr__(self):
        return "<DisclosurePolicy %s/%s feats=%d floor=%.2f budget=%.2f %s>" % (
            self.observer_class, self.purpose, len(self.allowed_features),
            self.utility_floor, self.leakage_budget, self._hash[:8])


# the three committed policies the funnel benchmark compares (same floor + budget; only the features differ):
#   raw      — emit the full state (high utility, but the secret is fully recoverable)
#   compiled — emit only the task-relevant derived features (utility preserved, leakage collapsed)
#   blind    — emit nothing (zero leakage, but the agent cannot act)
_FLOOR = 0.90
_BUDGET = 3.0          # bits of leakage about the exact cell (H(secret) = 6 bits) permitted

POLICIES = {
    "raw": DisclosurePolicy("agent", "survive",
                            {"enemy_x", "enemy_y", "enemy_health"}, "exact_cell", _FLOOR, _BUDGET),
    "compiled": DisclosurePolicy("agent", "survive",
                                 {"threat_level", "cover_available"}, "exact_cell", _FLOOR, _BUDGET),
    "blind": DisclosurePolicy("agent", "survive",
                              frozenset(), "exact_cell", _FLOOR, _BUDGET),
}
