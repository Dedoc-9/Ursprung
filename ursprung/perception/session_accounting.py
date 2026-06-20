# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/session_accounting.py — Session Leakage Accounting (the fix the adversary demanded).

`adversary.py` falsified the loop's per-frame leakage number: a sequence of policy-compliant, individually-tiny
disclosures triangulated the exact secret across a session. The lesson — *leakage per observation ≠ leakage per
session* — is not a game problem; it is the general one every accumulating observer (LLM agent, robot, analyst,
dashboard) creates. This module is the honest response, and it is the **first general result** in the stack:
**purpose-preserving disclosure under an accumulating observer.**

The mechanism: account for leakage over the SESSION, not the frame. A `SessionLeakageBudget` caps total bits an
observer may accumulate about the secret; the `AccumulationAwareCompiler` selects which disclosure channels to
expose by their committed (worst-case) *session* leakage — keeping task-useful, low-session-leakage channels
and dropping the ones that triangulate, even when each of their individual frames looks harmless.

The key empirical claim, then re-tested against the EXACT `adversary.py` learner: when the task-relevant feature
(a coarse "close / far" band, stable across the session) is **separable** from the triangulating channel (the
per-frame threat bit that varies with the observer's vantage), accumulation-aware disclosure can keep utility
at 1.0 while the accumulating learner's recovery **collapses** from the full secret (6 bits) to the band
(~1 bit) — never the exact cell.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: this holds (a) against the *modeled* accumulating
observer class — a richer class may still accumulate through an unmodeled channel (`secure-against-class ≠
secure`), and (b) only because the task channel is *separable* from the leak channel; a task that genuinely
needs the high-resolution signal faces a real utility/leakage tradeoff, not a free lunch. Constructed world.
leakage(session) ≠ leakage(frame); leakage ≠ exploitability; simulation ≠ physics.
"""
from __future__ import annotations

from .adversary import observe_threat, vantage_path, recovered_bits, H_SECRET, _cells, _manhattan

HOME = (0, 0)
CLOSE = 7                       # the task only needs a coarse "close / far" band, stable across the session
SESSION_BUDGET = 2.0            # bits of the secret an observer may accumulate over the whole session


# --- the task (needs only the coarse band) ----------------------------------------------------------

def band(s):
    """A 2-value, session-stable task feature: is the persistent enemy close or far from HOME?"""
    return 0 if _manhattan(s, HOME) <= CLOSE else 1


def optimal_action(s):
    return "cover" if band(s) == 0 else "hold"


def agent_action(disclosed_band):
    if disclosed_band is None:
        return "hold"           # blind guess (the most-common action)
    return "cover" if disclosed_band == 0 else "hold"


# --- channels + their committed (worst-case) SESSION leakage ----------------------------------------

CHANNELS = {
    "band": {"task_useful": True},            # stable across frames → does not triangulate
    "moving_threat": {"task_useful": False},  # varies with vantage → triangulates to the exact cell
}


def channel_session_leakage(name):
    """The bits an observer accumulates from a channel over a whole session — committed worst-case, secret-
    independent (so the policy can be fixed before the secret is known)."""
    if name == "band":
        return max(recovered_bits([c for c in _cells() if band(c) == b]) for b in (0, 1))
    if name == "moving_threat":
        return H_SECRET          # multilateration over the session recovers the exact cell (6 bits)
    raise ValueError(name)


def accumulation_aware_select(budget=SESSION_BUDGET):
    """The AccumulationAwareCompiler's choice: greedily include task-useful, low-session-leakage channels while
    the cumulative *session* leakage stays under budget. Drops the triangulating channel."""
    chosen, total = [], 0.0
    for name in sorted(CHANNELS, key=lambda n: (not CHANNELS[n]["task_useful"], channel_session_leakage(n))):
        if total + channel_session_leakage(name) <= budget:
            chosen.append(name)
            total += channel_session_leakage(name)
    return chosen


SESSION_POLICIES = {
    "naive": ["band", "moving_threat"],          # the policy adversary.py broke (per-frame compliant, leaks a session)
    "accumulation_aware": accumulation_aware_select(),
    "blind": [],
}


# --- re-run the EXACT accumulating adversary against each session policy -----------------------------

def exploit(secret, channels):
    """The session exploitability: run the accumulating learner using whatever channels the policy disclosed."""
    cset = _cells()
    if "band" in channels:
        b = band(secret)
        cset = [c for c in cset if band(c) == b]
    if "moving_threat" in channels:
        obs = [(v, observe_threat(secret, v)) for v in vantage_path()]
        cset = [c for c in cset if all(observe_threat(c, v) == t for v, t in obs)]
    return cset


def utility(channels):
    """Task success: the agent needs the coarse band to act optimally; without it, it guesses."""
    return 1.0 if "band" in channels else 0.5


class SessionResult:
    __slots__ = ("policy", "channels", "utility", "exploitability", "candidates",
                 "within_budget", "sufficient", "exact_recovered", "passes", "coverage_boundary")

    def __init__(self, policy, secret, budget=SESSION_BUDGET, utility_floor=0.9):
        ch = SESSION_POLICIES[policy]
        cset = exploit(secret, ch)
        self.policy = policy
        self.channels = list(ch)
        self.utility = utility(ch)
        self.exploitability = round(recovered_bits(cset), 4)
        self.candidates = len(cset)
        self.within_budget = self.exploitability <= budget
        self.sufficient = self.utility >= utility_floor
        self.exact_recovered = (len(cset) == 1 and cset[0] == secret)
        self.passes = self.within_budget and self.sufficient
        self.coverage_boundary = ("session exploitability under the MODELED accumulating observer class and a "
                                  "SEPARABLE task channel; a richer class or a non-separable task can still "
                                  "accumulate — secure-against-class ≠ secure")

    def __repr__(self):
        return "<SessionResult %s U=%.2f exploit=%.2f cand=%d within=%s exact=%s PASSES=%s>" % (
            self.policy, self.utility, self.exploitability, self.candidates,
            self.within_budget, self.exact_recovered, self.passes)


def evaluate(policy, secret=(5, 2)):
    return SessionResult(policy, secret)


# --- the crucible: re-run the adversary; show the collapse ------------------------------------------

def crucible(secret=(5, 2)):
    res = {name: evaluate(name, secret) for name in SESSION_POLICIES}
    out = {"aware_channels": SESSION_POLICIES["accumulation_aware"],
           "session_budget": SESSION_BUDGET,
           "frontier": {n: (r.utility, r.exploitability) for n, r in res.items()}}
    out["naive_exact_recovered"] = res["naive"].exact_recovered
    out["naive_fails_budget"] = not res["naive"].within_budget
    out["aware_drops_triangulating_channel"] = "moving_threat" not in SESSION_POLICIES["accumulation_aware"]
    out["aware_keeps_task_channel"] = "band" in SESSION_POLICIES["accumulation_aware"]
    out["aware_preserves_utility"] = res["accumulation_aware"].sufficient
    out["aware_within_budget"] = res["accumulation_aware"].within_budget
    out["aware_collapses_exploitability"] = res["accumulation_aware"].exploitability < res["naive"].exploitability
    out["aware_does_not_recover_exact"] = not res["accumulation_aware"].exact_recovered
    out["blind_under_serves"] = res["blind"].within_budget and not res["blind"].sufficient
    out["only_aware_passes"] = (res["accumulation_aware"].passes and not res["naive"].passes
                                and not res["blind"].passes)
    # the general result: utility preserved AND session exploitability collapsed under an accumulating observer
    out["purpose_preserving_under_accumulation"] = (res["accumulation_aware"].sufficient
                                                    and res["accumulation_aware"].within_budget
                                                    and not res["accumulation_aware"].exact_recovered
                                                    and res["naive"].exact_recovered)
    # robustness: aware stays within budget and never recovers the exact cell, for every secret
    out["aware_holds_for_all_secrets"] = all(
        (lambda r: r.within_budget and not r.exact_recovered)(SessionResult("accumulation_aware", s))
        for s in _cells())
    return out


def demo():
    r = crucible()
    print("Session Leakage Accounting — purpose-preserving disclosure under an ACCUMULATING observer\n")
    print("  the same adversary as adversary.py, re-run against three SESSION policies")
    print("  (session budget = %.1f bits of the secret; H(secret) = 6 bits)\n" % SESSION_BUDGET)
    print("  %-20s %-26s %-8s %-12s %s" % ("policy", "channels", "utility", "exploit(bits)", "verdict"))
    for name in ("naive", "accumulation_aware", "blind"):
        res = evaluate(name)
        verdict = ("PASSES" if res.passes else ("over-accumulates" if res.sufficient else "under-serves"))
        print("  %-20s %-26s %-8.2f %-12.2f %s"
              % (name, ",".join(res.channels) or "(none)", res.utility, res.exploitability, verdict))
    print("\n  accumulation-aware drops the triangulating channel, keeps the stable task band:")
    print("  utility stays 1.0 while the accumulating learner collapses from the EXACT cell (6 bits) to the")
    print("  band (~1 bit) — exact never recovered. The first purpose-preserving result under accumulation.")
    print("  HONEST: holds against the modeled observer class + a separable task channel. leakage(session) ≠ leakage(frame).")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.session_accounting", OBSERVER, mutates_core=False,
                          note="Session Leakage Accounting: account leakage over the SESSION not the frame; the "
                               "AccumulationAwareCompiler drops triangulating channels under a session budget. "
                               "Re-running adversary.py: utility 1.0 preserved while exploitability collapses "
                               "6→~1 bit (exact never recovered) — purpose-preserving disclosure under accumulation")
    except LayerViolation:
        pass
