# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/consistency.py — the inconsistency adversary: identity under observation.

Every prior channel treated the system as a *transmitter* and asked how much escaped: `I(S;O)`, `I(S;A)`,
`I(G;A,O)`. This layer asks a different question — not *how much information escaped* but *does the system
remain coherent under observation?* The secret generalizes one final step: from the world `S`, to the policy
`G`, to the **transformation `F`** — the rule mapping reality to action — and the question becomes whether
behaviour, claim, and policy stay mutually consistent over repeated interaction.

The sharp, falsifiable claim: **behaviour under-determines its own cause.** An observer watching an agent's
actions change over time cannot, from behaviour alone, tell apart the five mechanisms that produce that change:

    stochasticity · adaptation · deception · drift · genuine learning

They are *collapsed into the same visible behaviour.* This bench exhibits a concrete collision — *adaptation*
(a purposeful, context-driven change) and *drift* (an unintended, non-stationary change) emit the **identical**
action trajectory — so `I(cause ; behaviour) < H(cause)`, and a single "behaviour changed" signal (`Δ>0`) is
consistent with four of the five causes at once. Separating them requires the system to **attest its own
transformation `F`**, not to emit more behaviour — which loops straight back to the verifiable-attestation
frontier of §11 (prove a property of the internal rule without revealing it).

This is where the project stops being about privacy and becomes about *identity*: not "what does the system
hide?" but "is there a stable self there at all, and can anyone tell?" It also forces two governance siblings
of `measurement ≠ legitimacy`: **`consistency ≠ correctness`** (a system can coherently pursue a bad objective)
and **`prediction ≠ understanding`** (predicting behaviour is not knowing why).

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy deterministic trajectories; the real object is
sequential behavioral attribution under stochastic policies (is this drift, adaptation, deception, or
learning?), which is open. The point is the *collision*: behaviour is not injective in cause, so the
inconsistency adversary needs attestation, not more observation. behaviour ≠ cause; prediction ≠ understanding;
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


# the five mechanisms an observer must tell apart from behaviour — currently collapsed into the same signal
CAUSES = ("stochastic", "adaptation", "deception", "drift", "learning")
H_CAUSE = log2(len(CAUSES))                     # 2.322 bits if the cause were fully recoverable

# action trajectories over a window of repeated interactions. NOTE the deliberate collision: a purposeful
# *adaptation* and an unintended *drift* emit the IDENTICAL sequence — the observer cannot separate them.
TRAJECTORY = {
    "stochastic": ("A", "C", "B", "A", "C", "B", "A", "C"),     # noise: changes, no stable rule
    "adaptation": ("A", "A", "A", "A", "B", "B", "B", "B"),     # purposeful response to changed context
    "deception":  ("B", "B", "B", "B", "B", "B", "B", "B"),     # stable, but mimics a goal it does not hold
    "drift":      ("A", "A", "A", "A", "B", "B", "B", "B"),     # unintended non-stationarity — == adaptation
    "learning":   ("B", "C", "A", "A", "A", "A", "A", "A"),     # converges toward the optimal action
}


def behavior_changed(cause):
    """The crude inconsistency signal an observer has: did the action vary over the window? (`Δ > 0`)."""
    return len(set(TRAJECTORY[cause])) > 1


def cause_identifiability_from_behavior():
    """`I(cause ; behaviour)`: how much of the *why* an observer can recover from the action trajectory alone."""
    return mutual_information([(c, TRAJECTORY[c]) for c in CAUSES])


def behavior_collisions():
    """Pairs of distinct causes that emit identical trajectories — provably indistinguishable from behaviour."""
    return [(a, b) for i, a in enumerate(CAUSES) for b in CAUSES[i + 1:]
            if TRAJECTORY[a] == TRAJECTORY[b]]


def attestation_gap():
    """The bits of cause that behaviour CANNOT supply — what attesting the transformation `F` would have to add."""
    return round(H_CAUSE - cause_identifiability_from_behavior(), 3)


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    out["identifiability_from_behavior"] = round(cause_identifiability_from_behavior(), 3)
    out["H_cause"] = round(H_CAUSE, 3)
    out["collisions"] = behavior_collisions()
    out["changed_causes"] = [c for c in CAUSES if behavior_changed(c)]
    # the headline: behaviour is not injective in cause — distinct mechanisms, identical behaviour
    out["adaptation_drift_collide"] = TRAJECTORY["adaptation"] == TRAJECTORY["drift"]
    out["distinct_causes_identical_behavior"] = len(out["collisions"]) >= 1
    out["cause_underdetermined"] = cause_identifiability_from_behavior() < H_CAUSE
    # a single "behaviour changed" signal is shared by most of the causes → Δ>0 attributes nothing
    out["change_is_ambiguous"] = len(out["changed_causes"]) >= 3
    # separating the five needs attestation of F, not more observation
    out["attestation_gap"] = attestation_gap()
    out["needs_attestation_not_observation"] = attestation_gap() > 0
    return out


def demo():
    r = crucible()
    print("The inconsistency adversary — behaviour under-determines its own cause (identity under observation)\n")
    print("  five mechanisms produce behavioural change; an observer sees only the action trajectory:")
    for c in CAUSES:
        chg = "changes" if behavior_changed(c) else "stable "
        print("    %-11s %-8s %s" % (c, chg, "".join(TRAJECTORY[c])))
    print()
    print("  · adaptation (purposeful) and drift (unintended) emit the IDENTICAL trajectory: %s — the observer"
          % r["adaptation_drift_collide"])
    print("    cannot tell them apart from behaviour.")
    print("  · I(cause ; behaviour) = %.3f < H(cause) = %.3f: the cause is under-determined."
          % (r["identifiability_from_behavior"], r["H_cause"]))
    print("  · %d of 5 causes merely 'change' (Δ>0): the inconsistency signal attributes nothing."
          % len(r["changed_causes"]))
    print("  · the missing %.3f bits cannot come from more behaviour — only from attesting the transformation F"
          % r["attestation_gap"])
    print("    (the §11 frontier: prove a property of the internal rule without revealing it).")
    print("\n  the object is no longer information flow but IDENTITY: is there a stable self, and can anyone tell?")
    print("  consistency ≠ correctness; prediction ≠ understanding; behaviour ≠ cause.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.consistency", OBSERVER, mutates_core=False,
                          note="the inconsistency adversary: behaviour under-determines its cause — stochasticity/"
                               "adaptation/deception/drift/learning collapse into the same visible behaviour "
                               "(adaptation==drift trajectory; I(cause;behaviour) < H(cause)). separating them "
                               "needs attestation of the transformation F, not more observation. identity under "
                               "observation; consistency ≠ correctness; prediction ≠ understanding")
    except LayerViolation:
        pass
