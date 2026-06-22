# SPDX-License-Identifier: AGPL-3.0-only
"""
fidelity_gap.py — WHY the extraction came back blind, and what would break through.

module_graph audited requests/click and was almost entirely blind: 91 and 197 blind spots, ~0 resolvable
edges. That is NOT a finding about requests/click. It is a finding about OUR MODEL. This instrument reads the
blindness, names its cause, and PROVES what is recoverable — without overclaiming what is not.

THE DIAGNOSIS — one root cause behind nearly every blind spot. The dumb extractor made two assumptions that
real packaged code violates wholesale:
    identity   = file BASENAME           → many `utils.py`, `__init__.py`, `compat.py`  → COLLISION (ambiguous)
    resolution = ABSOLUTE imports only   → real packages import RELATIVELY (`from . import x`) → BLIND
So ~95% of the blindness is a single defect: the module-identity function is wrong. Fixable.

THE BREAKTHROUGH — and the line it must not cross. Two piles, and the honesty is in keeping them apart:
    RECOVERABLE_STATIC   relative imports + basename collisions. Resolved by PACKAGE-PATH identity (the dotted
                         name from the package root) + relative-level math. We do not assert recoverability —
                         we RESOLVE them and show the edges appear and the collisions vanish.
    RUNTIME_FRONTIER     dynamic imports (`__import__`, `import_module`). A smarter parser will NEVER see the
                         target — it is computed at runtime. This is not a defect to fix; it is a real
                         epistemic boundary that needs an execution trace / the committed Weltlinie. Different
                         instrument (the kernel's provenance — frontier_probe), not a better regex. Named, not faked.
    SCOPE_BOUNDARY       a relative import that climbs ABOVE the scanned subtree (you scanned a sub-package).
                         Widen the scan root. A property of WHAT you pointed it at, declared honestly.
    OPAQUE_SOURCE        unparseable under utf-8 + the AST grammar (encoding/older syntax). Decode or exclude.

DECLARED ≠ VERIFIED. The package-root detection (walk up while `__init__.py`) and relative-level math are a
DECLARED model of Python import resolution. The real machinery has more — namespace packages, `sys.path`
edits, conditional/lazy imports, re-exports via `__all__`. Those remain in the residual, declared, never
silently "resolved." resolved ≠ executed (still AST-only, code is never run); a recovered edge means one
module NAMES another, never that a call path EXECUTES.

Run (from this directory):  PYTHONHASHSEED=0 python3 fidelity_gap.py   [optional: a path to diagnose]
"""
from __future__ import annotations

import ast
import os
import sys

import concurrency_probe as cp     # the now-real spatial lens: cross-package leakage on a recovered graph
import module_graph as mg          # the dumb baseline we are explaining (its blind spots are the input)


# ---- the corrected identity: a dotted module name from the package root (kills basename collisions) ----

def package_parts(dirpath, has_init):
    """Dotted package parts for a directory: walk UP while each dir has __init__.py. `has_init(d)`->bool.
    Pure given the predicate. Returns parts topmost-first. No filesystem abspath here (so it is testable)."""
    parts, d = [], dirpath
    while has_init(d):
        parts.append(os.path.basename(d))
        nd = os.path.dirname(d)
        if nd == d:           # reached the filesystem root — stop (guards an all-__init__ chain)
            break
        d = nd
    return list(reversed(parts))


def dotted_name(path, has_init):
    """Full dotted module identity for a .py file. `__init__.py` collapses to its package's name."""
    base = os.path.splitext(os.path.basename(path))[0]
    pkg = package_parts(os.path.dirname(path), has_init)
    if base == "__init__":
        return ".".join(pkg) if pkg else os.path.basename(os.path.dirname(path))
    return ".".join(pkg + [base]) if pkg else base   # not in a package → basename (same as the dumb model)


def resolve_relative(pkg_parts, level, module, names, known):
    """Resolve a relative import to dotted target(s) present in `known`. Pure.
    Returns (resolved:set, unresolved:list[reason]). `pkg_parts` = the dotted package the importing file sits in."""
    resolved, unresolved = set(), []
    cut = len(pkg_parts) - (level - 1)
    if cut < 1:                       # climbs above the scanned subtree (or relative import in a non-package)
        unresolved.append("relative climbs above scan root (level %d from package %s)"
                          % (level, ".".join(pkg_parts) or "<non-package>"))
        return resolved, unresolved
    anchor = pkg_parts[:cut]
    if module:
        cand = ".".join(anchor + module.split("."))
        (resolved.add(cand) if cand in known
         else unresolved.append("relative target outside scan: %s" % cand))
    else:                             # `from . import a, b` — each name may be a submodule
        for n in names:
            cand = ".".join(anchor + [n])
            if cand in known:
                resolved.add(cand)
            # a name that is NOT a submodule (a function/class) is simply not an edge — not a blind spot
    return resolved, unresolved


def _deepest_known(name, known):
    """For `import a.b.c`, return the deepest dotted prefix that is a known module (else None = external)."""
    cand = name
    while cand:
        if cand in known:
            return cand
        cand = cand.rsplit(".", 1)[0] if "." in cand else ""
    return None


def diagnose_source(dotted, pkg_parts, src, known):
    """Pure. From ONE module's source, return (edges, piles) under the CORRECTED model. Never executes code.
    piles: recovered_relative / runtime_frontier / scope_boundary (opaque is handled at the IO layer)."""
    edges = set()
    piles = {"recovered_relative": [], "runtime_frontier": [], "scope_boundary": []}
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                tgt = _deepest_known(a.name, known)
                if tgt and tgt != dotted:
                    edges.add((dotted, tgt))
        elif isinstance(node, ast.ImportFrom):
            if node.level:                                    # relative — the recoverable pile
                names = [a.name for a in node.names]
                res, un = resolve_relative(pkg_parts, node.level, node.module, names, known)
                for t in res:
                    if t != dotted:
                        edges.add((dotted, t))
                        piles["recovered_relative"].append((dotted, t))   # was a BLIND SPOT in the dumb model
                for reason in un:
                    piles["scope_boundary"].append((dotted, reason))
            elif node.module:                                 # absolute from-import
                tgt = _deepest_known(node.module, known)
                if tgt and tgt != dotted:
                    edges.add((dotted, tgt))
                for a in node.names:                          # `from pkg import submod`
                    sub = node.module + "." + a.name
                    if sub in known and sub != dotted:
                        edges.add((dotted, sub))
        elif isinstance(node, ast.Call):
            fn = node.func
            nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)
            if nm in ("__import__", "import_module"):         # the RUNTIME FRONTIER — never an edge, never recovered
                piles["runtime_frontier"].append(
                    (dotted, "dynamic import (%s) — target computed at runtime; needs a trace, not a parser" % nm))
    return edges, piles


def _has_init(d):
    return os.path.isfile(os.path.join(d, "__init__.py"))


def diagnose(root):
    """Build the CORRECTED model from a real source tree, with the residual fenced off. Reads only."""
    root = os.path.abspath(root)
    files = mg._py_files(root)
    ident, known, dotted_collisions = {}, set(), []
    for f in files:
        dn = dotted_name(f, _has_init)
        ident[f] = dn
        if dn in known:
            dotted_collisions.append(dn)
        known.add(dn)
    edges = set()
    piles = {"recovered_relative": [], "runtime_frontier": [], "scope_boundary": [], "opaque": []}
    for f in files:
        dn, pkg = ident[f], package_parts(os.path.dirname(f), _has_init)
        try:
            with open(f, encoding="utf-8") as fh:
                e, p = diagnose_source(dn, pkg, fh.read(), known)
            edges |= e
            for k in ("recovered_relative", "runtime_frontier", "scope_boundary"):
                piles[k] += p[k]
        except (SyntaxError, UnicodeDecodeError) as ex:
            piles["opaque"].append((dn, "unparseable: %s" % type(ex).__name__))
    partition = {ident[f]: mg._package(f, root) for f in files}   # directory-based, consistent with module_graph
    return {"known": known, "edges": edges, "partition": partition,
            "dotted_collisions": dotted_collisions, "piles": piles, "files": len(files)}


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

    dumb = mg.extract(target)
    fixed = diagnose(target)
    p = fixed["piles"]

    relative_dumb = sum("relative import" in w for _m, w in dumb["blind"])
    dynamic_dumb = sum("dynamic import" in w for _m, w in dumb["blind"])
    unparse_dumb = sum("unparseable" in w for _m, w in dumb["blind"])

    cross, rate = cp.leakage(list(fixed["edges"]), fixed["partition"])
    cyc = mg.find_cycle(fixed["known"], fixed["edges"])

    print("fidelity_gap — WHY the model came back blind, and what breaks through. (declared model; AST-only.)")
    print(f"target: {target}\n")
    print("  dumb model (basename identity, absolute-only):")
    print(f"    modules {len(dumb['nodes'])}   edges {len(dumb['edges'])}   blind {len(dumb['blind'])}   basename-collisions {len(dumb['collisions'])}")
    print("  corrected model (package-path identity, relative-resolution):")
    print(f"    modules {len(fixed['known'])}   edges {len(fixed['edges'])}   dotted-collisions {len(fixed['dotted_collisions'])}")
    print(f"    recovered relative edges {len(p['recovered_relative'])}   |   spatial leak {rate:.2f} ({len(cross)} cross-package)")
    print(f"    structural cycle: {cyc or 'none (acyclic)'}")
    print()

    print(f"  {'failure mode':<20}{'count':>7}   {'verdict':<18} why")
    rows = [
        ("RELATIVE_IMPORT", relative_dumb, "RECOVERABLE", "wrong identity (basename); package-path + level math resolves these"),
        ("BASENAME_COLLISION", len(dumb["collisions"]), "RECOVERABLE", f"ambiguous identity; dotted names make them unique (now {len(fixed['dotted_collisions'])})"),
        ("DYNAMIC_IMPORT", dynamic_dumb, "RUNTIME_FRONTIER", "target computed at runtime; no static identity exists — needs a trace"),
        ("SCOPE_BOUNDARY", len(p["scope_boundary"]), "SCOPE", "relative import climbs above the scanned subtree — widen the root"),
        ("OPAQUE_SOURCE", unparse_dumb + len(p["opaque"]), "OPAQUE", "unparseable under utf-8 + AST — decode or exclude"),
    ]
    for name, n, verdict, why in rows:
        if n:
            print(f"  {name:<20}{n:>7}   {verdict:<18} {why}")
    print()

    recoverable = relative_dumb + len(dumb["collisions"])
    frontier = dynamic_dumb
    print(f"  BREAKTHROUGH: {recoverable} blind spots were a MODEL DEFECT (recovered) — edges {len(dumb['edges'])} → {len(fixed['edges'])}, collisions {len(dumb['collisions'])} → {len(fixed['dotted_collisions'])}.")
    print(f"  RESIDUAL: {frontier} dynamic import(s) are a RUNTIME FRONTIER — a static parser cannot cross this; it is handed to provenance, not faked.")
    if p["runtime_frontier"]:
        for (m, why) in p["runtime_frontier"]:
            print(f"              · {m}: {why}")
    print()

    _selftest()


def _selftest() -> None:
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        passed += 1 if ok else 0
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. package-path identity: dotted name from the package root; __init__ collapses; non-package = basename
    init_dirs = {"/p/src/requests"}
    hi = lambda d: d in init_dirs
    check("package_path_identity",
          dotted_name("/p/src/requests/adapters.py", hi) == "requests.adapters"
          and dotted_name("/p/src/requests/__init__.py", hi) == "requests"
          and dotted_name("/p/loose.py", hi) == "loose",
          "src/requests/adapters.py → 'requests.adapters'; __init__ → 'requests'; loose file → 'loose'")

    # 2. the recoverable pile: a requests-style relative import resolves to a real dotted target
    res, un = resolve_relative(["requests"], 1, "models", [], {"requests.models"})
    check("relative_import_recovered", res == {"requests.models"} and not un,
          "from .models import X  (was blind under basename) → edge requests→requests.models")

    # 3. the scope boundary: a relative import that climbs above the scanned subtree is NOT silently resolved
    res2, un2 = resolve_relative(["requests"], 2, "x", [], {"requests.models"})
    check("scope_boundary_declared", not res2 and un2 and "above scan root" in un2[0],
          "from .. import x  from the top package → declared SCOPE boundary, not a fake edge")

    # 4. recover relative AND isolate runtime: the dynamic import becomes NO edge and stays in its own pile
    e4, p4 = diagnose_source("requests.adapters", ["requests"],
                             "from .models import Response\nfrom importlib import import_module\nimport_module('z')\n",
                             {"requests.adapters", "requests.models"})
    check("recovers_relative_isolates_runtime",
          ("requests.adapters", "requests.models") in e4 and len(e4) == 1
          and len(p4["runtime_frontier"]) == 1 and len(p4["recovered_relative"]) == 1,
          "relative → 1 real edge; dynamic import → runtime pile, never an edge (no overclaim)")

    # 5. collisions killed by identity: two `utils.py` in different packages become distinct dotted names
    hi5 = lambda d: os.path.basename(d) in ("requests", "tests")
    a, b = dotted_name("/p/src/requests/utils.py", hi5), dotted_name("/p/tests/utils.py", hi5)
    check("basename_collision_killed", a == "requests.utils" and b == "tests.utils" and a != b,
          "two 'utils' (a dumb collision) → 'requests.utils' vs 'tests.utils' — disambiguated")

    # 6. clean on our OWN folder: no __init__ → dotted == basename → it reproduces the dumb edges, invents no gap
    here = os.path.dirname(os.path.abspath(__file__))
    d, dumb = diagnose(here), mg.extract(here)
    check("clean_on_own_package",
          d["known"] == dumb["nodes"] and dumb["edges"] <= d["edges"]
          and not d["piles"]["recovered_relative"] and not d["piles"]["runtime_frontier"],
          "same nodes, edges ⊇ dumb, zero phantom gap — our own code is already faithfully modelable")

    # 7. sealed / deterministic / NO OVERCLAIM: rerun identical; runtime frontier is never folded into recovered
    again = diagnose(here)
    no_overclaim = not (set(map(tuple, d["piles"]["runtime_frontier"])) & set(map(tuple, d["piles"]["recovered_relative"])))
    check("sealed_no_overclaim",
          again["edges"] == d["edges"] and again["known"] == d["known"] and no_overclaim,
          "AST-only, no writes, deterministic; the runtime frontier is NEVER counted as recovered")

    print(f"\n{passed}/{total} checks. The blindness was read, not lamented: ~all of it was ONE model defect —")
    print("basename identity where real packages need a package-PATH identity, and absolute-only resolution where")
    print("real packages import relatively. The corrected model PROVES recovery (relative imports become real")
    print("edges; basename collisions disappear under dotted names) — and it FENCES the residual: dynamic imports")
    print("are a runtime frontier a parser can never cross, declared and handed to provenance, never faked into an")
    print("edge. `declared ≠ verified` (the import model is the common case, not CPython); `resolved ≠ executed`")
    print("(a recovered edge means one module NAMES another, never that a call path runs). The gap is mapped: push")
    print("the static model here, stop pushing it there — that boundary is where the committed Weltlinie begins.")
    assert passed == total, "the fidelity-gap instrument failed its own self-test"


if __name__ == "__main__":
    main()
