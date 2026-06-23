# SPDX-License-Identifier: AGPL-3.0-only
"""
discrimination_matrix.py — rank experiments by how much uncertainty they COLLAPSE, not by cost or precision,
and gate them behind a prediction-commitment check.

When several hypotheses fit the same observable, the convergence object labels the axis `INTERVENTION_ONLY`
(observation underdetermines it). The way out is the red-team move: find a manipulation whose predictions
*diverge*. This instrument scores that — and, crucially, distinguishes two reasons a cell is empty:

    UNKNOWN         — WE have not worked out this hypothesis's prediction yet (a gap on our side; cheap to fill).
    UNDERCOMMITTED  — the HYPOTHESIS itself refuses/fails to specify a prediction (a defect on the theory's
                      side; NO future observation can discriminate a theory that will not commit).

Both block discrimination, but they imply opposite actions: fill an `UNKNOWN` (run the cheap simulation);
*demand commitment for* an `UNDERCOMMITTED` (a workshop, not a measurement). And the honest guard:
**`UNDERCOMMITTED` ≠ false** — an uncommitted theory is *set aside as non-discriminable*, never refuted
(`absence of evidence ≠ evidence of absence`). The bottleneck is often prediction scarcity, not data scarcity.

Discipline (unchanged):
  * a prediction cell is `DECLARED` — a model output, never a measurement (Rule 5: a simulation is a witness).
  * neither `UNKNOWN` nor `UNDERCOMMITTED` ever counts as separation (no fabricated divergence).
  * the output is an ALLOCATION of investigation, never a verdict on which hypothesis is true.

Run (from this directory):  PYTHONHASHSEED=0 python3 discrimination_matrix.py
"""
from __future__ import annotations

from itertools import combinations

from reality_status import DECLARED, MEASURED_BY_INTERVENTION


class _State:
    """A non-prediction cell state. Distinct objects so neither collides with a real prediction string."""
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


UNKNOWN = _State("UNKNOWN")               # our gap — fill it cheaply (a simulation)
UNDERCOMMITTED = _State("UNDERCOMMITTED")  # the theory's defect — demand commitment, or set aside (not refute)


def is_committed(cell) -> bool:
    """A cell carries a usable prediction iff it is neither UNKNOWN nor UNDERCOMMITTED."""
    return cell is not UNKNOWN and cell is not UNDERCOMMITTED


def cell(preds: dict, experiment, hypothesis):
    return preds.get((experiment, hypothesis), UNKNOWN)   # absent ⇒ UNKNOWN (not recorded ≠ theory refused)


def separates(preds: dict, experiment, h1, h2) -> bool:
    """True iff BOTH hypotheses commit a prediction under this experiment AND the predictions differ."""
    p1, p2 = cell(preds, experiment, h1), cell(preds, experiment, h2)
    return is_committed(p1) and is_committed(p2) and p1 != p2


def epistemic_value(preds: dict, experiment, hypotheses) -> int:
    """How many hypothesis pairs this experiment would separate = DECLARED→MEASURED_BY_INTERVENTION conversions."""
    return sum(1 for h1, h2 in combinations(hypotheses, 2) if separates(preds, experiment, h1, h2))


def separated_pairs(preds: dict, experiment, hypotheses) -> list:
    return [(h1, h2) for h1, h2 in combinations(hypotheses, 2) if separates(preds, experiment, h1, h2)]


def rank(preds: dict, experiments, hypotheses) -> list:
    """Experiments by descending epistemic value. Allocation of investigation — NOT a truth ranking."""
    return sorted(((e, epistemic_value(preds, e, hypotheses)) for e in experiments),
                  key=lambda t: t[1], reverse=True)


def hypothesis_status(preds: dict, hypothesis, experiments) -> str:
    """COMMITTED (makes ≥1 falsifiable forecast) · UNDERCOMMITTED (refuses on ≥1, commits to none — a theory
    defect, set aside as non-discriminable, NOT refuted) · PENDING (only UNKNOWN — our gap, fill it cheaply)."""
    cells = [cell(preds, e, hypothesis) for e in experiments]
    if any(is_committed(c) for c in cells):
        return "COMMITTED"
    if any(c is UNDERCOMMITTED for c in cells):
        return "UNDERCOMMITTED"
    return "PENDING"


def presimulation_gate(preds: dict, hypotheses, experiments) -> dict:
    """Before ranking/funding simulations: separate the cheap fills (UNKNOWN) from the theory-side demands
    (UNDERCOMMITTED). Two different programs — measurement vs commitment — with opposite cost profiles."""
    fill = sorted((e, h) for e in experiments for h in hypotheses if cell(preds, e, h) is UNKNOWN)
    demand = sorted(h for h in hypotheses if hypothesis_status(preds, h, experiments) == "UNDERCOMMITTED")
    return {"fill_unknown_cheap": fill, "demand_commitment_or_set_aside": demand}


def report(preds: dict, experiments, hypotheses) -> dict:
    """The only legitimate output: a ranking + the provenance + the commitment gate. No verdict, no truth, no
    'false'/'refuted' — an undercommitted hypothesis is set aside as non-discriminable, never falsified."""
    return {
        "ranking": rank(preds, experiments, hypotheses),                 # (experiment, pairs_separated)
        "hypothesis_status": {h: hypothesis_status(preds, h, experiments) for h in hypotheses},
        "gate": presimulation_gate(preds, hypotheses, experiments),
        "prediction_provenance": DECLARED,                               # every committed cell is a model output
        "conversion_target": MEASURED_BY_INTERVENTION,                   # what RUNNING the experiment yields
        "note": "ranks expected DECLARED→MEASURED_BY_INTERVENTION conversions (allocation, not verdict); "
                "UNDERCOMMITTED hypotheses are set aside as non-discriminable, NOT refuted",
    }


def main() -> None:
    print("discrimination_matrix — rank by uncertainty COLLAPSED; gate on prediction commitment.")
    print("UNKNOWN (our gap, fill cheaply) ≠ UNDERCOMMITTED (theory defect, demand or set aside). Never a verdict.\n")

    # synthetic worked example (mirrors the sonoluminescence program)
    H = ["thermal", "recombination", "opacity", "shock", "nonthermal_placeholder"]
    E = ["flash_t_lambda", "noble_gas_sweep", "asymmetry_sweep"]
    preds = {
        # emission micro-mechanisms commit on the spectral axis and diverge there
        ("flash_t_lambda", "thermal"): "continuum tracks T(t)",
        ("flash_t_lambda", "recombination"): "recomb features on cooling",
        ("flash_t_lambda", "opacity"): "graybody area×T evolves",
        # shock is a DYNAMICS hypothesis: it does not specify an emission spectrum → UNDERCOMMITTED on this axis
        ("flash_t_lambda", "shock"): UNDERCOMMITTED,
        # the placeholder refuses to predict anywhere → UNDERCOMMITTED (a theory defect, not our gap)
        ("flash_t_lambda", "nonthermal_placeholder"): UNDERCOMMITTED,
        ("noble_gas_sweep", "thermal"): "trend with ionization potential",
        ("noble_gas_sweep", "recombination"): "trend with ionization potential",
        ("noble_gas_sweep", "opacity"): "trend with ionization potential",
        ("noble_gas_sweep", "shock"): UNDERCOMMITTED,
        ("noble_gas_sweep", "nonthermal_placeholder"): UNDERCOMMITTED,
        # asymmetry is where shock FINALLY commits (a different axis); the emission trio is UNKNOWN here (our gap)
        ("asymmetry_sweep", "shock"): "emission suppressed if convergence prevented",
        # ("asymmetry_sweep", thermal/recombination/opacity) left absent ⇒ UNKNOWN (we have not computed them)
        ("asymmetry_sweep", "nonthermal_placeholder"): UNDERCOMMITTED,
    }

    for exp, val in rank(preds, E, H):
        print(f"  {exp:<16} value={val}   separates: {separated_pairs(preds, exp, H) or 'nothing'}")
    rep = report(preds, E, H)
    print(f"\n  hypothesis status: {rep['hypothesis_status']}")
    print(f"  gate · fill UNKNOWN (cheap simulation): {rep['gate']['fill_unknown_cheap']}")
    print(f"  gate · demand commitment / set aside:   {rep['gate']['demand_commitment_or_set_aside']}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<36} {detail}")

    # 1. fully-divergent experiment separates committed pairs only
    check("divergent_separates_committed", epistemic_value(preds, "flash_t_lambda", H) == 3,
          "flash separates the 3 COMMITTED emission mechanisms; shock/placeholder don't count")

    # 2. an all-same-trend experiment separates nothing among the committed
    check("same_trend_separates_nothing", epistemic_value(preds, "noble_gas_sweep", H) == 0,
          "thermal/recombination/opacity predict the same gas trend → 0 separations")

    # 3. UNKNOWN and UNDERCOMMITTED are DISTINCT states, and neither discriminates
    check("unknown_vs_undercommitted_distinct",
          UNKNOWN is not UNDERCOMMITTED and not is_committed(UNKNOWN) and not is_committed(UNDERCOMMITTED)
          and not separates(preds, "flash_t_lambda", "thermal", "shock"),
          "two different empty states; a committed-vs-UNDERCOMMITTED pair is NOT a separation")

    # 4. hypothesis status is three-way (COMMITTED / UNDERCOMMITTED / PENDING)
    check("status_three_way",
          hypothesis_status(preds, "thermal", E) == "COMMITTED"
          and hypothesis_status(preds, "nonthermal_placeholder", E) == "UNDERCOMMITTED"
          and hypothesis_status(preds, "shock", E) == "COMMITTED",   # shock commits on the asymmetry axis
          "thermal COMMITTED; placeholder UNDERCOMMITTED; shock COMMITTED (only on its own axis)")

    # 5. the gate partitions cheap fills from theory-side demands
    g = presimulation_gate(preds, H, E)
    check("gate_partitions_fill_vs_demand",
          ("asymmetry_sweep", "thermal") in g["fill_unknown_cheap"]
          and "nonthermal_placeholder" in g["demand_commitment_or_set_aside"]
          and "thermal" not in g["demand_commitment_or_set_aside"],
          "UNKNOWN emission cells under asymmetry → fill (cheap); the placeholder → demand commitment")

    # 6. UNDERCOMMITTED is set aside, NEVER falsified (absence of evidence ≠ evidence of absence)
    rep_keys_ok = not any(k in rep for k in ("false", "refuted", "eliminated", "true_hypothesis", "winner"))
    check("undercommitted_not_falsified",
          rep_keys_ok and "set aside" in rep["note"] and "non-discriminable" in rep["note"],
          "the report sets undercommitted theories aside as non-discriminable; it never marks them false")

    # 7. no inflation: provenance capped at DECLARED; conversion target labeled; output is allocation
    check("no_inflation_allocation_only",
          rep["prediction_provenance"] == DECLARED and rep["conversion_target"] == MEASURED_BY_INTERVENTION,
          "predictions stay DECLARED (Rule 5); running is what would convert to MEASURED_BY_INTERVENTION")

    print(f"\n{passed}/{total} checks. The matrix now separates two reasons a cell is empty: UNKNOWN (our gap —")
    print("fill it with a cheap simulation) and UNDERCOMMITTED (the theory refuses — demand a prediction or set")
    print("it aside as non-discriminable). Neither counts as discrimination; an UNDERCOMMITTED theory is never")
    print("called false (absence of evidence ≠ evidence of absence). The bottleneck it exposes is prediction")
    print("scarcity, not data scarcity — and the cheapest, highest-leverage move is to close the commitment gate")
    print("before spending a measurement dollar. Predictions stay DECLARED; the output is allocation, never a verdict.")
    assert passed == total, "discrimination_matrix failed its own self-test"


if __name__ == "__main__":
    main()
