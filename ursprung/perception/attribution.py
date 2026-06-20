# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/attribution.py — the missing layer: the ghost is a candidate set, not a truth.

The old DVSM ghost `G = Z − Π(Z)` carried a hidden assumption: *whatever survives outside the observer's
projection is hidden structure.* `ghost_invariance.py` showed that is too strong. This module names the
corrected object: the ghost decomposes,

    G = G_F + G_C            (generator residue  +  confounder / projection residue)

and the split cannot come from the residual itself — it comes from **tests against the other operators**. The
ghost is therefore not a place where mystery is stored; it is a **search space for attribution**. The missing
layer of the old 7-stage pipeline was never another stabilizer — it was *attribution* (call it `V`).

Two tests, and crucially **both are required**:

  1. **Projection invariance** — change the observer (`Π1 → Π2 → Π3`). A component that stays ghosted under
     *every* projection is independent of any one view; one that leaves the ghost under some `Π` was never
     hidden, only hidden *from that observer* (a projection artifact).
  2. **Necessity** — invariance is *not enough*: a repeated pattern can be a stable artifact. So intervene —
     remove the component and run `F`. If the trajectory changes, it participates in the generator; if not, it
     was descriptive, not causal.

    G_F = { x ∈ ghost : invariant across all Π  AND  necessary to F }
    G_C = ghost \ G_F

The decisive case this bench adds over `ghost_invariance`: a component `b` that is **invariant across every
projection but not necessary** — a *stable artifact*. Invariance alone would wrongly attribute it to the
generator; the necessity test correctly assigns it to `G_C`. Hence `stable ≠ causal`, and **invariance ∧
necessity** (not either alone) is the attribution rule.

A note on the hash layer (old L7): `Hash(Z)` binds *same state → same hash* — `integrity = reproducibility`.
It does **not** bind *correct state → truth*: a perfectly replayable system can replay the wrong explanation,
and the hash says nothing about which components are `G_F` vs `G_C`. `integrity = reproducibility ≠ causal
validity`. So the hash moves *conceptually downward*: the old 7-stage stack (…spectral → memory → hash) becomes
a 9-stage attribution stack — `… L7 Projection (Π) · L8 Attribution (separate G_F from G_C) · L9 Integrity
(hash / replay binding)`. Attribution comes *before* the hash, because the hash certifies the identity of a
trajectory, not the correctness of its explanation; integrity binds what attribution decided, it does not
decide it.

This module also keeps two questions deliberately separate (see `attribute()`): Q1 *was it ever hidden?*
(membership in `ghost_candidates`) and Q2 *was it causal?* (membership in `causal_candidates` = G_F). The `b`
component answers yes to Q1 and no to Q2 — the divergence that the old `G ≈ hidden mechanism` framing erased.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy separable state and discrete projections; real
attribution (which part of an EM/timing/quantization residue is generator vs artifact) needs many projections,
interventions, and is open and data-hungry. The ghost is a candidate set, not a truth. stable ≠ causal;
ghost ≠ hidden truth; integrity ≠ truth.
"""
from __future__ import annotations

import hashlib

N = 8
# g = generator-intrinsic; a = projection-relative artifact; b = STABLE artifact (invariant across Π, yet not
# necessary to the dynamics). v = visible.
Z = {"visible": 1, "g": 2, "a": 5, "b": 7}


def F_step(z):
    """Dynamics: the visible state advances by g; a and b are never used (so neither is necessary)."""
    return {"visible": (z["visible"] + z["g"]) % N, "g": z["g"], "a": z["a"], "b": z["b"]}


def trajectory(z, horizon=6):
    z = dict(z)
    out = []
    for _ in range(horizon):
        out.append(z["visible"])
        z = F_step(z)
    return out


# three observation maps; `a` is revealed by Π2 (so it leaves Π2's ghost → variant), g and b never revealed
PROJECTIONS = {
    "P1": lambda z: {"visible": z["visible"]},
    "P2": lambda z: {"visible": z["visible"], "a": z["a"]},
    "P3": lambda z: {"visible": z["visible"]},
}


def ghost(projection):
    return set(Z) - set(PROJECTIONS[projection](Z))


def is_necessary(component):
    """Intervention: alter the component and run F; necessary iff the trajectory changes."""
    z = dict(Z)
    z[component] = (z[component] + 1) % N
    return trajectory(z) != trajectory(Z)


def attribute():
    """Decompose the ghost into G_F (invariant ∧ necessary) and G_C (the rest) — the attribution operator V.

    Two questions, kept deliberately separate (this is the architecture's point):
      Q1 — was it EVER HIDDEN?   → membership in `ghost_candidates` (the union of every projection's ghost).
      Q2 — was it CAUSAL?         → membership in `causal_candidates` = G_F (invariant across Π ∧ necessary to F).
    A component can answer yes to Q1 and no to Q2 (the `b` case): ever hidden, never causal. Conflating the two
    is the mistake the old `G ≈ hidden mechanism` framing made.
    """
    ghosts = [ghost(p) for p in PROJECTIONS]
    invariant = set.intersection(*ghosts)            # hidden under EVERY projection (necessary for Q2, not sufficient)
    ghost_candidates = set.union(*ghosts)            # Q1: ever hidden under SOME projection
    necessary = {x for x in ghost_candidates if is_necessary(x)}     # intervention test (necessary for Q2)
    causal_candidates = {x for x in ghost_candidates if x in invariant and x in necessary}   # Q2: G_F = both
    g_f = causal_candidates
    g_c = ghost_candidates - g_f
    return {"ghost_candidates": ghost_candidates, "invariant": invariant, "necessary": necessary,
            "causal_candidates": causal_candidates, "G_F": g_f, "G_C": g_c}


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    r = attribute()
    out = {"G_F": sorted(r["G_F"]), "G_C": sorted(r["G_C"]),
           "invariant": sorted(r["invariant"]), "ghost_candidates": sorted(r["ghost_candidates"])}
    # the ghost is a candidate set, not a truth
    out["ghost_is_candidate_set"] = len(ghost("P1")) == 3
    # the decomposition partitions the candidates: G_F ⊔ G_C
    out["decomposition_partitions"] = (r["G_F"] | r["G_C"]) == r["ghost_candidates"] and not (r["G_F"] & r["G_C"])
    out["G_F_is_generator_only"] = r["G_F"] == {"g"}
    # the decisive case: a component invariant across EVERY projection but NOT necessary → G_C (stable artifact)
    out["stable_artifact_is_invariant"] = "b" in r["invariant"]
    out["stable_artifact_attributed_to_GC"] = "b" in r["G_C"]
    out["invariance_alone_overattributes"] = r["invariant"] > r["G_F"]    # {g,b} ⊋ {g}
    # the two questions are distinct: b is a GHOST candidate (ever hidden) but NOT a CAUSAL candidate (in G_F)
    out["ever_hidden_is_not_causal"] = "b" in r["ghost_candidates"] and "b" not in r["causal_candidates"]
    # both tests are required: G_F is the intersection of invariant and necessary, neither alone
    out["both_tests_required"] = r["G_F"] == (r["invariant"] & r["necessary"]) and r["invariant"] != r["G_F"]
    # the projection-relative artifact is the variant component
    out["projection_artifact_is_variant"] = "a" not in r["invariant"] and "a" in r["G_C"]
    # the hash binds reproducibility, not causal validity (it cannot tell G_F from G_C)
    h1 = hashlib.sha256(repr(sorted(Z.items())).encode()).hexdigest()
    h2 = hashlib.sha256(repr(sorted(Z.items())).encode()).hexdigest()
    out["integrity_is_reproducibility_not_validity"] = (h1 == h2)
    return out


def demo():
    r = crucible()
    print("Attribution — the ghost is a candidate set, not a truth (G = G_F + G_C)\n")
    print("  the residual G = Z − Π(Z) decomposes into generator residue (G_F) and confounder residue (G_C);")
    print("  the split comes from tests against the other operators, not from the residual itself.\n")
    print("  Q1 was it ever hidden?  ghost candidates: %s" % r["ghost_candidates"])
    print("  Q2 was it causal?       invariant across all Π: %s  →  G_F (invariant ∧ necessary)" % r["invariant"])
    print("  G_F (generator): %s     G_C (confounder/artifact): %s" % (r["G_F"], r["G_C"]))
    print()
    print("  · 'b' answers Q1 YES (ever hidden) but Q2 NO (not causal): %s — the two questions diverge"
          % r["ever_hidden_is_not_causal"])
    print("  · 'b' is invariant across EVERY projection but NOT necessary → a STABLE ARTIFACT, assigned to G_C: %s / %s"
          % (r["stable_artifact_is_invariant"], r["stable_artifact_attributed_to_GC"]))
    print("  · so invariance ALONE over-attributes (it would keep b): %s — both tests are required: %s"
          % (r["invariance_alone_overattributes"], r["both_tests_required"]))
    print("  · 'a' is projection-relative (leaves the ghost under Π2) → variant artifact in G_C: %s"
          % r["projection_artifact_is_variant"])
    print("  · the hash is reproducible but cannot tell G_F from G_C: integrity = reproducibility ≠ causal validity.")
    print("\n  the missing layer was never another stabilizer — it was ATTRIBUTION. stable ≠ causal; ghost ≠ hidden truth.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.attribution", OBSERVER, mutates_core=False,
                          note="the attribution operator V: the ghost is a candidate set (G = G_F + G_C); split "
                               "it by invariance across Π AND necessity to F. invariance ALONE over-attributes "
                               "(a stable artifact b is invariant but not necessary → G_C). both tests required; "
                               "integrity = reproducibility ≠ causal validity. stable ≠ causal; ghost ≠ hidden truth")
    except LayerViolation:
        pass
