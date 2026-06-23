# SPDX-License-Identifier: AGPL-3.0-only
"""
witness_panel.py — one fact, many witnesses: the architecture as a LATTICE, not a hierarchy.

`reality_status` put every boundary on one fact from ONE witness (the kernel). This puts one fact under
SEVERAL witness classes at once — static extraction, runtime trace, replay/intervention — and reconciles them
PER AXIS. The point is the property you can only see with ≥2 witness classes present:

    evidence strength is PARTIALLY ordered, not totally ordered.

No witness is globally strongest. Static dominates "declared coverage" (it sees dead/un-exercised edges nothing
else does); runtime dominates "execution reality" (it sees dynamic behaviour invisible statically); replay
dominates "identifiability" (only do(¬x) establishes causal necessity). The reconciler is not choosing a winner —
it preserves the strongest *justified* claim available **for each axis** and records the rest, and an absent
witness is first-class, not a blank.

THE LAW THIS MUST OBEY while absorbing a new witness class (the key test):
    no downstream (reconciled) claim may be stronger than the witness that produced it.
i.e. for every axis, STRENGTH[reconciled] ≤ max(STRENGTH[witnesses that spoke]); adding a witness may REFINE
(equal strength, better value) or EXTEND coverage (a new axis), but may NEVER inflate strength. If that holds,
the framework scales HORIZONTALLY across witness types, not just vertically across representations.

This file's verified core is the per-axis reconciliation + the law + the partial order (synthetic witnesses,
7/7). A small real panel (static via `repo_status`, runtime/replay shown ABSENT) is printed for illustration.
`declared ≠ verified`.

Run (from this directory):  PYTHONHASHSEED=0 python3 witness_panel.py
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import fidelity_gap as fg
import repo_status as rs
from reality_status import Cell, MEASURED, MEASURED_BY_INTERVENTION, DECLARED, NOT_APPLICABLE
from reconcile_status import reconcile_cell, STRENGTH, CONTESTED


@dataclass
class Witness:
    """A named evidence channel. `cells` maps axis -> (Cell, rank). An axis NOT in `cells` means this witness
    is SILENT on it (recorded as absent — never a denial)."""
    name: str
    cells: dict   # axis -> (Cell, rank)

    def speaks(self, axis) -> bool:
        return axis in self.cells


def panel(witnesses: list, axes: list) -> dict:
    """One fact through many witnesses, reconciled per axis. Pure. Absent witnesses recorded, never dropped."""
    rows = {}
    for axis in axes:
        contribs = [(w.name, w.cells[axis][0], w.cells[axis][1]) for w in witnesses if w.speaks(axis)]
        absent = [w.name for w in witnesses if not w.speaks(axis)]
        reconciled = reconcile_cell(contribs) if contribs else Cell("N/A", NOT_APPLICABLE, "no witness speaks this axis")
        rows[axis] = {"contribs": contribs, "absent": absent, "reconciled": reconciled}
    return rows


def render(title: str, rows: dict, axes: list) -> None:
    print(title)
    for axis in axes:
        r = rows[axis]
        rec = r["reconciled"]
        seen = ", ".join(f"{n}={c.value}[{c.status}]" for (n, c, _rk) in r["contribs"]) or "—"
        absent = f"   absent: {r['absent']}" if r["absent"] else ""
        print(f"  {axis:<18} → {rec.value} [{rec.status}]")
        print(f"      witnesses: {seen}{absent}")
        print(f"      └ {rec.evidence}")
    print()


def _static_witness_from_repo(root: str, dotted: str) -> Witness:
    """A real static witness: repo_status cells (drop N/A → silent on those axes). MEASURED ranks 2, DECLARED 1."""
    diag = fg.diagnose(root)
    cells = {}
    for axis, c in rs.repo_status(diag, dotted).items():
        if c.status != NOT_APPLICABLE:
            cells[axis] = (c, 2 if c.status in (MEASURED, MEASURED_BY_INTERVENTION) else 1)
    return Witness("static", cells)


def main() -> None:
    print("witness_panel — one fact, many witnesses; reconciled PER AXIS. Partial order, not a hierarchy.\n")

    # ---- a small REAL panel: static (repo_status) present; runtime + replay first-class ABSENT ----
    here = os.path.dirname(os.path.abspath(__file__))
    static_real = _static_witness_from_repo(here, "concurrency_probe")
    runtime_absent = Witness("runtime", {})     # not traced this run → silent on every axis
    replay_absent = Witness("replay", {})       # no replay witness in the repo domain → silent
    real_axes = ["commitment", "dependency", "identifiability"]
    real_rows = panel([static_real, runtime_absent, replay_absent], real_axes)
    render("real panel — module 'concurrency_probe' (static present; runtime/replay ABSENT):", real_rows, real_axes)

    # ---- the synthetic panel that exhibits the PARTIAL ORDER (different witness tops each axis) ----
    static = Witness("static", {
        "dependency":        (Cell("REVERSIBLE", MEASURED, "no declared importer"), 1),
        "declared_coverage": (Cell("COMPLETE", MEASURED, "sees all declared edges incl. dead/un-exercised"), 3),
        "identifiability":   (Cell("DECLARED", DECLARED, "cannot replay"), 0),
    })
    runtime = Witness("runtime", {
        "dependency":        (Cell("IRREVERSIBLE", MEASURED, "import OBSERVED at load time"), 2),
        "execution_reality": (Cell("OBSERVED", MEASURED, "saw actual load-time imports, incl. dynamic"), 3),
    })
    replay = Witness("replay", {
        "identifiability":   (Cell("NECESSARY", MEASURED_BY_INTERVENTION, "do(¬x) changes the world"), 3),
        "dependency":        (Cell("IRREVERSIBLE", MEASURED, "committed dependent"), 2),
    })
    axes = ["dependency", "declared_coverage", "execution_reality", "identifiability"]
    rows = panel([static, runtime, replay], axes)
    render("synthetic panel — three witness classes, four axes (no global winner):", rows, axes)

    # ------------------------------ self-test: the partial-order LAW ------------------------------
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<36} {detail}")

    def law_holds(rws):
        for r in rws.values():
            if r["contribs"]:
                if STRENGTH[r["reconciled"].status] > max(STRENGTH[c.status] for (_n, c, _rk) in r["contribs"]):
                    return False
        return True

    # 1. THE law: no reconciled claim stronger than the witness that produced it
    check("no_downstream_inflation", law_holds(rows),
          "∀axis STRENGTH[reconciled] ≤ max(STRENGTH[witnesses]) — downstream never exceeds its source")

    # 2. PARTIAL order: a different witness is top on each of three axes (no total order)
    check("partial_order_no_global_winner",
          rows["declared_coverage"]["reconciled"].value == "COMPLETE"          # static tops here
          and rows["execution_reality"]["reconciled"].value == "OBSERVED"      # runtime tops here
          and rows["identifiability"]["reconciled"].status == MEASURED_BY_INTERVENTION,  # replay tops here
          "static wins declared_coverage, runtime wins execution_reality, replay wins identifiability")

    # 3. absent witnesses are FIRST-CLASS, not blanks
    check("absent_is_first_class",
          "runtime" in rows["identifiability"]["absent"] and "static" in rows["execution_reality"]["absent"],
          "an axis a witness does not speak records it as absent — recorded, never dropped")

    # 4. ABSORB a new witness class without breaking the law (horizontal scaling)
    weak = Witness("static2", {"dependency": (Cell("REVERSIBLE", MEASURED, "weaker, lower coverage"), 1)})
    rows2 = panel([static, runtime, replay, weak], axes)
    check("absorbs_new_witness_preserves_law",
          law_holds(rows2) and rows2["dependency"]["reconciled"].value == "IRREVERSIBLE",
          "adding a witness keeps the law; a weaker one cannot lower the dominant claim (monotone)")

    # 5. refinement, NOT forced conflict (the two informative panel states from your sketch)
    silent = Witness("runtime_silent", {})
    only_static = panel([static, silent], ["dependency"])["dependency"]
    check("refinement_not_conflict",
          rows["dependency"]["reconciled"].status != CONTESTED
          and only_static["reconciled"].value == "REVERSIBLE" and "runtime_silent" in only_static["absent"],
          "static+runtime disagreement → refinement (not CONTESTED); a silent witness → recorded absent, static holds")

    # 6. the CENTRAL CLAIM: every reconciled claim's strength is one a witness actually earned (never invented)
    attached = all(rows[a]["reconciled"].status in {c.status for (_n, c, _rk) in rows[a]["contribs"]}
                   for a in axes if rows[a]["contribs"])
    check("claim_attached_to_earning_witness", attached,
          "reconciled strength ∈ the strengths witnesses supplied — never a status no witness earned")

    # 7. partial order FORMALIZED: static is top on one axis yet dominated on another → strength is not total
    static_tops_coverage = rows["declared_coverage"]["reconciled"].value == "COMPLETE"
    static_dominated_ident = rows["identifiability"]["reconciled"].status == MEASURED_BY_INTERVENTION  # replay, not static
    check("strength_is_partial_not_total", static_tops_coverage and static_dominated_ident,
          "the same witness (static) is strongest on declared_coverage and dominated on identifiability")

    print(f"\n{passed}/{total} checks. One fact, many witnesses, reconciled per axis — and the architecture is a")
    print("LATTICE, not a hierarchy: no witness is globally strongest (static owns declared coverage, runtime owns")
    print("execution reality, replay owns identifiability), so evidence strength is PARTIALLY ordered. A new witness")
    print("class is absorbed without any reconciled claim exceeding the witness that earned it (the law holds before")
    print("and after), absent witnesses are first-class, and disagreement between honest witnesses is refinement,")
    print("not forced conflict. The panel is not a dashboard — it is the live demonstration that every claim stays")
    print("attached to the strongest evidence that actually earned it, even as more witnesses are added. `declared ≠ verified`.")
    assert passed == total, "witness_panel failed its partial-order self-test"


if __name__ == "__main__":
    main()
