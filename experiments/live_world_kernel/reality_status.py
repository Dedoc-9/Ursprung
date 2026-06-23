# SPDX-License-Identifier: AGPL-3.0-only
"""
reality_status.py — the convergence object: every boundary, evaluated on the SAME committed fact.

The boundary docs each ask "can this happen?"; the failure matrix asks "which boundary am I hitting?". This is
the place all of them meet on one object: given a committed `event_id`, return a STRUCTURED STATE VECTOR — for
each boundary, where this fact currently stands. No scalar score. No verdict. Just the vector, and — the move
that makes this more than an observability dashboard — **each cell carries the provenance of its own verdict.**

    every cell reports HOW it knows, not just WHAT it says:
        MEASURED                 a real computation ran on the kernel's committed state
        MEASURED_BY_INTERVENTION a replay / do(¬eid) ran (necessity is an intervention, not an observation)
        DECLARED                 the axis applies but no probe is built yet — returns the contract pointer,
                                 NEVER a fabricated verdict (`declared ≠ verified`; a dashboard that fills
                                 unmeasured cells with green is the dashboard that lies)
        N/A                      the axis does not apply to this event

Of the seven axes, FOUR are live today (the kernel computes them) and THREE are `DECLARED` — their probes are
contracts, not code (SELF_MODIFICATION / AUTHORITY_ARBITRAGE / ADJUDICATION_THROUGHPUT boundary docs). This file
is therefore the convergence object made HONEST: real where real, declared where not, and it says which is which
on every cell. It becomes a complete diagnostic language only as those probes are built — and it will not pretend
otherwise in the meantime.

Run (from this directory):  PYTHONHASHSEED=0 python3 reality_status.py
"""
from __future__ import annotations

from dataclasses import dataclass

import live_world_kernel as lwk   # the kernel that actually computes commitment / dependency / durability

MEASURED = "MEASURED"
MEASURED_BY_INTERVENTION = "MEASURED_BY_INTERVENTION"
DECLARED = "DECLARED"            # axis applies, no probe yet — a pointer, never a verdict
NOT_APPLICABLE = "N/A"

_MEASURED = (MEASURED, MEASURED_BY_INTERVENTION)
_ALL_STATUSES = (MEASURED, MEASURED_BY_INTERVENTION, DECLARED, NOT_APPLICABLE)


@dataclass(frozen=True)
class Cell:
    """One boundary's standing on one fact — value plus the provenance of that value."""
    value: str
    status: str          # one of _ALL_STATUSES — the cell never omits how it knows
    evidence: str


def _find(k: lwk.Kernel, eid: str):
    return next((e for e in k.committed if e.eid == eid), None)


def _necessary(k: lwk.Kernel, eid: str) -> bool:
    """Causal necessity BY INTERVENTION: do(¬eid) on the committed log and replay. NECESSARY iff removing the
    fact (and its causal subtree) changes the committed world. This is a real intervention the log permits —
    distinct from the deep latent identifiability limit (hidden confounders) which observation cannot resolve."""
    full = lwk.project(k.committed)
    doomed = lwk.causal_closure(k.committed, {eid})
    without = lwk.project([e for e in k.committed if e.eid not in doomed])
    return full != without


def _orientability_cell(k: lwk.Kernel, eid: str) -> Cell:
    ev = _find(k, eid)
    if ev is None:
        return Cell("N/A", NOT_APPLICABLE, "event not in committed log")
    # a self-modification of the authority/provenance mechanism is the ONLY place orientability applies.
    # this kernel gates grant/revoke to the root, so no actor edits the authority it is subject to → N/A here.
    self_mod = ev.op in ("grant", "revoke") and ev.author != lwk.ROOT
    if self_mod:
        return Cell("DECLARED", DECLARED,
                    "self-modification of authority — orientability applies; probe not built "
                    "(see SELF_MODIFICATION_BOUNDARY.md)")
    return Cell("N/A", NOT_APPLICABLE,
                "event does not modify the authority/provenance mechanism — orientability inapplicable")


def reality_status(k: lwk.Kernel, eid: str) -> dict:
    """The convergence object. Returns {axis: Cell}. No scalar, no verdict; every cell self-reports provenance."""
    cells: dict[str, Cell] = {}
    committed = k.is_committed(eid)

    cells["commitment"] = Cell(
        "COMMITTED" if committed else "ABSENT", MEASURED,
        f"t_commit={k.t_commit.get(eid)}" if committed else "no commit record")

    if committed:
        irr = k.is_irreversible(eid)
        dependents = [e.eid for e in k.committed if eid in e.deps]
        cells["dependency"] = Cell(
            "IRREVERSIBLE" if irr else "REVERSIBLE", MEASURED,
            f"committed dependents={dependents}; t_dep={k.t_dep.get(eid)}")

        paths = k.recovery_paths(eid, {"primary"})
        cells["durability"] = Cell(
            "DURABLE" if paths else "FRAGILE", MEASURED,
            f"recovery paths independent of primary loss = {paths}")

        nec = _necessary(k, eid)
        cells["identifiability"] = Cell(
            "NECESSARY" if nec else "INERT", MEASURED_BY_INTERVENTION,
            ("do(¬closure) replay changes the committed world — causally necessary to current state"
             if nec else
             "do(¬closure) replay leaves the committed world unchanged — stable but inert (stable ≠ causal)")
            + " | note: deep latent identifiability (hidden confounder) is N/A — a fully-logged log permits do()")
    else:
        for ax in ("dependency", "durability", "identifiability"):
            cells[ax] = Cell("N/A", NOT_APPLICABLE, "fact not committed — downstream states undefined")

    # ---- the three axes whose probes are contracts, not code: DECLARED, never a fabricated verdict ----
    cells["authority"] = Cell(
        "DECLARED", DECLARED,
        "advantage reconstructability — adjudicator probe not built (see AUTHORITY_ARBITRAGE_BOUNDARY.md)")
    cells["verification"] = Cell(
        "DECLARED", DECLARED,
        "the kernel has t_commit/t_dep but NO t_verified (commit checks authority, not a floor); the "
        "commitment-vs-verification race is unmeasurable here (see ADJUDICATION_THROUGHPUT_BOUNDARY.md)")
    cells["orientability"] = _orientability_cell(k, eid)
    return cells


def candidate_risk(cells: dict) -> list:
    """Forward-matrix risks for this fact — MEASURED where the kernel supports it, DECLARED where it can't.
    Routes attention; never a verdict (FAILURE_MODE_MATRIX.md)."""
    risks = []
    if cells["dependency"].value == "IRREVERSIBLE" and cells["durability"].value == "FRAGILE":
        risks.append(Cell(
            "IRREVERSIBLE_AND_FRAGILE", MEASURED,
            "load-bearing but single-copy: a primary loss is permanent — SEVERED on a depended-on fact"))
    # the FLOODED→SEVERED cascade needs t_verified, which the kernel does not have → cannot be assessed
    risks.append(Cell(
        "FLOODED_CASCADE", DECLARED,
        "verification unmeasured (no t_verified) — FLOODED→SEVERED cascade risk cannot be assessed"))
    return risks


def summarize(cells: dict) -> dict:
    """The ONLY honest rollup: what is actually known vs not. No scalar; partition by provenance."""
    return {
        "measured": sorted(ax for ax, c in cells.items() if c.status in _MEASURED),
        "declared_pending": sorted(ax for ax, c in cells.items() if c.status == DECLARED),
        "not_applicable": sorted(ax for ax, c in cells.items() if c.status == NOT_APPLICABLE),
    }


_AXES = ("commitment", "dependency", "durability", "authority", "verification", "orientability", "identifiability")


def render(k: lwk.Kernel, eid: str) -> None:
    cells = reality_status(k, eid)
    print(f"reality_status({eid!r}):")
    for ax in _AXES:
        c = cells[ax]
        print(f"    {ax:<16} {c.value:<22} [{c.status}]")
        print(f"        └ {c.evidence}")
    print("    candidate risk:")
    for r in candidate_risk(cells):
        print(f"        · {r.value:<26} [{r.status}] {r.evidence}")
    s = summarize(cells)
    print(f"    KNOWN: {s['measured']}   PENDING: {s['declared_pending']}   N/A: {s['not_applicable']}")
    print()


def _scenario() -> lwk.Kernel:
    """A small committed world exercising each MEASURED axis (mirrors the kernel's own self-test world)."""
    k = lwk.Kernel()
    k.commit(lwk.EditEvent("g1", lwk.ROOT, "terrain.modify", "builderA", "grant"))
    k.commit(lwk.EditEvent("a1", "builderA", "terrain.modify", "stone", "create", (("x", 1),)))
    k.commit(lwk.EditEvent("a2", "builderA", "terrain.modify", "moss", "create", (("on", "stone"),), ("a1",)))
    k.replicate("a2", "node_b")                                   # a2 → durable via independent replica
    k.commit(lwk.EditEvent("a3", "builderA", "terrain.modify", "tree", "create", (("seed", 42),)))
    k.declare_regenerable("a3", {"seed_store"})                   # a3 → durable via regeneration, no deps
    k.commit(lwk.EditEvent("a4", "builderA", "terrain.modify", "hut", "create", (("x", 9),)))
    k.commit(lwk.EditEvent("a6", "builderA", "terrain.modify", "hut", "delete"))   # erases a4's effect → a4 inert
    return k


def main() -> None:
    k = _scenario()

    print("reality_status — every boundary on the SAME committed fact; each cell reports how it knows.")
    print("4 axes live (kernel), 3 DECLARED (probes are contracts). No scalar, no verdict.\n")
    render(k, "a1")   # the instructive one: irreversible AND fragile
    render(k, "a4")   # committed but causally INERT (stable ≠ causal)

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<38} {detail}")

    a1 = reality_status(k, "a1")
    a4 = reality_status(k, "a4")

    # 1. THE discipline gate (first success is negative): every cell self-reports its provenance — the
    #    aggregator never emits a value without saying how it knows.
    every_cell_provenanced = all(c.status in _ALL_STATUSES for c in a1.values()) and len(a1) == len(_AXES)
    check("self_provenance_complete", every_cell_provenanced,
          "every cell carries a status in {MEASURED, MEASURED_BY_INTERVENTION, DECLARED, N/A}")

    # 2. unbuilt axes are DECLARED, NEVER faked into a verdict (the dashboard-that-lies guard)
    check("unbuilt_axes_declared_not_faked",
          a1["authority"].status == DECLARED and a1["verification"].status == DECLARED
          and a1["authority"].value == "DECLARED" and a1["verification"].value == "DECLARED",
          "authority + verification return DECLARED, not RECONSTRUCTABLE/VERIFIED — no probe, no verdict")

    # 3. measured axes match the kernel's own primitives (the aggregator does not diverge from its source)
    check("measured_axes_match_kernel",
          a1["commitment"].value == ("COMMITTED" if k.is_committed("a1") else "ABSENT")
          and (a1["dependency"].value == "IRREVERSIBLE") == k.is_irreversible("a1"),
          "commitment/dependency cells equal is_committed/is_irreversible")

    # 4. N/A is DISTINCT from DECLARED — orientability does not apply to an ordinary edit (vs no-probe-yet)
    check("na_distinct_from_declared",
          a1["orientability"].status == NOT_APPLICABLE and a1["authority"].status == DECLARED,
          "orientability N/A (event is not a self-modification) ≠ authority DECLARED (probe missing)")

    # 5. durability MEASURED, and a fragile fact is reported honestly (not assumed safe)
    check("durability_measured_severance_honest",
          a1["durability"].value == "FRAGILE" and reality_status(k, "a2")["durability"].value == "DURABLE",
          "a1 primary-only → FRAGILE; a2 (replicated) → DURABLE")

    # 6. identifiability BY INTERVENTION: a necessary fact vs a stable-but-inert one (stable ≠ causal)
    check("identifiability_by_intervention",
          a1["identifiability"].value == "NECESSARY" and a4["identifiability"].value == "INERT"
          and a1["identifiability"].status == MEASURED_BY_INTERVENTION,
          "a1 changes the world under do(¬closure) → NECESSARY; a4's effect was erased → INERT")

    # 7. no scalar, no verdict — and the measurable forward-matrix risk surfaces for a1
    risks_a1 = {r.value for r in candidate_risk(a1)}
    no_scalar = not any(k_ in a1 for k_ in ("score", "health", "reality_score"))
    check("no_scalar_measured_risk_surfaces",
          no_scalar and "IRREVERSIBLE_AND_FRAGILE" in risks_a1,
          "no reality-score anywhere; a1 flagged IRREVERSIBLE_AND_FRAGILE (MEASURED), FLOODED_CASCADE stays DECLARED")

    print(f"\n{passed}/{total} checks. The convergence object holds: for one committed fact, every boundary is")
    print("evaluated on the same object and each cell says HOW it knows — four axes MEASURED on the kernel")
    print("(commitment, dependency, durability) plus one BY INTERVENTION (identifiability via do(¬eid) replay),")
    print("and three DECLARED because their probes are contracts, not code. It refuses to fabricate the unmeasured")
    print("cells (no green-by-default), keeps no scalar and issues no verdict, and surfaces only the forward-matrix")
    print("risk the kernel can actually support. This is where the boundaries first meet on one object — honest")
    print("about which are measured and which are still owed. `declared ≠ verified`; it tells you where to look.")
    assert passed == total, "reality_status failed its own self-test"


if __name__ == "__main__":
    main()
