# SPDX-License-Identifier: AGPL-3.0-only
"""
eval_harness.py — Phase 17: the centerpiece. A reproducible framework for EVALUATING graph-based allostery
hypotheses against experimental evidence.

This does NOT improve allostery prediction. It holds *any* predictor accountable. You give it (1) a per-
residue score from some method (betweenness, flow, your own), and (2) a GOLD set of residues that experiment
has shown to be allosterically important (e.g. allosteric-site or uncoupling-mutation positions, from deep
mutational scans / double-mutant cycles / the literature). It returns honest metrics with baselines:

    precision@k, recall, F1, rank-AUC,  AND
    a RANDOM null baseline (what you'd get by chance) + a DEGREE baseline (does the method beat "pick the
    most-connected residues?") + the LIFT over each.

The framework is method-agnostic on purpose: predictors come and go; a transparent scorer with baselines is
what lasts. The gold set is supplied by the caller and never fabricated here — the demo uses a clearly
SYNTHETIC structure + gold so the metric logic is verified without faking biology.

`good-score ≠ correct-mechanism`; `beats-null ≠ proven`. The harness reports correspondence to evidence and
the baselines that contextualize it; it does not certify mechanism.
"""
from __future__ import annotations


def _ranked(scores):
    return [r for r, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))]


def precision_recall_at_k(scores, gold, k):
    gold = set(gold)
    top = _ranked(scores)[:k]
    hits = sum(1 for r in top if r in gold)
    precision = hits / k if k else 0.0
    recall = hits / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"k": k, "hits": hits, "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def rank_auc(scores, gold):
    """AUC = P(a gold residue is ranked above a non-gold one). 0.5 = chance. Rank-based (Mann–Whitney)."""
    gold = set(scores) & set(gold)
    neg = set(scores) - gold
    if not gold or not neg:
        return None
    wins = ties = 0
    for g in gold:
        for n in neg:
            if scores[g] > scores[n]:
                wins += 1
            elif scores[g] == scores[n]:
                ties += 1
    return round((wins + 0.5 * ties) / (len(gold) * len(neg)), 4)


def random_baseline(n_total, gold, k):
    """Expected precision@k of picking k residues uniformly at random: |gold|/N."""
    return round(len(set(gold)) / n_total, 4) if n_total else 0.0


def degree_baseline(adj, gold, k):
    """Precision@k of the trivial 'most-connected residues' predictor — the bar a real method must clear."""
    deg = {n: len(adj[n]) for n in adj}
    return precision_recall_at_k(deg, gold, k)["precision"]


def evaluate(scores, gold, adj=None, k=None):
    """Full honest scorecard for one method's scores against an experimental gold set."""
    gold = set(scores) & set(gold)
    n = len(scores)
    k = k or max(1, len(gold))
    pr = precision_recall_at_k(scores, gold, k)
    null = random_baseline(n, gold, k)
    deg = degree_baseline(adj, gold, k) if adj is not None else None
    auc = rank_auc(scores, gold)
    return {
        "n_residues": n, "n_gold": len(gold), "k": k,
        "precision_at_k": pr["precision"], "recall": pr["recall"], "f1": pr["f1"], "auc": auc,
        "null_precision": null, "lift_over_null": round(pr["precision"] / null, 2) if null else None,
        "degree_baseline_precision": deg,
        "beats_degree": (None if deg is None else pr["precision"] > deg),
    }


def report(name, scores, gold, adj=None, k=None):
    m = evaluate(scores, gold, adj, k)
    print(f"  [{name}]  precision@{m['k']}={m['precision_at_k']}  recall={m['recall']}  F1={m['f1']}  AUC={m['auc']}")
    print(f"       vs null {m['null_precision']} (lift ×{m['lift_over_null']})"
          + (f"  vs degree-baseline {m['degree_baseline_precision']} (beats it: {m['beats_degree']})" if adj is not None else ""))
    return m


def main():
    import pdb_rin
    import rin_analysis as rin
    print("eval_harness.py — Phase 17: evaluating allostery hypotheses against (here, SYNTHETIC) gold\n")
    g = pdb_rin.build_rin(pdb_rin.synthetic_pdb()); adj = g["adj"]
    bc = rin.betweenness(adj)
    flow = rin.attenuating_flow(adj, "ALA1")
    # SYNTHETIC gold (illustrative only — NOT real experimental data): pretend VAL2 & VAL5 are the validated
    # allosterically-important residues, to verify the metric logic.
    gold = {"VAL2", "VAL5"}
    print("  gold set (SYNTHETIC, illustrative): " + ", ".join(sorted(gold)) + "\n")
    report("betweenness", bc, gold, adj)
    report("flow-from-ALA1", flow, gold, adj)
    print("\n  this scores hypotheses against evidence + baselines; it does NOT claim a better predictor.")
    print("  good-score ≠ correct-mechanism; beats-null ≠ proven. Supply a REAL gold set for real conclusions.")


if __name__ == "__main__":
    main()
