# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase4/provenance.py — wrap recovered edges in the Phase-3 contract, UNCHANGED.

The whole experiment: the Phase-3 `CausalEdge` / `ProvenanceGraph` are imported and reused exactly as written —
no edits for the learned case. If the discipline objects still hold with learned-factor nodes, the contract
survived ML; if they would need loosening, the contract was too symbolic. They hold.

`wrap_edges` emits an edge only through the contract: an intervention-grounded edge requires a real do() that
moved the child; any edge not so grounded must be `assumption_load_bearing` with a declared assumption — the
constructor refuses anything else. So a learned system *cannot* emit a bare edge: its atomic output is
`edge + provenance + admissibility boundary`, even when the latent factor's semantic identity is unknown.
"""
from __future__ import annotations

import importlib.util
import os

# import Phase 3's contract unchanged (by path, to avoid a same-name clash)
_p3_path = os.path.join(os.path.dirname(__file__), "..", "latent_phase3", "provenance.py")
_spec = importlib.util.spec_from_file_location("phase3_provenance", _p3_path)
_p3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_p3)

CausalEdge = _p3.CausalEdge
ProvenanceGraph = _p3.ProvenanceGraph
INTERVENTION_GROUNDED = _p3.INTERVENTION_GROUNDED
ASSUMPTION_LOAD_BEARING = _p3.ASSUMPTION_LOAD_BEARING


def wrap_edges(recovered, intervention_backed):
    """`recovered`: list of (src, dst). `intervention_backed`: set of (src, dst) a real do() established.
    Edges in the backed set are emitted intervention_grounded; the rest can only be emitted as
    assumption_load_bearing with a declared assumption — the Phase-3 constructor enforces it."""
    edges = []
    for (src, dst) in recovered:
        if (src, dst) in intervention_backed:
            edges.append(CausalEdge(src, dst, INTERVENTION_GROUNDED))
        else:
            edges.append(CausalEdge(src, dst, ASSUMPTION_LOAD_BEARING, {"type": "invariance"}))
    return ProvenanceGraph(edges)
