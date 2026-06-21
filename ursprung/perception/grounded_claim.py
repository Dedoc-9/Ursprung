# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/grounded_claim.py — the axiom made runtime: a conclusion that carries its floor.

The whole arc kept uncovering the same shape: every explanatory system has a layer that is *chosen, not
derived*.

    observation depends on a projection      Π
    attribution depends on a model           F
    robustness depends on a model class      𝓕
    the choice of 𝓕 depends on a stopping rule
    the stopping rule is a declared boundary  (conventions.admissible_model_class)

The realization is not that explanation is impossible — it is that **some layer of every explanatory system is
chosen rather than derived**, and a system that does not expose that layer accidentally smuggles an assumption
in as a fact. This module makes the difference a runtime object rather than a sentiment. Two statements that
*feel* alike are fundamentally different epistemic types:

    weak (floor-hiding):    "the evidence proves X."
    strong (floor-exposing): "given observer class A, projection Π, model class 𝓕, and evidence E,
                              X is the best SURVIVING explanation."

A `GroundedClaim` is the second kind, enforced: you cannot construct or emit one without declaring every chosen
layer, it never asserts truth (`truth_claim = False`, like a `Convention`), and it says *surviving*, never
*proven*. The runtime also classifies external claims — a bare "proves X" with no declared floor is flagged
`floor_hiding` — and demonstrates the operational consequence: the *same* evidence, under two *different
declared* 𝓕, yields *different* surviving conclusions (the knife edge of `model_relativity`). So "confidence"
is not a scalar attached to evidence; it is a function of the declared floor. Change the floor, change the
conclusion — which is exactly why the floor must be visible.

This is what turns the project's first rule — *arbitrary boundaries require deterministic handling, not claims
of truth* — from a software convention into an epistemology: the coordinate system, the observer, the
projection, the model class, and the stopping rule are all arbitrary boundaries in that precise sense. The
mature move is not pretending they were derived; it is declaring them, content-addressed, so a hidden
commitment becomes an inspectable one.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: this is an accounting/typing instrument, not a
truth oracle — it makes a claim's floor *visible and contestable*; it does not make the floor *right*. A
grounded claim can be useful, predictive, and robust and still rest on a declared boundary it did not derive.
The realization is "every system has a floor that cannot be justified entirely from within the system" — NOT
"everything is arbitrary" (that overshoots into relativism). Separators: proven ≠ surviving; floor-hiding ≠
floor-exposing; confidence ≠ scalar (it is conditional on the declared floor); declared ≠ derived; declared ≠
truth.
"""
from __future__ import annotations

import hashlib
import json

# The layers every honest conclusion stands on. Absence of any one = an undeclared (smuggled) floor.
REQUIRED_FLOOR = ("evidence", "projection", "observer_class", "model_class", "stopping_rule")

# ...but they are NOT the same kind of thing. Evidence is encountered; the projection / observer class / model
# class are chosen by the analyst; the stopping rule is a declared boundary. Flattening these erases exactly
# the distinction the project preserves — confidence is a function of (evidence, floor) only if the floor is
# visibly *not* the evidence. So each layer carries its provenance kind:
ENCOUNTERED = "encountered"   # observed / given by the world — not a choice
CHOSEN = "chosen"             # a selection the analyst made (and a reviewer may dispute)
DECLARED = "declared"         # a declared stopping boundary (a convention, never a truth claim)

FLOOR_KIND = {
    "evidence": ENCOUNTERED,
    "projection": CHOSEN,
    "observer_class": CHOSEN,
    "model_class": CHOSEN,
    "stopping_rule": DECLARED,
}


def _hash(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


class GroundedClaim:
    """A conclusion bound to the floor it stands on. It never asserts truth — only 'best surviving explanation
    given (A, Π, 𝓕, E)' — and it cannot emit a statement while any chosen layer is undeclared."""
    __slots__ = ("conclusion", "evidence", "projection", "observer_class", "model_class",
                 "stopping_rule", "truth_claim")

    def __init__(self, conclusion, evidence, projection, observer_class, model_class, stopping_rule):
        self.conclusion = conclusion
        self.evidence = evidence
        self.projection = projection            # Π — the observation channel
        self.observer_class = observer_class    # A_C — the reconstruction class
        self.model_class = model_class          # 𝓕 — the admissible explanation space
        self.stopping_rule = stopping_rule      # the declared boundary that terminates the regress
        self.truth_claim = False                # invariant: a grounded claim is never a truth claim

    def missing_floor(self):
        """Which layers were left undeclared (i.e. smuggled in)."""
        return [k for k in REQUIRED_FLOOR if not getattr(self, k)]

    def is_grounded(self):
        return not self.missing_floor()

    def observations(self):
        """What was ENCOUNTERED (given by the world, not chosen)."""
        return {k: getattr(self, k) for k in REQUIRED_FLOOR if FLOOR_KIND[k] == ENCOUNTERED}

    def choices(self):
        """What was CHOSEN by the analyst (and a reviewer may dispute) — Π, A_C, 𝓕."""
        return {k: getattr(self, k) for k in REQUIRED_FLOOR if FLOOR_KIND[k] == CHOSEN}

    def boundaries(self):
        """What was DECLARED as a stopping boundary (a convention, never a truth claim)."""
        return {k: getattr(self, k) for k in REQUIRED_FLOOR if FLOOR_KIND[k] == DECLARED}

    def statement(self):
        """Emit the only kind of statement this object will make: conditional, surviving, floor-declared.
        Refuses to emit anything while a layer is undeclared (you cannot hide the floor through this seam)."""
        if not self.is_grounded():
            raise ValueError("ungrounded claim: undeclared floor layers %s — declare them or do not conclude"
                             % self.missing_floor())
        return ("From evidence %s (encountered), under chosen projection %s, observer class %s, and model "
                "class %s, with declared boundary %s, %s is the BEST SURVIVING explanation. (truth_claim=false "
                "— a surviving explanation, not a settled truth.)"
                % (self.evidence, self.projection, self.observer_class, self.model_class,
                   self.stopping_rule, self.conclusion))

    def floor_digest(self):
        """Content address of the full stack: two claims with different floors have different identity, even
        for the same conclusion — so a conclusion's provenance is part of what it *is*."""
        return _hash({k: getattr(self, k) for k in REQUIRED_FLOOR + ("conclusion",)})

    def as_dict(self):
        d = {k: getattr(self, k) for k in REQUIRED_FLOOR}
        d.update({"conclusion": self.conclusion, "truth_claim": False, "floor_digest": self.floor_digest()})
        return d


FLOOR_HIDING = "floor_hiding"
FLOOR_EXPOSING = "floor_exposing"


def classify_claim(asserts_truth, declared_layers):
    """Type an arbitrary external claim. A claim is floor-HIDING if it asserts truth, or leaves any chosen
    layer undeclared; floor-EXPOSING only if it is conditional AND declares every layer. The bare 'the
    evidence proves X' is the canonical floor-hiding claim (it asserts truth and declares nothing)."""
    declared = set(declared_layers)
    missing = [k for k in REQUIRED_FLOOR if k not in declared]
    return FLOOR_HIDING if (asserts_truth or missing) else FLOOR_EXPOSING


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    E = "observed trajectory [2, 1, 0, 7, 6, 5]"
    stop = "conventions.admissible_model_class (declared boundary, truth_claim=false)"
    # the SAME evidence, two DIFFERENT declared model classes 𝓕 → different surviving conclusion (the knife edge)
    try:
        from . import model_relativity as mr
        k = mr.knife_edge()
        narrow_concl = "generator = %s" % sorted(k["too_small"])   # 𝓕 too narrow → confounder survives
        right_concl = "generator = %s" % sorted(k["right"])        # 𝓕 well-chosen
    except Exception:
        narrow_concl, right_concl = "generator = ['c', 'g']", "generator = ['g']"
    narrow = GroundedClaim(narrow_concl, E, "visible-only Π", "interventionist A_C", "𝓕 = {F1}", stop)
    right = GroundedClaim(right_concl, E, "visible-only Π", "interventionist A_C", "𝓕 = {F1, F2}", stop)

    # a grounded claim requires every chosen layer; an undeclared layer makes it ungrounded
    out["grounded_requires_all_layers"] = not GroundedClaim("X", E, "", "A_C", "𝓕", stop).is_grounded()
    # the only statement it will emit is conditional + 'surviving', never 'proven'
    s = right.statement()
    out["statement_is_conditional"] = ("BEST SURVIVING" in s) and ("prove" not in s.lower())
    out["statement_names_every_layer"] = all(tok in s for tok in ("observer class", "projection", "model class", "evidence"))
    # it refuses to emit a statement while a layer is undeclared (the floor cannot be hidden through this seam)
    try:
        GroundedClaim("X", E, "", "A_C", "𝓕", stop).statement()
        out["undeclared_floor_blocks_statement"] = False
    except ValueError:
        out["undeclared_floor_blocks_statement"] = True
    # the bare 'the evidence proves X' is the canonical floor-HIDING claim; the declared conditional is exposing
    out["bare_proof_is_floor_hiding"] = classify_claim(True, set()) == FLOOR_HIDING
    out["declared_conditional_is_floor_exposing"] = classify_claim(False, REQUIRED_FLOOR) == FLOOR_EXPOSING
    # the operational consequence: confidence is conditional on the declared floor, not a scalar of the evidence
    out["confidence_depends_on_declared_floor"] = (narrow.conclusion != right.conclusion) and (narrow.evidence == right.evidence)
    # provenance is part of identity: same evidence, different floor → different claim
    out["different_floor_different_identity"] = narrow.floor_digest() != right.floor_digest()
    # invariant: a grounded claim never asserts truth
    out["claim_never_asserts_truth"] = right.truth_claim is False
    # the floor is NOT one undifferentiated thing: evidence is encountered, Π/A_C/𝓕 are chosen, the stopping
    # rule is declared. The categories partition the floor.
    enc, cho, dec = set(right.observations()), set(right.choices()), set(right.boundaries())
    out["floor_categories_partition"] = (enc | cho | dec) == set(REQUIRED_FLOOR) and not (enc & cho) and not (cho & dec) and not (enc & dec)
    out["evidence_encountered_rest_not"] = (enc == {"evidence"}
                                            and cho == {"projection", "observer_class", "model_class"}
                                            and dec == {"stopping_rule"})
    # the deep implication: the conclusion's variability is attributable to a CHOSEN layer (𝓕), with the
    # ENCOUNTERED evidence held identical — confidence is f(evidence, floor), not a scalar of the evidence
    differing = [k for k in REQUIRED_FLOOR if getattr(narrow, k) != getattr(right, k)]
    out["variation_attributable_to_a_choice"] = (differing == ["model_class"]
                                                  and FLOOR_KIND["model_class"] == CHOSEN
                                                  and narrow.evidence == right.evidence)
    out["_statement"] = s
    out["_narrow"] = narrow.conclusion
    out["_right"] = right.conclusion
    return out


def demo():
    r = crucible()
    print("Grounded claim — a conclusion that carries its floor (the axiom, made runtime)\n")
    print("  weak (floor-hiding):     'the evidence proves X.'           → %s" % FLOOR_HIDING)
    print("  strong (floor-exposing): the GroundedClaim statement below  → %s\n" % FLOOR_EXPOSING)
    print("  " + r["_statement"] + "\n")
    print("  · a claim cannot be stated while a chosen layer is undeclared: %s" % r["undeclared_floor_blocks_statement"])
    print("  · it says SURVIVING, never proven: %s" % r["statement_is_conditional"])
    print("  · the same evidence under 𝓕={F1} vs 𝓕={F1,F2} → different surviving conclusion (%s vs %s):"
          % (r["_narrow"], r["_right"]))
    print("      confidence is conditional on the declared floor, not a scalar of the evidence: %s"
          % r["confidence_depends_on_declared_floor"])
    print("  · provenance is identity — different floor, different claim: %s" % r["different_floor_different_identity"])
    print("\n  the question shifts from 'have we proven the final explanation?' to")
    print("  'what assumptions made this explanation possible, and are they visible?'  proven ≠ surviving.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.grounded_claim", OBSERVER, mutates_core=False,
                          note="the axiom made runtime: a conclusion that carries its floor (evidence, Π, A_C, "
                               "𝓕, stopping rule). Cannot be stated with an undeclared layer; never asserts "
                               "truth, only 'best surviving explanation given (A,Π,𝓕,E)'. Classifies a bare "
                               "'evidence proves X' as floor_hiding. Confidence is conditional on the declared "
                               "floor (same E, different 𝓕 → different conclusion). proven != surviving; "
                               "declared != derived; declared != truth")
    except LayerViolation:
        pass
