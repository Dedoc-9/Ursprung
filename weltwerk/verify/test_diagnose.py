# SPDX-License-Identifier: AGPL-3.0-only
"""
test_diagnose.py — validity-not-outcome proofs for the model-based diagnosis layer.

These assert the inference machinery is sound, not that any world is "good":
  1. recovers_planted_single_fault — destroy reactor, observe, diagnose ⇒ top hypothesis = {reactor}
  2. minimal_preferred             — a single-fault explanation is returned, not a pair, when one suffices
  3. ambiguous_returns_multiple    — symmetric causes + partial observation ⇒ ≥2 tied rivals, underdetermined
  4. suggested_observation         — the ambiguous case proposes a real discriminating observation
  5. confidence_normalized         — returned ranking weights sum to ~1.0 (allocation weights, not P)
  6. determinism                   — two diagnoses agree on faults order and weights
  7. consumes_ghost                — a kernel_check ghost is diagnosed back to the entity it destroyed
  8. no_explanation_honest         — an observation outside the fault model yields NO hypothesis (not a guess)

Run:  python3 test_diagnose.py
"""
from __future__ import annotations

from diagnose import diagnose, from_ghost, observe_after
from kernel_check import check
from world_sim import DEMO_WORLD

AMB = """
world "Amb"
entity gen_a:
  position 0 0 0
  powers bus
entity gen_b:
  position 1 0 0
  powers bus
entity bus:
  position 2 0 0
  health 10
  powers light
entity light:
  position 3 0 0
  health 10
"""

ISO = """
world "Iso"
entity lonely:
  position 0 0 0
  health 10
"""

NEVER_DESTROYED = {"nothing_ever_destroyed":
                   lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime)}


def chk(name, ok, detail):
    return (name, ok, detail)


def test_recovers_planted_single_fault():
    obs = observe_after(DEMO_WORLD, [("destroy", "reactor")])
    rep = diagnose(DEMO_WORLD, obs, trace=[("destroy", "reactor")])
    ok = rep.best is not None and rep.best.faults == ("reactor",)
    return chk("recovers_planted_single_fault", ok,
               f"top = {rep.best.faults if rep.best else None} @ {rep.best.confidence if rep.best else 0}")


def test_minimal_preferred():
    obs = observe_after(DEMO_WORLD, [("destroy", "reactor")])
    rep = diagnose(DEMO_WORLD, obs)
    ok = rep.best is not None and len(rep.best.faults) == 1
    return chk("minimal_preferred", ok, f"best fault-set size = {len(rep.best.faults) if rep.best else None}")


def test_ambiguous_returns_multiple():
    obs = {"bus": (True, "disabled"), "light": (True, "disabled")}
    rep = diagnose(AMB, obs)
    tops = [d.faults for d in rep.diagnoses]
    ok = (rep.underdetermined and len(rep.diagnoses) >= 2
          and abs(rep.diagnoses[0].confidence - rep.diagnoses[1].confidence) < 1e-9)
    return chk("ambiguous_returns_multiple", ok, f"underdetermined={rep.underdetermined}; rivals={tops}")


def test_suggested_observation():
    obs = {"bus": (True, "disabled"), "light": (True, "disabled")}
    rep = diagnose(AMB, obs)
    s = rep.best.suggested_observation if rep.best else None
    ok = bool(s) and ("gen_a" in s or "gen_b" in s)
    return chk("suggested_observation", ok, f"suggests: {s}")


def test_confidence_normalized():
    obs = {"bus": (True, "disabled"), "light": (True, "disabled")}
    rep = diagnose(AMB, obs)
    total = sum(d.confidence for d in rep.diagnoses)
    ok = abs(total - 1.0) < 1e-6
    return chk("confidence_normalized", ok, f"sum(weights) = {round(total, 6)}")


def test_determinism():
    obs = observe_after(DEMO_WORLD, [("destroy", "reactor")])
    a = diagnose(DEMO_WORLD, obs)
    b = diagnose(DEMO_WORLD, obs)
    ok = ([(d.faults, d.confidence) for d in a.diagnoses]
          == [(d.faults, d.confidence) for d in b.diagnoses])
    return chk("determinism", ok, f"identical ranked output: {ok}")


def test_consumes_ghost():
    res = check(DEMO_WORLD, max_depth=2, invariants=NEVER_DESTROYED)
    g = res.ghost
    destroyed = g.path[0][1]
    rep = from_ghost(DEMO_WORLD, g)
    ok = rep.best is not None and rep.best.faults == (destroyed,)
    return chk("consumes_ghost", ok, f"ghost destroyed {destroyed!r}; diagnosed {rep.best.faults if rep.best else None}")


def test_no_explanation_honest():
    # an isolated node cannot be 'disabled' under entity-loss (no upstream; destroying it ⇒ 'destroyed')
    rep = diagnose(ISO, {"lonely": (True, "disabled")})
    ok = rep.diagnoses == [] and not rep.underdetermined
    return chk("no_explanation_honest", ok, f"diagnoses={rep.diagnoses} (not-explained ≠ no-cause)")


def main():
    results = [
        test_recovers_planted_single_fault(),
        test_minimal_preferred(),
        test_ambiguous_returns_multiple(),
        test_suggested_observation(),
        test_confidence_normalized(),
        test_determinism(),
        test_consumes_ghost(),
        test_no_explanation_honest(),
    ]
    print("test_diagnose — model-based diagnosis over the causal kernel (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a planted fault is recovered as the "
          f"minimal\n  explanation, symmetric causes under partial observation stay UNDERDETERMINED with a "
          f"proposed\n  discriminating observation, weights are normalized allocation (not probability), and an\n"
          f"  observation outside the fault model yields no hypothesis. consistency ≠ causation.")
    assert passed == total, f"{total - passed} check(s) failed — the diagnosis layer is not sound"


if __name__ == "__main__":
    main()
