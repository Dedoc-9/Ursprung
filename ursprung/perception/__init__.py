# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/ — the first complete PERCEPTION LOOP (a measurement substrate, not a milestone).

One end-to-end path that exercises the whole thesis on a small, falsifiable problem:

    world state → DisclosurePolicy → compiled observation → agent → task performance → leakage measurement

Reality (`toy_task`) contributes truth; the `DisclosurePolicy` + `observation_compiler` contribute controlled
disclosure; the agent + `participation_utility` contribute measured usefulness; `channel_discovery` (QIF)
contributes leakage; and the `MeasurementResult` reports the (utility, leakage) frontier under a stated
observer class — never a bare "safe". It is the repo's first privacy-funnel benchmark: *can task success be
preserved while keeping leakage under a declared budget?* Composition of everything already built — not a new
law. See `docs/INFORMATION_INTENT.md` §7 (the build order this is step 1–4 of).
"""
from __future__ import annotations

from . import (toy_task, disclosure_policy, observation_compiler, utility,  # noqa: F401
               adversary, session_accounting, frontier, fidelity, observer_capacity, response, intent,
               consistency, identifiability)
from .disclosure_policy import DisclosurePolicy, POLICIES
from .observation_compiler import compile_observation
from .utility import (participation_utility, leakage_bits, evaluate, funnel_frontier,
                      crucible, demo, MeasurementResult)

__all__ = ["toy_task", "disclosure_policy", "observation_compiler", "utility", "adversary",
           "session_accounting", "frontier", "fidelity", "observer_capacity", "response", "intent",
           "consistency", "identifiability", "DisclosurePolicy", "POLICIES", "compile_observation",
           "participation_utility", "leakage_bits", "evaluate", "funnel_frontier",
           "crucible", "demo", "MeasurementResult"]


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception", OBSERVER, mutates_core=False,
                          note="the first complete perception loop: world → DisclosurePolicy → compiled "
                               "observation → agent → task → leakage (QIF). the repo's first utility/leakage "
                               "frontier; composition of M10–M21 + channel_discovery, not a law")
    except LayerViolation:
        pass
