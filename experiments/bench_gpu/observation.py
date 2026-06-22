# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/observation.py — BenchmarkObservation: a measurement that carries its own provenance.

This completes the symmetry the kernel established, now applied to measurement itself: a number cannot exist
without the conditions that produced it.

    TemporalErrorProfile without a BenchmarkObservation  =  UNACCOUNTED measurement

An observation binds the *what* (the FrameArtifact identity measured), the *conditions* (device / driver /
backend / GPU budget — execution conditions, not identity), the *measurement* (the GPU-interval ruler + the
temporal-error profile, with latency as an optional separate instrument), and the *why* (the provenance
digest). Three distinct fields are kept distinct on purpose and never collapsed into one:

    artifact_digest    = what was requested + transformed (the image/representation receipt)
    temporal_profile   = what the backend observed (a measurement)
    provenance_digest  = why this artifact exists (the lineage)

The image hash is another receipt, not the lineage; the measurement is an observation, not the identity.
The harness should emit ONLY observations — a bare profile or interval that is not bound into one is refused.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from contract import RunRecord, TemporalErrorProfile, _digest
from frame import FrameArtifact, _require_provenance
from timing import GpuInterval, LatencyProfile

UNACCOUNTED = "UNACCOUNTED"


@dataclass(frozen=True)
class BenchmarkObservation:
    artifact_digest: str                  # the FrameArtifact identity that was measured
    run: RunRecord                        # device / power / driver / backend / resolution / temp / commit
    backend: str                          # which backend produced the measurement (fixture | real_gpu | …)
    gpu_budget: int                       # an EXECUTION CONDITION (not part of the artifact's identity)
    gpu_interval: GpuInterval             # the authoritative GPU-timestamp ruler measurement
    temporal_profile: TemporalErrorProfile
    provenance_digest: str                # why the measured artifact exists (the lineage receipt)
    latency_profile: Optional[LatencyProfile] = None   # a separate instrument; optional

    def __post_init__(self):
        _require_provenance(self.provenance_digest)

    def status(self) -> str:
        # a measurement that does not carry its full run-provenance is UNACCOUNTED — never silently usable
        if self.run.status() != "recorded" or self.run.backend != self.backend:
            return UNACCOUNTED
        return "recorded"

    def digest(self) -> str:
        return _digest({
            "artifact_digest": self.artifact_digest,
            "run": self.run.digest(),
            "backend": self.backend,
            "gpu_budget": self.gpu_budget,
            "gpu_interval": [self.gpu_interval.begin_tick, self.gpu_interval.end_tick],
            "temporal_profile": self.temporal_profile.axes(),
            "provenance_digest": self.provenance_digest,
            "latency_profile": None if self.latency_profile is None else self.latency_profile.total(),
        })


def observe(backend, frame: FrameArtifact, run: RunRecord, gpu_budget: int,
            latency: Optional[LatencyProfile] = None) -> BenchmarkObservation:
    """Run a backend and bind its output into a self-describing observation. Refuses to emit a measurement
    whose run-provenance is incomplete (UNACCOUNTED) — there is no path to a bare, unbound number."""
    if run.status() != "recorded":
        raise ValueError("UNACCOUNTED: a measurement requires complete run-provenance (missing: %s)"
                         % ", ".join(run.missing()))
    profile, interval = backend.render(frame, gpu_budget)
    return BenchmarkObservation(
        artifact_digest=frame.digest(),
        run=run,
        backend=backend.name,
        gpu_budget=gpu_budget,
        gpu_interval=interval,
        temporal_profile=profile,
        provenance_digest=frame.provenance_digest,
        latency_profile=latency,
    )
