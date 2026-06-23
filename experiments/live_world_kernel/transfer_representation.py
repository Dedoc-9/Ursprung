# SPDX-License-Identifier: AGPL-3.0-only
"""
transfer_representation.py — the transfer-representation discriminator. inflation_vs_search showed evaluator
inflation is persistent-but-stable; the open question it left is the transfer one: *what mechanism changes
EXTERNAL capability without raising inflation?* So here search is held fixed and the TRANSFER ENCODING is varied,
filling the table you sketched:

    representation      acquisition cost     external score      inflation
    reset (baseline)         ?                   ?                  ?
    raw_weights              ?                   ?                  ?
    support_set              ?                   ?                  ?
    basis_structure          ?                   ?                  ?
    learned_init             ?                   ?                  ?

A mechanism only WINS if it does all three at once vs the baseline: lower acquisition cost AND higher external
score AND inflation no worse. Lower cost alone is "found a better way to feed the proxy," not transfer.

OPERATING PRINCIPLE (the thread these witnesses converged on): *expectation may follow evidence; evidence may not
follow expectation.* The self-tests therefore check VALIDITY + classifier soundness only — that the experiment
ran, the metric is deterministic, inflation is definitional, every mechanism is measured on the SAME held-out
tasks, and the reported winner matches the measured rule. Any ranking is a result, not a failure.
`declared ≠ verified`; `prediction ≠ measurement`; `measurement → updated prediction`.

The five encodings (operationalized in THIS toy — open to revision; comb the per-mechanism numbers, not the names):
  reset           cold every task (active=all coords, w=0)                         — no transfer
  raw_weights     carry the last solved weight vector (active=all)                 — value transfer (stale risk)
  support_set     restrict search to coords found useful so far (active=useful)    — structure transfer (exclusion risk)
  basis_structure per-coord step size ∝ prior typical |w| (soft preference)        — preconditioner transfer
  learned_init    warm-start from the AVERAGE of prior solutions (active=all)      — a learned prior / "features"

Run (from this directory):  PYTHONHASHSEED=0 python3 transfer_representation.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

D = 12
SEED = 20260623
NOISE = 0.15            # lowered so the relative threshold below is actually reachable (the cost axis must vary)
MAXSTEPS = 500          # acquisition-cost ceiling per curriculum task
SIGMA = 0.20
RELATIVE_THETA = 0.50   # acquisition target = halve each task's baseline clean error (per-task fair + reachable)
CAP_BUDGET = 30         # fixed budget for capability (external/proxy) scoring
USEFUL_TOL = 0.10       # |w| above which a coord counts as "used"

BASE = {1: 0.5, 2: 0.6, 5: -0.4, 6: -0.3}                 # shared structure across ALL tasks (transferable)
CURRICULUM = [(9, 0.5), (4, -0.5), (7, 0.5), (10, -0.5)]  # each curriculum task adds one extra coord
HELDOUT = [(3, 0.5), (8, -0.5), (11, 0.5)]                # held-out tasks: same BASE, NEW extras (never seen)
MECHANISMS = ["reset", "raw_weights", "support_set", "basis_structure", "learned_init"]


def _basis(x):
    return [math.cos(j * math.pi * x) for j in range(D)]


def _err(w, pts):
    return sum(abs(sum(wi * bi for wi, bi in zip(w, _basis(x))) - y) for x, y in pts) / len(pts)


def make_task(seed, extra_j, extra_c):
    rng = random.Random(seed)
    coeff = [0.0] * D
    for j, c in BASE.items():
        coeff[j] = c
    coeff[extra_j] = extra_c
    support = sorted(list(BASE) + [extra_j])
    truth = lambda x: sum(coeff[j] * math.cos(j * math.pi * x) for j in range(D))
    train = [(x, truth(x) + rng.gauss(0, NOISE)) for x in (rng.random() for _ in range(14))]
    clean = [(i / 23, truth(i / 23)) for i in range(24)]
    return {"seed": seed, "train": train, "clean": clean, "baseline": _err([0.0] * D, clean),
            "support": support, "extra": extra_j}


def _inner(active, w_init, sigma_vec, task, steps, stop_theta):
    """(1+1) on `active` from `w_init` with per-coord sigma; optimizes NOISY train; optionally stops at clean<theta.
    Deterministic in (task, config)."""
    rng = random.Random(task["seed"] * 31 + 5)
    w = list(w_init)
    e_tr = _err(w, task["train"])
    for t in range(1, steps + 1):
        cand = list(w)
        for j in active:
            cand[j] = w[j] + sigma_vec[j] * rng.gauss(0, 1)
        c = _err(cand, task["train"])
        if c < e_tr:
            w, e_tr = cand, c
        if stop_theta is not None and _err(w, task["clean"]) < stop_theta:
            return t, w
    return steps, w


@dataclass
class State:
    last_w: list = field(default_factory=lambda: [0.0] * D)
    sum_w: list = field(default_factory=lambda: [0.0] * D)
    abs_w: list = field(default_factory=lambda: [0.0] * D)
    count: int = 0
    useful: set = field(default_factory=set)

    def update(self, w):
        self.last_w = list(w)
        self.count += 1
        for j in range(D):
            self.sum_w[j] += w[j]
            self.abs_w[j] += abs(w[j])
        self.useful |= {j for j in range(D) if abs(w[j]) > USEFUL_TOL}


def config(mech, st: State):
    """Return (active, w_init, sigma_vec) for the next task — the transfer encoding, independent of the task's
    own (unknown) support."""
    ALL = tuple(range(D))
    base_sig = [SIGMA] * D
    if mech == "reset" or st.count == 0:
        return ALL, [0.0] * D, base_sig
    if mech == "raw_weights":
        return ALL, list(st.last_w), base_sig
    if mech == "learned_init":
        return ALL, [st.sum_w[j] / st.count for j in range(D)], base_sig
    if mech == "support_set":
        active = tuple(sorted(st.useful)) if st.useful else ALL
        return active, [0.0] * D, base_sig
    if mech == "basis_structure":
        typ = [st.abs_w[j] / st.count for j in range(D)]
        return ALL, [0.0] * D, [SIGMA * (0.3 + 4.0 * typ[j]) for j in range(D)]
    raise ValueError(mech)


def capability(active, w_init, sigma_vec, task):
    """Clean-eval error removed under a FIXED budget from the (warm) start — higher = a better learner."""
    _, w = _inner(active, w_init, sigma_vec, task, CAP_BUDGET, stop_theta=None)
    return task["baseline"] - _err(w, task["clean"])


def run_mechanism(mech, curriculum_tasks, heldout_tasks):
    st = State()
    acq = 0
    for task in curriculum_tasks:
        active, w0, sig = config(mech, st)
        steps, w_solved = _inner(active, w0, sig, task, MAXSTEPS, stop_theta=RELATIVE_THETA * task["baseline"])
        acq += steps
        st.update(w_solved)
    # evaluate the FINAL transfer state on curriculum (proxy) and held-out (external), same warm config
    a, w, s = config(mech, st)
    proxy = sum(capability(a, w, s, t) for t in curriculum_tasks) / len(curriculum_tasks)
    external = sum(capability(a, w, s, t) for t in heldout_tasks) / len(heldout_tasks)
    return {"acq_cost": acq, "proxy": proxy, "external": external, "inflation": proxy - external}


def run():
    curriculum = [make_task(SEED + 100 + i, j, c) for i, (j, c) in enumerate(CURRICULUM)]
    heldout = [make_task(SEED + 900 + i, j, c) for i, (j, c) in enumerate(HELDOUT)]
    rows = {m: run_mechanism(m, curriculum, heldout) for m in MECHANISMS}
    return {"rows": rows, "curriculum": curriculum, "heldout": heldout}


def winners(rows):
    """A mechanism WINS iff vs baseline it lowers cost AND raises external AND does not worsen inflation."""
    b = rows["reset"]
    out = {}
    for m, r in rows.items():
        if m == "reset":
            out[m] = "baseline"
        elif r["acq_cost"] < b["acq_cost"] and r["external"] > b["external"] + 1e-9 and r["inflation"] <= b["inflation"] + 1e-9:
            out[m] = "WINS"
        else:
            out[m] = "no"
    return out


def main():
    print("transfer_representation — which transfer encoding raises EXTERNAL capability without raising inflation?")
    print("principle: expectation may follow evidence; evidence may not follow expectation. self-tests = validity.\n")
    R = run()
    rows = R["rows"]
    win = winners(rows)
    print(f"  {'representation':<16}{'acq_cost':>10}{'external':>11}{'proxy':>10}{'inflation':>11}   verdict")
    for m in MECHANISMS:
        r = rows[m]
        print(f"  {m:<16}{r['acq_cost']:>10}{r['external']:>11.3f}{r['proxy']:>10.3f}{r['inflation']:>11.3f}   {win[m]}")
    won = [m for m in MECHANISMS if win[m] == "WINS"]
    print(f"\n  winners (lower cost + higher external + no worse inflation than baseline): {won or 'none'}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    # 1. the experiment RAN: every mechanism produced finite metrics, and the baseline exists
    finite = all(all(math.isfinite(rows[m][k]) for k in ("acq_cost", "proxy", "external", "inflation")) for m in MECHANISMS)
    check("experiment_ran", finite and "reset" in rows and set(rows) == set(MECHANISMS),
          f"{len(MECHANISMS)} encodings measured incl. baseline 'reset'")

    # 2. inflation is DEFINITIONAL (proxy - external), not an expectation
    check("inflation_is_definitional",
          all(abs(rows[m]["inflation"] - (rows[m]["proxy"] - rows[m]["external"])) < 1e-12 for m in MECHANISMS),
          "inflation == proxy - external for every encoding")

    # 3. the metric is deterministic
    t = R["heldout"][0]
    a, w, s = config("reset", State())
    check("capability_deterministic", capability(a, w, s, t) == capability(a, w, s, t),
          "capability(config, task) reproducible")

    # 4. FAIR comparison: every mechanism is scored on the SAME held-out tasks
    seen_extras = {j for j, _ in CURRICULUM}
    check("same_heldout_for_all",
          [t["seed"] for t in R["heldout"]] == [SEED + 900 + i for i in range(len(HELDOUT))]
          and [t["extra"] for t in R["heldout"]] == [j for j, _ in HELDOUT]
          and all(t["extra"] not in seen_extras for t in R["heldout"]),
          "all encodings evaluated on one fixed held-out set whose extra coords were never in the curriculum")

    # 5. costs are within the valid range [len(curriculum), len(curriculum)*MAXSTEPS]
    lo, hi = len(CURRICULUM), len(CURRICULUM) * MAXSTEPS
    check("costs_in_range", all(lo <= rows[m]["acq_cost"] <= hi for m in MECHANISMS),
          f"every acquisition cost within [{lo}, {hi}]")

    # 6. the winner verdict MATCHES the rule on the numbers (verdict matches evidence, not a hoped mechanism)
    recomputed = winners(rows)
    b = rows["reset"]
    sound = recomputed == win and all(
        (win[m] == "WINS") == (m != "reset" and rows[m]["acq_cost"] < b["acq_cost"]
                               and rows[m]["external"] > b["external"] + 1e-9
                               and rows[m]["inflation"] <= b["inflation"] + 1e-9)
        for m in MECHANISMS)
    check("winner_verdict_sound", sound,
          "a mechanism is flagged WINS iff it actually beat baseline on all three axes")

    # 7. classification complete + no inflation of claims (no encoding declared 'transfer solved')
    check("classification_complete",
          all(win[m] in ("baseline", "WINS", "no") for m in MECHANISMS),
          "every encoding has a defined verdict; result is mechanism-relative, no general 'transfer solved' claim")

    print(f"\n  {passed}/{total} checks (VALIDITY, not outcome). The table stands on its own: whichever encodings")
    print("  win, tie, or lose, the bench measured them on one fixed held-out set and graded the verdict against")
    print("  the numbers. The point is the column relationship — an encoding that only lowers cost is feeding the")
    print("  proxy; one that raises EXTERNAL while holding inflation is real transfer. expectation may follow")
    print("  evidence; evidence may not follow expectation. `optimize ≠ evaluate`; `prediction ≠ measurement`.")
    assert passed == total, "transfer_representation failed a VALIDITY check (not an outcome expectation)"


if __name__ == "__main__":
    main()
