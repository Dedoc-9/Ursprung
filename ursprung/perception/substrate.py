# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/substrate.py — substrate hiddenness: the generator leaks through the physical residue.

Every prior layer treated hiddenness as *informational* — the output is encrypted, ambiguous, or
non-identifiable. This layer is *physical*: the generator is hidden because the causal mechanism is not
observable through the available channel. The model widens from `G → A → observer` to

    G + physical substrate → { intended output A, physical residue R } → observer

where `R` is everything the process emits besides its message — power draw, timing, electromagnetic emission,
thermal/mechanical footprint. So intent/identity leakage `I(G;A,O)` becomes `I(G ; A, O, R)`, and the observer
is no longer just a learner but a **sensor-fusion adversary**.

The consequences this bench exhibits:

  * **signal privacy ≠ generator privacy.** An encrypted output hides the *content* (`I(G;A) = 0`) while the
    *residue* exposes the *machine* (`I(G;power) > 0`). Hiding what it said is not hiding what it is.
  * **sensor fusion dominates.** Two weak channels combine to more than either alone — `I(G;{power,timing})`
    exceeds `max(I(G;power), I(G;timing))`. The adversary's reach is the *union* of its sensors.
  * **leakage is a physical capacity curve.** `L` is not only a function of model capacity (`observer_capacity`)
    but of *which channels the observer physically has*: `L(C_sensors, C_compute, T)`, monotone in sensor access.
  * **unobserved ≠ unknown.** With no residue channel (only the encrypted output) recovery is 0 — yet the
    generator is fully *determined*; the observer merely lacks the channel. This is distinct from the
    non-identifiable / max-entropy case (`identifiability.py`), where there is no stable generator to recover.

This is the control-theory frame: a hidden generator is an *unobservable* state. The limit is not computation
but **observability** — and so the project's oldest question returns in its sharpest form: *hidden from which
observer, through which channel, over what time horizon?*

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy channels (declared functions of `G`), not
measured power/EM traces; real residue is continuous, noisy, and device-specific, and the fusion gain depends on
the sensor suite. The point is structural: `I(G;A)=0` does not imply `I(G;A,O,R)=0`. signal privacy ≠ generator
privacy; unobserved ≠ unknown; simulation ≠ physics.
"""
from __future__ import annotations

from math import log2

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
        m = 0.0
        for (x, y), c in pxy.items():
            j = c / n
            m += j * log2(j / ((px[x] / n) * (py[y] / n)))
        return max(0.0, m)


GENERATORS = (0, 1, 2, 3)          # the hidden machine state / generator (uniform → 2 bits)
H_GEN = log2(len(GENERATORS))

# the channels the substrate emits. `content` is the intended output, here ENCRYPTED (constant — leaks nothing);
# the rest are physical residue R, each a projection of the generator.
CHANNELS = {
    "content": lambda g: 0,                 # encrypted message — content hidden, I(G;content)=0
    "power":   lambda g: 1 if g >= 2 else 0,  # power draw leaks the high bit
    "timing":  lambda g: g % 2,             # response timing leaks the low bit
    "em":      lambda g: g,                  # electromagnetic emission leaks the whole state
}


def channel_leakage(channel_names):
    """`I(G ; observed channels)` — how much of the generator a sensor suite recovers."""
    fns = [CHANNELS[n] for n in channel_names]
    return mutual_information([(g, tuple(f(g) for f in fns)) for g in GENERATORS])


def physical_capacity_curve(sensor_suites):
    """`L(C_sensors)` — leakage as a function of which channels the observer physically has."""
    return [(tuple(s), round(channel_leakage(s), 3)) for s in sensor_suites]


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    out["content_leak"] = round(channel_leakage(["content"]), 3)
    out["power_leak"] = round(channel_leakage(["power"]), 3)
    out["timing_leak"] = round(channel_leakage(["timing"]), 3)
    out["fused_leak"] = round(channel_leakage(["power", "timing"]), 3)
    # signal privacy ≠ generator privacy: content sealed, residue leaks the machine
    out["signal_hidden"] = channel_leakage(["content"]) == 0.0
    out["generator_leaks_via_residue"] = channel_leakage(["power"]) > 0
    out["signal_privacy_neq_generator_privacy"] = out["signal_hidden"] and out["generator_leaks_via_residue"]
    # sensor fusion dominates any single channel
    out["fusion_exceeds_single"] = channel_leakage(["power", "timing"]) > max(
        channel_leakage(["power"]), channel_leakage(["timing"]))
    out["fusion_recovers_full_generator"] = abs(channel_leakage(["power", "timing"]) - H_GEN) < 1e-9
    # the physical capacity curve is monotone in sensor access
    curve = physical_capacity_curve([[], ["content"], ["power"], ["power", "timing"]])
    out["capacity_curve"] = curve
    bits = [b for _, b in curve]
    out["capacity_monotone"] = all(bits[i + 1] >= bits[i] for i in range(len(bits) - 1))
    # unobserved ≠ unknown: with only the encrypted channel, recovery is 0 though the generator is DETERMINED;
    # add a residue channel and it is fully recovered — the 0 was a missing channel, not a missing generator.
    out["unobserved_recovery"] = channel_leakage(["content"])          # 0 — no channel
    out["observed_recovery"] = channel_leakage(["em"])                 # full — channel present
    out["unobserved_not_unknown"] = (out["unobserved_recovery"] == 0.0
                                     and abs(out["observed_recovery"] - H_GEN) < 1e-9)
    return out


def demo():
    r = crucible()
    print("Substrate hiddenness — the generator leaks through the physical residue (a sensor-fusion adversary)\n")
    print("  G + substrate → { intended output A, residue R = power/timing/EM/… } → observer.  I(G;A,O,R).\n")
    print("  channel        I(G ; channel) bits")
    for name in ("content", "power", "timing", "em"):
        print("    %-9s    %.3f" % (name, round(channel_leakage([name]), 3)))
    print()
    print("  · signal privacy ≠ generator privacy: the encrypted output leaks %.0f about G, the power channel leaks %.0f."
          % (r["content_leak"], r["power_leak"]))
    print("  · sensor fusion dominates: power⊕timing recovers %.0f bits — the WHOLE generator — though each leaks 1."
          % r["fused_leak"])
    print("  · leakage is a physical capacity curve L(C_sensors): %s — monotone in sensor access."
          % [(list(s), b) for s, b in r["capacity_curve"]])
    print("  · unobserved ≠ unknown: with only the encrypted channel, recovery is 0 — yet the generator is fully")
    print("    DETERMINED; add a residue channel and it is fully recovered. the 0 was a missing channel, not noise.")
    print("\n  a hidden generator is an UNOBSERVABLE state, not an absent one. the question is never 'is it hidden?'")
    print("  but 'hidden from which observer, through which channel, over what horizon?' simulation ≠ physics.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.substrate", OBSERVER, mutates_core=False,
                          note="substrate hiddenness: the generator leaks through physical residue R "
                               "(power/timing/EM) even when the output A is encrypted — I(G;A,O,R). signal "
                               "privacy ≠ generator privacy; sensor fusion dominates; L is a physical capacity "
                               "curve L(C_sensors); unobserved ≠ unknown (an unobservable state, not an absent one)")
    except LayerViolation:
        pass
