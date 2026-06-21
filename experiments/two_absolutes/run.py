# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/two_absolutes/run.py — the two class-independent guarantees, with the verifiability correction.

    python3 experiments/two_absolutes/run.py     # stdlib only; deterministic

Reviews and corrects a proposed "M22 = irreversible erasure" guarantee: erasure done information-theoretically
is just severance (M21); erasure done physically is class-relative (Landauer — it dissipates into a reservoir a
richer observer reads). The real second absolute is INDISTINGUISHABILITY, with the honest bound that it is
almost always DECLARED, not proved (proving it needs exhaustive intervention).
"""
from __future__ import annotations

from absolutes import StatusClaim, validate, ABSOLUTE, RELATIVE


def _raises(fn, exc=Exception):
    try:
        fn(); return False
    except exc:
        return True


def main():
    severed = validate(StatusClaim("M21_severed", witness={"kind": "severance_witness", "detail": "no channel carries it"}))
    indist = validate(StatusClaim("indistinguishable", witness={"kind": "interventional_identity_witness",
                                                                 "detail": "P(Y|do(X))=P(Y|do(X')) declared over 𝓐"}))
    survived = validate(StatusClaim("survived", adversary_class="O_A"))

    print("TWO ABSOLUTES — severance and indistinguishability (everything else is relative)\n")
    print("   M21_severed     :", severed)
    print("   indistinguishable:", indist)
    print("   survived        :", survived)
    print("\n   absolutes:", ABSOLUTE, " relative:", RELATIVE)

    checks = {
        "1_physical_erasure_rejected_as_absolute": _raises(lambda: validate(StatusClaim("M22_erased")), TypeError),
        "2_logical_erasure_is_severance_not_a_new_absolute": severed["status"] == "M21_severed" and severed["tier"] == "absolute",
        "3a_severed_requires_its_witness": _raises(lambda: validate(StatusClaim("M21_severed"))),
        "3b_indistinguishable_requires_its_witness": _raises(lambda: validate(StatusClaim("indistinguishable"))),
        "4_absolute_cannot_be_conditioned_on_adversary_class":
            _raises(lambda: validate(StatusClaim("M21_severed", witness={"kind": "severance_witness"}, adversary_class="O_A"))),
        "5_indistinguishability_is_declared_not_verified": indist["verified_by_runtime"] is False,
        "6_severance_is_constructive_indistinguishability_is_the_frontier":
            severed["verifiability"] == "constructive" and indist["verifiability"] == "requires_exhaustive_intervention",
        "7_relative_status_carries_its_adversary_class": survived["tier"] == "relative" and survived["relative_to"] == "O_A",
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "two-absolutes discipline did not hold"
    print("\nall %d checks passed — two absolutes (severance, indistinguishability); erasure is not a third." % len(checks))
    return checks


if __name__ == "__main__":
    main()
