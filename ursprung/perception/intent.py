# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/intent.py — Intent Leakage I(G ; A,O): the secret is the policy, not the data.

The action channel (`response.py`) showed the actor's behaviour re-leaks the world secret `S`. This layer goes
one level deeper, to the secret the LLM era actually exposes: not *what the world is* but *what optimization
process is producing this behaviour*. An observer running **inverse planning** ("what goal would make this
behaviour rational?") need never recover `S` — it recovers `G`, the agent's goal / policy / preference:

    you can fail privacy while preserving the secret:
        the opponent never learns  enemy_location = X
        but learns                 "this agent always retreats when X is nearby"
    the data is hidden; the strategy is exposed.

So the unifying quantity is **intent leakage** `I(G ; A, O)` — the recoverability of the policy from behaviour,
the object behind inverse reinforcement learning, Bayesian intention inference, and signaling theory. This is a
*different secret* from `I(S;O)` and `I(S;A)`, and for an adaptive agent it is often the dominant one: the world
changes, but the policy is invariant and therefore far more worth stealing.

Bench: a hidden goal `G ∈ {aggressive, defensive, evasive}`, each a deterministic context→action policy. An
observer watches `(context, action)` pairs and infers `G`. Findings, mirroring every prior channel:

  * intent leakage **accumulates** — `I(G ; behaviour)` rises from 0 (one ambiguous action) to `H(G)=1.585`
    bits (the *whole* policy recovered) as observations compound. The cascade/accumulation structure, now on
    the optimizer.
  * a **behavioral-ambiguity** defense (make goals act alike) caps `I(G;A)` below `H(G)` — at the coupled cost
    of losing the goals' distinct optimal behaviour. The same tradeoff economics as every other channel.

The endpoint your other layers were circling: the most privacy-preserving intelligent system is not the one
that hides the most data, but the one that has learned *when acting itself is the unnecessary disclosure* — and
that knows its own policy is the thing most worth concealing.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: a toy with deterministic policies; the real object
is inverse RL / Bayesian intent inference over stochastic policies, and the ambiguity defense is coupled by
construction. `I(G;A,O)` is a *different* secret from `I(S;·)`; behaviour is a message; non-action ≠ ignorance;
simulation ≠ physics.
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


GOALS = ("aggressive", "defensive", "evasive")
H_GOAL = log2(len(GOALS))                       # 1.585 bits — the full policy, if uniform over goals
CONTEXTS = (0, 1, 2, 3)

# Each goal is a context→action policy. Designed so the goal is only distinguishable as behaviour ACCUMULATES:
# all three act the same at context 0, and separate progressively — the inverse-planning / cascade structure.
COMMITTED = {
    "aggressive": ("advance", "advance", "hold", "hold"),
    "defensive":  ("advance", "hold", "hold", "retreat"),
    "evasive":    ("advance", "hold", "retreat", "retreat"),
}

# A behavioral-ambiguity defense: defensive and evasive act identically, so they cannot be told apart — at the
# cost of the agent no longer pursuing them as distinct goals.
AMBIGUOUS = {
    "aggressive": ("advance", "advance", "hold", "hold"),
    "defensive":  ("hold", "hold", "hold", "hold"),
    "evasive":    ("hold", "hold", "hold", "hold"),
}


def behavior(policy, goal, horizon):
    """The action sequence an observer sees over the first `horizon` contexts under a goal's policy."""
    return tuple(policy[goal][c] for c in range(horizon))


def intent_leakage(policy, horizon):
    """I(G ; behaviour): how much of the agent's goal/policy is recoverable from its observed behaviour."""
    return mutual_information([(g, behavior(policy, g, horizon)) for g in GOALS])


def intent_curve(policy=COMMITTED):
    """Intent leakage as a function of how much behaviour the observer has accumulated."""
    return [(w, round(intent_leakage(policy, w), 3)) for w in range(1, len(CONTEXTS) + 1)]


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    full = len(CONTEXTS)
    out["curve"] = intent_curve(COMMITTED)
    out["intent_leakage_full"] = round(intent_leakage(COMMITTED, full), 3)
    out["single_observation"] = round(intent_leakage(COMMITTED, 1), 3)
    # the policy is recoverable from behaviour, and recovery ACCUMULATES toward the whole policy
    out["intent_is_a_secret"] = intent_leakage(COMMITTED, full) > 0
    out["full_policy_recovered"] = abs(intent_leakage(COMMITTED, full) - H_GOAL) < 1e-9
    bits = [b for _, b in out["curve"]]
    out["intent_accumulates"] = all(bits[i + 1] >= bits[i] for i in range(len(bits) - 1))
    out["single_observation_ambiguous"] = intent_leakage(COMMITTED, 1) < H_GOAL
    # the behavioral-ambiguity defense caps intent leakage — at the cost of goal distinctness (coupled)
    out["ambiguous_leakage_full"] = round(intent_leakage(AMBIGUOUS, full), 3)
    out["ambiguity_caps_intent_leak"] = intent_leakage(AMBIGUOUS, full) < H_GOAL
    out["ambiguity_costs_distinctness"] = AMBIGUOUS["defensive"] == AMBIGUOUS["evasive"]
    return out


def demo():
    r = crucible()
    print("Intent Leakage I(G;A,O) — the secret is the POLICY, not the data\n")
    print("  a hidden goal G ∈ {aggressive, defensive, evasive}, each a context→action policy. an observer")
    print("  does inverse planning: 'what goal makes this behaviour rational?' — it never needs the world state.\n")
    print("  observations W   I(G ; behaviour) bits")
    for w, b in r["curve"]:
        print("       %d              %.3f" % (w, b))
    print()
    print("  · the goal IS recoverable from behaviour, and recovery ACCUMULATES to the whole policy (%.3f = H(G)):"
          % r["intent_leakage_full"])
    print("    one action is ambiguous (%.3f); a session of them exposes the optimizer." % r["single_observation"])
    print("  · a behavioral-ambiguity defense caps the leak (%.3f < %.3f) — but the goals become indistinct: %s"
          % (r["ambiguous_leakage_full"], H_GOAL, r["ambiguity_costs_distinctness"]))
    print("\n  you can hide the data and still expose the strategy. for an adaptive agent the policy is the")
    print("  dominant secret — the world changes, the optimizer does not. I(G;·) is a different secret from I(S;·).")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.intent", OBSERVER, mutates_core=False,
                          note="Intent Leakage I(G;A,O): the secret generalizes from world-state S to the "
                               "agent's GOAL/POLICY G. an inverse-planning observer recovers the policy from "
                               "behaviour (accumulates to H(G)); behavioral ambiguity caps it at the cost of "
                               "goal distinctness. the secret is the policy, not the data — the LLM-era object")
    except LayerViolation:
        pass
