# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/stress.py — adversarial weakness extraction (stressors that try to BREAK the policies).

Ursprung's best discoveries came from failure, so the next gains come from adversarial testing, not more
laws. This harness ports the Reality_Engine workbench's weakness-extraction tools onto Ursprung's allocation
policies:

  · Goodhart mutation guard   (after `toolkit/mutate.py`) — degrade the allocator and confirm the metric
    NOTICES; `test_quality ≠ test_count`; honest about degradations it cannot see.
  · Failure-boundary adversaries (after `causal_runtime/adversary.py`) — find the exact condition where an
    allocator STOPS being valid: WRONG (raw consequence overspends on improbable futures → expected value),
    GAMEABLE (self-reported consequence is exploitable → independent evidence). Each implies a recorded repair.
  · (The LATE boundary and shrink-to-minimal-counterexample patterns from `adversary.py`/`glitch` apply too;
    the perceptual mismatch is exercised in `policy_arena.py`.)

Each adversary shows a naive allocator LOSING and records the repair as a boundary, not a hidden caveat.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures where policies break; it changes nothing and
asserts no truth. `observation → allocation`, never `→ truth`. integrity ≠ truth.
"""
from __future__ import annotations

import math
import random

from .raster import aliasing_error
from . import allocation as al


# --- Goodhart mutation guard (can the metric notice a degraded allocator?) --------------------------

def _scene(n=40, seed=1):
    return al._scene(n=n, seed=seed)


def _residual(regions, alloc):
    return sum(al._causal_priority(r) * aliasing_error(r["size"], alloc.get(rid, 0) + 1)
              for rid, r in regions.items())


def mutation_guard(seed=1, budget=400):
    """Degrade the two-stage allocator; the future-causal residual metric must WORSEN (detected). Returns
    [(mutant, detected, why)]. An undetected mutant means the metric is blind there — recorded honestly."""
    regions = _scene(seed=seed)
    base = _residual(regions, al.two_stage_allocate(regions, budget, al._causal_priority))

    def m_constant(regions, b):    return al._hamilton({rid: 1 for rid in regions}, b)
    def m_invert(regions, b):      return al._hamilton(
        {rid: max(1, 10_000 - al._causal_priority(r)) for rid, r in regions.items()}, b)
    def m_drop_resistance(regions, b):  # rank-only, no water-filling under resistance (the proportional defect)
        return al._hamilton(al.rank(regions, al._causal_priority), b)
    def m_random(regions, b):      return al._hamilton(
        {rid: random.Random(seed * 7 + i).randint(1, 1000) for i, rid in enumerate(regions)}, b)

    out = []
    for name, fn in (("constant", m_constant), ("invert_priority", m_invert),
                     ("drop_resistance(→proportional)", m_drop_resistance), ("random", m_random)):
        r = _residual(regions, fn(regions, budget))
        detected = r > base
        out.append((name, detected, "residual %d vs base %d (%s)"
                    % (r, base, "worse → noticed" if detected else "NOT worse → blind")))
    return out


# --- WRONG: raw consequence overspends on improbable futures (expected value repairs) ---------------

def adversary_wrong(seed=2, budget=400, n=50):
    rng = random.Random(seed)
    regions = {}
    for i in range(n):
        improbable = (i % 4 == 0)
        regions["r%02d" % i] = {
            "consequence": rng.randint(800, 1000) if improbable else rng.randint(1, 200),
            "probability": (rng.randint(1, 5) if improbable else rng.randint(60, 100)),  # %; improbable = rare
            "size": rng.randint(2, 12), "uncertainty": 1.0, "persistence": 1,
        }
    def realized(alloc):  # realized residual weights error by consequence × probability (expected impact)
        return sum(r["consequence"] * r["probability"] * aliasing_error(r["size"], alloc.get(rid, 0) + 1)
                   for rid, r in regions.items())
    raw = realized(al._hamilton({rid: r["consequence"] for rid, r in regions.items()}, budget))
    ev = realized(al._hamilton({rid: r["consequence"] * r["probability"] for rid, r in regions.items()}, budget))
    return {"raw_consequence": raw, "expected_value (C×prob)": ev, "broke": raw > ev,
            "repair": "weight by expected value consequence×probability (possibility ≠ likelihood)"}


# --- GAMEABLE: self-reported consequence is exploitable (independent evidence repairs) ---------------

def adversary_gameable(seed=3, budget=400, n=40):
    rng = random.Random(seed)
    regions = {}
    gamer = "r00"
    for i in range(n):
        rid = "r%02d" % i
        true_impact = rng.randint(1, 100)
        regions[rid] = {"true_impact": true_impact,
                        # the gamer inflates its SELF-REPORTED consequence to attract budget:
                        "self_consequence": (5000 if rid == gamer else true_impact),
                        "evidence": rng.randint(50, 100) if rid != gamer else 5,   # independent corroboration
                        "size": rng.randint(2, 12)}
    def captured_by_gamer(alloc):
        return alloc.get(gamer, 0) * 100 // max(1, budget)   # % of budget the gamer captured
    naive = captured_by_gamer(al._hamilton({rid: r["self_consequence"] for rid, r in regions.items()}, budget))
    hardened = captured_by_gamer(al._hamilton(
        {rid: r["true_impact"] * r["evidence"] for rid, r in regions.items()}, budget))
    return {"naive_self_report_%budget_to_gamer": naive, "evidence_weighted_%budget_to_gamer": hardened,
            "broke": naive > hardened,
            "repair": "weight by impact × independent_evidence (proposal ≠ authority, for allocation)"}


def report(seed=1):
    print("Ursprung stressors — extracting weaknesses (after workbench mutate / adversary)\n")
    print("  Goodhart mutation guard (metric must notice a degraded allocator):")
    blind = 0
    for name, detected, why in mutation_guard(seed=seed):
        print("    [%s] %-28s %s" % ("noticed" if detected else "BLIND", name, why))
        blind += 0 if detected else 1
    print("    → %d undetected (recorded honestly; a no-information signal cannot be broken)\n" % blind)

    w = adversary_wrong()
    print("  WRONG (improbable futures): raw_consequence %d vs expected_value %d → naive %s"
          % (w["raw_consequence"], w["expected_value (C×prob)"], "BROKE" if w["broke"] else "held"))
    print("    repair: %s" % w["repair"])

    g = adversary_gameable()
    print("  GAMEABLE: gamer captured %d%% of budget (self-report) vs %d%% (evidence-weighted) → naive %s"
          % (g["naive_self_report_%budget_to_gamer"], g["evidence_weighted_%budget_to_gamer"],
             "BROKE" if g["broke"] else "held"))
    print("    repair: %s" % g["repair"])
    print("\n  Each weakness is recorded as a BOUNDARY with its repair, not hidden. integrity ≠ truth.")
    return {"wrong": w, "gameable": g}


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("stress", OBSERVER, mutates_core=False,
                          note="adversarial weakness extraction (Goodhart mutation guard + WRONG/GAMEABLE "
                               "boundaries, after workbench mutate/adversary); records repairs as boundaries")
    except LayerViolation:
        pass
