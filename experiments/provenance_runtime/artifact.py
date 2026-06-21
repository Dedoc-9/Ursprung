# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/provenance_runtime/artifact.py — the one runtime object: a provenance-bearing artifact.

The implementation arc (Phases 1–6, and the symbolic objects before them) produced many objects that were all
the same shape: a value bound to the conditions of its own existence. Phase R consolidates them. The unifying
runtime object is not an estimator, encoder, or graph — it is the **Artifact**: identity, provenance, evidence
boundary, status. Every prior object becomes an artifact *type*, not a separate project.

    Artifact
     ├── identity      content hash (and a CLAIM hash — what is asserted, distinct from how it is represented)
     ├── provenance    creator manifest · transformation history · dependencies · declared assumptions
     ├── evidence       observations · interventions · model family 𝓕 · admissibility set 𝓐
     └── status        verified | survived | assumed | unknown

The architectural inversion: a normal ML runtime asks *"what output did the model produce?"* This runtime asks
*"what object exists, under what transformations, and what licenses its existence?"* — the model output is just
one possible artifact.

The creator is neither hidden nor sovereign: the creator manifest is one explicit **provenance source**, a named
causal input. That blocks both symmetric failures — anthropomorphism ("it discovered because it thinks like
us") and technological projection ("it discovered because it is outside us"). The runtime only ever says: *this
artifact persisted under these declared transformations and constraints.*

The contract is fixed; the encoder/estimator/model is a plugin. `transform()` produces a new artifact with
inherited provenance (a dependency on its parent + an extended history), so a developer can change the
representation, model, or assumptions **without losing the history of what made the result admissible**.
`identity includes provenance` — including the provenance of the creator. HONEST: this records and audits
declared provenance; it does not validate it (`declared cost ≠ verified cost`).
"""
from __future__ import annotations

import hashlib
import json

STATUSES = ("verified", "survived", "assumed", "unknown")


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


class Artifact:
    """A value bound to its conditions of existence. The base type for every prior phase object."""

    def __init__(self, kind, content, creator_manifest=None, transformation_history=(), dependencies=(),
                 declared_assumptions=(), observations=(), interventions=(), model_family=(),
                 admissibility_set=(), status="unknown"):
        if status not in STATUSES:
            raise ValueError("status must be one of %r" % (STATUSES,))
        self.kind = kind
        self.content = content
        self.provenance = {
            "creator_manifest": creator_manifest or {},          # the creator: a named provenance source
            "transformation_history": list(transformation_history),
            "dependencies": list(dependencies),                  # parent artifact digests (the provenance DAG)
            "declared_assumptions": list(declared_assumptions),
        }
        self.evidence = {
            "observations": list(observations),
            "interventions": list(interventions),
            "model_family": list(model_family),                  # 𝓕
            "admissibility_set": list(admissibility_set),        # 𝓐
        }
        self.status = status

    def claim_digest(self):
        """The CLAIM identity — what is asserted (kind + content + status), independent of how it is
        represented or what produced it. Two artifacts with the same claim digest assert the same thing."""
        return _digest({"kind": self.kind, "content": self.content, "status": self.status})

    def digest(self):
        """The FULL identity — including provenance and evidence. identity includes provenance: two artifacts
        with identical content but different provenance are different objects."""
        return _digest({"kind": self.kind, "content": self.content,
                        "provenance": self.provenance, "evidence": self.evidence, "status": self.status})

    def transform(self, operation, **changes):
        """Produce a NEW artifact with inherited provenance — a dependency on this one and an extended history.
        Changing the representation/model/assumptions never erases what made the prior result admissible."""
        return Artifact(
            self.kind, changes.get("content", self.content),
            creator_manifest=changes.get("creator_manifest", self.provenance["creator_manifest"]),
            transformation_history=self.provenance["transformation_history"] + [operation],
            dependencies=self.provenance["dependencies"] + [self.digest()],
            declared_assumptions=changes.get("declared_assumptions", self.provenance["declared_assumptions"]),
            observations=self.evidence["observations"], interventions=self.evidence["interventions"],
            model_family=changes.get("model_family", self.evidence["model_family"]),
            admissibility_set=self.evidence["admissibility_set"], status=changes.get("status", self.status))

    def compare(self, other):
        """Compare CLAIMS, not representations. Two artifacts can be claim-equivalent while differing in full
        identity (different provenance/representation) — the Phase-5 humility, generalized to every artifact."""
        return {"claim_equivalent": self.claim_digest() == other.claim_digest(),
                "same_full_identity": self.digest() == other.digest(),
                "shared_history": (self.digest() in other.provenance["dependencies"]
                                   or other.digest() in self.provenance["dependencies"])}

    def audit(self):
        """Expose what was DEMONSTRATED (interventions, observations) vs ASSUMED (declared assumptions), and
        whether the artifact is unverified."""
        demonstrated = list(self.evidence["interventions"]) + (["observations"] if self.evidence["observations"] else [])
        return {"kind": self.kind, "status": self.status,
                "demonstrated": demonstrated,
                "assumed": list(self.provenance["declared_assumptions"]),
                "unverified": self.status in ("assumed", "unknown")}

    def __repr__(self):
        return "<Artifact %s [%s] %s>" % (self.kind, self.status, self.digest())
