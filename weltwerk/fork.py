# SPDX-License-Identifier: AGPL-3.0-only
"""
fork.py — do(): the intervention primitive. "git diff for worlds."

This is the defining verb of the editor and the reason the whole stack exists: a measurement without
an intervention boundary is a claim generator. do() supplies the boundary. The developer does not edit
numbers — they edit a CAUSE, on a disposable shadow, and SEE the consequence before committing.

THE FLOW (every edit is a fork, never an in-place mutation of truth):

    committed world  (the Weltlinie, at the present tick)
        │  clone()                 clone()
        ├──────────────┐              │
        ▼              ▼              │
    line_A          line_B           │   line_A = unchanged future   (do nothing)
    run(H)        do(iv); run(H)      │   line_B = intervened future  (do(intervention))
        │              │              │
        └──── WorldDiff.compute ──────┘   "under this declared model, here is what changed"
                       │
              commit(iv)  OR  discard()
                       │
                       ▼
    commit applies the INTERVENTION to the committed present and logs an edit event.
    It does NOT freeze the simulated horizon as truth — prediction ≠ committed trajectory.
    The future then re-derives live. discard() leaves the Weltlinie untouched; the shadows evaporate.

SEPARATORS this file keeps:
  prediction ≠ causation        (the horizon run is a PREVIEW; only commit() writes a cause)
  shadow ≠ committed            (line_A / line_B are disposable; the committed world is observed by all)
  diff ≠ verdict                (a WorldDiff reports deltas under a declared model — it does not say
                                 the edit was "good"; that judgment is the developer's, or a later
                                 observer's allocation, never this file's)
  estimate ≠ property           (every number here is "under toy-ecology-v0", not a fact about reality)
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from world import REGIME, Agent, Ruleset, World


# --- interventions: a declared cause, applied to a shadow ---------------------------------------
@dataclass(frozen=True)
class Intervention:
    """A do(). `kind` selects the operator; `params` are its arguments. The empty/identity
    intervention exists so the diff machinery can be tested against a known-zero result."""
    kind: str
    params: tuple = ()
    note: str = ""

    def label(self) -> str:
        if self.kind == "identity":
            return "do(nothing)  [identity / control]"
        return f"do({self.kind}{self.params})" + (f"  — {self.note}" if self.note else "")


def identity() -> Intervention:
    return Intervention("identity", (), "control: must produce an empty diff")


def remove_resource(loc: str) -> Intervention:
    return Intervention("remove_resource", (loc,), f"zero the resource node at {loc}")


def cull_species(species: str) -> Intervention:
    return Intervention("cull_species", (species,), f"set {species} population = 0")


def set_param(field_name: str, value) -> Intervention:
    return Intervention("set_param", (field_name, value), f"ruleset.{field_name} := {value!r}")


def spawn(aid: str, species: str, loc: str, energy: int) -> Intervention:
    return Intervention("spawn", (aid, species, loc, energy), f"introduce {species} at {loc}")


def apply_intervention(w: World, iv: Intervention) -> World:
    """Mutate a SHADOW world in place (caller must pass a clone, never the committed world).
    Returns the same world for chaining. Records the edit in the shadow's provenance log."""
    if iv.kind == "identity":
        pass
    elif iv.kind == "remove_resource":
        (loc,) = iv.params
        if loc in w.resources:
            w.resources[loc] = 0
    elif iv.kind == "cull_species":
        (species,) = iv.params
        for aid in sorted(w.agents):
            a = w.agents[aid]
            if a.species == species and a.alive:
                w.agents[aid] = replace(a, alive=False, energy=0)
    elif iv.kind == "set_param":
        (field_name, value) = iv.params
        w.rules = replace(w.rules, **{field_name: value})
    elif iv.kind == "spawn":
        (aid, species, loc, energy) = iv.params
        w.agents[aid] = Agent(aid=aid, species=species, loc=loc, energy=energy)
    else:
        raise ValueError(f"unknown intervention kind: {iv.kind!r}")
    w.log.append(f"INTERVENTION @tick {w.tick}: {iv.label()}")
    return w


# --- the diff: what changed, under this declared model ------------------------------------------
@dataclass(frozen=True)
class WorldDiff:
    horizon: int
    intervention_label: str
    regime: str
    population_delta: dict           # species -> (B - A)
    alive_delta: int                 # total alive  (B - A)
    resource_delta: dict             # location -> (B - A)
    survival_flips: dict             # original aid -> ("A_only"|"B_only"|"both"|"neither")
    hash_a: str
    hash_b: str

    @property
    def empty(self) -> bool:
        return self.hash_a == self.hash_b

    @staticmethod
    def compute(line_a: World, line_b: World, horizon: int, label: str) -> "WorldDiff":
        pa, pb = line_a.population(), line_b.population()
        pop_delta = {s: pb.get(s, 0) - pa.get(s, 0) for s in sorted(set(pa) | set(pb))}
        res_delta = {L: line_b.resources.get(L, 0) - line_a.resources.get(L, 0)
                     for L in sorted(set(line_a.resources) | set(line_b.resources))}
        flips: dict[str, str] = {}
        originals = sorted(set(line_a.agents) & set(line_b.agents))
        for aid in originals:
            in_a = line_a.agents[aid].alive
            in_b = line_b.agents[aid].alive
            flips[aid] = ("both" if in_a and in_b else
                          "A_only" if in_a else
                          "B_only" if in_b else "neither")
        return WorldDiff(
            horizon=horizon,
            intervention_label=label,
            regime=REGIME["model"],
            population_delta=pop_delta,
            alive_delta=len(line_b.alive_agents()) - len(line_a.alive_agents()),
            resource_delta=res_delta,
            survival_flips=flips,
            hash_a=line_a.state_hash(),
            hash_b=line_b.state_hash(),
        )

    def render(self) -> str:
        if self.empty:
            head = f"  WORLD DIFF  [{self.intervention_label}]  → IDENTICAL (no causal effect under model)"
            return head + f"\n    horizon={self.horizon} ticks · regime={self.regime}"
        lines = [f"  WORLD DIFF  [{self.intervention_label}]  (horizon={self.horizon} ticks · under {self.regime})",
                 f"    alive (total):   {self.alive_delta:+d}",
                 f"    population:      " + ", ".join(f"{s} {d:+d}" for s, d in self.population_delta.items()),
                 f"    resources:       " + ", ".join(f"{L} {d:+d}" for L, d in self.resource_delta.items())]
        flipped = {k: v for k, v in self.survival_flips.items() if v in ("A_only", "B_only")}
        if flipped:
            lines.append("    survival flips:  " + ", ".join(
                f"{k}:{'lived-only-without-edit' if v == 'A_only' else 'lived-only-with-edit'}"
                for k, v in flipped.items()))
        lines.append("    NOTE: deltas are 'B − A' under the declared model — not a prediction of reality.")
        return "\n".join(lines)


# --- the fork object: a TRAJECTORY PAIR (the streamtube boundary around causation) ---------------
@dataclass
class Fork:
    committed: World            # the authoritative Weltlinie (reference, not a copy)
    intervention: Intervention
    horizon: int
    line_a: World               # unchanged future, final state (preview)
    line_b: World               # intervened future, final state (preview)
    diff: WorldDiff             # EXACT-under-model state delta
    trace_a: tuple = ()         # per-tick feature vectors of the unchanged leg (the trajectory)
    trace_b: tuple = ()         # per-tick feature vectors of the intervened leg
    observations: dict = field(default_factory=dict)  # name -> Observation (ESTIMATES; allocation, not truth)

    def observe(self, observer) -> "object":
        """Attach an observer. The observer is a function of ONE trajectory; the Fork hands it both
        legs to diff. Result is an Observation carrying its own evidence class — never folded into the
        EXACT WorldDiff. (See observers.py.)"""
        obs = observer.diff(self.trace_a, self.trace_b)
        self.observations[obs.name] = obs
        return obs

    def observe_all(self, observers) -> dict:
        for ob in observers:
            self.observe(ob)
        return self.observations

    def report(self) -> str:
        """Render EXACT (WorldDiff) and ESTIMATE (observer) registers SEPARATELY — an estimate must
        never borrow the authority of an exact-under-model delta."""
        out = [self.diff.render()]
        if self.observations:
            out.append("  ── observer estimates (allocation, not verdict; can be wrong inside the model) ──")
            for name in sorted(self.observations):
                out.append(self.observations[name].render())
        return "\n".join(out)

    def commit(self) -> World:
        """The ONLY write to truth. Applies the intervention to the committed PRESENT and logs an
        edit event. Does NOT install the simulated horizon — the future re-derives live.
        (prediction ≠ committed trajectory.)"""
        apply_intervention(self.committed, self.intervention)
        self.committed.log.append(
            f"COMMIT @tick {self.committed.tick}: {self.intervention.label()} "
            f"(previewed {self.horizon} ticks; alive Δ was {self.diff.alive_delta:+d})")
        return self.committed

    def discard(self) -> World:
        """Leave the Weltlinie untouched. The shadows evaporate; only this decision is recorded."""
        self.committed.log.append(f"DISCARD @tick {self.committed.tick}: rejected {self.intervention.label()}")
        return self.committed


def _run_traced(w: World, n: int) -> tuple[World, tuple]:
    """Run n ticks while recording the feature vector at every tick — so a Fork is a TRAJECTORY,
    not just an endpoint. The trace is what trajectory-geometry observers (orbit, generativity) read."""
    trace = [w.features()]
    for _ in range(n):
        w.step()
        trace.append(w.features())
    return w, tuple(trace)


def fork(committed: World, iv: Intervention, horizon: int = 20) -> Fork:
    """Branch reality. Run the unchanged future (A) and the intervened future (B) on the SAME dice,
    from the same present, capturing each leg's full trajectory, and diff them. Neither preview
    touches the committed world."""
    line_a, trace_a = _run_traced(committed.clone(), horizon)
    line_b, trace_b = _run_traced(apply_intervention(committed.clone(), iv), horizon)
    diff = WorldDiff.compute(line_a, line_b, horizon, iv.label())
    return Fork(committed=committed, intervention=iv, horizon=horizon,
                line_a=line_a, line_b=line_b, diff=diff, trace_a=trace_a, trace_b=trace_b)


if __name__ == "__main__":
    from world import genesis
    w = genesis(seed=0).run(5)             # let the world settle a few ticks
    print("fork.py — do(): git diff for worlds\n")
    print(f"  committed present: tick={w.tick} pop={w.population()} res={dict(sorted(w.resources.items()))}\n")
    for iv in (identity(), cull_species("predator"), remove_resource("forest")):
        f = fork(w, iv, horizon=20)
        print(f.diff.render())
        print()
    print("  (committed world is untouched — we only previewed; commit() would write the edit)")
    print(f"  committed present after previews: tick={w.tick} pop={w.population()}  (unchanged)")
