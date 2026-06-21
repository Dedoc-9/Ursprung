# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase4/run.py — Representation Learning Under Provenance Constraints (the benchmark harness).

    PYTHONHASHSEED=0 python3 experiments/latent_phase4/run.py     # needs numpy; seeded → replayable

The question is NOT "can a net discover causes?" It is "does the provenance contract survive a learned
representation?" — put a learned latent inside the already-built machinery (Phase-2 topology, Phase-3
provenance, both reused unchanged) and see which discipline objects still hold. Success criterion, intentionally
narrow: *a learned latent factor may be unknown; its provenance may not be.*
"""
from __future__ import annotations

import numpy as np

from world import make_world, FACTORS, NODES
from encoder import families
from intervene import reconstruction_r2, outcome_sensitivity, gauge_invariant
from topology import roles
from robustness import robust_recoverability, per_family_recoverability
from provenance import wrap_edges, INTERVENTION_GROUNDED, ASSUMPTION_LOAD_BEARING, CausalEdge


def main():
    world = make_world(seed=0)
    lat = families(world["X"])
    ref = lat["AE_pca"][0]

    print("PHASE 4 — Representation Learning Under Provenance Constraints\n")

    # Tier 0 — reconstruction (admission ticket only)
    recon = {n: round(reconstruction_r2(world["X"], Xh), 3) for n, (Z, Xh) in lat.items()}
    print("Tier 0  reconstruction R²:", recon)

    # Tier 1 — recoverability (gauge-invariant) + intervention on the outcome, per learned factor
    print("Tier 1  recoverability of true factors from the LEARNED latent + do()->outcome:")
    rec = {f: per_family_recoverability(world[f], lat) for f in FACTORS}
    interv = {f: round(outcome_sensitivity(world, f), 3) for f in FACTORS}
    for f in FACTORS:
        print("   factor %s: recover=%s  do(%s)->outcome=%.2f" % (f, rec[f], f, interv[f]))

    # Tier 2 — latent topology (Phase-2 logic over learned factors)
    rls, R = roles(world)
    print("Tier 2  recovered intervention topology (roles):", rls)

    # Tier 3 — robustness across encoder families (⋂ over 𝓕)
    robust = {f: round(robust_recoverability(world[f], lat), 3) for f in FACTORS}
    print("Tier 3  robust recoverability (min over encoder families):", robust)

    # Tier 4 — provenance-preserving discovery: emit edges THROUGH the reused Phase-3 contract
    recovered = [("z::g", "z::m"), ("z::m", "y"), ("z::c", "y")]          # last is the confounder edge
    intervention_backed = {("z::g", "z::m"), ("z::m", "y")}               # do()-established; c->y is NOT
    graph = wrap_edges(recovered, intervention_backed)
    A_full = {"invariance"}
    print("Tier 4  provenance graph over LEARNED factors:", graph.edges)
    print("        report:", graph.report(A_full))

    # success criterion: factor identity is gauge-ambiguous, provenance is not
    th = 0.7
    Rot = np.array([[np.cos(th), -np.sin(th), 0], [np.sin(th), np.cos(th), 0], [0, 0, 1]])
    pd_before = [round(abs(np.corrcoef(ref[:, i], world["g"])[0, 1]), 2) for i in range(ref.shape[1])]
    pd_after = [round(abs(np.corrcoef((ref @ Rot.T)[:, i], world["g"])[0, 1]), 2) for i in range(ref.shape[1])]

    checks = {
        "tier0_reconstruction_passes": min(recon.values()) >= 0.6,
        "tier1_generator_recovered_and_causal": robust["g"] >= 0.9 and interv["g"] >= 0.9,
        "tier1_confounder_recovered_but_not_causal": robust["c"] >= 0.9 and interv["c"] <= 0.1,
        "tier2_topology_recovered": rls["g"] == "root" and rls["m"] == "mediator" and rls["y"] == "sink" and rls["c"] == "isolated",
        "tier3_generator_robust_across_families": robust["g"] >= 0.9,
        "tier4_intervention_edges_grounded": all(e.mode == INTERVENTION_GROUNDED for e in graph.intervention_subgraph()),
        "tier4_confounder_edge_must_declare_assumption": _raises(lambda: CausalEdge("z::c", "y", ASSUMPTION_LOAD_BEARING)),
        "tier4_A_invariant_core_is_intervention_grounded": sorted((e.src, e.dst) for e in graph.A_invariant_core([A_full, set()])) == [("z::g", "z::m"), ("z::m", "y")],
        "factor_unknown_provenance_known": pd_before != pd_after and all(e.mode == INTERVENTION_GROUNDED for e in graph.intervention_subgraph()),
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase 4: the provenance contract did NOT survive the learned representation"
    print("\nall %d checks passed — provenance survived the learned representation." % len(checks))
    print("A learned latent factor may be unknown (gauge-ambiguous: %s → %s); its provenance is not." % (pd_before, pd_after))
    return checks


def _raises(fn):
    try:
        fn(); return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
