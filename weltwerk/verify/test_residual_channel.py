# SPDX-License-Identifier: AGPL-3.0-only
"""
test_residual_channel.py — the domain-agnostic causal diagnostic is sound (validity-not-outcome). Pure-stdlib.

  1. estimators_exact          — MI of an independent product = 0; MI of an identical pair = H. (sanity)
  2. null_calibrates           — on a no-channel generator, I(X;Y|Z) is consistent with the shuffle null ⇒
                                 decision CONSISTENT_WITH_NULL (confounded-only signal is not a channel).
  3. channel_detected          — on an injected-channel generator, I(X;Y|Z) ≫ null ⇒ RESIDUAL_DEPENDENCE.
  4. planted_separation        — the procedure separates the planted null from the planted channel.
  5. compression_equals_cmi    — compression_gain == I(X;Y|Z) exactly (the identity that ties #5 and #7).
  6. misspec_stable_for_channel— a genuine channel stays positive under Z-coarsening ⇒ RESIDUAL_MISSPEC_STABLE.
  7. as_analysis_honest        — the result projects to an AnalysisResult with scope + ≥1 limitation.
  8. determinism               — seeded audits agree.

Sound iff 8/8: the procedure correctly separates PLANTED null and channel, calibrates its own bias with the
within-Z shuffle null, equates compression gain to conditional MI, and reports honestly. It proves a property
of the DECISION PROCEDURE, not of any real system. `proves-the-procedure ≠ proves-the-phenomenon`.

Run:  python3 test_residual_channel.py
"""
from __future__ import annotations

import math

from residual_channel import (mutual_information, conditional_mutual_information, compression_gain,
                              audit, planted_case_validator, demo_gen_null, demo_gen_channel)
from artifacts import AnalysisResult, Limitation


def chk(name, ok, detail):
    return (name, ok, detail)


def test_estimators_exact():
    indep = [(a, b) for a in range(3) for b in range(3)]           # p(x,y)=p(x)p(y) ⇒ MI=0
    ident = [(a, a) for a in range(3)] * 3                          # Y=X ⇒ MI=H(X)=log2 3
    ok = abs(mutual_information(indep)) < 1e-9 and abs(mutual_information(ident) - math.log2(3)) < 1e-9
    return chk("estimators_exact", ok, f"MI(indep)≈0, MI(ident)≈log2(3)={math.log2(3):.3f}")


def test_null_calibrates():
    r = audit(demo_gen_null(), reps=100)
    ok = r.decision == "CONSISTENT_WITH_NULL" and abs(r.cmi - r.null_mean) < 0.01
    return chk("null_calibrates", ok, f"CMI={r.cmi:.4f} ≈ null={r.null_mean:.4f} → {r.decision}")


def test_channel_detected():
    r = audit(demo_gen_channel(), reps=100)
    ok = r.decision.startswith("RESIDUAL") and r.cmi > 0.05 and r.cmi > r.null_mean + 4 * r.null_std
    return chk("channel_detected", ok, f"CMI={r.cmi:.4f} ≫ null={r.null_mean:.4f} (z={r.z_score:.1f}) → {r.decision}")


def test_planted_separation():
    v = planted_case_validator(demo_gen_null, demo_gen_channel)
    return chk("planted_separation", v["separates"],
               f"null→{v['null_decision']}, channel→{v['channel_decision']}, separates={v['separates']}")


def test_compression_equals_cmi():
    for gen in (demo_gen_null, demo_gen_channel):
        s = gen()
        if abs(compression_gain(s) - conditional_mutual_information(s)) >= 1e-9:
            return chk("compression_equals_cmi", False, "gain != CMI")
    return chk("compression_equals_cmi", True, "compression_gain == I(X;Y|Z) for both generators")


def test_misspec_stable_for_channel():
    drop_z = lambda s: [(x, y, 0) for x, y, _z in s]               # coarsen Z to a constant
    r = audit(demo_gen_channel(), reps=100, misspec_fns=(drop_z,))
    ok = r.decision == "RESIDUAL_MISSPEC_STABLE" and all(c > 0.05 for c in r.misspec_cmis)
    return chk("misspec_stable_for_channel", ok, f"decision={r.decision} misspec_cmis={tuple(round(c,3) for c in r.misspec_cmis)}")


def test_as_analysis_honest():
    a = audit(demo_gen_channel(), reps=50).as_analysis()
    ok = (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
          and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations))
    return chk("as_analysis_honest", ok, f"scope={a.scope!r} limitations={len(a.limitations)}")


def test_determinism():
    a, b = audit(demo_gen_null(), reps=50), audit(demo_gen_null(), reps=50)
    ok = (a.cmi, a.null_mean, a.decision) == (b.cmi, b.null_mean, b.decision)
    return chk("determinism", ok, f"repeated audit agrees: {ok}")


def main():
    results = [
        test_estimators_exact(),
        test_null_calibrates(),
        test_channel_detected(),
        test_planted_separation(),
        test_compression_equals_cmi(),
        test_misspec_stable_for_channel(),
        test_as_analysis_honest(),
        test_determinism(),
    ]
    print("test_residual_channel — domain-agnostic confounder-conditioned dependence audit\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the procedure separates planted null/channel, "
          f"calibrates its\n  own bias, equates compression gain to conditional MI, and reports honestly. "
          f"proves-the-procedure ≠ proves-the-phenomenon.")
    assert passed == total, f"{total - passed} check(s) failed — diagnostic not sound"


if __name__ == "__main__":
    main()
