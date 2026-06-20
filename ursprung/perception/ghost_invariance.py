# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/ghost_invariance.py — a ghost is not automatically a hidden truth.

The project's original ghost (`ghost_report.py`, M1) is the residual `G = Z − Π(Z)` — what exists minus what is
observable. The old framing treated that residual as *hidden information the observer failed to capture*. The
confounder slot (`confounder.py`) forces the harder question: is the ghost a **generator component**, or merely
a **projection artifact** — the shadow of the observer, an arbitrary remainder this particular `Π` happened to
drop?

The distinction is testable, and it is the DVSM↔perception merge in one bench. A ghost component is a real
hidden-generator candidate only if it is both:

  * **invariant** — it appears in the ghost under *every* projection (change `Π`; if the component leaves the
    ghost, it was a property of the projection, not of the generator), and
  * **necessary** — removing it *changes the behaviour* (`F`'s trajectory); a component you can delete with no
    effect on the dynamics is contingent, not generative.

So:  **Generator = invariant necessity.  Confounder = invariant-looking contingency.**  ("Arbitrary" does not
mean random — a lattice, a codebook, a learned policy all look arbitrary from outside; they are generative only
relative to the mechanism that needs them.)

Bench: `Z = (visible, g, a)` where the dynamics `F` advances the visible state by `g` and *ignores* `a`. Two
projections — `Π1` reveals only the visible state (ghost `= {g, a}`), `Π2` reveals visible + `a` (ghost
`= {g}`). The **invariant** ghost component (`g`, in both ghosts) survives the projection change and is
necessary → generator. The **variant** component (`a`, in `Π1`'s ghost but not `Π2`'s) is a projection artifact
and is removable with no behavioural effect → confounder. The old conclusion "the ghost contains hidden
information" was half right: part of it is the generator, part of it is just the observer's shadow.

(And L7's hash binding proves only that the state did not change unexpectedly, never that it is the *true*
state — a perfectly hashed confounder is still a confounder: `integrity ≠ truth`.)

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: a toy with a clean separable state; real residual
attribution (which part of an EM/timing/quantization residue is generator vs projection artifact) needs varied
projections and interventions, and is open. ghost ≠ hidden truth; mechanism ≠ correlation; integrity ≠ truth.
"""
from __future__ import annotations

N = 8
Z0 = {"visible": 1, "g": 2, "a": 5}     # g = generator-intrinsic; a = arbitrary (the dynamics ignores it)


def F_step(z):
    """The generator's dynamics: the visible state advances by g; a is never used (so a is not necessary)."""
    return {"visible": (z["visible"] + z["g"]) % N, "g": z["g"], "a": z["a"]}


def trajectory(z, horizon=6):
    z = dict(z)
    out = []
    for _ in range(horizon):
        out.append(z["visible"])
        z = F_step(z)
    return out


# two projections (observation boundaries) revealing different parts of Z
PROJECTIONS = {
    "P1": lambda z: {"visible": z["visible"]},                 # reveals only the visible state
    "P2": lambda z: {"visible": z["visible"], "a": z["a"]},     # also reveals the arbitrary component a
}


def ghost(projection):
    """The ghost under a projection: the components of Z that this Π does NOT reveal (G = Z − Π(Z))."""
    return set(Z0) - set(PROJECTIONS[projection](Z0))


def removing_changes_behavior(component, new_value):
    """Necessity test: does altering this component change the F trajectory? (Is it generative, or contingent?)"""
    z = dict(Z0)
    z[component] = new_value
    return trajectory(z) != trajectory(Z0)


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    g1, g2 = ghost("P1"), ghost("P2")
    invariant = g1 & g2                # ghost components present under every projection
    variant = g1 ^ g2                  # ghost components whose presence depends on the projection
    out["ghost_P1"] = sorted(g1)
    out["ghost_P2"] = sorted(g2)
    out["invariant_ghost"] = sorted(invariant)
    out["variant_ghost"] = sorted(variant)
    # the ghost contains more than the generator
    out["ghost_has_nongenerator"] = "a" in g1
    # the invariant ghost component is the generator candidate; the variant is a projection artifact
    out["invariant_ghost_is_generator"] = invariant == {"g"}
    out["variant_is_projection_artifact"] = "a" in variant
    # necessity: g is necessary (removing it changes behaviour); a is contingent (no effect)
    out["g_necessary"] = removing_changes_behavior("g", 3)
    out["a_contingent"] = not removing_changes_behavior("a", 0)
    # Generator = invariant necessity; Confounder = invariant-looking contingency
    out["generator_invariant_and_necessary"] = ("g" in invariant) and removing_changes_behavior("g", 3)
    out["artifact_neither_necessary_nor_invariant"] = ("a" in variant) and not removing_changes_behavior("a", 0)
    return out


def demo():
    r = crucible()
    print("Ghost invariance — a ghost is not automatically a hidden truth (it may be the observer's shadow)\n")
    print("  ghost = Z − Π(Z) (what exists minus what's observable).  test each ghost component two ways:")
    print("  (1) invariant under a change of projection?   (2) necessary — removing it changes behaviour?\n")
    print("  ghost under P1 (reveals visible):        %s" % r["ghost_P1"])
    print("  ghost under P2 (reveals visible + a):    %s" % r["ghost_P2"])
    print("  invariant ghost (in both): %s   variant ghost (Π-dependent): %s"
          % (r["invariant_ghost"], r["variant_ghost"]))
    print()
    print("  · 'g' is in every projection's ghost AND necessary (removing it changes F): generator. %s / %s"
          % (r["invariant_ghost_is_generator"], r["g_necessary"]))
    print("  · 'a' is in P1's ghost but not P2's, and removing it changes nothing: a projection artifact. %s / %s"
          % (r["variant_is_projection_artifact"], r["a_contingent"]))
    print("\n  Generator = invariant necessity. Confounder = invariant-looking contingency.")
    print("  part of the ghost is the generator; part is the observer's shadow. ghost ≠ hidden truth; integrity ≠ truth.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.ghost_invariance", OBSERVER, mutates_core=False,
                          note="a ghost (G = Z − Π(Z)) is not automatically hidden truth: an invariant ghost "
                               "component (in every projection's ghost) that is necessary (removing it changes F) "
                               "is the generator; a variant component (Π-dependent, removable) is a projection "
                               "artifact — the observer's shadow. generator = invariant necessity; ghost ≠ hidden truth")
    except LayerViolation:
        pass
