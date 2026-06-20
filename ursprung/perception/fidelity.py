# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/fidelity.py — the Perception Fidelity Condition (a Dini-style test for the whole stack).

The Dini condition gives a *sufficient* condition under which a Fourier representation faithfully reconstructs
a signal at a point. This module is its analogue for interactive systems: a *sufficient* condition under which
a compiled observation is **task-faithful** (the observer can still act) while being **inference-bounded** (the
protected secret stays unrecoverable). It unifies the three pillars the perception work surfaced —

  * the **frontier** — how much can be removed?            (participation)
  * the **threshold** — when does reconstruction succeed?  (reconstruction boundary)
  * **inverse leakage** — what uncertainty survived?       (residual `H(S|O)`)

— into one PASS/FAIL over everything already built. A transform `T : W → O` (world → observation) satisfies the
**Perception Fidelity Condition** for a task and an observer class C iff:

    (1) participation convergence:   utility(O) ≥ U_min          (the belief converges to the task-relevant truth)
    (2) reconstruction boundary:     recovery_C(O) < τ           (it does NOT converge to the protected secret)

Crucially, by the adversary/session result, clause (2) is a **session / accumulated** quantity — `I(S ; O₁..O_T)`,
not `I(S ; O_t)`. This is the information-cascade lesson (Bikhchandani–Hirshleifer–Welch): a sequence of weak
signals can collapse an observer's belief even when each frame looked safe. So the condition tests recovery
*over the horizon*, which is why a per-frame check (a single Fourier coefficient) is not enough.

The goal is therefore not to stop convergence but to **direct** it: the observer's belief should converge on
the truths required for participation and provably not on the protected state.

A note on the two Dini objects. Dini's *test* (above) is the Fourier-convergence criterion; the related Dini
*derivatives* — the four one-sided upper/lower derivates `D⁺, D₊, D⁻, D₋` — are the sharper tool for clause
(2), because the reconstruction bound is really an **upper Dini derivate of accumulated recovery**: the
*worst-case rate* at which a session of observations collapses the observer's uncertainty (the cascade slope),
not an average. A scalar leakage "derivative" often does not exist or misleads (the per-frame MI did); the
extreme one-sided derivates are what bound the danger. And the **Denjoy–Young–Saks theorem** (Denjoy 1915 for
continuous functions, Young 1917 for measurable, **Saks 1924 for *arbitrary* functions**) — that the four Dini
derivates fall, almost everywhere, into exactly four cases (a finite derivative, or one of three extreme
patterns where some derivates are ±∞) — is the analogue of the empirical finding that `(task, policy,
observer-class)` triples land in a few recovery regimes: *faithful-and-bounded* (separable), an *irreducible
tradeoff* (non-separable), or *cascade-collapse*. The deepest fit is Saks's step to **arbitrary** functions:
this stack likewise refuses to assume the observer is well-behaved, which is exactly why the *upper* derivate
(worst case), not an average, is the right bound. A "Denjoy–Young–Saks for perception" — classifying which
regime holds almost everywhere — is the honest, theorem-shaped target this condition gestures at, and it is
**not** proved here.

Applied to the two cases already in the repo:
  * the **separable** session task → the condition HOLDS (utility 1.0, session recovery 0.83 < τ; ~5 bits of
    residual uncertainty preserved). The free lunch was a *feasible* fidelity condition.
  * the **non-separable** interception task → the condition is **INFEASIBLE** at meaningful bounds: the only
    disclosure level that meets U_min busts τ, so faithfulness and boundedness become mutually exclusive. The
    irreducible tradeoff, expressed as the condition *failing* — which is itself the useful answer.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: like Dini, this is **sufficient, not necessary**,
and it holds only under the *modeled* observer class C and the *declared* utility model — a richer class or a
different task moves feasibility (`secure-against-class ≠ secure`). It does not prove safety; it reports whether
*this* representation is, under *these* assumptions, both faithful enough for its purpose and unfaithful enough
to its secret. Constructed world; `simulation ≠ physics`.
"""
from __future__ import annotations

from . import session_accounting as _sess
from . import frontier as _fr

SECRET_BITS = 6.0


def residual_uncertainty(recovery_bits):
    """Inverse leakage: the bits of the secret that remain unrecoverable — `H(S|O)`."""
    return SECRET_BITS - recovery_bits


class FidelityResult:
    __slots__ = ("task", "observer_class", "participation", "recovery", "residual",
                 "u_min", "tau", "faithful", "bounded", "holds", "coverage_boundary")

    def __init__(self, task, observer_class, participation, recovery, u_min, tau):
        self.task = task
        self.observer_class = observer_class
        self.participation = round(participation, 4)
        self.recovery = round(recovery, 4)              # session / accumulated recovery (cascade-aware)
        self.residual = round(residual_uncertainty(recovery), 4)
        self.u_min = u_min
        self.tau = tau
        self.faithful = participation >= u_min          # (1) participation convergence
        self.bounded = recovery < tau                   # (2) reconstruction boundary
        self.holds = self.faithful and self.bounded     # the Perception Fidelity Condition
        self.coverage_boundary = ("sufficient, not necessary; under the MODELED observer class and the declared "
                                  "utility model; recovery is the SESSION (accumulated) quantity — secure-against-"
                                  "class ≠ secure")

    def __repr__(self):
        return "<FidelityResult %s faithful=%s bounded=%s HOLDS=%s (U=%.2f≥%.2f, recov=%.2f<%.2f)>" % (
            self.task, self.faithful, self.bounded, self.holds,
            self.participation, self.u_min, self.recovery, self.tau)


# --- the separable case (the session task) — the condition is FEASIBLE -------------------------------

def evaluate_separable(u_min=0.9, tau=2.0, observer_class="accumulating"):
    """The accumulation-aware session policy: utility 1.0, session recovery ~0.83 bits → faithful AND bounded."""
    res = _sess.evaluate("accumulation_aware")
    return FidelityResult("separable/session", observer_class, res.utility, res.exploitability, u_min, tau)


# --- the non-separable case (the interception task) — is the condition FEASIBLE at all? --------------

def evaluate_nonseparable_at(k_bits, u_min=0.9, tau=3.0, observer_class="accumulating"):
    return FidelityResult("nonseparable/interception@%d" % k_bits, observer_class,
                          _fr.utility(k_bits), _fr.leakage(k_bits), u_min, tau)


def feasible_nonseparable(u_min=0.9, tau=3.0):
    """Does ANY disclosure resolution satisfy both clauses for the non-separable task? (The frontier crossing
    the (U_min, τ) box.) If not, the representation cannot be both task-faithful and inference-bounded here."""
    levels = [evaluate_nonseparable_at(k, u_min, tau) for k in range(int(SECRET_BITS) + 1)]
    satisfying = [r for r in levels if r.holds]
    meet_umin = [r for r in levels if r.faithful]
    return {"feasible": bool(satisfying),
            "satisfying_levels": [r.task for r in satisfying],
            "levels_meeting_u_min": [(r.task, r.recovery) for r in meet_umin]}


# --- the crucible: the condition distinguishes the feasible case from the irreducible one ------------

def crucible():
    out = {}
    sep = evaluate_separable(u_min=0.9, tau=2.0)
    out["separable_faithful"] = sep.faithful
    out["separable_bounded"] = sep.bounded
    out["separable_holds"] = sep.holds                       # the free lunch = a feasible fidelity condition
    out["separable_residual"] = sep.residual                  # ~5 bits of uncertainty preserved
    out["separable_preserves_uncertainty"] = sep.residual > 4.0

    nf = feasible_nonseparable(u_min=0.9, tau=3.0)
    out["nonseparable_feasible"] = nf["feasible"]             # expected: False
    out["nonseparable_levels_meeting_u_min"] = nf["levels_meeting_u_min"]
    # the only level meeting U_min busts τ → faithful XOR bounded, never both
    out["nonseparable_umin_only_at_full_leakage"] = (len(nf["levels_meeting_u_min"]) > 0
                                                     and all(rec >= 3.0 for _, rec in nf["levels_meeting_u_min"]))
    full = evaluate_nonseparable_at(6, u_min=0.9, tau=3.0)
    out["nonseparable_full_utility_zero_residual"] = full.residual == 0.0

    # the condition does its job: HOLDS for the separable task, INFEASIBLE for the non-separable one
    out["condition_distinguishes"] = sep.holds and not nf["feasible"]
    return out


def demo():
    r = crucible()
    print("Perception Fidelity Condition — task-faithful AND inference-bounded (a Dini-style sufficient test)\n")
    print("  (1) participation convergence: utility ≥ U_min   (belief converges to the task-relevant truth)")
    print("  (2) reconstruction boundary:   recovery < τ       (belief does NOT converge to the secret)")
    print("  recovery is the SESSION (accumulated) quantity — the information-cascade lesson.\n")
    sep = evaluate_separable(0.9, 2.0)
    print("  separable / session task:      %r" % sep)
    print("     → HOLDS: faithful and bounded; %.2f bits of the secret stay hidden (inverse leakage preserved)."
          % sep.residual)
    print("  non-separable / interception:  feasible at meaningful bounds (U_min=0.9, τ=3)? %s"
          % r["nonseparable_feasible"])
    print("     → the only level that meets U_min is full disclosure, which busts τ — faithfulness and")
    print("       boundedness are mutually exclusive. The irreducible tradeoff, as the condition FAILING.")
    print("\n  goal: not to stop convergence but to DIRECT it. sufficient, not necessary; under the modeled")
    print("  observer class. integrity ≠ truth; secure-against-class ≠ secure.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.fidelity", OBSERVER, mutates_core=False,
                          note="Perception Fidelity Condition (Dini-style, sufficient): task-faithful "
                               "(utility ≥ U_min) AND inference-bounded (session recovery < τ). HOLDS for the "
                               "separable task; INFEASIBLE for the non-separable one — unifies frontier + "
                               "threshold + inverse-leakage; cascade-aware (recovery is the session quantity)")
    except LayerViolation:
        pass
