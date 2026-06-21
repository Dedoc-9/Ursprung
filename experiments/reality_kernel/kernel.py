# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/kernel.py — RealityKernel: the assembled organism.

Four immutable concepts over the objects the project already earned:

    Artifact   a thing that exists or is claimed          (declared provenance required)
    Event      how it changed                              (lineage / a named source required)
    Commit     an accepted transition receipt              (a record, never an authorization)
    Query      provenance-aware observation                (existence AND absence)

The inversion that makes it a runtime rather than an engine: most engines store `object → history
(optional)`; here `history → object` — an object without lineage is incomplete. The kernel's strongest
possible claim, and its honest ceiling:

    nothing exists here without a trace of how it entered;
    nothing is missing here without a trace of why it is missing.

It does not certify that any structure is fundamental — it remains a notary (`declared ≠ verified`).
"""
from __future__ import annotations

import query as Q
from _evidence import World, diagnose
from artifact import Artifact
from commit import CommitChannel, CommitReceipt, SeveranceError
from event import Event


class RealityKernel:
    def __init__(self):
        self.world = World()
        self.commits = CommitChannel(self.world)
        self.nonrecovery = {}                      # target -> {diagnosis, source, missing}

    # --- Event → Commit: the only way state advances ---
    def apply(self, event: Event, requires: str = None) -> CommitReceipt:
        return self.commits.commit(event, requires=requires)

    # --- absence is first-class too ---
    def record_nonrecovery(self, target: str, case: dict, source: str, missing: str = None):
        self.nonrecovery[target] = {"diagnosis": diagnose(case), "source": source, "missing": missing}

    # --- Artifact: a thing with declared provenance ---
    def artifact(self, kind, content, provenance, **kw) -> Artifact:
        return Artifact(kind, content, provenance, **kw)

    # --- Query: existence and absence, with provenance and resolution path ---
    def query(self, target: str) -> dict:
        return Q.query(self.world, self.nonrecovery, target)

    def provenance_of(self, target):
        return Q.provenance_of(self.world, target)

    def provenance_of_nonrecovery(self, target):
        return Q.provenance_of_nonrecovery(self.nonrecovery, target)
