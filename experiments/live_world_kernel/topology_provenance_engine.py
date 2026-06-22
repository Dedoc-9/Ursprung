# SPDX-License-Identifier: AGPL-3.0-only
"""
topology_provenance_engine.py — bundle the three diagnostic probes into one audit over a shared system model.

It runs all three VERIFIED reference probes over a SINGLE declared description of a system's data flows and
reports three INDEPENDENT coherence dimensions:

    structural  (klein_probe)        — do the system's boundaries cohere, or is some local boundary a false
                                       global claim?  ORIENTABLE / NON_ORIENTABLE
    provenance  (frontier_probe)     — where does possibility become obligation; did a dependency outrun
                                       commitment?  ALIGNED / NEEDS_PROMOTION / OBSERVER_DEPENDENT
    spatial     (concurrency_probe)  — is a chosen partition a clean gauge or a semantic leak?
                                       GOOD_GAUGE / GAUGE_WITH_COST / SEMANTIC_LEAK

THE DISCIPLINE IT INHERITS — and the one feature that makes it faithful rather than a dashboard that lies:
it REFUSES to collapse the three dimensions into a single "coherence score." Objectivity is not one scalar
(the whole project's stance). The report is a VECTOR of three categorical verdicts plus per-axis attention
flags; the only legitimate rollup is the unweighted conjunction "all axes clean?", never a weighted number.

It also inherits: observe, do NOT enforce; apparatus, NO verdict (it surfaces attention signals — "look here"
— never "this is broken/safe", never "merge/fix"); pure (rerunning the audit changes nothing).

HONEST SCOPE. "Continuous" is a USAGE (run it per-commit / in CI), not a new runtime — this is a single-pass
harness. The encodings — which boundaries become signed edges, which ops the flow contains, which partition —
are DECLARED models (`declared ≠ verified`). A clean audit means "no attention signal under this declared
model," never `safe` (`tested ≠ safe`). It bundles three reference instruments; resemblance to industrial
tooling is resonance, not validation.

Run (from this directory):  PYTHONHASHSEED=0 python3 topology_provenance_engine.py
"""
from __future__ import annotations

from dataclasses import dataclass

import klein_probe as kp          # structural: orientability of boundaries
import frontier_probe as fp       # provenance: where possibility becomes obligation
import concurrency_probe as cp    # spatial: partition leakage / convergence

AXES = ("structural", "provenance", "spatial")
CLEAN = {"structural": "ORIENTABLE", "provenance": "ALIGNED", "spatial": "GOOD_GAUGE"}


@dataclass
class SystemModel:
    """One declared description of a system's data flows, fed to all three lenses."""
    name: str
    boundaries: list                 # klein signed edges: (u, v, sign, boundary_name)
    flow: list                       # frontier ops: [(method_name, *args), ...] applied to a Runtime
    deps: list                       # concurrency dependency edges: (premise, dependent)
    partition: dict                  # concurrency: element -> region
    budget: int = 1                  # reconciliation budget per tick
    load: int = 0                    # new cross-boundary deps per tick (0 = quiescent)
    horizon: int = 5


def audit(m: SystemModel) -> dict:
    """Run the three probes over the one model. Pure: builds fresh probe state, mutates nothing in `m`."""
    # structural — orientability of the boundary set (klein_probe)
    structural = kp.classify(m.boundaries)

    # provenance — replay the declared flow through a fresh frontier Runtime, then classify (frontier_probe)
    rt = fp.Runtime()
    for op in m.flow:
        getattr(rt, op[0])(*op[1:])
    provenance = fp.classify(rt)

    # spatial — leakage + convergence of the chosen partition (concurrency_probe)
    cross, rate = cp.leakage(m.deps, m.partition)
    trace = (cp.settle_under_load(len(cross), m.load, m.budget, m.horizon) if m.load > 0
             else cp.settle_quiescent(len(cross), m.budget))
    spatial = cp.classify(rate, cp.converged(trace))

    return {"structural": structural, "provenance": provenance, "spatial": spatial,
            "leak_rate": rate, "contradictions": len(rt.contradictions)}
    # NOTE: deliberately no "score" / "health" scalar. Three independent dimensions, never one number.


def attention(report: dict) -> list:
    """The axes not in their clean state — 'look here', NOT 'broken'. A surfaced signal, never a verdict."""
    return [ax for ax in AXES if report[ax] != CLEAN[ax]]


def clean_vector(report: dict) -> tuple:
    """Per-axis clean/attention as a 3-tuple of bools — a VECTOR, never collapsed to a scalar."""
    return tuple(report[ax] == CLEAN[ax] for ax in AXES)


# ---------------------------------------------------------------------------------------------------
# Three system models: coherent (all axes clean), fragile (all flagged), orthogonal (axes are independent).
# ---------------------------------------------------------------------------------------------------
ALIGNED_FLOW = [("new_candidate", "tree"), ("mutate", "tree"), ("promote", "tree"), ("derived_commit", "nav", "tree")]
NEEDS_PROMO_FLOW = [("new_candidate", "tree"), ("derived_commit", "nav", "tree"), ("mutate", "tree")]
WHOLE = {"a": "R0", "b": "R0", "c": "R0", "d": "R0"}                 # cluster kept whole → no leak
SPLIT = {"a": "R0", "b": "R0", "c": "R1", "d": "R1"}                 # cuts b→c → leak
CLUSTER = [("a", "b"), ("b", "c"), ("c", "d")]

COHERENT = SystemModel("coherent", kp.COHERENT, ALIGNED_FLOW, CLUSTER, WHOLE, budget=1, load=0)
FRAGILE = SystemModel("fragile", kp.OBSERVER, NEEDS_PROMO_FLOW, CLUSTER, SPLIT, budget=1, load=3)
ORTHOGONAL = SystemModel("orthogonal", kp.COHERENT, ALIGNED_FLOW, CLUSTER, SPLIT, budget=1, load=3)


def main() -> None:
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<36} {detail}")

    print("topology_provenance_engine — three independent coherence lenses over one system model.")
    print("structural ⟂ provenance ⟂ spatial. A vector, never a score. Observe, not enforce; no verdict.\n")

    models = [COHERENT, FRAGILE, ORTHOGONAL]
    reports = {m.name: audit(m) for m in models}

    print(f"  {'model':<12} {'structural':<16} {'provenance':<17} {'spatial':<16} attention")
    for m in models:
        r = reports[m.name]
        print(f"  {m.name:<12} {r['structural']:<16} {r['provenance']:<17} {r['spatial']:<16} {attention(r) or 'none'}")
    print()

    # 1. one model, three lenses — the integration: a single description audited three ways
    rc = reports["coherent"]
    check("integrates_three_lenses", all(ax in rc for ax in AXES) and rc["structural"] and rc["provenance"] and rc["spatial"],
          "a single SystemModel yields structural + provenance + spatial verdicts together")

    # 2. coherent system is clean on every axis
    check("coherent_clean_all_axes",
          rc["structural"] == "ORIENTABLE" and rc["provenance"] == "ALIGNED" and rc["spatial"] == "GOOD_GAUGE"
          and attention(rc) == [],
          "ORIENTABLE / ALIGNED / GOOD_GAUGE — no attention signal")

    # 3. fragile system raises every axis
    rf = reports["fragile"]
    check("fragile_flags_all_axes",
          rf["structural"] == "NON_ORIENTABLE" and rf["provenance"] == "NEEDS_PROMOTION" and rf["spatial"] == "SEMANTIC_LEAK"
          and set(attention(rf)) == set(AXES),
          "NON_ORIENTABLE / NEEDS_PROMOTION / SEMANTIC_LEAK — all three flagged")

    # 4. the axes are INDEPENDENT — one red among greens (you need all three; no axis implies another)
    ro = reports["orthogonal"]
    check("axes_are_independent",
          ro["structural"] == "ORIENTABLE" and ro["provenance"] == "ALIGNED" and ro["spatial"] == "SEMANTIC_LEAK"
          and attention(ro) == ["spatial"],
          "structural+provenance clean, spatial fragile — coherence is a vector, not a single property")

    # 5. the engine REUSES the verified probes (does not reimplement or diverge from them)
    consistent = (reports["fragile"]["structural"] == kp.classify(FRAGILE.boundaries)
                  and reports["coherent"]["spatial"] == cp.classify(*_spatial_inputs(COHERENT)))
    check("reuses_verified_probes", consistent,
          "engine verdicts == the underlying probe verdicts — it bundles, never re-derives")

    # 6. pure / sealed / no verdict — rerun is identical, model untouched, outputs are labels not directives
    before = audit(FRAGILE)
    again = audit(FRAGILE)
    label_pool = {"ORIENTABLE", "NON_ORIENTABLE", "ALIGNED", "NEEDS_PROMOTION", "OBSERVER_DEPENDENT",
                  "GOOD_GAUGE", "GAUGE_WITH_COST", "SEMANTIC_LEAK"}
    no_directive = all(before[ax] in label_pool for ax in AXES)  # never 'safe' / 'fix' / 'merge'
    check("pure_sealed_no_verdict", before == again and no_directive,
          "rerun identical; outputs are classifications, never 'safe' / 'fix' / 'merge'")

    # 7. NO scalar collapse — the report is a 3-vector; the only rollup is the unweighted conjunction
    has_no_score = not any(k in reports["fragile"] for k in ("score", "health", "coherence_score"))
    vec = clean_vector(reports["orthogonal"])
    all_clean = all(vec)  # the ONLY honest aggregation: every axis clean — unweighted AND, not a score
    check("no_scalar_collapse", has_no_score and isinstance(vec, tuple) and len(vec) == 3 and all_clean is False,
          f"three independent verdicts kept as a vector {vec}; no weighted 'coherence score' is ever emitted")

    print(f"\n{passed}/{total} checks. The engine audited one system model through three independent lenses —")
    print("structural (boundary orientability), provenance (where possibility becomes obligation), spatial")
    print("(partition leakage/convergence) — and kept them as a VECTOR, refusing to fuse them into a single")
    print("coherence score. Coherent models come back clean on every axis; fragile ones raise every axis; and")
    print("a model can be clean on two axes and leak on the third (they are independent). It bundles three")
    print("VERIFIED probes without re-deriving them, surfaces attention signals rather than verdicts, enforces")
    print("nothing, and never says 'safe'. 'Continuous' means run it in CI; the encodings are declared models.")
    print("`declared ≠ verified`; `tested ≠ safe`; objectivity is not one scalar — not even for the auditor.")
    assert passed == total, "the topology/provenance engine failed its own self-test"


def _spatial_inputs(m: SystemModel):
    """Recompute the (rate, did_converge) the spatial lens feeds cp.classify — for the consistency check."""
    cross, rate = cp.leakage(m.deps, m.partition)
    trace = (cp.settle_under_load(len(cross), m.load, m.budget, m.horizon) if m.load > 0
             else cp.settle_quiescent(len(cross), m.budget))
    return rate, cp.converged(trace)


if __name__ == "__main__":
    main()
