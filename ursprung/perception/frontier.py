# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/frontier.py — the NON-separable privacy–utility frontier (the measurable cost of knowledge).

Session accounting (`session_accounting.py`) won because the task channel was *separable* from the leak
channel — the task needed a coarse band, the secret was a fine cell, so the compiler dropped the triangulating
channel for free. That was the easy case, and it rested on a large hidden assumption: **useful information and
secret information can be separated.** This module deliberately violates it.

The task here is **exact interception**: the agent must name the enemy's exact cell, and "utility" is the
fraction of encounters it hits exactly. Now the thing the task needs (precise position) *is* the thing being
protected (the secret). There is no channel to drop — only a resolution to choose. Disclosing `k` of the
secret's 6 bits narrows the candidate set to `2^(6−k)` cells; the agent aims at the centroid; it hits exactly
only when the disclosure pins the cell. So **leakage and utility are the same quantity**, and the result is not
a win — it is a **frontier**:

    leakage (bits)   utility (exact-hit rate)
        0                ~0.02
        1                ~0.03
        ...               (utility ≈ 2^(leakage−6) — doubling per disclosed bit)
        6                 1.00

Full utility STRICTLY requires full leakage. That is the opposite of the separable case (there, U=1.0 at
L<1 bit), and it is the more important outcome: it shows the session win was a special case, not a general
escape. When the task genuinely needs the secret, the framework's job is no longer to *eliminate* the tradeoff
but to **measure** it — to publish the cost of knowledge so the policy author's choice (more utility, or less
leakage?) becomes explicit, measurable, and contestable. *That* visibility — not a free lunch — is the
contribution.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: the utility model (exact-hit interception, centroid
aim) is a declared convention; a different task geometry shifts the curve's shape but not its coupling. The
broader claim — that participation *rarely* needs full knowledge — is now a per-task empirical question this
frontier can answer case by case, not a settled thesis. leakage ↔ utility are coupled here by construction;
constructed world; `simulation ≠ physics`.
"""
from __future__ import annotations

from math import log2

try:
    from ..channel_discovery import mutual_information
except Exception:                                            # pragma: no cover - standalone fallback
    from collections import Counter as _Counter

    def mutual_information(pairs):
        n = len(pairs)
        if n == 0:
            return 0.0
        px = _Counter(x for x, _ in pairs)
        py = _Counter(y for _, y in pairs)
        pxy = _Counter(pairs)
        m = 0.0
        for (x, y), c in pxy.items():
            j = c / n
            m += j * log2(j / ((px[x] / n) * (py[y] / n)))
        return max(0.0, m)


GRID = 8
N = GRID * GRID                  # 64 cells, 6-bit secret
SECRET_BITS = int(log2(N))       # 6


def _cell(i):
    return (i // GRID, i % GRID)


def _manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def candidates(secret_index, k_bits):
    """The cells still possible after disclosing the top `k_bits` of the secret's index (2^(6−k) candidates)."""
    shift = SECRET_BITS - k_bits
    prefix = secret_index >> shift
    return [i for i in range(N) if (i >> shift) == prefix]


def _centroid(idxs):
    xs = [_cell(i)[0] for i in idxs]
    ys = [_cell(i)[1] for i in idxs]
    return (round(sum(xs) / len(xs)), round(sum(ys) / len(ys)))


def utility(k_bits):
    """Exact-interception success: the agent aims at the candidate centroid and hits only when it is the cell.
    The task needs the secret — so utility rises only as the disclosure pins the cell."""
    hits = 0
    for s in range(N):
        guess = _centroid(candidates(s, k_bits))
        if guess == _cell(s):
            hits += 1
    return hits / N


def leakage(k_bits):
    """I(secret ; disclosure) in bits — measured by the QIF estimator; equals k by construction."""
    shift = SECRET_BITS - k_bits
    return mutual_information([(s, s >> shift) for s in range(N)])


def frontier():
    """The privacy–utility frontier: (leakage_bits, utility) for every disclosure resolution k = 0..6."""
    return [(round(leakage(k), 3), round(utility(k), 4)) for k in range(SECRET_BITS + 1)]


def marginal_value_of_a_bit():
    """The measurable cost/value of knowledge: how much utility each additional disclosed bit buys."""
    us = [utility(k) for k in range(SECRET_BITS + 1)]
    return [round(us[k + 1] - us[k], 4) for k in range(SECRET_BITS)]


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    fr = frontier()
    leak = [l for l, _ in fr]
    util = [u for _, u in fr]
    out = {"frontier": fr, "marginal_value_of_a_bit": marginal_value_of_a_bit()}
    # it IS a frontier: both axes strictly increase together — a genuine tradeoff curve, no dominating point
    out["leakage_monotone"] = all(leak[i + 1] > leak[i] for i in range(SECRET_BITS))
    out["utility_monotone"] = all(util[i + 1] > util[i] for i in range(SECRET_BITS))
    out["leakage_equals_bits"] = all(abs(leak[k] - k) < 1e-9 for k in range(SECRET_BITS + 1))
    # NON-separable: full utility strictly requires full leakage (the opposite of the session free lunch)
    out["full_utility"] = util[-1] == 1.0
    out["full_utility_requires_full_leakage"] = (util[-1] == 1.0 and leak[-1] == float(SECRET_BITS))
    out["no_high_utility_at_low_leakage"] = max(u for l, u in fr if l <= 1.0) < 0.10
    out["min_leakage_for_half_utility"] = min((l for l, u in fr if u >= 0.5), default=None)
    # coupling: every bit of utility is a bit of leakage (utility ≈ 2^(leakage−6))
    out["each_bit_buys_utility"] = all(m > 0 for m in out["marginal_value_of_a_bit"])
    out["utility_floor"] = util[0]               # ~0.02 — near-blind interception is near-hopeless
    # the contrast the benchmark exposes: separable case reached U=1.0 at L<1 bit; here U=1.0 needs L=6
    out["separable_was_a_special_case"] = out["full_utility_requires_full_leakage"]
    return out


def demo():
    r = crucible()
    print("Non-separable privacy–utility frontier — the measurable cost of knowledge\n")
    print("  task: EXACT interception (the agent must name the enemy's exact cell). Now the information the")
    print("  task needs IS the secret — no channel to drop, only a resolution to choose.\n")
    print("  leakage (bits)   utility (exact-hit)   value of this bit")
    mv = r["marginal_value_of_a_bit"]
    for k, (l, u) in enumerate(r["frontier"]):
        v = "" if k == 0 else "  %+.4f" % mv[k - 1]
        print("       %.0f             %.4f%s" % (l, u, v))
    print()
    print("  the curve doubles per bit (utility ≈ 2^(leakage−6)): leakage and utility are the SAME quantity.")
    print("  full utility (1.0) strictly requires full leakage (6 bits): %s — no free lunch."
          % r["full_utility_requires_full_leakage"])
    print("  (the separable session case reached U=1.0 at <1 bit — that was the special case, not the rule.)")
    print("\n  the framework's job here is not to ELIMINATE the tradeoff but to MEASURE it: whoever sets the")
    print("  leakage budget is choosing a utility, and the choice is now explicit and contestable. integrity ≠ truth.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.frontier", OBSERVER, mutates_core=False,
                          note="the non-separable privacy–utility frontier: an exact-interception task where "
                               "utility IS the secret; utility ≈ 2^(leakage−6), full utility requires full "
                               "leakage. the session win was a separable special case; here the framework "
                               "MEASURES the cost of knowledge rather than escaping it")
    except LayerViolation:
        pass
