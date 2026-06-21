# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/live_latent_provenance/compression.py
A provenance cache hierarchy — a stress test of the meta-invariant under a frame budget.

This is NOT a renderer and NOT a real-time claim. It tests one architectural property:

    Provenance identity survives representation change.

The earlier phases asked: can a claim keep its floor? a coordinate its status? an edge its
support? a latent its claim? an inference its price? an edit its source? ignorance its diagnosis?
This asks the same question at a different pressure:

    Can a runtime keep provenance when it is forced to COMPRESS?

The split (the contract boundary, which is where "4.13 ms" actually lives — not in the renderer):

    frame(t):     execute      — the hot path moves only {state, transform, provenance_digest}
    background:   preserve why  — the latent store resolves a digest to the full lineage on demand

The hot loop never asks "why is this object true?". It asks "what is the IDENTITY of the
explanation attached to this object?". A real system MUST compress; compression is allowed.
What is forbidden is severance — an optimization that silently converts `why this exists` into
`it exists`. That is the exact collapse the project has been preventing, now as a runtime mode.

Earned separators (by the architecture, not asserted):
    full provenance ≠ hot-path representation
    compression     ≠ severance

Three resolution outcomes, kept crisp and NOT collapsed into one another:
    resolved            the digest resolves → full lineage recovered (provenance conserved)
    PROVENANCE_SEVERED  a digest was assigned, then nulled/dangling → recorded identity LOST.
                        Structure remains (gravity is still 0.5); the HISTORY was destroyed.
                        A runtime failure mode, never a silent fallback to `unknown`.
    UNACCOUNTED         no digest was ever assigned → never recorded (the silent gap).

Calibration — PROVENANCE_SEVERED is NOT the epistemic `severance` of the failure taxonomy.
Epistemic severance = a signal is absent in the WORLD (I(X;O)=0), observer-independent. Runtime
PROVENANCE_SEVERED = the world still has structure but the runtime threw away its record of why.
Same word, different objects; the runtime mode is class-relative and repairable in principle
(re-commit the lineage), the epistemic one is not. Do not conflate them.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

# Sentinel: this object was created without ever attaching provenance (distinct from a nulled digest).
UNRECORDED = "<unrecorded>"


def _digest(record: Dict[str, Any]) -> str:
    """Content digest of a full provenance record — its IDENTITY in the hot path."""
    return hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode()).hexdigest()[:12]


@dataclass
class LiveObject:
    """The hot-path object. Carries state, a transform, and a provenance DIGEST — never the graph.

    The frame loop moves these; the cost of carrying provenance is O(1) (one digest), independent
    of how deep the lineage is. `full provenance ≠ hot-path representation`.
    """

    state: Any
    transform: Any
    provenance_digest: str = UNRECORDED

    def reencode(self, *, state: Any = None, transform: Any = None) -> "LiveObject":
        """An internal optimization of the hot-path REPRESENTATION (pack state, change transform).
        It may change everything about execution; it leaves the provenance digest untouched —
        the invariant `execution representation can change, provenance identity cannot`.
        """
        return LiveObject(
            state=self.state if state is None else state,
            transform=self.transform if transform is None else transform,
            provenance_digest=self.provenance_digest,
        )


@dataclass
class ProvenanceStore:
    """The latent store. Holds full lineage keyed by digest; resolves out of the frame budget.

    A full record carries: origin, edit_lineage, assumptions, survival_tests, failures,
    verification_status — the same fields the reality-authoring layer records, now addressable
    by a single hot-path digest.
    """

    _records: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def commit(self, record: Dict[str, Any]) -> str:
        d = _digest(record)
        self._records[d] = dict(record)
        return d

    def compress(self, obj: LiveObject, record: Dict[str, Any]) -> LiveObject:
        """Move the full lineage into the latent store; the hot-path object keeps only the digest.
        This is compression, and it is ALLOWED — provenance is conserved because the digest resolves.
        """
        obj.provenance_digest = self.commit(record)
        return obj

    def resolve(self, obj: LiveObject) -> Dict[str, Any]:
        """Resolve a hot-path object's provenance. The three outcomes are kept distinct."""
        d = obj.provenance_digest
        if d == UNRECORDED:
            return {"status": "UNACCOUNTED", "reason": "no digest was ever assigned"}
        if d is None or d not in self._records:
            # A digest was assigned and is now null or points nowhere: the record was destroyed.
            return {"status": "PROVENANCE_SEVERED", "reason": "recorded identity lost; structure remains"}
        return {"status": "resolved", "provenance": self._records[d]}

    def is_traceable(self, obj: LiveObject) -> bool:
        return self.resolve(obj)["status"] == "resolved"

    def resolve_digest(self, digest: Optional[str]) -> Dict[str, Any]:
        """Resolve a bare digest (not wrapped in a LiveObject) — used by the commit path, where the
        thing being checked is an event's provenance reference, not a hot-path object."""
        return self.resolve(LiveObject(state=None, transform=None, provenance_digest=digest))


# --- Optimizations as plugins: one compresses, one severs. The contract distinguishes them. -------

def optimize_compress(store: ProvenanceStore, obj: LiveObject, *, transform: Any = "optimized") -> LiveObject:
    """A legitimate optimization: re-encode the hot-path representation, keep the digest.
    The world may become faster/smaller/optimized; the digest still resolves — traceable."""
    return obj.reencode(transform=transform)


def optimize_sever(obj: LiveObject) -> LiveObject:
    """A FORBIDDEN optimization: drop the digest to save the carry. Converts `why this exists`
    into `it exists`. The contract must catch this as PROVENANCE_SEVERED, not accept it silently."""
    return LiveObject(state=obj.state, transform=obj.transform, provenance_digest=None)


class SeveranceError(RuntimeError):
    """Raised by a guarded frame step when an object enters the hot path untraceable."""


def admit_to_frame(store: ProvenanceStore, obj: LiveObject) -> LiveObject:
    """The contract boundary. An object may enter the frame loop only if its provenance is
    traceable (resolved). A severed or unaccounted object is refused — the runtime exposes the
    failure rather than rendering an untraceable world. `compression ≠ severance` enforced here.
    """
    status = store.resolve(obj)["status"]
    if status != "resolved":
        raise SeveranceError(status)
    return obj
