# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/observer_capacity.py — Leakage(C): leakage as a function of observer CAPACITY.

The repo has repeatedly shown that exploitability is *class-relative* (M21) — but as a set of discrete cases.
This module makes the dependence a **curve**. Against a single FIXED representation, it sweeps a ladder of
observer capacities and measures how much of the secret each recovers, exhibiting the claim the VC-dimension
bridge predicts: a more capable observer extracts more from the *same* disclosure, so the honest quantity is
`Leakage(C)`, never a scalar `Leakage`. "Low leakage" is meaningless until the observer class is named.

The scenario is the adversary's: a persistent secret (a fixed cell, 6 bits) and a mobile observer that sees one
policy-compliant `threat` bit per frame. Here **capacity is the observer's memory horizon `W`** — how many of
the session's observations it can integrate. A memoryless observer (`W=1`) recovers almost nothing; an observer
that can accumulate the whole session recovers the exact cell. The curve rises monotonically in between:

    capacity W      recovered bits
        1               0.39      (memoryless — near-blind)
        2               0.54
        4               0.91
        8               1.42
       16+              6.00      (full secret — the multilateration learner of adversary.py)

HONEST BOUND: memory horizon is a *proxy* for capacity, and this is an 8×8 toy. The genuine frontier — and a
different *kind* of build — is a **scaling-model observer on a non-toy world**, where `C` is real model
capacity, not a window length. This module does not attempt that; it **defines the axis that frontier scales.**
The orthogonal capacity axis (hypothesis-class richness) is `adversary_capacity.py`'s lattice. `Leakage(C)`;
secure-against-class ≠ secure; simulation ≠ physics.
"""
from __future__ import annotations

from .adversary import observe_threat, vantage_path, consistent_cells, recovered_bits


CAPACITY_LADDER = (1, 2, 4, 8, 16, 32, 64)     # observer memory horizons (a capacity proxy)


def recovery_at_capacity(secret, horizon):
    """How many bits of the secret an observer with memory `horizon` recovers from the fixed representation."""
    obs = [(v, observe_threat(secret, v)) for v in vantage_path()[:horizon]]
    return recovered_bits(consistent_cells(obs))


def capacity_curve(secret=(5, 2)):
    """`Leakage(C)` as a curve: (capacity, recovered_bits) over the ladder, against ONE fixed representation."""
    return [(w, round(recovery_at_capacity(secret, w), 3)) for w in CAPACITY_LADDER]


def crucible(secret=(5, 2)):
    curve = capacity_curve(secret)
    bits = [b for _, b in curve]
    out = {"curve": curve}
    out["monotone_in_capacity"] = all(bits[i + 1] >= bits[i] for i in range(len(bits) - 1))
    out["rises_overall"] = bits[-1] > bits[0]
    out["memoryless_recovers_little"] = bits[0] < 2.0           # W=1 ≈ near-blind
    out["full_capacity_recovers_secret"] = bits[-1] == 6.0      # the accumulating learner
    # the same fixed representation leaks differently to different observers → leakage is a function of C
    out["same_representation_capacity_dependent_leakage"] = bits[0] != bits[-1]
    out["leakage_undefined_without_observer_class"] = out["same_representation_capacity_dependent_leakage"]
    return out


def demo():
    r = crucible()
    print("Leakage(C) — leakage as a function of observer CAPACITY (one fixed representation)\n")
    print("  scenario: a persistent secret + a mobile observer; capacity = memory horizon W (how many of the")
    print("  session's observations the observer can integrate).\n")
    print("  capacity W   recovered bits")
    for w, b in r["curve"]:
        print("     %-4d        %.3f" % (w, b))
    print("\n  the SAME disclosure leaks 0.39 bits to a memoryless observer and the WHOLE secret to an")
    print("  accumulating one. 'low leakage' is undefined without naming the observer class: %s"
          % r["leakage_undefined_without_observer_class"])
    print("  this DEFINES the capacity axis; the real frontier scales C to a model on a non-toy world (not done here).")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.observer_capacity", OBSERVER, mutates_core=False,
                          note="Leakage(C): recovery as a monotone curve over observer capacity (memory horizon) "
                               "against a FIXED representation — the same disclosure leaks differently to "
                               "different observers (the VC/M21 bridge as a curve). Defines the axis the real "
                               "scaling-model benchmark would extend; memory-horizon is a proxy, 8×8 is a toy")
    except LayerViolation:
        pass
