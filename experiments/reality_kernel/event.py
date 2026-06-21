# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/event.py — Event: a transition with lineage.

An Event is how an Artifact changed: target, previous → new, and a **source** (who/what produced the
change). A transition without a named source is a silent mutation, which the runtime forbids — so an
Event cannot be constructed without one. The Event is pure data; turning it into a committed world
change (and validating its provenance) is the CommitChannel's job, not the Event's.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class Event:
    target: str
    previous: Any
    new: Any
    source: str
    dependencies: List[str] = field(default_factory=list)
    survival: List[bool] = field(default_factory=list)
    justification: str = "—"
    scope: str = "—"

    def __post_init__(self):
        if not self.source:
            raise ValueError("an Event must name a source — no transition without lineage")

    def record(self) -> dict:
        return {"target": self.target, "previous": self.previous, "new": self.new,
                "source": self.source, "dependencies": list(self.dependencies),
                "survival": list(self.survival)}
