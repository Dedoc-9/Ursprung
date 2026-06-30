# SPDX-License-Identifier: AGPL-3.0-only
"""The two structural interfaces. A future Rust port mirrors `ChannelEstimator`; a real game/sim/agent client
mirrors `Client`. Keeping these narrow is what lets the transport and the language change underneath without a
protocol migration.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from channel_profiler.messages import ChannelEstimate, SampleMessage


@runtime_checkable
class ChannelEstimator(Protocol):
    """Stateful per-window MI estimator. A Rust implementation will mirror these four methods."""

    def ingest(self, sample: SampleMessage) -> None:
        """Add one sample to the current window."""
        ...

    def estimate(self) -> ChannelEstimate:
        """MI estimate (with CIs) over the current window; UNDERDETERMINED if samples are insufficient."""
        ...

    def reset_window(self) -> None:
        """Drop the current window (e.g. after a fidelity change — the channel changed)."""
        ...

    def stats(self) -> dict:
        """Diagnostics (n_samples, alphabet sizes, …) — the future metrics surface."""
        ...


@runtime_checkable
class Client(Protocol):
    """An interactive system the profiler wraps. The toy scene implements this; so would a real engine."""

    def step(self) -> SampleMessage:
        """Advance one frame; return the tagged (secret, observation) pair."""
        ...

    def apply_fidelity(self, level: float) -> None:
        """Adjust rendering fidelity (here: the detail radius). Advisory — the host chooses to honor it."""
        ...

    @property
    def current_fidelity(self) -> float:
        ...
