# SPDX-License-Identifier: AGPL-3.0-only
"""
cow_world.py — the scaling probe: does fork-and-observe survive a 1000× larger world?

This is NOT the editable world (that is ../world.py); it is a stripped chunked world built to MEASURE
one thing: the *cost* of a counterfactual fork as the state grows. It tests two cost claims that are
easy to conflate (conflating them would be its own inflation):

  CLAIM A — the fork is O(1).            Copy-on-write: a fork shares an immutable base and starts with
                                         an empty overlay. (Measured: fork_cost.)
  CLAIM B — the counterfactual costs     You always pay O(N·H) ONCE for the authoritative line A (you
            only its blast radius.       cannot know reality for free). Line B (the edit) REUSES A's
                                         trajectory for every chunk the edit does not touch, and
                                         re-simulates only the dirty region: O(dirty·H), not a second
                                         O(N·H). (Measured: cf_cost vs naive_cf_cost.)

THE LOAD-BEARING FINDING (a real result, stated as one):
  Locality of EFFECT requires locality of RANDOMNESS. A single global RNG stream couples every chunk —
  a local edit shifts the draw sequence everywhere and the dirty set explodes to N. So each chunk draws
  from a POSITIONAL stream seed(s, chunk, tick). With chunk-local rules the dirty set stays constant;
  cross-chunk coupling would grow it as a light-cone (the declared boundary, ../README Phase 5).

SEPARATORS:
  fork-is-cheap ≠ simulation-is-cheap   (A is paid in full; only the COUNTERFACTUAL is marginal)
  cheaper-mechanism ≠ different-answer  (test_cow asserts by-difference B == full honest sim of B,
                                         byte-identical — the No-Strength-Creation discipline, on compute)
  op-count ≠ wall-clock                 (we report deterministic entity-step counts; wall-clock is a
                                         nondeterministic secondary, never the verdict)

DELIBERATE OMISSIONS (declared): no reproduction (entity set is fixed, so chunk membership is static
and the experiment is about cost, not population growth); no cross-chunk coupling in the base rules
(added coupling is the light-cone boundary case, measured separately).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace


# --- positional randomness: the prerequisite for locality ---------------------------------------
def _chunk_rng(seed: int, chunk: int, tick: int) -> random.Random:
    """A stream keyed by POSITION, not by history. Chunk d's draws are independent of chunk c's past,
    so a local edit in c cannot desync d. This is what makes the dirty set local."""
    s = ((seed & 0x7FFFFFFF) * 73856093) ^ (chunk * 19349663) ^ (tick * 83492791)
    return random.Random(s & 0x7FFFFFFF)


@dataclass(frozen=True)
class Ent:
    eid: int
    species: str   # "prey" | "pred"
    energy: int
    alive: bool = True


@dataclass(frozen=True)
class ChunkState:
    """One chunk's entire state. Frozen + value-equal so 'did this chunk change?' is a cheap ==."""
    ents: tuple          # tuple[Ent], sorted by eid
    resource: int

    def count(self) -> int:
        return len(self.ents)


@dataclass(frozen=True)
class Rules:
    hunger: int = 1
    eat_gain: int = 3
    start_energy: int = 6
    predation_prob_pct: int = 50
    predation_enabled: bool = True
    regen_rate: int = 2
    regen_cap: int = 30


Snapshot = dict          # chunk_id(int) -> ChunkState


# --- the one chunk-local rule (pure: (state, rules, seed, chunk, tick) -> state) -----------------
def step_chunk(cs: ChunkState, rules: Rules, seed: int, chunk: int, tick: int) -> ChunkState:
    rng = _chunk_rng(seed, chunk, tick)
    ents = {e.eid: e for e in cs.ents}
    resource = cs.resource
    order = sorted(ents)

    # 1) hunger + starvation
    for eid in order:
        e = ents[eid]
        if e.alive:
            ne = e.energy - rules.hunger
            ents[eid] = replace(e, energy=max(0, ne), alive=ne > 0)

    # 2) prey eat the chunk resource (deterministic eid order)
    for eid in order:
        e = ents[eid]
        if e.alive and e.species == "prey" and resource > 0:
            resource -= 1
            ents[eid] = replace(e, energy=e.energy + rules.eat_gain)

    # 3) predation (each pred may take one prey in-chunk; positional coin-flip)
    if rules.predation_enabled:
        for eid in order:
            p = ents[eid]
            if not (p.alive and p.species == "pred"):
                continue
            prey = [k for k in order if ents[k].alive and ents[k].species == "prey"]
            if prey and rng.random() * 100 < rules.predation_prob_pct:
                ents[prey[0]] = replace(ents[prey[0]], alive=False, energy=0)
                ents[eid] = replace(p, energy=p.energy + rules.eat_gain)

    # 4) resource regen
    resource = min(rules.regen_cap, resource + rules.regen_rate)
    return ChunkState(ents=tuple(ents[k] for k in order), resource=resource)


def full_sim(snap: Snapshot, rules: Rules, seed: int, horizon: int) -> tuple[Snapshot, int]:
    """The authoritative line: simulate EVERY chunk H ticks. Cost = total entity-steps (O(N·H))."""
    state = dict(snap)
    cost = 0
    for t in range(horizon):
        nxt = {}
        for c in sorted(state):
            cost += state[c].count()
            nxt[c] = step_chunk(state[c], rules, seed, c, t)
        state = nxt
    return state, cost


# --- the edit + the counterfactual-by-difference ------------------------------------------------
@dataclass(frozen=True)
class Edit:
    kind: str            # "cull_pred_chunk" (LOCAL) | "set_rule" (GLOBAL)
    chunk: int = -1
    rule_field: str = ""
    rule_value: object = None

    def label(self) -> str:
        if self.kind == "cull_pred_chunk":
            return f"LOCAL do(cull predators in chunk {self.chunk})"
        return f"GLOBAL do(rules.{self.rule_field} := {self.rule_value!r})"


def apply_edit(snap: Snapshot, rules: Rules, edit: Edit) -> tuple[Snapshot, Rules, set]:
    """Return (edited snapshot, edited rules, dirty chunk set). Dirty = chunks whose FUTURE diverges
    from line A. A rules change is global ⇒ every chunk dirty (no reuse). A local state edit ⇒ only
    that chunk dirty (clean chunks provably reuse A: same inputs, same positional RNG, local rules)."""
    if edit.kind == "cull_pred_chunk":
        c = edit.chunk
        cs = snap[c]
        ents = tuple(replace(e, alive=False, energy=0) if e.species == "pred" else e for e in cs.ents)
        new_snap = dict(snap)
        new_snap[c] = ChunkState(ents=ents, resource=cs.resource)
        return new_snap, rules, {c}
    elif edit.kind == "set_rule":
        new_rules = replace(rules, **{edit.rule_field: edit.rule_value})
        return dict(snap), new_rules, set(snap.keys())   # global: all chunks dirty
    raise ValueError(f"unknown edit kind {edit.kind!r}")


@dataclass(frozen=True)
class CounterfactualResult:
    line_a: Snapshot          # authoritative future (no edit)
    line_b: Snapshot          # edited future (reconstructed)
    dirty: frozenset
    a_cost: int               # O(N·H) — paid once, this is reality
    cf_cost: int              # O(dirty·H) — the MARGINAL cost of the counterfactual
    naive_cf_cost: int        # O(N·H) — what a full re-sim of the edit would cost
    fork_cost_cow: int        # 0 — COW fork shares the base
    fork_cost_clone: int      # N — a deepcopy fork

    def diff_chunks(self) -> list:
        """Chunks that actually differ A vs B (cheap: only dirty chunks CAN differ)."""
        return sorted(c for c in self.dirty if self.line_a[c] != self.line_b[c])


def counterfactual(snap: Snapshot, rules: Rules, seed: int, edit: Edit, horizon: int) -> CounterfactualResult:
    """Fork reality and diff it — at scale. Pay for line A once; the edit reuses A for clean chunks and
    simulates only the dirty region."""
    line_a, a_cost = full_sim(snap, rules, seed, horizon)
    snap_b, rules_b, dirty = apply_edit(snap, rules, edit)

    # simulate ONLY dirty chunks under the edited rules; clean chunks inherit line A
    state = {c: snap_b[c] for c in dirty}
    cf_cost = 0
    for t in range(horizon):
        nxt = {}
        for c in sorted(dirty):
            cf_cost += state[c].count()
            nxt[c] = step_chunk(state[c], rules_b, seed, c, t)
        state = nxt
    line_b = dict(line_a)
    for c in dirty:
        line_b[c] = state[c]

    n_entities = sum(cs.count() for cs in snap.values())
    return CounterfactualResult(
        line_a=line_a, line_b=line_b, dirty=frozenset(dirty),
        a_cost=a_cost, cf_cost=cf_cost, naive_cf_cost=n_entities * horizon,
        fork_cost_cow=0, fork_cost_clone=n_entities,
    )


def brute_force_edit_future(snap: Snapshot, rules: Rules, seed: int, edit: Edit, horizon: int) -> Snapshot:
    """The HONEST baseline: apply the edit and fully simulate the whole edited world. The
    by-difference reconstruction must match this byte-for-byte, or the optimization is invalid."""
    snap_b, rules_b, _ = apply_edit(snap, rules, edit)
    final, _ = full_sim(snap_b, rules_b, seed, horizon)
    return final


def snapshot_hash(snap: Snapshot) -> str:
    from hashlib import blake2b
    h = blake2b(digest_size=16)
    for c in sorted(snap):
        cs = snap[c]
        h.update(f"|C{c}:r{cs.resource}".encode())
        for e in cs.ents:
            h.update(f":{e.eid},{e.species},{e.energy},{int(e.alive)}".encode())
    return h.hexdigest()


def genesis(n_entities: int, n_chunks: int, seed: int = 0) -> Snapshot:
    """Distribute n_entities across n_chunks deterministically (~half prey / half pred)."""
    snap: Snapshot = {c: None for c in range(n_chunks)}
    buckets: dict[int, list] = {c: [] for c in range(n_chunks)}
    for eid in range(n_entities):
        c = eid % n_chunks
        species = "prey" if eid % 2 == 0 else "pred"
        buckets[c].append(Ent(eid=eid, species=species, energy=6))
    for c in range(n_chunks):
        snap[c] = ChunkState(ents=tuple(buckets[c]), resource=20)
    return snap


if __name__ == "__main__":
    snap = genesis(n_entities=2000, n_chunks=50, seed=0)
    rules = Rules()
    r = counterfactual(snap, rules, seed=0, edit=Edit("cull_pred_chunk", chunk=7), horizon=20)
    print("cow_world.py — counterfactual-by-difference at scale\n")
    print(f"  entities={sum(cs.count() for cs in snap.values())} chunks={len(snap)} horizon=20")
    print(f"  edit: {Edit('cull_pred_chunk', chunk=7).label()}")
    print(f"  fork_cost:  cow={r.fork_cost_cow}  vs  clone={r.fork_cost_clone}")
    print(f"  line A (reality, paid once): {r.a_cost} entity-steps")
    print(f"  counterfactual: cow_marginal={r.cf_cost}  vs  naive_full={r.naive_cf_cost}"
          f"  ({r.cf_cost / r.naive_cf_cost:.1%} of naive)")
    print(f"  dirty chunks={sorted(r.dirty)}  actually-differ={r.diff_chunks()}")
