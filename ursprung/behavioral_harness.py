# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/behavioral_harness.py — the Behavioral Reality Harness (M19): the last observer is the player.

M18 turned the project's discipline on itself: it forced the distinction between a *representation policy* and
an *information-flow guarantee*, and it measured observable behavior. But M18 was still passive (traffic →
measurement) and it collapsed leakage into scalars. M19 closes three gaps the M18 result exposed, then names
the final observer the whole stack was always serving.

  1. CONVERGENCE LEAKAGE VECTOR (CLV) — privacy is not a scalar. The exact/bucketed/floor result proved that
     correction *magnitude*, *existence*, *timing*, *correlation*, and *aggregation* are independent axes: a
     player who knows "a rollback happened + an event was nearby + the timing matches" has reconstructed the
     cause without ever seeing the magnitude. The harness emits a VECTOR (mirroring the M6 resistance tensor),
     never one "privacy" number — and the vector reveals that no M17/M18 policy ever touched the *timing* axis.
  2. ADVERSARIAL PROBE CONTROL / COUNTERFACTUAL AMPLIFICATION — a passive client and an adversarial client are
     different systems. The attacker does not sample uniformly; it chooses inputs to estimate the server's
     hidden decision boundary (input A → observe correction → input A′ → observe Δ → repeat). A correction is
     dangerous not for the bit it carries but because the attacker chooses the question:
        Counterfactual Debt = correction_information × probe_control.
     One bit × ten-thousand chosen experiments is a query oracle (M13, where the query is now a *world
     perturbation*).
  3. THE EXPERIMENT-LAYER SEAM — the same measurement API runs over a SIMULATED channel (deterministic,
     replayable → a regression environment) and a REAL channel (UDP/TCP/QUIC → the validity environment). The
     simulator is not thrown away when the socket arrives; it becomes the regression bed. This is the
     CORE-truth / VIEW-representation separation, lifted to experiments.

THE FINAL OBSERVER — a player need not mathematically infer the enemy; they can learn the *policy by feel*:
"my shots behave differently when the opponent is behind cover." That is `image ≠ generator` (M15) at the
gameplay layer. The player is a perceptual side-channel analyzer, and the last firewall is behavioral
indistinguishability: interaction outcomes must not vary in a way that teaches the generator.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures what observers learn through interaction; it
commits nothing and asserts no truth. privacy ≠ scalar; correction ≠ cause; image ≠ generator; integrity ≠ truth.

HONEST BOUND: the leakage axes, probe model, and behavioral "classifier" are declared proxies — not a learned
adversary, not a real player, not a real socket. The REAL channel here is intentionally unbuilt (it reports
unavailable): wiring it, and putting real humans in front of it, is the validity step. Real perceptual
learning is human and unmeasured; this is the SHAPE of the final observer, not its proof. simulation ≠ physics.
"""
from __future__ import annotations


# --- 1. Convergence Leakage Vector (privacy is not a scalar) ----------------------------------------

CLV_AXES = ("magnitude", "existence", "timing", "correlation", "aggregation")

# per-policy leakage on each axis (1.0 = fully leaks that axis, 0.0 = closed). Produced by the M18 harness:
# bucketing closes magnitude but not existence; NOTHING in M17/M18 ever addressed timing.
_CLV = {
    "exact":            {"magnitude": 1.0, "existence": 1.0, "timing": 1.0, "correlation": 1.0, "aggregation": 1.0},
    "bucketed":         {"magnitude": 0.4, "existence": 1.0, "timing": 1.0, "correlation": 1.0, "aggregation": 1.0},
    "floor":            {"magnitude": 0.4, "existence": 0.4, "timing": 1.0, "correlation": 0.6, "aggregation": 1.0},
    "timing_normalized": {"magnitude": 0.4, "existence": 0.4, "timing": 0.0, "correlation": 0.6, "aggregation": 0.4},
}


def clv(policy):
    """The Convergence Leakage Vector for a reconciliation policy — a per-axis profile, not a debt scalar."""
    return dict(_CLV[policy])


def clv_scalar(policy):
    """The (lossy) collapse to a single number — kept only to demonstrate why it must NOT be used alone."""
    return round(sum(_CLV[policy].values()), 3)


def axis_closed(policy, axis):
    return _CLV[policy][axis] == 0.0


# --- 2. adversarial probe control / counterfactual amplification ------------------------------------

def counterfactual_debt(correction_info_bits, probe_control):
    """A correction's danger = the bit it carries × the attacker's ability to choose the question."""
    return correction_info_bits * probe_control


def adversary_boundary_uncertainty(probes, controlled, span=100):
    """How well an observer can localize the server's hidden decision boundary. A PASSIVE client cannot choose
    its experiments and stays at full span; an adversary that CONTROLS inputs binary-searches the boundary,
    halving uncertainty per chosen probe → a query oracle over world perturbations."""
    if not controlled:
        return float(span)
    return span / (2 ** max(0, probes))


# --- 3. the experiment-layer seam (same API; simulated = regression, real = validity) ---------------

class ExperimentLayer:
    """One measurement API over two channels. The simulated channel is deterministic and replayable (the
    regression environment); the real channel (UDP/TCP/QUIC) is the validity environment. Crucially the
    simulator is NOT discarded when the socket lands — it remains the regression bed. (CORE truth / VIEW
    representation, for experiments.)"""

    def __init__(self, channel="simulated"):
        self.channel = channel
        self.replayable = (channel == "simulated")
        self.available = (channel == "simulated")   # the real socket is intentionally unbuilt here

    def measure(self, probes, controlled=True):
        """Identical signature for both channels — that sameness is the whole point of the seam."""
        if self.channel == "simulated":
            return {"available": True, "replayable": True,
                    "boundary_uncertainty": adversary_boundary_uncertainty(probes, controlled)}
        return {"available": False, "replayable": False,
                "note": "wire a real socket here — same API, this becomes the validity environment"}


# --- 4. the final observer: the player learns the policy by FEEL ------------------------------------

# does the interaction OUTCOME (hit-reg, recoil, audio, animation) vary with hidden state under this policy?
_BEHAVIOR_VARIES = {"naive": True, "constant_feel": False}


def behavioral_distinguishability(policy):
    """Can a player separate "opponent behind cover" from "in the open" purely from how the game FEELS? 0.5 =
    chance (indistinguishable); 1.0 = the feel teaches the policy. image ≠ generator, at the gameplay layer."""
    return 1.0 if _BEHAVIOR_VARIES[policy] else 0.5


def player_learns_policy(policy):
    return behavioral_distinguishability(policy) > 0.5


FEEL = {"hit_landed", "explosion_felt", "recoil", "audio_cue", "visible_motion"}
POLICY_TELLS = {"hitreg_forgiveness_threshold", "aim_assist_boundary", "rollback_threshold",
                "audio_occlusion_rule", "matchmaking_correction"}


def admissible_behavioral_disclosure(kind):
    """A player may experience the world (feel its consequences); they may not learn the generator (the policy
    thresholds) through interaction. The last `image ≠ generator`."""
    return (kind in FEEL) and (kind not in POLICY_TELLS)


# --- the behavioral crucible ------------------------------------------------------------------------

def crucible():
    out = {}
    # 1. CLV: privacy is a vector, not a scalar
    out["clv_exact"] = clv("exact")
    out["clv_bucketed"] = clv("bucketed")
    out["clv_floor"] = clv("floor")
    out["bucketing_closes_magnitude"] = clv("bucketed")["magnitude"] < clv("exact")["magnitude"]
    out["bucketing_keeps_existence"] = clv("bucketed")["existence"] == clv("exact")["existence"]
    # non-collapsibility: floor's scalar < bucketed's, yet the timing axis is IDENTICAL (a scalar would hide this)
    out["floor_scalar_lower"] = clv_scalar("floor") < clv_scalar("bucketed")
    out["timing_axis_untouched"] = clv("floor")["timing"] == clv("bucketed")["timing"] == 1.0
    out["only_timing_norm_closes_timing"] = axis_closed("timing_normalized", "timing") and not axis_closed("floor", "timing")
    # 2. counterfactual amplification
    out["passive_uncertainty"] = adversary_boundary_uncertainty(probes=14, controlled=False)
    out["probing_uncertainty"] = adversary_boundary_uncertainty(probes=14, controlled=True)
    out["debt_passive"] = counterfactual_debt(1, 1)
    out["debt_probing"] = counterfactual_debt(1, 10000)
    # 3. experiment-layer seam
    sim_a, sim_b = ExperimentLayer("simulated"), ExperimentLayer("simulated")
    out["sim_replayable"] = sim_a.measure(8) == sim_b.measure(8) and sim_a.replayable
    out["real_unavailable_same_api"] = (ExperimentLayer("real").measure(8)["available"] is False)
    # 4. the player as final observer
    out["naive_feel_learnable"] = player_learns_policy("naive")
    out["constant_feel_opaque"] = not player_learns_policy("constant_feel")
    out["feel_ok"] = admissible_behavioral_disclosure("recoil")
    out["policy_tell_blocked"] = not admissible_behavioral_disclosure("rollback_threshold")
    return out


def demo():
    r = crucible()
    print("Behavioral Reality Harness — the last observer is the player\n")
    print("  1. Convergence Leakage Vector (privacy is not a scalar):")
    for p in ("exact", "bucketed", "floor", "timing_normalized"):
        print("       %-17s %s  (scalar %.1f)" % (p, clv(p), clv_scalar(p)))
    print("     · bucketing closes magnitude but not existence: %s / %s"
          % (r["bucketing_closes_magnitude"], r["bucketing_keeps_existence"]))
    print("     · floor's scalar is lower yet the TIMING axis is untouched — a scalar would hide that: %s"
          % (r["floor_scalar_lower"] and r["timing_axis_untouched"]))
    print("  2. counterfactual amplification: passive uncertainty=%.0f vs probing=%.4f; debt 1 vs %d"
          % (r["passive_uncertainty"], r["probing_uncertainty"], r["debt_probing"]))
    print("  3. experiment seam: simulated replayable=%s; real channel same API, unavailable=%s"
          % (r["sim_replayable"], r["real_unavailable_same_api"]))
    print("  4. the player: naive feel is learnable=%s; constant-feel is opaque=%s; policy-tell blocked=%s"
          % (r["naive_feel_learnable"], r["constant_feel_opaque"], r["policy_tell_blocked"]))
    print("\n  a player may FEEL the world; they may not learn the generator by playing it.")
    print("  the last observer was never the renderer — it was always the player. simulation ≠ physics.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("behavioral_harness", OBSERVER, mutates_core=False,
                          note="Behavioral Reality Harness — Convergence Leakage Vector + counterfactual "
                               "amplification (adversarial probe control) + experiment-layer seam + the player "
                               "as the final observer (image≠generator at the gameplay layer)")
    except LayerViolation:
        pass
