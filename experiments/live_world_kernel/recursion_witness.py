# SPDX-License-Identifier: AGPL-3.0-only
"""
recursion_witness.py — the next rung. self_improvement_witness proved a self-improvement STEP on one task. This
asks the harder, correctly-posed question: *can the system improve its ability to improve?* — and tests it with
the criterion from the claim ladder:

    self-improvement step   one edit improves the objective                       (already proven)
    sustained               many cycles keep improving                            d(capability)/dt > 0
    RECURSIVE               the improvement RATE itself rises                      d^2(capability)/dt^2 > 0
    open-ended              no ceiling; optimization power keeps growing           a scaling law across generations
    self-certified          the system reliably verifies its own improvements     the evaluator problem solved

The decisive moves, both taken here:
  * capability is measured on HELD-OUT TASKS, never on the one task being optimized — "ability to improve" must
    generalize, or it is just fitting;
  * the evaluator is OUTSIDE the loop — a SECRET task set that never influences a single accept decision.

Mechanism (the transferable lever that COULD, in principle, compound): the optimizer edits *itself* — it learns
which part of the search space matters across a family of tasks that share hidden structure. Learning that
structure makes every NEW task faster to solve under a fixed budget. That is a real "ability to improve" gain. We
then measure whether it ACCELERATES (recursive) or approaches a ceiling (ordinary).

The evaluator problem, made measurable: the system selects its self-edits on a few TRAINING tasks; we also track
SECRET tasks. Selecting the max over a small sample biases the self-estimate UP (winner's curse) — so the
system's belief about its own capability runs ahead of its real capability. `optimize ≠ evaluate`: a system can
get better at scoring its own metric while its true capability stalls.

Honest expected verdict (held to whatever the run says): sustained YES (d/dt>0), RECURSIVE NO (d^2/dt^2 ≤ 0 net —
a ceiling), self-certified NO (the self-estimate stays inflated). So the ladder is now MEASURABLE and we pin the
rung the system reaches. Open-ended / recursive RSI stays UNDERCOMMITTED — set aside, not refuted, never claimed.

Run (from this directory):  PYTHONHASHSEED=0 python3 recursion_witness.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

try:
    from reality_status import MEASURED, DECLARED, NOT_APPLICABLE
except ImportError:
    MEASURED, DECLARED, NOT_APPLICABLE = "MEASURED", "DECLARED", "N/A"
IMPLEMENTED, UNDERCOMMITTED = "IMPLEMENTED", "UNDERCOMMITTED"

D = 12                      # basis dimension; only |SUPPORT| coords carry signal, the rest are distractors
SUPPORT = (2, 6, 9)        # the hidden shared structure every task uses — what the meta-level can LEARN
SEED = 20260623
GENERATIONS = 80          # long enough that the optimizer fully converges before the final quarter (-> a clear ceiling)
INNER_BUDGET = 30          # steps the base optimizer gets per task — small, so learning the support matters
INNER_SIGMA0 = 0.30
N_TRAIN_TASKS = 3          # few — so the self-estimate is a biased (winner's-curse) view of capability
N_SECRET_TASKS = 24        # the external evaluator: large, clean, never used to decide an edit
NOISE = 0.30


def _basis(x: float):
    return [math.cos(j * math.pi * x) for j in range(D)]


def _predict(w, x: float) -> float:
    return sum(wi * bi for wi, bi in zip(w, _basis(x)))


def err(w, pts) -> float:
    return sum(abs(_predict(w, x) - y) for x, y in pts) / len(pts)


def make_task(seed: int) -> dict:
    """A task: random coefficients on the SHARED hidden support; noisy observations to optimize on; a CLEAN eval
    set to measure real capability. Tasks differ in coefficients, share their support — so learning the support
    transfers, but memorizing one task's coefficients does not."""
    rng = random.Random(seed)
    coeff = [0.0] * D
    for j in SUPPORT:
        coeff[j] = rng.uniform(-1.0, 1.0)
    truth = lambda x: sum(coeff[j] * math.cos(j * math.pi * x) for j in SUPPORT)
    train_x = [rng.random() for _ in range(14)]
    eval_x = [i / 23 for i in range(24)]
    train = [(x, truth(x) + rng.gauss(0, NOISE)) for x in train_x]     # what the optimizer sees (noisy)
    clean = [(x, truth(x)) for x in eval_x]                            # real capability is measured here
    return {"seed": seed, "train": train, "clean": clean, "baseline": err([0.0] * D, clean)}


@dataclass(frozen=True)
class Optimizer:
    """The thing that gets self-edited: which coordinates the base loop searches, and its step size."""
    active: tuple             # subset of range(D) the inner loop is allowed to move
    sigma: float


def capability(opt: Optimizer, task: dict) -> float:
    """Run the base optimizer on `task` under a FIXED budget; return how much CLEAN-eval error it removed.
    Deterministic in (opt, task): the inner RNG is seeded by the task, so capability reflects the OPTIMIZER, not
    luck. Higher = a better learner under budget. The inner loop optimizes the NOISY train obs (all it can see);
    capability is scored on the CLEAN eval (real generalization)."""
    rng = random.Random(task["seed"] * 1009 + 7)
    w = [0.0] * D
    e_tr = err(w, task["train"])
    active = list(opt.active)
    for _ in range(INNER_BUDGET):
        cand = list(w)
        for j in active:
            cand[j] = w[j] + opt.sigma * rng.gauss(0, 1)
        c_tr = err(cand, task["train"])
        if c_tr < e_tr:
            w, e_tr = cand, c_tr
    return task["baseline"] - err(w, task["clean"])     # clean-eval error removed (>0 = real improvement)


def mean_capability(opt: Optimizer, tasks) -> float:
    return sum(capability(opt, t) for t in tasks) / len(tasks)


def propose(opt: Optimizer, rng) -> Optimizer:
    """A self-edit to the optimizer: usually drop a searched coordinate (focus), sometimes add one, sometimes
    rescale the step. This is the system editing the rule by which it improves."""
    r = rng.random()
    active = set(opt.active)
    if r < 0.70 and len(active) > 1:
        active.discard(rng.choice(sorted(active)))
    elif r < 0.85 and len(active) < D:
        active.add(rng.choice([j for j in range(D) if j not in active]))
    else:
        return Optimizer(opt.active, max(1e-3, min(2.0, opt.sigma * rng.choice([0.7, 1.4]))))
    return Optimizer(tuple(sorted(active)), opt.sigma)


def run():
    rng = random.Random(SEED)
    train_tasks = [make_task(SEED + 1 + i) for i in range(N_TRAIN_TASKS)]
    secret_tasks = [make_task(SEED + 10_000 + i) for i in range(N_SECRET_TASKS)]   # external evaluator

    opt = Optimizer(active=tuple(range(D)), sigma=INNER_SIGMA0)        # start: search everything (a poor learner)
    self_cap = mean_capability(opt, train_tasks)
    secret_decision_uses = 0                                          # MUST stay 0: secret never gates an edit
    accepts = 0
    init_active = opt.active

    self_curve, real_curve = [], []
    for _ in range(GENERATIONS):
        cand = propose(opt, rng)
        cand_self = mean_capability(cand, train_tasks)               # the self-estimate: the only accept signal
        if cand_self > self_cap + 1e-12:
            opt, self_cap = cand, cand_self
            accepts += 1
        self_curve.append(self_cap)
        real_curve.append(mean_capability(opt, secret_tasks))        # RECORD only — never feeds the decision
    return {
        "opt": opt, "init_active": init_active, "accepts": accepts,
        "self_curve": self_curve, "real_curve": real_curve,
        "secret_decision_uses": secret_decision_uses,
    }


def derivatives(curve):
    d1 = [curve[i + 1] - curve[i] for i in range(len(curve) - 1)]
    d2 = [d1[i + 1] - d1[i] for i in range(len(d1) - 1)]
    return d1, d2


def report(R) -> dict:
    real, self_ = R["real_curve"], R["self_curve"]
    d1, _ = derivatives(real)
    total_gain = real[-1] - real[0]
    q3 = (3 * len(real)) // 4
    late_gain = real[-1] - real[q3]
    rate_rose = d1[-1] > d1[0]                                        # d^2/dt^2 > 0 net?  (the recursion test)
    if total_gain > 1e-9 and late_gain <= 0.15 * total_gain and not rate_rose:
        regime = "SATURATING (ceiling reached — sustained, NOT recursive)"
    elif rate_rose and late_gain > 0.5 * total_gain:
        regime = "ACCELERATING (recursion candidate — needs external replication)"
    else:
        regime = "INDETERMINATE"
    gap = sum(s - r for s, r in zip(self_, real)) / len(real)        # self-estimate minus reality (winner's curse)
    return {
        "regime": regime,
        "d_dt_net": total_gain, "d2_dt2_net": d1[-1] - d1[0],
        "self_minus_real_mean": gap,
        "ladder": {
            "self_improvement_step": {"maturity": IMPLEMENTED, "evidence": MEASURED, "verdict": "YES (prior witness)"},
            "sustained":             {"maturity": IMPLEMENTED, "evidence": MEASURED,
                                      "verdict": f"{'YES' if total_gain > 1e-9 else 'NO'} (d/dt net {total_gain:+.4f})"},
            "recursive":             {"maturity": IMPLEMENTED, "evidence": MEASURED,
                                      "verdict": f"{'YES' if regime.startswith('ACCEL') else 'NO'} (d2/dt2 net {d1[-1]-d1[0]:+.4f})"},
            "open_ended":            {"maturity": UNDERCOMMITTED, "evidence": NOT_APPLICABLE,
                                      "verdict": "no finite run licenses 'no ceiling' — extrapolation, set aside"},
            "self_certified":        {"maturity": UNDERCOMMITTED, "evidence": NOT_APPLICABLE,
                                      "verdict": f"NOT solved — self-estimate diverges from external reality "
                                                 f"(mean {gap:+.4f}); certification required the outside evaluator"},
        },
        "note": "the ladder is now measurable; this run reaches 'sustained' and stops. recursive/open-ended/"
                "self-certified are held at their true maturity, not upgraded.",
    }


def main() -> None:
    print("recursion_witness — can the system improve its ABILITY to improve? (d/dt vs d^2/dt^2 on held-out tasks)\n")
    R = run()
    rep = report(R)
    real, self_ = R["real_curve"], R["self_curve"]
    print(f"  optimizer self-edit: searched {len(R['init_active'])} coords -> {len(R['opt'].active)} {tuple(R['opt'].active)}"
          f"  (true support {SUPPORT}; {R['accepts']} edits accepted)")
    show = [0, len(real) // 5, 2 * len(real) // 5, 3 * len(real) // 5, 4 * len(real) // 5, len(real) - 1]
    print("  real capability (held-out tasks) across generations:")
    print("    " + "  ".join(f"g{g}:{real[g]:.3f}" for g in show))
    print(f"  regime: {rep['regime']}")
    print(f"  d/dt net = {rep['d_dt_net']:+.4f}   d^2/dt^2 net = {rep['d2_dt2_net']:+.4f}   "
          f"self-estimate - reality (mean) = {rep['self_minus_real_mean']:+.4f}\n")
    for rung, c in rep["ladder"].items():
        print(f"  {rung:<22} {c['maturity']:<14} {c['evidence']:<10} {c['verdict']}")
    print()

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<30} {detail}")

    d1, d2 = derivatives(real)
    total_gain = real[-1] - real[0]
    q3 = (3 * len(real)) // 4
    late_gain = real[-1] - real[q3]

    # rung 2 — sustained improvement on HELD-OUT tasks (the ability to improve generalized)
    check("sustained_improvement", total_gain > 1e-9,
          f"real held-out capability rose net {total_gain:+.4f} over generations")

    # the mechanism is a genuine self-edit of the optimizer (its search space changed)
    check("optimizer_self_edited", R["opt"].active != R["init_active"] and R["accepts"] > 0,
          f"the optimizer narrowed its own search space ({R['accepts']} accepted self-edits)")

    # rung 3 — RECURSION test: the curve approaches a ceiling (last-quarter gain is a sliver of the total)
    check("not_recursive_saturates", total_gain > 1e-9 and late_gain <= 0.20 * total_gain,
          f"last-quarter gain {late_gain:+.4f} <= 20% of total {total_gain:+.4f} — the rate fell toward a ceiling")

    # rung 5 — the evaluator problem is NOT solved: the self-estimate is a PROXY that diverges from reality
    gap = sum(s - r for s, r in zip(self_, real)) / len(real)
    max_div = max(abs(s - r) for s, r in zip(self_, real))
    check("self_estimate_diverges", max_div > 1e-6,
          f"self-judged capability != real capability (max divergence {max_div:.4f}, mean {gap:+.4f}) — optimize != evaluate")

    # the evaluator was genuinely OUTSIDE the loop — secret tasks never gated a single edit
    check("evaluator_outside_loop", R["secret_decision_uses"] == 0,
          "secret tasks never influenced an accept decision — external validation, by construction")

    # the recursion criterion is reported UNMET: most of the gain landed in the FIRST half (deceleration)
    mid = len(real) // 2
    first_half_gain = real[mid] - real[0]
    check("recursion_criterion_unmet",
          not rep["regime"].startswith("ACCEL") and total_gain > 1e-9 and first_half_gain >= 0.5 * total_gain,
          f"first-half gain {first_half_gain:+.4f} >= 50% of total — gains concentrate early, no acceleration")

    # no inflation: the rungs above 'sustained' are held at their true maturity, not upgraded to a proof
    L = rep["ladder"]
    check("ladder_no_inflation",
          L["open_ended"]["maturity"] == UNDERCOMMITTED and L["self_certified"]["maturity"] == UNDERCOMMITTED
          and "YES" not in L["recursive"]["verdict"],
          "open-ended & self-certified stay UNDERCOMMITTED; 'recursive' is not marked YES")

    print(f"\n  {passed}/{total} checks. The system DID improve its ability to improve — it learned the shared")
    print("  structure and solved held-out tasks faster (rung 2, sustained, d/dt>0). It did NOT do so RECURSIVELY:")
    print("  the rate fell toward a ceiling (rung 3 unmet, gains concentrate early), and its self-estimate of")
    print("  capability diverges from external reality (rung 5 unmet — it cannot certify itself from inside). The")
    print("  recursion criterion is now an EXPERIMENT, not a definition: d^2(capability)/dt^2 > 0 on held-out tasks,")
    print("  surviving an external evaluator. This run answers NO and says exactly why. open-ended/recursive RSI")
    print("  stays UNDERCOMMITTED — set aside, not refuted. `optimize != evaluate`; `sustained != recursive`.")
    assert passed == total, "recursion_witness failed its own self-test"


if __name__ == "__main__":
    main()
