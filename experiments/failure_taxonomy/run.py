# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/failure_taxonomy/run.py — type the provenance of ignorance, never a generic "unknown".

    python3 experiments/failure_taxonomy/run.py     # stdlib only; deterministic
"""
from __future__ import annotations

from failure import (classify_failure, diagnose, tier,
                     SEVERANCE, INDISTINGUISHABILITY, ASSUMPTION_LIMIT, RESOURCE_LIMIT, ABSOLUTE)

CASES = {
    SEVERANCE: {"signal_present": False, "alternative_cause_matches": False,
                "resolves_under_richer_admissibility": False, "resolves_under_richer_observer": False},
    INDISTINGUISHABILITY: {"signal_present": True, "alternative_cause_matches": True,
                           "resolves_under_richer_admissibility": False, "resolves_under_richer_observer": False},
    ASSUMPTION_LIMIT: {"signal_present": True, "alternative_cause_matches": False,
                       "resolves_under_richer_admissibility": True, "resolves_under_richer_observer": False},
    RESOURCE_LIMIT: {"signal_present": True, "alternative_cause_matches": False,
                     "resolves_under_richer_admissibility": False, "resolves_under_richer_observer": True},
}


def main():
    print("FAILURE TAXONOMY — the provenance of ignorance (why is the cause unrecoverable?)\n")
    for expected, case in CASES.items():
        print("   %-22s → %s" % (expected, diagnose(case)))

    checks = {
        "classify_severance": classify_failure(CASES[SEVERANCE]) == SEVERANCE,
        "classify_indistinguishability": classify_failure(CASES[INDISTINGUISHABILITY]) == INDISTINGUISHABILITY,
        "classify_assumption_limit": classify_failure(CASES[ASSUMPTION_LIMIT]) == ASSUMPTION_LIMIT,
        "classify_resource_limit": classify_failure(CASES[RESOURCE_LIMIT]) == RESOURCE_LIMIT,
        "absolutes_resolve_under_neither_axis": all(
            not CASES[k]["resolves_under_richer_admissibility"] and not CASES[k]["resolves_under_richer_observer"]
            for k in ABSOLUTE),
        "assumption_limit_resolves_only_under_richer_A":
            CASES[ASSUMPTION_LIMIT]["resolves_under_richer_admissibility"] and not CASES[ASSUMPTION_LIMIT]["resolves_under_richer_observer"],
        "resource_limit_resolves_only_under_richer_observer":
            CASES[RESOURCE_LIMIT]["resolves_under_richer_observer"] and not CASES[RESOURCE_LIMIT]["resolves_under_richer_admissibility"],
        "no_generic_unknown": all(classify_failure(c) != "unclassified" for c in CASES.values()),
        "severance_is_independence_indistinguishability_is_equivalence":
            diagnose(CASES[SEVERANCE])["relation"] == "independence" and diagnose(CASES[INDISTINGUISHABILITY])["relation"] == "equivalence",
        "four_distinct_kinds_two_absolute_two_relative":
            len({classify_failure(c) for c in CASES.values()}) == 4
            and sum(tier(classify_failure(c)) == "absolute" for c in CASES.values()) == 2,
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "failure taxonomy did not hold"
    print("\nall %d checks passed — ignorance now names its own provenance (severance / indistinguishability / assumption / resource)." % len(checks))
    return checks


if __name__ == "__main__":
    main()
