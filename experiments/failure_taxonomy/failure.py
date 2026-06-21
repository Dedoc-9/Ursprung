# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/failure_taxonomy/failure.py — the provenance of ignorance: WHY is a cause unrecoverable?

An estimator that fails should not report a generic "unknown." Under this project's discipline it must say
*which kind* of failure it hit — because the four kinds have completely different remedies (and two of them
have none). This is the downstream consequence of the two absolutes: it types the **provenance of ignorance**,
unifying the whole identifiability arc into one classifier.

    severance              ABSOLUTE   information is ABSENT — I(X;O)=0 for every observable. An INDEPENDENCE
                                       relation. "No path remains." (M21)
    indistinguishability   ABSOLUTE   information is PRESENT but non-discriminating — a distinct cause X'
                                       induces identical distributions over every observable AND intervention.
                                       An EQUIVALENCE relation (X ~ X'). "Multiple paths, same observable world."
    assumption_limit       RELATIVE   not enough admissible structure — recovery resolves under a richer
                                       admissibility set 𝓐 (a stronger declared assumption), NOT under a richer
                                       observer. (the model_relativity / 𝓐 knife edge)
    resource_limit         RELATIVE   observer boundedness — recovery resolves under a richer observer class,
                                       NOT by adding assumptions. (the adversary_capacity lattice)

The two absolutes are **observer-independent**: they resolve neither under a richer observer nor a richer 𝓐 —
the failure is in the world's relation to the observables, not in the observer. The two relative limits each
resolve under exactly one axis, which is what distinguishes them from each other. Severance and
indistinguishability are different mathematical objects (independence vs equivalence), which is why "no signal"
and "ambiguous signal" must never collapse into one verdict.

HONEST BOUND: like the two-absolutes module, this classifies a DECLARED situation — it records which kind of
failure is *claimed* (and what would resolve it), not a verified proof that e.g. no observable carries the
signal (severance) or that an alternative cause matches across all interventions (indistinguishability — the
un-runnable check). `declared ≠ verified`. The value is the taxonomy: it forbids a generic "unknown" and forces
the failure to name its own provenance.
"""
from __future__ import annotations

SEVERANCE = "severance"
INDISTINGUISHABILITY = "indistinguishability"
ASSUMPTION_LIMIT = "assumption_limit"
RESOURCE_LIMIT = "resource_limit"

ABSOLUTE = (SEVERANCE, INDISTINGUISHABILITY)        # observer-independent — no remedy
RELATIVE = (ASSUMPTION_LIMIT, RESOURCE_LIMIT)       # resolve under their own axis

RELATION = {SEVERANCE: "independence", INDISTINGUISHABILITY: "equivalence",
            ASSUMPTION_LIMIT: "admissibility", RESOURCE_LIMIT: "capacity"}
REMEDY = {SEVERANCE: "none (information is absent)",
          INDISTINGUISHABILITY: "none (a distinct cause is observationally identical)",
          ASSUMPTION_LIMIT: "admit a stronger declared assumption (enlarge 𝓐)",
          RESOURCE_LIMIT: "upgrade the observer class (more capacity / interventions)"}


def tier(kind):
    return "absolute" if kind in ABSOLUTE else ("relative" if kind in RELATIVE else "unknown")


def classify_failure(case):
    """Type a recovery failure. `case` declares the situation:
        signal_present                    — does any observable carry information about X?
        alternative_cause_matches         — does a distinct X' match over all observables AND interventions?
        resolves_under_richer_admissibility — would a stronger declared assumption recover it?
        resolves_under_richer_observer    — would a richer observer class recover it?
    Order matters: absence first, then collision, then the relative axes."""
    if not case.get("signal_present"):
        return SEVERANCE
    if case.get("alternative_cause_matches"):
        return INDISTINGUISHABILITY
    if case.get("resolves_under_richer_admissibility"):
        return ASSUMPTION_LIMIT
    if case.get("resolves_under_richer_observer"):
        return RESOURCE_LIMIT
    return "unclassified"      # a well-formed recovery failure should never land here


def diagnose(case):
    """A full failure record — the provenance of ignorance, not a bare 'unknown'."""
    kind = classify_failure(case)
    return {"failure": kind, "tier": tier(kind), "relation": RELATION.get(kind),
            "remedy": REMEDY.get(kind, "ill-formed case"),
            "observer_independent": kind in ABSOLUTE}
