# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase3/run.py — Phase 3 (discipline-first): a provenance benchmark, not an estimator one.

    python3 experiments/latent_phase3/run.py     # stdlib only; deterministic

The tests verify the DISCIPLINE before any claim of improved causal recovery: that support provenance is part
of a graph's identity, that an admissibility boundary 𝓐 governs which edges survive, that the
intervention-grounded and assumption-load-bearing subgraphs stay distinguishable, and that the report can
quantify how much of the graph each kind of support carries. The estimator questions (which IV? which
invariance test?) are intentionally left open — they are not what this layer is for.
"""
from __future__ import annotations

from provenance import (CausalEdge, ProvenanceGraph,
                        INTERVENTION_GROUNDED as IG, ASSUMPTION_LOAD_BEARING as AB)


def example_graph():
    """g→x→y recovered by intervention (Phase 2); z→y and w→y recoverable only under declared assumptions."""
    return ProvenanceGraph([
        CausalEdge("g", "x", IG),
        CausalEdge("x", "y", IG),
        CausalEdge("z", "y", AB, {"type": "invariance"}),          # recovered via invariance across environments
        CausalEdge("w", "y", AB, {"type": "instrument_validity"}),  # recovered via an instrumental variable
    ])


def main():
    G = example_graph()
    A_full = {"invariance", "instrument_validity"}
    A_minus_inv = {"instrument_validity"}

    # a graph with the SAME adjacency but g→x demoted to assumption-backed
    G2 = ProvenanceGraph([
        CausalEdge("g", "x", AB, {"type": "invariance"}),
        CausalEdge("x", "y", IG),
        CausalEdge("z", "y", AB, {"type": "invariance"}),
        CausalEdge("w", "y", AB, {"type": "instrument_validity"}),
    ])

    print("PHASE 3 — edge provenance (support is part of a causal graph's identity)\n")
    print("graph:", G.edges)
    print("digest(𝓐=full):           ", G.digest(A_full))
    print("digest(same adjacency, g→x assumed):", G2.digest(A_full), " (different object)")
    print("surviving under 𝓐=full:        ", G.surviving(A_full))
    print("surviving under 𝓐 without invariance:", G.surviving(A_minus_inv), " (z→y dropped)")
    rep = G.report(A_full)
    print("report(𝓐=full):", rep)
    core = G.A_invariant_core([A_full, A_minus_inv, set()])
    print("𝓐-invariant core (survives every 𝓐):", core, " = the intervention-grounded subgraph")

    checks = {
        # the user's four provenance tests
        "1_provenance_changes_identity": G.digest(A_full) != G2.digest(A_full),
        "2_removing_assumption_removes_edge": (any(e.src == "z" for e in G.surviving(A_full))
                                               and not any(e.src == "z" for e in G.surviving(A_minus_inv))),
        "3_subgraphs_distinguishable": (set(map(id, G.intervention_subgraph())).isdisjoint(map(id, G.assumption_subgraph()))
                                        and len(G.intervention_subgraph()) + len(G.assumption_subgraph()) == len(G.edges)),
        "4_report_quantifies_provenance": rep["intervention_backed"] == 2 and rep["assumption_backed"] == 2 and rep["intervention_fraction"] == 0.5,
        # the discipline invariants
        "edge_requires_declared_assumption": _raises(lambda: CausalEdge("a", "b", AB)),
        "intervention_grounded_is_A_invariant_core": sorted((e.src, e.dst) for e in core) == [("g", "x"), ("x", "y")],
        "no_assumed_edge_wears_intervened_label": (all(e.support_label() == AB for e in G.assumption_subgraph())
                                                   and all(e.support_label() == IG for e in G.intervention_subgraph())),
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase 3 provenance discipline did not hold"
    print("\nall %d checks passed — support is part of identity; assumptions cannot masquerade as interventions." % len(checks))
    return checks


def _raises(fn):
    try:
        fn(); return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
