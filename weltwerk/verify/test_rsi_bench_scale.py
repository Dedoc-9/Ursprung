# SPDX-License-Identifier: AGPL-3.0-only
"""
test_rsi_bench_scale.py — apparatus-validity proofs for the enterprise RSI benchmark (validity-not-outcome).

Asserts the harness measures honestly and that ONLY genuinely generalizing policies beat the baseline on
held-out worlds — using mostly *relative* comparisons (robust). It does not assert a general RSI claim.

  1. heldout_disjoint        — train and held-out world texts are instance-disjoint
  2. learned_generalizes     — learned beats baseline on held-out: REG > 1.5 and sign-test p < 0.05; learned ≥ frequency
  3. memorizer_overfit_fail  — memorizer and overfit do NOT transfer (REG ≈ 1) and both < learned
  4. greedy_blast_defeated   — the trap structures defeat rank-by-blast: greedy REG < learned REG
  5. p_value_sane            — baseline-vs-baseline ⇒ p = 1.0 (no difference); learned ⇒ p < 0.05
  6. efficiency_positive     — held-out verified-work reduction per training experiment > 0
  7. no_false_restore        — the first restorer a policy hits is a real engine re-verification
  8. determinism             — two runs agree

Run:  python3 test_rsi_bench_scale.py
"""
from __future__ import annotations

from rsi_bench_scale import (run, gen_world, world_info, restorer_set, fit_learned, _learned,
                             TAIL_OK, ENGINE)
from repair import _forbid_and_verify

R = run(n_train=30, n_held=30, verbose=False)
P = R["policies"]


def chk(name, ok, detail):
    return (name, ok, detail)


def test_heldout_disjoint():
    tr = {gen_world(s) for s in range(R["n_train"])}
    he = {gen_world(s) for s in range(100000, 100000 + R["n_held"])}
    ok = tr.isdisjoint(he)
    return chk("heldout_disjoint", ok, f"train {len(tr)} ∩ held {len(he)} = {len(tr & he)}")


def test_learned_generalizes():
    L, F = P["learned"], P["frequency"]
    ok = L["REG"] > 1.5 and L["p_value"] < 0.05 and L["REG"] >= F["REG"]
    return chk("learned_generalizes", ok,
               f"learned REG={L['REG']} p={L['p_value']} ≥ frequency REG={F['REG']}")


def test_memorizer_overfit_fail():
    M, O, L = P["memorizer"], P["overfit"], P["learned"]
    ok = M["REG"] < 1.2 and O["REG"] < 1.2 and M["REG"] < L["REG"] and O["REG"] < L["REG"]
    return chk("memorizer_overfit_fail", ok,
               f"memorizer REG={M['REG']}, overfit REG={O['REG']} (both ≈1, < learned {L['REG']})")


def test_greedy_blast_defeated():
    G, L = P["greedy_blast"], P["learned"]
    ok = G["REG"] < L["REG"]
    return chk("greedy_blast_defeated", ok, f"greedy_blast REG={G['REG']} < learned REG={L['REG']} (traps work)")


def test_p_value_sane():
    base = P["baseline(canonical)"]
    ok = base["p_value"] == 1.0 and base["wins"] == 0 and base["losses"] == 0 and P["learned"]["p_value"] < 0.05
    return chk("p_value_sane", ok, f"baseline p={base['p_value']} (no self-difference); learned p={P['learned']['p_value']}")


def test_efficiency_positive():
    ok = R["efficiency_per_train_experiment"] > 0
    return chk("efficiency_positive", ok, f"verified-work reduction / train experiment = {R['efficiency_per_train_experiment']}")


def test_no_false_restore():
    info = world_info(gen_world(100000))
    rs = restorer_set(info)
    w = fit_learned([world_info(gen_world(s)) for s in range(8)])
    order = _learned(info, w)
    first = next((a for a in order if a in rs), None)
    ok = (len(rs) >= 1 and first is not None
          and _forbid_and_verify(info["world"], first, TAIL_OK, ENGINE, info["bound"]).status != "VIOLATED")
    return chk("no_false_restore", ok, f"first restorer {first} re-verifies as non-VIOLATED; |restorers|={len(rs)}")


def test_determinism():
    R2 = run(n_train=30, n_held=30, verbose=False)
    ok = (R["policies"]["learned"]["REG"] == R2["policies"]["learned"]["REG"]
          and R["policies"]["learned"]["p_value"] == R2["policies"]["learned"]["p_value"]
          and R["iterated_curve_(k,REG)"] == R2["iterated_curve_(k,REG)"])
    return chk("determinism", ok, f"identical learned REG/p and iterated curve across runs: {ok}")


def main():
    results = [
        test_heldout_disjoint(),
        test_learned_generalizes(),
        test_memorizer_overfit_fail(),
        test_greedy_blast_defeated(),
        test_p_value_sane(),
        test_efficiency_positive(),
        test_no_false_restore(),
        test_determinism(),
    ]
    print("test_rsi_bench_scale — enterprise RSI benchmark apparatus validity (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: held-out disjoint; learned generalizes "
          f"(REG>1.5, p<0.05);\n  memorizer/overfit do NOT transfer; trap structures defeat greedy-blast; the "
          f"p-value is sane;\n  efficiency-per-experiment is positive; restorers are real re-verifications; "
          f"runs are deterministic.\n  The harness separates generalization from lookup at scale. "
          f"improved_map ≠ changed_criterion.")
    assert passed == total, f"{total - passed} check(s) failed — the scaled apparatus is not sound"


if __name__ == "__main__":
    main()
