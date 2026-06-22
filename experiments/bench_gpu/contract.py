# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/bench_gpu/contract.py — the measurement contract a GPU benchmark harness must satisfy.

This is NOT the benchmark. It is the part of `docs/REAL_SILICON_BENCHMARK.md` that can be made executable
and verifiable WITHOUT a GPU: the run-provenance closure (a benchmark run is an Artifact), the equal-budget
comparison structure, and the Pareto temporal-error profile (a vector, never a summed score). The real
GPU backend is a declared seam, deliberately empty — running it is the un-faked frontier on real silicon.

Invariants enforced here (so the harness can never quietly violate them):
  * a result without run-provenance is UNACCOUNTED — the thing that licenses a number travels with it;
  * every policy is measured at the SAME GPU-timestamp budget (the GPU clock is the shared ruler);
  * temporal error is a Pareto PROFILE — there is no `.score()` / `.total()`; summing is structurally absent;
  * the real backend raises NotImplementedError — measurements are not faked.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List

UNACCOUNTED = "UNACCOUNTED"


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


# --- reproducibility: a benchmark RUN is an Artifact (run-provenance + content digests) ----------
@dataclass
class RunRecord:
    device: str = ""
    power_profile: str = ""
    driver: str = ""
    backend: str = ""
    resolution: str = ""
    temperature_state: str = ""
    algorithm_commit: str = ""

    _REQUIRED = ("device", "power_profile", "driver", "backend", "resolution",
                 "temperature_state", "algorithm_commit")

    def missing(self) -> List[str]:
        return [f for f in self._REQUIRED if not getattr(self, f)]

    def status(self) -> str:
        # a run that does not carry its full provenance is UNACCOUNTED — never silently usable
        return "recorded" if not self.missing() else UNACCOUNTED

    def digest(self) -> str:
        return _digest({f: getattr(self, f) for f in self._REQUIRED})


# --- the temporal-error PROFILE: a vector, never a sum --------------------------------------------
@dataclass(frozen=True)
class TemporalErrorProfile:
    reconstruction_error: float
    motion_instability: float
    boundary_discontinuity: float
    perceptual_artifact: float
    # NOTE: there is deliberately no .score()/.total()/.sum() — collapsing four failure modes into one
    # scalar would recreate the multiplicative-convenience the fidelity-laws audit removed.

    def axes(self) -> Dict[str, float]:
        return {"reconstruction_error": self.reconstruction_error,
                "motion_instability": self.motion_instability,
                "boundary_discontinuity": self.boundary_discontinuity,
                "perceptual_artifact": self.perceptual_artifact}


def dominates(a: TemporalErrorProfile, b: TemporalErrorProfile) -> bool:
    """a Pareto-dominates b iff a is ≤ b on every axis and < on at least one (lower error is better)."""
    aa, ba = a.axes(), b.axes()
    return all(aa[k] <= ba[k] for k in aa) and any(aa[k] < ba[k] for k in aa)


def pareto_front(profiles: Dict[str, TemporalErrorProfile]) -> List[str]:
    """Names not dominated by any other — no total order is imposed (incomparable profiles coexist)."""
    return sorted(n for n in profiles if not any(dominates(profiles[m], profiles[n]) for m in profiles if m != n))


def compare(candidate: str, profiles: Dict[str, TemporalErrorProfile]) -> dict:
    """A verdict by domination, never a scalar ranking. 'pareto_win' = candidate dominates every other;
    'pareto_nondominated' = on the front but trades off; 'dominated' = some policy beats it on all axes."""
    others = [n for n in profiles if n != candidate]
    if all(dominates(profiles[candidate], profiles[o]) for o in others) and others:
        verdict = "pareto_win"
    elif candidate in pareto_front(profiles):
        verdict = "pareto_nondominated"
    else:
        verdict = "dominated"
    return {"verdict": verdict, "front": pareto_front(profiles), "candidate": candidate}


# --- the GPU-budget backend: a seam. The real one is the un-faked frontier ------------------------
class GpuBudgetBackend:
    """Measure a policy's temporal-error profile at a FIXED GPU-timestamp budget (N ticks)."""

    def measure(self, policy: str, gpu_tick_budget: int, scene: str) -> TemporalErrorProfile:
        raise NotImplementedError


class RealBackend(GpuBudgetBackend):
    """Vulkan/DX12/wgpu on real silicon (e.g. the Z2 Extreme). NOT implemented here — measurements are not
    faked; this is the frontier the contract is written to be satisfied by, on the device."""

    def measure(self, policy, gpu_tick_budget, scene):
        raise NotImplementedError(
            "real GPU backend (Vulkan/DX12/wgpu) — run on device with GPU-timestamp queries; not faked here")


class MockBackend(GpuBudgetBackend):
    """Deterministic SYNTHETIC profiles, for exercising the harness LOGIC only. It makes no fidelity claim —
    the numbers are a fixture, not a measurement. Records the budgets it was asked for (to prove equal-budget)."""

    def __init__(self):
        self.budgets_seen = []

    def measure(self, policy, gpu_tick_budget, scene):
        self.budgets_seen.append(gpu_tick_budget)
        h = int(_digest([policy, scene]), 16)
        # synthetic, deterministic, policy-dependent — a fixture for the comparator, NOT a result
        return TemporalErrorProfile(
            reconstruction_error=(h % 97) / 10.0,
            motion_instability=((h >> 7) % 89) / 10.0,
            boundary_discontinuity=((h >> 13) % 83) / 10.0,
            perceptual_artifact=((h >> 19) % 79) / 10.0,
        )


def fidelity_compare(backend: GpuBudgetBackend, policies: List[str], gpu_tick_budget: int,
                     scene: str, run: RunRecord):
    """Equal-budget comparison. Refuses to produce a result without complete run-provenance (UNACCOUNTED),
    and measures every policy at the SAME GPU-timestamp budget."""
    if run.status() != "recorded":
        raise ValueError("UNACCOUNTED: a benchmark result must carry full run-provenance (missing: %s)"
                         % ", ".join(run.missing()))
    profiles = {p: backend.measure(p, gpu_tick_budget, scene) for p in policies}
    return {"run_digest": run.digest(), "gpu_tick_budget": gpu_tick_budget, "profiles": profiles}
