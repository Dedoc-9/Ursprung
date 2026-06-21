# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/commit.py — Commit: an ACCEPTED transition receipt, and the channel that
issues it.

A `CommitReceipt` is a RECORD of what happened, not a grant of permission. It answers what changed,
the prior state, the source, the dependencies, and the provenance digest — never "was this allowed?".
The runtime is a recorder that enforces non-forgetting, not a sovereign that authorizes change
(`attestation ≠ authority`). A receipt cannot exist without a resolvable provenance digest, and state
can advance ONLY by the channel issuing one — there is no drop path here, so a state change can never
slip through unrecorded.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from _evidence import Edit

UNRECORDED = "<unrecorded>"


class SeveranceError(RuntimeError):
    """Raised when a commit would advance state on provenance that does not resolve."""


@dataclass(frozen=True)
class CommitReceipt:
    target: str
    previous: Any
    new: Any
    source: str
    dependencies: tuple
    provenance_digest: str

    def __post_init__(self):
        if not self.provenance_digest or self.provenance_digest == UNRECORDED:
            raise ValueError("a CommitReceipt must carry a resolvable provenance digest (a receipt, "
                             "not an authorization)")


class CommitChannel:
    """The only path that advances world state. Never drops; issues a receipt iff the transition's
    provenance resolves; refuses (raises, no state change) otherwise."""

    def __init__(self, world):
        self.world = world
        self.receipts = []
        self.refused = 0

    def _resolves(self, digest: str) -> bool:
        return any(e.digest() == digest for h in self.world.history.values() for e in h)

    def commit(self, event, requires: str = None) -> CommitReceipt:
        # an optional prerequisite: a prior provenance digest this transition declares it depends on
        if requires is not None and not self._resolves(requires):
            self.refused += 1
            raise SeveranceError("refuse to advance state: required provenance does not resolve")
        edit = Edit(event.target, event.previous, event.new, event.source,
                    event.justification, event.scope, depends_on=requires, survival_tests=event.survival)
        self.world.apply(edit)
        receipt = CommitReceipt(event.target, event.previous, event.new, event.source,
                                tuple(event.dependencies), edit.digest())
        self.receipts.append(receipt)
        return receipt
