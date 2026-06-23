# SPDX-License-Identifier: AGPL-3.0-only
"""
discrimination_matrix.py — rank experiments by how much uncertainty they COLLAPSE, not by cost or precision,
and gate them behind a prediction-commitment check.

When several hypotheses fit the same observable, the convergence object labels the axis `INTERVENTION_ONLY`
(observation underdetermines it). The way out is the red-team move: find a manipulation whose predictions
*diverge*. This instrument scores that — and distinguishes two reasons a cell is empty:

    UNKNOWN         — WE have not worked out this hypothesis's prediction yet (a gap on our side; cheap to fill).
    UNDERCOMMITTED  — the HYPOTHESIS itself refuses/fails to specify a prediction (a defect on the theory's
                      side; NO future observation can discriminate a theory that will not commit).

Both block discrimination, opposite actions: fill an `UNKNOWN` (cheap simulation); *demand commitment for* an
`UNDERCOMMITTED` (a workshop). Honest guard: **`UNDERCOMMITTED` ≠ false** — an uncommitted theory is *set aside
as non-discriminable*, never refuted (`absence of evidence ≠ evidence of absence`).

TWO RANKING METRICS (primary + secondary):
  * `epistemic_value`  = number of hypothesis PAIRS forced into mutually-exclusive predictions (DECLARED→MBI).
  * `partition_entropy` (collapse power) = Shannon entropy of the COMMITTED-hypothesis outcome partition. Not all
     separations are equal: an experiment that splits hypotheses into many, evenly-sized outcome classes collapses
     uncertainty more aggressively than one that barely splits them. Bounded above by `log2(#committed)` — an
     experiment can collapse no more uncertainty than the committed hypotheses contain, so uncommitted theories
     LOWER the ceiling for the whole program.

Discipline: a prediction cell is `DECLARED` (a model output, never a measurement — Rule 5: a simulation is a
witness). Neither `UNKNOWN` nor `UNDERCOMMITTED` ever counts as separation. The output is an ALLOCATION of
investigation, never a verdict. `partition_entropy` uses string-equality outcome classes — a coarse proxy that
does NOT model whether two *different* predictions are experimentally resolvable (that is the measurement-
resolution / occlusion axis, separate from partition power); collapse power is therefore an *upper bound* on
realized discriminating power.

Run (from this directory):  PYTHONHASHSEED=0 python3 discrimination_matrix.py
"""
from __future__ import annotations

import math
from itertools import combinations

# The epistemic-status vocabulary is canonically defined ONCE in reality_status.py (single source of truth,
# shared with reconcile_status / witness_panel / runtime_witness). Import it when available; fall back to a
# *declared* local mirror ONLY when running standalone — never a silent fork (`compress ≠ sever`). In-repo the
# import always wins, so the two never diverge; the fallback exists solely so the file runs in isolation.
try:
    from reality_status import DECLARED, MEASURED_BY_INTERVENTION
except ImportError:                                   # standalone fallback — MUST mirror reality_status.py
    DECLARED = "DECLARED"
    MEASURED_BY_INTERVENTION = "MEASURED_BY_INTERVENTION"


class _State:
    """A non-prediction cell state. Distinct objects so neither collides with a real prediction string."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


UNKNOWN = _State("UNKNOWN")               # our gap — fill it cheaply (a simulation)
UNDERCOMMITTED = _State("UNDERCOMMITTED")  # the theory's defect — demand commitment, or set aside (not refute)


def is_committed(cell_value) -> bool:
    """A cell carries a usable prediction iff it is neither UNKNOWN nor UNDERCOMMITTED."""
    return cell_value is not UNKNOWN and cell_value is not UNDERCOMMITTED


def cell(preds: dict, experiment, hypothesis):
    return preds.get((experiment, hypothesis), UNKNOWN)   # absent ⇒ UNKNOWN (not recorded ≠ theory refused)


def separates(preds: dict, experiment, h1, h2) -> bool:
    """True iff BOTH hypotheses commit a prediction under this experiment AND the predictions differ."""
    p1, p2 = cell(preds, experiment, h1), cell(preds, experiment, h2)
    return is_committed(p1) and is_committed(p2) and p1 != p2


def epistemic_value(preds: dict, experiment, hypotheses) -> int:
    """Primary metric: hypothesis pairs separated = DECLARED→MEASURED_BY_INTERVENTION conversions."""
    return sum(1 for h1, h2 in combinations(hypotheses, 2) if separates(preds, experiment, h1, h2))


def separated_pairs(preds: dict, experiment, hypotheses) -> list:
    return [(h1, h2) for h1, h2 in combinations(hypotheses, 2) if separates(preds, experiment, h1, h2)]


# --- secondary metric: collapse power (how aggressively the hypothesis space is partitioned) ---
def outcome_classes(preds: dict, experiment, hypotheses) -> dict:
    """Partition the COMMITTED hypotheses into outcome-equivalence classes (same predicted observable → same
    class). UNKNOWN/UNDERCOMMITTED are EXCLUDED — an experiment cannot partition a theory that does not predict.
    NOTE: 'same outcome' = string-identical prediction; a coarse proxy that does NOT model experimental
    resolvability of two *different* predictions (the measurement-resolution axis, separate from partition power)."""
    classes: dict = {}
    for h in hypotheses:
        c = cell(preds, experiment, h)
        if is_committed(c):
            classes.setdefault(c, []).append(h)
    return classes


def outcome_diversity(preds: dict, experiment, hypotheses) -> int:
    """Number of distinct committed outcomes — how many distinguishable futures the experiment predicts."""
    return len(outcome_classes(preds, experiment, hypotheses))


def partition_entropy(preds: dict, experiment, hypotheses) -> float:
    """Shannon entropy (bits) of the committed-hypothesis outcome partition = 'collapse power'. High when the
    experiment splits the committed hypotheses into many, EVENLY-sized classes; 0.0 with ≤1 committed class.
    Bounded above by log2(#committed)."""
    classes = outcome_classes(preds, experiment, hypotheses)
    n = sum(len(v) for v in classes.values())
    if n <= 1:
        return 0.0
    return -sum((len(m) / n) * math.log2(len(m) / n) for m in classes.values())


def committed_ceiling(preds: dict, experiments, hypotheses) -> float:
    """Program-wide ceiling on collapse power: log2(# hypotheses that commit ANYWHERE). Uncommitted theories
    lower this for EVERY experiment — commitment raises the ceiling; measurement only realizes up to it."""
    committed = [h for h in hypotheses if any(is_committed(cell(preds, e, h)) for e in experiments)]
    return math.log2(len(committed)) if len(committed) > 1 else 0.0


def rank(preds: dict, experiments, hypotheses) -> list:
    """Experiments by (pairs separated, then collapse power). Allocation of investigation — NOT a truth ranking."""
    return sorted(((e, epistemic_value(preds, e, hypotheses), round(partition_entropy(preds, e, hypotheses), 3))
                   for e in experiments),
                  key=lambda t: (t[1], t[2]), reverse=True)


def hypothesis_status(preds: dict, hypothesis, experiments) -> str:
    """COMMITTED (≥1 falsifiable forecast) · UNDERCOMMITTED (refuses on ≥1, commits to none — set aside as
    non-discriminable, NOT refuted) · PENDING (only UNKNOWN — our gap, fill cheaply)."""
    cells = [cell(preds, e, hypothesis) for e in experiments]
    if any(is_committed(c) for c in cells):
        return "COMMITTED"
    if any(c is UNDERCOMMITTED for c in cells):
        return "UNDERCOMMITTED"
    return "PENDING"


def presimulation_gate(preds: dict, hypotheses, experiments) -> dict:
    """Before ranking/funding simulations: separate cheap fills (UNKNOWN) from theory-side demands
    (UNDERCOMMITTED). Two programs — measurement vs commitment — with opposite cost profiles."""
    fill = sorted((e, h) for e in experiments for h in hypotheses if cell(preds, e, h) is UNKNOWN)
    demand = sorted(h for h in hypotheses if hypothesis_status(preds, h, experiments) == "UNDERCOMMITTED")
    return {"fill_unknown_cheap": fill, "demand_commitment_or_set_aside": demand}


def report(preds: dict, experiments, hypotheses) -> dict:
    """Ranking + provenance + commitment gate + collapse power. No verdict, no truth, no 'false'/'refuted'."""
    return {
        "ranking": rank(preds, experiments, hypotheses),                 # (experiment, pairs, collapse_power)
        "hypothesis_status": {h: hypothesis_status(preds, h, experiments) for h in hypotheses},
        "gate": presimulation_gate(preds, hypotheses, experiments),
        "collapse_ceiling": round(committed_ceiling(preds, experiments, hypotheses), 3),
        "prediction_provenance": DECLARED,
        "conversion_target": MEASURED_BY_INTERVENTION,
        "note": "ranks expected DECLARED→MEASURED_BY_INTERVENTION conversions (allocation, not verdict); "
                "UNDERCOMMITTED hypotheses are set aside as non-discriminable, NOT refuted; collapse_power is an "
                "UPPER bound — it assumes distinct predictions are experimentally resolvable (resolution is a "
                "separate axis)",
    }


def main() -> None:
    print("discrimination_matrix — rank by uncertainty COLLAPSED (pairs + collapse power); gate on commitment.")
    print("UNKNOWN (our gap) ≠ UNDERCOMMITTED (theory defect). Never a verdict; collapse power is an upper bound.\n")

    H = ["thermal", "recombination", "opacity", "shock", "nonthermal_placeholder"]
    E = ["flash_t_lambda", "noble_gas_sweep", "asymmetry_sweep"]
    preds = {
        ("flash_t_lambda", "thermal"): "continuum tracks T(t)",
        ("flash_t_lambda", "recombination"): "recomb features on cooling",
        ("flash_t_lambda", "opacity"): "graybody area×T evolves",
        ("flash_t_lambda", "shock"): UNDERCOMMITTED,                 # dynamics axis: no emission-spectrum prediction
        ("flash_t_lambda", "nonthermal_placeholder"): UNDERCOMMITTED,  # placeholder: refuses to predict
        ("noble_gas_sweep", "thermal"): "trend with ionization potential",
        ("noble_gas_sweep", "recombination"): "trend with ionization potential",
        ("noble_gas_sweep", "opacity"): "trend with ionization potential",
        ("noble_gas_sweep", "shock"): UNDERCOMMITTED,
        ("noble_gas_sweep", "nonthermal_placeholder"): UNDERCOMMITTED,
        ("asymmetry_sweep", "shock"): "emission suppressed if convergence prevented",
        ("asymmetry_sweep", "nonthermal_placeholder"): UNDERCOMMITTED,
    }

    for exp, val, ent in rank(preds, E, H):
        print(f"  {exp:<16} pairs={val}  collapse_power={ent:>5}  ({outcome_diversity(preds, exp, H)} outcome classes)")
    rep = report(preds, E, H)
    print(f"\n  collapse ceiling = log2(#committed) = {rep['collapse_ceiling']}  (raised only by commitment, not measurement)")
    print(f"  hypothesis status: {rep['hypothesis_status']}")
    print(f"  gate · fill UNKNOWN (cheap): {rep['gate']['fill_unknown_cheap']}")
    print(f"  gate · demand commitment:    {rep['gate']['demand_commitment_or_set_aside']}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<38} {detail}")

    # 1. primary metric: a divergent experiment separates the committed pairs only
    check("divergent_separates_committed", epistemic_value(preds, "flash_t_lambda", H) == 3,
          "flash separates the 3 COMMITTED emission mechanisms; shock/placeholder don't count")

    # 2. an all-same-trend experiment separates nothing
    check("same_trend_separates_nothing", epistemic_value(preds, "noble_gas_sweep", H) == 0,
          "thermal/recombination/opacity predict the same gas trend → 0 separations")

    # 3. UNKNOWN and UNDERCOMMITTED are DISTINCT, and neither discriminates
    check("unknown_vs_undercommitted_distinct",
          UNKNOWN is not UNDERCOMMITTED and not is_committed(UNKNOWN) and not is_committed(UNDERCOMMITTED)
          and not separates(preds, "flash_t_lambda", "thermal", "shock"),
          "two different empty states; committed-vs-UNDERCOMMITTED is NOT a separation")

    # 4. hypothesis status three-way
    check("status_three_way",
          hypothesis_status(preds, "thermal", E) == "COMMITTED"
          and hypothesis_status(preds, "nonthermal_placeholder", E) == "UNDERCOMMITTED"
          and hypothesis_status(preds, "shock", E) == "COMMITTED",
          "thermal COMMITTED; placeholder UNDERCOMMITTED; shock COMMITTED (only on its own axis)")

    # 5. the gate partitions cheap fills from theory-side demands
    g = presimulation_gate(preds, H, E)
    check("gate_partitions_fill_vs_demand",
          ("asymmetry_sweep", "thermal") in g["fill_unknown_cheap"]
          and "nonthermal_placeholder" in g["demand_commitment_or_set_aside"]
          and "thermal" not in g["demand_commitment_or_set_aside"],
          "UNKNOWN emission cells → fill (cheap); the placeholder → demand commitment")

    # 6. UNDERCOMMITTED is set aside, NEVER falsified
    rep_keys_ok = not any(k in rep for k in ("false", "refuted", "eliminated", "true_hypothesis", "winner"))
    check("undercommitted_not_falsified",
          rep_keys_ok and "set aside" in rep["note"] and "non-discriminable" in rep["note"],
          "report sets undercommitted theories aside as non-discriminable; never marks them false")

    # 7. no inflation: predictions DECLARED; conversion target labeled; allocation only
    check("no_inflation_allocation_only",
          rep["prediction_provenance"] == DECLARED and rep["conversion_target"] == MEASURED_BY_INTERVENTION,
          "predictions stay DECLARED (Rule 5); running converts to MEASURED_BY_INTERVENTION")

    # 8. collapse power: counts DISTINCT committed outcomes (diversity)
    pe = {("d", "a"): "A", ("d", "b"): "B", ("d", "c"): "C", ("d", "x"): "D",       # 4 distinct → div 4
          ("bal", "a"): "A", ("bal", "b"): "A", ("bal", "c"): "B", ("bal", "x"): "B",   # (2,2)
          ("skew", "a"): "A", ("skew", "b"): "B", ("skew", "c"): "B", ("skew", "x"): "B",  # (1,3)
          ("one", "a"): "A", ("one", "b"): "A", ("one", "c"): "A", ("one", "x"): "A",      # (4) one class
          ("sparse", "a"): "A", ("sparse", "b"): UNDERCOMMITTED, ("sparse", "c"): UNDERCOMMITTED, ("sparse", "x"): UNDERCOMMITTED}
    HH = ["a", "b", "c", "x"]
    check("diversity_counts_distinct_outcomes",
          outcome_diversity(pe, "d", HH) == 4 and outcome_diversity(pe, "bal", HH) == 2
          and outcome_diversity(pe, "one", HH) == 1,
          "distinct committed predictions → outcome classes; identical predictions collapse into one")

    # 9. entropy REWARDS diversity (more distinct outcomes → more collapse power)
    check("entropy_rewards_diversity", partition_entropy(pe, "d", HH) > partition_entropy(pe, "bal", HH),
          "4 distinct outcomes (2.0 bits) > 2 outcomes (1.0 bit) — more aggressive partition")

    # 10. entropy REWARDS balance at equal diversity (the thing pair-count/diversity miss)
    check("entropy_rewards_balance",
          outcome_diversity(pe, "bal", HH) == outcome_diversity(pe, "skew", HH)
          and partition_entropy(pe, "bal", HH) > partition_entropy(pe, "skew", HH),
          "(2,2) split = 1.0 bit > (1,3) split ≈ 0.81 bit — same #classes, balance breaks the tie")

    # 11. uncommitted hypotheses are EXCLUDED from the partition (no fake collapse from sparsity)
    check("uncommitted_excluded_from_partition",
          outcome_diversity(pe, "sparse", HH) == 1 and partition_entropy(pe, "sparse", HH) == 0.0,
          "1 committed + 3 UNDERCOMMITTED → 1 class, 0 collapse power (sparsity is never rewarded)")

    # 12. the ceiling = log2(#committed); a maximally-diverse experiment realizes it; commitment raises it
    check("collapse_ceiling_is_log2_committed",
          committed_ceiling(pe, ["d"], HH) == 2.0 and partition_entropy(pe, "d", HH) == 2.0,
          "ceiling = log2(4 committed) = 2.0; the all-distinct experiment realizes it — uncommitted theories lower it")

    print(f"\n{passed}/{total} checks. Two metrics: pairs separated (primary) and collapse power = partition")
    print("entropy over the COMMITTED hypotheses (secondary) — which rewards splitting them into many, evenly-")
    print("sized outcome classes, not just any split. Its ceiling is log2(#committed), so an UNDERCOMMITTED theory")
    print("lowers the achievable collapse power for the whole program: commitment raises the ceiling, measurement")
    print("only realizes up to it. UNKNOWN ≠ UNDERCOMMITTED; the latter is set aside, never falsified; collapse")
    print("power is an UPPER bound (assumes distinct predictions are resolvable). Allocation, never a verdict.")
    assert passed == total, "discrimination_matrix failed its own self-test"


if __name__ == "__main__":
    main()
