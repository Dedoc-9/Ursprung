# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase5/run.py — Provenance-Preserving Learning: representation is free, status is conserved.

    PYTHONHASHSEED=0 python3 experiments/latent_phase5/run.py     # needs numpy; seeded → replayable

Not "find the truth." The goal is representations whose claims remain inspectable after learning — and the
developer is a NAMED component of the object, not a hidden author. Tests: creator visibility, intervention
honesty, assumption locality, representation humility, and the closed scale gauge.
"""
from __future__ import annotations

from representation import make_world, build_representation


def main():
    world = make_world(seed=0)

    # two encoders → different latent COORDINATES, same factors recovered
    rep_a = build_representation(world, "AE_seed11", seed=11)
    rep_b = build_representation(world, "AE_seed22", seed=22)
    # a degenerate encoder (k=1) cannot recover all factors
    rep_deg = build_representation(world, "AE_k1", k=1, seed=33)
    # a representation built on a per-column-rescaled observable (a scale gauge transform)
    import numpy as np
    world_scaled = make_world(seed=0, scale=np.linspace(0.1, 10, 10))
    rep_scaled = build_representation(world_scaled, "AE_seed11_rescaled", seed=11)
    # same encoder, but the developer declares NO intervention access (only assumptions)
    rep_no_access = build_representation(world, "AE_seed11_no_access", seed=11, intervention_access=())

    print("PHASE 5 — Provenance-Preserving Learning\n")
    print("rep_a  per-dim identity %s  claim %s" % (rep_a.per_dim_identity(), rep_a.claim()))
    print("rep_b  per-dim identity %s  claim %s" % (rep_b.per_dim_identity(), rep_b.claim()))
    print("rep_deg (k=1) claim: %s" % rep_deg.claim())
    print("rep_scaled claim: %s   rep_no_access claim: %s" % (rep_scaled.claim(), rep_no_access.claim()))
    print("manifest(rep_a): %s" % rep_a.manifest)

    checks = {
        # 1. creator visibility — the manifest traces the declared choices; changing one changes its identity
        "creator_visibility": rep_a.manifest_digest() != rep_no_access.manifest_digest(),
        # 2. intervention honesty — declared access changes which edges are grounded vs assumed
        "intervention_honesty": rep_a.claim() != rep_no_access.claim(),
        # 3. assumption locality — every assumption-load-bearing edge names its assumption (Phase-3 invariant)
        "assumption_locality": all(e.assumption and e.assumption.get("type")
                                   for e in rep_no_access.provenance_graph().assumption_subgraph()),
        # 4a. representation humility — different latents, SAME provenance-qualified claim → equivalent
        "representation_humility_equivalent": (rep_a.per_dim_identity() != rep_b.per_dim_identity()
                                               and rep_a.claim() == rep_b.claim()),
        # 4b. a representation that cannot support the claims is NOT equivalent
        "degenerate_not_equivalent": rep_deg.claim() != rep_a.claim() and rep_deg.claim().startswith("INCOMPLETE"),
        # the scale gauge is closed — per-column rescaling does not change the claim
        "scale_gauge_closed": rep_scaled.claim() == rep_a.claim(),
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase 5: provenance did not survive as the representation-invariant identity"
    print("\nall %d checks passed — representation is free; epistemic status is conserved." % len(checks))
    print("The latent is the coordinate system; the provenance-qualified claim is the identity.")
    return checks


if __name__ == "__main__":
    main()
