# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/model_relativity.py — necessity is model-relative; the generator survives the model class.

`attribution.py` separated *hidden* from *causal*: a component is in `G_F` only if it is invariant across
projections AND **necessary** to the dynamics `F`. But that test smuggled in an assumption — it took a single,
fixed `F`. The necessity verdict depends on *which* `F` you intervene on:

    G_F(F_model_1)  ≠  G_F(F_model_2)

A component can look necessary under a restricted model and become irrelevant under a richer one that explains
the same observed trajectory differently. So the attribution layer has a deeper failure mode of exactly the
kind it was built to catch: it separates *hidden* from *causal*, but it does not yet separate **causal under
this model** from **causal invariant across models**. This module applies the same invariance principle one
layer down — to the *causal test itself*.

    robust generator  =  ⋂ over admissible models F  of  G_F(F)

This is the `A_C` loop made concrete: the model class is an adversary/observer-class choice (which dynamics are
admitted), and "necessary" is only as trustworthy as the class it quantifies over. A single model cannot tell a
generator from a model-relative artifact; a *class* of models that all fit the data can.

The bench: a world advances `visible` by `g + c`, with `g` and `c` constant, producing an OBSERVED trajectory.
Two models both *reproduce* it (both admissible) but factor it differently:
  - `F1` (restricted): treats `c` as a live causal input. Intervene on `c` → its prediction changes → `c`
    reads as **necessary**.
  - `F2` (richer): has recognized the `c` contribution is a constant offset `K`, folded into a parameter; it
    never reads the state variable `c`. Intervene on `c` → prediction unchanged → `c` reads as **not
    necessary**.
So `G_F(F1) = {g, c}`, `G_F(F2) = {g}`, and the robust generator `⋂ = {g}`. `c` was *causal under a model, not
causal across models* — a model-relative artifact that the single-model necessity test would have promoted.
`g` is necessary under both → it survives the model class.

The knife edge (`knife_edge()`): `⋂ G_F(F)` is only as good as the admissible class `𝓕` you chose. Add a third,
over-rich model `F3` (autoregressive on the observable alone — reads neither latent, yet fits) and the robust
set collapses monotonically: `{g,c}` (𝓕 too narrow → the confounder survives) ⊋ `{g}` (well-chosen) ⊋ `{}` (𝓕
too broad → the generator is *erased*). The failure modes are symmetric — under-modeling lets confounders
survive, over-modeling makes every mechanism optional — so `causal-across-chosen-𝓕 ≠ causal-across-all-possible-F`.

THE BOUNDARY (where this lands, and deliberately NOT another module): there is **no purely internal
certificate**. A system can prove a residue is stable, necessary under a model, and survives an observer class,
but the final question — *why is THIS the right space of models `𝓕` to quantify over?* — is epistemology, not a
pipeline layer. Specifying the rules for `𝓕` without smuggling the answer in is the open hard problem, the same
boundary where scientific explanation, causal discovery, and formal verification meet. The successor object is
not a generator-finder but **an attribution system with an explicit uncertainty boundary around its admissible
explanation space**. The "all possible F" limit is already visible here: it collapses to ∅. The separator needs
its own separator.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy — hand-written admissible models, discrete
state, "richer/restricted" is illustrative (the load-bearing claim is only that necessity is model-relative,
not which model is better). The real version is open and hard: enumerating or learning the admissible model
class `𝓕`, and the fact that `⋂ over models` can shrink the recovered generator toward nothing as the class
grows richer. Separators: causal-under-a-model ≠ causal-across-models; causal-across-chosen-𝓕 ≠
causal-across-all-possible-F; necessity is model-relative; stable ≠ causal.
"""
from __future__ import annotations

N = 8
HORIZON = 6
# the world: visible advances by (g + c); g and c are constant. c is the component whose causal status is
# model-relative; g is the genuine generator.
Z = {"visible": 2, "g": 3, "c": 4}
CANDIDATES = ["g", "c"]


def observed_trajectory(z=None, horizon=HORIZON):
    """The ground-truth observed sequence the models must reproduce."""
    z = dict(Z if z is None else z)
    out = []
    for _ in range(horizon):
        out.append(z["visible"])
        z = {**z, "visible": (z["visible"] + z["g"] + z["c"]) % N}
    return out


OBSERVED = observed_trajectory()
_K = Z["c"]  # the constant offset the richer model F2 has absorbed as a parameter (not a live state variable)


def F1_restricted(z, horizon=HORIZON):
    """Naive model: treats c as a live causal input (reads the state variable c every step)."""
    z = dict(z)
    out = []
    for _ in range(horizon):
        out.append(z["visible"])
        z = {**z, "visible": (z["visible"] + z["g"] + z["c"]) % N}
    return out


def F2_richer(z, horizon=HORIZON):
    """Richer model: the c-contribution is a constant offset K; c is not a variable of this model."""
    z = dict(z)
    out = []
    for _ in range(horizon):
        out.append(z["visible"])
        z = {**z, "visible": (z["visible"] + z["g"] + _K) % N}
    return out


_DELTA = (Z["g"] + Z["c"]) % N  # the per-step advance, seen purely on the observable


def F3_overrich(z, horizon=HORIZON):
    """Over-rich model: autoregressive on the OBSERVABLE alone — reads neither g nor c. It fits the data by
    advancing `visible` by the observed per-step delta, so BOTH latents look redundant under it. This is the
    other blade of the knife edge: a class rich enough to model the observable directly absorbs the generator."""
    z = dict(z)
    out = []
    for _ in range(horizon):
        out.append(z["visible"])
        z = {**z, "visible": (z["visible"] + _DELTA) % N}
    return out


MODELS = {"F1_restricted": F1_restricted, "F2_richer": F2_richer}


def fits(model):
    """A model is admissible only if it reproduces the observed trajectory — necessity is meaningless otherwise."""
    return model(Z) == OBSERVED


def necessary_under(model, component):
    """Intervention relative to a model: perturb the component, run THAT model, compare trajectories."""
    z = dict(Z)
    z[component] = (z[component] + 1) % N
    return model(z) != model(Z)


def G_F(model_name):
    """The generator set as judged by ONE model: components necessary under that (admissible) model."""
    model = MODELS[model_name]
    if not fits(model):
        return set()
    return {c for c in CANDIDATES if necessary_under(model, c)}


def robust_generator():
    """What stays necessary across the whole admissible model class — the model-invariant generator."""
    admissible = [G_F(name) for name in MODELS if fits(MODELS[name])]
    return set.intersection(*admissible) if admissible else set()


# --- the knife edge: the intersection is only as good as the model class you chose ------------------
# ⋂ over models removes model-relative explanations — but the choice of which models are admissible is the
# whole game. Too SMALL a class and confounders survive; too LARGE a class and the intersection collapses,
# erasing real mechanisms. The same knife edge appears in causal discovery, scientific modeling, and
# cryptographic attestation: the separator is only as good as the space of alternatives it rules out.

_ALL_MODELS = {"F1_restricted": F1_restricted, "F2_richer": F2_richer, "F3_overrich": F3_overrich}


def _G_F_over(model_fn):
    return {c for c in CANDIDATES if fits(model_fn) and necessary_under(model_fn, c)}


def robust_over(model_names):
    """Robust generator as the intersection of G_F over a CHOSEN admissible class (a subset of _ALL_MODELS)."""
    sets = [_G_F_over(_ALL_MODELS[n]) for n in model_names if fits(_ALL_MODELS[n])]
    return set.intersection(*sets) if sets else set()


def knife_edge():
    """Exhibit both failure modes of the model-class choice on one bench."""
    too_small = robust_over(["F1_restricted"])                                    # only the naive model
    right = robust_over(["F1_restricted", "F2_richer"])                           # the well-chosen class
    too_large = robust_over(["F1_restricted", "F2_richer", "F3_overrich"])        # includes the over-rich model
    return {"too_small": too_small, "right": right, "too_large": too_large}


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    gf1, gf2 = G_F("F1_restricted"), G_F("F2_richer")
    robust = robust_generator()
    out = {"observed": OBSERVED, "G_F_F1": sorted(gf1), "G_F_F2": sorted(gf2), "robust": sorted(robust)}
    # both models reproduce the data — both are admissible; necessity is only meaningful among models that fit
    out["both_models_fit_observed"] = fits(F1_restricted) and fits(F2_richer)
    # the same component reads necessary under one model and not the other
    out["c_necessary_under_F1"] = "c" in gf1
    out["c_not_necessary_under_F2"] = "c" not in gf2
    out["g_necessary_under_both"] = "g" in gf1 and "g" in gf2
    # therefore the generator set is model-relative
    out["G_F_differs_by_model"] = gf1 != gf2
    # the robust generator is what survives the model class
    out["robust_generator_is_g"] = robust == {"g"}
    # c was causal under a model but not invariant across models — a model-relative artifact
    out["c_causal_under_model_not_across"] = "c" in gf1 and "c" not in robust
    # a single model cannot separate them; the model class can (same lesson as ≥2 contexts in confounder.py)
    out["single_model_insufficient"] = gf1 != robust and robust == (gf1 & gf2)
    # the knife edge: the intersection is correct only for a well-chosen class
    k = knife_edge()
    out["too_small"], out["right_class"], out["too_large"] = sorted(k["too_small"]), sorted(k["right"]), sorted(k["too_large"])
    out["too_small_keeps_confounder"] = "c" in k["too_small"]                 # class too small → confounder survives
    out["right_class_recovers_g"] = k["right"] == {"g"}                       # well-chosen → exactly the generator
    out["too_large_erases_generator"] = k["too_large"] == set()              # class too large → generator erased
    out["knife_edge_monotone_collapse"] = k["too_small"] > k["right"] > k["too_large"]  # ⋂ shrinks as class grows
    return out


def demo():
    r = crucible()
    print("Model relativity — necessity is relative to the assumed dynamics (G_F is a function of F)\n")
    print("  observed trajectory (both models reproduce it): %s" % r["observed"])
    print("  G_F under F1 (restricted): %s     G_F under F2 (richer): %s" % (r["G_F_F1"], r["G_F_F2"]))
    print("  robust generator = ⋂ over admissible models: %s" % r["robust"])
    print()
    print("  · 'c' is necessary under F1 (%s) but not under F2 (%s) — necessity is model-relative"
          % (r["c_necessary_under_F1"], r["c_not_necessary_under_F2"]))
    print("  · so the generator set itself depends on the model: %s" % r["G_F_differs_by_model"])
    print("  · 'c' is causal under a model but NOT across models → a model-relative artifact: %s"
          % r["c_causal_under_model_not_across"])
    print("  · 'g' survives every admissible model → the robust generator: %s" % r["robust_generator_is_g"])
    print("  · a single model cannot separate them; the model CLASS can: %s" % r["single_model_insufficient"])
    print()
    print("  the knife edge — the intersection is only as good as the model class you chose:")
    print("    too small {F1}:        %s   → the confounder c survives" % r["too_small"])
    print("    well-chosen {F1,F2}:   %s        → exactly the generator" % r["right_class"])
    print("    too large {F1,F2,F3}:  %s         → the generator g is erased (an over-rich model absorbs it)" % r["too_large"])
    print("    monotone collapse as the class grows: %s" % r["knife_edge_monotone_collapse"])
    print()
    print("  the same invariance principle, one layer deeper: causal-under-a-model ≠ causal-across-models.")
    print("  the model class is the A_C choice — 'necessary to which F?' is the next boundary, and CHOOSING")
    print("  the admissible class is the open hard problem (too small: confounders survive; too large: collapse).")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.model_relativity", OBSERVER, mutates_core=False,
                          note="necessity is model-relative: G_F(F_model_1) != G_F(F_model_2). The same "
                               "component reads necessary under a restricted model and redundant under a richer "
                               "one that fits the same data. The robust generator = intersection of G_F over "
                               "the admissible model class (the A_C loop, one layer deeper). A single model "
                               "cannot separate causal from model-relative artifact; a model class can. "
                               "causal-under-a-model != causal-across-models")
    except LayerViolation:
        pass
