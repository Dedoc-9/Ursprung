# SPDX-License-Identifier: AGPL-3.0-only
"""ToyGridScene — the minimal interactive system with a constructible secret→observable channel.

Implements the `Client` protocol. Two sampling modes, kept distinct on purpose:

* `step()` — TRAJECTORY dynamics: the NPC moves one cell per frame in its (hidden) goal direction, clamped at
  the walls. This is the regime the closed-loop demo runs in. Its position distribution is whatever the dynamics
  produce — there is no analytic MI for it.
* `sample_iid()` — VALIDATION sampling: the NPC is re-placed uniformly at random and a fresh uniform goal is
  drawn each call, so the distribution exactly matches `analytic_mi.analytic_mi(...)`. The estimator is validated
  against the analytic value ONLY on these i.i.d. samples. `analytic ≠ trajectory`.

The channel (`coarsen`) is imported from the validation anchor so the scene and the ground truth can never
drift apart. Fidelity = the detail radius (larger ⇒ more detail ⇒ more leakage; shrink to reduce leakage).
"""
from __future__ import annotations

import os
import random
import sys
from typing import Tuple

# the anchor (same dir) and the repo-root package, importable whether run directly or imported
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
for _p in (_HERE, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from analytic_mi import GOALS, coarsen  # noqa: E402
from channel_profiler.messages import SampleMessage  # noqa: E402

Pos = Tuple[int, int]
_MOVE = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}


class ToyGridScene:
    """A width×height grid with one hidden NPC (position + goal) and a coarsened observer view."""

    def __init__(
        self,
        width: int = 10,
        height: int = 10,
        observer_pos: Pos = (4, 4),
        radius: int = 2,
        seed: int = 0,
        session_id: str = "toy",
    ) -> None:
        self.width = width
        self.height = height
        self.observer_pos = observer_pos
        self._radius = int(radius)
        self.session_id = session_id
        self._rng = random.Random(seed)
        self._frame = 0
        self._npc: Pos = (self._rng.randrange(height), self._rng.randrange(width))
        self._goal = self._rng.choice(GOALS)

    # ---- Client protocol --------------------------------------------------------------------------
    def step(self) -> SampleMessage:
        """Advance the trajectory one frame and emit the tagged sample."""
        dr, dc = _MOVE[self._goal]
        r = min(self.height - 1, max(0, self._npc[0] + dr))
        c = min(self.width - 1, max(0, self._npc[1] + dc))
        self._npc = (r, c)
        return self._emit()

    def apply_fidelity(self, level: float) -> None:
        """Set the detail radius (advisory; the host chooses to call this). Clamped to [0, max grid extent]."""
        max_r = max(self.width, self.height)
        self._radius = int(max(0, min(max_r, round(level))))

    @property
    def current_fidelity(self) -> float:
        return float(self._radius)

    # ---- validation sampler (i.i.d. uniform — matches the analytic prior) -------------------------
    def sample_iid(self) -> SampleMessage:
        """Re-place the NPC uniformly and draw a fresh uniform goal, then emit. Distribution == analytic prior."""
        self._npc = (self._rng.randrange(self.height), self._rng.randrange(self.width))
        self._goal = self._rng.choice(GOALS)
        return self._emit()

    # ---- shared emission --------------------------------------------------------------------------
    def _emit(self) -> SampleMessage:
        view = coarsen(self._npc, self.observer_pos, self._radius)
        msg = SampleMessage(
            session_id=self.session_id,
            frame=self._frame,
            secret_tags={"npc_pos": self._npc, "goal": self._goal},
            observation_tags={"view": view},
            fidelity_level=float(self._radius),
        )
        self._frame += 1
        return msg


if __name__ == "__main__":
    sc = ToyGridScene(seed=1, radius=2)
    print("5 i.i.d. validation samples (uniform prior):")
    for _ in range(5):
        m = sc.sample_iid()
        print(f"  frame={m.frame} secret={m.secret_tags} view={m.observation_tags['view']} r={m.fidelity_level}")
    print("5 trajectory steps (NPC moves toward goal):")
    sc2 = ToyGridScene(seed=1, radius=2)
    for _ in range(5):
        m = sc2.step()
        print(f"  frame={m.frame} npc={m.secret_tags['npc_pos']} goal={m.secret_tags['goal']} view={m.observation_tags['view']}")
