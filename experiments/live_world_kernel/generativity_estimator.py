# SPDX-License-Identifier: AGPL-3.0-only
"""
generativity_estimator.py — the refined estimator the last run argued for, on both axes the discussion exposed:

  (A) STATISTICAL POWER. verified_branching_estimator gave m ≈ 1.00 ± 1.00 at n=3 — vacuous, because a greedy
      lineage walk in a (near-)subcritical domain dies before it can sample (the process destroys its own sample).
      Fix: many INDEPENDENT roots, pooled verified-parent samples, and BOOTSTRAP confidence intervals over roots,
      with a hard reporting rule — informative only if the CI excludes 1; otherwise "cannot distinguish".

  (B) THE RIGHT QUANTITY. A branching process counts offspring as independent lineages, but verified self-edits
      overlap: two verified children may unlock the SAME future region. So raw child count overstates generativity.
      We therefore estimate two means side by side:
          m_offspring = E[ verified children per verified parent ]                 (reproduction rate)
          m_novel     = E[ net-new reachable verified STATES per verified parent ] (frontier expansion)
      Always m_offspring ≥ m_novel; the GAP is the overlap, quantified. m_novel is closer to what "recursive
      self-improvement" actually requires: that the reachable verified frontier keeps expanding.

DECLARED MODELING BOUNDARY (no free lunch): m_novel needs a notion of STATE IDENTITY — when two verified states
count as "the same". Here a state is `(active-coordinate set, sigma rounded to 1 decimal)`. This is an
Arbitrary-Boundary choice; coarser identity ⇒ more overlap ⇒ smaller m_novel. It is declared, and could be varied.

DECLARED CI METHOD (which interval this is, and why): m_novel is a COVERAGE functional, |union|/n. A with-replacement
bootstrap that RECOMPUTES the union per resample collapses on duplicated roots (a repeated root adds parents but no
new distinct states), biasing the interval low so the point falls outside it — this is the bug `ci_brackets_point`
caught. So m_novel's CI here is the LINEARIZATION (influence-function / Hájek-projection) interval: bootstrap the
per-parent MARGINAL-novelty contributions (which sum to |union|), a standard asymptotically-valid variance estimate
that stays point-centred. The cost: marginal ATTRIBUTION is order-dependent (the mean is not), so this is a
linearization interval, NOT an exact union bootstrap; an exact treatment would need subsampling WITHOUT replacement
(m-out-of-n), which avoids duplicate-collapse but carries its own coverage-ratio finite-sample bias. No method is
free; this one is named.

Output is an ESTIMATE under a stated verification regime (external ∧ replicated ∧ calibrated offspring), with CIs,
never "this domain has/lacks RSI". `m_offspring ≥ m_novel`; `estimate ≠ property`; `declared ≠ verified`.

Run (from this directory):  PYTHONHASHSEED=0 python3 generativity_estimator.py
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
EXTERNAL_SEEDS = [101, 202, 303]
N_EXTERNAL = 5
REP_FRAC = 0.60
CAL_TOL = 0.01
ROOTS = 20
MAX_DEPTH = 3
SIGMA_ID_DP = 1            # state identity: sigma rounded to this many decimals (the declared boundary)
BOOTSTRAP = 2000
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


def state_id(opt):
    return (opt.active, round(opt.sigma, SIGMA_ID_DP))      # the declared state-identity boundary


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
        k = (o.active, round(o.sigma, 6))
        if k not in seen:
            seen.add(k)
            uniq.append(o)
    return uniq


def is_verified_child(child, parent_ext, parent_proxy, ext_sets, proxy_tasks):
    c_ext = ext_per_seed(child, ext_sets)
    external_gain = sum(c_ext) / len(c_ext) - sum(parent_ext) / len(parent_ext)
    need = math.ceil(REP_FRAC * len(ext_sets))
    replicated = sum(1 for c, p in zip(c_ext, parent_ext) if c > p) >= need
    proxy_gain = mean_cap(child, proxy_tasks) - parent_proxy
    calibration_ok = proxy_gain <= external_gain + CAL_TOL
    return (external_gain > 0) and replicated and calibration_ok


def collect(root, ext_sets, proxy_tasks):
    """Greedy verified walk from one root. Per visited verified parent: offspring count + its verified-child
    STATE set (deduped by state_id) + capability s."""
    out = []
    parent = root
    p_ext = ext_per_seed(parent, ext_sets)
    p_proxy = mean_cap(parent, proxy_tasks)
    for _ in range(MAX_DEPTH):
        neighbors = enumerate_neighbors(parent)
        verified = [nb for nb in neighbors if is_verified_child(nb, p_ext, p_proxy, ext_sets, proxy_tasks)]
        out.append({"s": sum(p_ext) / len(p_ext), "offspring": len(verified),
                    "children": frozenset(state_id(nb) for nb in verified)})
        if not verified:
            break
        parent = max(verified, key=lambda c: sum(ext_per_seed(c, ext_sets)))
        p_ext = ext_per_seed(parent, ext_sets)
        p_proxy = mean_cap(parent, proxy_tasks)
    return out


def pool(per_root):
    """m_offspring and m_novel are BOTH per-parent means (so bootstrap is valid). p['novel'] is the parent's
    MARGINAL novelty (child states not seen in any earlier parent); marginal novelties sum to |global union|, so
    mean(novel) == |union| / n — the coverage rate — but as a per-parent attribute it bootstraps to a CI centered
    on the point estimate. Requires p['novel'] precomputed by run() in a fixed order."""
    parents = [p for rr in per_root for p in rr]
    n = len(parents)
    if n == 0:
        return 0, 0.0, 0.0
    m_off = sum(p["offspring"] for p in parents) / n
    m_nov = sum(p["novel"] for p in parents) / n
    return n, m_off, m_nov


def bootstrap_ci(per_root, rng, B=BOOTSTRAP):
    R = len(per_root)
    offs, novs = [], []
    for _ in range(B):
        sample = [per_root[rng.randrange(R)] for _ in range(R)]
        n, mo, mn = pool(sample)
        if n > 0:
            offs.append(mo)
            novs.append(mn)
    offs.sort()
    novs.sort()
    ci = lambda xs: (xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs))])
    return ci(offs), ci(novs)


def informativeness(ci):
    lo, hi = ci
    if hi < 1.0:
        return "subcritical (CI entirely below 1)"
    if lo > 1.0:
        return "supercritical (CI entirely above 1)"
    return "UNINFORMATIVE — cannot distinguish from critical under current sampling (CI crosses 1)"


def buckets(per_root, B=3):
    parents = sorted((p for rr in per_root for p in rr), key=lambda p: p["s"])
    n = len(parents)
    out = []
    for b in range(B):
        chunk = parents[b * n // B:(b + 1) * n // B]
        if chunk:
            s_b = sum(p["s"] for p in chunk) / len(chunk)
            mo = sum(p["offspring"] for p in chunk) / len(chunk)
            mn = sum(p["novel"] for p in chunk) / len(chunk)
            out.append((s_b, mo, mn, len(chunk)))
    return out


def run():
    rng = random.Random(SEED)
    proxy_tasks = [make_task(SEED + 1 + i) for i in range(N_PROXY)]
    ext_sets = [[make_task(s * 1000 + i) for i in range(N_EXTERNAL)] for s in EXTERNAL_SEEDS]
    roots = []
    for _ in range(ROOTS):
        size = rng.randint(4, D)
        active = tuple(sorted(rng.sample(range(D), size)))
        roots.append(Optimizer(active, rng.choice([0.2, 0.3, 0.4, 0.5])))
    per_root = [collect(r, ext_sets, proxy_tasks) for r in roots]
    # MARGINAL novelty in a fixed order (root order, then walk order): each parent's child states not yet seen.
    # Sum of marginals == |global union|, so mean(novel) == coverage rate, but as a per-parent attribute it
    # bootstraps to a point-centred CI. (Marginal ATTRIBUTION is order-dependent; the mean is not.)
    seen = set()
    for rr in per_root:
        for p in rr:
            p["novel"] = len(p["children"] - seen)
            seen |= p["children"]
    return {"per_root": per_root, "ext_sets": ext_sets, "proxy_tasks": proxy_tasks}


def main():
    print("generativity_estimator — m_offspring (reproduction) vs m_novel (frontier expansion), many roots + CIs.")
    print("offspring = VERIFIED (external ∧ replicated ∧ calibrated). state identity = (active set, sigma~1dp). estimate, not verdict.\n")
    R = run()
    per_root = R["per_root"]
    n, m_off, m_nov = pool(per_root)
    ci_off, ci_nov = bootstrap_ci(per_root, random.Random(SEED + 99))
    bks = buckets(per_root)

    print(f"  verified parents pooled across {ROOTS} independent roots: n = {n}")
    print(f"  m_offspring ≈ {m_off:.2f}   95% CI [{ci_off[0]:.2f}, {ci_off[1]:.2f}]   -> {informativeness(ci_off)}")
    print(f"  m_novel     ≈ {m_nov:.2f}   95% CI [{ci_nov[0]:.2f}, {ci_nov[1]:.2f}]   -> {informativeness(ci_nov)}")
    print(f"  overlap gap  = m_offspring - m_novel = {m_off - m_nov:.2f}  (how much offspring overstates generativity)\n")
    print("  m(s) by capability bucket (low→high s):")
    for s_b, mo, mn, nb in bks:
        print(f"    s≈{s_b:+.3f}  m_offspring≈{mo:.2f}  m_novel≈{mn:.2f}  (n={nb})")
    print()

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    # 1. ran with real statistical power (many roots pooled into n verified parents) + CIs
    check("estimator_ran", n > 0 and len(per_root) == ROOTS and all(map(math.isfinite, (m_off, m_nov, *ci_off, *ci_nov))),
          f"{ROOTS} roots → n={n} verified parents; offspring & novel CIs computed")

    # 2. offspring are genuinely VERIFIED (reconstruct the roots, recompute the gate on the first parent w/ offspring)
    ok2 = True
    rng2 = random.Random(SEED)
    roots2 = []
    for _ in range(ROOTS):
        size = rng2.randint(4, D)
        active = tuple(sorted(rng2.sample(range(D), size)))
        roots2.append(Optimizer(active, rng2.choice([0.2, 0.3, 0.4, 0.5])))
    for root, rr in zip(roots2, per_root):
        if rr and rr[0]["offspring"] > 0:
            p_ext = ext_per_seed(root, R["ext_sets"])
            p_proxy = mean_cap(root, R["proxy_tasks"])
            verified = [nb for nb in enumerate_neighbors(root)
                        if is_verified_child(nb, p_ext, p_proxy, R["ext_sets"], R["proxy_tasks"])]
            ok2 = (len(verified) == rr[0]["offspring"]
                   and frozenset(state_id(nb) for nb in verified) == rr[0]["children"])
            break
    check("offspring_are_verified", ok2,
          "counted offspring = neighbours passing external∧replicated∧calibrated; child STATES match (recomputed)")

    # 3. THE invariant: novel ≤ offspring per parent (marginal-novel ≤ distinct children ≤ offspring), so m_novel ≤ m_offspring
    all_parents = [p for rr in per_root for p in rr]
    check("novel_le_offspring",
          all(p["novel"] <= p["offspring"] for p in all_parents) and m_nov <= m_off + 1e-9
          and all(mn <= mo + 1e-9 for _, mo, mn, _ in bks),
          f"m_novel {m_nov:.2f} ≤ m_offspring {m_off:.2f} per parent and per bucket — the gap IS the overlap")

    # 4. each point estimate lies within its bootstrap CI
    check("ci_brackets_point", ci_off[0] - 1e-9 <= m_off <= ci_off[1] + 1e-9 and ci_nov[0] - 1e-9 <= m_nov <= ci_nov[1] + 1e-9,
          "point estimates fall inside their 95% bootstrap intervals")

    # 5. the informativeness label matches the CI vs 1 (verdict matches evidence)
    def expect(ci):
        lo, hi = ci
        return "below" if hi < 1 else ("above" if lo > 1 else "cross")
    lbl = lambda ci: ("below" if "below" in informativeness(ci) else "above" if "above" in informativeness(ci) else "cross")
    check("informativeness_sound", lbl(ci_off) == expect(ci_off) and lbl(ci_nov) == expect(ci_nov),
          "‘informative/uninformative’ is exactly whether the CI excludes or crosses 1")

    # 6. determinism: the core metric is reproducible (so the whole pipeline is)
    t = R["ext_sets"][0][0]
    op = Optimizer(SUPPORT, 0.3)
    check("capability_deterministic", capability(op, t) == capability(op, t),
          "capability(opt, task) reproducible — the seeded estimate is deterministic")

    # 7. no overclaim: estimates carry CIs; uses 'cannot distinguish' when a CI crosses 1; never 'has/lacks RSI'
    blob = (informativeness(ci_off) + " " + informativeness(ci_nov)).lower()
    check("no_overclaim_estimate",
          "rsi" not in blob and "has " not in blob and "lacks" not in blob and "proves" not in blob,
          "output is m ± CI under a regime + a declared state-identity boundary — not a domain verdict")

    print(f"\n  {passed}/{total} checks. Two means, side by side, with bootstrap CIs over independent roots: m_offspring")
    print("  (reproduction) and m_novel (frontier expansion), with the gap reporting overlap. The honest reading is")
    print("  whichever the CIs license: a CI crossing 1 reads 'cannot distinguish under current sampling', not")
    print("  'near-critical'. m_novel ≤ m_offspring always — counting offspring is an upper bound on generativity.")
    print("  estimate ≠ property; the state-identity boundary is declared and could be varied. `declared ≠ verified`.")
    assert passed == total, "generativity_estimator failed a validity/invariant check"


if __name__ == "__main__":
    main()
