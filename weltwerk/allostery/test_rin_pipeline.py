# SPDX-License-Identifier: AGPL-3.0-only
"""
test_rin_pipeline.py — Phase 17 proofs (validity-not-outcome): the evaluation FRAMEWORK is sound.

We verify the machinery, not a biological claim (the gold sets here are synthetic).

  1. pdb_parse_and_contacts  — a PDB parses to residues; near pairs contact, far pairs don't, seq-neighbours skipped
  2. reach_is_component      — reach() returns the connected component (Potential)
  3. flow_decays_with_dist   — attenuating flow gives a nearer residue more signal than a farther one (Actual)
  4. potential_superset_actual — the carrying (Actual) set is a subset of the reachable (Potential) set
  5. betweenness_finds_bridge— Brandes betweenness peaks on the bridge of a barbell graph (sanity of the method)
  6. eval_metrics_correct    — precision@k / recall / F1 / AUC are computed correctly on a known ranking
  7. eval_baselines          — the harness reports a random null + degree baseline + lift; a perfect ranking beats null
  8. determinism             — analyses + evaluation are reproducible

Run:  python3 test_rin_pipeline.py
"""
from __future__ import annotations

import pdb_rin
import rin_analysis as rin
from eval_harness import evaluate, precision_recall_at_k, rank_auc


def check(name, ok, detail):
    return (name, ok, detail)


def test_pdb_parse_and_contacts():
    g = pdb_rin.build_rin(pdb_rin.synthetic_pdb())
    labels = g["labels"]; adj = g["adj"]
    ok = (len(labels) == 6 and "ALA6" in adj["ALA1"]            # cross-strand contact (~5 Å)
          and "LEU3" not in adj["ALA1"]                          # far (~10 Å) ⇒ no contact
          and "VAL2" not in adj["ALA1"])                         # sequence neighbour ⇒ skipped
    return check("pdb_parse_and_contacts", ok, f"{len(labels)} residues; ALA1 contacts {sorted(adj['ALA1'])}")


def test_reach_is_component():
    g = pdb_rin.build_rin(pdb_rin.synthetic_pdb())
    r = rin.reach(g["adj"], "ALA1")
    return check("reach_is_component", r == set(g["labels"]), f"reachable {len(r)}/{len(g['labels'])}")


def test_flow_decays_with_dist():
    g = pdb_rin.build_rin(pdb_rin.synthetic_pdb())
    f = rin.attenuating_flow(g["adj"], "ALA1")
    ok = f["ALA6"] > f["LEU3"]            # ALA6 is 1 hop from ALA1; LEU3 is 2 hops
    return check("flow_decays_with_dist", ok, f"flow ALA6={round(f['ALA6'],4)} > LEU3={round(f['LEU3'],4)}")


def test_potential_superset_actual():
    g = pdb_rin.build_rin(pdb_rin.synthetic_pdb())
    pa = rin.potential_vs_actual(g["adj"], "ALA1")
    ok = pa["carrying"] <= pa["potential"] and len(pa["carrying"]) <= len(pa["potential"])
    return check("potential_superset_actual", ok,
                 f"carrying {len(pa['carrying'])} ⊆ potential {len(pa['potential'])}")


def test_betweenness_finds_bridge():
    # barbell: two triangles joined through BRIDGE — every cross path goes through it
    adj = {"a1": ["a2", "a3", "BRIDGE"], "a2": ["a1", "a3"], "a3": ["a1", "a2"],
           "BRIDGE": ["a1", "b1"],
           "b1": ["b2", "b3", "BRIDGE"], "b2": ["b1", "b3"], "b3": ["b1", "b2"]}
    bc = rin.betweenness(adj)
    top = max(bc, key=lambda v: bc[v])
    return check("betweenness_finds_bridge", top == "BRIDGE", f"top betweenness = {top} ({round(bc[top],2)})")


def test_eval_metrics_correct():
    scores = {"n1": 9, "n2": 8, "n3": 3, "n4": 2, "n5": 1, "n6": 0}
    gold = {"n1", "n2"}
    pr = precision_recall_at_k(scores, gold, 2)
    auc = rank_auc(scores, gold)
    ok = pr["precision"] == 1.0 and pr["recall"] == 1.0 and pr["f1"] == 1.0 and auc == 1.0
    return check("eval_metrics_correct", ok, f"P@2={pr['precision']} R={pr['recall']} F1={pr['f1']} AUC={auc}")


def test_eval_baselines():
    adj = {f"n{i}": [] for i in range(1, 7)}
    scores = {"n1": 9, "n2": 8, "n3": 3, "n4": 2, "n5": 1, "n6": 0}
    gold = {"n1", "n2"}
    m = evaluate(scores, gold, adj, k=2)
    ok = (m["null_precision"] == round(2 / 6, 4) and m["lift_over_null"] and m["lift_over_null"] > 1
          and m["degree_baseline_precision"] is not None)
    return check("eval_baselines", ok,
                 f"precision {m['precision_at_k']} vs null {m['null_precision']} (lift ×{m['lift_over_null']})")


def test_determinism():
    g = pdb_rin.build_rin(pdb_rin.synthetic_pdb())
    a = rin.betweenness(g["adj"]); b = rin.betweenness(g["adj"])
    f1 = rin.attenuating_flow(g["adj"], "ALA1"); f2 = rin.attenuating_flow(g["adj"], "ALA1")
    return check("determinism", a == b and f1 == f2, f"betweenness + flow reproducible: {a == b and f1 == f2}")


def main():
    results = [
        test_pdb_parse_and_contacts(),
        test_reach_is_component(),
        test_flow_decays_with_dist(),
        test_potential_superset_actual(),
        test_betweenness_finds_bridge(),
        test_eval_metrics_correct(),
        test_eval_baselines(),
        test_determinism(),
    ]
    print("test_rin_pipeline — Phase 17: PDB → RIN → analyses → evaluation framework (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: real PDBs parse to a contact network,"
          f"\n  reach=Potential and attenuating flow=Actual (carrying ⊆ reachable), established centrality finds"
          f"\n  the bridge, and the EVALUATION harness computes precision/recall/F1/AUC with random + degree"
          f"\n  baselines. The framework is verified; the biology needs a real gold set.")
    assert passed == total, f"{total - passed} check(s) failed — the evaluation framework is not sound"


if __name__ == "__main__":
    main()
