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
    ("core", ".", "test_reality_core_probe.py"),
    ("core", ".", "test_kappa_remediation.py"),
    ("core", ".", "test_discrete_certificate.py"),
    ("commercial", "commercial", "test_kernel_auditor.py"),
    ("commercial", "commercial", "test_commercial_obligations.py"),
    ("commercial", "commercial", "test_binframe_adapter.py"),
    ("commercial", "commercial", "test_compliance_doc.py"),
    ("commercial", "commercial", "test_live_gate.py"),
]


def run_suite(subdir: str, fname: str) -> tuple:
    path = os.path.join(_HERE, subdir, fname)
    # PYTHONUTF8=1 forces the child's stdio to UTF-8 regardless of the OS locale (fixes the cp1252 pipe crash).
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    t0 = time.time()
    proc = subprocess.run([sys.executable, path], cwd=os.path.dirname(path), env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    return proc.returncode == 0, time.time() - t0, proc.stdout, proc.stderr


def _live_commercial_gate(results: dict) -> int:
    """Obligation B (static-check → live-run): a SUPPORTED commercial claim's backing test suite must have
    PASSED in THIS run. Drop a fresh receipt next to verify.py, then audit the ledger against it. Fails closed.
    HONEST CEILING: `receipt ≠ proof`; `tested ≠ safe` — this proves the suite RAN AND PASSED in this build,
    never that the suite is correct or complete; the receipt is a trusted build-environment artifact."""
    run_id = "%d-%d" % (int(time.time()), os.getpid())
    receipt = os.path.join(_HERE, ".verify_receipt.tsv")
    try:
        with open(receipt, "w", encoding="utf-8") as f:
            f.write("# suite\tstatus\trun_id  (receipt != proof; tested != safe: ran+passed here, not 'correct')\n")
            for suite in sorted(results):
                f.write("%s\t%s\t%s\n" % (suite, "PASS" if results[suite] else "FAIL", run_id))
    except OSError as e:
        print(f"  LIVE GATE: cannot write receipt ({e}) — failing closed.")
        return 1
    sys.path.insert(0, os.path.join(_HERE, "commercial"))
    try:
        from commercial_obligations import COMMERCIAL_CLAIMS, audit_commercial_ledger
    except Exception as e:                                                   # noqa: BLE001
        print(f"  LIVE GATE: cannot import commercial ledger ({e}) — failing closed.")
        return 1
    live = {s: ("PASS" if ok else "FAIL") for s, ok in results.items()}
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS, live_receipts=live)
    if a["unverified_live"]:
        print(f"\n  LIVE GATE FAILED: supported claims whose backing suite did not PASS in this run: "
              f"{a['unverified_live']}. static-check ≠ live-execution; receipt ≠ proof.")
        return 1
    print(f"  LIVE GATE PASSED: every supported claim's backing suite PASSED this run (run_id={run_id}). "
          f"receipt ≠ proof; tested ≠ safe.")
    return 0


def main(argv):
    group = argv[1] if len(argv) > 1 else "all"
    suites = [s for s in SUITES if group in ("all", s[0])]
    if not suites:
        print(f"verify.py: unknown group {group!r} (use: all | core | commercial)")
        return 2

    print(f"DVSM verification gate — group={group}, {len(suites)} suite(s), PYTHONHASHSEED=0\n")
    passed = 0
    failures = []
    results = {}
    for _grp, subdir, fname in suites:
        ok, dt, out, err = run_suite(subdir, fname)
        results[os.path.splitext(fname)[0]] = ok
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
    if group == "all":
        # Obligation B: bind the commercial gate to THIS run. Only meaningful on a full run (a partial group
        # lacks some backing suites), so it is skipped for `core` / `commercial`.
        rc = _live_commercial_gate(results)
        if rc != 0:
            return rc
    print("  GATE PASSED. tested ≠ safe; measured ≠ guaranteed; integrity ≠ truth.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
