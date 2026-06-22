# SPDX-License-Identifier: AGPL-3.0-only
"""
concurrency_probe.py — geometry proposes a partition; the dependency graph judges it; convergence reveals
whether the boundary was good. Observe, do NOT enforce. Apparatus, no verdict.

The Dini temptation, graded: Dini's theorem (a monotone pointwise-convergent sequence of continuous functions
on a COMPACT space converges UNIFORMLY) is real, but its hypotheses do not hold for a live edited world —
edit trajectories are not monotone, and a geometrically bounded region does not bound its DEPENDENCY surface
(`geometric locality ≠ dependency locality`). So Dini does not *guarantee* uniform latency or kill stragglers.
What survives is narrower and honest:

    * a partition (Hilbert/Morton/octree/graph-cut/curved metric) is a *chosen* representation — a HYPOTHESIS
      about where coordination is cheap, never a claim about the world (Arbitrary-Boundary Law);
    * the only Dini-shaped quantity that fits is a monotone METRIC — unresolved cross-boundary dependencies —
      and it converges uniformly only in the QUIESCENT settle phase (edits stopped); under live overload it
      must be ALLOWED to diverge. Convergence is a thing you MEASURE, not assume.

So this probe does not enforce a partition or promise convergence. It measures, for a given partition and a
given dependency graph: how much the boundary LEAKS (cross-region dependencies), and whether the residual
SETTLES — then classifies the partition as a clean gauge, a bounded-cost gauge, or a semantic leak that should
be repartitioned. `geometry proposes → dependencies judge → convergence reveals`. The functions are pure (no
state, no mutation, no enforcement) — the sealed-observer property in functional form.

(Reconciliation-layer cousin of `prediction.py`'s Dini-style observer `ghost = max(0, observed − predicted)`.)

Run:  PYTHONHASHSEED=0 python3 concurrency_probe.py
"""
from __future__ import annotations


# --- the judge: a dependency edge (a, b) means "b depends on a"; it leaks if it crosses the partition ---
def leakage(deps, partition):
    """Pure. Returns (cross_edges, rate). The dependency graph judges the partition the geometry proposed."""
    cross = [(a, b) for (a, b) in deps if partition[a] != partition[b]]
    rate = len(cross) / len(deps) if deps else 0.0
    return cross, rate


# --- locality kinds: geometric (same region) vs causal (a dependency edge). They are not the same relation. ---
def geometric_pairs(objects, partition):
    return {frozenset((x, y)) for x in objects for y in objects
            if x != y and partition[x] == partition[y]}


def causal_pairs(deps):
    return {frozenset((a, b)) for (a, b) in deps}


# --- convergence (Dini-shaped, on the monotone metric, QUIESCENT phase): unresolved cross-deps settle to 0 ---
def settle_quiescent(n_cross, budget):
    """No new edits arrive; reconcile `budget` per tick. Monotone non-increasing → 0. Returns the trace."""
    unresolved = n_cross
    trace = [unresolved]
    while unresolved > 0:
        unresolved = max(0, unresolved - budget)
        trace.append(unresolved)
    return trace


def settle_under_load(n_cross, new_per_tick, budget, horizon):
    """Live editing keeps creating cross-boundary deps. If new_per_tick > budget the metric DIVERGES —
    the partition cannot be Dini-tamed under that load. Convergence is allowed to fail; that is information."""
    unresolved = n_cross
    trace = [unresolved]
    for _ in range(horizon):
        unresolved = max(0, unresolved + new_per_tick - budget)
        trace.append(unresolved)
    return trace


def converged(trace):
    return trace[-1] == 0


def monotone_non_increasing(trace):
    return all(trace[i] >= trace[i + 1] for i in range(len(trace) - 1))


# --- the verdict-free classification: keep / bounded-cost / repartition ---
def classify(rate, did_converge):
    if rate == 0.0:
        return "GOOD_GAUGE"        # boundary carries no causal traffic — a clean gauge (keep)
    if did_converge:
        return "GAUGE_WITH_COST"   # leaks, but the residual settles in quiescence — semantic but bounded
    return "SEMANTIC_LEAK"         # leaks faster than it settles — the optimization boundary BECAME reality (repartition)


def main() -> None:
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<36} {detail}")

    print("concurrency_probe — geometry proposes a partition; dependencies judge it; convergence reveals.")
    print("Observe, not enforce. The partition is a hypothesis; reality says whether it was chosen well.\n")

    # one fixed world + dependency cluster (b depends on a). o5 is isolated (no dependency).
    objects = ["o0", "o1", "o2", "o3", "o4", "o5"]
    deps = [("o0", "o1"), ("o1", "o2"), ("o2", "o3"), ("o3", "o4")]

    # two competing partition HYPOTHESES over the SAME world + SAME dependencies
    p_aligned = {o: "R0" for o in objects}                                   # cluster stays whole
    p_split = {"o0": "R0", "o1": "R0", "o2": "R1", "o3": "R1", "o4": "R1", "o5": "R0"}  # cuts o1→o2

    cross_aligned, rate_aligned = leakage(deps, p_aligned)
    cross_split, rate_split = leakage(deps, p_split)

    budget = 1
    trace_aligned = settle_quiescent(len(cross_aligned), budget)
    trace_split = settle_quiescent(len(cross_split), budget)
    trace_overload = settle_under_load(len(cross_split), new_per_tick=3, budget=budget, horizon=5)

    cls_aligned = classify(rate_aligned, converged(trace_aligned))
    cls_split = classify(rate_split, converged(trace_split))
    cls_overload = classify(rate_split, converged(trace_overload))

    print("  partition            leakage   converges?   classification")
    print(f"    aligned            {rate_aligned:.2f}      {str(converged(trace_aligned)):<11} {cls_aligned}")
    print(f"    split (quiescent)  {rate_split:.2f}      {str(converged(trace_split)):<11} {cls_split}")
    print(f"    split (overloaded) {rate_split:.2f}      {str(converged(trace_overload)):<11} {cls_overload}")
    print()

    # 1. leakage is a representation CHOICE, not a property of the world: same deps, different partition, different leak
    check("leakage_is_a_choice_not_ontology", rate_aligned == 0.0 and rate_split > 0.0,
          f"identical dependency graph; aligned leaks {rate_aligned:.2f}, split leaks {rate_split:.2f} (Arbitrary-Boundary)")

    # 2. the dependency graph is the JUDGE: it names exactly which dependency the split partition cuts
    check("dependency_graph_is_the_judge", cross_split == [("o1", "o2")] and cross_aligned == [],
          f"split cuts exactly {cross_split}; aligned cuts none")

    # 3. geometric locality ≠ dependency locality (the recurring boundary lesson, made measurable)
    geo, cau = geometric_pairs(objects, p_split), causal_pairs(deps)
    geo_not_cau, cau_not_geo = geo - cau, cau - geo
    check("geometric_neq_dependency_locality", bool(geo_not_cau) and bool(cau_not_geo),
          "∃ geometric-neighbours-not-dependent (e.g. o0,o5) AND ∃ dependent-but-not-co-located (o1,o2)")

    # 4. Dini-shaped convergence holds on the monotone metric — but only in the QUIESCENT phase
    check("convergence_quiescent_is_monotone",
          monotone_non_increasing(trace_split) and converged(trace_split),
          f"unresolved cross-deps settle monotonically to 0 once edits cease: {trace_split}")

    # 5. ...and is ALLOWED to fail under live overload — convergence is measured, never assumed
    check("convergence_fails_under_overload",
          not converged(trace_overload) and trace_overload[-1] > trace_overload[0],
          f"new cross-deps (3/tick) outrun reconciliation (1/tick): {trace_overload} — repartition signal")

    # 6. classification keeps the three honest outcomes (keep / bounded-cost / repartition)
    check("classification_three_outcomes",
          cls_aligned == "GOOD_GAUGE" and cls_split == "GAUGE_WITH_COST" and cls_overload == "SEMANTIC_LEAK",
          "clean gauge / bounded-cost gauge / semantic leak — the partition earns or loses its place")

    # 7. sealed + no verdict: the measuring functions are PURE (no mutation of world or deps; no enforcement)
    deps_snapshot, part_snapshot = list(deps), dict(p_split)
    _ = leakage(deps, p_split); _ = leakage(deps, p_split)
    _ = settle_quiescent(len(cross_split), budget)
    pure = (deps == deps_snapshot and p_split == part_snapshot
            and leakage(deps, p_split) == (cross_split, rate_split))
    check("instrument_is_sealed_no_verdict", pure,
          "leakage/settle/classify are pure — they observe the partition, never reorder edits or adopt one")

    print(f"\n{passed}/{total} checks. The instrument ran the pipeline WITHOUT enforcing a partition: geometry")
    print("proposed two boundaries, the dependency graph judged them (same world, different leakage — the")
    print("boundary is a choice, not ontology), and convergence revealed the rest — settling uniformly in")
    print("quiescence on the monotone metric, diverging under live overload (where Dini cannot help and must")
    print("not pretend to). It surfaces GOOD_GAUGE / GAUGE_WITH_COST / SEMANTIC_LEAK and a repartition signal,")
    print("with NO verdict on which partition to adopt — the math earns its place by surviving contact with the")
    print("frontier, or it doesn't. geometric locality ≠ dependency locality; boundaries are chosen, reality grades them.")
    assert passed == total, "the concurrency instrument failed its own self-test"


if __name__ == "__main__":
    main()
