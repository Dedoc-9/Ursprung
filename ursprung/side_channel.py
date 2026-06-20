# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/side_channel.py — defenses for the hard cases where the renderer ITSELF becomes a sensor.

Even with the access-control firewall (M11) and the composition firewall (M12), three subtler leaks remain —
the renderer's own behavior becomes a side channel:

  1. TIMING — frame time that varies with hidden expense leaks ("8→12→15→8ms" = something appeared behind the
     wall). Defense (cryptographic side-channel style): normalize/quantize timing so resource-dependent
     variance is hidden.
  2. PREDICTION INVERSION — the renderer prepares for a future; an attacker reverses the prep to infer the
     cause ("debris prepared ⇒ grenade thrown"). Defense: **prepare(possibility) ≠ announce(probability)** —
     prepare BREADTH so the prep set does not reveal which future is likely.
  3. COLLUDING CLIENTS — M10 consensus by witness COUNT fails when 8 of 10 are compromised. Defense:
     **weighted trust** = evidence × authority × reliability × validity, not headcount.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures and caps information leakage from the renderer's
own behavior; it commits no state and asserts no truth. integrity ≠ truth; consensus ≠ truth.

HONEST BOUND: declared leak proxies (timing range, branch count, trust factors), not measured covert-channel
capacity; the result is the *shape* of each defense, not the constants.
"""
from __future__ import annotations


# --- 1. timing normalization ------------------------------------------------------------------------

def timing_leak(frame_times):
    """How much the frame-time stream leaks: the spread (max − min) that correlates with hidden expense."""
    return (max(frame_times) - min(frame_times)) if frame_times else 0


def normalize_timing(frame_times, quantum):
    """Quantize each frame to the next multiple of `quantum` (a constant presentation budget), hiding
    resource-dependent variance. A frame that 'costs more' is padded to the same slot — no timing tell."""
    return [((t + quantum - 1) // quantum) * quantum for t in frame_times]


# --- 2. prediction-inversion guard ------------------------------------------------------------------

def inversion_leak(prepared_branches):
    """How much the prep set reveals the likely future (0..100). One prepared branch ⇒ the trigger is obvious
    (100). Preparing BREADTH dilutes it: leak ≈ 100 / breadth. prepare(possibility) ≠ announce(probability)."""
    n = max(1, len(set(prepared_branches)))
    return 100 // n


def breadth_preserves_secrecy(prepared_branches, min_breadth=3):
    """The guard: prepare enough plausible branches that the prep cannot be inverted to the cause."""
    return len(set(prepared_branches)) >= min_breadth


# --- 3. weighted-trust consensus (defeats colluding clients) ----------------------------------------

def claim_trust(claim):
    """Trust = evidence × authority × reliability × validity (each 0..100), scaled to 0..100. NOT a witness
    count — a colluding client has low authority/reliability no matter how many copies it sends."""
    e = max(0, min(100, int(claim.get("evidence", 0))))
    a = max(0, min(100, int(claim.get("authority", 0))))      # closeness to authoritative source (server high)
    r = max(0, min(100, int(claim.get("reliability", 0))))    # historical reliability
    v = max(0, min(100, int(claim.get("validity", 0))))       # temporal validity (fresh)
    return e * a // 100 * r // 100 * v // 100


def weighted_consensus(claims, trust_threshold=50):
    """Admit the hash with the most TRUST WEIGHT (not the most witnesses), iff it clears a threshold and out-
    weighs the rest. claims: [{hash, ...trust factors}]. Defeats a low-trust colluding majority. Returns
    {admitted, winning_hash, winning_trust, other_trust, by_count_would_pick}."""
    by_hash_trust, by_hash_count = {}, {}
    for c in claims:
        h = c["hash"]
        by_hash_trust[h] = by_hash_trust.get(h, 0) + claim_trust(c)
        by_hash_count[h] = by_hash_count.get(h, 0) + 1
    if not by_hash_trust:
        return {"admitted": False, "winning_hash": None, "winning_trust": 0, "other_trust": 0, "by_count_would_pick": None}
    winning = max(sorted(by_hash_trust), key=lambda h: by_hash_trust[h])
    win_trust = by_hash_trust[winning]
    other = sum(v for h, v in by_hash_trust.items() if h != winning)
    by_count = max(sorted(by_hash_count), key=lambda h: by_hash_count[h])
    return {"admitted": win_trust >= trust_threshold and win_trust > other, "winning_hash": winning,
            "winning_trust": win_trust, "other_trust": other, "by_count_would_pick": by_count}


def demo():
    print("Side-channel defenses — when the renderer's own behavior becomes a sensor\n")
    # 1. timing
    ft = [8, 12, 15, 8]
    print("  1. timing: raw leak (spread) = %d ms; normalized (quantum=16) leak = %d ms"
          % (timing_leak(ft), timing_leak(normalize_timing(ft, 16))))
    # 2. prediction inversion
    print("  2. inversion leak: 1 branch prepared = %d; 4 branches prepared = %d (prepare breadth ≠ announce prob)"
          % (inversion_leak(["debris"]), inversion_leak(["intact", "damaged", "destroyed", "scorched"])))
    # 3. colluding clients
    cheat = [{"hash": "CHEAT", "evidence": 30, "authority": 10, "reliability": 10, "validity": 80} for _ in range(8)]
    honest = [{"hash": "TRUE", "evidence": 90, "authority": 95, "reliability": 90, "validity": 90},   # server
              {"hash": "TRUE", "evidence": 80, "authority": 60, "reliability": 80, "validity": 90},
              {"hash": "TRUE", "evidence": 80, "authority": 60, "reliability": 80, "validity": 90}]
    v = weighted_consensus(cheat + honest)
    print("  3. colluding clients (8 cheat vs 3 honest+server):")
    print("     by COUNT would pick: %s  | by WEIGHTED TRUST admits: %s (trust %d vs %d)"
          % (v["by_count_would_pick"], v["winning_hash"], v["winning_trust"], v["other_trust"]))
    print("\n  consensus ≠ truth: weight by authority/reliability, not headcount. integrity ≠ truth.")
    return v


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("side_channel", OBSERVER, mutates_core=False,
                          note="side-channel defenses — timing normalization, prediction-inversion breadth "
                               "guard, weighted-trust consensus (defeats colluding clients); consensus ≠ truth")
    except LayerViolation:
        pass
