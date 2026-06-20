# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/adversarial_dynamics.py — Adversarial Information Dynamics (M14): the defense is the leak.

M13 capped accumulation. M14 asks the harder question: can an attacker learn the *shape* of hidden state
through entirely legal interactions — by watching the defense REACT? The anti-cheat problem stops being
"stop bad data" and becomes "stop systems from inferring hidden state through the system's own behavior."

Five mechanisms, each with a negative control:

  1. REACTION DEBT — the defense leaks through its reactions. Fog spikes / occlusion shifts / LOD drops /
     latency rises exactly when the player nears a hidden enemy: no position is disclosed, but the
     DISCONTINUITY is the signal.  ReactionDebt = observer_change × inference_value × persistence.
     Safe reaction = behavior uncorrelated with the secret (constant or scheduled), so the change carries
     no information about the trigger.

  2. ABSENCE FIREWALL — the hardest cheats are "I noticed something MISSING" (no footstep, no particle, no
     streaming request, no packet). Absence Signal = expected − observed. missing ≠ informative unless the
     observer is causally entitled to that difference; otherwise the suppression must also mask its own gap.

  3. DISTRIBUTED RECONSTRUCTION DEBT — M11 blocked one observer, M13 one timeline; a GROUP is a distributed
     sensor (A sees timing, B particles, C audio, server the correction). Each fragment stays below
     threshold per-observer; their UNION reconstructs. The composition firewall must cap the global set.

  4. ADAPTIVE ≠ RANDOM — randomness alone has an exploitable distribution (the attacker averages it out).
     The defense boundary must MOVE in response to observed probing: "this observer's interaction pattern is
     making this dependency channel unsafe," not "hide this object."

  5. THE ULTIMATE INVARIANT — a representation may reveal CONSEQUENCES (explosion, damage, motion, sound)
     but never the MECHANISM by which hidden state becomes predictable (why before it happened, who before
     causality exists, which hidden branch was prepared). That is the anti-wallhack floor.

CLASSIFICATION: OBSERVER (mutates_core=False). M14 is closer to a game-theoretic control layer than a render
pass, but it still commits nothing and asserts no truth. reaction ≠ disclosure; absence ≠ information;
consequence ≠ mechanism; integrity ≠ truth.

HONEST BOUND: declared correlation/bit/probe proxies, not measured covert-channel capacity against a real
learner; the result is the SHAPE of each defense. Every constructed number expires against real telemetry —
which is exactly where M14 stops being a renderer milestone and needs real traffic to tune against.
"""
from __future__ import annotations


# --- 1. Reaction Debt (the defense leaks through its own reactions) ---------------------------------

class ReactionMonitor:
    """Watches whether the defense's observable behavior is CORRELATED with a hidden trigger. If the reaction
    only fires when the secret is near, the reaction itself is the channel."""

    def __init__(self):
        self.events = []      # (trigger_present: 0/1, reaction_magnitude)

    def observe(self, trigger_present, reaction_magnitude):
        self.events.append((1 if trigger_present else 0, max(0, int(reaction_magnitude))))

    def correlation_leak(self):
        """|E[reaction | trigger] − E[reaction | no trigger]|. 0 ⇒ behavior reveals nothing about the secret."""
        on = [m for t, m in self.events if t]
        off = [m for t, m in self.events if not t]
        if not on or not off:
            return 0
        return abs(sum(on) // len(on) - sum(off) // len(off))


def reaction_debt(observer_change, inference_value, persistence):
    """Information revealed by CHANGING behavior. observer_change is the correlation_leak (0 if the reaction
    is independent of the secret); inference_value = how diagnostic it is; persistence = how long it lingers."""
    return observer_change * inference_value * persistence


def safe_reaction(baseline, _trigger_present):
    """A reaction that does NOT depend on the secret: emit the same baseline whether or not the trigger is
    present. The defense still acts (fog, LOD, latency budgeting) — it just acts uncorrelated with the secret."""
    return baseline


# --- 2. Absence firewall (missing ≠ informative) ----------------------------------------------------

def absence_signal(expected, observed):
    """The negative-space channel: what is conspicuously MISSING relative to the expected representation."""
    return max(0, expected - observed)


def mask_absence(expected, observed, entitled):
    """If the observer is NOT causally entitled to the difference, the suppression must also fill its own gap
    (a decoy keeps observed == expected) so absence carries no information. If entitled, the gap is honest."""
    if entitled:
        return observed
    return expected          # decoy fills the hole → absence_signal == 0


# --- 3. Distributed Reconstruction Debt (cross-client triangulation) --------------------------------

def per_observer_reconstruction(observer_fragments, fact_bits):
    """fraction reconstructed by EACH observer alone (each may sit safely below threshold)."""
    return {o: min(1.0, sum(bits) / max(1, fact_bits)) for o, bits in observer_fragments.items()}


def distributed_reconstruction(observer_fragments, fact_bits):
    """fraction reconstructed by the UNION of all observers (the colluding group as one distributed sensor)."""
    total = sum(b for bits in observer_fragments.values() for b in bits)
    return min(1.0, total / max(1, fact_bits))


def distributed_firewall(observer_fragments, fact_bits, threshold=0.5):
    """Admit fragments globally (across ALL observers) only while the cumulative reconstruction stays under
    threshold; block the marginal fragment that would cross it — even though each observer is individually safe."""
    cap = threshold * fact_bits
    cumulative = 0
    admitted, blocked = [], []
    for obs in sorted(observer_fragments):
        for i, bits in enumerate(observer_fragments[obs]):
            if cumulative + bits <= cap:
                cumulative += bits
                admitted.append((obs, i))
            else:
                blocked.append((obs, i))
    return {"reconstruction": min(1.0, cumulative / max(1, fact_bits)),
            "admitted": admitted, "blocked": blocked}


# --- 4. Adaptive ≠ random defense -------------------------------------------------------------------

def random_defense_leak(probes, base_leak=10):
    """A fixed-distribution defense: every probe leaks the same amount; a learner just averages it out."""
    return [base_leak] * probes


def adaptive_defense_leak(probes, base_leak=10):
    """The boundary MOVES with observed probing: each probe is detected and tightens the channel, so sustained
    probing yields diminishing information (the defense adapts to the attacker, it does not roll dice)."""
    out, detected = [], 0
    for _ in range(probes):
        out.append(max(0, base_leak // (1 + detected)))
        detected += 1
    return out


# --- 5. the ultimate invariant: consequence may be revealed, mechanism may not ----------------------

CONSEQUENCE = {"explosion", "damage", "visible_motion", "sound", "destruction"}
MECHANISM = {"why_before_event", "cause_before_causality", "prepared_branch", "predicted_position",
             "hidden_branch_choice"}


def reveals_mechanism(kind, when_relative_to_event):
    """A disclosure reveals MECHANISM if it names a hidden cause/branch, OR if it exposes a consequence BEFORE
    the committed event (showing the explosion early is prediction = the mechanism of how the secret becomes
    knowable). Consequences are admissible only at/after the event commits on the Weltlinie."""
    if kind in MECHANISM:
        return True
    if kind in CONSEQUENCE and when_relative_to_event < 0:
        return True            # a consequence shown early leaks the predictive mechanism
    return False


def admissible_disclosure(kind, when_relative_to_event):
    """A representation may reveal consequences (at/after commit) but never the mechanism by which hidden state
    becomes predictable. This is the anti-wallhack floor."""
    return (kind in CONSEQUENCE) and (when_relative_to_event >= 0) and not reveals_mechanism(kind, when_relative_to_event)


# --- the adaptation crucible ------------------------------------------------------------------------

def crucible():
    out = {}
    # 1. reaction debt: a naive defense reacts only near the hidden enemy → correlated; safe defense is constant
    naive, safe = ReactionMonitor(), ReactionMonitor()
    pattern = [True, False, True, False, True, False, True, False]
    for trig in pattern:
        naive.observe(trig, 10 if trig else 1)            # fog spikes near the secret → leak
        safe.observe(trig, safe_reaction(5, trig))        # constant fog → no leak
    out["reaction_naive_leak"] = reaction_debt(naive.correlation_leak(), inference_value=2, persistence=3)
    out["reaction_safe_leak"] = reaction_debt(safe.correlation_leak(), inference_value=2, persistence=3)
    # 2. absence: suppressing a footstep particle leaves a hole; the decoy masks it for the unentitled observer
    expected, observed = 10, 0
    out["absence_naive"] = absence_signal(expected, observed)
    out["absence_masked"] = absence_signal(expected, mask_absence(expected, observed, entitled=False))
    out["absence_entitled_honest"] = absence_signal(expected, mask_absence(expected, observed, entitled=True))
    # 3. distributed: 3 observers, 20 bits each (each 0.31 < 0.5); union 60/64 ≈ 0.94 reconstructs
    frags = {"A": [20], "B": [20], "C": [20]}
    per = per_observer_reconstruction(frags, fact_bits=64)
    out["per_observer_each_safe"] = all(v <= 0.5 for v in per.values())
    out["distributed_union"] = distributed_reconstruction(frags, fact_bits=64)
    out["distributed_firewalled"] = distributed_firewall(frags, fact_bits=64, threshold=0.5)["reconstruction"]
    # 4. adaptive vs random over 20 probes
    out["random_total"] = sum(random_defense_leak(20))
    out["adaptive_total"] = sum(adaptive_defense_leak(20))
    # 5. mechanism vs consequence
    out["consequence_after_ok"] = admissible_disclosure("explosion", when_relative_to_event=2)
    out["consequence_before_blocked"] = not admissible_disclosure("explosion", when_relative_to_event=-3)
    out["mechanism_always_blocked"] = not admissible_disclosure("prepared_branch", when_relative_to_event=5)
    return out


def demo():
    r = crucible()
    print("Adversarial Information Dynamics — the DEFENSE is the leak\n")
    print("  1. reaction debt: naive (reacts near the secret)=%d  vs  safe (constant reaction)=%d"
          % (r["reaction_naive_leak"], r["reaction_safe_leak"]))
    print("  2. absence: missing-particle signal naive=%d  masked(unentitled)=%d  entitled(honest)=%d"
          % (r["absence_naive"], r["absence_masked"], r["absence_entitled_honest"]))
    print("  3. distributed: each observer alone safe=%s; union reconstructs=%.2f; firewalled=%.2f"
          % (r["per_observer_each_safe"], r["distributed_union"], r["distributed_firewalled"]))
    print("  4. adaptive vs random over 20 probes: random leaks %d  vs  adaptive %d (boundary moves on probing)"
          % (r["random_total"], r["adaptive_total"]))
    print("  5. invariant: consequence-after-event ok=%s; consequence-before blocked=%s; mechanism blocked=%s"
          % (r["consequence_after_ok"], r["consequence_before_blocked"], r["mechanism_always_blocked"]))
    print("\n  a representation may reveal CONSEQUENCES, never the MECHANISM by which hidden state becomes")
    print("  predictable. reaction ≠ disclosure; absence ≠ information; consequence ≠ mechanism; integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("adversarial_dynamics", OBSERVER, mutates_core=False,
                          note="Adversarial Information Dynamics — Reaction Debt + absence firewall + "
                               "distributed reconstruction + adaptive≠random + consequence≠mechanism invariant")
    except LayerViolation:
        pass
