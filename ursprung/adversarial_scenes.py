# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/adversarial_scenes.py — pathological scenes that attack the allocator's ADAPTATION, not its equation.

The project has proven it can find wrong equations. The harder question: *what happens when the equation is
correct, but the world changes faster than the allocator can adapt?* These generators (after `glitch`/
`crucible`: deterministic, seeded, designed to break a policy) build worst cases and probe two allocators:

    greedy  = ranked_waterfill recomputed every frame   (responsive, but thrashes)
    damped  = water-fill an EMA-smoothed weight          (steady, but lags)

  1. FLICKER TRAP        an object alternates important/irrelevant every frame.
                         Test: does the allocator THRASH? (transition debt)  → greedy bad, damped good.
  2. FALSE FUTURE        an object reports high priority but never realizes consequence.
                         Test: does it HOARD fidelity forever? (the WRONG failure) → priority hoards.
  3. DELAYED CONSEQUENCE  a low-priority object becomes critical N frames later.
                         Test: is budget THERE when it matters? → greedy adapts, damped LAGS.
  4. REPRESENTATION CLIFF a region whose error jumps at a threshold (LOD 3→2), not smoothly.
                         Test: does the scalar (perimeter) resistance DETECT the cliff? → it misses it.

The meta-finding the scenes are built to surface: damping fixes FLICKER but causes LAG on DELAYED
CONSEQUENCE — so no single damping constant wins everything. The right adaptation speed depends on the
world's rate of change (→ adaptive damping / multi-horizon, the open frontier). integrity ≠ truth.

CLASSIFICATION: OBSERVER (mutates_core=False). Deterministic, stdlib only.
"""
from __future__ import annotations

import math
import random

from . import allocation as al
from . import transition_debt as td
from .representation import representation_resistance
from .raster import aliasing_error


# --- the two allocators under test ------------------------------------------------------------------

def greedy(regions, budget):
    return al.two_stage_allocate(regions, budget, al._causal_priority)


class Damped:
    """Water-fill a slowly-moving EMA of the priority×resistance weight (steady, but lags)."""
    def __init__(self, num=1, den=4):
        self.ema = None; self.num = num; self.den = den

    def __call__(self, regions, budget):
        target = {rid: max(1, al._causal_priority(r) * representation_resistance(r)) for rid, r in regions.items()}
        if self.ema is None:
            self.ema = dict(target)
        else:
            self.ema = {rid: (self.ema.get(rid, 0) * (self.den - self.num) + target[rid] * self.num) // self.den
                        for rid in target}
        w = {rid: max(1, int(math.isqrt(max(1, self.ema[rid]))) * 100) for rid in self.ema}
        return al._hamilton(w, budget)


def _stable_base(n, seed):
    rng = random.Random(seed)
    return [{"id": "r%02d" % i, "sensitivity": rng.randint(1, 10), "size": rng.randint(2, 12),
             "persistence": rng.randint(1, 5), "uncertainty": rng.uniform(0.5, 2.0),
             "consequence": rng.randint(1, 4)} for i in range(n)]


# --- 1. FLICKER TRAP --------------------------------------------------------------------------------

def flicker_trap(frames=24, n=20, seed=1):
    base = _stable_base(n, seed)
    seq = []
    for t in range(frames):
        fr = {b["id"]: dict(b) for b in base}
        f = dict(base[0])                               # the flickering object
        f["uncertainty"], f["consequence"] = (4.0, 10) if t % 2 == 0 else (0.5, 1)
        fr[base[0]["id"]] = f
        seq.append(fr)
    return seq


def probe_thrash(seq, allocator, budget=400):
    """Transition debt incurred across the sequence (lower = steadier). Greedy thrashes the flicker object."""
    sens = {rid: r["sensitivity"] for rid, r in seq[0].items()}
    prev = None; debt = 0
    for regions in seq:
        a = allocator(regions, budget)
        if prev is not None:
            debt += td.transition_debt(prev, a, sens)
        prev = a
    return debt


# --- 2. FALSE FUTURE --------------------------------------------------------------------------------

def false_future(frames=16, n=20, seed=2):
    base = _stable_base(n, seed)
    seq = []
    for _ in range(frames):
        fr = {b["id"]: dict(b) for b in base}
        g = dict(base[0])
        g["uncertainty"], g["consequence"] = 4.0, 10     # always LOOKS important
        g["realized"] = 0                                # ...but never realizes any consequence
        fr[base[0]["id"]] = g
        for b in base[1:]:
            fr[b["id"]]["realized"] = fr[b["id"]]["consequence"]
        seq.append(fr)
    return seq


def probe_hoard(seq, budget=400):
    """% of budget the false-future object hoards under a priority allocator vs a realized-consequence one."""
    gid = sorted(seq[0])[0]
    def pct(weightfn):
        tot = 0
        for regions in seq:
            a = al._hamilton({rid: weightfn(r) for rid, r in regions.items()}, budget)
            tot += a.get(gid, 0)
        return tot * 100 // (budget * len(seq))
    priority = pct(lambda r: al._causal_priority(r))
    realized = pct(lambda r: max(1, int(round(r["uncertainty"] * 100)) * r.get("realized", r["consequence"]) * r["persistence"]))
    return {"priority_hoard_%": priority, "realized_hoard_%": realized}


# --- 3. DELAYED CONSEQUENCE -------------------------------------------------------------------------

def delayed_consequence(frames=24, delay=12, n=20, seed=3):
    base = _stable_base(n, seed)
    seq = []
    for t in range(frames):
        fr = {b["id"]: dict(b) for b in base}
        s = dict(base[0])
        s["uncertainty"], s["consequence"] = (4.0, 10) if t >= delay else (0.5, 1)   # critical only from `delay`
        fr[base[0]["id"]] = s
        seq.append(fr)
    return seq


def probe_lag(seq, allocator, delay, budget=400):
    """Budget the sleeper holds AT the critical frame as a fraction of what greedy would give it then.
    Greedy ≈ 1.0 (responsive); damped < 1 (it lags)."""
    sid = sorted(seq[0])[0]
    got_at_critical = None
    for t, regions in enumerate(seq):
        a = allocator(regions, budget)
        if t == delay:
            got_at_critical = a.get(sid, 0)
            ideal = greedy(regions, budget).get(sid, 0)
            break
    return (got_at_critical or 0), max(1, ideal)


# --- 4. REPRESENTATION CLIFF ------------------------------------------------------------------------

def representation_cliff(n=20, seed=4):
    rng = random.Random(seed)
    regions = {}
    for i in range(n):
        rid = "r%02d" % i
        regions[rid] = {"id": rid, "size": rng.randint(2, 12), "uncertainty": rng.uniform(0.5, 2.0),
                        "consequence": rng.randint(1, 5), "persistence": rng.randint(1, 5),
                        "cliff_k": 0}
    # the cliff region looks LOW priority (so priority/perimeter allocation starves it) yet has a hidden
    # threshold: catastrophic below 30 samples, fine above. Scalar resistance cannot see the step.
    regions["r00"].update({"uncertainty": 0.5, "consequence": 1, "persistence": 1, "cliff_k": 30})
    return regions


def _cliff_error(region, samples):
    if samples < region.get("cliff_k", 0):
        return 5_000_000                      # the cliff: catastrophic perceptual damage below the threshold
    return aliasing_error(region["size"], samples)


def probe_cliff(regions, budget=400):
    """Realized error under perimeter-resistance allocation vs a cliff-aware allocation. The scalar perimeter
    resistance is smooth → it MISSES the cliff and underfunds the cliff region."""
    def realized(alloc):
        return sum(_cliff_error(r, alloc.get(rid, 0) + 1) for rid, r in regions.items())
    perim = al.two_stage_allocate(regions, budget, al._causal_priority)   # resistance = perimeter (cliff-blind)
    # cliff-aware: RESERVE cliff_k samples for cliff regions (clears the threshold), water-fill the rest
    reserve = {rid: r["cliff_k"] for rid, r in regions.items() if r.get("cliff_k")}
    rest = al.two_stage_allocate(regions, max(0, budget - sum(reserve.values())), al._causal_priority)
    aware = {rid: rest.get(rid, 0) + reserve.get(rid, 0) for rid in regions}
    return {"perimeter_resistance_error": realized(perim), "cliff_aware_error": realized(aware)}


# --- report -----------------------------------------------------------------------------------------

def report(seed=1, budget=400):
    print("Adversarial scenes — attacking adaptation, not the equation\n")

    fseq = flicker_trap(seed=seed)
    g = probe_thrash(fseq, greedy, budget); d = probe_thrash(fseq, Damped(), budget)
    print("  1. FLICKER TRAP   transition debt: greedy %d vs damped %d  → greedy %s"
          % (g, d, "THRASHES" if g > d else "ok"))

    h = probe_hoard(false_future())
    print("  2. FALSE FUTURE   budget hoarded: priority %d%% vs realized %d%%  → priority %s"
          % (h["priority_hoard_%"], h["realized_hoard_%"], "HOARDS" if h["priority_hoard_%"] > h["realized_hoard_%"] else "ok"))

    dseq = delayed_consequence(delay=12, seed=seed)
    gg, gi = probe_lag(dseq, greedy, 12, budget)
    dg, di = probe_lag(delayed_consequence(delay=12, seed=seed), Damped(), 12, budget)
    print("  3. DELAYED CONSEQ at the critical frame: greedy %d/%d vs damped %d/%d  → damped %s"
          % (gg, gi, dg, di, "LAGS" if dg < gg else "keeps up"))

    c = probe_cliff(representation_cliff())
    print("  4. REPRESENTATION CLIFF  realized error: perimeter %d vs cliff-aware %d  → scalar resistance %s"
          % (c["perimeter_resistance_error"], c["cliff_aware_error"],
             "MISSES the cliff" if c["perimeter_resistance_error"] > c["cliff_aware_error"] else "ok"))

    print("\n  META-FINDING: damping fixes FLICKER (scene 1) but causes LAG on DELAYED CONSEQUENCE (scene 3) —")
    print("  no single damping constant wins all. The right adaptation speed depends on the world's rate of")
    print("  change → adaptive damping / multi-horizon is the open frontier. integrity ≠ truth.")
    return {"flicker": (g, d), "false_future": h, "delayed": (gg, dg), "cliff": c}


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("adversarial_scenes", OBSERVER, mutates_core=False,
                          note="pathological scenes (flicker / false-future / delayed / cliff) attacking "
                               "allocator adaptation; greedy thrashes vs damped lags — no universal damping")
    except LayerViolation:
        pass
