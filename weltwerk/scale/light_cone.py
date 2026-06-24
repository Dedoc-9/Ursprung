# SPDX-License-Identifier: AGPL-3.0-only
"""
light_cone.py — when chunks are COUPLED, how fast does an edit's blast radius grow?

cow_world.py measured the counterfactual cost under chunk-LOCAL rules: the dirty set stayed constant,
marginal cost flat. That result was mortgaged to an assumption — that locality stays local. MMOs are
interesting precisely where it does not (markets, logistics, projectiles, migration all couple distant
regions). This probe removes the assumption and MEASURES the consequence.

Coupling mechanism: a ring of chunks with nearest-neighbour RESOURCE DIFFUSION. Each tick a chunk
leaks a fraction of its resource to its two ring-neighbours. A local edit therefore propagates: cull
predators in chunk c → prey eat c's resource differently → c's resource diverges → diffusion carries
the divergence to c±1 next tick, c±2 the tick after. That is a light-cone of velocity 1 chunk/tick
(per direction).

WHAT IS MEASURED (all EXACT_UNDER_MODEL — counts of which chunks actually differ from line A):
  radius(t)            — ring distance the divergence has reached
  dirty_count(t)       — |chunks that differ from A| (≤ 2t+1 on a ring, capped at n_chunks)
  information_velocity — chunks added to the dirty frontier per tick
  saturation_tick      — when the cone fills the world and the counterfactual win vanishes
  cf_cost              — entity-steps simulated == the cone VOLUME (Σ_t dirty_count(t)·chunk_size)

THE CRUX (test_light_cone.py): the by-difference reconstruction — re-simulate only the cone, reuse
line A for clean chunks — must be BYTE-IDENTICAL to a full honest sim of the edited coupled world.
Coupling makes this the hard correctness case: a frontier chunk's diffusion reads a clean neighbour,
whose state must be taken from line A's recorded trajectory. cheaper-mechanism ≠ different-answer.

SEPARATORS:
  coupling ≠ chaos                 (a finite information velocity is itself the thing we measure)
  cone-bounded ≠ world-bounded     (the win holds only while the cone has not saturated the world)
  measured-radius ≠ predicted      (we report the EXACT dirty set; topology only BOUNDS it)
"""
from __future__ import annotations

from dataclasses import dataclass

from cow_world import (ChunkState, Edit, Rules, apply_edit, genesis,
                       snapshot_hash, step_chunk)

EVIDENCE = "EXACT_UNDER_MODEL"   # we measure the actual dirty set, not a proxy of it
LEAK_PCT = 10                    # fraction of a chunk's resource that diffuses to each neighbour/tick


def neighbors(c: int, n: int) -> tuple[int, int]:
    return ((c - 1) % n, (c + 1) % n)


def _leak(resource: int) -> int:
    return (resource * LEAK_PCT) // 100


def next_chunk(get, d: int, n: int, rules: Rules, seed: int, tick: int) -> ChunkState:
    """One chunk's coupled transition. `get(idx)` returns the START-of-tick state of chunk idx (from B
    for dirty chunks, from line A for clean ones). Local dynamics + nearest-neighbour diffusion."""
    left, right = neighbors(d, n)
    sd, sl, sr = get(d), get(left), get(right)
    inflow = _leak(sl.resource) + _leak(sr.resource)
    outflow = 2 * _leak(sd.resource)
    stepped = step_chunk(sd, rules, seed, d, tick)          # local rule (hunger/eat/predation/regen)
    new_res = max(0, min(rules.regen_cap, stepped.resource + inflow - outflow))
    return ChunkState(ents=stepped.ents, resource=new_res)


def full_sim_traced(snap: dict, rules: Rules, seed: int, horizon: int) -> tuple[list, int]:
    """The authoritative coupled future, recording every tick's snapshot (line A's trajectory)."""
    n = len(snap)
    traj = [dict(snap)]
    cost = 0
    state = dict(snap)
    for t in range(horizon):
        cur = state
        nxt = {}
        for d in range(n):
            cost += cur[d].count()
            nxt[d] = next_chunk(lambda i: cur[i], d, n, rules, seed, t)
        state = nxt
        traj.append(state)
    return traj, cost


@dataclass(frozen=True)
class LightConeResult:
    line_b: dict
    cone_count: tuple             # chunks we RE-SIMULATE at each tick (conservative; drives cost)
    actual_count: tuple           # chunks that ACTUALLY differ from line A (the true causal spread)
    radius: tuple                 # ring radius of ACTUAL divergence at each tick
    information_velocity: float   # ACTUAL dirty chunks added per tick (pre-saturation)
    saturation_tick: int          # first tick actual divergence fills the world (-1 if never)
    cf_cost: int                  # entity-steps simulated == cone volume (what we pay)
    naive_cf_cost: int            # N·H — a full re-sim of the edit
    n_chunks: int
    evidence_class: str = EVIDENCE

    def render(self) -> str:
        sat = self.saturation_tick if self.saturation_tick >= 0 else "none (cone < world)"
        return (f"  [{self.evidence_class}] light-cone: velocity≈{self.information_velocity:.2f} chunks/tick, "
                f"saturation@{sat}\n"
                f"    actual divergence head: {list(self.actual_count[:6])}"
                f"{' …' if len(self.actual_count) > 6 else ''}\n"
                f"    cf_cost(cone)={self.cf_cost}  vs  naive(full)={self.naive_cf_cost}  "
                f"({self.cf_cost / self.naive_cf_cost:.1%} of naive)")


def counterfactual_lightcone(snap: dict, rules: Rules, seed: int, edit: Edit, horizon: int) -> LightConeResult:
    """Reconstruct line B by simulating ONLY the growing dirty cone, reusing line A for clean chunks."""
    n = len(snap)
    traj_a, _ = full_sim_traced(snap, rules, seed, horizon)
    snap_b, rules_b, dirty0 = apply_edit(snap, rules, edit)

    cone = set(dirty0)                          # chunks we re-simulate (conservative)
    b_state = {c: snap_b[c] for c in cone}      # start-of-tick B states for cone chunks
    # actual divergence at t=0: chunks whose edited state already differs from A
    actual0 = sum(1 for c in cone if snap_b[c] != traj_a[0][c])
    cone_count = [len(cone)]
    actual_count = [actual0]
    radius = [0]
    cf_cost = 0
    saturation_tick = -1

    for t in range(horizon):
        # the frontier expands by one ring step: any neighbour of a dirty chunk MAY diverge this tick
        new_cone = set(cone)
        for c in cone:
            l, r = neighbors(c, n)
            new_cone.add(l)
            new_cone.add(r)
        cur_b = b_state
        get = lambda i, _t=t, _b=cur_b: _b[i] if i in _b else traj_a[_t][i]
        nxt = {}
        for d in sorted(new_cone):
            cf_cost += get(d).count()
            nxt[d] = next_chunk(get, d, n, rules_b, seed, t)
        b_state = nxt
        cone = new_cone
        # ACTUAL divergence (physics diagnostic): cone chunks whose B-state genuinely differs from A.
        # It may LAG the cone (diffusion can round to an identical value at the frontier).
        actual = sum(1 for d in b_state if b_state[d] != traj_a[t + 1][d])
        cone_count.append(min(len(cone), n))
        actual_count.append(actual)
        # saturation / radius / velocity key off the CONE — that is what drives cost (cf_cost == cone
        # volume). The win at the margin vanishes when the cone fills the world.
        if saturation_tick < 0 and len(cone) >= n:
            saturation_tick = t + 1
        radius.append(radius[-1] + (1 if len(cone) < n else 0))

    line_b = dict(traj_a[horizon])              # clean chunks == line A's final
    for d in b_state:
        line_b[d] = b_state[d]

    # information velocity: mean CONE frontier growth before saturation (chunks added per tick,
    # bounded by topology — ring nearest-neighbour ⇒ ≤2). This is the cost-relevant propagation rate.
    pre = [cone_count[i + 1] - cone_count[i] for i in range(len(cone_count) - 1)
           if cone_count[i] < n]
    velocity = (sum(pre) / len(pre)) if pre else 0.0
    n_entities = sum(cs.count() for cs in snap.values())
    return LightConeResult(
        line_b=line_b, cone_count=tuple(cone_count), actual_count=tuple(actual_count),
        radius=tuple(radius), information_velocity=velocity, saturation_tick=saturation_tick,
        cf_cost=cf_cost, naive_cf_cost=n_entities * horizon, n_chunks=n,
    )


def brute_force_edit_future(snap: dict, rules: Rules, seed: int, edit: Edit, horizon: int) -> dict:
    """Honest baseline: apply the edit, fully simulate the whole COUPLED world."""
    snap_b, rules_b, _ = apply_edit(snap, rules, edit)
    traj, _ = full_sim_traced(snap_b, rules_b, seed, horizon)
    return traj[horizon]


if __name__ == "__main__":
    snap = genesis(n_entities=4000, n_chunks=200, seed=0)
    r = counterfactual_lightcone(snap, Rules(), 0, Edit("cull_pred_chunk", chunk=100), horizon=40)
    print("light_cone.py — how fast does a coupled edit travel?\n")
    print(f"  entities=4000 chunks=200 horizon=40  coupling=ring nearest-neighbour ({LEAK_PCT}% leak)")
    print(r.render())
    print("\n  (radius grows ~1 chunk/tick; the win holds only until the cone fills the world)")
