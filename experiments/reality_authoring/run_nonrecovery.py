# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_authoring/run_nonrecovery.py — ignorance as a first-class historical object.

    python3 experiments/reality_authoring/run_nonrecovery.py     # stdlib only; deterministic

A world answers both "why does this exist?" (edit lineage) and "why is this absent/unresolved?" (a recorded
failure diagnosis), and flags the silent gap (UNACCOUNTED). Object-first: the diagnosis is stored;
recommended_action is a derived view.
"""
from __future__ import annotations

from nonrecovery import WorldWithIgnorance, NonRecovery, Edit


def main():
    w = WorldWithIgnorance()
    w.apply(Edit("gravity", 1.0, 0.5, "developer", "gameplay_constraint", "world_v12", survival_tests=[True]))

    severance = {"signal_present": False, "alternative_cause_matches": False,
                 "resolves_under_richer_admissibility": False, "resolves_under_richer_observer": False}
    assumption = {"signal_present": True, "alternative_cause_matches": False,
                  "resolves_under_richer_admissibility": True, "resolves_under_richer_observer": False}
    resource = {"signal_present": True, "alternative_cause_matches": False,
                "resolves_under_richer_admissibility": False, "resolves_under_richer_observer": True}

    w.record_nonrecovery(NonRecovery("relation_R", severance, source="analysis_v3"))
    w.record_nonrecovery(NonRecovery("relation_S", assumption, source="analysis_v3", missing_admissibility="instrument_validity_A"))
    w.record_nonrecovery(NonRecovery("relation_T", resource, source="analysis_v3"))

    print("PROVENANCE OF NON-RECOVERY — ignorance as a first-class historical object\n")
    for t in ("gravity", "relation_R", "relation_S", "relation_T", "relation_NEVER_ASKED"):
        print("   %-20s → %s" % (t, w.explain(t)))
    print("\n   recommended_action (a DERIVED view, not stored):",
          {t: w.recommended_action(t) for t in ("relation_R", "relation_S", "relation_T")})

    checks = {
        "1_present_has_edit_provenance": w.explain("gravity")["status"] == "present" and w.provenance_of("gravity")[0]["source"] == "developer",
        "2_absent_severance_is_recorded_and_observer_independent":
            w.explain("relation_R")["why"] == "severance" and w.provenance_of_nonrecovery("relation_R").diagnosis["observer_independent"] is True,
        "3_unresolved_assumption_carries_missing_condition":
            w.explain("relation_S")["why"] == "assumption_limit" and w.explain("relation_S")["missing"] == "instrument_validity_A",
        "4_unresolved_resource_is_relative":
            w.provenance_of_nonrecovery("relation_T").diagnosis["tier"] == "relative" and w.explain("relation_T")["observer_independent"] is False,
        "5_ignorance_is_a_historical_object":
            len(w.provenance_of_nonrecovery("relation_R").digest()) == 12 and w.provenance_of_nonrecovery("relation_R").source == "analysis_v3",
        "6_symmetry_both_sides_inspectable":
            w.explain("gravity")["status"] == "present" and w.explain("relation_R")["status"] == "absent_or_unresolved",
        "7_unaccounted_absence_is_flagged": w.explain("relation_NEVER_ASKED")["status"] == "UNACCOUNTED",
        "8_policy_is_a_derived_view_object_first":
            w.recommended_action("relation_R") == "stop" and w.recommended_action("relation_S") == "declare" and w.recommended_action("relation_T") == "allocate",
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "provenance-of-nonrecovery did not hold"
    print("\nall %d checks passed — absence carries lineage; the action map is derived, the object survives." % len(checks))
    return checks


if __name__ == "__main__":
    main()
