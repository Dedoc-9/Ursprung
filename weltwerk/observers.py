# SPDX-License-Identifier: AGPL-3.0-only
"""
observers.py — lenses attached to a Fork. An observer READS trajectories and ALLOCATES attention;
it never defines truth and never edits the world.

THE MERGE (the architectural center this slice proves):
    A Fork is a trajectory pair (trace_a, trace_b) around a declared intervention boundary.
    An observer is a function of ONE trajectory:        observe(leg) -> observable
    The DIFF is the pairing across the boundary:         diff(A, B)   -> Observation(B vs A)
This keeps the streamtube boundary where it belongs: around the pairing, not inside the observable.

THE DISCIPLINE (the no-inflation rule applied to the UI itself):
    Every Observation carries its EVIDENCE CLASS. A WorldDiff (in fork.py) is EXACT_UNDER_MODEL — an
    exact state delta given the regime. An observer estimate is ESTIMATE — it can be WRONG even inside
    the model (sampling, model-break, coarse-graining). The two must NEVER render as equal-looking
    numbers; an estimate must not borrow an exact delta's authority. That confusion — a green check on
    an estimate — is the failure this whole repository exists to catch.

SEPARATORS:
  metric ≠ truth            (an observer allocates attention; it does not certify)
  estimate ≠ property       (a number "under toy-ecology-v0", with uncertainty, not a fact)
  NO_TRAJECTORY ≠ CONVERGED (an unsampled / dead leg is NOT a settled one — the dead-start ghost)
  cheap-proxy ≠ verified    (this Orbit is a live proxy; the CI-bearing estimator is the slow upgrade)
"""
from __future__ import annotations

from dataclasses import dataclass

# evidence classes (the two registers the report keeps apart)
EXACT_UNDER_MODEL = "EXACT_UNDER_MODEL"   # an exact delta given the declared regime (e.g. WorldDiff)
ESTIMATE = "ESTIMATE"                      # can be wrong inside the model — carries ghosts/uncertainty

# orbit classifications (NO_TRAJECTORY is first-class — it is NOT a kind of convergence)
NO_TRAJECTORY = "NO_TRAJECTORY"   # too few / frozen samples — we cannot speak to where it is going
CONVERGED = "CONVERGED"           # late-window motion died: settled into a basin / cycle
EXPLORING = "EXPLORING"           # late-window motion persists: still moving through state space

# declared parameters (Arbitrary-Boundary Law: these are conveniences, not invariants)
LATE_FRACTION = 0.34              # the "late window" is the final third of the trajectory
SETTLE_EPS = 1.0                  # avg feature-L1 motion/tick below this in the late window ⇒ "settled"
MIN_STEPS = 2                     # fewer transitions than this ⇒ NO_TRAJECTORY (cannot judge geometry)


def _l1(u: tuple, v: tuple) -> int:
    return sum(abs(a - b) for a, b in zip(u, v))


@dataclass(frozen=True)
class Observation:
    """One observer's reading across a fork's two legs. Carries its evidence class and any ghosts so
    the report can keep it out of the EXACT register."""
    name: str
    leg_a: dict
    leg_b: dict
    delta: dict
    evidence_class: str
    ghosts: tuple
    note: str

    def render(self) -> str:
        cls = self.delta.get("classification", "")
        ghost = f"  ⚠ ghosts: {', '.join(self.ghosts)}" if self.ghosts else ""
        return (f"    [{self.evidence_class}] {self.name:14s} "
                f"A={self.leg_a.get('classification','?')} → B={self.leg_b.get('classification','?')}"
                f"  {cls}{ghost}\n"
                f"        {self.note}")


class Observer:
    """Base lens. Subclasses implement per_leg(trace) -> observable dict; diff() pairs the legs.
    An observer NEVER mutates a world and NEVER sees the committed timeline — only trajectories."""
    name = "observer"
    evidence_class = ESTIMATE   # observers estimate; only fork.WorldDiff is EXACT_UNDER_MODEL

    def per_leg(self, trace: tuple) -> dict:
        raise NotImplementedError

    def diff(self, trace_a: tuple, trace_b: tuple) -> Observation:
        a, b = self.per_leg(trace_a), self.per_leg(trace_b)
        ghosts = tuple(sorted({g for g in (a.get("_ghost"), b.get("_ghost")) if g}))
        delta = {k: round(b[k] - a[k], 4) for k in a
                 if isinstance(a.get(k), (int, float)) and isinstance(b.get(k), (int, float))}
        delta["classification"] = self._classify_pair(a, b)
        return Observation(name=self.name, leg_a=a, leg_b=b, delta=delta,
                           evidence_class=self.evidence_class, ghosts=ghosts, note=self._note(a, b))

    def _classify_pair(self, a: dict, b: dict) -> str:
        return ""

    def _note(self, a: dict, b: dict) -> str:
        return ""


class OrbitObserver(Observer):
    """'Where is the world going?' — a CHEAP, deterministic trajectory-geometry proxy.

    Reads the coarse feature trajectory and reports straightness = |displacement| / path_length
    (0 = pure cycling / return to origin; 1 = a straight escape) plus late-window speed to tell a
    settled basin from continued exploration. It is explicitly NOT the verified CI-bearing
    orbit_estimator (experiments/live_world_kernel/orbit_estimator.py) — that runs on a slow
    background cadence (hard-problem #1). Evidence class is ESTIMATE; NO_TRAJECTORY is reported, never
    silently folded into CONVERGED (the dead-start ghost we fixed once already)."""
    name = "orbit"

    def per_leg(self, trace: tuple) -> dict:
        n = len(trace)
        if n - 1 < MIN_STEPS:
            return {"straightness": 0.0, "displacement": 0.0, "path_length": 0.0,
                    "late_speed": 0.0, "classification": NO_TRAJECTORY, "_ghost": NO_TRAJECTORY}
        steps = [_l1(trace[i], trace[i + 1]) for i in range(n - 1)]
        path_length = float(sum(steps))
        displacement = float(_l1(trace[0], trace[-1]))
        if path_length == 0.0:
            # frozen world: it moved nowhere. That is NOT a basin it explored into — it never moved.
            return {"straightness": 0.0, "displacement": 0.0, "path_length": 0.0,
                    "late_speed": 0.0, "classification": NO_TRAJECTORY, "_ghost": NO_TRAJECTORY}
        late_k = max(1, int(round((n - 1) * LATE_FRACTION)))
        late_speed = sum(steps[-late_k:]) / late_k
        straightness = displacement / path_length
        classification = CONVERGED if late_speed <= SETTLE_EPS else EXPLORING
        return {"straightness": round(straightness, 4), "displacement": displacement,
                "path_length": path_length, "late_speed": round(late_speed, 4),
                "classification": classification, "_ghost": None}

    def _classify_pair(self, a: dict, b: dict) -> str:
        ds = round(b["straightness"] - a["straightness"], 4)
        return f"Δstraightness={ds:+.4f}, Δlate_speed={round(b['late_speed'] - a['late_speed'], 4):+.4f}"

    def _note(self, a: dict, b: dict) -> str:
        return ("cheap live proxy over coarse features; ESTIMATE, not a verdict. "
                "Verified CI-bearing orbit runs on a background cadence. "
                "NO_TRAJECTORY ≠ CONVERGED: an unmoved leg has no geometry to read.")


if __name__ == "__main__":
    from world import genesis
    from fork import cull_species, fork, identity, set_param

    w = genesis(seed=0).run(5)
    print("observers.py — Orbit as a lens on a Fork (trajectory pair)\n")
    for iv in (identity(), cull_species("predator"), set_param("predation_enabled", False)):
        f = fork(w, iv, horizon=30)
        f.observe(OrbitObserver())
        print(f.report())
        print()
    print("  EXACT (WorldDiff) and ESTIMATE (orbit) render in separate registers — by design.")
