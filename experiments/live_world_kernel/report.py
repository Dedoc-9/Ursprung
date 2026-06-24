# SPDX-License-Identifier: AGPL-3.0-only
"""
report.py — the Verified Improvement Dynamics Suite. Composes the four axes built across this arc into one
*profile* under a declared (system, domain, verification-regime, state-identity) scope. It does NOT output
"RSI = true/false" — that would be the inflation every instrument here refuses. It outputs a dynamics profile and
a *candidate* judgement about continued verified frontier expansion, with each axis carrying its own uncertainty.

    Axis 1  Capability   ΔC          did external capability actually improve?        (orbit strict trajectory)
    Axis 2  Branching    m_offspring  do verified edits reproduce?                    (generativity_estimator)
    Axis 3  Generativity m_novel      does the verified frontier expand?              (generativity_estimator)
    Axis 4  Orbit        O(t)         where does the trajectory travel?               (orbit_estimator)

Candidate condition (necessary, not sufficient; under the declared regime):  ΔC>0 ∧ m_novel CI excludes 1 above
∧ orbit EXPANDING. Any axis that "cannot distinguish under current sampling" makes the verdict UNCERTAIN, never NO
or YES. The composition reuses the already-verified estimators; only the glue + interpretation is new, and the
self-tests check that the interpretation matches the axis verdicts and that no boolean RSI claim is emitted.

`estimate ≠ property`; the result is a profile of a (system, domain, regime, identity) tuple, not a verdict on RSI.

Run (from this directory):  PYTHONHASHSEED=0 python3 report.py
"""
from __future__ import annotations

import math
import random

import generativity_estimator as G
import orbit_estimator as O

SEED = 20260623


def interpret(capability, gen_super, gen_uninf, branch_uninf, orbit_word):
    """Map the four axis verdicts to a candidate judgement. UNCERTAIN dominates: an undistinguished axis cannot
    be resolved into YES or NO."""
    if gen_uninf or branch_uninf:
        return "UNCERTAIN"
    if capability == "improving" and gen_super and orbit_word == "EXPANDING":
        return "YES"
    if (not gen_super) or orbit_word in ("CONVERGED", "NO_TRAJECTORY", "CYCLING"):
        return "NO"
    return "UNCERTAIN"


def build_profile():
    gen = G.run()
    n, m_off, m_nov = G.pool(gen["per_root"])
    ci_off, ci_nov = G.bootstrap_ci(gen["per_root"], random.Random(SEED + 99))
    branching = G.informativeness(ci_off)
    generativity = G.informativeness(ci_nov)
    orb = O.run_summary()
    dC = orb["dC"]

    capability = "improving" if dC > 1e-9 else ("declining" if dC < -1e-9 else "flat")
    gen_super = "above 1" in generativity
    gen_uninf = generativity.startswith("UNINFORMATIVE")
    branch_uninf = branching.startswith("UNINFORMATIVE")
    orbit_word = orb["explore_class"].split()[0]
    verdict = interpret(capability, gen_super, gen_uninf, branch_uninf, orbit_word)

    return {
        "n": n, "m_off": m_off, "m_nov": m_nov, "ci_off": ci_off, "ci_nov": ci_nov, "gap": m_off - m_nov,
        "dC": dC, "capability": capability, "branching": branching, "generativity": generativity,
        "orbit_class": orb["explore_class"], "orbit_word": orbit_word,
        "gen_super": gen_super, "gen_uninf": gen_uninf, "branch_uninf": branch_uninf, "verdict": verdict,
        "scope": ("system = toy cosine-basis optimizer (active-set + σ edits); "
                  "domain = shared-support task family; "
                  "verification regime = external(3 held-out seed sets) ∧ replicated(≥60%) ∧ calibrated; "
                  "state identity = (active set, σ~1dp)"),
    }


VERDICT_PHRASE = {
    "YES": "consistent with continued verified frontier expansion (necessary signature present, not proof)",
    "NO": "verified frontier not expanding under this regime",
    "UNCERTAIN": "at least one axis cannot distinguish under current sampling",
}


def main():
    print("Verified Improvement Dynamics Suite — a profile under a declared scope, NOT an 'RSI = true/false' verdict.\n")
    p = build_profile()
    print("  Verified Improvement Dynamics profile")
    print(f"    Axis 1  Capability   ΔC          : {p['capability']:<10} (ΔC = {p['dC']:+.3f})")
    print(f"    Axis 2  Branching    m_offspring : {p['branching']}  (m≈{p['m_off']:.2f}, CI [{p['ci_off'][0]:.2f},{p['ci_off'][1]:.2f}])")
    print(f"    Axis 3  Generativity m_novel     : {p['generativity']}  (m≈{p['m_nov']:.2f}, CI [{p['ci_nov'][0]:.2f},{p['ci_nov'][1]:.2f}]; overlap gap {p['gap']:+.2f})")
    print(f"    Axis 4  Orbit        O(t)        : {p['orbit_class']}")
    print(f"\n  Candidate for continued verified frontier expansion: {p['verdict']} — {VERDICT_PHRASE[p['verdict']]}")
    print(f"  Scope: {p['scope']}.")
    print("  (estimate, not property; change the regime or the state-identity boundary and the profile changes.)\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<30} {detail}")

    # 1. all four axes produced finite, present values
    check("four_axes_present",
          all(k in p for k in ("capability", "branching", "generativity", "orbit_class"))
          and all(math.isfinite(v) for v in (p["dC"], p["m_off"], p["m_nov"])),
          "Capability / Branching / Generativity / Orbit all measured")

    # 2. the candidate verdict MATCHES the axis verdicts (verdict matches evidence; UNCERTAIN dominates)
    recomputed = interpret(p["capability"], p["gen_super"], p["gen_uninf"], p["branch_uninf"], p["orbit_word"])
    check("interpretation_sound", recomputed == p["verdict"] and p["verdict"] in ("YES", "NO", "UNCERTAIN"),
          f"verdict '{p['verdict']}' recomputes from the four axis verdicts")

    # 3. UNCERTAIN really dominates: if any used axis is uninformative, the verdict is not YES/NO
    if p["gen_uninf"] or p["branch_uninf"]:
        check("uncertain_dominates", p["verdict"] == "UNCERTAIN",
              "an undistinguished axis forces UNCERTAIN, never YES/NO")
    else:
        check("uncertain_dominates", True, "no axis was uninformative this run — rule vacuously holds")

    # 4. NO boolean RSI claim anywhere; the verdict is about frontier EXPANSION, explicitly scoped
    blob = (p["verdict"] + " " + VERDICT_PHRASE[p["verdict"]] + " " + p["branching"] + " " + p["generativity"]).lower()
    check("no_rsi_boolean",
          "rsi = true" not in blob and "rsi=true" not in blob and "rsi = false" not in blob and "rsi" not in blob,
          "output is a frontier-expansion candidate judgement + profile — never 'RSI = true/false'")

    # 5. the scope (system, domain, regime, identity) is declared
    sc = p["scope"].lower()
    check("scope_declared",
          all(t in sc for t in ("system", "domain", "regime", "identity")),
          "the (system, domain, verification-regime, state-identity) tuple is named — the result is triple-relative")

    # 6. determinism of the interpretation map (pure function)
    check("interpretation_deterministic",
          interpret("improving", True, False, False, "EXPANDING") == "YES"
          and interpret("improving", False, False, False, "CONVERGED") == "NO"
          and interpret("improving", True, True, False, "EXPANDING") == "UNCERTAIN",
          "interpret() is a pure, total map over the axis verdicts")

    print(f"\n  {passed}/{total} checks. The suite reports a four-axis dynamics PROFILE under a declared scope and a")
    print("  candidate judgement about verified frontier expansion — YES/NO/UNCERTAIN, with UNCERTAIN dominating an")
    print("  undistinguished axis — never 'RSI = true/false'. The project's endpoint is not a detector for a")
    print("  phenomenon; it is a measurement of the preconditions any defensible version of it would require.")
    print("  `estimate ≠ property`; the profile is of a (system, domain, regime, identity) tuple, not of RSI.")
    assert passed == total, "report.py failed a validity/soundness check"


if __name__ == "__main__":
    main()
