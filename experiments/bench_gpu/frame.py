# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/frame.py — the immutable frame description and the backend-agnostic golden replay.

The backend does NOT decide whether a frame is valid; it CONSUMES an immutable description and measures
what happened. That preserves the kernel boundary: `kernel → describes what · backend → measures what
happened`. A `GoldenReplay` is a benchmark artifact (NOT a renderer format) — the same artifact replays on
the reference backend, the real GPU backend, and any future native implementation, so the renderer becomes
just another substrate that must preserve the kernel's distinctions.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


def _require_provenance(d: str):
    # a provenance digest must be a real digest, never a bare label — the kernel learned strings are easy to
    # downgrade into labels. (A `Digest` value object would make this a type guarantee; this is the floor.)
    if not d or d in ("unknown", "none", "null"):
        raise ValueError("provenance_digest must be a real digest, not empty or a placeholder label")


@dataclass(frozen=True)
class FrameArtifact:
    """The immutable frame description a backend consumes. Its identity is the world's, not the render's —
    computed from scene/transform/policy/provenance digests, never from any rendered output. A pixel
    difference is a measurement result: not an artifact mutation, and not a provenance replacement. The image
    hash is another receipt, never the lineage."""

    scene_digest: str
    transform_digest: str
    policy_id: str
    provenance_digest: str

    def __post_init__(self):
        _require_provenance(self.provenance_digest)

    def digest(self) -> str:
        return _digest(asdict(self))


@dataclass(frozen=True)
class GoldenReplay:
    """A benchmark artifact — replayable across backends. Not a renderer format; a deterministic *recipe* for
    a frame (like an `Event`, it explains how the frame is produced, it is not the frame). It carries the
    experiment's IDENTITY only — scene, seed, policy, provenance. The GPU budget is an EXECUTION CONDITION,
    not part of identity (the same artifact may be measured at 1/2/4/8 ms without becoming a different thing),
    so it lives on the BenchmarkObservation, not here. `object identity ≠ execution conditions`."""

    scene: str
    seed: int
    policy: str
    provenance_digest: str

    def __post_init__(self):
        _require_provenance(self.provenance_digest)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)

    @staticmethod
    def from_json(s: str) -> "GoldenReplay":
        return GoldenReplay(**json.loads(s))

    def frame(self) -> FrameArtifact:
        """Derive the immutable FrameArtifact this golden describes — deterministic and backend-agnostic, so
        the same golden yields the same frame identity on every backend."""
        return FrameArtifact(
            scene_digest=_digest([self.scene, self.seed]),
            transform_digest=_digest([self.scene, self.seed, "transform"]),
            policy_id=self.policy,
            provenance_digest=self.provenance_digest,
        )
