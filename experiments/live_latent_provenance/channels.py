# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/live_latent_provenance/channels.py — the two paths, made first-class so misuse is
impossible by construction rather than by policy.

The probe established that the dangerous failure mode is an OPTIMIZATION manufacturing a provenance
gap:

    buffer full → drop event → world state advances anyway → UNACCOUNTED

The current policy (drop resolve requests, never commits) is correct, but a policy can be violated by
the next refactor. The fix is to make the two paths DIFFERENT TYPES with different powers, so the
violation cannot be written:

    CommitChannel   never drops · state-changing · provenance REQUIRED · only path that advances state
    ResolveRing     may drop/defer · inspection only · counted · CANNOT advance state

Two structural guarantees follow:
  1. A `Commit` cannot be constructed without provenance — an unprovenanced state change is unspeakable.
  2. State can advance ONLY through `CommitChannel.apply`, which has no drop path at all; `ResolveRing`
     has no `apply`. So "a full buffer dropped a state change" is not a reachable program state.

`compression ≠ severance`, lifted from a runtime check into the type boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from compression import ProvenanceStore, SeveranceError, UNRECORDED


@dataclass(frozen=True)
class Commit:
    """A state-changing event. Provenance is a required field; constructing one without a usable
    digest raises. There is no way to express "advance state, provenance unknown"."""

    target: str
    new_state: Any
    provenance_digest: str

    def __post_init__(self):
        d = self.provenance_digest
        if d is None or d == UNRECORDED or d == "":
            raise ValueError(
                "a Commit must carry provenance; refusing to construct an unprovenanced state change"
            )


class CommitChannel:
    """The only path that advances world state. Never drops. Applies synchronously, and only after
    confirming the commit's provenance resolves — a severed/dangling digest is REFUSED (raises), so
    state never advances on lost provenance. Deliberately has no offer/full/drop surface."""

    def __init__(self, store: ProvenanceStore):
        self.store = store
        self.applied = 0
        self.refused = 0

    def apply(self, commit: Commit, world: dict) -> None:
        if self.store.resolve_digest(commit.provenance_digest)["status"] != "resolved":
            self.refused += 1
            raise SeveranceError("refuse to advance state on untraceable provenance")
        world[commit.target] = commit.new_state
        self.applied += 1


class ResolveRing:
    """Inspection path. A single-producer/single-consumer ring that MAY drop under backpressure
    (counted) — dropping a resolve request only defers inspection, it loses no state. Has no `apply`:
    it physically cannot advance world state. (NOT lock-free under the GIL — see probe.py bounds.)"""

    def __init__(self, capacity: int = 4096):
        self._buf: List[Optional[str]] = [None] * capacity
        self._cap = capacity
        self._w = 0
        self._r = 0
        self.dropped = 0

    def offer(self, digest: str) -> bool:
        nxt = (self._w + 1) % self._cap
        if nxt == self._r:
            self.dropped += 1
            return False
        self._buf[self._w] = digest
        self._w = nxt
        return True

    def poll(self) -> Optional[str]:
        if self._r == self._w:
            return None
        d = self._buf[self._r]
        self._r = (self._r + 1) % self._cap
        return d

    def empty(self) -> bool:
        return self._r == self._w
