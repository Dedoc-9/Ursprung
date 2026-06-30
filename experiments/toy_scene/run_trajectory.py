# SPDX-License-Identifier: AGPL-3.0-only
"""run_trajectory.py — produce a stream of (secret, observation) samples from the toy scene as JSONL.

Two modes:
  --mode iid         i.i.d. uniform placement (matches the analytic prior; the validation regime)
  --mode trajectory  the NPC moves greedily toward its goal (the demo regime)

Each line is one SampleMessage rendered to JSON. Useful for offline replay through the estimator and for
eyeballing the channel. This is plumbing, not the thesis — the closed loop lives in demo_closed_loop.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from scene import ToyGridScene  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--radius", type=int, default=2)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mode", choices=["iid", "trajectory"], default="iid")
    args = ap.parse_args()

    sc = ToyGridScene(seed=args.seed, radius=args.radius)
    emit = sc.sample_iid if args.mode == "iid" else sc.step
    for _ in range(args.n):
        m = emit()
        print(json.dumps({
            "session": m.session_id,
            "frame": m.frame,
            "secret": {k: list(v) if isinstance(v, tuple) else v for k, v in m.secret_tags.items()},
            "observation": {k: list(v) if isinstance(v, tuple) else v for k, v in m.observation_tags.items()},
            "fidelity": m.fidelity_level,
            "protocol_version": m.protocol_version,
        }))


if __name__ == "__main__":
    main()
