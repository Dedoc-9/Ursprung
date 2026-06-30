# SPDX-License-Identifier: AGPL-3.0-only
"""repo_audit.py — relative-import-resolving architectural recon for EXTERNAL repos.

Closes the gap measured last run: module_graph.scan_source punts on relative imports ("package resolution
not modeled by this dumb pass"), so on a real package (click) the graph was almost all blind spots. This
resolves relative imports to dotted module names per Python's import semantics, builds dotted-name nodes
(no basename collisions), reuses module_graph.find_cycle, and self-tests on a SYNTHETIC package (de-pinned
from live_world_kernel's own source). Observe-only: AST parse, never executes target code. It REPORTS a
resolution rate and DECLARES the symbol-vs-module boundary rather than fabricating edges. integrity != truth.
"""
from __future__ import annotations
import ast, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from module_graph import find_cycle, _py_files   # reuse the validated cycle detector + .py walker


def dotted(path, root):
    parts = os.path.relpath(path, root)[:-3].split(os.sep)   # strip ".py"
    is_pkg = parts[-1] == "__init__"
    return (".".join(parts[:-1]) if is_pkg else ".".join(parts)), is_pkg


def resolve_relative(importer, is_pkg, level, module):
    """Python relative-import semantics -> absolute dotted module (or None if it climbs above the top)."""
    pkg = importer.split(".") if is_pkg else importer.split(".")[:-1]
    if level - 1 > len(pkg):
        return None
    base = pkg[: len(pkg) - (level - 1)]
    return ".".join(base + ([module] if module else []))


def _abs_prefix(name, nodes):
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        c = ".".join(parts[:i])
        if c in nodes:
            return c
    return None


def scan(name, is_pkg, src, nodes):
    edges, blind, rel_total, rel_resolved = set(), [], 0, 0
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            for a in node.names:
                t = _abs_prefix(a.name, nodes)
                if t and t != name:
                    edges.add((name, t))
        elif isinstance(node, ast.ImportFrom):
            if node.level:                                    # relative import — RESOLVE it
                rel_total += 1
                tgt = resolve_relative(name, is_pkg, node.level, node.module)
                cand = [tgt] if node.module else [tgt + "." + a.name for a in node.names] if tgt else []
                hit = [c for c in cand if c in nodes and c != name]
                if hit:
                    rel_resolved += 1
                    edges.update((name, c) for c in hit)
                else:
                    blind.append((name, "relative import unresolved (level %d) — symbol re-export, not a submodule" % node.level))
            elif node.module:
                t = _abs_prefix(node.module, nodes)
                if t and t != name:
                    edges.add((name, t))
    return edges, blind, rel_total, rel_resolved


def extract(root):
    nodes = {}
    for f in _py_files(root):
        dn, is_pkg = dotted(f, root)
        nodes[dn] = (f, is_pkg)
    nodeset = set(nodes)
    edges, blind, rt, rr = set(), [], 0, 0
    for dn, (f, is_pkg) in nodes.items():
        try:
            e, b, t, r = scan(dn, is_pkg, open(f, encoding="utf-8").read(), nodeset)
            edges |= e; blind += b; rt += t; rr += r
        except (SyntaxError, UnicodeDecodeError) as ex:
            blind.append((dn, "unparseable: %s" % type(ex).__name__))
    return {"nodes": nodeset, "edges": edges, "blind": blind, "rel_total": rt, "rel_resolved": rr}


def report(model):
    fanin = {}
    for (_u, v) in model["edges"]:
        fanin[v] = fanin.get(v, 0) + 1
    rt, rr = model["rel_total"], model["rel_resolved"]
    cyc = find_cycle(model["nodes"], model["edges"])
    return {
        "modules": len(model["nodes"]), "edges": len(model["edges"]),
        "relative_imports": rt, "relative_resolved": rr,
        "resolution_rate": round(rr / rt, 4) if rt else 1.0,
        "top_blast_radius_fan_in": sorted(fanin.items(), key=lambda kv: -kv[1])[:5],
        "dependency_cycle": cyc, "blind_spots": len(model["blind"]),
    }


def _selftest():
    nodes = {"pkg", "pkg.a", "pkg.b", "pkg.sub", "pkg.sub.c"}
    e, _, t, r = scan("pkg", True, "from .a import x\nfrom .b import y\n", nodes)
    assert e == {("pkg", "pkg.a"), ("pkg", "pkg.b")} and (t, r) == (2, 2), (e, t, r)
    e2, _, _, _ = scan("pkg.sub.c", False, "from .. import a\nfrom ..b import z\n", nodes)
    assert ("pkg.sub.c", "pkg.a") in e2 and ("pkg.sub.c", "pkg.b") in e2, e2
    _, _, t3, r3 = scan("pkg.a", False, "from .nope import q\n", nodes)
    assert (t3, r3) == (1, 0), (t3, r3)               # unresolved declared, never fabricated
    print("selftest 3/3: spec-correct relative resolution on a SYNTHETIC package (not kernel-pinned).")


def main():
    _selftest()
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    print(json.dumps(report(extract(root)), indent=2, default=list))


if __name__ == "__main__":
    main()
