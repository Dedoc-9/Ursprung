# SPDX-License-Identifier: AGPL-3.0-only
"""WindowManager — the *trigger policy*, kept separate from the estimator (Architecture Decision #4).

It decides WHEN to estimate (window full) and detects a fidelity change (the channel changed ⇒ the old samples
are from a different distribution and must be dropped). It carries no statistics — that is the estimator's job.
This separation is what makes a future multi-session backend a `HashMap<SessionId, (WindowManager, Estimator)>`
rather than a rewrite.
"""
from __future__ import annotations

from typing import List, Optional

from channel_profiler.messages import SampleMessage, SessionConfig


class WindowManager:
    def __init__(self, config: SessionConfig) -> None:
        self.config = config
        self.samples: List[SampleMessage] = []
        self.last_fidelity: Optional[float] = None
        self.reset_signal: bool = False  # set True on the push where fidelity changed (loop resets the estimator)

    def push(self, sample: SampleMessage) -> bool:
        """Buffer a sample; return True when the window is full. Clears the window (and raises `reset_signal`)
        when the fidelity level changes, since post-change samples come from a different channel."""
        self.reset_signal = False
        if self.last_fidelity is not None and sample.fidelity_level != self.last_fidelity:
            self.samples.clear()
            self.reset_signal = True
        self.last_fidelity = sample.fidelity_level
        self.samples.append(sample)
        return len(self.samples) >= self.config.window_size

    def clear(self) -> None:
        self.samples.clear()

    def __len__(self) -> int:
        return len(self.samples)
