# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/accumulation.py — Accumulation Safety (M13): the query is allowed, the SEQUENCE is not.

After M12, the anti-cheat problem stops looking like "detect cheating" and becomes information economics under
adversarial constraints. The subtlest attacker is **maliciously honest**: every request it makes is legal —
"can I prepare this? cache this? request this representation?" — and the attack is in the AGGREGATION. A
single frame's shadow/sound/particle is harmless; 500 frames of them is a tracker (compression over history).

Four accumulation-safety mechanisms:

  1. TEMPORAL RECONSTRUCTION DEBT — Reconstruction Debt (M12) gains MEMORY: bits accumulate over a window
     (with decay), so history-compression is caught even when each frame is below threshold.
        ReconstructionDebt ≈ accumulated_bits(window) × inference_power
  2. REPRESENTATION PRIVACY BUDGET — per observer×object: a hidden enemy has budget 0, a visible door
     unlimited, a destructible wall limited. Every representation decision SPENDS; when the *combination*
     exceeds the budget the representation must change — not because a piece is bad, but because the sum is.
  3. CAUSAL QUERY RATE LIMITING — each query is allowed; a suspicious accumulation of legitimate queries about
     the same subject is throttled. "Allowed query, disallowed sequence."
  4. importance ≠ exposure — the allocator may internally know "this matters" without changing externally
     observable behavior, so the renderer's own spend cannot fingerprint hidden importance.

CLASSIFICATION: OBSERVER (mutates_core=False). It accounts for and caps information accumulation; it commits
no state and asserts no truth. integrity ≠ truth; authorized ≠ harmless; allowed-query ≠ allowed-sequence.

HONEST BOUND: declared bit/budget/rate proxies, not measured covert-channel capacity; the result is the
*shape* of each defense (accumulation is the threat; cap the sequence, not the query).
"""
from __future__ import annotations


def _temporal_relevance(dt, coherence):
    if dt < 0:
        dt = 0
    return max(0, 100 * coherence // (coherence + dt))


# --- 1. temporal reconstruction debt (memory over a window) -----------------------------------------

class TemporalReconstructionTracker:
    """Accumulates per-observation information bits over time with decay. A cheat reconstructs from HISTORY,
    not one frame; this catches the compression-over-history that a single-frame firewall (M12) misses."""

    def __init__(self, window=64, coherence=64):
        self.window = window
        self.coherence = coherence
        self.history = []          # list of (tick, bits)

    def observe(self, tick, bits):
        self.history.append((tick, max(0, int(bits))))
        self.history = [(t, b) for (t, b) in self.history if t > tick - self.window]

    def accumulated(self, now):
        """Decayed sum of observed bits within the window — recent observations count more."""
        return sum(b * _temporal_relevance(now - t, self.coherence) // 100 for (t, b) in self.history)

    def debt(self, now, fact_bits, inference_power=1, threshold=0.5):
        """Reconstruction fraction from accumulated history × inference_power, beyond the safe threshold."""
        frac = min(1.0, self.accumulated(now) * inference_power / max(1, fact_bits))
        return max(0.0, frac - threshold)


# --- 2. representation privacy budget (per observer × object) ---------------------------------------

class PrivacyBudget:
    """Per observer×object privacy budget. hidden enemy → 0; visible door → unlimited; destructible wall →
    limited. Every representation decision spends; the COMBINATION, not the piece, is what trips it."""

    def __init__(self):
        self._budget = {}    # (observer, obj) -> allowed (None = unlimited)
        self._spent = {}     # (observer, obj) -> spent

    def set_budget(self, observer, obj, allowed):
        self._budget[(observer, obj)] = allowed     # None = unlimited; 0 = forbidden

    def spend(self, observer, obj, amount):
        """Try to spend `amount` of privacy budget. Returns True if permitted; False means the representation
        must change (downgrade / suppress) because the accumulated exposure would exceed the budget."""
        key = (observer, obj)
        allowed = self._budget.get(key, None)       # default unlimited unless declared sensitive
        if allowed is None:
            return True
        spent = self._spent.get(key, 0)
        if spent + amount > allowed:
            return False
        self._spent[key] = spent + amount
        return True

    def remaining(self, observer, obj):
        allowed = self._budget.get((observer, obj), None)
        return None if allowed is None else allowed - self._spent.get((observer, obj), 0)


# --- 3. causal query rate limiting (allowed query, disallowed sequence) -----------------------------

class CausalQueryRateLimiter:
    """Each query about a subject is legal; an accumulation of them beyond `max_per_window` is throttled.
    Catches the maliciously-honest client whose every individual request is valid."""

    def __init__(self, window=100, max_per_window=50):
        self.window = window
        self.max_per_window = max_per_window
        self._log = {}      # (observer, subject) -> list of ticks

    def allow(self, observer, subject, now):
        key = (observer, subject)
        log = [t for t in self._log.get(key, []) if t > now - self.window]
        log.append(now)
        self._log[key] = log
        return len(log) <= self.max_per_window     # the SEQUENCE, not the query, is what fails


# --- 4. importance ≠ exposure (defeat the allocator-as-fingerprint side channel) --------------------

def exposed_level(internal_importance, public_levels=1):
    """Map internal importance to a coarse PUBLIC exposure level. With public_levels=1 the external behavior
    is constant regardless of internal importance — so an observer cannot read 'this matters' from the
    renderer's spend. importance ≠ exposure."""
    if public_levels <= 1:
        return 0
    bucket = 100 // public_levels
    return min(public_levels - 1, max(0, int(internal_importance)) // max(1, bucket))


def importance_is_hidden(importances, public_levels=1):
    """True iff differing internal importances collapse to the SAME external exposure (no fingerprint leak)."""
    return len({exposed_level(i, public_levels) for i in importances}) == 1


# --- the maliciously-honest accumulation crucible ---------------------------------------------------

def crucible():
    out = {}
    # 1. history compression: 5 harmless bits/frame for 200 frames reconstructs over the window
    trk = TemporalReconstructionTracker(window=64, coherence=64)
    per_frame = 5
    for t in range(200):
        trk.observe(t, per_frame)
    out["per_frame_harmless"] = per_frame < 0.5 * 64
    out["accumulated_debt"] = trk.debt(now=199, fact_bits=64, inference_power=1, threshold=0.5)
    # 2. privacy budget: hidden enemy = 0 → any spend blocked; visible door = unlimited
    pb = PrivacyBudget(); pb.set_budget("A", "enemy_hidden", 0); pb.set_budget("A", "door", None)
    out["hidden_spend_blocked"] = not pb.spend("A", "enemy_hidden", 0.1)
    out["visible_spend_ok"] = pb.spend("A", "door", 5.0)
    # 3. rate limiting: a maliciously-honest client makes 1 legal query/frame
    rl = CausalQueryRateLimiter(window=100, max_per_window=50)
    allows = [rl.allow("A", "enemy_hidden", t) for t in range(120)]
    out["early_queries_allowed"] = all(allows[:50])
    out["accumulation_throttled"] = (False in allows)
    # 4. importance != exposure
    out["importance_hidden"] = importance_is_hidden([10, 90], public_levels=1)
    return out


def demo():
    r = crucible()
    print("Accumulation Safety — the query is allowed, the SEQUENCE is not\n")
    print("  1. history compression: 5 bits/frame harmless per-frame=%s; accumulated reconstruction debt=%.2f"
          % (r["per_frame_harmless"], r["accumulated_debt"]))
    print("  2. privacy budget: hidden-object spend blocked=%s; visible-object spend ok=%s"
          % (r["hidden_spend_blocked"], r["visible_spend_ok"]))
    print("  3. rate limit: first 50 legal queries allowed=%s; accumulation later throttled=%s"
          % (r["early_queries_allowed"], r["accumulation_throttled"]))
    print("  4. importance ≠ exposure: internal {10,90} collapse to one external level=%s" % r["importance_hidden"])
    print("\n  a maliciously-honest client makes only legal requests; the attack is the AGGREGATION.")
    print("  allowed-query ≠ allowed-sequence; authorized ≠ harmless. integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("accumulation", OBSERVER, mutates_core=False,
                          note="Accumulation Safety — temporal reconstruction debt + privacy budgets + causal "
                               "query rate limiting + importance≠exposure; allowed-query ≠ allowed-sequence")
    except LayerViolation:
        pass
