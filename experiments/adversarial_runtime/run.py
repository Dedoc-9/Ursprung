# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/adversarial_runtime/run.py — attack the declarations; keep the corpses.

    python3 experiments/adversarial_runtime/run.py     # stdlib only; deterministic

The non-entrenchment runtime: weaponize declared≠verified, inject structural contradiction, run adversarial
survival tests and bury what dies, and anchor what can be anchored — with the loud honest bound that a software
anchor is tamper-evident ordering, not physical irreversibility.
"""
from __future__ import annotations

from adversarial import (Artifact, weaponize, verifiable_status, ParadoxEngine,
                         NecroRegistry, survives, ExternalAnchor)


def main():
    honest = Artifact("CausalEdge", ("g", "y"), interventions=["do(g)"], status="verified")
    laundered = Artifact("CausalEdge", ("g", "y"), status="verified")            # claims verified, no evidence
    assumed = Artifact("EstimatorOutput", ("c", "y"), declared_assumptions=["invariance"], status="assumed")
    paradox = ParadoxEngine.make_paradox()

    print("ADVERSARIAL RUNTIME — attack the declarations, keep the corpses\n")

    # 1. weaponize
    print("1. weaponize declared≠verified:")
    print("   honest    :", weaponize(honest))
    print("   laundered :", weaponize(laundered))

    # 2. paradox engine
    con = ParadoxEngine.contradictions([honest, paradox, assumed,
                                        Artifact("CausalEdge", ("g", "y"), declared_assumptions=["x"], status="assumed")])
    print("\n2. structural contradictions:", con)

    # 3. necro-registry
    necro = NecroRegistry()
    necro.run_survival(honest, [("swap_encoder",), ("change_environment",)])     # survives both (intervention-grounded)
    necro.run_survival(assumed, [("remove_assumption", "invariance")])           # dies
    print("\n3. necro-registry epitaphs:", necro.epitaphs())

    # 4. external anchor
    anchor = ExternalAnchor()
    dA = anchor.commit(honest.digest()); dB = anchor.commit(assumed.digest())
    fresh = ExternalAnchor(); fresh.commit(honest.digest())
    print("\n4. anchor: A precedes B =", anchor.precedes(honest.digest(), assumed.digest()),
          "| chain valid =", anchor.verify(), "| reproducible(not physically irreversible) =", fresh.chain[0]["anchor"] == anchor.chain[0]["anchor"])

    checks = {
        "1_weaponize_catches_laundering": weaponize(laundered)["laundering"] and not weaponize(honest)["laundering"],
        "1_verifiable_status_ignores_declaration": verifiable_status(laundered) == "unknown" and verifiable_status(honest) == "verified",
        "2_paradox_verified_without_evidence": any(c[0] == "verified_without_evidence" for c in con),
        "2_paradox_same_claim_contradictory_status": any(c[0] == "same_claim_contradictory_status" for c in con),
        "3_intervention_edge_survives_perturbation": survives(honest, ("swap_encoder",)) and survives(honest, ("change_environment",)),
        "3_assumption_edge_dies_when_assumption_removed": not survives(assumed, ("remove_assumption", "invariance")),
        "3_necro_preserves_the_dead_with_cause": len(necro.epitaphs()) == 1 and "remove_assumption" in necro.epitaphs()[0]["cause_of_death"],
        "4_anchor_proves_ordering": anchor.precedes(honest.digest(), assumed.digest()) and not anchor.precedes(assumed.digest(), honest.digest()),
        "4_anchor_is_tamper_evident": anchor.verify() and not _tampered(anchor),
        "4_software_anchor_is_reproducible_not_physically_irreversible": fresh.chain[0]["anchor"] == anchor.chain[0]["anchor"],
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "adversarial runtime did not hold"
    print("\nall %d checks passed — the declarations were attacked; what survived is marked, what died is kept." % len(checks))
    return checks


def _tampered(anchor):
    """Tamper with a copy's first entry and confirm verification fails (the chain is tamper-evident)."""
    import copy
    c = copy.deepcopy(anchor)
    if not c.chain:
        return False
    c.chain[0]["digest"] = "FORGED"
    return c.verify()


if __name__ == "__main__":
    main()
