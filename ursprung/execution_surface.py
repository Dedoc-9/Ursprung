# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/execution_surface.py — Execution Surface Privacy (M16): observable cost ≠ hidden state.

M15 hid the *function* (image ≠ generator). But a representation system is also a PHYSICAL PROCESS, and the
process is observable. The attacker stops asking "what is hidden?" or even "what does the renderer reveal?"
and asks the only question left: **"what does the renderer STRUGGLE with?"** A 6 ms hitch when an enemy
streams in, a cache miss, a memory bump — none of it discloses a world fact, yet all of it classifies the
hidden state. This is the boundary condition the stack has been converging on: you can protect information
flow, but you cannot make execution costless or invisible.

The invariant: **observable cost ≠ hidden state**; more strongly, **runtime behavior must not become a
classifier**. This is precisely where M6 (shader cache / transition debt) and M15 (privacy) fuse — the
"industrial bridge" was never a side quest; it is the *physical implementation layer* of the security model.

Five mechanisms, each with a negative control:

  1. TRANSITION SIGNATURE DEBT — Transition Debt (M5/M6) applied to OBSERVATION: Signature = Δ(latency,
     cache, memory, bandwidth, shader_state). A hidden object must not produce a unique signature. Streaming
     an animation on demand spikes 6 ms when the enemy nears (leak); a pre-prepared representation does not.
  2. CACHE SIDE-CHANNEL BUDGET — a cache hit/miss is a message. Cache Exposure = the difference between what
     gets prepared when the secret is present vs absent. The fix is not "don't prepare"; it is "prepare by an
     allowed readiness policy, not by hidden-state visibility" — the `importance ≠ exposure` rule, again.
  3. SEMANTIC CONSTANT-TIME — not literally constant CPU time, but: world A (hidden enemy exists) and world B
     (it does not) must not be separable by a classifier watching representation behavior. The right
     measurement is a world-indistinguishability test, not a cryptographic proof.
  4. THREE-CURRENCY OBJECTIVE — the safest renderer may do work that looks wasteful, because *unused*
     preparation is cheaper than an *observable* preparation event. The objective stops being "minimize GPU
     work" and becomes minimize(fidelity_debt + transition_debt + information_leakage).
  5. RENDERER ≠ ORACLE — a client may observe the world; it may not observe the machinery by which hidden
     world state becomes observable. That is the line between a renderer and an oracle.

CLASSIFICATION: OBSERVER (mutates_core=False). It shapes the *cost profile* of presentation; it never mutates
the Weltlinie. observable cost ≠ hidden state; renderer ≠ oracle; integrity ≠ truth.

HONEST BOUND: declared cost-vector and separability proxies, NOT a measured micro-architectural side channel
against a real profiler. The world-indistinguishability "classifier" is a separability check, not a learned
adversary. On real silicon, leakage is continuous (cache lines, DVFS, memory-bus contention) and these
integer signatures collapse to noise — this is the SHAPE of the defense, and the precise place every
constructed number expires against real telemetry. integrity ≠ truth.
"""
from __future__ import annotations


# --- 1. Transition Signature Debt -------------------------------------------------------------------

COST_AXES = ("latency", "cache", "memory", "bandwidth", "shader_state")


def execution_signature(hidden_present, mode):
    """The observable cost vector the renderer emits for a frame, given whether the hidden object is present.
    on_demand: streams the representation when the secret nears → a unique spike (the signature IS the leak).
    prepared:  the representation is already resident → the same baseline whether or not the secret is present."""
    if mode == "on_demand":
        spike = 1 if hidden_present else 0
        return (6 * spike, 1 * spike, 2 * spike, 3 * spike, 1 * spike)
    if mode == "prepared":
        return (3, 1, 2, 3, 1)          # over-prepared constant baseline, independent of the secret
    raise ValueError("mode must be on_demand|prepared")


def transition_signature_debt(mode):
    """The magnitude of the cost signature that CORRELATES with the hidden state (|sig(present) − sig(absent)|).
    0 ⇒ runtime behavior reveals nothing about whether the secret is present."""
    present = execution_signature(True, mode)
    absent = execution_signature(False, mode)
    return sum(abs(p - a) for p, a in zip(present, absent))


# --- 2. Cache Side-Channel Budget -------------------------------------------------------------------

def cache_exposure(prepared_when_present, prepared_when_absent):
    """A hit/miss is a message: what an observer learns from WHICH decisions were prepared. Exposure = the
    symmetric difference of the prepared sets across secret-present vs secret-absent. 0 ⇒ readiness policy is
    independent of the secret (prepared by allowed policy, not by hidden-state visibility)."""
    return len(set(prepared_when_present) ^ set(prepared_when_absent))


# --- 3. semantic constant-time (world indistinguishability) -----------------------------------------

def world_separable(mode):
    """Can an observer separate world A (hidden enemy exists) from world B (it does not) by watching
    representation behavior? True ⇒ runtime behavior is a classifier (a leak)."""
    return execution_signature(True, mode) != execution_signature(False, mode)


def classifier_accuracy(mode):
    """Separability proxy: 1.0 if the two worlds are perfectly distinguishable from behavior, else chance 0.5.
    (A separability check, NOT a learned adversary — see HONEST BOUND.)"""
    return 1.0 if world_separable(mode) else 0.5


# --- 4. three-currency objective (the optimization target changes) ----------------------------------

PLANS = {
    # the cheapest GPU plan leaks (its execution spikes); the over-prepared plan costs more work but leaks 0.
    "min_gpu":       {"fidelity_debt": 2, "transition_debt": 2, "leakage": 10},
    "over_prepared": {"fidelity_debt": 1, "transition_debt": 6, "leakage": 0},
}


def total_cost(plan, leak_weight=1):
    """minimize(fidelity_debt + transition_debt + leak_weight·information_leakage). leak_weight=0 recovers the
    OLD objective (pure GPU minimization); leak_weight≥1 is the new three-currency objective."""
    p = PLANS[plan] if isinstance(plan, str) else plan
    return p["fidelity_debt"] + p["transition_debt"] + leak_weight * p["leakage"]


def cheapest_plan(leak_weight=1):
    return min(PLANS, key=lambda name: total_cost(name, leak_weight))


# --- 5. renderer ≠ oracle (the final invariant) -----------------------------------------------------

WORLD_OBSERVABLES = {"explosion", "damage", "door_opened", "visible_motion", "sound"}
MACHINERY = {"cache_hit_implies_prepared", "latency_spike_implies_stream", "mem_growth_implies_entity",
             "bandwidth_burst_implies_asset_load"}


def is_oracle_observation(kind):
    """An observation crosses from renderer to ORACLE if it exposes the machinery by which hidden world state
    becomes observable (a cost/cache/timing tell), rather than a world fact."""
    return kind in MACHINERY


def admissible_execution_observation(kind):
    """A client may observe the world; it may not observe the machinery. renderer ≠ oracle."""
    return (kind in WORLD_OBSERVABLES) and not is_oracle_observation(kind)


# --- the execution-surface crucible -----------------------------------------------------------------

def crucible():
    out = {}
    # 1. transition signature: on-demand streaming spikes for the secret; pre-preparation does not
    out["signature_on_demand"] = transition_signature_debt("on_demand")
    out["signature_prepared"] = transition_signature_debt("prepared")
    # 2. cache exposure: prepare enemy assets only when near (leak) vs a fixed policy set (no leak)
    out["cache_exposure_naive"] = cache_exposure(["enemy_anim", "common"], ["common"])
    out["cache_exposure_policy"] = cache_exposure(["common", "enemy_anim"], ["common", "enemy_anim"])
    # 3. world indistinguishability
    out["separable_on_demand"] = world_separable("on_demand")
    out["separable_prepared"] = world_separable("prepared")
    out["accuracy_on_demand"] = classifier_accuracy("on_demand")
    out["accuracy_prepared"] = classifier_accuracy("prepared")
    # 4. three currencies: the objective flip changes the winner over the SAME two plans
    out["new_objective_winner"] = cheapest_plan(leak_weight=1)     # leakage counted → over_prepared
    out["old_objective_winner"] = cheapest_plan(leak_weight=0)     # GPU only → min_gpu
    out["over_prepared_total_new"] = total_cost("over_prepared", 1)
    out["min_gpu_total_new"] = total_cost("min_gpu", 1)
    # 5. renderer ≠ oracle
    out["world_observation_ok"] = admissible_execution_observation("explosion")
    out["machinery_blocked"] = not admissible_execution_observation("latency_spike_implies_stream")
    return out


def demo():
    r = crucible()
    print("Execution Surface Privacy — observable cost ≠ hidden state\n")
    print("  1. transition signature: on-demand streaming debt=%d (a unique spike) vs pre-prepared=%d"
          % (r["signature_on_demand"], r["signature_prepared"]))
    print("  2. cache exposure: prepare-on-visibility=%d (hit/miss is a message) vs fixed policy=%d"
          % (r["cache_exposure_naive"], r["cache_exposure_policy"]))
    print("  3. world indistinguishability: on-demand separable=%s (acc %.1f) vs prepared separable=%s (acc %.1f)"
          % (r["separable_on_demand"], r["accuracy_on_demand"], r["separable_prepared"], r["accuracy_prepared"]))
    print("  4. three currencies: new objective picks '%s' (%d ≤ %d); old GPU-only objective picks '%s'"
          % (r["new_objective_winner"], r["over_prepared_total_new"], r["min_gpu_total_new"],
             r["old_objective_winner"]))
    print("  5. renderer ≠ oracle: world observation ok=%s; machinery (timing tell) blocked=%s"
          % (r["world_observation_ok"], r["machinery_blocked"]))
    print("\n  unused preparation can be cheaper than an OBSERVABLE preparation event; the safest renderer")
    print("  sometimes does 'wasteful' work. observable cost ≠ hidden state; renderer ≠ oracle; integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("execution_surface", OBSERVER, mutates_core=False,
                          note="Execution Surface Privacy — transition signature debt + cache side-channel "
                               "budget + semantic constant-time + three-currency objective + renderer≠oracle")
    except LayerViolation:
        pass
