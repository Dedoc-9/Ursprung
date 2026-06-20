# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/representation_privacy.py — Representation Privacy / Ambiguity Control (M15): image ≠ generator.

The arc so far asked, in order: is the claim intact (M10), may this observer use it (M11), does the
combination reveal too much (M12), does history (M13), does the defense's own behavior (M14)? M15 closes the
loop: once the system *intentionally* manages uncertainty, the management itself can become a signal. The
final attack is not inferring the hidden object — it is inferring the **generator**: the rule that maps
hidden state → representation ("streaming stalls ⇒ enemy near", "particles appear ⇒ a hitbox loaded").

This is the refinement of M14's `consequence ≠ mechanism` into the sharper invariant **`image ≠ generator`**:
a representation may expose the world, but not the function that produced it.

Five mechanisms, each with a negative control:

  1. AMBIGUITY DEBT — a system can leak by being too *precise*. If the exposed uncertainty radius shrinks as a
     monotone, invertible function of the true secret, the uncertainty field is itself a measurement
     instrument. AmbiguityDebt = expected_uncertainty − attacker_residual_uncertainty. The goal is not
     maximum fog; it is that uncertainty does not become an instrument.
  2. REPRESENTATION HYSTERESIS — a single safe→unsafe→safe threshold oscillates and the attacker reads the
     boundary by hovering on it. The fix is the shader-stability / transition-debt fix: enter-threshold ≠
     exit-threshold (a thermostat: hide at 100, reveal at 70). SecurityHysteresisDebt ∝ probe-able flips.
  3. DECOY WITHOUT REALITY MUTATION — CORE cannot lie (no fake committed entity). VIEW may emit
     non-informative continuity / equivalent-cost representation. The distinction: fake REALITY is forbidden;
     a fake OBSERVABILITY pattern (that asserts no world fact and mutates no core) is admissible.
  4. OBSERVER FINGERPRINT DEBT — extends `importance ≠ exposure` to `observer behavior ≠ representation
     policy`. Two observers acting differently must not get wildly different representation transitions unless
     the world state requires it. FingerprintDebt = observer-specific variance not causally required.
  5. image ≠ generator — a representation may expose world consequences but not the engine rules that map
     hidden state to representation. Implementation tells (streaming/particle/animation correlated with the
     secret) leak the generator even when no world fact is disclosed.

CLASSIFICATION: OBSERVER (mutates_core=False). It shapes how uncertainty is *presented*; it never mutates the
Weltlinie and never asserts a false world fact. ambiguity ≠ deception; image ≠ generator; integrity ≠ truth.

HONEST BOUND — what this is NOT. These are STRUCTURAL proxies (coarse quantization, hysteresis bands, variance
caps), not a cryptographic guarantee. The formal version of "image ≠ generator" is **Indistinguishability
Obfuscation (iO)**: two circuits with identical I/O are computationally indistinguishable, resting on
Goldreich-Levin hard-core predicates and the conjectured hardness of Learning-With-Errors / discrete log. iO
gives a *provable* bound on what the generator leaks; our shaping gives only the SHAPE of that goal under
declared assumptions. We can demonstrate that an invertible exposure leaks and a quantized one leaks less — we
cannot claim indistinguishability. Treat every number here as a model construct that expires against a real
adversary and a real hardness assumption. integrity ≠ truth.
"""
from __future__ import annotations


# --- 1. Ambiguity Debt (uncertainty must not become a measurement instrument) -----------------------

SECRET_RANGE = 10           # the secret (e.g. true distance 0..10) the design intends to keep ambiguous


def exposed_radius(true_secret, mode):
    """The uncertainty radius the renderer EXPOSES for a hidden object given the true secret.
    naive: radius tracks the secret exactly (invertible — the fog IS a ruler).
    shaped: coarse / constant (the secret is not recoverable from the exposed structure)."""
    if mode == "naive":
        return max(0, SECRET_RANGE - int(true_secret))      # shrinks precisely as the player approaches
    if mode == "shaped":
        return 8                                            # constant: reveals nothing about the secret
    raise ValueError("mode must be naive|shaped")


def recoverable_levels(secrets, mode):
    """How many distinct secret values an attacker can DISTINGUISH from the exposed uncertainty structure."""
    return len({exposed_radius(s, mode) for s in secrets})


def attacker_residual_uncertainty(secrets, mode):
    """The ambiguity an attacker is actually left with after reading the exposed structure."""
    return SECRET_RANGE / recoverable_levels(secrets, mode)


def ambiguity_debt(secrets, mode, expected=SECRET_RANGE):
    """Expected ambiguity minus what the attacker is actually left with. High ⇒ the uncertainty field has
    collapsed into a measurement instrument."""
    return max(0.0, expected - attacker_residual_uncertainty(secrets, mode))


# --- 2. Representation Hysteresis (the boundary must resist being used as a probe) -------------------

class HysteresisBoundary:
    """A representation visibility boundary with separate enter/exit thresholds (a thermostat). A single
    threshold flips on every crossing — the attacker hovers on it and reads the rule. A band does not."""

    def __init__(self, enter, exit_, state="visible"):
        self.enter = enter      # become hidden at/above this
        self.exit = exit_       # become visible at/below this
        self.state = state

    def update(self, signal):
        if self.state == "visible" and signal >= self.enter:
            self.state = "hidden"
        elif self.state == "hidden" and signal <= self.exit:
            self.state = "visible"
        return self.state


def count_flips(enter, exit_, signals):
    b = HysteresisBoundary(enter, exit_)
    prev, flips = b.state, 0
    for s in signals:
        st = b.update(s)
        if st != prev:
            flips += 1
            prev = st
    return flips


def security_hysteresis_debt(enter, exit_, signals):
    """Each boundary flip is a probe-able event; a probe-able boundary leaks its threshold."""
    return count_flips(enter, exit_, signals)


# --- 3. decoy without reality mutation (fake reality ❌ / fake observability pattern ✅) --------------

def decoy_admissible(decoy):
    """A decoy is admissible iff it neither mutates committed state nor asserts a false world fact. It may only
    fill an observability pattern (continuity, equivalent-cost representation). CORE cannot lie; VIEW may
    smooth. fake REALITY is forbidden; a fake OBSERVABILITY PATTERN is allowed."""
    return (not decoy.get("mutates_core", False)) and (not decoy.get("asserts_world_fact", False))


# --- 4. Observer Fingerprint Debt (observer behavior ≠ representation policy) ------------------------

def fingerprint_debt(policy_per_observer, causally_required_variance=0):
    """Variance in representation policy ACROSS observers that the world state does not require. If two
    observers in the same situation get different transitions, the attacker has made the engine reveal its
    rules. Extends `importance ≠ exposure` to `observer behavior ≠ representation policy`."""
    if not policy_per_observer:
        return 0
    spread = max(policy_per_observer) - min(policy_per_observer)
    return max(0, spread - causally_required_variance)


# --- 5. image ≠ generator (the final invariant) -----------------------------------------------------

WORLD_FACTS = {"explosion", "damage", "door_opened", "visible_motion", "sound"}
GENERATOR_TELLS = {"streaming_stall_implies_proximity", "particle_implies_hitbox_loaded",
                   "anim_compression_implies_npc_active", "lod_drop_implies_entity"}


def reveals_generator(kind, impl_correlation):
    """A disclosure reveals the GENERATOR if it is a known implementation tell, OR if an engine-internal event
    (streaming/particle/animation) is correlated with hidden state — letting the observer infer the mapping
    rather than the world."""
    return (kind in GENERATOR_TELLS) or (impl_correlation > 0)


def admissible_world_observation(kind, impl_correlation):
    """A representation may expose a world consequence; it may not expose the rule that maps hidden state to
    representation. image ≠ generator."""
    return (kind in WORLD_FACTS) and not reveals_generator(kind, impl_correlation)


# --- the ambiguity-control crucible -----------------------------------------------------------------

def crucible():
    out = {}
    secrets = list(range(SECRET_RANGE + 1))
    # 1. ambiguity debt: invertible exposure collapses the field; coarse exposure preserves it
    out["ambiguity_naive"] = ambiguity_debt(secrets, "naive")
    out["ambiguity_shaped"] = ambiguity_debt(secrets, "shaped")
    out["naive_recoverable"] = recoverable_levels(secrets, "naive")
    out["shaped_recoverable"] = recoverable_levels(secrets, "shaped")
    # 2. hysteresis: a signal ramps past 100 once, then oscillates in [72..98]
    signals = [60, 70, 85, 95, 110] + [98, 72, 96, 74, 95, 73, 97, 72, 94, 75]
    out["single_threshold_flips"] = security_hysteresis_debt(80, 80, signals)
    out["hysteresis_flips"] = security_hysteresis_debt(100, 70, signals)
    # 3. decoy: a fake committed enemy lies about reality; baseline continuity particles do not
    out["fake_reality_blocked"] = not decoy_admissible(
        {"name": "spawn_fake_enemy", "mutates_core": False, "asserts_world_fact": True})
    out["fake_observability_ok"] = decoy_admissible(
        {"name": "baseline_continuity_particles", "mutates_core": False, "asserts_world_fact": False})
    out["core_mutation_blocked"] = not decoy_admissible(
        {"name": "rewrite_state", "mutates_core": True, "asserts_world_fact": False})
    # 4. fingerprint debt: same situation, different per-observer policy (not causally required) leaks the rules
    out["fingerprint_leak"] = fingerprint_debt([10, 50], causally_required_variance=0)
    out["fingerprint_hardened"] = fingerprint_debt([30, 30], causally_required_variance=0)
    # 5. image != generator
    out["world_fact_ok"] = admissible_world_observation("explosion", impl_correlation=0)
    out["generator_tell_blocked"] = not admissible_world_observation("streaming_stall_implies_proximity", 0)
    out["correlated_impl_blocked"] = not admissible_world_observation("explosion", impl_correlation=7)
    return out


def demo():
    r = crucible()
    print("Representation Privacy / Ambiguity Control — image ≠ generator\n")
    print("  1. ambiguity debt: invertible exposure=%.2f (recoverable %d levels) vs shaped=%.2f (%d level)"
          % (r["ambiguity_naive"], r["naive_recoverable"], r["ambiguity_shaped"], r["shaped_recoverable"]))
    print("  2. hysteresis: single-threshold flips=%d (probe-able) vs enter≠exit band flips=%d"
          % (r["single_threshold_flips"], r["hysteresis_flips"]))
    print("  3. decoy: fake reality blocked=%s; fake observability pattern ok=%s; core mutation blocked=%s"
          % (r["fake_reality_blocked"], r["fake_observability_ok"], r["core_mutation_blocked"]))
    print("  4. fingerprint debt: uncaused per-observer variance leak=%d vs hardened=%d"
          % (r["fingerprint_leak"], r["fingerprint_hardened"]))
    print("  5. image ≠ generator: world fact ok=%s; generator-tell blocked=%s; correlated-impl blocked=%s"
          % (r["world_fact_ok"], r["generator_tell_blocked"], r["correlated_impl_blocked"]))
    print("\n  a representation may expose the WORLD, never the rule that maps hidden state → representation.")
    print("  the formal form of this is Indistinguishability Obfuscation; this is its SHAPE, not its proof.")
    print("  ambiguity ≠ deception; image ≠ generator; integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("representation_privacy", OBSERVER, mutates_core=False,
                          note="Representation Privacy / Ambiguity Control — ambiguity debt + representation "
                               "hysteresis + decoy-without-mutation + fingerprint debt + image≠generator")
    except LayerViolation:
        pass
