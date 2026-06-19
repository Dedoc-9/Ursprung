# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/divergence.py — the three classes of difference (the renderer's debugging language).

Once the Arbitrary-Boundary Law is mechanical, an observed artifact is no longer "a bug" by default. It is
first *classified by the layer that produced it*. There are exactly three kinds of difference in Ursprung:

    1. WORLD divergence          CORE changed.
                                 INVALID for any VIEW/ALLOCATOR/OBSERVER change (only CORE may move state).
    2. REPRESENTATION divergence Same CORE, different projection / approximation / convention.
                                 EXPECTED — measure it (it is a boundary footprint, not an error).
    3. OBSERVATION divergence    Same representation, different measured behavior.
                                 INVESTIGATE — this is a ghost; allocate attention, do not assume a cause.

So a future artifact — shimmer during motion, LOD pop, temporal ghosting, shadow instability, a
floating-point edge case, an AI-upscaler hallucination — runs through:

    artifact observed
        → which layer introduced it?
            → boundary convention   (representation divergence — expected)
            → approximation         (representation divergence — expected)
            → implementation error  (a real bug)
            → missing causal model  (observation divergence — investigate ghost)

This is the LLM guardrail in structural form: an agent proposing "replace the rasterizer because this
artifact exists" must first answer *which class* the artifact is. That is much harder to hand-wave.

CLASSIFICATION: OBSERVER (mutates_core=False). It classifies differences; it changes nothing.

HONEST BOUND: the classifier tells you *where to look*, not *what is true*. A REPRESENTATION verdict says
the difference is lawful given the convention — not that the convention is the right one (integrity ≠ truth).
"""
from __future__ import annotations

WORLD = "world_divergence"
REPRESENTATION = "representation_divergence"
OBSERVATION = "observation_divergence"
NONE = "no_divergence"


class DivergenceVerdict:
    __slots__ = ("kind", "valid", "action", "detail")

    def __init__(self, kind, valid, action, detail=""):
        self.kind = kind
        self.valid = valid        # is this difference admissible for the layer that produced it?
        self.action = action      # what the engineer should do next
        self.detail = detail

    def __repr__(self):
        return "<Divergence %s valid=%s: %s>" % (self.kind, self.valid, self.action)


def classify(core_changed, representation_changed=False, observation_changed=False, layer="VIEW"):
    """Classify an observed difference into one of the three classes.

    core_changed           : did the committed CORE trajectory change?
    representation_changed : same CORE, but a different projection/approximation/convention was used?
    observation_changed    : same representation, but the measured behavior differs (a residual)?
    layer                  : the layer of the change under review (CORE may legitimately move state).
    """
    if core_changed:
        valid = (layer == "CORE")
        return DivergenceVerdict(
            WORLD, valid,
            "CORE moved — legitimate only for a CORE change; for VIEW/ALLOCATOR/OBSERVER this is a write-back "
            "leak and is INVALID" if not valid else "CORE change: re-verify replay identity + conformance",
            "the committed Weltlinie changed")
    if representation_changed:
        return DivergenceVerdict(
            REPRESENTATION, True,
            "EXPECTED — measure it: identify the convention/approximation that produced it (conventions.py), "
            "record it as a boundary footprint, decide if acceptable for the purpose",
            "same world, different lens")
    if observation_changed:
        return DivergenceVerdict(
            OBSERVATION, True,
            "INVESTIGATE — this is a ghost: classify category/origin (ghost_report.py), allocate attention; "
            "do not assume a cause and do not rewrite the world",
            "same representation, different measured behavior")
    return DivergenceVerdict(NONE, True, "no difference observed", "")


def classify_artifact_source(source):
    """Map a suspected artifact source to its divergence class + whether it is a real bug. Encodes the
    'which layer introduced it?' fan-out for triage."""
    table = {
        "boundary_convention": (REPRESENTATION, False),   # expected, not a bug
        "approximation":       (REPRESENTATION, False),   # expected, not a bug
        "implementation_error": (WORLD, True),            # a real bug (or a CORE/impl defect)
        "missing_causal_model": (OBSERVATION, False),     # a ghost to investigate, not yet a bug
    }
    kind, is_bug = table.get(source, (OBSERVATION, False))
    return {"source": source, "divergence_kind": kind, "is_bug": is_bug}


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("divergence", OBSERVER, mutates_core=False,
                          note="classifies world/representation/observation divergence (debugging language)")
    except LayerViolation:
        pass
