# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/transition_debt.py — the hidden variable the perceptual axis exposed: switching has a cost.

`allocation = importance + resistance` misses that *changing* the allocation is itself expensive. The arena
surfaced this as perceptual churn; named as a debt, it completes the cost model:

    Total Cost = Representation Debt  +  λ · Transition Debt  +  Latency Debt

    Representation Debt = the future-causal residual (Σ priority · aliasing) — paid by under-fidelity
    Transition Debt     = cost(previous allocation → new allocation) = Σ sensitivity · |Δ samples|  (= PCL)
    Latency Debt        = (reserved) the cost of acting late
    λ                   = the EXCHANGE RATE between representation and transition debt

This explains *why* damped water-filling works: it is not merely smoothing — it pays less Transition Debt.
And it dissolves the "which policy wins?" question into a frontier: the optimum is a **function of λ**. Measured
on the arena (seed 1):

    λ < ~82,000        → ranked_waterfill   (transition cheap → chase the causal residual)
    ~82k < λ < ~591k   → damped_waterfill   (the hardened compromise)
    λ > ~591,000       → uniform            (transition dominant → never move)

Different *modes* are simply different λ — without changing the world model:
    cinematic   : causal accuracy dominant, latency tolerated      → LOW λ
    competitive : low latency + high temporal stability            → HIGH λ
    VR          : perceptual continuity dominant                   → VERY HIGH λ

CLASSIFICATION: OBSERVER (mutates_core=False). It scores cost and selects a policy from the frontier per a
declared λ; it allocates nothing into committed state and asserts no truth.

HONEST BOUND: λ is a declared exchange rate, not a measured constant; Latency Debt is reserved (not modeled).
Constructed-world; the *shape* (a λ-parameterized frontier) is the result, not the crossover numbers, which
`expire_if` measured on real silicon. `integrity ≠ truth`.
"""
from __future__ import annotations


def transition_debt(prev_alloc, cur_alloc, weight):
    """cost(prev → cur) = Σ weight · |Δ samples|. Identical to Perceptual Continuity Loss — the same quantity
    viewed as the debt of switching. `weight` is per-id (sensitivity)."""
    ids = set(prev_alloc) | set(cur_alloc)
    return sum(max(1, int(weight.get(i, 1))) * abs(cur_alloc.get(i, 0) - prev_alloc.get(i, 0)) for i in ids)


def total_cost(representation_debt, transition_debt_value, exchange_rate=1, latency_debt=0):
    """Total Cost = Representation Debt + λ · Transition Debt + Latency Debt. Lower is better."""
    return representation_debt + exchange_rate * transition_debt_value + latency_debt


# mode → exchange-rate band (declared policy, not a measured constant)
MODES = {
    "cinematic": 0,            # causal accuracy dominant; switching is cheap
    "competitive": 120_000,    # low latency + temporal stability; penalize churn
    "vr": 800_000,             # perceptual continuity dominant; almost never move
}


def best_policy(arena_results, exchange_rate):
    """Pick the policy minimizing total cost at a given λ. arena_results: {name: (rep_debt, transition_debt)}."""
    return min(arena_results, key=lambda k: total_cost(arena_results[k][0], arena_results[k][1], exchange_rate))


def regimes(arena_results, lambdas):
    """Map each λ → the policy that wins there (the frontier). Returns [(λ, policy), ...]."""
    return [(lam, best_policy(arena_results, lam)) for lam in lambdas]


def crossovers(arena_results, lam_max=2_000_000, step=1000):
    """The λ values where the winning policy changes — the boundaries of the frontier's regimes."""
    out = []
    prev = None
    lam = 0
    while lam <= lam_max:
        b = best_policy(arena_results, lam)
        if b != prev:
            out.append((lam, b))
            prev = b
        lam += step
    return out


def demo(seed=1, budget=400, frames=24):
    from . import policy_arena as arena
    res = arena.run(seed=seed, budget=budget, frames=frames)
    print("Transition Debt — Total Cost = Representation + λ·Transition (+ Latency), arena seed=%d\n" % seed)
    print("  policy                         rep_debt(causal)   transition_debt(PCL)")
    for k in sorted(res, key=lambda k: res[k][0]):
        print("    %-28s %16d %14d" % (k, res[k][0], res[k][1]))
    print("\n  frontier — winning policy by exchange rate λ:")
    for lam, pol in crossovers(res):
        print("    λ ≥ %9d → %s" % (lam, pol))
    print("\n  modes are λ choices over ONE world model:")
    for mode, lam in MODES.items():
        print("    %-12s (λ=%d) → %s" % (mode, lam, best_policy(res, lam)))
    print("\n  This is why damped water-filling works: it pays less Transition Debt. integrity ≠ truth.")
    return res


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("transition_debt", OBSERVER, mutates_core=False,
                          note="Total Cost = Representation + λ·Transition + Latency; the winning policy is a "
                               "function of the exchange rate λ (modes = λ choices over one world)")
    except LayerViolation:
        pass
