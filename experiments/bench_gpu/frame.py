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


@dataclass(frozen=True)
class FrameArtifact:
    """The immutable frame description a backend consumes. Its identity is the world's, not the render's —
    computed from scene/transform/policy/provenance digests, never from any rendered output."""

    scene_digest: str
    transform_digest: str
    policy_id: str
    provenance_digest: str

    def digest(self) -> str:
        return _digest(asdict(self))


@dataclass(frozen=True)
class GoldenReplay:
    """A benchmark artifact — replayable across backends. Not a renderer format; a deterministic description
    of what to measure and at what GPU budget."""

    scene: str
    seed: int
    policy: str
    frame_budget_gpu_ticks: int
    provenance_digest: str

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
