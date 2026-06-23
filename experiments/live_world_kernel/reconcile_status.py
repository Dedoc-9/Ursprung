# SPDX-License-Identifier: AGPL-3.0-only
"""
reconcile_status.py — measurement survives DISAGREEMENT (declare when your witnesses conflict).

`repo_status` proved provenance survives extraction (one witness, downgraded honestly). This asks the harder
question: when TWO witnesses model the same system and disagree, what does the convergence object say? The
shallow answer — "disagreement → DECLARED" — is wrong by the project's own rule: the Dentatus states keep
**conflicting evidence** distinct from **not measured**. Collapsing them forces two different uncertainties into
one. So disagreement gets its own state, `CONTESTED`, and reconciliation is governed by the epistemic lattice:

    STRENGTH:  MEASURED_BY_INTERVENTION  >  MEASURED  >  DECLARED  >  N/A
    (CONTESTED is the conflicting-evidence marker — non-actionable, strictly below MEASURED, distinct from DECLARED)

Disagreement is NOT uniform — the lattice says how to reconcile:
    * a STRONGER witness vs a weaker one  → REFINEMENT, not deadlock: the stronger wins (the weaker already
      admits it is a lower bound), and the dissent is RECORDED, never dropped.
    * PEERS at equal strength with incompatible claims  → genuine CONTESTED: both recorded, neither chosen.

THE INVARIANT (the file's headline self-test): **reconciliation strength ≤ the strongest witness.** Agreement
preserves it; conflict can only LOWER it to CONTESTED; nothing is ever raised by inheritance. "Epistemic strength
may only decrease as evidence weakens" — made executable. Never increase. Never stay strong by inheritance.

The two real witnesses that already disagree on the same repo: `module_graph` (basename, absolute-only — weaker)
vs `fidelity_gap` (package-path, relative-aware — stronger). The symmetric CONTESTED case (two peers, e.g. static
vs runtime tracing) is exercised synthetically — the runtime witness is not built. `declared ≠ verified`.

Run (from this directory):  PYTHONHASHSEED=0 python3 reconcile_status.py   [optional: a repo path for the real demo]
"""
from __future__ import annotations

import os
import sys

import module_graph as mg
import fidelity_gap as fg
from reality_status import Cell, MEASURED, MEASURED_BY_INTERVENTION, DECLARED, NOT_APPLICABLE

CONTESTED = "CONTESTED"   # conflicting evidence — distinct from DECLARED (not measured); Dentatus epistemic state

# the lattice as a numeric order. CONTESTED and DECLARED are both non-actionable (1) but DISTINCT labels.
STRENGTH = {MEASURED_BY_INTERVENTION: 3, MEASURED: 2, DECLARED: 1, CONTESTED: 1, NOT_APPLICABLE: 0}


def reconcile_cell(witnesses: list) -> Cell:
    """Pure. witnesses = [(name, Cell, coverage_rank), ...]. Reconcile by the lattice:
    dominance (strength, then coverage) resolves with dissent recorded; co-maximal peers that disagree → CONTESTED.
    INVARIANT: STRENGTH[result] ≤ max(STRENGTH[inputs]) — strength may only decrease, never inflate."""
    active = [(n, c, r) for (n, c, r) in witnesses if c.status != NOT_APPLICABLE]
    if not active:
        return Cell("N/A", NOT_APPLICABLE, "all witnesses inapplicable")

    def key(t):
        return (STRENGTH[t[1].status], t[2])

    top = max(key(t) for t in active)
    tops = [t for t in active if key(t) == top]
    top_values = {t[1].value for t in tops}

    if len(top_values) == 1:                       # a unique value dominates (alone or by strength/coverage)
        value = next(iter(top_values))
        status = tops[0][1].status
        others = sorted({(n, c.value) for (n, c, _r) in active if c.value != value})
        if not others:
            ev = f"corroborated by {sorted(n for n, _c, _r in active)} at {status}"
        else:
            winners = sorted(n for n, _c, _r in tops)
            ev = f"{winners} ({status}) dominates; recorded dissent (weaker/lower-coverage): {others}"
        return Cell(value, status, ev)            # strength = the top witness's — NOT increased

    claims = sorted((n, c.value) for (n, c, _r) in tops)   # co-maximal peers disagree
    return Cell("CONTESTED", CONTESTED,
                f"co-maximal witnesses disagree {claims} — conflicting evidence, neither dominates "
                "(declared as conflict, not silently resolved)")


# --------------------------------------------------------------------------------------------------
# Real demo: two static extractors that genuinely disagree on the same repo.
# --------------------------------------------------------------------------------------------------
def _indeg(edges, m):
    return sum(1 for (_u, v) in edges if v == m)


def _dependency_witnesses(root: str):
    """Build per-module dependency claims from BOTH real extractors. Shared key = the package-path module name;
    the basename witness is mapped onto it by basename (and DECLARES where its basename is ambiguous/absent —
    its own known weakness). Returns (modules, claim_fn)."""
    mgx = mg.extract(root)                         # basename namespace (weaker: collisions, no relative imports)
    fgx = fg.diagnose(root)                        # package-path namespace (stronger: relative recovered)
    mg_nodes, mg_edges, mg_coll = mgx["nodes"], mgx["edges"], set(mgx["collisions"])
    fg_known, fg_edges = fgx["known"], fgx["edges"]

    def claim(dotted: str):
        b = dotted.rsplit(".", 1)[-1]
        fg_cell = Cell("IRREVERSIBLE" if _indeg(fg_edges, dotted) > 0 else "REVERSIBLE", MEASURED,
                       f"package-path extractor: in-degree={_indeg(fg_edges, dotted)}")
        if b in mg_coll or b not in mg_nodes:
            mg_cell = Cell("DECLARED", DECLARED,
                           f"basename extractor cannot disambiguate '{b}' (collision/absent) — no claim")
        else:
            mg_cell = Cell("IRREVERSIBLE" if _indeg(mg_edges, b) > 0 else "REVERSIBLE", MEASURED,
                           f"basename extractor (lower coverage): in-degree={_indeg(mg_edges, b)}")
        # fidelity_gap dominates module_graph by coverage (proven: collisions→0, relative imports recovered)
        return reconcile_cell([("basename", mg_cell, 1), ("package_path", fg_cell, 2)]), mg_cell, fg_cell

    return sorted(fg_known), claim


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    print("reconcile_status — two witnesses, one system: declare when they DISAGREE (CONTESTED ≠ DECLARED).")
    print("Strength may only DECREASE on conflict, never inflate by inheritance.\n")

    modules, claim = _dependency_witnesses(root)
    print(f"extracted: {root}  ({len(modules)} modules)  —  basename (weak) vs package-path (strong)\n")
    shown = 0
    for m in modules:
        reconciled, mg_cell, fg_cell = claim(m)
        if mg_cell.value != fg_cell.value and shown < 4:     # show where the witnesses actually disagree
            print(f"  dependency({m!r}):  reconciled = {reconciled.value} [{reconciled.status}]")
            print(f"      basename:     {mg_cell.value} [{mg_cell.status}]")
            print(f"      package_path: {fg_cell.value} [{fg_cell.status}]")
            print(f"      └ {reconciled.evidence}")
            shown += 1
    if shown == 0:
        print("  (witnesses agree on every module here — a flat/absolute-import repo; point at a package "
              "like click to see refinement)\n")
    else:
        print()

    # ---------------- self-test: the reconciliation LATTICE (synthetic witnesses, deterministic) ----------------
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    runtime_irr = ("runtime", Cell("IRREVERSIBLE", MEASURED_BY_INTERVENTION, "ran the tests"), 3)
    static_rev = ("static", Cell("REVERSIBLE", MEASURED, "import-graph lower bound"), 2)
    static_irr = ("static2", Cell("IRREVERSIBLE", MEASURED, "import-graph lower bound"), 2)
    declared = ("noprobe", Cell("DECLARED", DECLARED, "no probe"), 1)
    na = ("na", Cell("N/A", NOT_APPLICABLE, "inapplicable"), 0)

    # 1. THE invariant: result strength ≤ strongest input, across a battery — never inflated by inheritance
    battery = [[static_rev], [runtime_irr, static_rev], [static_rev, static_irr],
               [declared, static_rev], [runtime_irr, static_irr, declared]]
    monotone = all(STRENGTH[reconcile_cell(ws).status] <= max(STRENGTH[w[1].status] for w in ws) for ws in battery)
    check("strength_never_inflates", monotone,
          "STRENGTH[reconcile] ≤ max(STRENGTH[inputs]) for every case — strength only decreases")

    # 2. a STRONGER witness refines a weaker one (resolution, not deadlock) — and records the dissent
    r = reconcile_cell([static_rev, runtime_irr])
    check("stronger_refines_not_contests",
          r.value == "IRREVERSIBLE" and r.status == MEASURED_BY_INTERVENTION and "REVERSIBLE" in r.evidence,
          "runtime (intervention) overrides static (lower bound); static's dissent is recorded, not dropped")

    # 3. PEERS at equal strength that disagree → CONTESTED (both claims recorded)
    r = reconcile_cell([static_rev, static_irr])
    check("peers_disagree_contested",
          r.status == CONTESTED and "REVERSIBLE" in r.evidence and "IRREVERSIBLE" in r.evidence,
          "two MEASURED peers, incompatible → CONTESTED, both claims kept")

    # 4. CONTESTED is DISTINCT from DECLARED (conflicting evidence ≠ not measured — Dentatus states)
    check("contested_distinct_from_declared",
          CONTESTED != DECLARED and reconcile_cell([static_rev, static_irr]).status != DECLARED,
          "conflict gets its own state; it is not folded into 'not measured'")

    # 5. agreement PRESERVES strength (not lowered to CONTESTED/DECLARED)
    r = reconcile_cell([static_irr, ("static3", Cell("IRREVERSIBLE", MEASURED, "agrees"), 2)])
    check("agreement_preserves_strength", r.value == "IRREVERSIBLE" and r.status == MEASURED and "corroborated" in r.evidence,
          "witnesses that agree → the value at MEASURED, corroborated — strength kept")

    # 6. all-N/A → N/A (inapplicability is not conflict)
    check("all_na_is_na", reconcile_cell([na, ("na2", Cell("N/A", NOT_APPLICABLE, "x"), 0)]).status == NOT_APPLICABLE,
          "every witness inapplicable → N/A (not CONTESTED, not DECLARED)")

    # 7. NO SILENT PICK: the losing/dissenting claim always survives in the evidence (refine AND contest)
    refine = reconcile_cell([static_rev, runtime_irr])
    contest = reconcile_cell([static_rev, static_irr])
    check("no_silent_pick",
          "REVERSIBLE" in refine.evidence and ("REVERSIBLE" in contest.evidence and "IRREVERSIBLE" in contest.evidence),
          "the witness that did not win is recorded in both the refined and the contested outcome")

    print(f"\n{passed}/{total} checks. Measurement survives disagreement — by declaring the disagreement. Two")
    print("witnesses of one system are reconciled on the epistemic lattice: a stronger witness REFINES a weaker")
    print("one (the lower bound yields, its dissent recorded), and equal-strength peers that conflict become")
    print("CONTESTED — a first-class 'conflicting evidence' state kept distinct from 'not measured' (DECLARED).")
    print("Reconciliation strength can only DECREASE on conflict, never inflate by inheritance, and no witness is")
    print("ever silently dropped. The deepest form of the discipline is not 'declare what you know' — it is")
    print("'declare when your witnesses disagree'. `declared ≠ verified`; preservation of provenance under conflict.")
    assert passed == total, "reconcile_status failed its own self-test"


if __name__ == "__main__":
    main()
