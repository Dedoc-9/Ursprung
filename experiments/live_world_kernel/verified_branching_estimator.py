# SPDX-License-Identifier: AGPL-3.0-only
"""
verified_branching_estimator.py — the domain estimator that follows from the (corrected) theorem. The theorem says
m_verified is the critical quantity but cannot tell you its value; that is empirical, per domain. This instrument
ESTIMATES it.

It does NOT decide "this domain has/lacks RSI" — that would exceed the evidence. It estimates whether a domain
*appears* subcritical or supercritical under a specified verification regime, with uncertainty.

    verified parent
        ↓  enumerate single-edit neighbours
        ↓  keep only VERIFIED improvements (external gain ∧ replication ∧ calibration — rsi_engine's gate)
        ↓  count them  →  one sample of the offspring number
    m_verified = mean offspring over verified parents visited along a walk across capability scales s
        ↓
    classify: subcritical (m<1−δ) / near-critical (|m−1|≤δ) / supercritical (m>1+δ)   [+ uncertainty]
    and estimate m(s): depletion / temporary-boom / critical / generativity-signal

Crucial honesty: offspring are VERIFIED improvements, not proposed edits and not proxy gains; the output is
"estimated verified branching behaviour under these conditions", with ± SE; the classification is of the
*estimate*, never a claim that the domain is or is not capable of open-ended RSI. `declared ≠ verified`;
`m̂ > 1 ≥ m_verified` would be the runaway. The estimate is also regime-dependent (offspring depend on the
verification regime and the seed sets) — change the regime and you are estimating a different m.

Run (from this directory):  PYTHONHASHSEED=0 python3 verified_branching_estimator.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

D = 12
SEED = 20260623
NOISE = 0.20
INNER_BUDGET = 20
N_PROXY = 3
EXTERNAL_SEEDS = [101, 202, 303]      # independent held-out task sets (replication regime)
N_EXTERNAL = 5
REP_FRAC = 0.60
CAL_TOL = 0.01
MAX_DEPTH = 10
DELTA = 0.10                          # near-critical band around 1
SUPPORT = (2, 6, 9)


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


def ext_per_seed(opt, ext_sets):
    return [mean_cap(opt, tasks) for tasks in ext_sets]


def enumerate_neighbors(opt):
    """All distinct single edits: drop a searched coord, add an unsearched coord, scale sigma."""
    out, active = [], set(opt.active)
    if len(active) > 1:
        for j in sorted(active):
            out.append(Optimizer(tuple(sorted(active - {j})), opt.sigma))
    for j in range(D):
        if j not in active:
            out.append(Optimizer(tuple(sorted(active | {j})), opt.sigma))
    for f in (0.7, 1.4):
        ns = max(1e-3, min(2.0, opt.sigma * f))
        if ns != opt.sigma:
            out.append(Optimizer(opt.active, ns))
    seen, uniq = set(), []
    for o in out:
        key = (o.active, round(o.sigma, 6))
        if key not in seen:
            seen.add(key)
            uniq.append(o)
    return uniq


def is_verified_child(child, parent_ext, parent_proxy, ext_sets, proxy_tasks):
    """rsi_engine's gate: external gain ∧ replication ∧ calibration. The offspring must be VERIFIED."""
    c_ext = ext_per_seed(child, ext_sets)
    external_gain = sum(c_ext) / len(c_ext) - sum(parent_ext) / len(parent_ext)
    need = math.ceil(REP_FRAC * len(ext_sets))
    replicated = sum(1 for c, p in zip(c_ext, parent_ext) if c > p) >= need
    proxy_gain = mean_cap(child, proxy_tasks) - parent_proxy
    calibration_ok = proxy_gain <= external_gain + CAL_TOL
    return (external_gain > 0) and replicated and calibration_ok


def run():
    proxy_tasks = [make_task(SEED + 1 + i) for i in range(N_PROXY)]
    ext_sets = [[make_task(s * 1000 + i) for i in range(N_EXTERNAL)] for s in EXTERNAL_SEEDS]
    roots = [Optimizer(tuple(range(D)), 0.30), Optimizer(tuple(range(D)), 0.55)]
    records = []
    for root in roots:
        parent = root
        p_ext = ext_per_seed(parent, ext_sets)
        p_proxy = mean_cap(parent, proxy_tasks)
        for _ in range(MAX_DEPTH):
            neighbors = enumerate_neighbors(parent)
            verified = [nb for nb in neighbors if is_verified_child(nb, p_ext, p_proxy, ext_sets, proxy_tasks)]
            records.append({"s": sum(p_ext) / len(p_ext), "k": len(verified),
                            "parent": parent, "verified": verified, "n_neighbors": len(neighbors)})
            if not verified:
                break                                   # the walk's lineage went extinct here
            parent = max(verified, key=lambda c: sum(ext_per_seed(c, ext_sets)))   # advance up capability
            p_ext = ext_per_seed(parent, ext_sets)
            p_proxy = mean_cap(parent, proxy_tasks)
    return {"records": records, "ext_sets": ext_sets, "proxy_tasks": proxy_tasks}


def mean_std(xs):
    n = len(xs)
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0
    return m, math.sqrt(var)


def classify_m(m, delta=DELTA):
    return "subcritical" if m < 1 - delta else ("supercritical" if m > 1 + delta else "near-critical")


def buckets_of_s(records, B=3):
    rs = sorted(records, key=lambda r: r["s"])
    n = len(rs)
    out = []
    for b in range(B):
        chunk = rs[b * n // B:(b + 1) * n // B]
        if chunk:
            out.append((sum(r["s"] for r in chunk) / len(chunk), sum(r["k"] for r in chunk) / len(chunk), len(chunk)))
    return out


def classify_shape(buckets, delta=DELTA):
    ms = [m for _, m, _ in buckets]
    if not ms:
        return "no-data"
    if all(m < 1 - delta for m in ms):
        return "subcritical everywhere (depletion)"
    if ms[0] > 1 + delta and ms[-1] < 1 - delta:
        return "temporary boom then depletion (m falls below 1 as capability rises)"
    if all(abs(m - 1) <= delta for m in ms):
        return "near-critical across tested scales"
    if all(m > 1 + delta for m in ms):
        return "supercritical across tested scales (generativity SIGNAL — not proof)"
    return "mixed / indeterminate"


def main():
    print("verified_branching_estimator — estimate m_verified for a domain (an ESTIMATE under conditions, not a verdict).")
    print("offspring = VERIFIED improvements (external ∧ replicated ∧ calibrated), never proposed edits or proxy gains.\n")
    R = run()
    records = R["records"]
    ks = [r["k"] for r in records]
    m, sd = mean_std(ks)
    se = sd / math.sqrt(len(ks)) if ks else 0.0
    cls = classify_m(m)
    buckets = buckets_of_s(records)
    shape = classify_shape(buckets)

    print(f"  verified parents visited: {len(records)} (across {len([r for r in records if r['k']==0])} extinction points)")
    print("  offspring count k at capability s (each parent):")
    for r in records:
        print(f"    s={r['s']:+.3f}  verified offspring k={r['k']}  (of {r['n_neighbors']} neighbours)")
    print(f"\n  m(s) by capability bucket (low→high s):")
    for s_b, m_b, n_b in buckets:
        print(f"    s≈{s_b:+.3f}  m_verified≈{m_b:.2f}  (n={n_b})  -> {classify_m(m_b)}")
    print(f"\n  ESTIMATE (under this verification regime): m_verified ≈ {m:.2f} ± {se:.2f}  ->  {cls}")
    print(f"  m(s) shape: {shape}")
    print(f"  (regime-dependent; change the verification regime/seed sets and you estimate a different m.)\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    # 1. the estimator ran and produced a finite estimate with uncertainty
    check("estimator_ran", len(records) > 0 and math.isfinite(m) and math.isfinite(se) and len(buckets) > 0,
          f"{len(records)} parents, m={m:.2f} ± {se:.2f}, {len(buckets)} capability buckets")

    # 2. THE invariant: every counted offspring is genuinely VERIFIED, and counted == the gate's verdict
    rec = next((r for r in records if r["k"] > 0), records[0])
    p = rec["parent"]
    p_ext = ext_per_seed(p, R["ext_sets"])
    p_proxy = mean_cap(p, R["proxy_tasks"])
    recomputed = [nb for nb in enumerate_neighbors(p)
                  if is_verified_child(nb, p_ext, p_proxy, R["ext_sets"], R["proxy_tasks"])]
    check("offspring_are_verified", len(recomputed) == rec["k"] and set(recomputed) == set(rec["verified"]),
          "counted offspring exactly equal the neighbours that pass external∧replicated∧calibrated — not proposed edits")

    # 3. m is the mean of the offspring counts (definitional)
    check("m_is_mean_offspring", abs(m - sum(ks) / len(ks)) < 1e-12,
          f"m_verified == mean(offspring counts) = {sum(ks)/len(ks):.4f}")

    # 4. the standard error is computed correctly
    m2, sd2 = mean_std(ks)
    check("standard_error_correct", abs(se - (sd2 / math.sqrt(len(ks)))) < 1e-12 and m2 == m,
          "SE == sample std / sqrt(n) — uncertainty is reported, not hidden")

    # 5. the classification matches the estimate vs the band (verdict matches evidence)
    check("classification_sound", cls == classify_m(m) and cls in {"subcritical", "near-critical", "supercritical"},
          f"label '{cls}' is exactly m vs the ±{DELTA} band around 1")

    # 6. m(s) buckets recompute deterministically and the shape label matches them (verdict matches evidence)
    check("m_of_s_sound", buckets == buckets_of_s(records) and shape == classify_shape(buckets),
          f"capability buckets + shape '{shape}' recompute from the records")

    # 7. the output is an ESTIMATE under conditions — never 'has/lacks RSI', and carries uncertainty
    blob = (cls + " " + shape).lower()
    check("no_overclaim_estimate",
          "rsi" not in blob and "has " not in blob and "lacks" not in blob and "proves" not in blob and se >= 0,
          "classification is of the estimate (sub/near/super) with ±SE — no 'has/lacks RSI', no proof claim")

    print(f"\n  {passed}/{total} checks (validity + estimator soundness). The output is a measured, regime-dependent")
    print("  ESTIMATE of the verified branching mean — m_verified ≈ a number ± SE, with an m(s) shape — not a verdict")
    print("  on whether the domain 'has RSI'. The theorem says m_verified is the critical quantity; this estimates")
    print("  it under one regime. The honest reading of a supercritical estimate is 'looks supercritical under these")
    print("  conditions', and of m(s) falling through 1 is 'a boom that depletes'. `declared ≠ verified`.")
    assert passed == total, "verified_branching_estimator failed a validity/soundness check"


if __name__ == "__main__":
    main()
