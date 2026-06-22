# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/backends.py — the reference backend (no pixels) and the real GPU backend (the seam).

The determinism boundary, made structural:

    CORE  — deterministic artifact graph / transforms / digests   (FrameArtifact identity lives here)
    GPU   — implementation of rendering, performance observations, pixel output   (measurements live here)

A pixel difference is a *measurement result*: not a new world state, not an artifact mutation, and not a
provenance replacement — the image hash is another receipt, never the lineage. Nothing a backend observes can
change the FrameArtifact's identity. The fixture backend renders no pixels; the real backend is the un-faked
seam.
"""
from __future__ import annotations

from contract import TemporalErrorProfile
from frame import FrameArtifact, _digest
from timing import GpuInterval


class FixtureBackend:
    """Deterministic, no pixels. NOT a reference *renderer* — a FIXTURE that validates the harness contract,
    never fidelity. Consumes a FrameArtifact, returns a synthetic profile fixture plus a GPU interval that
    spends exactly the budget. Its numbers are a fixture for the harness, not a measurement of anything."""

    name = "fixture"

    def render(self, frame: FrameArtifact, gpu_tick_budget: int):
        h = int(frame.digest(), 16)
        profile = TemporalErrorProfile(
            reconstruction_error=(h % 97) / 10.0,
            motion_instability=((h >> 7) % 89) / 10.0,
            boundary_discontinuity=((h >> 13) % 83) / 10.0,
            perceptual_artifact=((h >> 19) % 79) / 10.0,
        )
        interval = GpuInterval(begin_tick=0, end_tick=gpu_tick_budget)   # reference spends exactly the budget
        return profile, interval


class RealGpuBackend:
    """THE SEAM — the un-faked frontier. On the device (e.g. Z2 Extreme) it has exactly four jobs and no more:

      1. SUBMIT the immutable FrameArtifact as GPU work (it consumes; it does not decide validity).
      2. TIMESTAMP the actual GPU interval (gpu_end − gpu_begin) via timestamp queries — the budget ruler.
         CPU submit/present times are recorded as provenance, never the ruler.
      3. KEEP DETERMINISM ABOVE THE FLOAT BOUNDARY — GPU floating point / driver scheduling / clock drift
         stay in the measurement layer; they never enter the artifact graph or its digests.
      4. CAPTURE present-to-photon as a SEPARATE latency instrument, not mixed into fidelity.

    Not implemented here: the Vulkan/DX12/wgpu calls are device-only. Measurements are not faked."""

    name = "real_gpu"

    def render(self, frame: FrameArtifact, gpu_tick_budget: int):
        raise NotImplementedError(
            "real GPU backend (Vulkan/DX12/wgpu) — submit + GPU timestamp queries + present-to-photon on "
            "device; the API choice and implementation are the deliberately-boring next step, run on silicon")
