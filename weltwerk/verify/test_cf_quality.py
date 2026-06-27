# SPDX-License-Identifier: AGPL-3.0-only
"""
test_cf_quality.py — PO-2 proofs: counterfactual accuracy against an independent exhaustive gold. Pure-stdlib.

  1. single_cause_recovered    — on single-minimal-cause traces, analyze critical == gold (precision=recall=1)
  2. mixed_excludes_decoy      — the mixed trace flags the true cause, not the decoy
  3. overdetermined_honest     — analyze returns ∅ AND gold size ≥ 2 (honest blind spot, not a false cause)
  4. no_false_critical         — every flagged-critical event's single removal truly clears the violation
  5. beats_random_baseline     — analyze precision on single-cause > a random labeller's expected precision
  6. determinism               — repeated evaluation agrees

Run:  python3 test_cf_quality.py
"""
from __future__ import annotations

from cf_quality_bench import evaluate, minimal_removal_set, SUITE, TAIL_OK
import counterfactual
from artifacts import normalize_invariants


def chk(name, ok, detail):
    return (name, ok, detail)


def test_single_cause_recovered():
    bad = []
    for label, w, tr, inv, exp in SUITE:
        if exp != "single-cause":
            continue
        r = evaluate(w, tr, inv)
        if not (r["precision"] == 1.0 and r["recall"] == 1.0):
            bad.append(f"{label}:P={r['precision']},R={r['recall']}")
    return chk("single_cause_recovered", not bad, f"single-cause P=R=1 except: {bad or 'none'}")


def test_mixed_excludes_decoy():
    w, tr, inv = next((w, tr, inv) for (l, w, tr, inv, e) in SUITE if l == "mixed/decoy")
    r = evaluate(w, tr, inv)
    crit = [tuple(c) for c in r["critical"]]
    ok = ("destroy", "hub") in crit and all(c[1] != "decoy" for c in crit)
    return chk("mixed_excludes_decoy", ok, f"critical={r['critical']} (true cause, no decoy)")


def test_overdetermined_honest():
    w, tr, inv = next((w, tr, inv) for (l, w, tr, inv, e) in SUITE if l == "overdet/two")
    r = evaluate(w, tr, inv)
    ok = r["critical"] == [] and r["gold_size"] >= 2
    return chk("overdetermined_honest", ok, f"critical={r['critical']} (∅) gold_size={r['gold_size']} (≥2)")


def test_no_false_critical():
    bad = []
    for label, w, tr, inv, exp in SUITE:
        nz = normalize_invariants(inv)
        crit = set(counterfactual.analyze(w, tr, inv).critical)
        events = [tuple(e) for e in tr]
        for c in crit:
            reduced = [e for e in events if e != c]
            if counterfactual._trajectory_violates(w, reduced, nz):   # removing a 'critical' must clear it
                bad.append(f"{label}:{c}")
    return chk("no_false_critical", not bad, f"flagged-critical whose removal does NOT clear: {bad or 'none'}")


def test_beats_random_baseline():
    sc = [(w, tr, inv) for (l, w, tr, inv, e) in SUITE if e == "single-cause"]
    analyze_p = sum(evaluate(w, tr, inv)["precision"] for (w, tr, inv) in sc) / len(sc)
    # EXPECTED precision of a uniformly-random single-event labeller = mean(|gold| / len(trace))
    exp_random = sum(len(minimal_removal_set(w, tr, inv)) / len(tr) for (w, tr, inv) in sc) / len(sc)
    ok = analyze_p > exp_random
    return chk("beats_random_baseline", ok, f"analyze precision {round(analyze_p,3)} > expected-random {round(exp_random,3)}")


def test_determinism():
    w, tr, inv = next((w, tr, inv) for (l, w, tr, inv, e) in SUITE if l == "star/single")
    ok = evaluate(w, tr, inv) == evaluate(w, tr, inv)
    return chk("determinism", ok, f"repeated evaluation agrees: {ok}")


def main():
    results = [
        test_single_cause_recovered(),
        test_mixed_excludes_decoy(),
        test_overdetermined_honest(),
        test_no_false_critical(),
        test_beats_random_baseline(),
        test_determinism(),
    ]
    print("test_cf_quality — PO-2: counterfactual accuracy vs exhaustive gold (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: single-cause critical events are recovered "
          f"exactly,\n  the decoy is excluded, overdetermined traces yield ∅ honestly (gold size ≥ 2), no flagged "
          f"event is\n  a false cause, and accuracy beats a random labeller. PO-2 discharged for the tested "
          f"structures.\n  single-event-ablation ≠ minimal-set (a stated, now-quantified boundary).")
    assert passed == total, f"{total - passed} check(s) failed — counterfactual accuracy not established"


if __name__ == "__main__":
    main()
