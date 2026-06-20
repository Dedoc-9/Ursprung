# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/channel_discovery.py — Channel Discovery (a harness feature, not a law): what channels EXIST?

M21 reduced the whole anti-cheat arc to one question — *can hidden state influence an observable?* — and gave
the only class-independent guarantee: if the secret is transmitted through no observable channel, no observer
can extract it. But that guarantee is only as good as the list of channels you thought to check. M20's bit-7
slip was a bug in the model of the OBSERVER; the dual bug is in the model of the WORLD — the channel you never
enumerated. Real systems always have more state than the model: packet timing, cache residency, branch
behaviour, animation scheduling, audio mixing, GPU/CPU contention, memory pressure, server-tick alignment.

So before touching real sockets, the harness needs to stop asking "does channel X leak?" and start asking
"what channels exist, and which of them carry information about the secret?" This module is that inversion:

    observable trace → { latency, frame_time, packet_timing, correction, resource, audio, animation, … }
                     → mutual information I(channel ; secret) per channel
                     → rank, flag the leakers, and SURFACE the ones no one audited.

The produced lesson (and the reason this is worth building): a channel that *no prior milestone enumerated*
(here, `animation_events`) is discovered to leak — an audit of only the modeled set would have passed while
the system bled through the unlisted channel. The hardest unknown was never the secret; it is the observer's
representation of the world.

This ties straight back to M21's split:
  * I(channel ; secret) == 0  ⇒  the secret is SEVERED from that channel — the class-independent ABSOLUTE
    guarantee (no observer, of any capacity, learns the secret through it).
  * I(channel ; secret) >  0  ⇒  the secret leaks; the channel is then handed to the adversary class
    (`adversary_capacity`) — whether it is *exploitable* is class-relative, but the leak is real.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures information flow in a trace; it commits nothing,
asserts no truth. It is a discovery instrument, not a defense. measurement ≠ truth; integrity ≠ truth.

HONEST BOUND: discrete mutual information over a constructed, deterministic trace — not a learned statistic
over real telemetry, and not an exhaustive channel set (by definition, discovery cannot enumerate a channel
the *trace* omits). On real silicon the channels are continuous and coupled (DVFS, cache lines, bus
contention), MI must be estimated with error, and new channels appear that no trace captured. This finds the
SHAPE of channel discovery — that the unlisted channel is the dangerous one — not a complete audit.
simulation ≠ physics; absence of evidence here ≠ evidence of absence on real hardware.
"""
from __future__ import annotations

from collections import Counter
from math import log2


# --- the observable trace (a deterministic stand-in for real telemetry) -----------------------------

# the channels prior milestones explicitly reasoned about. NOTE: `animation_events` is deliberately NOT here —
# it is observed in the trace but absent from the audit, to show discovery catches what enumeration misses.
MODELED_AUDIT = ("latency", "packet_timing", "audio_events", "frame_time", "correction_events", "resource_events")


def _secret(t):
    """The hidden state over time (here: an event is 'present' on part of each period)."""
    return 1 if (t % 8) < 3 else 0


def channels(t):
    """Every observable the trace exposes at tick t. Clean channels are functions of the period BLOCK (t//8),
    which is independent of the secret (t%8) over a whole number of periods → exactly zero information.
    Leaking channels are functions of the secret. `animation_events` is the UNMODELED leaker."""
    block = t // 8
    s = _secret(t)
    return {
        # clean: depend only on the block, never on the secret  →  I(·;secret) == 0  (severed)
        "latency":          block % 4,
        "packet_timing":    (block >> 1) % 3,
        "audio_events":     block % 2,
        # leaking: depend on the secret  →  I(·;secret) > 0
        "frame_time":       s * 3 + (block % 2),          # a hitch when the event is present
        "correction_events": s,                            # a rollback exactly when present (fully reveals)
        "resource_events":  s * 2 + (block % 2),           # an asset load when present
        # the UNMODELED channel: leaks PARTIALLY, and is NOT in MODELED_AUDIT.
        # NOTE: `s | (block&1)`, not `s ^ (block&1)` — XOR with a ~uniform independent bit is a one-time pad
        # (I=0, perfectly severed); OR keeps a real but noisy correlation (I≈0.27 < H(secret)≈0.95).
        "animation_events": s | (block & 1),
    }


def trace(n=256):
    return [(_secret(t), channels(t)) for t in range(n)]


# --- mutual information (the discovery instrument) --------------------------------------------------

def mutual_information(pairs):
    """Discrete I(X;Y) in bits over observed (x, y) samples. 0 ⇒ independent (severed)."""
    n = len(pairs)
    if n == 0:
        return 0.0
    px = Counter(x for x, _ in pairs)
    py = Counter(y for _, y in pairs)
    pxy = Counter(pairs)
    mi = 0.0
    for (x, y), c in pxy.items():
        joint = c / n
        mi += joint * log2(joint / ((px[x] / n) * (py[y] / n)))
    return max(0.0, mi)          # clamp tiny negative float error


def channel_information(tr=None):
    """I(channel ; secret) for every channel observed in the trace."""
    tr = tr or trace()
    names = sorted(tr[0][1].keys())
    return {name: round(mutual_information([(s, obs[name]) for s, obs in tr]), 4) for name in names}


# --- discovery: rank, flag leakers, surface the unmodeled ones --------------------------------------

def discover(tr=None, threshold=0.02):
    """Invert the question: scan ALL observed channels, rank by information about the secret, and flag the
    leakers — including channels outside the modeled audit set."""
    info = channel_information(tr)
    ranked = sorted(info.items(), key=lambda kv: kv[1], reverse=True)
    leaking = [name for name, mi in ranked if mi > threshold]
    severed = [name for name, mi in ranked if mi <= threshold]
    unmodeled_leaks = [name for name in leaking if name not in MODELED_AUDIT]
    audit_only_leaks = [name for name in leaking if name in MODELED_AUDIT]
    return {
        "info": info, "ranked": ranked,
        "leaking": leaking, "severed": severed,
        "unmodeled_leaks": unmodeled_leaks,         # the channels an audit of the modeled set would MISS
        "audit_only_leaks": audit_only_leaks,
    }


def secret_severed_in(channel, tr=None, threshold=0.02):
    """True iff the secret is severed from this channel (I == 0) — the M21 class-independent absolute guarantee."""
    return channel_information(tr).get(channel, 0.0) <= threshold


# --- the discovery crucible -------------------------------------------------------------------------

def crucible():
    d = discover()
    out = {"info": d["info"], "ranked": d["ranked"]}
    # 1. the leakers are found, the clean channels read as severed
    out["leaking"] = d["leaking"]
    out["severed"] = d["severed"]
    out["correction_fully_reveals"] = d["info"]["correction_events"] > 0.9          # I ≈ H(secret)
    out["clean_channels_severed"] = all(d["info"][c] == 0.0
                                        for c in ("latency", "packet_timing", "audio_events"))
    # 2. THE HEADLINE: an unmodeled channel leaks and an audit of the modeled set would have missed it
    out["unmodeled_leak_found"] = "animation_events" in d["unmodeled_leaks"]
    out["animation_not_in_audit"] = "animation_events" not in MODELED_AUDIT
    out["audit_alone_would_pass"] = ("animation_events" not in d["audit_only_leaks"]) and out["unmodeled_leak_found"]
    # 3. tie to M21: severed ⇒ absolute (class-independent); leaking ⇒ hand to the adversary class
    out["severed_is_absolute"] = secret_severed_in("audio_events")
    out["leak_is_real"] = not secret_severed_in("animation_events")
    # 4. discovery inverts the question: it ranks ALL channels, not just the audited ones
    out["discovers_more_than_audit"] = len(d["info"]) > len(MODELED_AUDIT)
    return out


def demo():
    r = crucible()
    print("Channel Discovery — what channels EXIST? (invert 'does channel X leak?')\n")
    print("  I(channel ; secret) in bits — ranked:")
    for name, mi in r["ranked"]:
        tag = ""
        if mi <= 0.02:
            tag = "  (severed — absolute, M21)"
        elif name not in MODELED_AUDIT:
            tag = "  ← UNMODELED leaker (an audit would have missed this)"
        print("     %-18s %.4f%s" % (name, mi, tag))
    print()
    print("  · clean channels read as severed (I=0): %s" % r["clean_channels_severed"])
    print("  · correction_events fully reveals the secret (I≈H): %s" % r["correction_fully_reveals"])
    print("  · an UNMODELED channel (animation_events) was discovered to leak: %s" % r["unmodeled_leak_found"])
    print("  · auditing only the enumerated set would have PASSED while the system bled: %s"
          % r["audit_alone_would_pass"])
    print("\n  the hardest unknown was never the secret — it is the observer's representation of the world.")
    print("  I=0 ⇒ severed ⇒ absolute (any observer); I>0 ⇒ leak is real, exploitability is class-relative.")
    print("  measurement ≠ truth; absence of evidence here ≠ evidence of absence on real hardware.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("channel_discovery", OBSERVER, mutates_core=False,
                          note="Channel Discovery (harness feature) — invert 'does channel X leak?' into 'what "
                               "channels exist?'; mutual information per channel; surfaces UNMODELED leakers an "
                               "audit would miss; I=0 ⇒ severed/absolute (M21), I>0 ⇒ feed the adversary class")
    except LayerViolation:
        pass
