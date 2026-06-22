# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/run.py — verify the seam plumbing + the self-describing measurement (still no GPU).

Now includes BenchmarkObservation: a number cannot exist without the conditions that produced it. The
harness emits only observations; a bare profile/interval that is not bound to its provenance is refused.
"""
from __future__ import annotations

from backends import FixtureBackend, RealGpuBackend
from contract import RunRecord, TemporalErrorProfile
from frame import FrameArtifact, GoldenReplay
from observation import BenchmarkObservation, observe
from timing import CpuTiming, GpuInterval, LatencyProfile


def _raises(fn, exc=ValueError):
    try:
        fn()
        return False
    except exc:
        return True


def _run(backend="fixture"):
    return RunRecord(device="Z2 Extreme (RDNA 3.5)", power_profile="25W", driver="x.y.z", backend=backend,
                     resolution="1920x1080", temperature_state="sustained", algorithm_commit="deadbeef")


def main():
    golden = GoldenReplay(scene="hallway", seed=1, policy="PFAL", provenance_digest="deadbeefcafe")
    fb = FixtureBackend()
    frame = golden.frame()
    run = _run("fixture")

    # the SAME artifact, two budgets → same identity, two distinct observations
    obs_1 = observe(fb, frame, run, gpu_budget=123456)
    obs_2 = observe(fb, frame, run, gpu_budget=246912)

    cpu = CpuTiming(cpu_submission_latency=0.4, cpu_observed_gpu_duration=4.1, present_latency=0.7)
    good_fidelity = TemporalErrorProfile(0.1, 0.1, 0.1, 0.1)
    bad_loop = LatencyProfile(2.0, 4.0, 8.0, 20.0)

    # an observation built on incomplete run-provenance is UNACCOUNTED / refused at emission
    bare_run = RunRecord(device="Z2 Extreme")
    refused = _raises(lambda: observe(fb, frame, bare_run, gpu_budget=123456))
    # an observation whose run-provenance backend disagrees with the measuring backend is UNACCOUNTED
    mismatched = BenchmarkObservation(artifact_digest=frame.digest(), run=_run("real_gpu"), backend="fixture",
                                      gpu_budget=1, gpu_interval=GpuInterval(0, 1),
                                      temporal_profile=good_fidelity, provenance_digest="x" * 12)

    real_seam_empty = _raises(lambda: RealGpuBackend().render(frame, 123456), NotImplementedError)

    checks = {
        "1_fixture_backend_is_not_a_reference_renderer": fb.name == "fixture",
        "2_golden_round_trips_without_a_budget_field":
            GoldenReplay.from_json(golden.to_json()) == golden and not hasattr(golden, "frame_budget_gpu_ticks"),
        "3_provenance_cannot_be_empty_or_a_label":
            _raises(lambda: FrameArtifact("s", "t", "p", ""))
            and _raises(lambda: GoldenReplay("s", 1, "p", "unknown")),
        "4_budget_is_an_execution_condition_not_identity":
            obs_1.artifact_digest == obs_2.artifact_digest and obs_1.gpu_budget != obs_2.gpu_budget,
        "5_pixel_diff_is_a_measurement_not_an_identity_change":
            # different budgets/observations → same world identity, different observation digest
            obs_1.artifact_digest == frame.digest() and obs_1.digest() != obs_2.digest(),
        "6_gpu_interval_is_the_ruler_cpu_is_provenance":
            obs_1.gpu_interval.duration() == 123456 and hasattr(cpu, "cpu_observed_gpu_duration")
            and not hasattr(cpu, "gpu_execution_time"),
        "7_latency_sums_fidelity_does_not":
            hasattr(LatencyProfile, "total") and not hasattr(TemporalErrorProfile, "total")
            and abs(bad_loop.total() - 34.0) < 1e-9,
        "8_observation_binds_provenance_or_is_unaccounted":
            obs_1.status() == "recorded" and refused and mismatched.status() == "UNACCOUNTED",
        "9_three_fields_stay_distinct_never_collapsed":
            len({obs_1.artifact_digest, obs_1.provenance_digest, obs_1.digest()}) == 3,
        "10_latency_is_optional_separate_instrument":
            obs_1.latency_profile is None and observe(fb, frame, run, 1, latency=bad_loop).latency_profile is bad_loop,
        "11_real_backend_is_an_honestly_empty_seam": real_seam_empty,
    }

    print("GPU BENCHMARK — seam + observation self-check (no GPU; no fidelity claim)\n")
    print("   golden:", golden.to_json())
    print("   artifact identity:", frame.digest(), "(invariant across budgets — CORE ⟂ GPU observation)")
    print("   obs@123456 digest:", obs_1.digest(), " obs@246912 digest:", obs_2.digest(), " (same artifact)")
    print("   artifact ≠ provenance ≠ observation:", obs_1.artifact_digest, obs_1.provenance_digest, obs_1.digest())
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "the seam/observation contract was violated"
    print("\nall %d checks passed — a measurement cannot exist without the conditions that produced it; the"
          " image hash is a receipt, not the lineage. Substrate ≠ benchmark." % len(checks))
    return checks


if __name__ == "__main__":
    main()
