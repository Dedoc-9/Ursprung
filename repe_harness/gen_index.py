#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""gen_index.py — auto-generate a machine-parseable function index (JSON) FROM SOURCE, so it cannot drift.

A hand-written manifest/index of file:line + signatures is prose about code (`claim != code`) and goes stale
within one commit. This regenerates the index from the AST, so it is always faithful, and `--check` fails if a
committed index.json is out of sync (wire it as a gate). It gives Claude/agents targeted grep-by-signature
lookups instead of full-file reads, WITHOUT the drift a hand-maintained index carries. `generated != hand-kept`.

Workflow:
  python gen_index.py --root . --out index.json      # write the index (commit it)
  python gen_index.py --root . --check index.json     # CI gate: exit 1 if the committed index is stale
  python gen_index.py --selftest                       # verify the generator itself (no repo needed)
"""
import ast, json, os, argparse


def _emit(fname, node, prefix=""):
    args = [a.arg for a in node.args.args]
    doc = (ast.get_docstring(node) or "").strip().splitlines()
    return {"file": fname, "name": prefix + node.name,
            "signature": f"{prefix + node.name}({', '.join(args)})",
            "lineno": node.lineno, "doc": doc[0] if doc else ""}


def index_file(path):
    fname = os.path.basename(path); out = []
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(_emit(fname, node))
        elif isinstance(node, ast.ClassDef):
            cdoc = (ast.get_docstring(node) or "").strip().splitlines()
            out.append({"file": fname, "name": "class " + node.name, "signature": "class " + node.name,
                        "lineno": node.lineno, "doc": cdoc[0] if cdoc else ""})
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.append(_emit(fname, m, node.name + "."))
    return out


def index_dir(root, prefix="phase"):
    idx = []
    for f in sorted(os.listdir(root)):
        if f.endswith(".py") and f.startswith(prefix):
            idx += index_file(os.path.join(root, f))
    return idx


def selftest():
    import tempfile
    d = tempfile.mkdtemp(); p = os.path.join(d, "phase_fix.py")
    open(p, "w").write("def foo(a, b):\n    '''does foo.'''\n    return a\n\n"
                       "class Bar:\n    '''a bar.'''\n    def m(self, x):\n        '''method m.'''\n        return x\n")
    idx = index_file(p); names = {r["name"] for r in idx}
    foo = [r for r in idx if r["name"] == "foo"][0]
    ok_names = {"foo", "class Bar", "Bar.m"} <= names
    ok_sig = foo["signature"] == "foo(a, b)" and foo["doc"] == "does foo." and foo["lineno"] == 1
    ok_method = any(r["name"] == "Bar.m" and r["signature"] == "Bar.m(self, x)" for r in idx)
    ok_det = index_file(p) == idx
    open(p, "a").write("\ndef baz():\n    return 1\n")
    ok_drift = index_file(p) != idx
    print(f"[selftest] extracts funcs+classes+methods  : {ok_names}")
    print(f"[selftest] signature+doc+lineno correct    : {ok_sig}")
    print(f"[selftest] method qualname Bar.m(self, x)  : {ok_method}")
    print(f"[selftest] deterministic regeneration      : {ok_det}")
    print(f"[selftest] drift detected on edit (--check): {ok_drift}")
    ok = ok_names and ok_sig and ok_method and ok_det and ok_drift
    print(f"[selftest] {'PASS 5/5 - generated index faithful + drift-detecting (never silently stale)' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="auto-generate a drift-proof function index from source")
    ap.add_argument("--root", default="."); ap.add_argument("--prefix", default="phase")
    ap.add_argument("--out"); ap.add_argument("--check"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    idx = index_dir(a.root, a.prefix)
    if a.check:
        committed = json.load(open(a.check, encoding="utf-8"))
        if committed != idx:
            print("INDEX STALE — regenerate: gen_index.py --root %s --out %s" % (a.root, a.check)); raise SystemExit(1)
        print("index in sync (%d entries)" % len(idx)); return
    text = json.dumps(idx, indent=2)
    if a.out:
        open(a.out, "w").write(text); print("wrote %d entries -> %s" % (len(idx), a.out))
    else:
        print(text)


if __name__ == "__main__":
    main()
