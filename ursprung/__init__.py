# SPDX-License-Identifier: AGPL-3.0-only
"""
Ursprung — a deterministic high-fidelity renderer built as a read-only consumer of the sealed
Reality_Engine (Chronicle/Dentatus) workbench.

Pipeline:  authoritative world state → deterministic snapshot → visual interpretation → (GPU) → frame

Layer map (see registry.py):  CORE (world_core) · VIEW (view_layer, raster) · ALLOCATOR (temporal_membrane,
tcff, allocation, shader_cache, readiness, representation_futures, representation_compiler) · OBSERVER
(everything that measures/ranks/attributes — prediction, the law modules, the information-firewall arc, and
the harnesses). Only CORE may move committed state.

Two arcs over one verified world: (1) rendering economics — finite fidelity is a budget, every approximation
is debt, priority ≠ allocation; (2) the information firewall — the renderer must not become an oracle for
hidden state (see README's "second arc" and docs/MEASUREMENT_DISCIPLINE.md). The workbench is the
VERIFICATION SUBSTRATE, not the renderer.
"""
from . import (world_core, view_layer, ghost_report, verify, registry,  # noqa: F401
               render_record, conventions, divergence, prediction, temporal_membrane,
               pfal_bench, tcff, polygon_reconciliation, fidelity_conservation, reality_debt,
               causal_continuity, raster, raster_bench, representation, allocation,
               perceptual, policy_arena, stress, transition_debt, adversarial_scenes,
               resistance_tensor, shader_cache, causal_surface, readiness,
               causal_contract, representation_futures, causal_mutation, provider_contract,
               dependency_surface, dependency_integrity, representation_compiler,
               capability, causal_access, reconstruction, side_channel, accumulation,
               adversarial_dynamics, representation_privacy, execution_surface, convergence,
               reality_harness, behavioral_harness, adversary_harness, adversary_capacity,
               channel_discovery, disclosure)
from . import perception  # the first complete perception loop (subpackage)

__all__ = ["world_core", "view_layer", "ghost_report", "verify", "registry",
           "render_record", "conventions", "divergence", "prediction",
           "temporal_membrane", "pfal_bench", "tcff", "polygon_reconciliation",
           "fidelity_conservation", "reality_debt", "causal_continuity", "raster", "raster_bench",
           "representation", "allocation", "perceptual", "policy_arena", "stress",
           "transition_debt", "adversarial_scenes", "resistance_tensor", "shader_cache",
           "causal_surface", "readiness", "causal_contract", "representation_futures",
           "causal_mutation", "provider_contract", "dependency_surface",
           "dependency_integrity", "representation_compiler", "capability", "causal_access",
           "reconstruction", "side_channel", "accumulation", "adversarial_dynamics",
           "representation_privacy", "execution_surface", "convergence", "reality_harness",
           "behavioral_harness", "adversary_harness", "adversary_capacity", "channel_discovery",
           "disclosure", "perception"]
__version__ = "0.32.0"