# SPDX-License-Identifier: AGPL-3.0-only
"""
repo_status.py — the convergence object fed by a REAL extraction (can epistemic provenance survive contact with reality?)

`reality_status.py` ran the seven boundaries over a hand-built kernel fact, where the evidence is strong: the
kernel owns its log, so it can `MEASURE` commitment/dependency/durability and even `MEASURE_BY_INTERVENTION`
(replay `do(¬eid)`). This file feeds the SAME convergence object from a *real extracted system* — a source tree
parsed by `fidelity_gap` / `module_graph` — where the evidence is much weaker. A static import graph cannot run
the program; it cannot replay; it has blind spots (dynamic imports).

The whole point, and the only honest way to do it: **the epistemic type must DOWNGRADE to match the weaker
evidence, never inherit the kernel's strength.** Concretely —

    kernel  identifiability = NECESSARY  [MEASURED_BY_INTERVENTION]   (it can replay do(¬eid))
    repo    identifiability = (unknown)  [DECLARED]                   (static cannot replay — observation ≠
                                                                       intervention; needs running code/tests)

If the extractor quietly kept `MEASURED_BY_INTERVENTION` over static evidence, it would be inventing certainty —
the exact failure `fidelity_gap` exists to refuse (`declared ≠ verified`). So `MEASURED_BY_INTERVENTION` must
appear **nowhere** in a static extraction, and the blind spots (dynamic imports) must propagate as `DECLARED`,
not vanish. The answer to "can epistemic provenance survive contact with reality?" is *yes — by getting weaker,
honestly.*

Run (from this directory):  PYTHONHASHSEED=0 python3 repo_status.py   [optional: a path to a real repo to audit]
"""
from __future__ import annotations

import sys

import module_graph as mg
import fidelity_gap as fg
from reality_status import Cell, MEASURED, DECLARED, NOT_APPLICABLE   # reuse the SAME epistemic vocabulary

HIGH_FAN_IN = 3
_AXES = ("commitment", "dependency", "durability", "authority", "verification", "orientability", "identifiability")


def _indeg(edges, m):
    return sum(1 for (_u, v) in edges if v == m)


def _outs(edges, m):
    return [v for (u, v) in edges if u == m]


def _dynamic_modules(diag):
    return {d for (d, _why) in diag["piles"]["runtime_frontier"]}


def repo_status(diag: dict, dotted: str) -> dict:
    """The convergence object over an EXTRACTED module. Every cell's provenance reflects STATIC evidence —
    downgraded from the kernel's, never inheriting it. Returns {axis: Cell}."""
    known, edges, dyn = diag["known"], diag["edges"], _dynamic_modules(diag)
    cells: dict[str, Cell] = {}

    present = dotted in known
    cells["commitment"] = Cell(
        "PRESENT" if present else "ABSENT", MEASURED,
        "found in extraction — NOTE: extraction-presence, NOT authority-gated commitment (weaker than kernel COMMITTED)")

    if present:
        indeg = _indeg(edges, dotted)
        out = _outs(edges, dotted)
        dep_note = (f"static in-degree={indeg} (LOWER BOUND — dynamic importers are invisible); out-degree={len(out)}")
        if dotted in dyn:
            dep_note += " | this module has dynamic imports — its OUTBOUND deps are incomplete"
        cells["dependency"] = Cell("IRREVERSIBLE" if indeg > 0 else "REVERSIBLE", MEASURED, dep_note)
    else:
        cells["dependency"] = Cell("N/A", NOT_APPLICABLE, "module not in extraction")

    cells["durability"] = Cell("N/A", NOT_APPLICABLE,
                               "no replica / regeneration concept in a static codebase — durability inapplicable")
    cells["authority"] = Cell("N/A", NOT_APPLICABLE,
                              "no authority mechanism in an import graph — authority arbitrage inapplicable")
    cells["verification"] = Cell("DECLARED", DECLARED,
                                 "test floor / verification not assessed by static import extraction "
                                 "(see ADJUDICATION_THROUGHPUT_BOUNDARY.md)")
    cells["orientability"] = Cell("N/A", NOT_APPLICABLE,
                                  "bare imports carry no signed trust boundary (module_graph declares klein N/A)")
    # THE downgrade: the kernel earns MEASURED_BY_INTERVENTION; static extraction cannot — it can never be more than DECLARED.
    cells["identifiability"] = Cell(
        "DECLARED", DECLARED,
        "causal necessity requires running the code / its tests (intervention); static extraction cannot replay "
        "— observation ≠ intervention. The kernel can MEASURE_BY_INTERVENTION; static evidence is DOWNGRADED to DECLARED")
    return cells


def candidate_risk(diag: dict, dotted: str, cycle) -> list:
    """Forward-matrix risks the STATIC extractor can support — MEASURED where structural, DECLARED where the
    extraction is blind. Routes attention; never a verdict."""
    edges, dyn = diag["edges"], _dynamic_modules(diag)
    risks = []
    indeg = _indeg(edges, dotted)
    if indeg >= HIGH_FAN_IN:
        risks.append(Cell("HIGH_FAN_IN", MEASURED, f"in-degree={indeg} — blast-radius concentration (review target)"))
    if cycle and dotted in cycle:
        risks.append(Cell("IN_DEPENDENCY_CYCLE", MEASURED, f"participates in import cycle {cycle} — resilience/DoS surface"))
    if dotted in dyn:
        risks.append(Cell("UNRESOLVED_DEPENDENCY", DECLARED,
                          "dynamic import (__import__/import_module) — dependency surface incomplete, not assessable statically"))
    return risks


def epistemic_coverage(diag: dict) -> dict:
    """The honest repo-level rollup: of all module×axis cells, how many are actually MEASURED vs owed vs N/A.
    No scalar risk score — just how much this extraction genuinely knows."""
    tally = {MEASURED: 0, DECLARED: 0, NOT_APPLICABLE: 0}
    for m in diag["known"]:
        for c in repo_status(diag, m).values():
            tally[c.status] = tally.get(c.status, 0) + 1
    return tally


def render(diag: dict, dotted: str, cycle) -> None:
    cells = repo_status(diag, dotted)
    print(f"repo_status({dotted!r}):")
    for ax in _AXES:
        c = cells[ax]
        print(f"    {ax:<16} {c.value:<14} [{c.status}]")
        print(f"        └ {c.evidence}")
    risks = candidate_risk(diag, dotted, cycle)
    print("    candidate risk:" + ("" if risks else " none"))
    for r in risks:
        print(f"        · {r.value:<22} [{r.status}] {r.evidence}")
    print()


def main() -> None:
    import os
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    diag = fg.diagnose(root)
    cycle = mg.find_cycle(diag["known"], diag["edges"])

    print("repo_status — the convergence object fed by a REAL extraction; epistemic types DOWNGRADED to match")
    print("static evidence (the kernel can replay; a parser cannot). No scalar, no verdict.\n")
    print(f"extracted: {root}  ({len(diag['known'])} modules, {len(diag['edges'])} edges)\n")

    # pick the highest fan-in module to show (the most load-bearing), plus one leaf
    by_indeg = sorted(diag["known"], key=lambda m: _indeg(diag["edges"], m), reverse=True)
    if by_indeg:
        render(diag, by_indeg[0], cycle)
    if len(by_indeg) > 1:
        render(diag, by_indeg[-1], cycle)

    cov = epistemic_coverage(diag)
    total = sum(cov.values()) or 1
    print(f"  epistemic coverage over {len(diag['known'])} modules × {len(_AXES)} axes:")
    print(f"    MEASURED {cov[MEASURED]}  ·  DECLARED {cov[DECLARED]}  ·  N/A {cov[NOT_APPLICABLE]}")
    print(f"    static extraction genuinely measures ~{100*cov[MEASURED]//total}% of the axis-cells; the rest is "
          f"owed or inapplicable — and the object SAYS SO rather than fabricating it.\n")

    # ---- self-test: the downgrade is the discipline; the first success is that nothing was upgraded ----
    passed = total_c = 0

    def check(name, ok, detail=""):
        nonlocal passed, total_c
        total_c += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<36} {detail}")

    sample = by_indeg[0] if by_indeg else None
    cells = repo_status(diag, sample) if sample else {}

    # 1. THE headline discipline check: MEASURED_BY_INTERVENTION appears NOWHERE — static never earns the kernel's strength
    all_statuses = {c.status for m in diag["known"] for c in repo_status(diag, m).values()}
    check("no_kernel_strength_on_static", "MEASURED_BY_INTERVENTION" not in all_statuses,
          "no cell claims MEASURED_BY_INTERVENTION over static evidence — provenance downgraded, never inherited")

    # 2. identifiability specifically downgraded to DECLARED with the 'cannot replay' reason
    idc = cells.get("identifiability")
    check("identifiability_downgraded", bool(idc) and idc.status == DECLARED and "cannot replay" in idc.evidence,
          "identifiability = DECLARED (static cannot replay), NOT MEASURED_BY_INTERVENTION like the kernel")

    # 3. dependency is MEASURED but flagged a LOWER BOUND (dynamic importers invisible)
    dep = cells.get("dependency")
    check("dependency_is_lower_bound", bool(dep) and dep.status == MEASURED and "LOWER BOUND" in dep.evidence,
          "in-degree reported as a static lower bound, not a complete dependency claim")

    # 4. static-inapplicable axes are N/A (not DECLARED, not MEASURED)
    check("static_axes_na",
          cells.get("durability").status == NOT_APPLICABLE
          and cells.get("authority").status == NOT_APPLICABLE
          and cells.get("orientability").status == NOT_APPLICABLE,
          "durability / authority / orientability = N/A (inapplicable to a static import graph)")

    # 5. blind spots PROPAGATE: a synthetic dynamic-import module downgrades dependency + raises UNRESOLVED_DEPENDENCY
    syn = {"known": {"m", "x"}, "edges": {("m", "x")},
           "piles": {"runtime_frontier": [("m", "dynamic import (__import__)")]}}
    syn_dep = repo_status(syn, "m")["dependency"]
    syn_risk = {r.value for r in candidate_risk(syn, "m", None)}
    check("blind_spots_propagate",
          "incomplete" in syn_dep.evidence and "UNRESOLVED_DEPENDENCY" in syn_risk,
          "a module with a dynamic import → outbound deps flagged incomplete + UNRESOLVED_DEPENDENCY [DECLARED]")

    # 6. the bridge does not diverge from its source (in-degree matches the extractor's edges)
    if sample:
        direct = sum(1 for (_u, v) in diag["edges"] if v == sample)
        match = (dep.value == ("IRREVERSIBLE" if direct > 0 else "REVERSIBLE"))
    else:
        match = True
    check("matches_extractor", match, "dependency cell agrees with a direct count over the extractor's edges")

    # 7. no scalar — epistemic coverage is a partition by provenance, never a risk score
    check("no_scalar_only_coverage", set(cov) <= {MEASURED, DECLARED, NOT_APPLICABLE},
          "repo-level rollup is a {MEASURED/DECLARED/N/A} partition, never a 'risk score'")

    print(f"\n{passed}/{total_c} checks. Epistemic provenance SURVIVED contact with reality — by getting weaker,")
    print("honestly. Fed a real extraction, the convergence object reports what static analysis can actually")
    print("support (presence, a lower-bound dependency, structural risks) and DOWNGRADES the rest: identifiability")
    print("falls from MEASURED_BY_INTERVENTION to DECLARED because a parser cannot replay; durability/authority/")
    print("orientability are N/A; dynamic-import blind spots propagate as DECLARED, never silently resolved. The")
    print("kernel's strongest label appears NOWHERE over static evidence. `declared ≠ verified`: the object audits")
    print("not just the system, but the provenance of every claim it makes about the system.")
    assert passed == total_c, "repo_status failed its own self-test"


if __name__ == "__main__":
    main()
