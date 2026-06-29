# SPDX-License-Identifier: AGPL-3.0-only
"""
verify.py — the single DVSM verification gate. Runs every DVSM open-core and commercial test suite as an
isolated subprocess and exits non-zero if ANY suite fails. The CI gate behind `make verify`; also runnable
directly: `python verify.py` (or `core` / `commercial`).

ENCODING NOTE: the suites print Unicode separators (≠, ‖, κ). When stdout is a PIPE (as in a subprocess, CI
log, or `> file`), Python uses the locale encoding — cp1252 on Windows — which cannot encode them and raises
UnicodeEncodeError *after* the checks have already passed. So this gate (a) forces the children into UTF-8
mode (`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`) and decodes their output as UTF-8, and (b) reconfigures its
own stdout to UTF-8 so the gate is safe under redirection too. `green-gate ≠ correct-product`; `tested ≠ safe`.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

# make the gate's OWN stdout robust under redirection / cp1252 consoles
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_HERE = os.path.dirname(os.path.abspath(__file__))

# (group, subdir-relative-to-DVSM, filename)
SUITES = [
    ("core", ".", "test_dvsm_reference.py"),
    ("core", ".", "test_coupling_audit.py"),
    ("core", ".", "test_invariant_ledger.py"),
    ("core", ".", "test_dvsm_backend.py"),
    ("commercial", "commercial", "test_kernel_auditor.py"),
    ("commercial", "commercial", "test_commercial_obligations.py"),
    ("commercial", "commercial", "test_binframe_adapter.py"),
]


def run_suite(subdir: str, fname: str) -> tuple:
    path = os.path.join(_HERE, subdir, fname)
    # PYTHONUTF8=1 forces the child's stdio to UTF-8 regardless of the OS locale (fixes the cp1252 pipe crash).
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    t0 = time.time()
    proc = subprocess.run([sys.executable, path], cwd=os.path.dirname(path), env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode == 0, time.time() - t0, proc.stdout, proc.stderr


def main(argv):
    group = argv[1] if len(argv) > 1 else "all"
    suites = [s for s in SUITES if group in ("all", s[0])]
    if not suites:
        print(f"verify.py: unknown group {group!r} (use: all | core | commercial)")
        return 2

    print(f"DVSM verification gate — group={group}, {len(suites)} suite(s), PYTHONHASHSEED=0\n")
    passed = 0
    failures = []
    for _grp, subdir, fname in suites:
        ok, dt, out, err = run_suite(subdir, fname)
        summary = next((ln.strip() for ln in reversed((out or "").splitlines()) if "checks." in ln), "")
        print(f"  [{'PASS' if ok else 'FAIL'}] {subdir}/{fname:32s} ({dt:4.1f}s)  {summary}")
        if ok:
            passed += 1
        else:
            failures.append((fname, out, err))

    total = len(suites)
    print(f"\n  GATE: {passed}/{total} suites passed.")
    if failures:
        for fname, out, err in failures:
            print(f"\n----- FAILED: {fname} -----")
            print("\n".join((out or "").splitlines()[-25:]))
            if (err or "").strip():
                print("[stderr]\n" + "\n".join(err.splitlines()[-15:]))
        print("\n  GATE FAILED. green-gate ≠ correct-product; but a red gate is decisive. tested ≠ safe.")
        return 1
    print("  GATE PASSED. tested ≠ safe; measured ≠ guaranteed; integrity ≠ truth.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
