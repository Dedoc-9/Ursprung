#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""session_verifier.py — grep-verify that a cited symbol appears VERBATIM in a source file.

Enforces the session operating contract's rule 1 (`claim != code`): before anyone states that a function,
string literal, or enum exists, this tool greps the file and prints the exact matching line(s) + number.
It is the mechanical form of "when you are about to claim something is verified: quote the line."

Usage:
  python session_verifier.py residual_channel.py "RESIDUAL_MISSPEC_STABLE"
  python session_verifier.py epistemic_types.py "synthesize_gate" "Grounded"
  python session_verifier.py --root /path/to/repo claim_ledger.py "SUPPORTED"
  python session_verifier.py --manifest session_symbols.txt
  python session_verifier.py --selftest

Path resolution: FILE may be a path relative to repo root (e.g. weltwerk/verify/residual_channel.py) OR a bare
basename (e.g. residual_channel.py). A bare basename is resolved by searching the repo tree; if it matches more
than one file the result is UNREADABLE (ambiguous) and the candidates are listed — the tool REFUSES to silently
pick one. (Silently taking the first match is the `head -1` trap this session already hit once with world.py.)

Per-symbol status:
  VERIFIED    the string was found verbatim (>=1 line); the line(s) + number are printed
  GHOST       the string was NOT found; flagged as requiring investigation
  UNREADABLE  the FILE could not be resolved to exactly one readable file

Exit code: 0 iff EVERY symbol is VERIFIED; 1 if any GHOST; 2 if any UNREADABLE and no GHOST.
(So "exit 0 only if every symbol is VERIFIED" and "exit 1 on any GHOST" both hold; UNREADABLE gets its own
non-zero code so a missing file is distinguishable from a missing symbol.)

GRADE:         VERIFIED (apparatus) when --selftest passes — the matcher's OWN logic is exercised.
DOES_NOT_SHOW: that a matched symbol is semantically correct, defined, reachable, imported, or used as intended
               — ONLY that the exact characters appear on the printed line. A hit inside a comment, a string
               literal, or a docstring still counts as VERIFIED. `verbatim-match != semantics`.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

SKIP_DIRS = {".git", "target", "__pycache__", "node_modules", ".venv", ".mypy_cache", "build", "dist"}
VERIFIED, GHOST, UNREADABLE = "VERIFIED", "GHOST", "UNREADABLE"


def _safe_print(s: str = "") -> None:
    """Print that survives a Windows cp1252 console when a matched line carries `!=`/`κ`/`λ`/`⊇` etc.
    (the repo's own AGENTS.md PYTHONUTF8 gotcha under redirected output). Falls back to a lossy encode."""
    try:
        print(s)
    except UnicodeEncodeError:
        enc = (sys.stdout.encoding or "utf-8")
        sys.stdout.buffer.write((s + "\n").encode(enc, errors="replace"))


def find_root(explicit: str | None = None) -> Path:
    """--root wins; else the nearest ancestor of this script carrying a repo marker; else the script's dir."""
    if explicit:
        return Path(explicit).resolve()
    here = Path(__file__).resolve().parent
    for d in (here, *here.parents):
        if (d / ".git").exists() or (d / "method.md").exists() or (d / "AGENTS.md").exists():
            return d
    return here


def resolve_file(root: Path, arg: str):
    """Return (path, None) for exactly one readable file, else (None, reason).
    Accepts a root-relative path OR a bare basename (searched tree-wide; ambiguity is refused, not resolved)."""
    direct = root / arg
    if direct.is_file():
        return direct, None
    name = Path(arg).name
    matches = []
    for p in root.rglob(name):
        rel_parts = p.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if p.is_file():
            matches.append(p)
    if len(matches) == 1:
        return matches[0], None
    if not matches:
        return None, f"not found under {root}"
    rels = ", ".join(str(m.relative_to(root)) for m in sorted(matches))
    return None, f"ambiguous basename '{name}' — {len(matches)} matches: {rels} (pass a root-relative path)"


def grep_symbol(path: Path, symbol: str):
    """Literal (verbatim) substring search — NOT regex, NOT parsing. Returns [(lineno, line), ...]."""
    hits = []
    with path.open(encoding="utf-8", errors="strict") as f:
        for i, line in enumerate(f, 1):
            if symbol in line:
                hits.append((i, line.rstrip("\n")))
    return hits


def verify(root: Path, filearg: str, symbols):
    """Verify each symbol against one file. Prints a panel per symbol; returns {symbol: status}."""
    path, reason = resolve_file(root, filearg)
    if path is None:
        _safe_print(f"[{UNREADABLE}] {filearg}: {reason}")
        return {s: UNREADABLE for s in symbols}
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    statuses = {}
    for s in symbols:
        try:
            hits = grep_symbol(path, s)
        except (OSError, UnicodeDecodeError) as e:
            statuses[s] = UNREADABLE
            _safe_print(f"[{UNREADABLE}] {rel} :: {s!r}: {e}")
            continue
        if hits:
            statuses[s] = VERIFIED
            _safe_print(f"[{VERIFIED}] {rel} :: {s!r}  ({len(hits)} line(s))")
            for ln, text in hits:
                _safe_print(f"    {ln}: {text.strip()}")
        else:
            statuses[s] = GHOST
            _safe_print(f"[{GHOST}] {rel} :: {s!r}  — NOT FOUND; requires investigation")
    return statuses


def exit_code(statuses) -> int:
    vals = list(statuses)
    if vals and all(v == VERIFIED for v in vals):
        return 0
    if any(v == GHOST for v in vals):
        return 1
    return 2  # some UNREADABLE, no GHOST (or empty)


def parse_manifest(text: str):
    """Parse 'path :: symbol [:: symbol ...]' lines. Skips blank lines and #comments. Returns [(path, [syms])]."""
    entries = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("::")]
        path, syms = parts[0], [p for p in parts[1:] if p]
        if path and syms:
            entries.append((path, syms))
    return entries


def run_manifest(root: Path, manifest_arg: str) -> int:
    """Verify every 'path :: symbol' entry in a manifest file. One panel per file; one aggregate exit code."""
    mp = Path(manifest_arg)
    if not mp.is_file():
        mp = root / manifest_arg
    if not mp.is_file():
        _safe_print(f"[{UNREADABLE}] manifest {manifest_arg!r}: not found (cwd or repo root)")
        return 2
    entries = parse_manifest(mp.read_text(encoding="utf-8"))
    all_status = []
    for path, syms in entries:
        all_status.extend(verify(root, path, syms).values())
    v = all_status.count(VERIFIED); g = all_status.count(GHOST); u = all_status.count(UNREADABLE)
    _safe_print("")
    _safe_print(f"[manifest] {len(entries)} file-entries, {len(all_status)} symbols: "
                f"{v} VERIFIED, {g} GHOST, {u} UNREADABLE  ->  exit {exit_code(all_status)}")
    return exit_code(all_status)


def selftest() -> int:
    """Validity-not-outcome: exercise the matcher's own logic on synthetic files (no repo, deterministic)."""
    import tempfile
    d = Path(tempfile.mkdtemp())
    src = d / "sample.py"
    src.write_text(
        "def synthesize_gate(a, b):\n"
        "    '''RESIDUAL_MISSPEC_STABLE also appears in this docstring.'''\n"
        "    return a  # note: grounded != true (κ, λ, ⊇ unicode on this line)\n"
        'SUPPORTED = {"ESTABLISHED", "MEASURED"}\n',
        encoding="utf-8")

    def run(filearg, syms):
        st = verify(d, filearg, syms)
        return st, exit_code(st.values())

    checks = []
    st, code = run("sample.py", ["synthesize_gate"])
    checks.append(("verbatim hit -> VERIFIED, exit 0", st["synthesize_gate"] == VERIFIED and code == 0))

    st, code = run("sample.py", ["run_residual_channel_audit"])
    checks.append(("absent symbol -> GHOST, exit 1", st["run_residual_channel_audit"] == GHOST and code == 1))

    st, code = run("does_not_exist.py", ["x"])
    checks.append(("missing file -> UNREADABLE, exit 2", st["x"] == UNREADABLE and code == 2))

    st, code = run("sample.py", ["synthesize_gate", "PHANTOM"])
    checks.append(("mixed found+absent -> exit 1 (GHOST dominates)",
                   st["synthesize_gate"] == VERIFIED and st["PHANTOM"] == GHOST and code == 1))

    st, _ = run("sample.py", ["RESIDUAL_MISSPEC_STABLE"])
    checks.append(("comment/docstring hit still VERIFIED (does_not_show)", st["RESIDUAL_MISSPEC_STABLE"] == VERIFIED))

    st, _ = run("sample.py", ["SUPPORTED"])
    checks.append(("string-literal set hit VERIFIED", st["SUPPORTED"] == VERIFIED))

    nested = d / "pkg" / "sub"
    nested.mkdir(parents=True)
    (nested / "deep.py").write_text("MARKER_X = 1\n", encoding="utf-8")
    st, _ = run("deep.py", ["MARKER_X"])
    checks.append(("bare basename resolved across tree", st["MARKER_X"] == VERIFIED))

    (d / "pkg" / "dup.py").write_text("A = 1\n", encoding="utf-8")
    (nested / "dup.py").write_text("A = 1\n", encoding="utf-8")
    st, code = run("dup.py", ["A"])
    checks.append(("ambiguous basename -> UNREADABLE (refuses silent pick)", st["A"] == UNREADABLE and code == 2))

    st, _ = run("sample.py", ["grounded != true"])
    checks.append(("unicode line matched + printed without crashing", st["grounded != true"] == VERIFIED))

    st, _ = run("sample.py", ["synthesize_gate(a, b)"])
    checks.append(("verbatim substring incl. signature fragment", st["synthesize_gate(a, b)"] == VERIFIED))

    ents = parse_manifest("# comment\n\nsample.py :: A :: B\n")
    checks.append(("manifest parse: skips comments/blanks, multi-symbol", ents == [("sample.py", ["A", "B"])]))
    green = d / "green.txt"
    green.write_text("sample.py :: synthesize_gate\nsample.py :: SUPPORTED\n", encoding="utf-8")
    checks.append(("manifest all-verified -> exit 0", run_manifest(d, str(green)) == 0))
    red = d / "red.txt"
    red.write_text("sample.py :: synthesize_gate\nsample.py :: NOPE_PHANTOM\n", encoding="utf-8")
    checks.append(("manifest with a ghost -> exit 1", run_manifest(d, str(red)) == 1))

    _safe_print("")
    ok_all = True
    for label, ok in checks:
        _safe_print(f"[selftest] {label:54s}: {ok}")
        ok_all = ok_all and ok
    npass = sum(1 for _, ok in checks if ok)
    n = len(checks)
    _safe_print(f"[selftest] {('PASS %d/%d - apparatus VERIFIED' % (npass, n)) if ok_all else ('FAIL %d/%d' % (npass, n))}")
    _safe_print("[grade]    VERIFIED (apparatus) — matcher logic exercised on synthetic files; deterministic.")
    _safe_print("[bound]    DOES_NOT_SHOW: that any matched symbol is semantically correct/defined/used —")
    _safe_print("[bound]    only that the exact characters appear on the printed line. verbatim-match != semantics.")
    return 0 if ok_all else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="grep-verify a cited symbol appears verbatim in a source file")
    ap.add_argument("file", nargs="?", help="path relative to repo root, or a bare basename")
    ap.add_argument("symbols", nargs="*", help="one or more symbol strings to verify verbatim")
    ap.add_argument("--root", help="repo root (default: nearest ancestor with .git / method.md / AGENTS.md)")
    ap.add_argument("--manifest", help="a file of 'path :: symbol [:: symbol ...]' lines to verify in one run")
    ap.add_argument("--selftest", action="store_true", help="exercise the matcher's own logic (no repo needed)")
    a = ap.parse_args()
    if a.selftest:
        raise SystemExit(selftest())
    if a.manifest:
        raise SystemExit(run_manifest(find_root(a.root), a.manifest))
    if not a.file or not a.symbols:
        ap.error("need FILE and at least one SYMBOL (or --manifest / --selftest)")
    statuses = verify(find_root(a.root), a.file, a.symbols)
    raise SystemExit(exit_code(statuses.values()))


if __name__ == "__main__":
    main()
