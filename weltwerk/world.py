# SPDX-License-Identifier: AGPL-3.0-only
"""
world.py — the Weltlinie: a minimal *deterministic, replayable* authoritative world.

This is NOT a game, a renderer, or an MMO. It is the smallest authoritative substrate that the
Weltwerk loop needs in order to be real: a world whose entire trajectory is a pure function of
(seed, ruleset, n_steps), so that it can be replayed bitwise and forked without ambiguity.

It embodies the discipline proven in experiments/live_world_kernel/live_world_kernel.py —
committed truth is distinct from speculative scratch — but at the *world-state* granularity the
editor needs, rather than the single-edit granularity the kernel proved.

INVARIANTS (enforced, not hoped):
  * Determinism:   run(seed, N) is bitwise-identical on every machine with PYTHONHASHSEED=0.
                   State advances only through a seeded PRNG and sorted iteration — never through
                   dict-ordering luck or wall-clock.
  * Authority:     the committed World is the only thing other layers may treat as true. A clone
                   (the shadow timeline) is DISPOSABLE and observed by no one until promoted.
  * Declared regime: this world's rules are a MODEL. `REGIME` names the assumptions. A diff computed
                   here is true "under this declared model", never "the future".

SEPARATORS this file keeps:
  simulation-state ≠ rendered-appearance   (there is no rendering here at all)
  committed ≠ speculative                  (clone() makes a shadow; the original is never touched)
  deterministic ≠ valid                    (reproducible does not mean the rules are right —
                                            replay proves the trajectory, not the model)

What this file deliberately does NOT do: it does not score the world, does not decide whether an
edit was "good", and does not know about observers (orbit/generativity/cost). Those are the Wirkfeld
layer; they READ this state and allocate attention — they never define truth here.
"""
from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field, replace
from hashlib import blake2b

# --- the declared regime ------------------------------------------------------------------------
# Naming the model so a diff is read as "under THIS", not "in reality". Changing any of these
# changes what every downstream measurement means.
REGIME = {
    "model": "toy-ecology-v0",
    "species": ("villager", "predator", "trader"),
    "locations": ("forest", "river", "settlement"),
    "assumptions": (
        "discrete synchronous ticks (no sub-tick ordering)",
        "energy is an integer scalar proxy for 'alive-ness' (not metabolism)",
        "movement is greedy-toward-resource (no planning, no memory)",
        "conflict is a pairwise coin-flip at a shared location (no tactics)",
        "resource regen is location-local and rule-driven (no weather, no season)",
    ),
}


@dataclass(frozen=True)
class Ruleset:
    """The world's laws. A MODEL CONSTRUCT — every field is a declared convenience, not an invariant."""
    hunger_per_tick: int = 1
    eat_gain: int = 4
    reproduce_threshold: int = 12
    reproduce_cost: int = 6
    start_energy: int = 8
    regen_rate: int = 2
    regen_cap: int = 20
    predation_enabled: bool = True
    predation_prob_pct: int = 60  # integer percent, kept integer for exact replay


@dataclass(frozen=True)
class Agent:
    aid: str
    species: str
    loc: str
    energy: int
    alive: bool = True


@dataclass
class World:
    """Authoritative world state. Mutable in place during a step, but a step is a pure function of
    (prior state, rng stream). Clone before any speculative mutation — never edit the committed one."""
    tick: int
    rules: Ruleset
    agents: dict[str, Agent]          # aid -> Agent (insertion-ordered; we iterate sorted for determinism)
    resources: dict[str, int]         # location -> units
    seed: int
    _rng_calls: int = 0               # how many PRNG draws consumed — part of the replayable state
    log: list[str] = field(default_factory=list)  # provenance breadcrumbs (record, never authority)
    _next_id: int = 0

    # -- determinism spine --------------------------------------------------------------------
    def _rng(self) -> random.Random:
        # Reconstruct the exact stream position from (seed, calls). Reconstruction, not a live handle,
        # so a clone resumes the identical stream — replay integrity over convenience.
        r = random.Random(self.seed)
        for _ in range(self._rng_calls):
            r.random()
        return r

    def _draw(self) -> float:
        r = random.Random(self.seed)
        for _ in range(self._rng_calls):
            r.random()
        val = r.random()
        self._rng_calls += 1
        return val

    def state_hash(self) -> str:
        """Canonical, order-independent digest of the committed state (excludes the prose log)."""
        h = blake2b(digest_size=16)
        h.update(f"t={self.tick};rc={self._rng_calls};seed={self.seed}".encode())
        for aid in sorted(self.agents):
            a = self.agents[aid]
            h.update(f"|A:{a.aid}:{a.species}:{a.loc}:{a.energy}:{int(a.alive)}".encode())
        for loc in sorted(self.resources):
            h.update(f"|R:{loc}:{self.resources[loc]}".encode())
        h.update(("|rules:" + repr(self.rules)).encode())
        return h.hexdigest()

    def clone(self) -> "World":
        """A DISPOSABLE shadow. Deep-copied; mutating it cannot touch the committed original.
        It resumes the identical PRNG stream, so 'what if' is measured on the same dice, not new luck."""
        return World(
            tick=self.tick,
            rules=self.rules,
            agents=copy.deepcopy(self.agents),
            resources=dict(self.resources),
            seed=self.seed,
            _rng_calls=self._rng_calls,
            log=[],                # shadow keeps its own provenance; it inherits none of the committed prose
            _next_id=self._next_id,
        )

    def alive_agents(self) -> list[Agent]:
        return [self.agents[k] for k in sorted(self.agents) if self.agents[k].alive]

    def population(self) -> dict[str, int]:
        pop = {s: 0 for s in REGIME["species"]}
        for a in self.alive_agents():
            pop[a.species] = pop.get(a.species, 0) + 1
        return pop

    def features(self) -> tuple[int, ...]:
        """A canonical, fixed-width integer feature vector for trajectory geometry.
        Ordering is fixed by REGIME (not dict luck) so a trajectory is comparable across legs.
        This is a MODEL PROJECTION — it discards position, identity, age, and history; an observer
        reading it sees only this coarse-grained shadow of the state (declared, lossy on purpose)."""
        pop = self.population()
        species = tuple(pop[s] for s in REGIME["species"])
        locs = tuple(self.resources.get(L, 0) for L in REGIME["locations"])
        return (len(self.alive_agents()),) + species + locs

    # -- the one rule of motion ---------------------------------------------------------------
    def step(self) -> None:
        """Advance one synchronous tick. Pure in (state, rng); deterministic under sorted iteration."""
        rules = self.rules
        # 1) hunger
        for aid in sorted(self.agents):
            a = self.agents[aid]
            if a.alive:
                self.agents[aid] = replace(a, energy=a.energy - rules.hunger_per_tick)
        # 2) starvation
        for aid in sorted(self.agents):
            a = self.agents[aid]
            if a.alive and a.energy <= 0:
                self.agents[aid] = replace(a, alive=False, energy=0)
        # 3) eat (villagers/traders consume resources at their location)
        for aid in sorted(self.agents):
            a = self.agents[aid]
            if a.alive and a.species != "predator" and self.resources.get(a.loc, 0) > 0:
                self.resources[a.loc] -= 1
                self.agents[aid] = replace(a, energy=a.energy + rules.eat_gain)
        # 4) predation (predator vs prey sharing a location, coin-flip)
        if rules.predation_enabled:
            for aid in sorted(self.agents):
                pred = self.agents[aid]
                if not (pred.alive and pred.species == "predator"):
                    continue
                prey_here = [k for k in sorted(self.agents)
                             if self.agents[k].alive and self.agents[k].species != "predator"
                             and self.agents[k].loc == pred.loc]
                if prey_here and self._draw() * 100 < rules.predation_prob_pct:
                    victim = prey_here[0]
                    self.agents[victim] = replace(self.agents[victim], alive=False, energy=0)
                    self.agents[aid] = replace(pred, energy=pred.energy + rules.eat_gain)
        # 5) migration (greedy toward the richest neighbouring resource)
        richest = max(self.resources, key=lambda L: (self.resources[L], L)) if self.resources else None
        if richest is not None:
            for aid in sorted(self.agents):
                a = self.agents[aid]
                if a.alive and a.species != "predator" and self.resources.get(a.loc, 0) == 0:
                    self.agents[aid] = replace(a, loc=richest)
        # 6) reproduction
        for aid in sorted(self.agents):
            a = self.agents[aid]
            if a.alive and a.energy >= rules.reproduce_threshold:
                child = Agent(aid=f"{a.species[0]}{self._next_id}", species=a.species,
                              loc=a.loc, energy=rules.start_energy, alive=True)
                self._next_id += 1
                self.agents[child.aid] = child
                self.agents[aid] = replace(a, energy=a.energy - rules.reproduce_cost)
        # 7) resource regen
        for loc in sorted(self.resources):
            self.resources[loc] = min(rules.regen_cap, self.resources[loc] + rules.regen_rate)
        self.tick += 1
        self.log.append(f"tick {self.tick}: pop={self.population()} res={dict(sorted(self.resources.items()))}")

    def run(self, n: int) -> "World":
        for _ in range(n):
            self.step()
        return self


def genesis(seed: int = 0, rules: Ruleset | None = None) -> World:
    """A small, fixed starting world (1 map, a handful of agents, 3 resource nodes).
    Deterministic given seed; the seed only drives stochastic rules (predation), never the layout."""
    rules = rules or Ruleset()
    agents: dict[str, Agent] = {}

    def add(aid: str, species: str, loc: str) -> None:
        agents[aid] = Agent(aid=aid, species=species, loc=loc, energy=rules.start_energy)

    add("v0", "villager", "settlement")
    add("v1", "villager", "settlement")
    add("v2", "villager", "forest")
    add("t0", "trader", "settlement")
    add("p0", "predator", "forest")
    add("p1", "predator", "river")

    resources = {"forest": 10, "river": 6, "settlement": 4}
    return World(tick=0, rules=rules, agents=agents, resources=resources, seed=seed, _next_id=0)


if __name__ == "__main__":
    w = genesis(seed=0).run(20)
    print("world.py — the Weltlinie (deterministic authoritative world)")
    print(f"  regime: {REGIME['model']}  |  tick={w.tick}  pop={w.population()}")
    print(f"  state_hash={w.state_hash()}")
    print("  (run weltwerk/test_weltwerk.py to verify determinism, shadow isolation, diff soundness)")
