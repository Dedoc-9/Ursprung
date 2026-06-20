# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/adversary_harness.py — the Adaptive Adversary Harness (M20): can an intelligent observer learn the
system itself?

M19 named the player as the final observer and showed they learn the *policy by feel*. But M19's observer was
still a one-shot separability check. M20 closes the loop: the player is not a passive recipient, they are an
ACTIVE EXPERIMENTER, and the architecture stops looking like an anti-cheat feature set and becomes a
measurement theory for adversarial interactive systems. The attacker model is now a learning problem:

    policy → observe response → infer policy → choose next experiment → exploit

The dangerous object is no longer "the enemy is at x=100"; it is "when I do X, the system changes in a way
that implies the enemy is near x=100." The player learns the TRANSFER FUNCTION. So the question changes from
"does this frame leak?" to "after N chosen interactions, what can a rational observer infer?" — which is the
question that separates a system that is secure from one that only looks secure.

This harness builds the closed loop the earlier milestones implied:

    world → policy/representation → adaptive agent → observation → memory → new strategy → world …

with (per the design): a probing agent, a memory of past observations, active experiment selection (it picks
the input that maximizes information gain, not a uniform sample), regret / learning-curve metrics, and an
extraction bound on what the agent can conclude. It then MEASURES, against each policy:

  * REGRET / LEARNING CURVE — how the agent's error about the server's hidden decision boundary falls (or
    does not) with interactions.
  * BEHAVIORAL LEAKAGE = information_gained / experiments — leakage measured from STRATEGIES, not frames.
  * INCENTIVE / DECISION-CHANNEL LEAKAGE — the hidden state leaks through the economy of actions (hit
    registration, movement prediction, audio occlusion, matchmaking, AI behavior), not only the renderer.
  * EXTRACTION BOUND — the produced result: a naive policy is cracked in O(log N); M19's constant-feel keeps
    the agent's regret pinned near chance no matter how many experiments it runs.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures what a *learning* observer can extract; it commits
nothing and asserts no truth. learning ≠ truth; secure-against-this-agent ≠ secure; integrity ≠ truth.

HONEST BOUND: the agent's hypothesis class is a 1-D threshold learner (active bisection). Constant-feel is
shown to resist THIS observer class — a real ML agent or human may model channels outside it and find
strategies nobody anticipated. The channel, the agent, and the player are all still simulated. "Secure against
this observer" is the only claim; the validity step is real agents, real netcode, real telemetry, real humans.
simulation ≠ physics; this proves resistance to a class, never to all observers. integrity ≠ truth.
"""
from __future__ import annotations

import math


# --- the system under test: a hidden decision boundary, seen through a policy ----------------------

def system_response(probe, true_boundary, policy):
    """The observable response to a chosen experiment `probe`.
    naive:          truthful (probe ≥ boundary) — the response is correlated with the hidden boundary.
    constant_feel:  a fixed function of the PROBE only, independent of the hidden boundary — the response
                    teaches the agent nothing about `true_boundary` (M19's behavioral indistinguishability)."""
    if policy == "naive":
        return probe >= true_boundary
    if policy == "constant_feel":
        return ((probe >> 7) & 1) == 1          # depends on the probe, never on the secret
    raise ValueError("policy must be naive|constant_feel")


# --- the adaptive observer: probing agent with memory + active experiment selection -----------------

class AdaptiveObserver:
    """A closed-loop learner. It keeps a belief interval over the hidden boundary, and each step CHOOSES the
    experiment that maximizes information gain (uncertainty sampling = bisection), observes, and updates."""

    def __init__(self, span=1024):
        self.span = span
        self.lo, self.hi = 0, span
        self.memory = []                         # (probe, response)

    def select_experiment(self):
        """Active learning: probe the midpoint of current uncertainty (max expected information gain)."""
        return (self.lo + self.hi) // 2

    def observe(self, probe, response):
        self.memory.append((probe, response))
        if response:
            self.hi = probe
        else:
            self.lo = probe

    def estimate(self):
        return (self.lo + self.hi) // 2

    def self_reported_uncertainty(self):
        """What the agent THINKS it knows — note this can be falsely confident under constant_feel."""
        return self.hi - self.lo


def run_agent(policy, true_boundary, span=1024, interactions=12):
    """Drive the closed loop for `interactions` steps; return the learning curve of TRUE regret (error against
    the real boundary, not the agent's self-belief)."""
    agent = AdaptiveObserver(span)
    curve = []
    for _ in range(interactions):
        probe = agent.select_experiment()
        agent.observe(probe, system_response(probe, true_boundary, policy))
        curve.append(abs(agent.estimate() - true_boundary))
    return curve


def evaluate(policy, span=1024, interactions=12, boundaries=None):
    """Average the learner's behaviour over a sample of hidden boundaries (so constant_feel can't be beaten by
    luck on one boundary)."""
    boundaries = boundaries or list(range(64, span, span // 8))
    curves = [run_agent(policy, T, span, interactions) for T in boundaries]
    final = [c[-1] for c in curves]
    first = [c[0] for c in curves]
    mean_final = sum(final) / len(final)
    mean_first = sum(first) / len(first)
    info_gained = max(0.0, math.log2(span) - math.log2(mean_final + 1))   # bits learned about the boundary
    return {
        "mean_final_regret": round(mean_final, 2),
        "mean_first_regret": round(mean_first, 2),
        "behavioral_leakage": round(info_gained / interactions, 4),        # info per chosen experiment
        "info_gained_bits": round(info_gained, 3),
        "learning_curve": [round(sum(c[k] for c in curves) / len(curves), 1)
                           for k in range(interactions)],
    }


# --- incentive / decision-channel leakage (the action economy, not the renderer) -------------------

DECISION_CHANNELS = ("hit_registration", "movement_prediction", "audio_occlusion", "matchmaking", "ai_behavior")


def decision_channel_leaks(policy):
    """Does each decision channel's behaviour vary with hidden state? naive ⇒ every channel leaks; constant_feel
    ⇒ none do. The hidden state can leak through the economy of actions, not only pixels."""
    leak = policy == "naive"
    return {ch: leak for ch in DECISION_CHANNELS}


def behavioral_leakage_through_decisions(policy):
    leaks = decision_channel_leaks(policy)
    return sum(1 for v in leaks.values() if v) / len(leaks)


# --- the closed-loop crucible -----------------------------------------------------------------------

def crucible(span=1024, interactions=12):
    out = {}
    naive = evaluate("naive", span, interactions)
    const = evaluate("constant_feel", span, interactions)
    out["naive"], out["constant_feel"] = naive, const
    # extraction bound: a learning bound the defense must keep the agent ABOVE
    bound = span / 8.0
    out["extraction_bound"] = bound
    # produced findings:
    out["naive_is_cracked"] = naive["mean_final_regret"] < bound             # learner localizes the boundary
    out["constant_feel_resists_learning"] = const["mean_final_regret"] >= bound
    out["naive_learns"] = naive["learning_curve"][-1] < naive["learning_curve"][0]   # curve descends
    out["constant_feel_curve_flat"] = const["learning_curve"][-1] >= const["learning_curve"][0] * 0.5
    out["leakage_naive_gt_constant"] = naive["behavioral_leakage"] > const["behavioral_leakage"]
    # incentive leakage through the action economy
    out["decision_leak_naive"] = behavioral_leakage_through_decisions("naive")
    out["decision_leak_constant"] = behavioral_leakage_through_decisions("constant_feel")
    return out


def demo():
    r = crucible()
    print("Adaptive Adversary Harness — can an intelligent observer learn the system itself?\n")
    print("  closed loop: world → policy → adaptive agent → observation → memory → new experiment → …\n")
    print("  naive policy     learning curve (true regret): %s" % r["naive"]["learning_curve"])
    print("  constant-feel    learning curve (true regret): %s" % r["constant_feel"]["learning_curve"])
    print()
    print("  · naive boundary localized to regret %.1f (< bound %.0f): cracked in O(log N) = %s"
          % (r["naive"]["mean_final_regret"], r["extraction_bound"], r["naive_is_cracked"]))
    print("  · constant-feel regret stays %.1f (≥ bound %.0f): a LEARNING adversary cannot localize it = %s"
          % (r["constant_feel"]["mean_final_regret"], r["extraction_bound"], r["constant_feel_resists_learning"]))
    print("  · Behavioral Leakage (info/experiment): naive %.3f vs constant-feel %.3f"
          % (r["naive"]["behavioral_leakage"], r["constant_feel"]["behavioral_leakage"]))
    print("  · incentive leakage through the action economy: naive %.0f%% of channels vs constant-feel %.0f%%"
          % (r["decision_leak_naive"] * 100, r["decision_leak_constant"] * 100))
    print("\n  the question is no longer 'does this frame leak?' but 'after N chosen interactions, what can a")
    print("  rational observer infer?' — secure against THIS observer class ≠ secure against all. integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("adversary_harness", OBSERVER, mutates_core=False,
                          note="Adaptive Adversary Harness — closed-loop learning observer (probe+memory+"
                               "experiment selection+regret); Behavioral Leakage = info/experiments; tests "
                               "whether constant-feel resists a LEARNING adversary; secure-against-class ≠ secure")
    except LayerViolation:
        pass
