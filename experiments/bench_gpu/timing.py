# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/timing.py — the GPU-interval ruler, CPU timing (provenance), and latency (a separate
instrument).

Two times, not one: the budget comparator uses ONLY the GPU interval (`gpu_end − gpu_begin`); CPU times are
recorded as provenance but are never the ruler. Present-to-photon is a separate latency experiment, kept out
of fidelity — otherwise a good reconstruction could hide a terrible interaction loop.

Note the deliberate asymmetry with the temporal-error profile: a LatencyProfile MAY sum (its stages are a
physical chain of sequential real durations — input → photon), whereas a TemporalErrorProfile may NOT
(its axes are incommensurable failure modes). Summing is legitimate only where the quantities are additive.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GpuInterval:
    """The equal-budget ruler. Duration is measured by GPU timestamp queries, not CPU wall time."""

    begin_tick: int
    end_tick: int

    def duration(self) -> int:
        return self.end_tick - self.begin_tick


@dataclass(frozen=True)
class CpuTiming:
    """Recorded as run-provenance — NOT the budget ruler. Kept so the host side is inspectable. Note
    `cpu_observed_gpu_duration` is the deliberately uglier name: it is the HOST's estimate of GPU time, which
    must never be confused with `GpuInterval.duration()` (the authoritative GPU-timestamp ruler)."""

    cpu_submission_latency: float
    cpu_observed_gpu_duration: float    # host-side observation, NOT the ruler (cf. GpuInterval.duration())
    present_latency: float


@dataclass(frozen=True)
class LatencyProfile:
    """input → photon, as a separate instrument. Its stages are a physical chain, so a total is meaningful."""

    input_to_submit: float
    submit_to_gpu_done: float
    gpu_done_to_present: float
    present_to_photon: float

    def total(self) -> float:
        return (self.input_to_submit + self.submit_to_gpu_done
                + self.gpu_done_to_present + self.present_to_photon)
