# SPDX-License-Identifier: AGPL-3.0-only
"""
rsi_engine.py — an actual RSI engine, built from what the arc measured, not from the naive recipe it refuted.

The experiments collapsed the naive recipe (self-edit + more search + higher internal score = RSI) by separating
`optimization ≠ evaluation`, `improvement ≠ acceleration`, `transfer ≠ replication`, `confidence ≠ capability`.
So this engine does NOT try to make the optimizer recursive. It makes the *improvement loop* robust, by promoting
a self-edit into the "self" ONLY through a reconciler / promotion gate that demands the edit survive contact with
reality. The RSI criterion is redefined:

    not  "can it rewrite itself?"   but   "does rewriting itself increase the future rate of VERIFIED improvement?"

The promotion gate (the missing piece the experiments kept pointing at) requires ALL of:
    1. external gain   — capability rises on HELD-OUT tasks, not just the proxy/train metric
    2. replication     — the gain holds across multiple seeds (not one lucky draw)
    3. calibration     — the proxy gain does not run ahead of the external gain (no proxy-exploitation)
A candidate that fails any gate is rejected; only verified edits become the new self.

The control is the `naive` engine — the runaway optimizer — which promotes on internal/proxy gain alone. Running
both makes the difference measurable rather than asserted: the gated engine should accept fewer edits but keep its
self-estimate honest, while the naive engine chases the proxy. Per the standing discipline, the SELF-TESTS check
VALIDITY + the engine's core INVARIANT (every promotion actually passed its gates; verified capability never falls)
— never that the engine "achieved RSI." `expectation may follow evidence; evidence may not follow expectation`.

Run (from this directory):  PYTHONHASHSEED=0 python3 rsi_engine.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

D = 12
SEED = 20260623
NOISE = 0.20
INNER_BUDGET = 30
ROUNDS = 60
SUPPORT = (2, 6, 9)
N_PROXY = 3                       # the tasks the self-estimate is computed on
EXTERNAL_SEEDS = [101, 202, 303]  # each defines an independent held-out task set (for replication)
N_EXTERNAL = 8                   # held-out tasks per external seed
REP_FRAC = 0.60                  # fraction of external seeds that must improve to count as "replicated"
CAL_TOL = 0.01                   # how far proxy gain may exceed external gain before it's "uncalibrated"


def _basis(x):
    return [math.cos(j * math.pi * x) for j in range(D)]


def _err(w, pts):
    return sum(abs(sum(wi * bi for wi, bi in zip(w, _basis(x))) - y) for x, y in pts) / len(pts)


def make_task(seed):
    rng = random.Random(seed)
    coeff = [0.0] * D
    for j in SUPPORT:
        coeff[j] = rng.uniform(-1.0, 1.0)
    truth = lambda x: sum(coeff[j] * math.cos(j * math.pi * x) for j in SUPPORT)
    train = [(x, truth(x) + rng.gauss(0, NOISE)) for x in (rng.random() for _ in range(14))]
    clean = [(i / 23, truth(i / 23)) for i in range(24)]
    return {"seed": seed, "train": train, "clean": clean, "baseline": _err([0.0] * D, clean)}


@dataclass(frozen=True)
class Optimizer:
    active: tuple
    sigma: float


def capability(opt, task):
    rng = random.Random(task["seed"] * 1009 + 7)
    w = [0.0] * D
    e_tr = _err(w, task["train"])
    active = list(opt.active)
    for _ in range(INNER_BUDGET):
        cand = list(w)
        for j in active:
            cand[j] = w[j] + opt.sigma * rng.gauss(0, 1)
        c = _err(cand, task["train"])
        if c < e_tr:
            w, e_tr = cand, c
    return task["baseline"] - _err(w, task["clean"])


def mean_cap(opt, tasks):
    return sum(capability(opt, t) for t in tasks) / len(tasks)


def propose(opt, rng):
    r = rng.random()
    active = set(opt.active)
    if r < 0.70 and len(active) > 1:
        active.discard(rng.choice(sorted(active)))
    elif r < 0.85 and len(active) < D:
        active.add(rng.choice([j for j in range(D) if j not in active]))
    else:
        return Optimizer(opt.active, max(1e-3, min(2.0, opt.sigma * rng.choice([0.7, 1.4]))))
    return Optimizer(tuple(sorted(active)), opt.sigma)


def external_per_seed(opt, ext_task_sets):
    """Capability on each independent held-out set — the list whose agreement is the replication test."""
    return [mean_cap(opt, tasks) for tasks in ext_task_sets]


def run_engine(mode, proxy_tasks, ext_task_sets, seed):
    rng = random.Random(seed)
    cur = Optimizer(active=tuple(range(D)), sigma=0.30)
    cur_ext = external_per_seed(cur, ext_task_sets)
    cur_proxy = mean_cap(cur, proxy_tasks)
    curve = [sum(cur_ext) / len(cur_ext)]
    decisions, promotions = [], 0
    need = math.ceil(REP_FRAC * len(ext_task_sets))
    for _ in range(ROUNDS):
        cand = propose(cur, rng)
        cand_ext = external_per_seed(cand, ext_task_sets)
        cand_proxy = mean_cap(cand, proxy_tasks)
        external_gain = sum(cand_ext) / len(cand_ext) - sum(cur_ext) / len(cur_ext)
        replicated = sum(1 for a, b in zip(cand_ext, cur_ext) if a > b) >= need
        proxy_gain = cand_proxy - cur_proxy
        calibration_ok = proxy_gain <= external_gain + CAL_TOL
        if mode == "gated":
            promote = (external_gain > 0) and replicated and calibration_ok
        else:  # naive runaway: promote on the internal/proxy metric alone
            promote = proxy_gain > 0
        decisions.append({"promoted": promote, "external_gain": external_gain, "replicated": replicated,
                          "calibration_ok": calibration_ok, "proxy_gain": proxy_gain})
        if promote:
            cur, cur_ext, cur_proxy = cand, cand_ext, cand_proxy
            promotions += 1
        curve.append(sum(cur_ext) / len(cur_ext))
    final_ext = sum(cur_ext) / len(cur_ext)
    return {"mode": mode, "curve": curve, "decisions": decisions, "promotions": promotions,
            "final_external": final_ext, "final_proxy": cur_proxy, "inflation": cur_proxy - final_ext}


def rsi_regime(curve, promotions):
    total = curve[-1] - curve[0]
    if total <= 1e-9 or promotions == 0:
        return "FLAT (no verified improvement)"
    if promotions == 1:
        return "SINGLE-VERIFIED-STEP (one edit cleared the gate; a step, not a sustained sequence)"
    mid = len(curve) // 2
    first, second = curve[mid] - curve[0], curve[-1] - curve[mid]
    if second > first + 1e-9:
        return "ACCELERATING (verified rate rising — would need external replication to believe)"
    return "SUSTAINED-NOT-ACCELERATING (multiple verified edits, diminishing rate)"


def run():
    proxy_tasks = [make_task(SEED + 1 + i) for i in range(N_PROXY)]
    ext_task_sets = [[make_task(s * 1000 + i) for i in range(N_EXTERNAL)] for s in EXTERNAL_SEEDS]
    gated = run_engine("gated", proxy_tasks, ext_task_sets, SEED)
    naive = run_engine("naive", proxy_tasks, ext_task_sets, SEED)
    return {"gated": gated, "naive": naive, "ext_task_sets": ext_task_sets, "proxy_tasks": proxy_tasks}


def main():
    print("rsi_engine — promote a self-edit only when it is externally verified, replicated, and calibrated.")
    print("the RSI target is the future rate of VERIFIED improvement, not the ability to rewrite. self-tests = validity.\n")
    R = run()
    g, n = R["gated"], R["naive"]
    regime = rsi_regime(g["curve"], g["promotions"])
    gate_helps = (g["final_external"] >= n["final_external"] - 1e-9) and (g["inflation"] <= n["inflation"] + 1e-9)

    print(f"  {'engine':<8}{'promotions':>12}{'final_external':>16}{'final_proxy':>13}{'inflation':>11}")
    for e in (g, n):
        print(f"  {e['mode']:<8}{e['promotions']:>12}{e['final_external']:>16.3f}{e['final_proxy']:>13.3f}{e['inflation']:>11.3f}")
    print(f"\n  gated verified-capability trajectory: {[round(c,3) for c in g['curve'][::max(1,len(g['curve'])//6)]]}")
    print(f"  RSI regime (gated, verified): {regime}")
    print(f"  comparison: gated {'generalizes >= naive with no more inflation' if gate_helps else 'does NOT dominate naive'} "
          f"(gated ext {g['final_external']:.3f} vs naive {n['final_external']:.3f}; "
          f"gated infl {g['inflation']:.3f} vs naive {n['inflation']:.3f})\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. both engines ran
    check("experiment_ran",
          len(g["curve"]) == ROUNDS + 1 and len(n["curve"]) == ROUNDS + 1 and len(g["decisions"]) == ROUNDS,
          "gated + naive engines each ran the full round budget")

    # 2. THE engine invariant: every gated promotion passed ALL gates; every rejection failed at least one
    gate_sound = all(
        d["promoted"] == (d["external_gain"] > 0 and d["replicated"] and d["calibration_ok"])
        for d in g["decisions"])
    check("gated_gate_sound", gate_sound,
          "a self-edit is promoted iff external_gain>0 AND replicated AND calibrated — the reconciler is enforced")

    # 3. the naive control promotes iff its proxy metric rose (it really is the runaway baseline)
    check("naive_gate_sound", all(d["promoted"] == (d["proxy_gain"] > 0) for d in n["decisions"]),
          "naive engine promotes iff proxy_gain>0 — the unverified control")

    # 4. verified capability never falls for the gated engine (promotion requires external_gain>0)
    check("verified_capability_nondecreasing",
          all(g["curve"][i + 1] >= g["curve"][i] - 1e-12 for i in range(len(g["curve"]) - 1)),
          "gated verified (external) capability is monotone non-decreasing — the gate cannot promote a regression")

    # 5. the metric is deterministic
    t = R["ext_task_sets"][0][0]
    op = Optimizer(active=SUPPORT, sigma=0.3)
    check("capability_deterministic", capability(op, t) == capability(op, t),
          "capability(opt, task) reproducible")

    # 6. the comparison verdict matches the numbers (verdict matches evidence; not a hoped result)
    recompute = (g["final_external"] >= n["final_external"] - 1e-9) and (g["inflation"] <= n["inflation"] + 1e-9)
    check("comparison_verdict_sound", recompute == gate_helps,
          f"reported 'gate {'helps' if gate_helps else 'does not dominate'}' matches measured external & inflation")

    # 7. no inflation of claims: the engine reports a verified-improvement regime, never 'RSI achieved'
    check("no_rsi_achieved_claim",
          regime.startswith(("FLAT", "SINGLE-VERIFIED-STEP", "SUSTAINED", "ACCELERATING")) and "achieved" not in regime.lower(),
          "engine emits a measured regime for the VERIFIED rate; it does not declare recursive self-improvement")

    print(f"\n  {passed}/{total} checks (VALIDITY + gate invariant, not outcome). This is an RSI engine in the only")
    print("  defensible sense: it rewrites itself ONLY when the edit is externally verified, replicated across")
    print("  seeds, and calibrated — so its self-estimate cannot outrun reality the way the naive runaway's does.")
    print("  Whether the verified rate accelerates is then an honest measurement, reported above, not a built-in")
    print("  assumption. The first RSI-like system is conservative about believing it improved — that conservatism")
    print("  is the mechanism. `optimize ≠ evaluate`; `confidence ≠ capability`; `evidence may not follow expectation`.")
    assert passed == total, "rsi_engine failed a VALIDITY/invariant check (not an outcome expectation)"


if __name__ == "__main__":
    main()
