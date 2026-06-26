# SPDX-License-Identifier: AGPL-3.0-only
"""
diagnose.py — model-based diagnosis over the causal kernel. The inverse of the model checker.

Provenance: reimplemented clean-room from consistency-based model-based-diagnosis theory
(de Kleer & Williams, "Diagnosing Multiple Faults", Artificial Intelligence 1987; Reiter 1987). This is
the discipline NASA's Livingstone 2 embodies; NO Livingstone source is used (its license is unverified
and treated as NOSA — see ../../docs/LICENSE_DECISIONS.md / ../../docs/PROVENANCE.md). Original AGPL code.

THE LOOP IT CLOSES:
    kernel_check (forward)  → finds a ghost: an invariant fails, here is the reachable state + trace
    diagnose    (inverse)   → given the OBSERVED state, what minimal fault(s) would EXPLAIN it,
                              ranked, plus the single observation that best distinguishes the rivals.

WHAT A DIAGNOSIS IS — AND IS NOT (Dentatus discipline, enforced):
  • A diagnosis is a HYPOTHESIS: a minimal fault set whose simulated consequences reproduce the
    observation. `consistency ≠ causation`; `minimal ≠ correct`; `explains-observation ≠ is-the-cause`.
  • `confidence` is a TRANSPARENT RANKING WEIGHT in [0,1], normalized across the returned rivals —
    NOT a probability that the hypothesis is true. It rewards parsimony (fewer faults) and parsimony of
    effects (fewer un-observed collateral predictions). `weight ≠ P(true)`; `salience ≠ importance`.
  • Competing explanations are PRESERVED, not collapsed. When rivals tie, the report says so and asks
    for the discriminating observation. Ghosts allocate investigation; they do not certify a cause.

MODEL BOUNDARIES (Arbitrary-Boundary Law — stated, not hidden):
  • FAULT MODEL = entity loss (an entity is destroyed; its cascade disables downstream). It does NOT
    diagnose partial damage amounts, captures, timing, or sensor error. `fault-model = entity-loss`.
  • Minimal-CARDINALITY diagnoses only: it searches single faults, then pairs (configurable). A real
    triple-fault is outside the default search. `not-found ≠ absent`.
  • Consistency is checked over the OBSERVED entities only. Unobserved entities cannot disqualify a
    hypothesis — which is exactly why partial observation yields genuine ambiguity. `unobserved ≠ ok`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from itertools import combinations

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim, DEMO_WORLD   # noqa: E402
from artifacts import AnalysisResult, Finding, Limitation   # noqa: E402  (the shared honesty contract)

NOMINAL = (True, "ok")     # an entity's healthy observable state: alive and ok


@dataclass
class Diagnosis:
    hypothesis: str                       # human-readable explanation
    faults: tuple                         # the component set (entity ids), sorted
    confidence: float                     # RANKING WEIGHT in [0,1], normalized over rivals — NOT P(true)
    supporting_events: list = field(default_factory=list)
    contradicting_events: list = field(default_factory=list)
    suggested_observation: str | None = None


@dataclass
class GhostReport:
    observed: list                        # symptom descriptions (entity: observed-state)
    diagnoses: list                       # ranked list[Diagnosis]
    underdetermined: bool                 # True ⇒ ≥2 minimal rivals tie; competing explanations kept
    fault_model: str = "entity-loss"

    @property
    def best(self):
        return self.diagnoses[0] if self.diagnoses else None

    def report(self, index: int = 1) -> str:
        L = [f"Ghost #{index}", "", "Observed:"]
        L += [f"  - {s}" for s in self.observed] or ["  - (nothing anomalous)"]
        L += ["", "Possible causes  (ranking weight, NOT probability of truth):"]
        if not self.diagnoses:
            L.append("  - none within the entity-loss fault model — `not-explained ≠ no-cause`")
        for d in self.diagnoses:
            L.append(f"  {round(100 * d.confidence)}%  {d.hypothesis}")
            if d.supporting_events:
                L.append(f"        supported by: {d.supporting_events}")
            if d.contradicting_events:
                L.append(f"        contradicted by: {d.contradicting_events}")
        sug = next((d.suggested_observation for d in self.diagnoses if d.suggested_observation), None)
        L += ["", "Next observation:", f"  {sug if sug else '(none would distinguish the current rivals)'}"]
        if self.underdetermined:
            L.append("  [rivals tie — explanation is UNDERDETERMINED; observe the above to discriminate]")
        return "\n".join(L)

    def as_analysis(self) -> AnalysisResult:
        """Project into the shared honesty contract (a reporting boundary, not a supertype). Diagnosis is
        observation-based, so `source_trace` is empty; the scope is the observed entities."""
        findings = tuple(Finding("FAULT_HYPOTHESIS", "observed-entities", d.hypothesis) for d in self.diagnoses)
        if not findings:
            findings = (Finding("NO_HYPOTHESIS", "observed-entities",
                                "no explanation within the entity-loss fault model"),)
        limitations = (
            Limitation("observed-entities", "unobserved entities are not assumed healthy"),
            Limitation("model", "consistency ≠ causation; confidence is a ranking weight, not a probability"),
        )
        return AnalysisResult(source_trace=(), scope="observed-entities",
                              findings=findings, limitations=limitations)


# ---- kernel helpers -----------------------------------------------------------------------------
def _state_map(sim: WorldSim) -> dict:
    return {n: (sim.runtime[n]["alive"], sim.runtime[n]["status"]) for n in sim.cg.nodes}


def observe_after(world_text: str, events: list) -> dict:
    """Replay `events` on a fresh world and return the observed (alive, status) per entity."""
    sim = WorldSim(world_text)
    for ev in events:
        sim.apply_event(*ev)
    return _state_map(sim)


def _predict_faults(world_text: str, faults) -> dict:
    """Nominal model with exactly `faults` destroyed: the predicted observable state."""
    sim = WorldSim(world_text)
    for f in faults:
        if f in sim.cg.nodes and sim.runtime[f]["alive"]:
            sim.apply_event("destroy", f)
    return _state_map(sim)


def _upstream(sim: WorldSim, e: str) -> set:
    """Entities that can causally reach e (its potential root causes under the entity-loss model)."""
    return {s for s in sim.cg.nodes if e in sim.cg.reach_ge1(s)}


# ---- diagnosis ----------------------------------------------------------------------------------
def diagnose(world_text: str, observed: dict, trace: list = None, max_faults: int = 2,
             top_k: int = 5) -> GhostReport:
    """Given an OBSERVED (alive,status) map (full or partial), return ranked minimal fault explanations.

    `observed` need only cover the entities actually seen; consistency is judged on those keys alone.
    `trace`, if given (e.g. a kernel_check ghost path), annotates each hypothesis with supporting /
    contradicting events. Returns a GhostReport.
    """
    base = WorldSim(world_text)
    nodes = set(base.cg.nodes)
    obs_keys = [e for e in observed if e in nodes]
    symptoms = [e for e in obs_keys if observed[e] != NOMINAL]
    obs_desc = [f"{e}: {'destroyed' if not observed[e][0] else observed[e][1]}" for e in sorted(symptoms)]

    if not symptoms:
        return GhostReport(observed=[], diagnoses=[], underdetermined=False)

    # candidate pool: each symptom plus everything upstream of it (its possible root causes)
    pool = set()
    for e in symptoms:
        pool |= {e} | _upstream(base, e)
    pool &= nodes

    def explains(D) -> bool:
        pred = _predict_faults(world_text, D)
        return all(pred[e] == observed[e] for e in obs_keys)     # reproduce observation on observed keys

    def unobserved_overpred(D) -> int:
        pred = _predict_faults(world_text, D)
        return sum(1 for e in nodes if e not in obs_keys and pred[e] != NOMINAL)

    # minimal-cardinality search: singles, then pairs, ... stop at the first size that explains anything
    explainers = []
    for k in range(1, max_faults + 1):
        for combo in combinations(sorted(pool), k):
            if explains(combo):
                explainers.append(tuple(sorted(combo)))
        if explainers:
            break

    if not explainers:
        return GhostReport(observed=obs_desc, diagnoses=[], underdetermined=False)

    # rank: weight = parsimony-of-effects (fewer unobserved collateral predictions ⇒ higher), normalized
    raw = {D: 1.0 / (1.0 + unobserved_overpred(D)) for D in explainers}
    total = sum(raw.values()) or 1.0
    ordered = sorted(explainers, key=lambda D: (-raw[D], D))

    # discriminating observation: where do the top two rivals' predictions differ, outside what we saw?
    suggestion = None
    if len(ordered) >= 2:
        p1, p2 = _predict_faults(world_text, ordered[0]), _predict_faults(world_text, ordered[1])
        for e in sorted(nodes - set(obs_keys)):
            if p1[e] != p2[e]:
                s1 = "destroyed" if not p1[e][0] else p1[e][1]
                s2 = "destroyed" if not p2[e][0] else p2[e][1]
                suggestion = (f"Check {e}: '{'+'.join(ordered[0])}' predicts {s1}, "
                              f"'{'+'.join(ordered[1])}' predicts {s2}")
                break

    trace_str = [f"{ev[0]} {ev[1]}" for ev in (trace or []) if len(ev) >= 2]
    out = []
    for D in ordered[:top_k]:
        pred = _predict_faults(world_text, D)
        downstream = sorted(e for e in nodes if e not in D and pred[e] != NOMINAL)
        hyp = (f"entity loss: {'+'.join(D)} — its failure cascades to "
               f"{downstream if downstream else 'no downstream effects'}")
        supporting = [s for s in trace_str if any(s == f"destroy {f}" for f in D)]
        contradicting = [s for s in trace_str if any(s == f"repair {f}" for f in D)]
        out.append(Diagnosis(
            hypothesis=hyp, faults=D, confidence=round(raw[D] / total, 4),
            supporting_events=supporting, contradicting_events=contradicting,
            suggested_observation=suggestion,
        ))
    underdetermined = len(ordered) >= 2 and abs(raw[ordered[0]] - raw[ordered[1]]) < 1e-9
    return GhostReport(observed=obs_desc, diagnoses=out, underdetermined=underdetermined)


def from_ghost(world_text: str, ghost, observe: list = None) -> GhostReport:
    """Adapter: turn a kernel_check Violation (with .path) into a diagnosis. By default the observation
    is the full state after replaying the ghost path; pass `observe` to restrict to seen entities."""
    full = observe_after(world_text, ghost.path)
    obs = full if observe is None else {e: full[e] for e in observe if e in full}
    return diagnose(world_text, obs, trace=ghost.path)


def main():
    print("diagnose.py — model-based diagnosis over the causal kernel (the inverse of the checker)\n")
    # we (pretend not to) know the cause: reactor was destroyed. We only see the resulting world.
    observed = observe_after(DEMO_WORLD, [("destroy", "reactor")])
    rep = diagnose(DEMO_WORLD, observed, trace=[("destroy", "reactor")])
    print(rep.report(index=1))
    print("\n  — full observation pins a single cause. Now a PARTIAL observation (only the territory):\n")
    # two independent power sources for one symptom, but we only observe the symptom ⇒ genuine ambiguity
    AMB = """
world "Amb"
entity gen_a:
  position 0 0 0
  powers bus
entity gen_b:
  position 1 0 0
  powers bus
entity bus:
  position 2 0 0
  health 10
  powers light
entity light:
  position 3 0 0
  health 10
"""
    obs = {"bus": (True, "disabled"), "light": (True, "disabled")}   # bus & light out; which gen failed?
    rep2 = diagnose(AMB, obs)
    print(rep2.report(index=2))


if __name__ == "__main__":
    main()
