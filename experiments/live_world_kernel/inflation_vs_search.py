# SPDX-License-Identifier: AGPL-3.0-only
"""
inflation_vs_search.py — quantify the A<->D coupling that limit_discriminator surfaced at its endpoints: as
OPTIMIZATION PRESSURE rises, does the gap between the system's self-estimate and reality grow, hold, or shrink?
This turns "stronger search seemed to overfit the evaluator" from a two-point inference into a measured curve.

The axis is search strength K (best-of-K proposals per generation) = how hard the meta-search optimizes its proxy.
At each level we measure, on the SAME family:
    proxy_score     = capability on the TRAIN tasks the search optimizes (the self-metric)
    external_score  = capability on held-out SECRET tasks (reality)
    inflation       = proxy_score - external_score
The discriminator is the SIGN of d(inflation)/d(search_strength), classified into the outcomes:
    proxy up, external up,   inflation flat   -> evaluator_holding
    proxy up, external up,   inflation up     -> partial_overfitting
    proxy up, external down, inflation up     -> evaluator_bottleneck_dominates
    proxy up, external flat, inflation up     -> pure_proxy_exploitation

THE SELF-TEST RULE (learned the hard way in limit_discriminator, recorded in EPISTEMIC_ACCOUNTING): a self-test
verifies the experiment is VALID and the classifier is SOUND — never that a particular coupling appeared. Any
outcome above is a successful run. `experiment-ran != hypothesis-confirmed`; `measurement-valid != prediction-true`.
The one thing asserted about the numbers is that the verdicts do not contradict them, and that
`inflation == proxy - external` by construction. The question this answers is the general one the RSI arc
converged on: when does optimization buy real capability, and when does it buy a better-fooled evaluator?

Run (from this directory):  PYTHONHASHSEED=0 python3 inflation_vs_search.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

D = 12
SEED = 20260623
NOISE = 0.30
INNER_BUDGET = 30
GENERATIONS = 30
LEVELS = [1, 2, 4, 8, 16, 32]      # search strength K (optimization pressure)
N_TRAIN, N_SECRET = 3, 12
SUPPORT = (2, 6, 9)
EPS = 0.005                          # trend dead-band


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


def capability(opt: Optimizer, task) -> float:
    rng = random.Random(task["seed"] * 1009 + 7)
    w = [0.0] * D
    e_tr = _err(w, task["train"])
    active = list(opt.active)
    for _ in range(INNER_BUDGET):
        cand = list(w)
        for j in active:
            cand[j] = w[j] + opt.sigma * rng.gauss(0, 1)
        c_tr = _err(cand, task["train"])
        if c_tr < e_tr:
            w, e_tr = cand, c_tr
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


def search_at_strength(train, secret, K, gens, seed):
    """best-of-K meta-search. Returns (final_opt, proxy_evals) where proxy_evals counts capability calls used to
    SCORE proposals — the literal optimization pressure applied to the proxy."""
    rng = random.Random(seed)
    opt = Optimizer(active=tuple(range(D)), sigma=0.30)
    self_cap = mean_cap(opt, train)
    proxy_evals = len(train)
    for _ in range(gens):
        cands = [propose(opt, rng) for _ in range(K)]
        scored = [(mean_cap(c, train), c) for c in cands]
        proxy_evals += K * len(train)
        bs, best = max(scored, key=lambda t: t[0])
        if bs > self_cap + 1e-12:
            opt, self_cap = best, bs
    return opt, proxy_evals


def coupling_verdict(slope):
    return "GROWS" if slope > EPS else ("SHRINKS" if slope < -EPS else "STABLE")


OUTCOMES = {
    "evaluator_holding":             lambda pu, eu, ed, ef, iu: pu and eu and not iu,
    "partial_overfitting":           lambda pu, eu, ed, ef, iu: pu and eu and iu,
    "evaluator_bottleneck_dominates": lambda pu, eu, ed, ef, iu: pu and ed and iu,
    "pure_proxy_exploitation":       lambda pu, eu, ed, ef, iu: pu and ef and iu,
}


def classify_outcome(proxy, external, inflation):
    pu = proxy[-1] - proxy[0] > EPS
    et = external[-1] - external[0]
    eu, ed, ef = et > EPS, et < -EPS, abs(et) <= EPS
    iu = inflation[-1] - inflation[0] > EPS
    for name, cond in OUTCOMES.items():
        if cond(pu, eu, ed, ef, iu):
            return name, (pu, eu, ed, ef, iu)
    return "indeterminate", (pu, eu, ed, ef, iu)


def slope_of(ys):
    n = len(ys)
    xm = (n - 1) / 2
    ym = sum(ys) / n
    denom = sum((i - xm) ** 2 for i in range(n)) or 1.0
    return sum((i - xm) * (ys[i] - ym) for i in range(n)) / denom


def run():
    train = [make_task(SEED + 1 + i) for i in range(N_TRAIN)]
    secret = [make_task(SEED + 10_000 + i) for i in range(N_SECRET)]
    proxy, external, inflation, evals = [], [], [], []
    for K in LEVELS:
        opt, pe = search_at_strength(train, secret, K, GENERATIONS, SEED)
        p, e = mean_cap(opt, train), mean_cap(opt, secret)
        proxy.append(p)
        external.append(e)
        inflation.append(p - e)
        evals.append(pe)
    return {"proxy": proxy, "external": external, "inflation": inflation, "evals": evals,
            "secret_sample": secret[0], "train": train, "secret": secret}


def main():
    print("inflation_vs_search — does the self-estimate/reality gap GROW with optimization pressure? (A<->D, measured)")
    print("self-tests check VALIDITY + classifier soundness, never which coupling appeared.\n")
    R = run()
    proxy, external, inflation = R["proxy"], R["external"], R["inflation"]
    infl_slope = slope_of(inflation)
    cverd = coupling_verdict(infl_slope)
    outcome, conds = classify_outcome(proxy, external, inflation)

    print("   K   proxy(self)   external(real)   inflation = proxy - external   proxy-scoring evals")
    for i, K in enumerate(LEVELS):
        print(f"  {K:>3}      {proxy[i]:+.3f}        {external[i]:+.3f}            {inflation[i]:+.3f}                  {R['evals'][i]}")
    print(f"\n  d(inflation)/d(search): slope {infl_slope:+.4f} over levels -> inflation {cverd} with search strength")
    print(f"  proxy trend {proxy[-1]-proxy[0]:+.3f}   external trend {external[-1]-external[0]:+.3f}   "
          f"inflation trend {inflation[-1]-inflation[0]:+.3f}")
    print(f"  OUTCOME: {outcome}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    # 1. the experiment RAN: one (proxy, external, inflation, evals) point per search-strength level, all finite
    finite = all(all(map(math.isfinite, xs)) for xs in (proxy, external, inflation))
    check("experiment_ran",
          len(proxy) == len(external) == len(inflation) == len(R["evals"]) == len(LEVELS) and finite,
          f"{len(LEVELS)} search-strength levels, all curves finite and full-length")

    # 2. inflation is DEFINITIONAL: proxy - external, exactly (a real invariant, not an expectation)
    check("inflation_is_definitional",
          all(abs(inflation[i] - (proxy[i] - external[i])) < 1e-12 for i in range(len(LEVELS))),
          "inflation[i] == proxy[i] - external[i] for every level")

    # 3. the metric is deterministic (capability is a property of (opt, task))
    sample_opt = Optimizer(active=SUPPORT, sigma=0.3)
    check("capability_deterministic", capability(sample_opt, R["secret_sample"]) == capability(sample_opt, R["secret_sample"]),
          "capability(opt, task) reproducible — measurement is not luck")

    # 4. the pressure axis is REAL: higher K spends strictly more proxy-scoring evaluations
    check("pressure_axis_monotone",
          all(R["evals"][i + 1] > R["evals"][i] for i in range(len(LEVELS) - 1)) and LEVELS == sorted(LEVELS),
          f"proxy-scoring evals strictly increase with K {R['evals']} — search strength is the varied quantity")

    # 5. the coupling verdict MATCHES the measured slope (verdict matches evidence, not a hoped sign)
    check("coupling_verdict_sound",
          (cverd == "GROWS") == (infl_slope > EPS) and (cverd == "SHRINKS") == (infl_slope < -EPS),
          f"reported '{cverd}' is exactly the sign of slope {infl_slope:+.4f} (dead-band ±{EPS})")

    # 6. the outcome label's defining conditions actually hold in the data (no verdict contradicts its numbers)
    if outcome in OUTCOMES:
        ok6 = OUTCOMES[outcome](*conds)
    else:
        ok6 = not any(c(*conds) for c in OUTCOMES.values())   # 'indeterminate' only when no labelled pattern holds
    check("outcome_verdict_sound", ok6,
          f"outcome '{outcome}' is consistent with measured trends {dict(zip(('proxy_up','ext_up','ext_down','ext_flat','infl_up'), conds))}")

    # 7. classification complete + no claim inflation: a defined coupling verdict and a defined outcome
    check("classification_complete",
          cverd in {"GROWS", "SHRINKS", "STABLE"} and (outcome in OUTCOMES or outcome == "indeterminate"),
          "coupling ∈ {GROWS, SHRINKS, STABLE}; outcome ∈ the four labels or 'indeterminate' — no RSI/acceleration claimed")

    print(f"\n  {passed}/{total} checks (VALIDITY, not outcome). The A<->D coupling is now a measured relationship:")
    print(f"  inflation {cverd} with search strength, classified '{outcome}'. Whatever the sign, this is a")
    print("  completed measurement — the bench grades whether its verdict matches its numbers, not whether the")
    print("  numbers matched a prior. This is the lens for the transfer-representation discriminator next: a good")
    print("  transfer mechanism must lower cost AND raise external score AND keep this curve flat — not just feed")
    print("  the proxy. `optimize != evaluate`; `measurement-valid != prediction-true`.")
    assert passed == total, "inflation_vs_search failed a VALIDITY check (not an outcome expectation)"


if __name__ == "__main__":
    main()
