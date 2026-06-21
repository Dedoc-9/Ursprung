# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/artifact.py — Artifact: a thing with DECLARED provenance.

The most general object in the kernel: anything that exists or is claimed. Its identity includes its
provenance (the meta-invariant), so an Artifact cannot be constructed without one — `claim_digest()`
is what is asserted (kind + content), `digest()` is the full identity (claim + provenance). The two
differ precisely because provenance is part of the identity, not metadata attached to it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict

UNRECORDED = "<unrecorded>"


def digest_of(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


@dataclass
class Artifact:
    kind: str
    content: Any
    provenance: Dict[str, Any]
    evidence: Dict[str, Any] = field(default_factory=dict)
    status: str = "declared"

    def __post_init__(self):
        if not self.provenance:
            raise ValueError("an Artifact must carry declared provenance (identity includes provenance)")

    def claim_digest(self) -> str:
        """What is asserted — kind + content, independent of how it came to be."""
        return digest_of({"kind": self.kind, "content": self.content})

    def digest(self) -> str:
        """The full identity — claim + provenance. Differs from claim_digest because provenance is
        part of the identity, not an annotation on it."""
        return digest_of({"kind": self.kind, "content": self.content, "provenance": self.provenance})
