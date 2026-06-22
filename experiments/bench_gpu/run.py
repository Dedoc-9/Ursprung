# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/run.py — verify the seam plumbing (still no GPU, still no fidelity claim).

Adds to the contract self-check the boring-but-load-bearing structure the real backend will fill: a
backend-agnostic golden replay, the GPU-interval ruler (not CPU wall time), the determinism boundary
(a pixel difference cannot change the world's identity), and latency as a separate instrument.
"""
from __future__ import annotations

from backends import ReferenceBackend, RealGpuBackend
from contract import RunRecord, TemporalErrorProfile, fidelity_compare
from frame import GoldenReplay
from timing import CpuTiming, GpuInterval, LatencyProfile


def main():
    golden = GoldenReplay(scene="hallway", seed=1, policy="PFAL",
                          frame_budget_gpu_ticks=123456, provenance_digest="deadbeefcafe")
    ref = ReferenceBackend()
    frame = golden.frame()

    # render the SAME frame at two different budgets — the world's identity must not move
    p1, i1 = ref.render(frame, golden.frame_budget_gpu_ticks)
    p2, i2 = ref.render(frame, golden.frame_budget_gpu_ticks * 2)

    # GPU interval is the ruler; CPU timing is provenance only
    interval = GpuInterval(begin_tick=1000, end_tick=1000 + golden.frame_budget_gpu_ticks)
    cpu = CpuTiming(cpu_submission_latency=0.4, gpu_execution_time=4.1, present_latency=0.7)

    # a good reconstruction that hides a bad loop: low fidelity error, high latency
    good_fidelity = TemporalErrorProfile(0.1, 0.1, 0.1, 0.1)
    bad_loop = LatencyProfile(input_to_submit=2.0, submit_to_gpu_done=4.0,
                              gpu_done_to_present=8.0, present_to_photon=20.0)

    real_seam_empty = False
    try:
        RealGpuBackend().render(frame, golden.frame_budget_gpu_ticks)
    except NotImplementedError:
        real_seam_empty = True

    checks = {
        "1_golden_round_trips":
            GoldenReplay.from_json(golden.to_json()) == golden,
        "2_golden_derives_a_deterministic_backend_agnostic_frame":
            golden.frame() == golden.frame() and len(frame.digest()) == 12,
        "3_gpu_interval_is_the_ruler_not_cpu_wall":
            interval.duration() == golden.frame_budget_gpu_ticks and hasattr(cpu, "gpu_execution_time"),
        "4_pixel_difference_is_a_measurement_not_a_world_state":
            # different budgets / observations do NOT change the frame's identity (CORE ⟂ GPU)
            i1.duration() != i2.duration() and frame.digest() == golden.frame().digest(),
        "5_latency_sums_fidelity_does_not":
            hasattr(LatencyProfile, "total") and not hasattr(TemporalErrorProfile, "total")
            and abs(bad_loop.total() - 34.0) < 1e-9,
        "6_good_fidelity_can_hide_a_bad_loop":
            max(good_fidelity.axes().values()) <= 0.1 and bad_loop.total() > 30.0,  # two instruments disagree, by design
        "7_real_backend_is_an_honestly_empty_seam":
            real_seam_empty,
        "8_result_still_needs_provenance":
            _refused_without_provenance(ref, golden),
    }

    print("GPU BENCHMARK — seam plumbing self-check (no GPU; no fidelity claim)\n")
    print("   golden:", golden.to_json())
    print("   frame identity:", frame.digest(), "(stable across budgets — CORE ⟂ GPU observation)")
    print("   GPU-interval ruler:", interval.duration(), "ticks | CPU timing is provenance:", cpu)
    print("   bad-loop latency total: %.1f ms while fidelity error ≤ %.1f — instruments disagree, by design"
          % (bad_loop.total(), max(good_fidelity.axes().values())))
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "the seam plumbing violated the contract"
    print("\nall %d checks passed — the seam is real except for the GPU calls themselves; the world's identity"
          " is independent of what any backend observes. Substrate ≠ benchmark." % len(checks))
    return checks


def _refused_without_provenance(ref, golden):
    bare = RunRecord(device="Z2 Extreme")  # incomplete
    try:
        fidelity_compare(ref_to_budget_backend(ref), [golden.policy], golden.frame_budget_gpu_ticks,
                         golden.scene, run=bare)
        return False
    except ValueError:
        return True


class _Adapter:
    """Adapt ReferenceBackend.render(frame, budget) to the contract's measure(policy, budget, scene)."""
    def __init__(self, ref):
        self.ref = ref

    def measure(self, policy, gpu_tick_budget, scene):
        g = GoldenReplay(scene=scene, seed=1, policy=policy, frame_budget_gpu_ticks=gpu_tick_budget,
                         provenance_digest="x")
        profile, _ = self.ref.render(g.frame(), gpu_tick_budget)
        return profile


def ref_to_budget_backend(ref):
    return _Adapter(ref)


if __name__ == "__main__":
    main()
