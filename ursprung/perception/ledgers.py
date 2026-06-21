# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/ledgers.py — two ledgers: keep "how did we arrive?" and "does it match the world?" apart.

`grounded_claim.py` made a conclusion carry its floor. But it left one fusion intact that the whole project
warns against: collapsing two different questions into one notion of "confidence."

    Q1 — can we reproduce and audit this account?        EPISTEMIC / accounting   (integrity)
    Q2 — does this account correspond to the world?       ONTOLOGICAL / truth      (adequacy)

These come apart, and the failure of every "confidence score" is that it lets a high mark in one masquerade as
a high mark in the other. So this module tracks them as **two separate objects** with no automatic link:

    EpistemicLedger.integrity(account)   — reproducible AND fully-declared floor? (belongs to integrity)
    OntologicalLedger.adequacy(record)   — predicts, survives intervention, robust across contexts? (belongs to truth)

The three canonical cases, as fixtures and negative controls:
  · buggy_calculator — `2 + 2 = 5`, deterministically, every time, fully declared. Integrity 1.0, adequacy 0.0.
    *reproducible but wrong* — perfect accounting, false conclusion.
  · prescient_intuition — a correct hunch with no declared procedure or evidence. Integrity ~0, adequacy ~0.9.
    *true but poorly accounted* — right answer, no provenance.
  · mature_science — reproducible procedure AND empirical adequacy. Both high. The only case that earns trust
    in both ledgers, and it earns it twice, separately.

The load-bearing result: a single scalar cannot tell `buggy_calculator` from `mature_science` — they have the
*same integrity* (1.0) and opposite adequacy — so collapsing the two ledgers into one "confidence" silently
launders a reproducible-but-wrong account into a trustworthy one. This is `integrity ≠ truth` given a runtime:
integrity lives in the epistemic ledger (same account → same result), truth in the ontological ledger (account
↔ world). A mature system keeps both visible and lets neither imply the other; the link between them is
explicit, never a collapse.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: the adequacy score is a toy stand-in (declared
0..1 inputs for prediction / intervention / robustness), NOT a measured correspondence with reality — and that
is the point: the ontological ledger is exactly where the project's numbers are weakest and most provisional
(`simulation ≠ physics`; everything expires on real silicon). The instrument does not claim to *measure* truth;
it claims to keep the truth question from being silently answered by the accounting question. Separators:
integrity ≠ truth; reproducible ≠ true; predictive ≠ causal; declared ≠ derived.
"""
from __future__ import annotations

from . import grounded_claim as gcm

# The epistemic floor a reproducible account must declare (reused from grounded_claim).
FLOOR = gcm.REQUIRED_FLOOR


class EpistemicLedger:
    """Question 1 — *how did we arrive here?* Integrity = the account is reproducible AND its floor is fully
    declared. This is bookkeeping; it says nothing about whether the conclusion matches the world."""

    def integrity(self, account):
        """`account`: the declared floor layers (truthy if declared) + a `reproducible` flag."""
        declared = sum(1 for k in FLOOR if account.get(k))
        if declared == len(FLOOR) and account.get("reproducible"):
            return 1.0
        # partial credit, halved if not even reproducible — but never full without complete declaration + replay
        return round(declared / len(FLOOR) * (1.0 if account.get("reproducible") else 0.5), 3)

    def reads(self):
        """What this ledger looks at — only the account's floor, never its worldly adequacy."""
        return tuple(FLOOR) + ("reproducible",)


class OntologicalLedger:
    """Question 2 — *why should we believe this corresponds to the world?* Adequacy = predicts, survives
    intervention, holds across contexts. This is the truth question; it says nothing about whether the path
    that produced the conclusion was reproducible or even declared."""

    AXES = ("predictive_accuracy", "survives_intervention", "cross_context_robustness")

    def adequacy(self, record):
        """`record`: 0..1 scores for prediction, intervention-survival, and cross-context robustness."""
        vals = [record.get(k, 0.0) for k in self.AXES]
        return round(sum(vals) / len(vals), 3)

    def reads(self):
        return self.AXES


# the canonical cases (fixtures + negative controls)
CASES = {
    "buggy_calculator": {  # 2+2=5, deterministically — flawless accounting, false conclusion
        "epistemic": {**{k: "declared" for k in FLOOR}, "reproducible": True},
        "ontological": {"predictive_accuracy": 0.0, "survives_intervention": 0.0, "cross_context_robustness": 0.0}},
    "prescient_intuition": {  # a correct hunch with no declared procedure — right, but unaccounted
        "epistemic": {**{k: "" for k in FLOOR}, "reproducible": False},
        "ontological": {"predictive_accuracy": 0.95, "survives_intervention": 0.90, "cross_context_robustness": 0.85}},
    "mature_science": {  # reproducible procedure AND empirical adequacy — earns trust in both ledgers, separately
        "epistemic": {**{k: "declared" for k in FLOOR}, "reproducible": True},
        "ontological": {"predictive_accuracy": 0.90, "survives_intervention": 0.88, "cross_context_robustness": 0.86}},
}


def score_all():
    E, O = EpistemicLedger(), OntologicalLedger()
    return {n: {"integrity": E.integrity(c["epistemic"]), "adequacy": O.adequacy(c["ontological"])}
            for n, c in CASES.items()}


def collapsed_confidence(scores, mode="integrity_only"):
    """A SINGLE 'confidence' scalar — the thing the two ledgers refuse to be. Provided only to show what it
    loses: 'integrity_only' crowns the buggy calculator; no scalar preserves the integrity/adequacy distinction."""
    if mode == "integrity_only":
        return {n: s["integrity"] for n, s in scores.items()}
    if mode == "adequacy_only":
        return {n: s["adequacy"] for n, s in scores.items()}
    return {n: round((s["integrity"] + s["adequacy"]) / 2, 3) for n, s in scores.items()}  # average


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    E, O = EpistemicLedger(), OntologicalLedger()
    s = score_all()
    out = {"scores": s}
    # the three cases land where the argument says they must
    out["reproducible_but_wrong"] = s["buggy_calculator"]["integrity"] >= 0.9 and s["buggy_calculator"]["adequacy"] <= 0.1
    out["true_but_poorly_accounted"] = s["prescient_intuition"]["integrity"] <= 0.1 and s["prescient_intuition"]["adequacy"] >= 0.8
    out["reproducible_and_adequate"] = s["mature_science"]["integrity"] >= 0.8 and s["mature_science"]["adequacy"] >= 0.8
    # neither ledger implies the other
    out["integrity_does_not_imply_truth"] = s["buggy_calculator"]["integrity"] >= 0.9 and s["buggy_calculator"]["adequacy"] <= 0.1
    out["truth_does_not_imply_integrity"] = s["prescient_intuition"]["adequacy"] >= 0.8 and s["prescient_intuition"]["integrity"] <= 0.1
    # the axes are independent functions: ontological inputs don't move integrity; floor doesn't move adequacy
    out["integrity_ignores_ontology"] = E.integrity({**CASES["buggy_calculator"]["epistemic"]}) == \
        E.integrity({**CASES["buggy_calculator"]["epistemic"], "predictive_accuracy": 0.99})
    out["adequacy_ignores_floor"] = O.adequacy({**CASES["mature_science"]["ontological"]}) == \
        O.adequacy({**CASES["mature_science"]["ontological"], "evidence": "anything"})
    # the load-bearing control: a single integrity scalar cannot tell reproducible-but-wrong from reproducible-and-adequate
    out["one_scalar_cannot_distinguish"] = (s["buggy_calculator"]["integrity"] == s["mature_science"]["integrity"]
                                            and s["buggy_calculator"]["adequacy"] != s["mature_science"]["adequacy"])
    # and collapsing to integrity-only crowns the buggy calculator (laundering accounting into truth)
    coll = collapsed_confidence(s, "integrity_only")
    out["collapse_launders_wrong_as_trustworthy"] = coll["buggy_calculator"] == max(coll.values()) and s["buggy_calculator"]["adequacy"] == 0.0
    return out


def demo():
    r = crucible()
    s = r["scores"]
    print("Two ledgers — integrity (how we arrived) vs adequacy (does it match the world)\n")
    print("  %-22s %-12s %-12s" % ("case", "integrity", "adequacy"))
    for n in ("buggy_calculator", "prescient_intuition", "mature_science"):
        print("  %-22s %-12s %-12s" % (n, s[n]["integrity"], s[n]["adequacy"]))
    print()
    print("  · reproducible but wrong (calculator): %s — flawless accounting, false conclusion" % r["reproducible_but_wrong"])
    print("  · true but poorly accounted (intuition): %s — right answer, no provenance" % r["true_but_poorly_accounted"])
    print("  · the axes are independent: integrity ignores ontology (%s), adequacy ignores the floor (%s)"
          % (r["integrity_ignores_ontology"], r["adequacy_ignores_floor"]))
    print("  · a single integrity scalar cannot tell the calculator from real science (same 1.0, opposite adequacy): %s"
          % r["one_scalar_cannot_distinguish"])
    print("  · so collapsing to one 'confidence' crowns the buggy calculator: %s" % r["collapse_launders_wrong_as_trustworthy"])
    print("\n  integrity ≠ truth, as two ledgers: keep both visible; let neither imply the other.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.ledgers", OBSERVER, mutates_core=False,
                          note="two separate ledgers — EPISTEMIC (integrity: reproducible + fully-declared "
                               "floor) vs ONTOLOGICAL (adequacy: predicts + survives intervention + robust). "
                               "They come apart: a buggy calculator is integrity 1.0 / adequacy 0.0; a correct "
                               "hunch is the reverse. A single integrity scalar cannot tell reproducible-but-"
                               "wrong from reproducible-and-adequate, so the ledgers must not be collapsed. "
                               "integrity != truth, made a runtime; reproducible != true")
    except LayerViolation:
        pass
