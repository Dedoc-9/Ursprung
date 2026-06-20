# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/response.py — the action channel: reaction itself is a leakage channel.

Every layer before this controlled what was *shown* and what could be *inferred from it* — the channel
`I(S;O)`. But there is a second channel the whole arc had left untouched: **the actor's own behavior.** An
observer does not only watch what you reveal; it watches what you *do* — what you defend, what you avoid, what
you prioritize, how fast you respond. A perfect disclosure policy (`I(S;O) ≈ 0`) still fails if the action
re-leaks the secret:

    I(S ; A) > 0          (the action is the message)

So this module makes **non-action a first-class output** and introduces a **response gate**. The naive model
`world → observation → decision → action` assumes the goal is to optimize the action. The mature model is
`world → observation → decision → action OR non-action`, and the rule is not *never react* (that decays into
avoidance, paralysis, failure to protect) but:

    act iff  ΔU_action ≥ C_information + C_signaling

— react only when the value of intervention exceeds its information/signaling cost, where the *signaling cost
is the action-leakage itself*. Three policies on a defend/no-op task (the secret is the enemy's zone; defending
the zone you should is the utility; an observer watches whether and which zone you defend):

  * **reactive** (gate 0, always act) — utility 1.0, but the action reveals the secret: `I(S;A) = H(S)`.
  * **silent** (gate ∞, never act) — `I(S;A) = 0`, but utility collapses.
  * **gated** — act only where `ΔU ≥ cost`; defends the high-value zone, abstains on the rest. Action-leakage
    *collapses* while the utility that matters is preserved — a **response frontier** parameterized by the gate.

And a no-op is **attributable**: the gate records whether an abstention was *optimal* (it computed `ΔU < cost`
and chose) or *ignorance* (it could not compute `ΔU`). That distinction — proving a non-action was a decision,
not a blind spot — is the action-channel parallel to `MeasurementResult` refusing the word "safe."

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: a toy (4 zones, declared values); action-utility
and action-leakage are *coupled* here (reducing the leak costs utility — a real tradeoff, like the non-separable
frontier, not a free lunch); the real version needs real agents and real objectives. `I(S;A)` matters as much
as `I(S;O)`; non-action ≠ ignorance; simulation ≠ physics.
"""
from __future__ import annotations

try:
    from ..channel_discovery import mutual_information
except Exception:                                            # pragma: no cover - standalone fallback
    from collections import Counter as _Counter
    from math import log2 as _log2

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
            m += j * _log2(j / ((px[x] / n) * (py[y] / n)))
        return max(0.0, m)


ZONES = (0, 1, 2, 3)                       # the secret is which zone the enemy is in (uniform → 2 bits)
VALUE = {0: 3, 1: 2, 2: 1, 3: 0}           # ΔU of defending each zone when the enemy is there
REACTIVE, SILENT = 0.0, 99.0               # gate thresholds for the always-act / never-act extremes


def observable_action(secret_zone, gate):
    """What an observer SEES the actor do. The gate combines information + signaling cost: the actor defends a
    zone only when its value clears the gate; otherwise it abstains (a first-class no-op)."""
    if VALUE[secret_zone] >= gate:
        return ("defend", secret_zone)
    return ("noop", None)


def action_leakage(gate):
    """I(S ; A): how much the secret leaks through the ACTION, over the zone distribution."""
    return mutual_information([(s, observable_action(s, gate)) for s in ZONES])


def task_utility(gate):
    """Normalized defended value: the share of the at-stake value the actor actually protects."""
    defended = sum(VALUE[s] for s in ZONES if VALUE[s] >= gate)
    total = sum(VALUE[s] for s in ZONES)
    return defended / total


def response_frontier(gates=(REACTIVE, 1.5, 2.5, SILENT)):
    """(gate, utility, action-leakage) — the action-channel tradeoff, parameterized by the response gate."""
    return [(g, round(task_utility(g), 3), round(action_leakage(g), 3)) for g in gates]


def abstention_reason(secret_zone, gate, knows=True):
    """Why the actor did (not) act — the accountability of a null action. An abstention is either *optimal*
    (ΔU computed, below the gate) or *ignorance* (ΔU not knowable). Proving the former is 'non-action ≠ blind spot'."""
    if not knows:
        return "ignorance"
    if VALUE[secret_zone] >= gate:
        return "acted"
    return "optimal_abstention"            # it knew ΔU and chose not to act


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    fr = response_frontier()
    out = {"frontier": fr}
    lk = {g: l for g, _, l in fr}
    ut = {g: u for g, u, _ in fr}
    # reaction is a channel: the reactive actor leaks the WHOLE secret through its action alone
    out["reactive_action_leak"] = lk[REACTIVE]
    out["reaction_is_a_channel"] = lk[REACTIVE] > 0
    out["reactive_leaks_full_secret"] = abs(lk[REACTIVE] - 2.0) < 1e-9     # H(S) = 2 bits, 4 zones
    out["reactive_utility"] = ut[REACTIVE]
    # the gate collapses action-leakage while preserving the high-value defense
    out["gated_action_leak"] = lk[2.5]
    out["gate_reduces_leakage"] = lk[2.5] < lk[REACTIVE]
    out["gate_preserves_high_value"] = task_utility(2.5) > 0              # zone 0 still defended
    # non-action is a coherent, first-class output
    out["silent_zero_leak"] = lk[SILENT] == 0.0
    out["silent_zero_utility"] = ut[SILENT] == 0.0
    # the response frontier is a coupled tradeoff (reducing the leak costs utility — not a free lunch)
    gs = [g for g, _, _ in fr]
    out["frontier_monotone"] = all(ut[gs[i + 1]] <= ut[gs[i]] and lk[gs[i + 1]] <= lk[gs[i]]
                                   for i in range(len(gs) - 1))
    out["coupled_tradeoff"] = not (ut[2.5] >= ut[REACTIVE] and lk[2.5] < lk[REACTIVE])  # can't keep full util at lower leak
    # a no-op is attributable: optimal abstention vs ignorance are distinguishable
    out["abstention_optimal"] = abstention_reason(2, 2.5, knows=True) == "optimal_abstention"
    out["abstention_ignorance"] = abstention_reason(2, 2.5, knows=False) == "ignorance"
    out["non_action_not_ignorance"] = out["abstention_optimal"] and out["abstention_ignorance"]
    return out


def demo():
    r = crucible()
    print("The action channel — reaction is a leakage channel; non-action is a first-class output\n")
    print("  task: defend the enemy's zone (value-weighted); an observer watches whether/which zone you defend.")
    print("  rule: act iff ΔU_action ≥ cost (info + signaling); the signaling cost IS the action-leakage.\n")
    print("  %-10s %-9s %s" % ("gate", "utility", "action-leak I(S;A) bits"))
    for g, u, l in r["frontier"]:
        name = "reactive" if g == REACTIVE else ("silent" if g == SILENT else "gated@%.1f" % g)
        print("  %-10s %-9.3f %.3f" % (name, u, l))
    print()
    print("  · a perfectly-sealed disclosure still leaks via the ACTION: reactive I(S;A)=%.1f bits = the whole secret."
          % r["reactive_action_leak"])
    print("  · the gate collapses action-leakage (%.2f vs %.1f) while keeping the high-value defense: %s"
          % (r["gated_action_leak"], r["reactive_action_leak"], r["gate_preserves_high_value"]))
    print("  · non-action is first-class (silent: utility %.0f, leak %.0f) — and ATTRIBUTABLE: a gated no-op is"
          % (0, 0))
    print("    'optimal_abstention' (it knew ΔU and chose), distinguishable from 'ignorance': %s"
          % r["non_action_not_ignorance"])
    print("\n  the mature state is not maximum reaction but MINIMUM NECESSARY reaction. I(S;A) matters as much")
    print("  as I(S;O); non-action ≠ ignorance; the tradeoff is real (coupled), not a free lunch. integrity ≠ truth.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.response", OBSERVER, mutates_core=False,
                          note="the action channel: reaction is a leakage channel (I(S;A)); a response gate "
                               "(act iff ΔU ≥ info+signaling cost) collapses action-leakage while preserving the "
                               "high-value action; non-action is first-class and ATTRIBUTABLE (optimal "
                               "abstention vs ignorance). minimum necessary reaction; I(S;A) ~ I(S;O)")
    except LayerViolation:
        pass
