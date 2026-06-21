# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase2/run.py — Phase 2: recover the intervention topology; separate root from mediator.

    PYTHONHASHSEED=0 python3 experiments/latent_phase2/run.py     # needs numpy; seeded → replayable

Phase 1 caught the confounder with the intervention gate but could not tell a root from a mediator (both are
causally relevant). Phase 2 recovers the *topology* from intervention asymmetries and shows that topology is
exactly what separates them. The asserts are the verification (numpy-dependent, outside the stdlib suite).
"""
from __future__ import annotations

from world import make_world, NODES
from topology import topology_report


def main():
    world = make_world(seed=0)
    r = topology_report(world, outcome="y")
    R, rls, rel = r["response"], r["roles"], r["relevant_to_outcome"]

    print("PHASE 2 — topology discovery (where in the intervention graph does each factor sit?)\n")
    print("intervention asymmetries  do(i) → moves j:")
    for i in NODES:
        print("   do(%s) → %s" % (i, {j: R[i][j] for j in NODES if j != i}))
    print("\nrecovered roles:  %s" % rls)
    print("Tier 2 (relevant to outcome y):  %s" % rel)

    print("\nVERDICT")
    print("  g and x are BOTH relevant to the outcome (Tier 2 passes for both) — Tier 2 cannot separate them.")
    print("  Topology (Tier 3) does: g is the ROOT (moved by none, moves all), x is a MEDIATOR (moved by g),")
    print("  y is the SINK, c is ISOLATED (observed but not in the causal chain).")
    print("  survives intervention ≠ root generator — the mediator passes Tier 2 and is placed below the root.")
    print("\n  HONEST: recovered topology ≠ discovered ontology — a graph over declared latent factors under 𝓕,")
    print("  assuming a real do(). With an unknown graph / no free intervention, topology recovery is the frontier.")

    checks = {
        "asymmetry_do_g_moves_x_and_y": R["g"]["x"] and R["g"]["y"] and not R["g"]["c"],
        "asymmetry_do_x_moves_y_not_g": R["x"]["y"] and not R["x"]["g"],
        "asymmetry_do_y_moves_nothing": not any(R["y"].values()),
        "asymmetry_do_c_moves_nothing": not any(R["c"].values()),
        "root_is_g": rls["g"] == "root",
        "mediator_is_x": rls["x"] == "mediator",
        "sink_is_y": rls["y"] == "sink",
        "isolated_is_c": rls["c"] == "isolated",
        "both_relevant_only_topology_separates": rel["g"] and rel["x"] and rls["g"] != rls["x"],
        "mediator_passes_tier2_but_is_not_root": rel["x"] and rls["x"] != "root",
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase 2 topology recovery did not hold"
    print("\nall %d checks passed — topology recovered; root distinguished from mediator by intervention asymmetry." % len(checks))
    return r


if __name__ == "__main__":
    main()
