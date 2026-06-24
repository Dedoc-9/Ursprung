# SPDX-License-Identifier: AGPL-3.0-only
"""
agent_transport.py — THE falsifier: does divergence stay sparse when identities MOVE?

Every cheap result so far was mortgaged to one assumption — that divergence stays sparse. It held under
RESOURCE DIFFUSION because diffusion ATTENUATES (a 10% leak damps the perturbation, so actual ≪ cone:
5 vs 60). Transport is different in kind: a migrating agent carries its WHOLE state across a chunk
boundary, with no attenuation. So divergence can ride a moving identity and *not* die out. This is the
MMO/FPS reality boundary — player movement is exactly where proximity and causality diverge.

MODEL: a ring of chunks. Local dynamics are chunk-local (reused from cow_world.step_chunk). Then a
MIGRATION phase: every alive agent in a resource-depleted chunk moves to its right neighbour, carrying
its identity and energy. Coupling is therefore directed (left → right), radius-1, and NON-attenuating.
An edit (cull predators in chunk c) changes who survives → who depletes a chunk → who migrates → the
divergence is carried downstream by the agents themselves.

THE MEASUREMENT (the bench delivers the verdict, not this file):
  cone_count  — chunks the divergence COULD have reached (directed reachability, drives cost)
  actual_count— chunks that genuinely differ from line A (the truth)
  sparsity    — peak_actual / peak_cone.  Diffusion gave ~0.08 (sparse). If transport gives ~1.0, the
                pruned allocator's economic advantage COLLAPSES (pruned ≈ conservative) and the
                divergence-aware-networking thesis fails for transport-dominated worlds. Either way is a
                result; the correctness story is untouched regardless.

CRUX (test): the by-difference reconstruction stays byte-identical to a full honest sim UNDER transport.
`diffusion-sparse ≠ transport-sparse`; `correctness-survives ≠ economics-survives`.
"""
from __future__ import annotations

from dataclasses import dataclass

from cow_world import ChunkState, Edit, Rules, apply_edit, genesis, snapshot_hash, step_chunk

MIGRATE_BELOW = 8          # an alive agent leaves (rightward) if its chunk's resource is at/below this


def _split(cs: ChunkState):
    """Depleted chunk ⇒ alive agents migrate (rightward); dead stay put. Else everyone stays.
    Decision depends only on cs (this chunk), keeping the stencil radius-1 and directed."""
    if cs.resource <= MIGRATE_BELOW:
        leavers = [a for a in cs.ents if a.alive]
        stayers = [a for a in cs.ents if not a.alive]
    else:
        leavers, stayers = [], list(cs.ents)
    return leavers, stayers


def next_chunk(get, d: int, n: int, rules: Rules, seed: int, tick: int) -> ChunkState:
    """next[d] = (stayers of d) + (right-migrants from the left neighbour). Local dynamics first, then
    transport. Depends on state[d] and state[left] only → directed radius-1 coupling."""
    left = (d - 1) % n
    inter_d = step_chunk(get(d), rules, seed, d, tick)
    inter_left = step_chunk(get(left), rules, seed, left, tick)
    _, d_stayers = _split(inter_d)
    left_leavers, _ = _split(inter_left)
    agents = tuple(sorted(d_stayers + left_leavers, key=lambda a: a.eid))
    return ChunkState(ents=agents, resource=inter_d.resource)


def full_sim_traced(snap: dict, rules: Rules, seed: int, horizon: int) -> tuple[list, int]:
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
class TransportResult:
    line_b: dict
    cone_count: tuple
    actual_count: tuple
    cost: int
    pruned: bool
    touched: frozenset = frozenset()

    @property
    def peak_cone(self) -> int:
        return max(self.cone_count)

    @property
    def peak_actual(self) -> int:
        return max(self.actual_count)


def reconstruct(snap: dict, rules: Rules, seed: int, edit: Edit, horizon: int, prune: bool) -> TransportResult:
    """Directed (rightward) counterfactual-by-difference. Divergence in chunk c can reach c+1 next tick
    (c+1 receives c's migrants), so the cone grows rightward; the frontier is base ∪ right(base)."""
    n = len(snap)
    traj_a, _ = full_sim_traced(snap, rules, seed, horizon)
    snap_b, rules_b, dirty0 = apply_edit(snap, rules, edit)

    tracked = set(dirty0)
    b_state = {c: snap_b[c] for c in tracked}
    cone_count = [len(tracked)]
    actual_count = [sum(1 for c in tracked if snap_b[c] != traj_a[0][c])]
    all_touched = set(tracked)
    cost = 0

    for t in range(horizon):
        base = {c for c in tracked if b_state[c] != traj_a[t][c]} if prune else set(tracked)
        frontier = set(base)
        for c in base:
            frontier.add((c + 1) % n)        # divergence is carried RIGHTWARD by migration
        get = lambda i, _t=t, _b=b_state: _b[i] if i in _b else traj_a[_t][i]
        new_b = {}
        for d in sorted(frontier):
            cost += get(d).count()
            new_b[d] = next_chunk(get, d, n, rules_b, seed, t)
        b_state = new_b
        tracked = frontier
        all_touched |= frontier
        cone_count.append(len(tracked))
        actual_count.append(sum(1 for d in b_state if b_state[d] != traj_a[t + 1][d]))

    line_b = dict(traj_a[horizon])
    for d in b_state:
        line_b[d] = b_state[d]
    return TransportResult(line_b=line_b, cone_count=tuple(cone_count), actual_count=tuple(actual_count),
                           cost=cost, pruned=prune, touched=frozenset(all_touched))


def brute_force_edit_future(snap: dict, rules: Rules, seed: int, edit: Edit, horizon: int) -> dict:
    snap_b, rules_b, _ = apply_edit(snap, rules, edit)
    return full_sim_traced(snap_b, rules_b, seed, horizon)[0][horizon]


def naive_cost(snap: dict, horizon: int) -> int:
    return sum(cs.count() for cs in snap.values()) * horizon


if __name__ == "__main__":
    snap = genesis(4000, 200, 0)
    rules, edit, H = Rules(), Edit("cull_pred_chunk", chunk=5), 60
    pru = reconstruct(snap, rules, 0, edit, H, prune=True)
    cons = reconstruct(snap, rules, 0, edit, H, prune=False)
    nv = naive_cost(snap, H)
    spar = pru.peak_actual / cons.peak_cone if cons.peak_cone else 0.0
    print("agent_transport.py — does divergence stay sparse when identities move?\n")
    print(f"  peak cone={cons.peak_cone}  peak actual={pru.peak_actual}  sparsity={spar:.2f}")
    print(f"  cost: pruned={pru.cost}  conservative={cons.cost}  naive={nv}  "
          f"(pruned/naive {pru.cost / nv:.1%}, pruned/conservative {pru.cost / cons.cost:.1%})")
    verdict = ("SPARSE — win survives transport" if spar < 0.5 else
               "DENSE — economic thesis FAILS under transport (correctness untouched)")
    print(f"  verdict: {verdict}")
