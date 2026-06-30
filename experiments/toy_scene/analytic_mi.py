# SPDX-License-Identifier: AGPL-3.0-only
"""analytic_mi.py — the VALIDATION ANCHOR for the Ursprung Channel Profiler v0.1.

It defines the channel (the coarsening / fog-of-war observation function) and computes the EXACT mutual
information I(S;O) for a fixed detail radius, by enumeration over the secret space under a uniform i.i.d. prior.

Why this is the anchor: for a *deterministic* observation function O = coarsen(S), the conditional entropy
H(O|S) = 0, so I(S;O) = H(O). We still compute it via the general joint formula
    I(S;O) = Σ_{s,o} p(s,o) log2[ p(s,o) / (p(s) p(o)) ]
so the estimator (which uses the same formula on samples) is being checked against the *same* quantity, not a
shortcut. The estimator validated against this must RECOVER this number within its confidence interval.

Distribution-matching note (load-bearing): this analytic value is the ground truth ONLY under the i.i.d. uniform
prior over (position, goal). The validation harness therefore samples i.i.d. (`ToyGridScene.sample_iid`). The
closed-loop demo uses moving-NPC *trajectory* dynamics, whose distribution differs — there is no analytic anchor
for the trajectory; the demo measures empirical leakage and shows convergence. `analytic ≠ trajectory`.

Channel definition (the one knob): `radius r` is the DETAIL radius (Chebyshev). Cells within r of the observer
are seen exactly (the NPC there is localized); everything else collapses to a single "FAR" symbol (the observer
cannot localize a distant NPC). Larger r ⇒ more cells localized ⇒ higher H(O) ⇒ MORE leakage. To REDUCE leakage
you SHRINK r. (This fixes the spec's self-contradictory "widen radius to reduce leakage": `fidelity = detail
radius`, larger = more leakage.)
"""
from __future__ import annotations

import math
from typing import Tuple

Pos = Tuple[int, int]
GOALS = ("N", "S", "E", "W")


def coarsen(npc_pos: Pos, observer_pos: Pos, radius: int) -> tuple:
    """The observation symbol the observer sees for an NPC at `npc_pos`.

    Within Chebyshev `radius` of the observer → the exact relative offset (full detail, NPC localized).
    Otherwise → the single ``("FAR",)`` symbol (the far field is not localizable). Deterministic in `npc_pos`,
    so I(S;O) = H(O). The goal direction does not affect a single observation, so it cancels in the MI.
    """
    dr = npc_pos[0] - observer_pos[0]
    dc = npc_pos[1] - observer_pos[1]
    if max(abs(dr), abs(dc)) <= radius:
        return ("NEAR", dr, dc)
    return ("FAR",)


def _entropy_bits(dist: dict) -> float:
    """Shannon entropy (bits) of a probability dict; ignores zero-mass atoms."""
    h = 0.0
    for p in dist.values():
        if p > 0.0:
            h -= p * math.log2(p)
    return h


def analytic_mi(
    width: int = 10,
    height: int = 10,
    observer_pos: Pos = (4, 4),
    radius: int = 2,
    goals: tuple = GOALS,
) -> float:
    """Exact I(S;O) in bits under a uniform i.i.d. prior over S = (position, goal).

    `S` includes the goal (per spec) even though a single observation does not depend on it — the goal is
    independent uniform noise that cancels exactly in the MI, so the result equals H(O). Computing the full
    joint formula makes that cancellation a *check*, not an assumption.
    """
    positions = [(r, c) for r in range(height) for c in range(width)]
    states = [(p, g) for p in positions for g in goals]
    n_states = len(states)
    p_state = 1.0 / n_states

    joint: dict = {}          # (s, o) -> prob
    p_s: dict = {}            # s -> prob
    p_o: dict = {}            # o -> prob
    for s in states:
        pos, _goal = s
        o = coarsen(pos, observer_pos, radius)
        joint[(s, o)] = joint.get((s, o), 0.0) + p_state
        p_s[s] = p_s.get(s, 0.0) + p_state
        p_o[o] = p_o.get(o, 0.0) + p_state

    mi = 0.0
    for (s, o), p_so in joint.items():
        mi += p_so * math.log2(p_so / (p_s[s] * p_o[o]))
    return mi


def observation_entropy(
    width: int = 10,
    height: int = 10,
    observer_pos: Pos = (4, 4),
    radius: int = 2,
) -> float:
    """H(O) in bits under the uniform prior over positions — equals analytic_mi() for the deterministic channel.

    Provided as an independent cross-check of `analytic_mi` (they must agree to within float error)."""
    positions = [(r, c) for r in range(height) for c in range(width)]
    p_o: dict = {}
    for pos in positions:
        o = coarsen(pos, observer_pos, radius)
        p_o[o] = p_o.get(o, 0.0) + 1.0 / len(positions)
    return _entropy_bits(p_o)


def observation_alphabet_size(
    width: int = 10, height: int = 10, observer_pos: Pos = (4, 4), radius: int = 2
) -> int:
    """Number of distinct observation symbols reachable on the grid (|O|)."""
    positions = [(r, c) for r in range(height) for c in range(width)]
    return len({coarsen(pos, observer_pos, radius) for pos in positions})


if __name__ == "__main__":
    W = H = 10
    obs = (4, 4)
    print(f"Toy channel: {W}x{H} grid, observer at {obs}, Chebyshev detail radius r.")
    print("r   |O|   I(S;O)=H(O) bits   (larger r ⇒ more leakage; shrink r to reduce)")
    for r in range(0, 6):
        mi = analytic_mi(W, H, obs, r)
        ho = observation_entropy(W, H, obs, r)
        k = observation_alphabet_size(W, H, obs, r)
        flag = "  [MI==H(O) check OK]" if abs(mi - ho) < 1e-9 else "  [MISMATCH!]"
        print(f"{r}   {k:3d}   {mi:8.4f}{flag}")
