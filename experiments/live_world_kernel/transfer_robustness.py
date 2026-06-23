# SPDX-License-Identifier: AGPL-3.0-only
"""
transfer_robustness.py — is any transfer-encoding finding ROBUST, or is it an artifact of one regime? The single
run in `transfer_representation.py` produced a winner (`support_set`) — but combing it against a different
noise/threshold regime showed three of five mechanisms FLIP their conclusion (raw_weights best->hurts;
learned_init worst->near-best; support_set inert->winner). A single run's winner is no more trustworthy than a
single seed. This instrument runs the same table across a GRID of regimes (noise × seed) and asks only what
survives:

    does ONE mechanism win in EVERY regime?      -> ROBUST_DOMINATOR
    does the winner change across regimes?        -> REGIME_DEPENDENT  (no robust transfer claim)
    does nothing ever win?                        -> NO_ROBUST_TRANSFER

Same operating principle as the rest of the stack: self-tests check VALIDITY + soundness only (did every regime
run, is inflation definitional, is the stability verdict consistent with the per-regime winners) — never that a
particular mechanism won. `expectation may follow evidence; evidence may not follow expectation`; a finding that
does not survive replication across regimes is not a finding.

Run (from this directory):  PYTHONHASHSEED=0 python3 transfer_robustness.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

D = 12
SEED = 20260623
MAXSTEPS = 500
SIGMA = 0.20
RELATIVE_THETA = 0.50
CAP_BUDGET = 30
USEFUL_TOL = 0.10

BASE = {1: 0.5, 2: 0.6, 5: -0.4, 6: -0.3}
CURRICULUM = [(9, 0.5), (4, -0.5), (7, 0.5), (10, -0.5)]
HELDOUT = [(3, 0.5), (8, -0.5), (11, 0.5)]
MECHANISMS = ["reset", "raw_weights", "support_set", "basis_structure", "learned_init"]
NOISES = [0.10, 0.20, 0.30]
SEED_OFFSETS = [0, 7, 13]


def _basis(x):
    return [math.cos(j * math.pi * x) for j in range(D)]


def _err(w, pts):
    return sum(abs(sum(wi * bi for wi, bi in zip(w, _basis(x))) - y) for x, y in pts) / len(pts)


def make_task(seed, extra_j, extra_c, noise):
    rng = random.Random(seed)
    coeff = [0.0] * D
    for j, c in BASE.items():
        coeff[j] = c
    coeff[extra_j] = extra_c
    truth = lambda x: sum(coeff[j] * math.cos(j * math.pi * x) for j in range(D))
    train = [(x, truth(x) + rng.gauss(0, noise)) for x in (rng.random() for _ in range(14))]
    clean = [(i / 23, truth(i / 23)) for i in range(24)]
    return {"seed": seed, "train": train, "clean": clean, "baseline": _err([0.0] * D, clean), "extra": extra_j}


def _inner(active, w_init, sigma_vec, task, steps, stop_theta):
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


def config(mech, st):
    ALL = tuple(range(D))
    base_sig = [SIGMA] * D
    if mech == "reset" or st.count == 0:
        return ALL, [0.0] * D, base_sig
    if mech == "raw_weights":
        return ALL, list(st.last_w), base_sig
    if mech == "learned_init":
        return ALL, [st.sum_w[j] / st.count for j in range(D)], base_sig
    if mech == "support_set":
        return (tuple(sorted(st.useful)) if st.useful else ALL), [0.0] * D, base_sig
    if mech == "basis_structure":
        typ = [st.abs_w[j] / st.count for j in range(D)]
        return ALL, [0.0] * D, [SIGMA * (0.3 + 4.0 * typ[j]) for j in range(D)]
    raise ValueError(mech)


def capability(active, w_init, sigma_vec, task):
    _, w = _inner(active, w_init, sigma_vec, task, CAP_BUDGET, stop_theta=None)
    return task["baseline"] - _err(w, task["clean"])


def run_mechanism(mech, curriculum, heldout):
    st = State()
    acq = 0
    for task in curriculum:
        active, w0, sig = config(mech, st)
        steps, w_solved = _inner(active, w0, sig, task, MAXSTEPS, stop_theta=RELATIVE_THETA * task["baseline"])
        acq += steps
        st.update(w_solved)
    a, w, s = config(mech, st)
    proxy = sum(capability(a, w, s, t) for t in curriculum) / len(curriculum)
    external = sum(capability(a, w, s, t) for t in heldout) / len(heldout)
    return {"acq_cost": acq, "proxy": proxy, "external": external, "inflation": proxy - external}


def regime_winners(rows):
    b = rows["reset"]
    return [m for m in MECHANISMS if m != "reset"
            and rows[m]["acq_cost"] < b["acq_cost"]
            and rows[m]["external"] > b["external"] + 1e-9
            and rows[m]["inflation"] <= b["inflation"] + 1e-9]


def run():
    regimes = {}
    for noise in NOISES:
        for off in SEED_OFFSETS:
            curriculum = [make_task(SEED + 100 + off + i, j, c, noise) for i, (j, c) in enumerate(CURRICULUM)]
            heldout = [make_task(SEED + 900 + off + i, j, c, noise) for i, (j, c) in enumerate(HELDOUT)]
            rows = {m: run_mechanism(m, curriculum, heldout) for m in MECHANISMS}
            regimes[(noise, off)] = {"rows": rows, "winners": regime_winners(rows)}
    return regimes


def stability(regimes):
    n = len(regimes)
    win_counts = {m: 0 for m in MECHANISMS if m != "reset"}
    for r in regimes.values():
        for m in r["winners"]:
            win_counts[m] += 1
    always = [m for m, c in win_counts.items() if c == n]
    ever = [m for m, c in win_counts.items() if c > 0]
    if always:
        verdict = f"ROBUST_DOMINATOR: {always}"
    elif ever:
        verdict = "REGIME_DEPENDENT (winner changes; no robust transfer claim)"
    else:
        verdict = "NO_ROBUST_TRANSFER (nothing wins in any regime)"
    return win_counts, always, ever, verdict, n


def main():
    print("transfer_robustness — does any transfer encoding win across REGIMES, or only in one? (replication test)")
    print("self-tests = validity + stability-verdict soundness. a finding that doesn't replicate is not a finding.\n")
    regimes = run()
    win_counts, always, ever, verdict, n = stability(regimes)

    print(f"  per-regime winners across {n} regimes (noise × seed):")
    for (noise, off), r in regimes.items():
        print(f"    noise={noise:<4} seed+{off:<3} -> winners: {r['winners'] or 'none'}")
    print(f"\n  win counts (out of {n}): " + "  ".join(f"{m}:{c}" for m, c in win_counts.items()))
    print(f"  STABILITY VERDICT: {verdict}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. every regime ran and produced finite metrics for all mechanisms
    finite = all(all(math.isfinite(r["rows"][m][k]) for m in MECHANISMS for k in ("acq_cost", "proxy", "external", "inflation"))
                 for r in regimes.values())
    check("all_regimes_ran", len(regimes) == len(NOISES) * len(SEED_OFFSETS) and finite,
          f"{len(regimes)} regimes (noise×seed), all metrics finite")

    # 2. inflation definitional everywhere
    check("inflation_is_definitional",
          all(abs(r["rows"][m]["inflation"] - (r["rows"][m]["proxy"] - r["rows"][m]["external"])) < 1e-12
              for r in regimes.values() for m in MECHANISMS),
          "inflation == proxy - external in every regime, every mechanism")

    # 3. deterministic metric
    a, w, s = config("reset", State())
    sample = make_task(SEED + 900, HELDOUT[0][0], HELDOUT[0][1], NOISES[0])
    check("capability_deterministic", capability(a, w, s, sample) == capability(a, w, s, sample),
          "capability(config, task) reproducible")

    # 4. each regime's winners are computed correctly from its own baseline (verdict matches evidence, per regime)
    sound_regime = all(r["winners"] == regime_winners(r["rows"]) for r in regimes.values())
    check("regime_winners_sound", sound_regime,
          "each regime's winner set recomputes to the same value from its rows")

    # 5. the STABILITY verdict matches the win counts (no claim beyond what replication supports)
    wc2, always2, ever2, _, _ = stability(regimes)
    ok5 = (("ROBUST_DOMINATOR" in verdict) == bool(always2)) and \
          (("REGIME_DEPENDENT" in verdict) == (not always2 and bool(ever2))) and \
          (("NO_ROBUST_TRANSFER" in verdict) == (not ever2))
    check("stability_verdict_sound", ok5 and wc2 == win_counts,
          f"verdict '{verdict.split('(')[0].strip()}' matches win counts (always={always2}, ever={ever2})")

    # 6. the held-out extras are never in the curriculum, in every regime (fair external measurement)
    seen = {j for j, _ in CURRICULUM}
    check("heldout_unseen_all_regimes", all(j not in seen for j, _ in HELDOUT),
          "held-out extra coords are disjoint from curriculum extras across all regimes")

    # 7. classification complete + no claim inflation
    check("classification_complete",
          verdict.startswith(("ROBUST_DOMINATOR", "REGIME_DEPENDENT", "NO_ROBUST_TRANSFER")),
          "a single stability verdict is emitted; no transfer claim beyond what replicates")

    print(f"\n  {passed}/{total} checks (VALIDITY, not outcome). This is the replication gate the single-run table")
    print("  needed: a transfer winner counts only if it survives across regimes. If the verdict is")
    print("  REGIME_DEPENDENT, the lesson is that 'best transfer representation' is not well-posed without fixing")
    print("  the regime — a more honest stopping point than crowning a one-run winner. evidence may not follow")
    print("  expectation; a finding that doesn't replicate across regimes is not a finding.")
    assert passed == total, "transfer_robustness failed a VALIDITY check (not an outcome expectation)"


if __name__ == "__main__":
    main()
