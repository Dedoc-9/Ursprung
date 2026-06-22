# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/run.py — verify the measurement CONTRACT (not the benchmark).

    python3 experiments/bench_gpu/run.py     # stdlib only; deterministic

This proves the harness obeys the contract before any GPU code exists: run-provenance travels with the
result (or it is UNACCOUNTED), the comparison is equal-budget, temporal error is a Pareto profile with no
scalar collapse, and the real backend is honestly empty. No pixels, no fidelity claim.
"""
from __future__ import annotations

from contract import (
    MockBackend,
    RealBackend,
    RunRecord,
    TemporalErrorProfile,
    compare,
    dominates,
    fidelity_compare,
    pareto_front,
)


def _complete_run():
    return RunRecord(device="Z2 Extreme (Radeon 890M, RDNA 3.5)", power_profile="25W", driver="x.y.z",
                     backend="vulkan", resolution="1920x1080", temperature_state="sustained",
                     algorithm_commit="deadbeef")


def main():
    # provenance closure
    full = _complete_run()
    bare = RunRecord(device="Z2 Extreme")  # missing the rest
    # a clear Pareto win, an incomparable trade-off, and a dominated profile
    a = TemporalErrorProfile(1.0, 1.0, 1.0, 1.0)   # best everywhere
    b = TemporalErrorProfile(2.0, 2.0, 2.0, 2.0)   # dominated by a
    c = TemporalErrorProfile(0.5, 3.0, 1.0, 1.0)   # incomparable with a (better axis 1, worse axis 2)
    profiles = {"a": a, "b": b, "c": c}

    mock = MockBackend()
    result = fidelity_compare(mock, ["pfal", "tcff", "causal", "uniform"], gpu_tick_budget=10000,
                              scene="scene01", run=full)

    refused = False
    try:
        fidelity_compare(mock, ["pfal"], 10000, "scene01", run=bare)
    except ValueError:
        refused = True

    real_seam_empty = False
    try:
        RealBackend().measure("pfal", 10000, "scene01")
    except NotImplementedError:
        real_seam_empty = True

    checks = {
        "1_complete_run_is_recorded_with_digest":
            full.status() == "recorded" and len(full.digest()) == 12,
        "2_run_missing_provenance_is_unaccounted":
            bare.status() == "UNACCOUNTED" and "driver" in bare.missing(),
        "3_profile_has_no_scalar_collapse":
            not any(hasattr(a, m) for m in ("score", "total", "sum")) and len(a.axes()) == 4,
        "4_domination_is_correct":
            dominates(a, b) and not dominates(a, c) and not dominates(c, a),
        "5_pareto_front_keeps_incomparable_both":
            set(pareto_front(profiles)) == {"a", "c"},   # b dominated; a and c incomparable → both on front
        "6_compare_returns_verdict_not_a_number":
            isinstance(compare("a", {"a": a, "b": b})["verdict"], str)
            and compare("a", {"a": a, "b": b})["verdict"] == "pareto_win"
            and compare("a", profiles)["verdict"] == "pareto_nondominated",
        "7_result_refused_without_provenance":
            refused and result["run_digest"] == full.digest(),
        "8_equal_budget_every_policy":
            len(set(mock.budgets_seen)) == 1 and mock.budgets_seen[0] == 10000,
        "9_real_backend_is_an_honestly_empty_seam": real_seam_empty,
    }

    print("GPU BENCHMARK — measurement CONTRACT self-check (no GPU; no fidelity claim)\n")
    print("   run-provenance:", full.status(), "digest", full.digest(), "| bare run:", bare.status())
    print("   pareto front of {a,b,c}:", pareto_front(profiles), "(b dominated; a,c incomparable)")
    print("   equal-budget check: budgets seen =", mock.budgets_seen)
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "the measurement contract was violated"
    print("\nall %d checks passed — the harness obeys the contract; the GPU backend remains the un-faked"
          " frontier (run on device). a benchmark run is an Artifact; timing is an event, not an identity."
          % len(checks))
    return checks


if __name__ == "__main__":
    main()
