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
DELTA_TRAJ = 0.10        # near-critical band for the trajectory-conditioned generativity


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
    gen_super_pooled = "above 1" in generativity
    gen_uninf_pooled = generativity.startswith("UNINFORMATIVE")
    branch_uninf = branching.startswith("UNINFORMATIVE")
    orbit_word = orb["explore_class"].split()[0]

    # TRAJECTORY-CONDITIONED generativity: m_novel at the REACHED (high) capability, not the space-pooled mean.
    # m is a function of state: m_novel(s_low) can be > 1 while m_novel(s_high) < 1. The RSI-relevant question is
    # "after the system has improved itself, is there still frontier?" — the high-s bucket, not the average.
    bks = G.buckets(gen["per_root"])
    lo_mnov = bks[0][2]
    hi_s, _, hi_mnov, _ = bks[-1]
    gen_traj = ("supercritical" if hi_mnov > 1 + DELTA_TRAJ
                else "subcritical" if hi_mnov < 1 - DELTA_TRAJ else "near-critical")
    gen_traj_super = gen_traj == "supercritical"
    gen_traj_uninf = gen_traj == "near-critical"
    shape = ("early expansion → late depletion (Type B: frontier exhaustion)" if lo_mnov > 1 and hi_mnov < 1
             else "expanding across tested capability (Type A)" if lo_mnov > 1 and hi_mnov > 1
             else "subcritical across tested capability" if lo_mnov <= 1 and hi_mnov <= 1 else "mixed")

    # the candidate criterion uses the TRAJECTORY-CONDITIONED generativity, not the pooled scalar
    verdict = interpret(capability, gen_traj_super, gen_traj_uninf, branch_uninf, orbit_word)

    return {
        "n": n, "m_off": m_off, "m_nov": m_nov, "ci_off": ci_off, "ci_nov": ci_nov, "gap": m_off - m_nov,
        "dC": dC, "capability": capability, "branching": branching, "generativity": generativity,
        "orbit_class": orb["explore_class"], "orbit_word": orbit_word,
        "gen_super_pooled": gen_super_pooled, "gen_uninf_pooled": gen_uninf_pooled, "branch_uninf": branch_uninf,
        "lo_mnov": lo_mnov, "hi_mnov": hi_mnov, "hi_s": hi_s, "gen_traj": gen_traj,
        "gen_traj_super": gen_traj_super, "gen_traj_uninf": gen_traj_uninf, "shape": shape, "verdict": verdict,
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
    print("  Verified Improvement Dynamics profile  (m is a function of state: m_novel(s_low) ≠ m_novel(s_high))")
    print(f"    Axis 1  Capability   ΔC          : {p['capability']:<10} (ΔC = {p['dC']:+.3f})")
    print(f"    Axis 2  Branching    m_offspring : {p['branching']}  (m≈{p['m_off']:.2f}, CI [{p['ci_off'][0]:.2f},{p['ci_off'][1]:.2f}])")
    print(f"    Axis 3  Generativity m_novel     :")
    print(f"              pooled (space-average) : {p['generativity']}  (m≈{p['m_nov']:.2f}, CI [{p['ci_nov'][0]:.2f},{p['ci_nov'][1]:.2f}]; overlap gap {p['gap']:+.2f})")
    print(f"              trajectory-conditioned : {p['gen_traj'].upper()} at reached capability  (m_novel(s≈{p['hi_s']:+.3f}) ≈ {p['hi_mnov']:.2f})")
    print(f"              shape                  : {p['shape']}  (m_novel(s): {p['lo_mnov']:.2f} → {p['hi_mnov']:.2f})")
    print(f"    Axis 4  Orbit        O(t)        : {p['orbit_class']}")
    print(f"\n  Candidate for continued verified frontier expansion: {p['verdict']} — {VERDICT_PHRASE[p['verdict']]}")
    print(f"  Criterion uses TRAJECTORY-CONDITIONED generativity (m_novel at reached capability), not the pooled mean —")
    print(f"  so all four axes now measure the same object at the same point in state space. The pooled-vs-trajectory")
    print(f"  disagreement is preserved above as the result: prolific reproduction ≠ generativity; generativity can")
    print(f"  exist at low capability and vanish along the trajectory; orbit shows whether the system escapes the basin.")
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

    # 2. the candidate verdict MATCHES the axis verdicts, using TRAJECTORY-CONDITIONED generativity (not pooled)
    recomputed = interpret(p["capability"], p["gen_traj_super"], p["gen_traj_uninf"], p["branch_uninf"], p["orbit_word"])
    check("interpretation_sound", recomputed == p["verdict"] and p["verdict"] in ("YES", "NO", "UNCERTAIN"),
          f"verdict '{p['verdict']}' recomputes from capability + TRAJECTORY-conditioned generativity + orbit")

    # 3. UNCERTAIN really dominates: if a used axis is uninformative, the verdict is not YES/NO
    if p["gen_traj_uninf"] or p["branch_uninf"]:
        check("uncertain_dominates", p["verdict"] == "UNCERTAIN",
              "an undistinguished axis forces UNCERTAIN, never YES/NO")
    else:
        check("uncertain_dominates", True, "no used axis was uninformative this run — rule vacuously holds")

    # 3b. the disagreement is PRESERVED, not erased: pooled AND trajectory-conditioned generativity both reported
    #     (validity only — we assert both are present/finite, NOT their ordering, which is an outcome)
    check("disagreement_preserved",
          all(k in p for k in ("generativity", "m_nov", "gen_traj", "hi_mnov"))
          and math.isfinite(p["m_nov"]) and math.isfinite(p["hi_mnov"]),
          f"pooled ({p['m_nov']:.2f}) and trajectory-conditioned at reached capability ({p['hi_mnov']:.2f}) both reported")

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
