# SPDX-License-Identifier: AGPL-3.0-only
"""
resource_accounting.py — a cost-accounting LAYER attached to the verified-dynamics suite, NOT a fifth RSI axis.

The question is the honest, measurable half of "switch logic to lesser-heat layers": does a cheap screen in front
of the expensive verification let the gated pipeline do FEWER units of defined work than a naive one that fully
verifies every candidate? That is *work avoidance*, and it is benchable today. What is NOT measured here is energy:
no joules, no power draw, no transition counts. `mechanism ≠ consequence` — a gate can reduce wasted evaluation
without being thermodynamically free; `no_inflation_latch` enforces `claim ≤ evidence`, it does not enforce
`heat ≈ 0`. Per the repo's own rule, the energy claim has no bench, so it is reported `N/A`, and the hardware
(FPGA/ASIC, joules/check) claim is `SCOPED` until a silicon power bench exists — never asserted.

Two pipelines over the SAME candidate edits, counting actual capability evaluations (the dominant work unit):
  NAIVE  — run the full verification (external across seeds + replication + calibration) on EVERY candidate.
  GATED  — run a CHEAP single-task screen first; run the full verification ONLY on candidates that pass the screen.

Reported, with the discipline's two guards:
  * work_avoided = W_naive − W_gated, MEASURED and printed with its sign — never asserted positive (an ineffective
    screen can make the gated pipeline do MORE work; that is an outcome, not a validity property).
  * fidelity: the screen is not free either — false_negatives (a candidate the full check would have verified, but
    the cheap screen dropped) and false_positives (passed the screen, failed the full check) are measured and shown.
  * work efficiency η = true_promotions / capability_evaluations, reported for naive and gated with Δη — the single
    ratio that puts saved work and lost opportunity on ONE ledger (a screen that saves 90% of evals but drops most
    useful paths shows up here as a deceptive-looking Δη that the false_negative count contradicts). η is a PROXY:
    read it WITH false_negatives, never as "higher is universally better" (a gate that rejects everything has 0
    promotions and a meaningless η).

This is the *Accounting* pillar of a measurement framework for verified adaptive systems (capability / generativity
/ orbit / accounting) — not an RSI detector. `claim ≤ measurement`; `mechanism ≠ consequence`; `declared ≠ verified`.

Run (from this directory):  PYTHONHASHSEED=0 python3 resource_accounting.py
"""
from __future__ import annotations

import math
import random

import generativity_estimator as G
from generativity_estimator import Optimizer, make_task, enumerate_neighbors

SEED = G.SEED
EXTERNAL_SEEDS, N_EXTERNAL, N_PROXY = G.EXTERNAL_SEEDS, G.N_EXTERNAL, G.N_PROXY
REP_FRAC, CAL_TOL, D = G.REP_FRAC, G.CAL_TOL, G.D
N_ROOTS = 5

EVAL = {"n": 0}                       # the work counter: every capability evaluation increments it


def cap(opt, task):
    EVAL["n"] += 1
    return G.capability(opt, task)


def mean_cap(opt, tasks):
    return sum(cap(opt, t) for t in tasks) / len(tasks)


def ext_list(opt, ext_sets):
    return [mean_cap(opt, ts) for ts in ext_sets]


COST_FULL = len(EXTERNAL_SEEDS) * N_EXTERNAL + N_PROXY    # capability evals one full check costs (per candidate)
COST_CHEAP = 1                                            # the cheap screen: one capability eval


def full_check(cand, parent_ext, parent_proxy, ext_sets, proxy_tasks):
    """The expensive gate: external gain ∧ replication ∧ calibration. Costs COST_FULL capability evals."""
    c_ext = ext_list(cand, ext_sets)
    external_gain = sum(c_ext) / len(c_ext) - sum(parent_ext) / len(parent_ext)
    need = math.ceil(REP_FRAC * len(ext_sets))
    replicated = sum(1 for c, p in zip(c_ext, parent_ext) if c > p) >= need
    proxy_gain = mean_cap(cand, proxy_tasks) - parent_proxy
    return (external_gain > 0) and replicated and (proxy_gain <= external_gain + CAL_TOL)


def cheap_screen(cand, parent_screen_val, screen_task):
    """A fast, single-task prefilter (1 eval). Necessary-ish, NOT sound — its misses are measured as fidelity cost."""
    return cap(cand, screen_task) > parent_screen_val


def run():
    rng = random.Random(SEED)
    proxy_tasks = [make_task(SEED + 1 + i) for i in range(N_PROXY)]
    ext_sets = [[make_task(s * 1000 + i) for i in range(N_EXTERNAL)] for s in EXTERNAL_SEEDS]

    # candidate edits = neighbourhoods of several seeded roots, each paired with its parent's caches
    items = []   # (cand, parent_ext, parent_proxy, parent_screen_val)
    for _ in range(N_ROOTS):
        size = rng.randint(4, D)
        parent = Optimizer(tuple(sorted(rng.sample(range(D), size))), rng.choice([0.2, 0.3, 0.4, 0.5]))
        p_ext = ext_list(parent, ext_sets)                 # parent caches: computed BEFORE counting, not charged
        p_proxy = mean_cap(parent, proxy_tasks)
        p_screen = G.capability(parent, proxy_tasks[0])    # screen baseline (uncounted; parent side)
        for cand in enumerate_neighbors(parent):
            items.append((cand, p_ext, p_proxy, p_screen))
    n = len(items)

    # NAIVE: full check on every candidate
    EVAL["n"] = 0
    naive_pass = []
    for i, (cand, pe, pp, ps) in enumerate(items):
        if full_check(cand, pe, pp, ext_sets, proxy_tasks):
            naive_pass.append(i)
    w_naive = EVAL["n"]

    # GATED: cheap screen first; full check only on survivors
    EVAL["n"] = 0
    screen_pass, gated_full = [], []
    for i, (cand, pe, pp, ps) in enumerate(items):
        if cheap_screen(cand, ps, proxy_tasks[0]):
            screen_pass.append(i)
            gated_full.append(i)
            full_check(cand, pe, pp, ext_sets, proxy_tasks)   # the survivors that get the expensive check
    w_gated = EVAL["n"]

    naive_set, screen_set = set(naive_pass), set(screen_pass)
    eta_naive = len(naive_set) / w_naive                       # true promotions per capability-eval
    eta_gated = len(naive_set & screen_set) / w_gated
    return {
        "n": n, "w_naive": w_naive, "w_gated": w_gated, "work_avoided": w_naive - w_gated,
        "full_checks_naive": n, "full_checks_gated": len(gated_full),
        "promotions_naive": len(naive_set),
        "promotions_gated": len(naive_set & screen_set),       # screen-pass AND full-pass
        "false_negatives": len(naive_set - screen_set),        # full-pass dropped by the cheap screen (missed)
        "false_positives": len(screen_set - naive_set),        # screen-pass that fail full (wasted full check)
        "eta_naive": eta_naive, "eta_gated": eta_gated, "d_eta": eta_gated - eta_naive,
        "energy_joules": None, "hardware_efficiency": "SCOPED",
    }


def main():
    print("resource_accounting — work-avoidance of a cheap-screen gate vs full verification (energy NOT measured).\n")
    r = run()
    print("  verification cost profile (work unit = capability evaluation):")
    print(f"    candidates: {r['n']}")
    print(f"    naive : full checks {r['full_checks_naive']:>4}   work {r['w_naive']:>6}")
    print(f"    gated : full checks {r['full_checks_gated']:>4}   work {r['w_gated']:>6}  (cheap screen on all {r['n']}, full on survivors)")
    sign = "saved" if r["work_avoided"] > 0 else ("SPENT extra" if r["work_avoided"] < 0 else "broke even")
    print(f"    work avoided: {r['work_avoided']:+d} capability-eval units  ({sign})")
    print(f"  fidelity (the screen is not free): promotions naive={r['promotions_naive']} gated={r['promotions_gated']}; "
          f"false negatives (missed)={r['false_negatives']}, false positives (wasted full)={r['false_positives']}")
    print(f"  work efficiency η = true promotions / capability-evals  (a PROXY — read WITH false negatives above, "
          f"not as 'higher = better'):")
    print(f"    naive η = {r['eta_naive']:.5f}   gated η = {r['eta_gated']:.5f}   Δη = {r['d_eta']:+.5f}")
    print(f"  energy: N/A — no joule / power / transition measurement performed")
    print(f"  hardware efficiency: {r['hardware_efficiency']} — requires a silicon (FPGA/ASIC) power bench\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    # 1. the accounting is internally consistent and the counter is correct
    check("accounting_consistent",
          r["work_avoided"] == r["w_naive"] - r["w_gated"] and r["w_naive"] == r["n"] * COST_FULL,
          f"work_avoided = w_naive - w_gated; w_naive == n×COST_FULL ({r['n']}×{COST_FULL}={r['n']*COST_FULL})")

    # 2. the gate ran the expensive check ONLY on screen survivors
    check("full_only_on_survivors",
          r["full_checks_gated"] <= r["n"] and r["w_gated"] == r["n"] * COST_CHEAP + r["full_checks_gated"] * COST_FULL,
          f"gated work == n×cheap + survivors×full ({r['n']}×1 + {r['full_checks_gated']}×{COST_FULL})")

    # 3. work avoidance is REPORTED, not asserted positive (an ineffective screen can spend MORE — that's an outcome)
    check("work_avoided_is_measured_not_assumed", isinstance(r["work_avoided"], int),
          f"work_avoided = {r['work_avoided']:+d} is a measured quantity with a sign, not a guaranteed gain")

    # 4. the screen's fidelity cost is measured (no free lunch): false negatives/positives are reported
    check("fidelity_reported",
          r["false_negatives"] >= 0 and r["false_positives"] >= 0
          and r["promotions_gated"] == r["promotions_naive"] - r["false_negatives"],
          f"missed={r['false_negatives']}, wasted={r['false_positives']} — the screen's cost is on the record")

    # 5. THE discipline guard: no energy is claimed (the field is unmeasured), per evidence ≤ maturity
    check("no_energy_claim", r["energy_joules"] is None,
          "energy_joules is N/A — no joule/power bench exists, so no thermal benefit is asserted")

    # 6. hardware efficiency is held SCOPED, never MEASURED
    check("hardware_efficiency_scoped", r["hardware_efficiency"] == "SCOPED",
          "FPGA/ASIC joules-per-check is a separate engineering hypothesis, scoped until a silicon bench runs")

    # 7. work efficiency η is definitional and put on the same ledger as fidelity (not asserted "higher is better")
    check("work_efficiency_consistent",
          abs(r["eta_naive"] - r["promotions_naive"] / r["w_naive"]) < 1e-12
          and abs(r["eta_gated"] - r["promotions_gated"] / r["w_gated"]) < 1e-12
          and abs(r["d_eta"] - (r["eta_gated"] - r["eta_naive"])) < 1e-12,
          f"η = true_promotions / capability-evals for both pipelines; Δη={r['d_eta']:+.5f} is a proxy, read with "
          f"false_negatives={r['false_negatives']}")

    # 8. determinism
    r2 = run()
    check("deterministic", (r2["w_naive"], r2["w_gated"], r2["work_avoided"], r2["d_eta"]) == (r["w_naive"], r["w_gated"], r["work_avoided"], r["d_eta"]),
          "seeded work counts and η reproduce exactly")

    print(f"\n  {passed}/{total} checks. This layer measures WORK AVOIDANCE (capability-eval units saved or spent by")
    print("  screening before full verification) and the screen's fidelity cost — both deterministic and signed. It")
    print("  measures NO energy: `mechanism ≠ consequence`, a gate reduces wasted evaluation without being free.")
    print("  Software work-avoidance is MEASURED; hardware joules/check is SCOPED until a silicon bench exists. The")
    print("  same no-inflation rule that stopped the RSI claim stops the energy claim. `declared ≠ verified`.")
    assert passed == total, "resource_accounting failed a validity check"


if __name__ == "__main__":
    main()
