# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/provenance_runtime/run.py — Phase R: the prior phases as one artifact identity system.

    python3 experiments/provenance_runtime/run.py     # stdlib only; deterministic

The test is NOT "does it discover better?" It is: can a developer change the representation, model, estimator,
or assumptions WITHOUT losing the history of what made the result admissible? Plus the runtime invariants:
identity includes provenance, transform inherits provenance, compare is over claims not representations, audit
separates assumed from demonstrated, and every prior phase migrates onto one `Artifact`.
"""
from __future__ import annotations

from artifact import Artifact


def migrate():
    """The prior phases, as artifact types — one identity system, not separate projects."""
    return {
        "GroundedClaim": Artifact("GroundedClaim", "X is best surviving explanation",
                                  creator_manifest={"floor": "declared"}, declared_assumptions=["floor"], status="survived"),
        "Coordinate": Artifact("Coordinate", {"integrity": 1.0, "adequacy": 0.0}, status="unknown"),  # ledgers
        "Representation": Artifact("Representation", "claim_a0939bb7984a",
                                   creator_manifest={"encoder": "AE_pca", "objective": "reconstruction"},
                                   model_family=["AE"], status="survived"),
        "CausalEdge": Artifact("CausalEdge", ("g", "y"), interventions=["do(g)"], status="verified"),
        "EstimatorOutput": Artifact("EstimatorOutput", ("g", "y"), declared_assumptions=["instrument_validity"],
                                    admissibility_set=["invariance"], status="assumed"),
    }


def main():
    arts = migrate()
    rep = arts["Representation"]
    edge = arts["CausalEdge"]
    est = arts["EstimatorOutput"]

    # the developer swaps the encoder; the claim is preserved, the change is recorded
    rep2 = rep.transform("swap_encoder", creator_manifest={"encoder": "AE_mlp", "objective": "reconstruction"})

    # same content, different provenance → different object
    edge_assumed = Artifact("CausalEdge", ("g", "y"), declared_assumptions=["invariance"], status="assumed")

    print("PHASE R — provenance runtime (one artifact, every prior phase a type)\n")
    for name, a in arts.items():
        print("   %-16s digest=%s claim=%s status=%s" % (name, a.digest(), a.claim_digest(), a.status))
    print("\n   swap encoder: rep %s → rep2 %s   (claim %s preserved, history %s)"
          % (rep.digest(), rep2.digest(), rep2.claim_digest(), rep2.provenance["transformation_history"]))
    print("   audit(EstimatorOutput):", est.audit())

    checks = {
        # the central test the runtime exists for
        "developer_can_swap_representation_without_losing_history":
            rep.compare(rep2)["claim_equivalent"] and not rep.compare(rep2)["same_full_identity"]
            and rep.compare(rep2)["shared_history"],
        # runtime invariants
        "identity_includes_provenance": edge.content == edge_assumed.content and edge.digest() != edge_assumed.digest(),
        "transform_inherits_provenance": rep.digest() in rep2.provenance["dependencies"]
            and rep2.provenance["transformation_history"] == ["swap_encoder"],
        "compare_is_over_claims_not_representations": rep.claim_digest() == rep2.claim_digest(),
        "audit_separates_assumed_from_demonstrated": edge.audit()["demonstrated"] == ["do(g)"]
            and edge.audit()["assumed"] == [] and est.audit()["assumed"] == ["instrument_validity"] and est.audit()["unverified"],
        "creator_is_a_provenance_source": rep.digest() != rep.transform("relabel", creator_manifest={"encoder": "AE_pca", "objective": "contrastive"}).digest(),
        "status_is_typed": arts["Coordinate"].status == "unknown" and est.status == "assumed" and edge.status == "verified",
        "all_phases_migrate_to_one_identity_system": len({a.digest() for a in arts.values()}) == len(arts)
            and all(a.claim_digest() for a in arts.values()),
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase R: the provenance runtime did not hold"
    print("\nall %d checks passed — one identity system; the model is a plugin, the artifact contract is not." % len(checks))
    return checks


if __name__ == "__main__":
    main()
