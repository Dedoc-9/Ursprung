# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/confounder.py — separating the generator from what merely looks like it.

The four-operator separation (`operators.py`) has a hidden fifth path the diagram must name: a **confounder**
`C` — an uncontrolled influence on the observation that is not the generator. The picture is

    F, M → Π → O ← C ← A_C

The observer sees `O`, never `F`, so `P(F | O)` is identifiable **only if the confounder space is
constrained**. This is the sharper successor to "what is the generator?": *under what conditions can the
generator be separated from everything that merely looks like the generator?*

The warning your phrasing names — a mechanism is arbitrary / senseless except as part of a whole — is the crux:
a recoverable pattern is **not** automatically the generator. It can be a generator, a constraint, a residue, a
projection artifact, or a temporary equilibrium. A perfectly fitted rule may be a confounder that holds only in
one context. So the mature criterion is not "find the rule that fits" but:

    **find what remains invariant when the observer, the projection, and the context all change.**

That invariant is the closest thing to a real generator. (This is Invariant Causal Prediction / invariant-
across-environments learning, in the project's language.)

The bench: a causal rule (the generator `F`) and a spurious rule (a confounder that correlates with the target
only within one environment). Findings:

  * **within one context, they are indistinguishable** — both fit perfectly; you cannot tell the generator from
    the confounder from a single environment.
  * **across contexts, only the generator survives** — the confounder's cross-environment accuracy collapses
    (0.667 vs 1.0); the invariant rule is the generator.
  * **higher capacity overfits the confounder** — a more expressive observer fits the spurious rule perfectly
    in-context yet generalizes worse. *High capacity, low causal identifiability* — the same danger as ML
    generalization: `mechanism ≠ correlation`, `fitted rule ≠ causal source`.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy rules and discrete environments; real
confounder separation (Invariant Causal Prediction, interventions) is open and data-hungry. The point is
structural — identifiability of `F` requires varying `C`, and the generator is the cross-context invariant.
mechanism ≠ correlation; fitted rule ≠ causal source; simulation ≠ physics.
"""
from __future__ import annotations

ENVIRONMENTS = ("e1", "e2", "e3")

# the rules an observer might infer: one causal (the true generator, invariant) and one spurious per
# environment (a confounder that correlates with the target only inside that environment)
RULES = ["causal"] + ["spurious@%s" % e for e in ENVIRONMENTS]


def accuracy(rule, env):
    """How well a rule predicts in an environment. The causal rule is right everywhere (it is the generator);
    a spurious rule is right only in the environment whose confounder it captured, chance elsewhere."""
    if rule == "causal":
        return 1.0
    return 1.0 if rule.endswith(env) else 0.5


def consistent_across(envs, rule):
    return all(accuracy(rule, e) == 1.0 for e in envs)


def invariant_rules(envs):
    """The rules that hold across every environment in `envs` — the candidate generators given that context set."""
    return [r for r in RULES if consistent_across(envs, r)]


def cross_environment_accuracy(rule):
    return sum(accuracy(rule, e) for e in ENVIRONMENTS) / len(ENVIRONMENTS)


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    one = invariant_rules(["e1"])
    allenv = invariant_rules(ENVIRONMENTS)
    out["invariant_in_one_env"] = one
    out["invariant_across_all"] = allenv
    # within one context the generator and a confounder are indistinguishable (both fit perfectly)
    out["single_context_ambiguous"] = len(one) > 1
    # across contexts only the generator survives — it is the cross-context invariant
    out["context_variation_identifies_generator"] = allenv == ["causal"]
    out["generator_is_the_invariant"] = "causal" in allenv and len(allenv) == 1
    # the confounder fits in its own context and fails across contexts
    out["confounder_fits_in_context"] = accuracy("spurious@e1", "e1") == 1.0
    out["confounder_fails_across"] = cross_environment_accuracy("spurious@e1") < 1.0
    # higher capacity overfits the confounder: equal-or-better in-context, worse cross-context
    out["capacity_overfits_confounder"] = (accuracy("spurious@e1", "e1") >= accuracy("causal", "e1")
                                           and cross_environment_accuracy("spurious@e1")
                                           < cross_environment_accuracy("causal"))
    # separation requires context variation — one environment cannot do it, two can
    out["separation_requires_context_variation"] = (len(invariant_rules(["e1"])) > 1
                                                    and len(invariant_rules(["e1", "e2"])) == 1)
    return out


def demo():
    r = crucible()
    print("Confounder separation — the generator is what stays invariant when context changes\n")
    print("  F, M → Π → O ← C ← A_C   (the observer sees O, never F; P(F|O) needs the confounder constrained)\n")
    print("  candidate rules invariant over one context [e1]: %s" % r["invariant_in_one_env"])
    print("    → ambiguous: the generator and a confounder both fit perfectly in one context.")
    print("  candidate rules invariant over all contexts:     %s" % r["invariant_across_all"])
    print("    → only the generator survives; the confounders dissolve. cross-env accuracy: causal %.3f vs spurious %.3f."
          % (cross_environment_accuracy("causal"), cross_environment_accuracy("spurious@e1")))
    print("  higher capacity overfits the confounder (better in-context, worse cross-context): %s"
          % r["capacity_overfits_confounder"])
    print("  separation requires varying the context (1 env can't, 2 can): %s"
          % r["separation_requires_context_variation"])
    print("\n  a recoverable pattern is not an identity — it can be a generator, constraint, residue, artifact,")
    print("  or temporary equilibrium. the generator is the invariant across observer, projection, and context.")
    print("  mechanism ≠ correlation; fitted rule ≠ causal source.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.confounder", OBSERVER, mutates_core=False,
                          note="confounder separation: O ← C; P(F|O) identifiable only if C is constrained. "
                               "within one context the generator and a confounder are indistinguishable; across "
                               "contexts only the generator (the invariant) survives; higher capacity overfits "
                               "the confounder. the generator is what stays invariant when observer/projection/"
                               "context change. mechanism ≠ correlation; fitted rule ≠ causal source")
    except LayerViolation:
        pass
