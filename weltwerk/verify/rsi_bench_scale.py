# SPDX-License-Identifier: AGPL-3.0-only
"""
rsi_bench_scale.py — the enterprise-evidence version of the RSI benchmark.

Upgrades over rsi_bench.py (which stays the minimal, verified reference):
  • SCALE + STATISTICS: a distribution of many seeded worlds; held-out paired comparison with a two-sided
    sign-test p-value, not a single point.
  • ADVERSARIAL CONTROL SUITE: baseline / random / greedy-blast / frequency / learned / memorizer / overfit.
    Requirement: only genuinely generalizing policies beat baseline on HELD-OUT.
  • TRAP STRUCTURES: high-blast decoys that are NOT restorers, so "rank by blast" (greedy) is actively wrong
    and the learned policy must find the real structural signal.
  • EFFICIENCY-PER-EXPERIMENT: verified-work reduction divided by training experiments (guards against
    "it only improved after a million examples").
  • ITERATED IMPROVEMENT CURVE: held-out work as the training log grows. Reported HONESTLY — on a one-shot-
    learnable task it saturates immediately; a sustained Policy0>Policy1>… decline requires a task that is
    not one-shot-learnable. We do not manufacture a decline.

Frozen throughout: engine (`ExplicitStateBFSEngine`), semantics, the fixed invariant. Every "restorer" is a
real engine re-verification (`repair._forbid_and_verify`), memoized. No policy authors its own metric.
`improved_map ≠ changed_criterion`; the benchmark is NULL-capable.
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                                  # noqa: E402
from kernel_check import check, build_alphabet                 # noqa: E402
from engine import ExplicitStateBFSEngine                      # noqa: E402
from repair import _forbid_and_verify                          # noqa: E402
import counterfactual                                          # noqa: E402

TAIL_OK = {"tail_ok": (lambda sim: sim.runtime["tail"]["status"] != "disabled")}
ENGINE = ExplicitStateBFSEngine()
N_TRAIN = 40
N_HELD = 40
# The ONLY tail_ok violation is `destroy hub` at depth 1, so a depth-2 search is provably sufficient to
# decide "restored" — and it keeps every re-verification cheap (deeper bounds blow up combinatorially).
BOUND = 2
_RESTORE = {}     # memo: (world, action) -> bool  (each entry is one real engine re-verification)


# ---- world distribution (with traps) ------------------------------------------------------------
def gen_world(seed: int) -> str:
    """faction → hub → tail is the ONLY path that can disable tail (unique restorer = forbid destroy hub).
    Plus a decoy chain, a second chain, and TRAP stars (high-blast non-restorers) so 'blast' is misleading."""
    rng = random.Random(seed)
    nd, ne, ntrap = rng.randint(2, 6), rng.randint(0, 3), rng.randint(0, 1)
    # seed in the name ⇒ every instance text is unique, so a text-keyed memorizer cannot hit held-out
    # (structural features are unaffected — the learned policy still generalizes). Prevents instance leakage.
    L = [f'world "RSI_{seed}"',
         'entity fac:', '  position 0 0 0', '  controls hub',
         'entity hub:', '  position 1 0 0', '  health 10', '  powers tail',
         'entity tail:', '  position 2 0 0', '  health 10']
    for i in range(nd):
        L += [f'entity d{i}:', f'  position {3 + i} 0 0', '  health 10']
        if i > 0:
            L.append(f'  powers d{i - 1}')
    for j in range(ne):
        L += [f'entity e{j}:', f'  position {3 + nd + j} 0 1', '  health 10']
        if j > 0:
            L.append(f'  powers e{j - 1}')
    for t in range(ntrap):                          # trap hub with several leaves ⇒ high blast, NOT a restorer
        leaves = rng.randint(2, 3)
        L += [f'entity th{t}:', f'  position {2 + t} 0 2', '  health 10']
        for k in range(leaves):
            L += [f'entity tl{t}_{k}:', f'  position {2 + t} {1 + k} 2', '  health 10']
            L.append(f'  powered_by th{t}')         # th{t} powers tl{t}_{k} (reversed kw) ⇒ th has high blast
    return "\n".join(L)


# ---- per-world structural features + ground truth ------------------------------------------------
def world_info(world: str) -> dict:
    sim = WorldSim(world)
    nodes = sim.cg.nodes
    alphabet = [tuple(a) for a in build_alphabet(sim)]
    res = check(world, max_depth=BOUND, invariants=TAIL_OK)
    ghost = {(e[0], e[1]) for e in res.ghost.path} if res.ghost else set()
    critical = set()
    if res.ghost:
        critical = {t for (_k, t) in counterfactual.analyze(world, res.ghost.path, TAIL_OK).critical}
    n = max(1, len(nodes))
    feats = {}
    for a in alphabet:
        kind, target = a[0], a[1]
        feats[a] = [len(sim.cg.reach_ge1(target)) / n,
                    1.0 if (kind, target) in ghost else 0.0,
                    1.0 if target in critical else 0.0,
                    1.0 if kind == "destroy" else 0.0]
    return {"world": world, "alphabet": alphabet, "feats": feats,
            "bound": BOUND, "violated": res.status == "VIOLATED"}


def restores(world: str, action, bound: int) -> bool:
    key = (world, tuple(action))
    if key not in _RESTORE:
        _RESTORE[key] = _forbid_and_verify(world, action, TAIL_OK, ENGINE, bound).status != "VIOLATED"
    return _RESTORE[key]


def restorer_set(info: dict) -> set:
    return {a for a in info["alphabet"] if restores(info["world"], a, info["bound"])}


def work(info: dict, order) -> int:
    """Lazy search cost: # of engine re-verifications until the first restorer (the true cost a policy pays)."""
    for i, a in enumerate(order, 1):
        if restores(info["world"], a, info["bound"]):
            return i
    return len(order) + 1


# ---- policies (orderings of the candidate actions) ----------------------------------------------
def _canonical(info):                       # baseline: deterministic canonical order
    return sorted(info["alphabet"])


def _random(info):
    return sorted(info["alphabet"], key=lambda a: hashlib.blake2b((info["world"] + repr(a)).encode()).hexdigest())


def _greedy_blast(info):                     # plausible-but-wrong: traps have high blast
    return sorted(info["alphabet"], key=lambda a: (-info["feats"][a][0], a))


def fit_learned(train):                      # mean-difference weights over all features
    pos, neg = [], []
    for info in train:
        rs = restorer_set(info)
        for a in info["alphabet"]:
            (pos if a in rs else neg).append(info["feats"][a])
    if not pos or not neg:
        return [0.0] * 4
    return [sum(v[j] for v in pos) / len(pos) - sum(v[j] for v in neg) / len(neg) for j in range(4)]


def _learned(info, w):
    canon = {a: i for i, a in enumerate(_canonical(info))}
    return sorted(info["alphabet"], key=lambda a: (-sum(wi * fi for wi, fi in zip(w, info["feats"][a])), canon[a]))


def fit_frequency(train):                    # weak 2-feature heuristic: P(restorer | kind, on_ghost)
    from collections import defaultdict
    tot, hit = defaultdict(int), defaultdict(int)
    for info in train:
        rs = restorer_set(info)
        for a in info["alphabet"]:
            sig = (a[0], info["feats"][a][1])
            tot[sig] += 1
            hit[sig] += int(a in rs)
    return {s: hit[s] / tot[s] for s in tot}


def _frequency(info, freq):
    canon = {a: i for i, a in enumerate(_canonical(info))}
    return sorted(info["alphabet"], key=lambda a: (-freq.get((a[0], info["feats"][a][1]), 0.0), canon[a]))


def _memorizer(info, memory):               # restorers-first if world seen in TRAIN, else baseline
    base = _canonical(info)
    known = memory.get(info["world"])
    return sorted(base, key=lambda a: (a not in known, base.index(a))) if known else base


def _overfit(info, memory):                 # restorers-first if seen, else RANDOM (no generalization)
    return _memorizer(info, memory) if info["world"] in memory else _random(info)


# ---- statistics ---------------------------------------------------------------------------------
def geomean(xs):
    xs = [x for x in xs if x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else 0.0


def sign_test_p(wins: int, losses: int) -> float:
    """Two-sided exact sign test under H0: P(policy faster) = 0.5."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(k + 1))
    return min(1.0, 2.0 * tail / (2 ** n))


def evaluate(held, order_fn) -> dict:
    wins = losses = 0
    regs, wp_list, wb_list = [], [], []
    hit_p = hit_b = 0
    for info in held:
        wb = work(info, _canonical(info))
        wp = work(info, order_fn(info))
        wb_list.append(wb); wp_list.append(wp)
        regs.append(wb / wp)
        wins += int(wp < wb); losses += int(wp > wb)
        hit_p += int(wp <= 3); hit_b += int(wb <= 3)
    return {"REG": round(geomean(regs), 3), "mean_work": round(sum(wp_list) / len(wp_list), 2),
            "mean_baseline_work": round(sum(wb_list) / len(wb_list), 2),
            "p_value": round(sign_test_p(wins, losses), 5), "wins": wins, "losses": losses,
            "budget3_hit": f"{hit_p}/{len(held)}", "budget3_baseline": f"{hit_b}/{len(held)}"}


# ---- the run ------------------------------------------------------------------------------------
def run(n_train=N_TRAIN, n_held=N_HELD, verbose=True) -> dict:
    train = [world_info(gen_world(s)) for s in range(n_train)]
    held = [world_info(gen_world(s)) for s in range(100000, 100000 + n_held)]
    w = fit_learned(train)
    freq = fit_frequency(train)
    memory = {info["world"]: restorer_set(info) for info in train}

    policies = {
        "baseline(canonical)": _canonical,
        "random": _random,
        "greedy_blast": _greedy_blast,
        "frequency": lambda info: _frequency(info, freq),
        "learned": lambda info: _learned(info, w),
        "memorizer": lambda info: _memorizer(info, memory),
        "overfit": lambda info: _overfit(info, memory),
    }
    results = {name: evaluate(held, fn) for name, fn in policies.items()}

    # efficiency: held-out verified-work reduction per training experiment (learned)
    base_mw = results["baseline(canonical)"]["mean_work"]
    eff = round((base_mw - results["learned"]["mean_work"]) / max(1, n_train), 4)

    # iterated improvement curve (honest; expect saturation on a one-shot-learnable task)
    curve = []
    k = 1
    while k <= n_train:
        wk = fit_learned(train[:k])
        curve.append((k, evaluate(held, lambda info, wk=wk: _learned(info, wk))["REG"]))
        k *= 2

    out = {"n_train": n_train, "n_held": n_held, "policies": results,
           "efficiency_per_train_experiment": eff, "iterated_curve_(k,REG)": curve,
           "weights": [round(x, 3) for x in w],
           "verdict_invariance": all(i["violated"] for i in train + held)}
    if verbose:
        print(f"rsi_bench_scale.py — enterprise RSI evidence  (train={n_train}, held={n_held}, frozen judge)\n")
        print(f"  {'policy':22s} {'REG':>6} {'mean_work':>10} {'p_value':>9} {'wins/loss':>10} {'budget3':>9}")
        for name, r in results.items():
            print(f"  {name:22s} {r['REG']:>6} {r['mean_work']:>10} {r['p_value']:>9} "
                  f"{str(r['wins'])+'/'+str(r['losses']):>10} {r['budget3_hit']:>9}")
        print(f"\n  baseline mean work: {base_mw}   efficiency/train-experiment: {eff}")
        print(f"  iterated curve (k, held-out REG): {curve}")
        print(f"  learned weights [blast,on_ghost,critical,destroy]: {out['weights']}")
        print(f"  verdict_invariance: {out['verdict_invariance']}")
        print("\n  Honest reading: a GENERALIZING policy has REG>1 with small p on HELD-OUT; memorizer/overfit")
        print("  collapse to REG≈1 (no transfer); greedy_blast (traps) should NOT beat baseline. The iterated")
        print("  curve saturates when the signal is one-shot-learnable — that is reported, not hidden.")
    return out


if __name__ == "__main__":
    run()
