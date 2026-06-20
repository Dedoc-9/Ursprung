# SPDX-License-Identifier: AGPL-3.0-only
"""
Ursprung — a deterministic high-fidelity renderer built as a read-only consumer of the sealed
Reality_Engine (Chronicle/Dentatus) workbench.

Pipeline:  authoritative world state → deterministic snapshot → visual interpretation → (GPU) → frame

Layer map (see registry.py):  CORE (world_core) · VIEW (view_layer) · OBSERVER (ghost_report, verify).
ALLOCATOR layers (LOD/culling/quality) come in a later milestone.

The workbench is the VERIFICATION SUBSTRATE, not the renderer. Only CORE may move committed state.
"""
from . import (world_core, view_layer, ghost_report, verify, registry,  # noqa: F401
               render_record, conventions, divergence, prediction, temporal_membrane,
               pfal_bench, tcff, polygon_reconciliation, fidelity_conservation, reality_debt,
               causal_continuity, raster, raster_bench, representation, allocation,
               perceptual, policy_arena, stress, transition_debt, adversarial_scenes,
               resistance_tensor, shader_cache, causal_surface, readiness,
               causal_contract, representation_futures, causal_mutation, provider_contract,
               dependency_surface, dependency_integrity, representation_compiler,
               capability, causal_access)

__all__ = ["world_core", "view_layer", "ghost_report", "verify", "registry",
           "render_record", "conventions", "divergence", "prediction",
           "temporal_membrane", "pfal_bench", "tcff", "polygon_reconciliation",
           "fidelity_conservation", "reality_debt", "causal_continuity", "raster", "raster_bench",
           "representation", "allocation", "perceptual", "policy_arena", "stress",
           "transition_debt", "adversarial_scenes", "resistance_tensor", "shader_cache",
           "causal_surface", "readiness", "causal_contract", "representation_futures",
           "causal_mutation", "provider_contract", "dependency_surface",
           "dependency_integrity", "representation_compiler", "capability", "causal_access"]
__version__ = "0.1.0-milestone1"