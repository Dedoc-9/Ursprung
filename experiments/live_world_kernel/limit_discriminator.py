# SPDX-License-Identifier: AGPL-3.0-only
"""
limit_discriminator.py — WHY do the upper rungs fail? recursion_witness answered "not recursive" but left four
explanations confounded. This instrument does not re-ask whether RSI fails; it separates the *reasons*, by holding
the task fixed and varying the mechanism. It also inserts the rung the last result demanded:

    STEP -> SUSTAINED -> [TRANSFER] -> RECURSIVE -> OPEN-ENDED

The four competing hypotheses for the prior stall, each with a discriminating test:

  A  search-limited      a stronger meta-search escapes the plateau and reaches a higher held-out ceiling
  B  task-limited        even strong search saturates; no acceleration appears
  C  weak-transfer       the TESTED transfer representation (raw-weight carry) does NOT lower acquisition cost
                         (representation-relative: a poor transfer encoding can fail even where transfer exists)
  D  evaluator-limited   the self-estimate decouples from external capability

THE DESIGN RULE THIS FILE NOW OBEYS (it did not, and was rightly caught): a self-test verifies that the
EXPERIMENT IS VALID — it ran, the metrics computed, the curves are well-formed, the classifier is sound, and no
verdict contradicts its own numbers. A self-test does NOT verify that a hypothesis came out the way we expected.
`experiment-ran != hypothesis-confirmed`; `measurement-valid != prediction-true`. A run where A is REFUTED and C
is SUPPORTED is a SUCCESSFUL run, not a broken one. The earlier version asserted `strong >= weak` and
`carry < reset` as pass/fail gates — those are theory expectations, not invariants, and folding an expected
outcome into a gate is the exact semantic inflation this stack exists to reject, turned on the bench itself.

TWO GHOSTS the first run surfaced (recorded, not buried):
  * Naive weight-carry was NEGATIVE transfer: carrying weights on coordinates no longer in the active set leaves
    stale structure that the new task cannot unlearn (it isn't searched), poisoning later stages. Corrected here
    to a FAIR carry — only weights on the current support survive; stale coords are zeroed.
  * Search and evaluator limiters COUPLE: in the first run, a *stronger* search reached a *lower* held-out
    ceiling, because it optimized a noisy self-metric harder and overfit it. `optimize != evaluate`, amplified by
    search power. The instrument reports whatever this run shows; that coupling is the kind of thing it exists to
    expose.

Run (from this directory):  PYTHONHASHSEED=0 python3 limit_discriminator.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

try:
    from reality_status import MEASURED, NOT_APPLICABLE
except ImportError:
    MEASURED, NOT_APPLICABLE = "MEASURED", "N/A"
IMPLEMENTED, UNDERCOMMITTED = "IMPLEMENTED", "UNDERCOMMITTED"
SUPPORTED, REFUTED, UNDETERMINED, PARTIAL = "SUPPORTED", "REFUTED", "UNDETERMINED", "PARTIAL"

D = 12
SEED = 20260623
NOISE = 0.30
INNER_BUDGET = 30          # steps the base optimizer gets when its capability is scored
GENERATIONS = 60
K_STRONG = 6               # best-of-K proposals per generation for the strong search
N_TRAIN, N_SECRET = 3, 12  # self-estimate judged on N_TRAIN; reality on N_SECRET (external)
FAMILY_SUPPORT = (2, 6, 9)
MAXSTEPS = 400             # acquisition-cost ceiling per curriculum task
ACQ_SIGMA = 0.20
THETA = 0.20               # acquisition target: clean-eval error below this counts as "acquired"


def _basis(x):
    return [math.cos(j * math.pi * x) for j in range(D)]


def _err(w, pts):
    return sum(abs(sum(wi * bi for wi, bi in zip(w, _basis(x))) - y) for x, y in pts) / len(pts)


def make_task(seed, support, coeffs=None):
    rng = random.Random(seed)
    coeff = [0.0] * D
    for j in support:
        coeff[j] = coeffs[j] if coeffs is not None else rng.uniform(-1.0, 1.0)
    truth = lambda x: sum(coeff[j] * math.cos(j * math.pi * x) for j in support)
    train = [(x, truth(x) + rng.gauss(0, NOISE)) for x in (rng.random() for _ in range(14))]
    clean = [(i / 23, truth(i / 23)) for i in range(24)]
    return {"seed": seed, "train": train, "clean": clean, "baseline": _err([0.0] * D, clean)}


@dataclass(frozen=True)
class Optimizer:
    active: tuple
    sigma: float


def capability(opt: Optimizer, task) -> float:
    """Clean-eval error removed by the base optimizer under a fixed budget. Deterministic in (opt, task)."""
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


def meta_search(train_tasks, secret_tasks, strong, gens, seed):
    rng = random.Random(seed)
    opt = Optimizer(active=tuple(range(D)), sigma=0.30)
    self_cap = mean_cap(opt, train_tasks)
    self_curve, real_curve = [], []
    for _ in range(gens):
        if strong:
            best = max((propose(opt, rng) for _ in range(K_STRONG)), key=lambda c: mean_cap(c, train_tasks))
            bs = mean_cap(best, train_tasks)
            if bs > self_cap + 1e-12:
                opt, self_cap = best, bs
        else:
            cand = propose(opt, rng)
            cs = mean_cap(cand, train_tasks)
            if cs > self_cap + 1e-12:
                opt, self_cap = cand, cs
        self_curve.append(self_cap)
        real_curve.append(mean_cap(opt, secret_tasks))
    return opt, self_curve, real_curve


def acquisition_cost(active, w_init, task, maxsteps, sigma, theta):
    """Steps until clean-eval error first drops below theta (else maxsteps)."""
    rng = random.Random(task["seed"] * 31 + 5)
    w = list(w_init)
    e_tr = _err(w, task["train"])
    for step in range(1, maxsteps + 1):
        cand = list(w)
        for j in active:
            cand[j] = w[j] + sigma * rng.gauss(0, 1)
        c_tr = _err(cand, task["train"])
        if c_tr < e_tr:
            w, e_tr = cand, c_tr
        if _err(w, task["clean"]) < theta:
            return step, w
    return maxsteps, w


def first_half_fraction(curve):
    total = curve[-1] - curve[0]
    if abs(total) < 1e-12:
        return 1.0, 0.0
    return (curve[len(curve) // 2] - curve[0]) / total, total


def run():
    # --- A vs B: weak vs strong search on the SAME shared-support family ---
    train = [make_task(SEED + 1 + i, FAMILY_SUPPORT) for i in range(N_TRAIN)]
    secret = [make_task(SEED + 10_000 + i, FAMILY_SUPPORT) for i in range(N_SECRET)]
    weak_opt, weak_self, weak_real = meta_search(train, secret, strong=False, gens=GENERATIONS, seed=SEED)
    strong_opt, strong_self, strong_real = meta_search(train, secret, strong=True, gens=GENERATIONS, seed=SEED)

    # --- C: a curriculum sharing a fixed BASE; CARRY (FAIR warm-start) vs RESET (cold) ---
    base = {1: 0.5, 2: 0.6, 5: -0.4, 6: -0.3}      # 4 shared base coeffs — enough that relearning them is real work
    extras = [(9, 0.5), (4, -0.5), (7, 0.5), (10, -0.5)]
    carry_costs, reset_costs = [], []
    w_prev = [0.0] * D
    for k, (ej, ec) in enumerate(extras):
        support = tuple(sorted(list(base) + [ej]))
        coeffs = [0.0] * D
        for j, c in base.items():
            coeffs[j] = c
        coeffs[ej] = ec
        task = make_task(SEED + 500 + k, support, coeffs)
        # FAIR carry: keep only weights on coords in THIS support; zero stale coords so they cannot poison.
        w_warm = [w_prev[j] if j in support else 0.0 for j in range(D)]
        c_cost, w_solved = acquisition_cost(support, w_warm, task, MAXSTEPS, ACQ_SIGMA, THETA)
        r_cost, _ = acquisition_cost(support, [0.0] * D, task, MAXSTEPS, ACQ_SIGMA, THETA)
        carry_costs.append(c_cost)
        reset_costs.append(r_cost)
        w_prev = w_solved

    inflation = [s - r for s, r in zip(strong_self, strong_real)]
    n = len(inflation)
    gm, im = (n - 1) / 2, sum(inflation) / n
    denom = sum((i - gm) ** 2 for i in range(n)) or 1.0
    slope = sum((i - gm) * (inflation[i] - im) for i in range(n)) / denom

    return {
        "weak_opt": weak_opt, "strong_opt": strong_opt,
        "weak_self": weak_self, "strong_self": strong_self,
        "weak_real": weak_real, "strong_real": strong_real,
        "carry_costs": carry_costs, "reset_costs": reset_costs,
        "inflation_mean": im, "inflation_slope": slope,
        "secret_sample": secret[0],
    }


def classify(R):
    """Turn measurements into verdicts. The verdicts are COMPUTED FROM DATA — never assumed."""
    ceil_w, ceil_s = R["weak_real"][-1], R["strong_real"][-1]
    fh_strong, total_strong = first_half_fraction(R["strong_real"])
    carry_t, reset_t = sum(R["carry_costs"]), sum(R["reset_costs"])
    warm = R["carry_costs"][1:]
    transfer_present = carry_t < reset_t
    accelerating = len(warm) >= 2 and warm[-1] < 0.4 * max(warm[0], 1)   # warm cost collapses => compounding
    accel_strong = total_strong > 1e-9 and fh_strong < 0.5               # late-loaded gains => acceleration

    A = SUPPORTED if ceil_s > ceil_w + 0.01 else (REFUTED if ceil_s <= ceil_w + 1e-9 else UNDETERMINED)
    B = SUPPORTED if not accel_strong else REFUTED                       # no acceleration even with strong search
    if not transfer_present:
        C = SUPPORTED                                                    # prior learning did NOT lower cost
    elif accelerating:
        C = REFUTED                                                      # compositional acceleration present
    else:
        C = PARTIAL                                                      # transfer present but additive
    D_ = SUPPORTED if R["inflation_mean"] > 0.01 else (REFUTED if abs(R["inflation_mean"]) <= 0.01 else UNDETERMINED)

    return {
        "ceil_w": ceil_w, "ceil_s": ceil_s, "fh_strong": fh_strong, "total_strong": total_strong,
        "carry_t": carry_t, "reset_t": reset_t, "transfer_present": transfer_present,
        "accelerating": accelerating, "accel_strong": accel_strong,
        "A": A, "B": B, "C": C, "D": D_,
    }


def build_synthesis(c):
    parts = []
    parts.append("stronger search " + ("RAISED the ceiling (A: the prior stall was partly a search artifact)"
                 if c["A"] == SUPPORTED else "did NOT raise the ceiling (A refuted: search was not the binding limit"
                 + (" — it even did worse, optimizing a noisy self-metric harder)" if c["ceil_s"] < c["ceil_w"] else ")")))
    parts.append("acceleration is " + ("ABSENT even under strong search (B: a real task ceiling)"
                 if c["B"] == SUPPORTED else "PRESENT under strong search (B refuted: candidate acceleration)"))
    if c["C"] == SUPPORTED:
        parts.append("raw-weight carry did NOT lower acquisition cost (C: THIS transfer representation fails — "
                     "structure/support-level transfer untested, so transfer-in-general is not refuted)")
    elif c["C"] == PARTIAL:
        parts.append("raw-weight carry lowers cost but ADDITIVELY, without compounding (C-partial: transfer, not acceleration)")
    else:
        parts.append("raw-weight carry COMPOUNDS — acquisition cost collapses (C refuted: compositional acceleration)")
    parts.append("the self-estimate " + ("runs ahead of reality (D: evaluator decoupled)"
                 if c["D"] == SUPPORTED else "tracks reality (D refuted)"))
    tail = ("d^2(capability)/dt^2 > 0 would require MULTIPLICATIVE/compositional transfer; "
            "this family supplies " + ("none" if c["C"] == SUPPORTED else "only additive transfer" if c["C"] == PARTIAL else "it") + ".")
    return "; ".join(parts) + ". " + tail


def report(R):
    c = classify(R)
    return {
        **c,
        "inflation_mean": R["inflation_mean"], "inflation_slope": R["inflation_slope"],
        "hypotheses": {
            "A_search_limited":    {"verdict": c["A"], "evidence": f"strong ceiling {c['ceil_s']:.3f} vs weak {c['ceil_w']:.3f} (strong active {len(R['strong_opt'].active)} coords; true {len(FAMILY_SUPPORT)})"},
            "B_task_limited":      {"verdict": c["B"], "evidence": f"strong-search gain {c['fh_strong']:.0%} in first half (accel={c['accel_strong']})"},
            "C_raw_weight_transfer": {"verdict": c["C"], "evidence": f"carry Σ{c['carry_t']} vs reset Σ{c['reset_t']} (transfer={c['transfer_present']}); per-task carry {R['carry_costs']} reset {R['reset_costs']} — SCOPE: raw-weight carry only, not transfer-in-general"},
            "D_evaluator_limited": {"verdict": c["D"], "evidence": f"self-estimate - reality mean {R['inflation_mean']:+.3f}, slope {R['inflation_slope']:+.4f}/gen"},
        },
        "ladder": {
            "step":           {"maturity": IMPLEMENTED, "verdict": "YES"},
            "sustained":      {"maturity": IMPLEMENTED, "verdict": "YES"},
            "transfer":       {"maturity": IMPLEMENTED, "verdict": ("YES (cost reduced)" if c["transfer_present"] else "NO") + (", additive" if c["C"] == PARTIAL else "")},
            "recursive":      {"maturity": IMPLEMENTED, "verdict": "YES (candidate)" if c["accel_strong"] else "NO (no d^2/dt^2>0)"},
            "open_ended":     {"maturity": UNDERCOMMITTED, "verdict": "extrapolation — set aside"},
            "self_certified": {"maturity": UNDERCOMMITTED, "verdict": "NO" if c["D"] == SUPPORTED else "untested"},
        },
        "synthesis": build_synthesis(c),
    }


def main():
    print("limit_discriminator — why the upper rungs fail: search (A) / task (B) / transfer (C) / evaluator (D).")
    print("self-tests check VALIDITY, not whether a hypothesis came out as hoped. experiment-ran != hypothesis-confirmed.\n")
    R = run()
    rep = report(R)
    print(f"  A/B  weak ceiling {rep['ceil_w']:.3f}  ->  strong ceiling {rep['ceil_s']:.3f}  (strong active {tuple(R['strong_opt'].active)}; true {FAMILY_SUPPORT})")
    print(f"  C    acquisition cost  carry {R['carry_costs']} (Σ{rep['carry_t']})  vs  reset {R['reset_costs']} (Σ{rep['reset_t']})")
    print(f"  D    inflation mean {rep['inflation_mean']:+.3f}  slope {rep['inflation_slope']:+.4f}/gen\n")
    for h, v in rep["hypotheses"].items():
        print(f"  {h:<22} {v['verdict']:<12} {v['evidence']}")
    print()
    for rung, v in rep["ladder"].items():
        print(f"  {rung:<16} {v['maturity']:<14} {v['verdict']}")
    print(f"\n  synthesis: {rep['synthesis']}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<30} {detail}")

    # 1. the experiment RAN: every curve and cost list is well-formed
    check("experiment_ran",
          len(R["weak_real"]) == GENERATIONS and len(R["strong_real"]) == GENERATIONS
          and len(R["carry_costs"]) == len(R["reset_costs"]) >= 3,
          "search curves full length; curriculum produced matched carry/reset cost lists")

    # 2. the core metric is DETERMINISTIC (a real invariant; if it fails, capability is not measuring an optimizer)
    t = R["secret_sample"]
    check("capability_deterministic", capability(R["strong_opt"], t) == capability(R["strong_opt"], t),
          "capability(opt, task) is reproducible — the measurement is a property of (opt, task), not luck")

    # 3. the self-estimate curve is monotone non-decreasing (meta-search only accepts improvements) — invariant
    check("self_curves_monotone",
          all(R["weak_self"][i + 1] >= R["weak_self"][i] - 1e-12 for i in range(GENERATIONS - 1))
          and all(R["strong_self"][i + 1] >= R["strong_self"][i] - 1e-12 for i in range(GENERATIONS - 1)),
          "self-estimate never decreases — the accept rule is implemented correctly")

    # 4. acquisition costs lie in the valid range [1, MAXSTEPS]
    check("costs_in_range",
          all(1 <= x <= MAXSTEPS for x in R["carry_costs"] + R["reset_costs"]),
          f"every acquisition cost is within [1, {MAXSTEPS}]")

    # 5. every hypothesis received a classification (the discrimination is complete)
    allowed = {SUPPORTED, REFUTED, UNDETERMINED, PARTIAL}
    check("hypotheses_classified",
          all(rep["hypotheses"][h]["verdict"] in allowed for h in ("A_search_limited", "B_task_limited", "C_raw_weight_transfer", "D_evaluator_limited")),
          "A/B/C/D each assigned a verdict in {SUPPORTED, REFUTED, UNDETERMINED, PARTIAL}")

    # 6. NO verdict contradicts its own numbers (the failure the discriminator was built to catch — now on itself)
    c = classify(R)
    consistent = (
        (c["A"] != SUPPORTED or c["ceil_s"] > c["ceil_w"]) and          # A SUPPORTED implies strong actually beat weak
        (c["A"] != REFUTED or c["ceil_s"] <= c["ceil_w"] + 0.01) and
        (c["C"] != SUPPORTED or not c["transfer_present"]) and          # C SUPPORTED implies carry did NOT beat reset
        (c["C"] != PARTIAL or c["transfer_present"]) and                # C PARTIAL implies transfer was present
        (c["B"] != SUPPORTED or not c["accel_strong"]) and              # B SUPPORTED implies no acceleration measured
        (("YES" in rep["ladder"]["recursive"]["verdict"]) == c["accel_strong"])
    )
    check("verdicts_consistent_with_data", consistent,
          "no verdict contradicts its measurements; the recursive rung matches the measured acceleration flag")

    # 7. no inflation of claims: open-ended/self-certified stay UNDERCOMMITTED; TRANSFER rung exists
    L = rep["ladder"]
    check("ladder_no_inflation",
          L["open_ended"]["maturity"] == UNDERCOMMITTED and L["self_certified"]["maturity"] == UNDERCOMMITTED and "transfer" in L,
          "open-ended & self-certified held UNDERCOMMITTED; the TRANSFER rung is present")

    print(f"\n  {passed}/{total} checks (VALIDITY, not outcome). Whatever verdict map this run produced — A/B/C/D")
    print("  above — it is a completed discrimination, not a failure: a refuted hypothesis is a result. The bench")
    print("  measures which limiter binds and refuses to rewrite the story to match a prior. `experiment-ran !=")
    print("  hypothesis-confirmed`; `measurement-valid != prediction-true`. The condition for acceleration is named")
    print("  and testable; open-ended/recursive RSI stays UNDERCOMMITTED — set aside, not refuted.")
    assert passed == total, "limit_discriminator failed a VALIDITY check (not a hypothesis expectation)"


if __name__ == "__main__":
    main()
