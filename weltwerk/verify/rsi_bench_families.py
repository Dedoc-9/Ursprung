# SPDX-License-Identifier: AGPL-3.0-only
"""
rsi_bench_families.py — Proof Obligation PO-5: bounded, SATURATING multi-iteration accrual on a task that is
provably NOT one-shot-learnable.

WHY THIS EXISTS (and what PO-6 already settled). `compute_control_bench` (PO-6) showed the natural restore
task is *one-shot*: a single linear fit ranks the restorer first at budget B=1. There is nothing for a second
iteration to add — so the saturation-at-k=1 seen in `rsi_bench_scale` is a property of THAT task, not evidence
about the loop. PO-5 asks the complementary question: WHEN a task is constructed to demand iteration, can the
improvement loop deliver genuine multi-round accrual, and does it saturate? If yes, then "RSI" here is real
but BOUNDED and TASK-GATED — never open-ended, never second-order. That is the whole, deflationary claim.

THE FAMILY. Each world has one true cause (a hub that powers a protected `tail`) among D decoy hubs. The engine
restorer is, and is verified to be, exactly `destroy <cause>` (forbidding it makes `tail` un-disable-able;
forbidding anything else leaves the violation). So the LABEL is a frozen engine fact. The trick is the
GEOMETRY of the features the learner sees: each action carries two observable binary tags — the coordinate
parities (px%2, py%2) of its target. We construct worlds so the cause is the unique action with
`px%2 XOR py%2 == 1`; every decoy and the tail have `XOR == 0`. The tags are ARBITRARY observables
(Arbitrary-Boundary Law) — what matters is only the LEARNABILITY GEOMETRY: the label is XOR-shaped in them.

WHY THAT FORCES ITERATION. A mean-difference linear policy on (f0,f1) provably gets ~zero weight on XOR (both
class-conditional means are 0.5) — it cannot rank the cause above chance, and MORE DATA cannot fix a missing
linear signal. An additive (boosting-style) loop over the four conjunction indicators CAN: round 1 captures
one cause-parity, round 2 the other, and then it saturates at the representable ceiling. So:

  • one-shot linear control      → stays at chance (provably; the not-one-shot witness)
  • equal-LABEL data-scaling      → stays at chance (the gain is capacity, not data)
  • iterated additive loop        → work(k) decreases over rounds, then SATURATES (the bounded accrual)

The criterion (engine, invariant, restorer label) is FROZEN across all iterations; only the policy changes.
`integrity ≠ truth`; `iteration ≠ open-ended`; this is first-order, saturating, task-gated accrual — and it is
labelled as exactly that, never as second-order self-improvement.
"""
from __future__ import annotations

import os
import sys
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                         # noqa: E402
from kernel_check import build_alphabet                # noqa: E402
from engine import ExplicitStateBFSEngine             # noqa: E402
from repair import _forbid_and_verify                  # noqa: E402

ENGINE = ExplicitStateBFSEngine()
BOUND = 2
N_DECOY = 6
TAIL_OK = {"tail_ok": (lambda s: s.runtime["tail"]["status"] != "disabled")}

TRAIN_SEEDS = range(0, 40)
HELD_SEEDS = range(1000, 1040)            # disjoint from train; mixed parity (consecutive)
MOREDATA_SEEDS = range(0, 160)            # 4× labels for the data-scaling control

_RESTORE: dict = {}


# ---- world family ------------------------------------------------------------------------------
def gen_world(seed: int, n_decoy: int = N_DECOY) -> str:
    """One world. Cause is the unique XOR-positive hub (px%2 != py%2) and the only powerer of `tail`."""
    ct = (0, 1) if seed % 2 == 0 else (1, 0)           # cause coord-parities: XOR == 1 either way
    L = [f'world "FAM_{seed}"', 'entity fac:', '  position 0 0 0', '  controls cause']
    for i in range(n_decoy):
        L.append(f'  controls d{i}')
    L += ['entity cause:', f'  position {ct[0]} {ct[1]} 0', '  health 10', '  powers tail']
    for i in range(n_decoy):
        a = (seed + i) % 2                              # decoy parity bit (both coords share it ⇒ XOR == 0)
        L += [f'entity d{i}:', f'  position {20 + 2 * i + a} {40 + 2 * i + a} 0', '  health 10']
    L += ['entity tail:', '  position 2 2 0', '  health 10']     # (2,2) ⇒ XOR == 0
    return "\n".join(L) + "\n"


def _tiebreak(world: str, action) -> str:
    """Pseudo-random, deterministic tie-break so zero-score policies sit at CHANCE (not at a name-sorted
    advantage — 'cause' would otherwise sort first alphabetically and fake a perfect linear policy)."""
    return hashlib.blake2b((world + repr(tuple(action))).encode()).hexdigest()


def world_info(world: str) -> dict:
    sim = WorldSim(world)
    cands = [tuple(a) for a in build_alphabet(sim) if a[0] == "destroy"]   # destroys can prevent a destroy
    feat = {}
    for a in cands:
        x, y, _ = sim._pos(a[1])
        feat[a] = (int(x) % 2, int(y) % 2)
    return {"world": world, "cands": cands, "feat": feat}


# ---- engine ground truth (frozen criterion) -----------------------------------------------------
def restores(world: str, action) -> bool:
    key = (world, tuple(action))
    if key not in _RESTORE:
        _RESTORE[key] = _forbid_and_verify(world, action, TAIL_OK, ENGINE, BOUND).status != "VIOLATED"
    return _RESTORE[key]


def restorer_set(info: dict) -> set:
    return {a for a in info["cands"] if restores(info["world"], a)}


def work(info: dict, order) -> int:
    """Lazy engine search cost: re-verifications until the first true restorer in the policy's order."""
    for i, a in enumerate(order, 1):
        if restores(info["world"], a):
            return i
    return len(order) + 1


# ---- features / learners ------------------------------------------------------------------------
CONJ = [lambda f: (1 - f[0]) * (1 - f[1]),   # c00
        lambda f: (1 - f[0]) * f[1],         # c01
        lambda f: f[0] * (1 - f[1]),         # c10
        lambda f: f[0] * f[1]]               # c11


def _samples(infos):
    """(feature, label) pooled over candidate actions. Label = construction (target=='cause'); the test
    `construction_valid` proves this equals the engine restorer set, so the label is engine-grounded."""
    out = []
    for info in infos:
        for a in info["cands"]:
            out.append((info["feat"][a], 1 if a[1] == "cause" else 0))
    return out


def fit_linear(infos):
    """One-shot mean-difference weights on the raw tags. Provably ~0 on XOR ⇒ chance, at ANY sample size."""
    s = _samples(infos)
    pos = [f for f, y in s if y == 1]
    neg = [f for f, y in s if y == 0]
    if not pos or not neg:
        return (0.0, 0.0)
    return tuple(sum(p[k] for p in pos) / len(pos) - sum(n[k] for n in neg) / len(neg) for k in (0, 1))


def fit_boosting(infos, rounds: int):
    """Greedy L2 (least-squares) boosting over the four conjunction indicators. Returns [(conj_idx, step)]."""
    s = _samples(infos)
    if not s:
        return []
    preds = [0.0] * len(s)
    chosen = []
    for _ in range(rounds):
        best = None
        for j, c in enumerate(CONJ):
            num = sum((y - p) * c(f) for (f, y), p in zip(s, preds))
            den = sum(c(f) ** 2 for (f, _y) in s)
            if den == 0:
                continue
            step = num / den
            reduction = step * step * den           # SSE drop from adding step·c_j
            if best is None or reduction > best[0]:
                best = (reduction, j, step)
        if best is None or best[0] <= 1e-12:
            break                                    # residual exhausted ⇒ saturated
        _r, j, step = best
        chosen.append((j, step))
        for i, (f, _y) in enumerate(s):
            preds[i] += step * CONJ[j](f)
    return chosen


def _score_boost(feat, model):
    return sum(step * CONJ[j](feat) for j, step in model)


def order_linear(info, w):
    return sorted(info["cands"],
                  key=lambda a: (-(w[0] * info["feat"][a][0] + w[1] * info["feat"][a][1]),
                                 _tiebreak(info["world"], a)))


def order_boost(info, model):
    return sorted(info["cands"],
                  key=lambda a: (-_score_boost(info["feat"][a], model), _tiebreak(info["world"], a)))


# ---- the experiment -----------------------------------------------------------------------------
def run(rounds_max: int = 3, n_decoy: int = N_DECOY) -> dict:
    train = [world_info(gen_world(s, n_decoy)) for s in TRAIN_SEEDS]
    held = [world_info(gen_world(s, n_decoy)) for s in HELD_SEEDS]
    more = [world_info(gen_world(s, n_decoy)) for s in MOREDATA_SEEDS]

    def mean_work(infos, order_fn):
        return sum(work(i, order_fn(i)) for i in infos) / len(infos)

    # iterated loop: held-out work as a function of #boosting rounds (k = 0..rounds_max)
    curve = []
    for k in range(0, rounds_max + 1):
        model = fit_boosting(train, k)
        curve.append((k, mean_work(held, lambda i, m=model: order_boost(i, m))))

    # controls (one-shot)
    w_base = fit_linear(train)
    w_more = fit_linear(more)
    linear_work = mean_work(held, lambda i: order_linear(i, w_base))
    moredata_work = mean_work(held, lambda i: order_linear(i, w_more))

    chance = (len(held[0]["cands"]) + 1) / 2.0
    return {
        "curve": curve,                                   # [(k, held_work)]
        "boost_k0": curve[0][1], "boost_final": curve[-1][1],
        "saturated": abs(curve[-1][1] - curve[-2][1]) < 1e-9,
        "linear_work": linear_work, "moredata_work": moredata_work,
        "linear_weights": w_base, "moredata_weights": w_more,
        "chance": chance, "n_held": len(held), "n_train": len(train), "n_decoy": n_decoy,
    }


def main():
    print("rsi_bench_families.py — PO-5: bounded multi-iteration accrual on a NOT-one-shot (XOR) task\n")
    r = run()
    print(f"  worlds: train={r['n_train']} held={r['n_held']} decoys={r['n_decoy']}   "
          f"chance work ≈ {r['chance']:.1f}\n")
    print("  iterated loop — held-out work vs #boosting rounds k:")
    for k, wv in r["curve"]:
        print(f"    k={k}: held work = {wv:.2f}")
    print(f"\n  one-shot linear control:        {r['linear_work']:.2f}   weights={tuple(round(x,3) for x in r['linear_weights'])}")
    print(f"  data-scaling control (4× data): {r['moredata_work']:.2f}   weights={tuple(round(x,3) for x in r['moredata_weights'])}")
    print(f"  accrual: k=0 {r['boost_k0']:.2f} → k={r['curve'][-1][0]} {r['boost_final']:.2f}   "
          f"saturated={r['saturated']}")
    print("\n  Reading: linear (one-shot) and data-scaling stay near chance — the task is provably not")
    print("  one-shot-learnable and not a data problem. The iterated loop climbs, then SATURATES at the")
    print("  representable ceiling. Bounded, task-gated, first-order accrual. iteration ≠ open-ended RSI.")


if __name__ == "__main__":
    main()
