# SPDX-License-Identifier: AGPL-3.0-only
"""Ursprung Channel Profiler (v0.1) — measure the bits an observer learns about a secret, with error bars.

A STANDALONE, pure-Python package. It deliberately does NOT live under `ursprung/`: that package's __init__
eagerly imports the sealed-workbench renderer, which would couple the profiler to `Reality_Engine`. The profiler
is a separate wedge — OBSERVER-class (it measures and reports; it never controls the host loop). Adaptation is
advisory. `telemetry ≠ control`; `estimate ≠ capacity`; `measured ≠ guaranteed`.

Light __init__: re-exports only the dependency-free message/protocol types. The estimator (which needs numpy)
is imported directly (`from channel_profiler.estimator import MillerMadowEstimator`) so `import channel_profiler`
stays cheap.
"""
from channel_profiler.messages import (  # noqa: F401
    CapacityReport,
    ChannelEstimate,
    SampleMessage,
    SessionConfig,
)
from channel_profiler.protocols import ChannelEstimator, Client  # noqa: F401

__version__ = "0.1.0"
