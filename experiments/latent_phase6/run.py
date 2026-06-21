# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase6/run.py — the inference contract: what did you spend for this edge?

    python3 experiments/latent_phase6/run.py     # stdlib only; deterministic

Discipline-first, no estimator. The tests verify the contract that forces an estimator to expose its exchange
rate before any estimator exists to be tempted otherwise: no free inference, same edge / different price /
different identity, accuracy cannot upgrade provenance, domain is part of the claim, cost composes, and cost is
a ledger not a scalar.
"""
from __future__ import annotations

from estimator_output import IdentificationCost, EstimatorOutput, InferenceBudget


def _raises(fn):
    try:
        fn(); return False
    except ValueError:
        return True


def main():
    # same edge, two different prices
    e_do = EstimatorOutput(("g", "y"), IdentificationCost(interventions=["do(g)"]), {"env0"})
    e_assume = EstimatorOutput(("g", "y"), IdentificationCost(assumptions=["instrument_validity"]), {"env0"})
    # same edge + price, different confidence domain
    e_dom1 = EstimatorOutput(("g", "y"), IdentificationCost(interventions=["do(g)"]), {"env0"})
    e_dom2 = EstimatorOutput(("g", "y"), IdentificationCost(interventions=["do(g)"]), {"env0", "env1"})
    # a graph with mixed provenance economy
    budget = InferenceBudget([
        EstimatorOutput(("a", "b"), IdentificationCost(interventions=["do(a)"]), {"env0"}),
        EstimatorOutput(("b", "c"), IdentificationCost(assumptions=["invariance"]), {"env0"}),
        EstimatorOutput(("c", "d"), IdentificationCost(assumptions=["instrument_validity"],
                                                       unverified_dependencies=["exclusion_restriction"]), {"env0"}),
    ])
    rep = budget.report()

    print("PHASE 6 — the inference contract (no edge without its price)\n")
    print("same edge 'g→y':  via do()  digest=%s   via assumption  digest=%s   (different objects)"
          % (e_do.digest(), e_assume.digest()))
    print("InferenceBudget report:", {k: rep[k] for k in ("intervention_purchased", "assumption_purchased", "mixed")})
    print("composed cost ledger:", rep["composed_cost"])

    checks = {
        # 1. no free inference — a cost is mandatory at construction
        "1_no_free_inference": _raises(lambda: EstimatorOutput(("g", "y"), IdentificationCost(), {"env0"})),
        # 2. same edge, different price → different identity
        "2_same_edge_different_price_different_identity": e_do.edge == e_assume.edge and e_do.digest() != e_assume.digest(),
        # 3. accuracy cannot upgrade provenance — high accuracy with no cost is still invalid; accuracy isn't required
        "3_accuracy_cannot_upgrade_provenance": _raises(lambda: EstimatorOutput(("g", "y"), IdentificationCost(), {"env0"}, accuracy=0.99)) and e_do.accuracy is None,
        # 4. domain is part of the claim
        "4_domain_is_part_of_claim": e_dom1.digest() != e_dom2.digest(),
        # 5. cost composes into a graph-level ledger
        "5_cost_composes": rep["intervention_purchased"] == 1 and rep["assumption_purchased"] == 2,
        # 6. cost is a ledger, not a scalar — same count, different KIND is distinguishable
        "6_cost_is_a_ledger_not_a_scalar": IdentificationCost(interventions=["x"]).digest() != IdentificationCost(assumptions=["y"]).digest(),
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase 6: the inference contract did not hold"
    print("\nall %d checks passed — every edge declares the price it was bought with; accuracy ≠ identifiability." % len(checks))
    return checks


if __name__ == "__main__":
    main()
