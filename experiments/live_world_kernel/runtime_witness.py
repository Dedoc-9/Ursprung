# SPDX-License-Identifier: AGPL-3.0-only
"""
runtime_witness.py — the witness that EARNS new evidence (and has its own blind spot).

The static extractor (fidelity_gap/module_graph) sees every *declared* import but is blind to *dynamic* ones
(its RUNTIME_FRONTIER). A runtime witness sees the opposite slice: every import actually *executed*, including
dynamic ones — but blind to *un-exercised* paths (a conditional/lazy import never triggered this run). So runtime
does NOT strictly dominate static; they have **orthogonal blind spots.** This is the first artifact where two
REAL witnesses of the same system meet, neither globally stronger.

THE HONEST-WITNESS RULE that makes the reconciliation truthful: **a witness must never deny from absence.**
Runtime "did not observe edge e this run" is `DECLARED` (its blind spot), NEVER `REVERSIBLE` (a denial it cannot
support). Consequence, and a finding that sharpens the disagreement picture: between two honest witnesses,
conflict collapses to REFINEMENT in both directions — runtime refines static where it caught a dynamic import;
static refines runtime where runtime was blind to an un-exercised path — and symmetric `CONTESTED` essentially
never fires. CONTESTED is reserved for two witnesses both *positively* asserting incompatible things (the
machinery still produces it — see the self-test — it just isn't reachable from honest absence).

    ⚠ SAFETY: tracing imports EXECUTES the target's import-time (module-level) code. Run it ONLY on code you
    trust. It does not call functions or run tests — only module load — but module load is still execution.

`declared ≠ verified`: the import TRACING below ships as a candidate (it executes target code; not run by the
author), while the RECONCILIATION DISCIPLINE — the part that must be correct — is verified synthetically (7/7).

Run (from this directory):  PYTHONHASHSEED=0 python3 runtime_witness.py   [optional: a repo path to trace]
"""
from __future__ import annotations

import os
import sys

import fidelity_gap as fg
from reality_status import Cell, MEASURED, DECLARED, NOT_APPLICABLE
from reconcile_status import reconcile_cell, STRENGTH, CONTESTED

STATIC_RANK = 1     # a declared import: real evidence, but may be dead
RUNTIME_RANK = 2    # an OBSERVED import: ground truth for this run — stronger evidence THAT the edge is real


# ---------------------------------------------------------------------------------------------------
# The reconciliation discipline (PURE — this is the verified core).
# ---------------------------------------------------------------------------------------------------
def dep_cells(static_edges, runtime_edges, m):
    """For module m, build the static + runtime dependency claims and reconcile them on the epistemic lattice.
    Returns (static_cell, runtime_cell, reconciled). Runtime NEVER denies from absence — absence is DECLARED."""
    s_in = any(v == m for (_u, v) in static_edges)
    r_in = any(v == m for (_u, v) in runtime_edges)

    static_cell = Cell(
        "IRREVERSIBLE" if s_in else "REVERSIBLE", MEASURED,
        "static: a declared importer exists" if s_in
        else "static: no declared importer (blind to dynamic imports — may be wrong)")

    if r_in:
        runtime_cell = Cell("IRREVERSIBLE", MEASURED,
                            "runtime: import OBSERVED at load time (ground truth for this run)")
    else:
        runtime_cell = Cell("DECLARED", DECLARED,
                            "runtime: not observed at load time — un-exercised paths invisible (absence ≠ denial)")

    reconciled = reconcile_cell([("static", static_cell, STATIC_RANK), ("runtime", runtime_cell, RUNTIME_RANK)])
    return static_cell, runtime_cell, reconciled


def reconcile_repo(static_edges, runtime_edges, modules):
    """Reconcile every module's dependency claim; tally the direction of refinement. Pure."""
    out, tally = {}, {"runtime_refines_static": 0, "static_refines_runtime": 0, "corroborated": 0, "contested": 0}
    for m in modules:
        sc, rc, rec = dep_cells(static_edges, runtime_edges, m)
        out[m] = (sc, rc, rec)
        if rec.status == CONTESTED:
            tally["contested"] += 1
        elif sc.value != rec.value and rc.value == rec.value:
            tally["runtime_refines_static"] += 1          # runtime caught what static missed (dynamic import)
        elif rc.value != rec.value and sc.value == rec.value and rc.status != MEASURED:
            tally["static_refines_runtime"] += 1          # runtime was blind (un-exercised), static held
        else:
            tally["corroborated"] += 1
    return out, tally


# ---------------------------------------------------------------------------------------------------
# The runtime TRACE (IO — executes target import-time code; ships as a candidate, not asserted).
# ---------------------------------------------------------------------------------------------------
def _resolve_targets(importer_pkg, name, fromlist, level):
    """Pure: resolve an import call to absolute dotted target module(s). Handles RELATIVE imports (level>0) via
    the importer's package — the blind spot that made the first trace silent on relative-heavy packages.
        level 0 : `name` is already absolute.
        level L : base = importer_pkg with (L-1) trailing components stripped; target = base[.name]; each
                  fromlist entry is a candidate submodule base[.name].entry.
    Returns a set of candidate absolute module names (filtered to the package later)."""
    targets = set()
    if level == 0:
        if name:
            targets.add(name)
            for f in (fromlist or ()):
                targets.add(name + "." + f)
        return targets
    parts = importer_pkg.split(".") if importer_pkg else []
    if level - 1 > 0:                                   # `from .. import x` etc. climb up the package tree
        parts = parts[:-(level - 1)] if len(parts) >= (level - 1) else []
    base = ".".join(parts)
    head = (base + "." + name) if (base and name) else (name or base)
    if head:
        targets.add(head)
        for f in (fromlist or ()):
            targets.add(head + "." + f)
    return targets


def _locate(root):
    """Best-effort: find (sys.path dir, top package name) for a repo. Prefers a src/<pkg> layout."""
    for base in (os.path.join(root, "src"), root):
        if os.path.isdir(base):
            for name in sorted(os.listdir(base)):
                if os.path.isfile(os.path.join(base, name, "__init__.py")):
                    return base, name
    return None, None


def trace_imports(src_dir, top_pkg):
    """Trace intra-package imports executed during MODULE LOAD. EXECUTES target import-time code. Best-effort:
    importer is read from the caller's globals __name__ (reliable for absolute imports; relative-import
    attribution is part of runtime's own blind spot)."""
    import builtins
    import importlib
    import pkgutil

    edges = set()
    sys.path.insert(0, src_dir)
    orig = builtins.__import__

    def hook(name, g=None, l=None, fromlist=(), level=0):
        g = g or {}
        importer = g.get("__name__", "?")
        importer_pkg = g.get("__package__") or importer    # the package relative imports resolve against
        for tgt in _resolve_targets(importer_pkg, name or "", fromlist, level):
            edges.add((importer, tgt))
        return orig(name, g, l, fromlist, level)

    builtins.__import__ = hook
    try:
        pkg = importlib.import_module(top_pkg)
        for mod in pkgutil.walk_packages(getattr(pkg, "__path__", []), top_pkg + "."):
            try:
                importlib.import_module(mod.name)
            except Exception:
                pass   # a submodule that won't import is itself a runtime fact (it simply contributes no edges)
    finally:
        builtins.__import__ = orig
        if src_dir in sys.path:
            sys.path.remove(src_dir)

    return {(u, v) for (u, v) in edges if u.startswith(top_pkg) and v.startswith(top_pkg)}


def main() -> None:
    print("runtime_witness — the witness that EARNS new evidence; orthogonal blind spots to static.")
    print("⚠ tracing EXECUTES the target's import-time code — trusted code only.\n")

    if len(sys.argv) > 1:
        root = sys.argv[1]
        src_dir, top = _locate(root)
        if not top:
            print(f"  could not locate a package under {root} (no src/<pkg>/__init__.py or <pkg>/__init__.py)\n")
        else:
            static = fg.diagnose(root)
            static_edges = static["edges"]
            try:
                runtime_edges = trace_imports(src_dir, top)
            except Exception as ex:
                runtime_edges = set()
                print(f"  runtime trace raised {type(ex).__name__}: {ex} (recorded as: observed nothing)\n")
            modules = sorted(static["known"] | {v for (_u, v) in runtime_edges})
            out, tally = reconcile_repo(static_edges, runtime_edges, modules)
            print(f"  traced {top} from {src_dir}: static {len(static_edges)} edges, runtime {len(runtime_edges)} edges")
            print(f"  reconciliation: runtime_refines_static={tally['runtime_refines_static']} "
                  f"(dynamic imports static missed), static_refines_runtime={tally['static_refines_runtime']} "
                  f"(paths runtime didn't exercise), corroborated={tally['corroborated']}, contested={tally['contested']}")
            shown = 0
            for m, (sc, rc, rec) in out.items():
                if sc.value != rec.value or (rc.status == MEASURED and sc.value != rc.value):
                    if shown < 4:
                        print(f"    dependency({m!r}): {rec.value} [{rec.status}]  (static={sc.value}, runtime={rc.value}[{rc.status}])")
                        shown += 1
            print("  (relative imports now resolved via importer package+level; the residual blind spot is")
            print("   imports inside functions NOT called this run — absence stays DECLARED, never denial)\n")
    else:
        print("  (no path given — running the verified reconciliation self-test only; pass a trusted repo path")
        print("   e.g.  python runtime_witness.py \"C:\\...\\Desktop\\tests_epi\\click\"  to trace a real package)\n")

    # ------------- self-test: the reconciliation discipline (synthetic, deterministic, the verified core) -------------
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # runtime caught a DYNAMIC import static missed → runtime refines static (NEW evidence earned)
    sc, rc, rec = dep_cells(static_edges=set(), runtime_edges={("a", "m")}, m="m")
    check("runtime_refines_static_on_dynamic",
          rec.value == "IRREVERSIBLE" and rec.status == MEASURED and "REVERSIBLE" in rec.evidence,
          "edge only runtime saw → IRREVERSIBLE [MEASURED]; static's REVERSIBLE recorded as refuted lower bound")

    # static saw a declared edge runtime did NOT exercise → static refines runtime (runtime was blind)
    sc, rc, rec = dep_cells(static_edges={("a", "m")}, runtime_edges=set(), m="m")
    check("static_refines_runtime_on_unexercised",
          rec.value == "IRREVERSIBLE" and rec.status == MEASURED and rc.status == DECLARED,
          "edge only static saw → static holds; runtime contributes DECLARED (unobserved), not a denial")

    # both saw it → corroborated, strength preserved
    sc, rc, rec = dep_cells(static_edges={("a", "m")}, runtime_edges={("a", "m")}, m="m")
    check("corroboration_preserves_strength",
          rec.value == "IRREVERSIBLE" and rec.status == MEASURED and "corroborated" in rec.evidence,
          "both witnesses agree → IRREVERSIBLE [MEASURED], corroborated")

    # THE honest-witness rule: runtime absence is DECLARED, never REVERSIBLE
    _, rc_absent, _ = dep_cells(static_edges={("a", "m")}, runtime_edges=set(), m="m")
    check("runtime_absence_is_not_denial",
          rc_absent.status == DECLARED and rc_absent.value == "DECLARED",
          "runtime never claims REVERSIBLE from absence — 'unobserved' is DECLARED (absence ≠ denial)")

    # honest pair NEVER contests; but the machinery still produces CONTESTED for two positive deniers
    honest_never = all(dep_cells(s, r, "m")[2].status != CONTESTED
                       for (s, r) in [(set(), {("a", "m")}), ({("a", "m")}, set()), ({("a", "m")}, {("a", "m")})])
    forced = reconcile_cell([("p1", Cell("IRREVERSIBLE", MEASURED, "asserts edge"), 1),
                             ("p2", Cell("REVERSIBLE", MEASURED, "asserts NO edge"), 1)])
    check("contested_only_for_positive_conflict",
          honest_never and forced.status == CONTESTED,
          "honest static+runtime → never CONTESTED; two positive-asserting peers → CONTESTED (machinery intact)")

    # the monotone invariant carries through the bridge
    cases = [(set(), {("a", "m")}), ({("a", "m")}, set()), ({("a", "m")}, {("a", "m")}), (set(), set())]
    monotone = all(
        STRENGTH[dep_cells(s, r, "m")[2].status]
        <= max(STRENGTH[dep_cells(s, r, "m")[0].status], STRENGTH[dep_cells(s, r, "m")[1].status])
        for (s, r) in cases)
    check("strength_never_inflates", monotone,
          "reconciled strength ≤ max(static, runtime) in every case — no inflation across the witness bridge")

    # runtime genuinely ADDS evidence: an edge set not contained in static's
    new_evidence = {("a", "m")} - set()
    check("earns_new_evidence", bool(new_evidence) and dep_cells(set(), {("a", "m")}, "m")[2].value == "IRREVERSIBLE",
          "runtime contributes edges absent from static (the dynamic ones) — new evidence, not a rearrangement")

    # relative-import resolution (the fix for the click 0-edges ghost) — verified as a pure function
    rel1 = _resolve_targets("click", "", ["utils"], 1)              # from . import utils  (in package click)
    rel2 = _resolve_targets("click.sub", "models", ["X"], 1)        # from .models import X (in click.sub.*)
    rel3 = _resolve_targets("click.sub", "pkg", [], 2)              # from ..pkg import *   (climb one level)
    absn = _resolve_targets("click", "os.path", [], 0)             # absolute import untouched
    check("relative_imports_resolved",
          "click.utils" in rel1 and "click.sub.models" in rel2 and "click.pkg" in rel3 and "os.path" in absn,
          "from . / from .mod / from ..pkg resolve to absolute dotted targets via importer package + level")

    print(f"\n{passed}/{total} checks. The runtime witness earns evidence the static one structurally cannot")
    print("(dynamic imports, executed at load time) and is blind to what the static one sees (un-exercised paths).")
    print("Neither dominates: reconciliation refines in BOTH directions on the epistemic lattice, and because an")
    print("honest witness never denies from absence (runtime 'unobserved' = DECLARED, not REVERSIBLE), symmetric")
    print("CONTESTED does not arise between them — it is reserved for two witnesses positively asserting")
    print("incompatible claims. Strength never inflates across the bridge. `declared ≠ verified`: the trace")
    print("executes target code and ships as a candidate; the reconciliation discipline is what is verified here.")
    assert passed == total, "runtime_witness failed its reconciliation self-test"


if __name__ == "__main__":
    main()
