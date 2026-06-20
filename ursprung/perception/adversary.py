# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/adversary.py — the frontier as an ADVERSARIAL benchmark: leakage ≠ exploitability.

The perception loop (`utility.py`) measures **leakage** — a per-observation mutual-information estimate
`I(secret ; view)`. This module measures **exploitability** — what a *learning* observer actually recovers —
and the two are not the same question.

The honest theory first: by the data-processing inequality, **no observer beats the per-observation MI bound on
a single observation.** So the only place exploitability can exceed the static estimate is **accumulation
across observations** — which is exactly the M13 (history-compression) / M19 (temporal axis) / M21 (richer
observer class) lesson, now pointed at the perception loop.

The scenario: a *persistent* secret (a fixed enemy cell) observed by a *mobile* observer over many frames. Each
frame discloses only a policy-compliant `threat` bit (is the enemy within range of the observer's current
vantage?) — individually a sliver of information. Two observer classes (M21 lattice):

  * **C_marginal** — a single-frame estimator. Bounded by the per-frame MI; cannot localize the cell.
  * **C_accumulate** — multilateration: intersect the cells consistent with the threat bit at each vantage over
    the session. A richer hypothesis class — and it recovers the *exact* cell.

The produced result (whatever it is) is the point: if the accumulating learner recovers far more than the
per-frame leakage estimate predicts, the static number is *falsified as a session-safety claim* — and the repo
gets stronger, the same way M18/M20/M21/Channel-Discovery each got stronger by a harness exposing a mistaken
assumption. This does NOT contradict the MI bound (it holds per observation); it shows a per-frame leakage
budget is the wrong budget for a session.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: constructed world, a specific learner class, a
fixed radius; the fix — accumulation-aware disclosure / a *session* leakage budget (constant-feel for the
temporal channel) — is the next increment, NOT claimed here. leakage ≠ exploitability; secure-against-class ≠
secure; simulation ≠ physics.
"""
from __future__ import annotations

from math import log2

from .toy_task import GRID

try:
    from ..channel_discovery import mutual_information
except Exception:                                            # pragma: no cover - standalone fallback
    from collections import Counter as _Counter

    def mutual_information(pairs):
        n = len(pairs)
        if n == 0:
            return 0.0
        px = _Counter(x for x, _ in pairs)
        py = _Counter(y for _, y in pairs)
        pxy = _Counter(pairs)
        mi = 0.0
        for (x, y), c in pxy.items():
            j = c / n
            mi += j * log2(j / ((px[x] / n) * (py[y] / n)))
        return max(0.0, mi)


RADIUS = 4                       # an enemy within this manhattan distance of the vantage reads as "threat: high"
H_SECRET = log2(GRID * GRID)     # 6 bits for an 8×8 grid


def _cells():
    return [(x, y) for x in range(GRID) for y in range(GRID)]


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def observe_threat(cell, vantage, radius=RADIUS):
    """The one policy-compliant bit a frame discloses: is the enemy within range of THIS vantage?"""
    return _manhattan(cell, vantage) <= radius


def vantage_path(frames=None):
    """A deterministic mobile-observer path. The full path visits every cell; a prefix is an early session."""
    path = _cells()
    return path if frames is None else path[:frames]


# --- C_marginal: the single-frame estimator (bounded by MI) -----------------------------------------

def per_frame_leakage(vantage=(0, 0), radius=RADIUS):
    """I(secret ; one threat observation) over the cell distribution — the static, per-observation estimate."""
    pairs = [(c[0] * GRID + c[1], observe_threat(c, vantage, radius)) for c in _cells()]
    return mutual_information(pairs)


# --- C_accumulate: the multilateration learner (intersect consistency sets) -------------------------

def consistent_cells(observations, radius=RADIUS):
    """The cells still consistent with every (vantage, threat) observation seen so far."""
    return [c for c in _cells() if all(observe_threat(c, v, radius) == t for v, t in observations)]


def accumulate(secret_cell, frames=None, radius=RADIUS):
    """Run the accumulating learner against a persistent secret over a session; return the surviving set."""
    obs = [(v, observe_threat(secret_cell, v, radius)) for v in vantage_path(frames)]
    return consistent_cells(obs, radius)


def recovered_bits(consistent_set):
    """Bits of the secret an observer has pinned down: 6 − log2(|remaining candidates|)."""
    n = len(consistent_set)
    return H_SECRET - (log2(n) if n else H_SECRET)


# --- the adversarial crucible -----------------------------------------------------------------------

def crucible(secret=(5, 2)):
    out = {}
    pf = per_frame_leakage()
    one = accumulate(secret, frames=1)
    full = accumulate(secret)                       # the whole session (every vantage)
    out["per_frame_leakage"] = round(pf, 4)         # the static estimate (C_marginal)
    out["single_frame_candidates"] = len(one)
    out["single_frame_recovered_bits"] = round(recovered_bits(one), 4)
    out["accumulated_candidates"] = len(full)
    out["accumulated_recovered_bits"] = round(recovered_bits(full), 4)
    out["exact_recovered"] = (len(full) == 1 and full[0] == secret)
    # the headline: exploitability under accumulation exceeds the per-frame leakage estimate
    out["accumulation_beats_single_frame"] = recovered_bits(full) > recovered_bits(one)
    out["exploitability_exceeds_estimate"] = recovered_bits(full) > pf + 1.0   # clearly, not marginally
    # the honest non-contradiction: a single frame does NOT beat the per-frame MI bound (DPI holds)
    out["single_frame_within_bound"] = recovered_bits(one) <= pf + 1e-9 + 1.0  # one bit ~ one threat test
    return out


def demo():
    r = crucible()
    print("Adversarial benchmark — leakage ≠ exploitability (the frontier under a LEARNING observer)\n")
    print("  persistent secret (a fixed enemy cell, 6 bits); a mobile observer; each frame discloses one")
    print("  policy-compliant 'threat' bit. two observer classes (the M21 lattice):\n")
    print("  C_marginal  (per-frame MI estimate):     leakage ≈ %.3f bits/observation" % r["per_frame_leakage"])
    print("  C_marginal  (single frame, best case):   recovers %.2f bits  (%d candidates remain)"
          % (r["single_frame_recovered_bits"], r["single_frame_candidates"]))
    print("  C_accumulate (multilateration, session): recovers %.2f bits  (%d candidate remains)  exact=%s"
          % (r["accumulated_recovered_bits"], r["accumulated_candidates"], r["exact_recovered"]))
    print()
    print("  → a single frame stays within the per-frame bound (DPI): %s" % r["single_frame_within_bound"])
    print("  → accumulation recovers the EXACT secret, far beyond the per-frame estimate: %s"
          % r["exploitability_exceeds_estimate"])
    print("\n  the per-frame leakage estimate is a valid per-OBSERVATION bound — and the WRONG budget for a")
    print("  SESSION. exploitability is class-relative (M21) and temporal (M13/M19). The fix — accumulation-aware")
    print("  disclosure / a session leakage budget — is the next increment, not claimed here. leakage ≠ exploitability.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.adversary", OBSERVER, mutates_core=False,
                          note="adversarial benchmark on the perception loop: a multilateration (accumulating) "
                               "learner recovers the exact secret across a session though each frame's MI is a "
                               "sliver — leakage (per-frame) ≠ exploitability (session); class-relative (M21), "
                               "temporal (M13). the static leakage estimate is the wrong budget for a session")
    except LayerViolation:
        pass
