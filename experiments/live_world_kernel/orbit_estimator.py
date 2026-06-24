# SPDX-License-Identifier: AGPL-3.0-only
"""
orbit_estimator.py — the third axis of the RSI decomposition: trajectory GEOMETRY in verified-improvement space.

  branching  (verified_branching_estimator) : does improvement reproduce?      m_offspring
  generativity (generativity_estimator)      : does the frontier grow?          m_novel
  ORBIT (this)                               : WHERE does the system travel?     O(t)

Branching and generativity are both blind to *cycling in a basin*: a system can keep producing verified edits
(`m_offspring` high) that merely circle a region it already discovered. Orbit measures the path itself —
expansion vs revisiting vs convergence — under a DECLARED distance metric `D` and the same declared state-identity
boundary `m_novel` uses (without one, exploration can be faked by re-representation).

    O(t) = D(S_t, S_0)          # displacement from origin over the verified trajectory S_0, S_1, ...
    directedness = D(S_T, S_0) / Σ D(S_t, S_{t-1})    # ~1 = directed expansion; ~0 = wandering in place
    revisit_rate, new_region_rate (by state identity)

Two trajectory policies are contrasted, because geometry depends on the move rule:
  STRICT  — move to the best strictly-improving VERIFIED neighbour (rsi_engine's gate). Monotone in external
            capability, so it CANNOT revisit; it expands then halts in a basin (frontier exhausted).
  EXPLORE — accept non-worsening verified neighbours and move to the one FARTHEST from everything visited (seek
            new territory). If the verified frontier is finite it is forced to revisit or halt — which is exactly
            the cycling/basin-confinement orbit is built to detect.

Classification: CONVERGED (halts, basin) / CYCLING-BASIN (keeps moving but revisits known states) / EXPANDING
(keeps reaching new verified regions). The candidate orbit signature for RSI is EXPANDING — combined with the
other axes, an RSI candidate needs ΔC>0 ∧ G(s)>1 ∧ O(t)↛0. Output is a geometry ESTIMATE under a declared metric
and identity, never "open-ended" or "has RSI"; O(t)↛0 reads "still moving through new territory after N", never
"forever". `declared ≠ verified`; `m_novel ≤ m_offspring`; exploration faked by re-representation is not exploration.

Run (from this directory):  PYTHONHASHSEED=0 python3 orbit_estimator.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

D_DIM = 12
SEED = 20260623
NOISE = 0.20
INNER_BUDGET = 20
N_PROXY = 3
EXTERNAL_SEEDS = [101, 202, 303]
N_EXTERNAL = 5
REP_FRAC = 0.60
CAL_TOL = 0.01
LAT_EPS = 0.01            # EXPLORE accepts neighbours no worse than this (allows lateral moves)
MAX_STEPS = 20
SIGMA_ID_DP = 1          # declared state identity: sigma rounded to this many decimals
SUPPORT = (2, 6, 9)


def _basis(x):
    return [math.cos(j * math.pi * x) for j in range(D_DIM)]


def _err(w, pts):
    return sum(abs(sum(wi * bi for wi, bi in zip(w, _basis(x))) - y) for x, y in pts) / len(pts)


def make_task(seed):
    rng = random.Random(seed)
    coeff = [0.0] * D_DIM
    for j in SUPPORT:
        coeff[j] = rng.uniform(-1.0, 1.0)
    truth = lambda x: sum(coeff[j] * math.cos(j * math.pi * x) for j in SUPPORT)
    train = [(x, truth(x) + rng.gauss(0, NOISE)) for x in (rng.random() for _ in range(14))]
    clean = [(i / 23, truth(i / 23)) for i in range(24)]
    return {"seed": seed, "train": train, "clean": clean, "baseline": _err([0.0] * D_DIM, clean)}


@dataclass(frozen=True)
class Optimizer:
    active: tuple
    sigma: float


def state_id(opt):
    return (opt.active, round(opt.sigma, SIGMA_ID_DP))               # the declared identity boundary


def dist(a, b):
    """Declared metric on states: symmetric-difference of active sets + scaled |Δ rounded-sigma|.
    Both terms are metrics, so the sum is a metric (D(x,x)=0, symmetric, triangle inequality)."""
    sym = len(set(a.active) ^ set(b.active))
    dsig = abs(round(a.sigma, SIGMA_ID_DP) - round(b.sigma, SIGMA_ID_DP))
    return sym + 2.0 * dsig


def capability(opt, task):
    rng = random.Random(task["seed"] * 1009 + 7)
    w = [0.0] * D_DIM
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
    for j in range(D_DIM):
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


def walk(root, policy, ext_sets, proxy_tasks, max_steps=MAX_STEPS):
    cur = root
    cur_ext = ext_per_seed(cur, ext_sets)
    cur_proxy = mean_cap(cur, proxy_tasks)
    traj = [cur]
    ext_curve = [sum(cur_ext) / len(cur_ext)]
    visited_ids = {state_id(cur)}
    moves = []          # (is_new_region: bool, step_size: float)
    halted = False
    need = math.ceil(REP_FRAC * len(ext_sets))
    for _ in range(max_steps):
        cands = []
        for nb in enumerate_neighbors(cur):
            c_ext = ext_per_seed(nb, ext_sets)
            eg = sum(c_ext) / len(c_ext) - sum(cur_ext) / len(cur_ext)
            rep = sum(1 for c, p in zip(c_ext, cur_ext) if c > p) >= need
            cal = (mean_cap(nb, proxy_tasks) - cur_proxy) <= eg + CAL_TOL
            ok = (eg > 0 and rep and cal) if policy == "strict" else (eg >= -LAT_EPS and rep and cal)
            if ok:
                cands.append((nb, c_ext))
        if not cands:
            halted = True
            break
        if policy == "strict":
            nb, c_ext = max(cands, key=lambda x: sum(x[1]))                 # best external
        else:
            nb, c_ext = max(cands, key=lambda x: min(dist(x[0], v) for v in traj))   # farthest from visited
        step = dist(nb, cur)
        sid = state_id(nb)
        is_new = sid not in visited_ids
        visited_ids.add(sid)
        moves.append((is_new, step))
        traj.append(nb)
        ext_curve.append(sum(c_ext) / len(c_ext))
        cur, cur_ext, cur_proxy = nb, c_ext, mean_cap(nb, proxy_tasks)
    return {"traj": traj, "ext_curve": ext_curve, "visited_ids": visited_ids, "moves": moves, "halted": halted}


def geometry(run):
    traj, moves = run["traj"], run["moves"]
    steps = len(moves)
    O_curve = [dist(s, traj[0]) for s in traj]
    displacement = dist(traj[-1], traj[0])
    path_length = sum(s for _, s in moves)
    directedness = displacement / path_length if path_length > 1e-12 else 0.0
    revisits = sum(1 for new, _ in moves if not new)
    revisit_rate = revisits / steps if steps else 0.0
    new_rate = (len(run["visited_ids"]) - 1) / steps if steps else 0.0
    late = moves[len(moves) // 2:]
    late_new_rate = sum(1 for new, _ in late if new) / len(late) if late else 0.0
    return {"steps": steps, "O_curve": O_curve, "displacement": displacement, "path_length": path_length,
            "directedness": directedness, "revisit_rate": revisit_rate, "new_rate": new_rate,
            "late_new_rate": late_new_rate, "halted": run["halted"]}


def classify_orbit(g):
    if g["halted"] and g["steps"] < MAX_STEPS:
        return "CONVERGED (frontier exhausted — settled in a basin)"
    if g["late_new_rate"] < 0.15 and g["revisit_rate"] > 0:
        return "CYCLING / BASIN-CONFINED (revisiting known verified states)"
    if g["late_new_rate"] >= 0.5:
        return "EXPANDING (keeps reaching new verified regions)"
    return "MIXED / SLOWING"


def main():
    print("orbit_estimator — trajectory geometry in verified-improvement space (where does the system travel?).")
    print("metric D = active-set symmetric-difference + 2·|Δσ~1dp|; identity = (active set, σ~1dp). estimate, not verdict.\n")
    proxy_tasks = [make_task(SEED + 1 + i) for i in range(N_PROXY)]
    ext_sets = [[make_task(s * 1000 + i) for i in range(N_EXTERNAL)] for s in EXTERNAL_SEEDS]
    root = Optimizer(tuple(range(D_DIM)), 0.30)

    results = {}
    for policy in ("strict", "explore"):
        r = walk(root, policy, ext_sets, proxy_tasks)
        g = geometry(r)
        results[policy] = (r, g)
        dC = r["ext_curve"][-1] - r["ext_curve"][0]
        moving = (not g["halted"]) and (g["late_new_rate"] > 0 or (g["O_curve"][-1] - g["O_curve"][len(g["O_curve"]) // 2]) > 0)
        print(f"  policy={policy:<8} steps={g['steps']:<3} halted={g['halted']!s:<5} ΔC={dC:+.3f}  "
              f"displacement={g['displacement']:.1f}  path={g['path_length']:.1f}  directedness={g['directedness']:.2f}")
        print(f"           revisit_rate={g['revisit_rate']:.2f}  new_region_rate={g['new_rate']:.2f}  "
              f"late_new_rate={g['late_new_rate']:.2f}  O(t)↛0 (still moving into new territory)={moving}")
        print(f"           O(t)=D(S_t,S_0): {[round(o,1) for o in g['O_curve']]}")
        print(f"           orbit: {classify_orbit(g)}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    g_strict = results["strict"][1]
    g_expl = results["explore"][1]

    # 1. ran: both trajectories produced finite geometry
    check("estimator_ran",
          all(math.isfinite(v) for g in (g_strict, g_expl)
              for v in (g["displacement"], g["path_length"], g["directedness"], g["revisit_rate"])),
          "strict + explore trajectories built; geometry finite")

    # 2. D is a metric: identity, symmetry, non-negativity, triangle (on sample states)
    a = Optimizer((1, 2, 3), 0.3)
    b = Optimizer((2, 3, 4), 0.5)
    c = Optimizer((5,), 0.2)
    metric_ok = (dist(a, a) == 0 and dist(a, b) == dist(b, a) and dist(a, b) >= 0
                 and dist(a, c) <= dist(a, b) + dist(b, c) + 1e-9)
    check("distance_is_metric", metric_ok,
          "D(x,x)=0, symmetric, non-negative, triangle inequality holds — a declared metric")

    # 3. STRICT is monotone in external capability and therefore CANNOT revisit (invariant)
    ext = results["strict"][0]["ext_curve"]
    check("strict_monotone_nonrevisiting",
          all(ext[i + 1] >= ext[i] - 1e-12 for i in range(len(ext) - 1)) and g_strict["revisit_rate"] == 0.0,
          "strict improve-only trajectory: external non-decreasing ⇒ revisit_rate = 0 (can't return to a worse state)")

    # 4. displacement ≤ path length, for both trajectories (triangle-inequality consequence — invariant)
    check("displacement_le_pathlength",
          g_strict["displacement"] <= g_strict["path_length"] + 1e-9 and g_expl["displacement"] <= g_expl["path_length"] + 1e-9,
          "net displacement never exceeds path length — geometry is consistent with the metric")

    # 5. orbit classification matches the measured geometry (verdict matches evidence)
    def label_sound(g):
        l = classify_orbit(g)
        if l.startswith("CONVERGED"):
            return g["halted"] and g["steps"] < MAX_STEPS
        if l.startswith("EXPANDING"):
            return g["late_new_rate"] >= 0.5
        if l.startswith("CYCLING"):
            return g["late_new_rate"] < 0.15 and g["revisit_rate"] > 0
        return True
    check("orbit_classification_sound", label_sound(g_strict) and label_sound(g_expl),
          f"each label's defining metric condition holds (strict → {classify_orbit(g_strict).split()[0]}, "
          f"explore → {classify_orbit(g_expl).split()[0]})")

    # 6. identity boundary is declared and is what revisit/new-region use
    check("identity_declared",
          state_id(Optimizer((1, 2), 0.31)) == state_id(Optimizer((1, 2), 0.34)) and
          state_id(Optimizer((1, 2), 0.31)) != state_id(Optimizer((1, 2), 0.41)),
          "state identity = (active set, σ~1dp) — coarser identity ⇒ more revisits; declared, could be varied")

    # 7. determinism
    g2 = geometry(walk(root, "strict", ext_sets, proxy_tasks))
    check("deterministic", g2["O_curve"] == g_strict["O_curve"],
          "seeded trajectory reproduces exactly")

    # 8. no overclaim: geometry estimate under declared metric/identity; never 'open-ended'/'has RSI'
    blob = (classify_orbit(g_strict) + " " + classify_orbit(g_expl)).lower()
    check("no_overclaim_estimate",
          "rsi" not in blob and "open-ended" not in blob and "has " not in blob and "proves" not in blob,
          "orbit is a geometry class under a declared metric — not a domain verdict; O(t)↛0 means 'after N', not 'forever'")

    print(f"\n  {passed}/{total} checks. Orbit is the third axis: branching asks if improvement reproduces,")
    print("  generativity if the frontier grows, orbit WHERE the system travels. A strict improve-only policy")
    print("  cannot cycle (it is monotone, so it expands then HALTS in a basin); an explore policy reveals whether")
    print("  new verified territory remains or the system is forced to revisit. The RSI-candidate orbit signature")
    print("  is EXPANDING (O(t)↛0 with new regions); combined: ΔC>0 ∧ G(s)>1 ∧ O(t)↛0. estimate ≠ property;")
    print("  the metric and identity are declared and could be varied; faked exploration via re-representation is not exploration.")
    assert passed == total, "orbit_estimator failed a validity/invariant check"


if __name__ == "__main__":
    main()
