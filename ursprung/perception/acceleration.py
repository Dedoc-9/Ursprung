# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/acceleration.py — Δvelocity: stabilizing vs diverging, and crisis as acceleration not level.

`trajectory.py` gave a claim a position `(accountability, correspondence)` and a velocity `(Δacc, Δcorr)`. But
velocity under-determines the *regime* — two claims can share a velocity and be in completely different
situations:

    t1: (0.2, 0.2) → (0.4, 0.4)     velocity (+0.2, +0.2)   — fragile-early, just leaving the floor
    t2: (0.8, 0.8) → (1.0, 1.0)     velocity (+0.2, +0.2)   — consolidating-late, near the ceiling

Same motion, different regime. The missing quantity is the **second derivative**:

    state        = (accountability, correspondence)
    velocity     = (Δaccountability, Δcorrespondence)
    acceleration = Δvelocity                              ← whether the process is stabilizing or diverging

Two payoffs that velocity alone cannot give:

1. **Stabilizing vs diverging.** When acceleration opposes velocity the motion is slowing — the claim is
   *stabilizing* (converging toward a settle). When acceleration aligns with velocity the motion is speeding
   up — the claim is *diverging*. `(0.2,0.2)→(0.6,0.6)→(0.8,0.8)` (speed 0.8 → 0.4) is stabilizing;
   `(0.8,0.8)→(0.7,0.6)→(0.5,0.2)` (speed 0.3 → 0.6) is diverging.

2. **Crisis is acceleration, not level.** A theory entering deep crisis is usually not just declining — the
   *rate* of decline is worsening. Steady decline (`Δcorr` constant, `Δ²corr ≈ 0`) and accelerating crisis
   (`Δcorr < 0` and `Δ²corr < 0`) share the same instantaneous sign of motion; only the second derivative tells
   them apart. `declining ≠ accelerating-decline`, just as `trajectory` taught `integrity-gain ≠ progress` and
   `ledgers` taught `integrity ≠ truth`. The danger this catches: a result whose adequacy is falling faster
   each step, while its accountability stays pinned at 1.0 — a confident model losing the world at an
   increasing rate.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: kinematic bookkeeping, one derivative past
`trajectory` — it names whether motion is speeding up or slowing down and inherits the toy adequacy axis
(`simulation ≠ physics`). It describes the *shape* of the motion; it does not explain or predict it (no
dynamical model of *why* a claim accelerates — that would itself be an `F`, with all the model-relativity
caveats). Separators: velocity ≠ regime; declining ≠ accelerating-decline; speeding-up ≠ progress.
"""
from __future__ import annotations

_EPS = 0.05  # dead-band: below this a derivative counts as zero


def velocities(path):
    """First derivative: the step-to-step change in (accountability, correspondence)."""
    return [(round(path[i + 1][0] - path[i][0], 3), round(path[i + 1][1] - path[i][1], 3))
            for i in range(len(path) - 1)]


def accelerations(path):
    """Second derivative: the step-to-step change in velocity."""
    v = velocities(path)
    return [(round(v[i + 1][0] - v[i][0], 3), round(v[i + 1][1] - v[i][1], 3)) for i in range(len(v) - 1)]


def _speed(v):
    """Scalar magnitude of a velocity (L1 — integer-friendly)."""
    return round(abs(v[0]) + abs(v[1]), 3)


def regime(path):
    """Stabilizing (motion slowing) / diverging (motion speeding up) / steady (constant speed). Needs ≥3 points
    — i.e. it needs acceleration; velocity alone cannot tell these apart."""
    v = velocities(path)
    if len(v) < 2:
        return "unknown"          # only one velocity sample → no acceleration → regime undefined
    s0, s1 = _speed(v[-2]), _speed(v[-1])
    if s1 < s0 - _EPS:
        return "stabilizing"      # decelerating — converging toward a settle
    if s1 > s0 + _EPS:
        return "diverging"        # accelerating away
    return "steady"               # constant velocity


def crisis(path):
    """Classify motion on the correspondence (adequacy) axis: accelerating_crisis / steady_decline /
    decline_arresting / not_declining. Crisis is the second derivative, not the level."""
    v = velocities(path)
    a = accelerations(path)
    dv = v[-1][1] if v else 0.0          # current correspondence velocity
    da = a[-1][1] if a else 0.0          # current correspondence acceleration
    if dv < -_EPS and da < -_EPS:
        return "accelerating_crisis"      # declining, and the decline is worsening
    if dv < -_EPS and abs(da) <= _EPS:
        return "steady_decline"           # declining at a constant rate
    if dv < -_EPS and da > _EPS:
        return "decline_arresting"        # still declining, but slowing — possible recovery
    return "not_declining"


# --- the crucible -----------------------------------------------------------------------------------

T1 = [(0.2, 0.2), (0.4, 0.4)]                       # fragile-early
T2 = [(0.8, 0.8), (1.0, 1.0)]                       # consolidating-late  (same velocity as T1)
STEADY_DECLINE = [(1.0, 0.9), (1.0, 0.8), (1.0, 0.7)]       # Δcorr = -0.1 constant, Δ²corr = 0
ACCELERATING_CRISIS = [(1.0, 0.9), (1.0, 0.8), (1.0, 0.5)]  # Δcorr -0.1 → -0.3, Δ²corr = -0.2
STABILIZING = [(0.2, 0.2), (0.6, 0.6), (0.8, 0.8)]          # speed 0.8 → 0.4 (slowing)
DIVERGING = [(0.8, 0.8), (0.7, 0.6), (0.5, 0.2)]            # speed 0.3 → 0.6 (speeding up)


def crucible():
    out = {}
    # acceleration is the change in velocity (needs ≥3 points)
    out["acceleration_is_delta_velocity"] = accelerations(STEADY_DECLINE) == [(0.0, 0.0)] and accelerations(ACCELERATING_CRISIS) == [(0.0, -0.2)]
    # same velocity, different regime → velocity under-determines the situation
    out["same_velocity_different_regime"] = velocities(T1) == velocities(T2) and T1[0] != T2[0]
    # crisis is the second derivative, not the level: steady decline vs accelerating crisis
    out["steady_decline_classified"] = crisis(STEADY_DECLINE) == "steady_decline"
    out["accelerating_crisis_classified"] = crisis(ACCELERATING_CRISIS) == "accelerating_crisis"
    # both are declining (same sign of velocity) — only acceleration separates them
    out["declining_not_equal_accelerating_decline"] = (crisis(STEADY_DECLINE) != crisis(ACCELERATING_CRISIS)
                                                       and velocities(STEADY_DECLINE)[-1][1] < 0
                                                       and velocities(ACCELERATING_CRISIS)[-1][1] < 0)
    # stabilizing vs diverging (the regime), and that it needs acceleration to tell apart
    out["stabilizing_classified"] = regime(STABILIZING) == "stabilizing"
    out["diverging_classified"] = regime(DIVERGING) == "diverging"
    out["regime_needs_acceleration"] = regime(STABILIZING) != regime(DIVERGING)
    # constant velocity → zero acceleration → steady regime
    out["zero_acceleration_is_steady"] = regime(STEADY_DECLINE) == "steady" and accelerations(STEADY_DECLINE) == [(0.0, 0.0)]
    return out


def demo():
    r = crucible()
    print("Acceleration — Δvelocity: stabilizing vs diverging, crisis as acceleration not level\n")
    print("  velocity ≠ regime: t1 (0.2,0.2)→(0.4,0.4) and t2 (0.8,0.8)→(1.0,1.0) share velocity %s,"
          % str(velocities(T1)[0]))
    print("    yet are different regimes (fragile-early vs consolidating-late): %s" % r["same_velocity_different_regime"])
    print()
    print("  crisis is the SECOND derivative, not the level:")
    print("    steady_decline      Δcorr const, Δ²corr=%s → %s" % (accelerations(STEADY_DECLINE)[0][1], crisis(STEADY_DECLINE)))
    print("    accelerating_crisis Δcorr falling faster, Δ²corr=%s → %s" % (accelerations(ACCELERATING_CRISIS)[0][1], crisis(ACCELERATING_CRISIS)))
    print("    both are declining; only acceleration separates them: %s" % r["declining_not_equal_accelerating_decline"])
    print()
    print("  stabilizing (speed %s→%s) vs diverging (speed %s→%s): %s / %s"
          % (_speed(velocities(STABILIZING)[0]), _speed(velocities(STABILIZING)[1]),
             _speed(velocities(DIVERGING)[0]), _speed(velocities(DIVERGING)[1]),
             r["stabilizing_classified"], r["diverging_classified"]))
    print("\n  velocity ≠ regime; declining ≠ accelerating-decline. the shape of the motion is evidence too.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.acceleration", OBSERVER, mutates_core=False,
                          note="Δvelocity over claim-state space: acceleration distinguishes stabilizing "
                               "(motion slowing) from diverging (speeding up), which share a velocity; and "
                               "accelerating_crisis (Δcorr<0 AND Δ²corr<0) from steady_decline (Δ²corr≈0), "
                               "which share a velocity sign. velocity != regime; declining != "
                               "accelerating-decline. Kinematic bookkeeping, one derivative past trajectory; "
                               "describes the shape of motion, does not explain it")
    except LayerViolation:
        pass
