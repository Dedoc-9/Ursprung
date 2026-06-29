# SPDX-License-Identifier: AGPL-3.0-only
"""
test_reality_core_probe.py — the verification backend separates a clean reality_core trace from one whose
diagnostic leaks into the input, grades the invariants honestly, and the CSV round-trips. Validity-not-outcome.
Pure-stdlib (~tens of seconds). Fixtures are generated in Python (the format the Rust dumper writes), so the
probe is validated end-to-end without needing the Rust toolchain.

  1. csv_roundtrip          — write a trace CSV and read_trace() recovers the rows/fields.
  2. clean_air_gap_held     — exogenous inputs ⇒ stress does NOT leak into the next input ⇒ AIR_GAP_HELD.
  3. leak_detected          — a controller that steers x0(t+1) from stress(t) ⇒ OBSERVER_CONTAMINATION.
  4. invariants_pass_clean  — a within-tolerance trace ⇒ all obligations CLOSED/BOUNDED.
  5. invariants_catch_break — a tampered frame (stress=3, or ‖WᵀW-I‖=1) ⇒ VIOLATED.
  6. replay_parity          — identical traces ⇒ CLOSED; a perturbed one ⇒ VIOLATED.

`observation ≠ authority`; `borrow-checker-clean ≠ air-gap-sound`; `undetected ≠ absent`.
"""
from __future__ import annotations

import csv
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))

from reality_core_probe import read_trace, audit_invariants, audit_airgap, replay_parity

FIELDS = ["frame", "x0", "x1", "stress", "sphere_res", "stiefel_res", "residual_ortho", "health"]
N = 6000


def chk(name, ok, detail):
    return (name, ok, detail)


def _clean(n=N, seed=1):
    rng = random.Random(seed)
    rows = []
    for t in range(n):
        rows.append({"frame": float(t), "x0": rng.gauss(0, 1), "x1": rng.gauss(0, 1),
                     "stress": rng.random() * 1.5, "sphere_res": 1e-16, "stiefel_res": 3e-16,
                     "residual_ortho": 1e-16, "health": "Nominal"})
    return rows


def _leaky(n=N, seed=2):
    rng = random.Random(seed)
    rows = []
    prev_stress = 0.0
    for t in range(n):
        stress = rng.random() * 1.5
        # x0(t) is steered by the PREVIOUS frame's stress ⇒ stress(t) leaks into x0(t+1): a broken air-gap
        x0 = float(int(prev_stress / 1.5 * 3)) + rng.gauss(0, 0.05)
        rows.append({"frame": float(t), "x0": x0, "x1": rng.gauss(0, 1), "stress": stress,
                     "sphere_res": 1e-16, "stiefel_res": 3e-16, "residual_ortho": 1e-16, "health": "Nominal"})
        prev_stress = stress
    return rows


def _write_csv(rows, path):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in FIELDS})


def test_csv_roundtrip():
    rows = _clean(50)
    p = os.path.join(tempfile.gettempdir(), "_rc_trace.csv")
    _write_csv(rows, p)
    back = read_trace(p)
    try:
        os.remove(p)
    except OSError:
        pass
    ok = len(back) == 50 and abs(back[10]["stress"] - rows[10]["stress"]) < 1e-9 and back[0]["health"] == "Nominal"
    return chk("csv_roundtrip", ok, f"rows={len(back)}")


def test_clean_air_gap_held():
    r = audit_airgap(_clean(N, 1))
    return chk("clean_air_gap_held", r.verdict == "AIR_GAP_HELD", f"verdict={r.verdict} cmi={r.result.cmi:.4f}")


def test_leak_detected():
    r = audit_airgap(_leaky(N, 2))
    return chk("leak_detected", r.verdict == "OBSERVER_CONTAMINATION", f"verdict={r.verdict} cmi={r.result.cmi:.4f}")


def test_invariants_pass_clean():
    obs = audit_invariants(_clean(2000))
    ok = all(o.status in ("CLOSED", "BOUNDED") for o in obs)
    return chk("invariants_pass_clean", ok, f"statuses={[o.status for o in obs]}")


def test_invariants_catch_break():
    rows = _clean(2000)
    rows[500]["stress"] = 3.0          # out of [0,2]
    rows[900]["stiefel_res"] = 1.0     # frame not orthonormal
    obs = {o.id: o.status for o in audit_invariants(rows)}
    ok = obs["RC-stress-bounded"] == "VIOLATED" and obs["RC-stiefel"] == "VIOLATED"
    return chk("invariants_catch_break", ok, f"stress={obs['RC-stress-bounded']} stiefel={obs['RC-stiefel']}")


def test_replay_parity():
    a = _clean(500, 5)
    same = replay_parity(a, [dict(r) for r in a]).status
    b = _clean(500, 5)
    b[7]["stress"] += 0.1
    diff = replay_parity(a, b).status
    ok = same == "CLOSED" and diff == "VIOLATED"
    return chk("replay_parity", ok, f"identical={same} perturbed={diff}")


def main():
    results = [
        test_csv_roundtrip(),
        test_clean_air_gap_held(),
        test_leak_detected(),
        test_invariants_pass_clean(),
        test_invariants_catch_break(),
        test_replay_parity(),
    ]
    print("test_reality_core_probe — verification backend for dvsm_reality_core\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. observation ≠ authority; borrow-checker-clean ≠ air-gap-sound.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
