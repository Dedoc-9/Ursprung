# SPDX-License-Identifier: AGPL-3.0-only
"""The wire-shaped message types — defined BEFORE any logic (Architecture Decision #1).

In v0.1 these are passed in-process between scene → window manager → estimator. They are shaped like a future
wire format (a `protocol_version` field is present from day one) so a later transport (WebSocket/gRPC) and a
multi-session backend can serialize them unchanged. `protocol shape is destiny` — keep these minimal, explicit,
versioned. No speculative fields.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ChannelEstimate:
    """The estimator's honest output. Never a bare scalar.

    `mi_estimate`/`ci_lower`/`ci_upper` are None unless `verdict == "ESTIMATED"`. The alphabet sizes are the
    OBSERVED distinct-symbol counts in the window (not the universe), so a reader can see the regime the estimate
    was made in.

    `effective_n` (v0.2.1): the temporal-correlation-corrected sample count. Under i.i.d. sampling it equals
    `n_samples`; under autocorrelation it is smaller (n / integrated-autocorrelation-time). It is the count the
    sufficiency gate should use on real streams. `None` for the i.i.d. estimator, which does not compute it.
    `effective_n ≤ n_samples`; `i.i.d.-n ≠ effective-n`.
    """

    mi_estimate: Optional[float]
    ci_lower: Optional[float]
    ci_upper: Optional[float]
    estimator: str
    n_samples: int
    alphabet_size_secret: int
    alphabet_size_observation: int
    verdict: str  # "ESTIMATED" | "UNDERDETERMINED" | "INSUFFICIENT_ALPHABET"
    effective_n: Optional[int] = None


@dataclass
class SampleMessage:
    """One tagged interaction step the client emits. `secret_tags`/`observation_tags` are plain dicts; the
    estimator canonicalizes them to hashable symbols. `fidelity_level` is the host's current detail radius
    (larger = more detail = more leakage)."""

    session_id: str
    frame: int
    secret_tags: Dict[str, Any]
    observation_tags: Dict[str, Any]
    fidelity_level: float
    protocol_version: int = 1


@dataclass
class CapacityReport:
    """What the profiler reports back per window. ADVISORY: `suggested_fidelity` is a suggestion the host may
    ignore (`telemetry ≠ control`)."""

    session_id: str
    window_start: int
    window_end: int
    estimate: ChannelEstimate
    budget: float
    verdict: str  # "BELOW_BUDGET" | "ABOVE_BUDGET" | "UNDERDETERMINED"
    suggested_fidelity: Optional[float]
    protocol_version: int = 1


@dataclass
class SessionConfig:
    """Per-session policy. `window_size` is a sample count (not a frame count — MI needs samples, not frames)."""

    session_id: str
    budget_bits_per_step: float
    window_size: int
    estimator: str = "miller_madow"
    adaptation_mode: str = "advisory"  # "advisory" | "automatic"
