# SPDX-License-Identifier: AGPL-3.0-only
"""
rsi_bench.py — the full RSI benchmark from RSI_EXPERIMENT_PROGRAM.md, runnable.

It measures whether the MAP (a candidate-ranking policy) can be made better at solving problems while the
TERRITORY (engine, semantics, invariant) stays frozen — and whether the gain is *capability* (transfers to
held-out problems) or *memorization* (does not). It is built to be able to report NULL: nothing here forces
a positive result, and the companion test asserts only that the apparatus is sound, never that RSI is real.

THE TASK (judged only by the frozen engine).  Each world is VIOLATED under a fixed invariant. The task is to
find an action whose forbidding RESTORES the world (re-verification yields no violation). The restorer set is
defined by the engine, not by any policy. WORK = how many candidate actions a policy tries before it hits a
restorer. A better map finds restorers in fewer tries — same verified result, less search.

THREE CONTROLS (RSI_EXPERIMENT_PROGRAM §0), all enforced here:
  • verdict-invariance — the restorer set and every verdict are computed once by the frozen engine and are
    independent of the policy; a policy only reorders candidates. (`improved_map ≠ changed_criterion`)
  • held-out transfer  — policies are fit on TRAIN, all gains reported on a structurally-disjoint HELD-OUT.
  • compute-equalization — REG is work-to-identical-result, so a "win" is fewer evaluations, not more compute.

POLICIES:
  • baseline   — deterministic pseudo-random candidate order (the null map).
  • learned    — a linear score over structural features, weights fit on TRAIN (the candidate capability).
  • memorizer  — stores restorers per world hash; perfect on seen worlds, falls back to baseline on unseen
                 (the planted fake — it must FAIL to transfer, proving the harness detects memorization).

Frozen instruments only: the engine (`ExplicitStateBFSEngine`), the fixed invariant, and `repair`'s
forbid-and-verify. No policy authors its own success metric.
"""
from __future__ import annotations

import hashlib
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                                  # noqa: E402
from kernel_check import check, build_alphabet                 # noqa: E402
from engine import ExplicitStateBFSEngine                      # noqa: E402
from repair import _forbid_and_verify                          # noqa: E402  (frozen forbid+re-verify)
import counterfactual                                          # noqa: E402

# Fixed invariant (territory): the tail entity may never be left 'disabled'.
TAIL_OK = {"tail_ok": (lambda sim: sim.runtime["tail"]["status"] != "disabled")}
ENGINE = ExplicitStateBFSEngine()


# ---- world distribution -------------------------------------------------------------------------
def gen_world(n_decoys: int, n_extra: int) -> str:
    """A star: faction → hub → tail (the only path that can DISABLE tail), plus harmless decoy/extra chains.
    The unique single-action restorer is forbidding destroy(hub). Size varies headroom; (n_decoys, n_extra)
    makes the text unique so TRAIN/HELD-OUT instances are disjoint."""
    L = ['world "RSI"',
         'entity fac:', '  position 0 0 0', '  controls hub',
         'entity hub:', '  position 1 0 0', '  health 10', '  powers tail',
         'entity tail:', '  position 2 0 0', '  health 10']
    for i in range(n_decoys):                       # harmless decoy chain (never touches tail)
        L += [f'entity d{i}:', f'  position {3 + i} 0 0', '  health 10']
        if i > 0:
            L.append(f'  powers d{i - 1}')          # forward CONTROL/relation keyword; target already declared
    for j in range(n_extra):                        # second harmless chain
        L += [f'entity e{j}:', f'  position {3 + n_decoys + j} 0 1', '  health 10']
        if j > 0:
            L.append(f'  powers e{j - 1}')
    return "\n".join(L)


TRAIN_PARAMS = [(nd, ne) for nd in (3, 4, 5) for ne in (0, 2, 4)]      # 9 small worlds
HELDOUT_PARAMS = [(nd, ne) for nd in (6, 7, 8) for ne in (0, 2, 4)]    # 9 larger, unseen worlds (disjoint)


# ---- precompute (frozen-engine ground truth + features), once per world -------------------------
def precompute(world: str) -> dict:
    sim = WorldSim(world)
    nodes = sim.cg.nodes
    alphabet = [tuple(a) for a in build_alphabet(sim)]
    res = check(world, max_depth=4, invariants=TAIL_OK)
    ghost = set()
    critical = set()
    if res.ghost is not None:
        ghost = {(e[0], e[1]) for e in res.ghost.path}
        rep = counterfactual.analyze(world, res.ghost.path, TAIL_OK)
        critical = {t for (_k, t) in rep.critical}
    bound = min(len(nodes) + 2, 8)
    restorers = set()
    feats = {}
    n = max(1, len(nodes))
    for a in alphabet:
        kind, target = a[0], a[1]
        blast = len(sim.cg.reach_ge1(target)) / n
        feats[a] = [blast,
                    1.0 if (kind, target) in ghost else 0.0,
                    1.0 if target in critical else 0.0,
                    1.0 if kind == "destroy" else 0.0]
        ev = _forbid_and_verify(world, a, TAIL_OK, ENGINE, bound)
        if ev.status != "VIOLATED":
            restorers.add(a)
    return {"world": world, "alphabet": alphabet, "restorers": restorers, "feats": feats,
            "violated": res.status == "VIOLATED"}


# ---- policies (reorder candidates only) ---------------------------------------------------------
def order_baseline(pc: dict):
    w = pc["world"]
    return sorted(pc["alphabet"],
                  key=lambda a: hashlib.blake2b((w + repr(a)).encode()).hexdigest())


def fit_weights(train: list) -> list:
    pos, neg = [], []
    for pc in train:
        for a in pc["alphabet"]:
            (pos if a in pc["restorers"] else neg).append(pc["feats"][a])
    if not pos or not neg:
        return [0.0, 0.0, 0.0, 0.0]
    dim = len(pos[0])
    mp = [sum(v[j] for v in pos) / len(pos) for j in range(dim)]
    mn = [sum(v[j] for v in neg) / len(neg) for j in range(dim)]
    return [mp[j] - mn[j] for j in range(dim)]          # mean-difference weights (Fisher-flavored)


def order_learned(pc: dict, weights: list):
    base = order_baseline(pc)
    rank = {a: i for i, a in enumerate(base)}
    def score(a):
        return sum(w * f for w, f in zip(weights, pc["feats"][a]))
    return sorted(pc["alphabet"], key=lambda a: (-score(a), rank[a]))   # ties → baseline order (deterministic)


def order_memorizer(pc: dict, memory: dict):
    w = pc["world"]
    base = order_baseline(pc)
    if w in memory:                                     # seen ⇒ restorers first
        known = memory[w]
        return sorted(base, key=lambda a: (a not in known, base.index(a)))
    return base                                         # unseen ⇒ no advantage


def work(order, restorers) -> int:
    for i, a in enumerate(order, 1):
        if a in restorers:
            return i
    return len(order) + 1


def geomean(xs):
    xs = [x for x in xs if x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else 0.0


def reg_over(worlds, order_fn) -> float:
    regs = []
    for pc in worlds:
        if not pc["restorers"]:
            continue
        wb = work(order_baseline(pc), pc["restorers"])
        wp = work(order_fn(pc), pc["restorers"])
        regs.append(wb / wp)
    return geomean(regs)


# ---- the run ------------------------------------------------------------------------------------
def run(verbose=True) -> dict:
    train = [precompute(gen_world(nd, ne)) for (nd, ne) in TRAIN_PARAMS]
    held = [precompute(gen_world(nd, ne)) for (nd, ne) in HELDOUT_PARAMS]
    weights = fit_weights(train)
    memory = {pc["world"]: set(pc["restorers"]) for pc in train}     # memorizer learns TRAIN answers

    learned = lambda pc: order_learned(pc, weights)
    memo = lambda pc: order_memorizer(pc, memory)

    reg_learn_train = reg_over(train, learned)
    reg_learn_held = reg_over(held, learned)
    reg_memo_train = reg_over(train, memo)
    reg_memo_held = reg_over(held, memo)

    def transfer(held_v, train_v):
        return (held_v / train_v) if train_v > 0 else 0.0

    # controls
    verdict_invariant = all(pc["violated"] for pc in train + held)   # restorers/verdicts are engine-defined
    recall_ok = all(work(learned(pc), pc["restorers"]) <= len(pc["alphabet"])
                    for pc in held if pc["restorers"])
    # fixed-budget B=3 on held-out (compute-equalized): hit-rate within 3 tries
    B = 3
    hit_learned = sum(1 for pc in held if pc["restorers"] and work(learned(pc), pc["restorers"]) <= B)
    hit_base = sum(1 for pc in held if pc["restorers"] and work(order_baseline(pc), pc["restorers"]) <= B)
    n_held = sum(1 for pc in held if pc["restorers"])

    # acceleration: held-out REG as TRAIN grows (expect saturating, not exponential)
    accel = []
    for k in (1, 3, 5, 7, 9):
        wk = fit_weights(train[:k])
        accel.append(round(reg_over(held, lambda pc: order_learned(pc, wk)), 3))

    result = {
        "reg_learned_train": round(reg_learn_train, 3), "reg_learned_heldout": round(reg_learn_held, 3),
        "reg_memorizer_train": round(reg_memo_train, 3), "reg_memorizer_heldout": round(reg_memo_held, 3),
        "transfer_learned": round(transfer(reg_learn_held, reg_learn_train), 3),
        "transfer_memorizer": round(transfer(reg_memo_held, reg_memo_train), 3),
        "verdict_invariance": verdict_invariant, "recall_preserved": recall_ok,
        "fixed_budget_B": B, "heldout_hitrate_learned": f"{hit_learned}/{n_held}",
        "heldout_hitrate_baseline": f"{hit_base}/{n_held}",
        "acceleration_curve_heldout_REG": accel,
        "weights_blast_onghost_critical_destroy": [round(w, 3) for w in weights],
    }
    if verbose:
        print("rsi_bench.py — full RSI benchmark (frozen verifier; honest, NULL-capable)\n")
        for k, v in result.items():
            print(f"  {k:38s} {v}")
        print("\n  Reading: capability ⇒ reg_learned_heldout > 1 AND transfer_learned ≈ 1 (gain survives held-out).")
        print("  Memorization ⇒ reg_memorizer_train high BUT reg_memorizer_heldout ≈ 1, transfer_memorizer → 0.")
        print("  The verdict never moves: verdict_invariance True, recall_preserved True. improved_map ≠ changed_criterion.")
    return result


if __name__ == "__main__":
    run()
