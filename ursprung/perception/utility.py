# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/utility.py — Participation Utility + the first privacy-funnel benchmark.

This closes the loop and supplies the term `docs/INFORMATION_INTENT.md` named but never measured:
**Participation Utility** — not theoretical, but *measured task success* under a compiled observation. Paired
with leakage (`I(secret ; observation)`, measured by the existing `channel_discovery` QIF estimator — an
existing module becomes the verifier), it produces the repo's first **utility/leakage frontier**.

The benchmark question: *can we preserve task success while keeping leakage under a declared budget?* The
success criterion is neither zero leakage nor maximum utility — it is the frontier point that clears BOTH the
utility floor and the leakage budget. Reported as a `MeasurementResult` that carries its coverage boundary;
never a bare "safe".
"""
from __future__ import annotations

from .toy_task import encounters, survives, secret, agent_action
from .observation_compiler import compile_observation, view_key
from .disclosure_policy import POLICIES

# the leakage verifier is the existing QIF module; fall back to a local copy if imported standalone.
try:
    from ..channel_discovery import mutual_information
except Exception:                                            # pragma: no cover - standalone fallback
    from collections import Counter as _Counter
    from math import log2 as _log2

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
            mi += j * _log2(j / ((px[x] / n) * (py[y] / n)))
        return max(0.0, mi)


# --- the two measured quantities --------------------------------------------------------------------

def participation_utility(policy):
    """Measured task success: the fraction of encounters the agent survives acting ONLY on the compiled view.
    This is the 'usefulness currency' the first arc lacked — value of the disclosure for the observer's goal."""
    enc = encounters()
    return sum(1 for ws in enc if survives(agent_action(compile_observation(ws, policy)), ws)) / len(enc)


def leakage_bits(policy):
    """I(secret ; observation) in bits, over the encounter distribution — Quantitative Information Flow, via
    the `channel_discovery` estimator. How much of the exact cell the view reveals."""
    enc = encounters()
    pairs = [(secret(ws), view_key(compile_observation(ws, policy))) for ws in enc]
    return mutual_information(pairs)


# --- the measurement result (carries its boundary, never a bare 'safe') -----------------------------

class MeasurementResult:
    __slots__ = ("policy_name", "observer_class", "utility", "leakage", "utility_floor",
                 "leakage_budget", "sufficient", "within_leakage", "passes", "coverage_boundary")

    def __init__(self, policy_name, policy, utility, leakage):
        self.policy_name = policy_name
        self.observer_class = policy.observer_class
        self.utility = round(utility, 4)
        self.leakage = round(leakage, 4)
        self.utility_floor = policy.utility_floor
        self.leakage_budget = policy.leakage_budget
        self.sufficient = utility >= policy.utility_floor          # cleared the participation floor
        self.within_leakage = leakage <= policy.leakage_budget     # under the leakage budget
        self.passes = self.sufficient and self.within_leakage
        self.coverage_boundary = ("leakage = I(secret; view) via channel_discovery QIF, under THIS estimator / "
                                  "observer class; an adaptive adversary (M20/M21) or an unmodeled channel may "
                                  "extract more — compliant ≠ safe")

    def __repr__(self):
        return "<MeasurementResult %s U=%.3f L=%.3f sufficient=%s within=%s PASSES=%s>" % (
            self.policy_name, self.utility, self.leakage, self.sufficient, self.within_leakage, self.passes)


def evaluate(name, policy=None):
    policy = policy or POLICIES[name]
    return MeasurementResult(name, policy, participation_utility(policy), leakage_bits(policy))


def funnel_frontier():
    """The (utility, leakage) point for every committed policy — the first privacy-funnel frontier in the repo."""
    return {name: evaluate(name, p) for name, p in POLICIES.items()}


# --- the crucible (one complete loop, with two negative controls) -----------------------------------

def crucible():
    fr = funnel_frontier()
    out = {"frontier": {name: (r.utility, r.leakage) for name, r in fr.items()}}
    out["raw_utility"], out["raw_leakage"] = fr["raw"].utility, fr["raw"].leakage
    out["compiled_utility"], out["compiled_leakage"] = fr["compiled"].utility, fr["compiled"].leakage
    out["blind_utility"], out["blind_leakage"] = fr["blind"].utility, fr["blind"].leakage
    # the produced result: only the compiled policy clears BOTH the floor and the budget
    out["compiled_passes"] = fr["compiled"].passes
    out["raw_over_discloses"] = fr["raw"].sufficient and not fr["raw"].within_leakage   # useful but leaks
    out["blind_under_serves"] = fr["blind"].within_leakage and not fr["blind"].sufficient  # private but useless
    out["only_compiled_passes"] = fr["compiled"].passes and not fr["raw"].passes and not fr["blind"].passes
    out["compiled_cuts_leakage"] = fr["compiled"].leakage < fr["raw"].leakage
    out["compiled_preserves_utility"] = fr["compiled"].utility >= fr["raw"].utility
    return out


def demo():
    r = crucible()
    print("Perception loop — the first privacy-funnel benchmark (preserve task success under a leakage budget)\n")
    print("  world → DisclosurePolicy → compiled observation → agent → task → leakage measurement\n")
    print("  %-9s %-9s %-9s %s" % ("policy", "utility", "leakage", "verdict"))
    fr = funnel_frontier()
    for name in ("raw", "compiled", "blind"):
        res = fr[name]
        verdict = ("PASSES" if res.passes
                   else ("over-discloses" if res.sufficient else "under-serves"))
        print("  %-9s %-9.3f %-9.3f %s" % (name, res.utility, res.leakage, verdict))
    print("\n  budget: utility ≥ %.2f AND leakage ≤ %.1f bits (H(secret)=6 bits)." % (
        POLICIES["compiled"].utility_floor, POLICIES["compiled"].leakage_budget))
    print("  only 'compiled' clears both: same task success as raw, a fraction of the leakage. The funnel point.")
    print("  leakage measured by channel_discovery QIF, under this observer class — compliant ≠ safe.")
    return r
