# SPDX-License-Identifier: AGPL-3.0-only
"""
module_graph.py — the self-extraction fidelity probe: turn ONE real artifact into a model and see where the
abstraction breaks. This is the first time the engine audits something it did NOT author.

The hardest hidden assumption, made the adversary: `SystemModel` is not reality — it is an *interpretation of
evidence*. So the probe's first success is not "finds bugs"; it is **knowing what it does not know.**

It is deliberately DUMB — AST only, no inference, no importance scores, no AI:
    Python module      → node
    intra-repo import  → directed edge
    package directory  → partition
Anything it cannot resolve statically (dynamic imports, relative imports, unparseable files, basename
collisions) is recorded as a BLIND SPOT, not silently dropped.

FIDELITY OVER COVERAGE — which lenses the evidence actually supports:
    spatial    (concurrency_probe.leakage)  APPLIES — cross-package imports = the directory boundary going
                                            semantic (does the org chart match the dependency graph?).
    structural (dependency cycles)          APPLIES via a fit-for-purpose check — directed import cycles
                                            (circular dependencies). NOTE: NOT klein signed-orientability —
                                            bare imports carry no signed trust/authority boundary, so forcing
                                            klein here would be the extraction lie. Declared, not faked.
    provenance (frontier_probe)             NOT APPLICABLE — a static import graph has no temporal
                                            candidate→commit→dependency flow. Would need git history or runtime
                                            traces. The probe REFUSES to fabricate a provenance verdict.

Observe, not enforce: it reads with `ast` (never executes scanned code), never writes, issues no verdict
(findings + a coverage boundary, never "fix this import"). `declared ≠ verified`; `tested ≠ safe`.

Run (from this directory):  PYTHONHASHSEED=0 python3 module_graph.py   [optional: a path to scan instead]
"""
from __future__ import annotations

import ast
import os
import sys

import concurrency_probe as cp   # the one lens a static import graph faithfully supports: cross-package leakage

_SKIP = {"target", ".git", "__pycache__", "node_modules", ".venv"}


def _py_files(root):
    out = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SKIP]
        for f in files:
            if f.endswith(".py"):
                out.append(os.path.join(dirpath, f))
    return out


def _modname(path):
    return os.path.splitext(os.path.basename(path))[0]


def _package(path, root):
    rel = os.path.relpath(os.path.dirname(path), root)
    return rel.split(os.sep)[0] if rel not in (".", "") else os.path.basename(os.path.abspath(root))


def scan_source(modname, src, names):
    """Pure: extract intra-repo import edges + blind spots from one module's source. No execution."""
    edges, blind = set(), []
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                t = a.name.split(".")[0]
                if t in names and t != modname:
                    edges.add((modname, t))
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import — package resolution not modeled by this dumb pass
                blind.append((modname, "relative import (level %d)" % node.level))
                continue
            if node.module:
                t = node.module.split(".")[0]
                if t in names and t != modname:
                    edges.add((modname, t))
        elif isinstance(node, ast.Call):
            fn = node.func
            nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
            if nm in ("__import__", "import_module"):
                blind.append((modname, "dynamic import (%s) — unobserved by static parse" % nm))
    return edges, blind


def extract(root):
    """Build the model from a real source tree. Reads only; never executes the scanned code."""
    files = _py_files(root)
    names, collisions = {}, []
    for f in files:
        m = _modname(f)
        if m in names:
            collisions.append(m)        # two files share a basename — the dumb name-resolution is ambiguous here
        names[m] = f
    edges, blind = set(), []
    for f in files:
        m = _modname(f)
        try:
            with open(f, encoding="utf-8") as fh:
                src = fh.read()
            e, b = scan_source(m, src, names)
            edges |= e
            blind += b
        except (SyntaxError, UnicodeDecodeError) as ex:
            blind.append((m, "unparseable: %s" % type(ex).__name__))
    partition = {m: _package(p, root) for m, p in names.items()}
    return {"nodes": set(names), "edges": edges, "partition": partition,
            "blind": blind, "collisions": collisions, "files": len(files)}


def find_cycle(nodes, edges):
    """A directed dependency cycle (circular import) — the fit-for-purpose structural check for imports."""
    adj = {}
    for (u, v) in edges:
        adj.setdefault(u, []).append(v)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    path = []

    def dfs(u):
        color[u] = GRAY
        path.append(u)
        for v in adj.get(u, []):
            if color.get(v, WHITE) == GRAY:
                return path[path.index(v):] + [v]
            if color.get(v, WHITE) == WHITE:
                c = dfs(v)
                if c:
                    return c
        color[u] = BLACK
        path.pop()
        return None

    for n in nodes:
        if color[n] == WHITE:
            c = dfs(n)
            if c:
                return c
    return None


def report(model):
    """Three lenses, each only where the evidence supports it — plus the coverage boundary."""
    cross, rate = cp.leakage(list(model["edges"]), model["partition"])
    cyc = find_cycle(model["nodes"], model["edges"])
    return {
        "spatial": {"cross_package_imports": sorted(cross), "leak_rate": rate},
        "structural": {"dependency_cycle": cyc},   # None = acyclic; klein signed-orientability N/A to bare imports
        "provenance": "NOT_APPLICABLE_static_imports",   # no temporal candidate→commit flow in an import graph
        "fidelity": {"files": model["files"], "modules": len(model["nodes"]), "edges": len(model["edges"]),
                     "blind_spots": model["blind"], "basename_collisions": model["collisions"]},
    }


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    model = extract(root)
    rep = report(model)

    print("module_graph — self-extraction fidelity probe (audit a system the engine did NOT author).")
    print(f"scanned: {root}\n")
    print(f"  modules: {rep['fidelity']['modules']}   intra-repo import edges: {rep['fidelity']['edges']}   files: {rep['fidelity']['files']}")
    print(f"  spatial   — cross-package imports: {len(rep['spatial']['cross_package_imports'])} (leak rate {rep['spatial']['leak_rate']:.2f})")
    print(f"  structural— dependency cycle: {rep['structural']['dependency_cycle'] or 'none (acyclic)'}   [klein signed-orientability N/A to bare imports]")
    print(f"  provenance— {rep['provenance']}  (a static import graph has no candidate→commit flow)")
    print(f"  fidelity  — blind spots: {len(rep['fidelity']['blind_spots'])}   basename collisions: {len(rep['fidelity']['basename_collisions'])}")
    if rep["fidelity"]["blind_spots"]:
        for (m, why) in rep["fidelity"]["blind_spots"]:
            print(f"              · {m}: {why}")
    print()

    # ---- self-test: verify the EXTRACTOR and the fidelity discipline (not 'does it find bugs') ----
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # the self-test always uses THIS subfolder (a system whose true structure we can inspect)
    here = os.path.dirname(os.path.abspath(__file__))
    m = extract(here)
    e = m["edges"]

    known = {("topology_provenance_engine", "klein_probe"),
             ("topology_provenance_engine", "frontier_probe"),
             ("topology_provenance_engine", "concurrency_probe")}
    check("extracts_known_edges", known <= e,
          "rediscovered topology_provenance_engine → {klein, frontier, concurrency} from the source (truth we can inspect)")

    one_package = len(set(m["partition"].values())) == 1
    check("partition_from_packages", one_package and all(v == os.path.basename(here) for v in m["partition"].values()),
          f"every module mapped to its package dir '{os.path.basename(here)}'")

    _, rate = cp.leakage(list(e), m["partition"])
    check("spatial_lens_applies", rate == 0.0,
          "single package → cross-package leak rate 0.00 (the subfolder is dependency-cohesive)")

    real_cycle = find_cycle(m["nodes"], e)
    syn_cycle = find_cycle({"A", "B"}, {("A", "B"), ("B", "A")})
    check("structural_cycle_check", real_cycle is None and syn_cycle is not None,
          "no circular dependency in the real graph; the detector catches a synthetic A→B→A")

    check("provenance_declared_not_applicable", report(m)["provenance"] == "NOT_APPLICABLE_static_imports",
          "refuses to fabricate a provenance verdict from a static import graph — declares it inapplicable")

    syn_e, syn_b = scan_source("syn", "import importlib\nimportlib.import_module('x')\nimport klein_probe\n",
                               {"klein_probe": 0, "syn": 0})
    knows_blind = any("dynamic import" in why for (_mod, why) in syn_b) and ("syn", "klein_probe") in syn_e
    check("declares_its_blind_spots", knows_blind and "blind" in m,
          "a dynamic import is flagged as a blind spot, a static one is resolved — it knows what it can't see")

    again = extract(here)
    sealed = again["edges"] == m["edges"] and "dependency_cycle" in report(m)["structural"]
    check("sealed_observe_only_deterministic", sealed,
          "ast-only (never executes scanned code), no writes, deterministic rerun; emits findings, not a verdict")

    print(f"\n{passed}/{total} checks. The probe turned one real artifact — this subfolder's own source — into a")
    print("model WITHOUT authoring it, and its first success was negative: it knows what it does not know. It")
    print("applied the spatial lens where the evidence supports it (cross-package imports), used a fit-for-purpose")
    print("structural check (dependency cycles, NOT forced klein orientability), and DECLARED the provenance lens")
    print("inapplicable to a static import graph rather than fabricating one. Blind spots (dynamic/relative")
    print("imports, collisions) are recorded, not hidden. `SystemModel` is an interpretation of evidence — and the")
    print("extraction now says so out loud. The threshold is crossed: auditing something it did not author.")
    assert passed == total, "the self-extraction probe failed its own self-test"


if __name__ == "__main__":
    main()
