# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_authoring/nonrecovery.py — ignorance as a first-class historical object.

The Reality Authoring Runtime made *present* structure provenance-bearing: every law, asset, and behaviour
remembers how it came to exist. This closes the symmetry the project kept circling — it makes *absent* and
*unresolved* structure provenance-bearing too. Most systems store the left-hand side and leave the right
implicit:

    structure  ↔  non-structure        knowledge  ↔  ignorance        presence  ↔  absence

Here both sides are explicit. A world can answer not only "why does gravity exist? → developer edit #17" but
also "why is relation R *absent*? → severance" and "why is relation S *unresolved*? → assumption_limit, missing
admissibility condition A." Ignorance stops being a silent `None` and becomes a recorded object with lineage.

This is built object-first, policy-second (the project's recurring order): the `NonRecovery` object carries the
full failure diagnosis (from `failure_taxonomy`) — its kind, tier, relation, remedy, and observer-independence —
so a `recommended_action()` view (allocate / declare / stop) can always be *derived* later, while the converse
is impossible: a policy decision cannot reconstruct the provenance after the fact. Preserve provenance first,
derive behaviour second.

`identity includes provenance` — now for what cannot presently be known, as well as for what exists. HONEST: a
`NonRecovery` records a *declared* diagnosis (which failure is claimed, and what would resolve it), not a proof
that no channel carries the signal (severance) or that an alternative cause matches across all interventions
(indistinguishability — the un-runnable check). `declared ≠ verified`. The one thing it forbids is the silent
gap: a structure that is neither present-with-provenance nor absent-with-a-diagnosis is `UNACCOUNTED` — the
implicit absence the framework refuses to leave implicit.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os

# reuse the Reality Authoring World/Edit (same dir) and the failure taxonomy (sibling dir), unedited
_here = os.path.dirname(__file__)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_reality = _load("ra_reality", os.path.join(_here, "reality.py"))
_failure = _load("ft_failure", os.path.join(_here, "..", "failure_taxonomy", "failure.py"))
World, Edit = _reality.World, _reality.Edit
diagnose = _failure.diagnose


class NonRecovery:
    """Why a structure is absent or unresolved — a historical object parallel to an `Edit`."""
    __slots__ = ("target", "case", "source", "missing_admissibility", "diagnosis")

    def __init__(self, target, case, source, missing_admissibility=None):
        self.target = target
        self.case = case                          # the declared recovery situation (see failure_taxonomy)
        self.source = source                      # who/what produced the diagnosis (a provenance source)
        self.missing_admissibility = missing_admissibility   # for assumption_limit: which condition is missing
        self.diagnosis = diagnose(case)           # failure / tier / relation / remedy / observer_independent

    def digest(self):
        return hashlib.sha256(json.dumps(
            {"target": self.target, "diagnosis": self.diagnosis, "source": self.source,
             "missing_admissibility": self.missing_admissibility}, sort_keys=True, default=str).encode()).hexdigest()[:12]

    def __repr__(self):
        return "<NonRecovery %s: %s by %s>" % (self.target, self.diagnosis["failure"], self.source)


class WorldWithIgnorance:
    """A world whose *present* structure carries edit lineage and whose *absent/unresolved* structure carries a
    diagnosis. Both sides inspectable; neither implicit."""

    def __init__(self):
        self.world = World()
        self.nonrecovery = {}                     # target -> NonRecovery

    # --- present structure (the Reality Authoring layer) ---
    def apply(self, edit):
        return self.world.apply(edit)

    def provenance_of(self, target):
        return self.world.provenance_of(target)

    # --- absent / unresolved structure (the new layer) ---
    def record_nonrecovery(self, nonrecovery):
        self.nonrecovery[nonrecovery.target] = nonrecovery
        return nonrecovery

    def provenance_of_nonrecovery(self, target):
        return self.nonrecovery.get(target)

    def explain(self, target):
        """The unified answer: present-because-edits, absent/unresolved-because-diagnosis, or UNACCOUNTED."""
        if self.world.history.get(target) and self.world.value(target) is not None:
            return {"status": "present", "provenance": self.provenance_of(target)}
        nr = self.nonrecovery.get(target)
        if nr:
            return {"status": "absent_or_unresolved", "why": nr.diagnosis["failure"],
                    "tier": nr.diagnosis["tier"], "remedy": nr.diagnosis["remedy"],
                    "observer_independent": nr.diagnosis["observer_independent"],
                    "missing": nr.missing_admissibility, "source": nr.source}
        return {"status": "UNACCOUNTED"}          # the implicit absence the framework refuses to allow

    def recommended_action(self, target):
        """A derived VIEW over the stored diagnosis (object-first, policy-second). Not stored — computed."""
        nr = self.nonrecovery.get(target)
        if not nr:
            return None
        return {"severance": "stop", "indistinguishability": "stop",
                "assumption_limit": "declare", "resource_limit": "allocate"}[nr.diagnosis["failure"]]
