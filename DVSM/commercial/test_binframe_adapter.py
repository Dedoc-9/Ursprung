# SPDX-License-Identifier: AGPL-3.0-only
"""
test_binframe_adapter.py — the BinaryFrame ingest parses real-format dumps faithfully, flags layout/parse
ghosts instead of emitting garbage, lifts the supportable obligations kernel-relative, and DECLARES what it
cannot lift. Validity-not-outcome. Pure-stdlib.

  1. roundtrip_abi          — pack→write→read recovers energy/hash/ghost exactly (ABI schema with hash).
  2. roundtrip_telem        — pack→read recovers f32 diagnostics exactly (rich telemetry schema).
  3. layout_mismatch_caught — trailing junk ⇒ ParseReport.layout_mismatch (no silent garbage).
  4. nonfinite_caught       — a NaN in the bytes ⇒ ParseReport.nonfinite > 0 (parse/endianness ghost).
  5. containment_lift       — real energies < U_MAX ⇒ BOUNDED; an injected over-bound ⇒ VIOLATED.
  6. replay_parity_lift     — identical dumps ⇒ CLOSED; a perturbed hash ⇒ VIOLATED.
  7. nonliftable_declared   — lift() names Ω→V and ν→λ as NOT liftable (V/λ not emitted).
  8. feeds_kernel_auditor   — parsed real-format rows feed KernelAuditor and produce honest analyses.

Sound iff 8/8. `parsed ≠ correct`; `emitted-telemetry ≠ full-state`; `integrity ≠ truth`.
"""
from __future__ import annotations

import math
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "verify"))

from binframe_adapter import (SCHEMA_ABI, SCHEMA_TELEM, write_binframes, read_binframes, parse_binframes,
                              containment, replay_parity, lift, non_liftable, with_next)
from kernel_auditor import KernelAuditor, CouplingProbe
from artifacts import AnalysisResult, Limitation


def chk(name, ok, detail):
    return (name, ok, detail)


def _tmp(name):
    return os.path.join(tempfile.gettempdir(), name)


def _rm(p):
    try:
        os.remove(p)
    except OSError:
        pass


def _abi_rows(n=2000):
    return [{"frame": i, "energy": float(i % 50), "stress": float(i % 3), "entropy": float(i % 4),
             "ghost": i % 8, "contained": 0, "hash": (i * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF} for i in range(n)]


def _telem_rows(n=4000):
    return [{"frame": i, "energy": float(i % 50), "novelty": float(i % 5), "stress": float(i % 3),
             "stiffness": float(i % 4), "omega_norm": float(i % 6), "entropy": float(i % 4),
             "drift": float(i % 7), "resonance_peak": 0.0, "ghost": i % 8, "contained": 0, "emitted": 1}
            for i in range(n)]


def test_roundtrip_abi():
    rows = _abi_rows(500)
    p = _tmp("_t_abi.bin")
    write_binframes(p, rows, SCHEMA_ABI)
    back, rep = read_binframes(p, SCHEMA_ABI)
    _rm(p)
    ok = rep.ok() and len(back) == 500 and all(
        back[i]["energy"] == rows[i]["energy"] and back[i]["hash"] == rows[i]["hash"]
        and back[i]["ghost"] == rows[i]["ghost"] for i in (0, 137, 499))
    return chk("roundtrip_abi", ok, f"n={rep.n_records} rec={rep.rec_size}B ok={rep.ok()}")


def test_roundtrip_telem():
    rows = _telem_rows(300)
    p = _tmp("_t_telem.bin")
    write_binframes(p, rows, SCHEMA_TELEM)
    back, rep = read_binframes(p, SCHEMA_TELEM)
    _rm(p)
    ok = rep.ok() and all(back[i]["omega_norm"] == rows[i]["omega_norm"]
                          and back[i]["energy"] == rows[i]["energy"] for i in (0, 99, 299))
    return chk("roundtrip_telem", ok, f"n={rep.n_records} rec={rep.rec_size}B ok={rep.ok()}")


def test_layout_mismatch_caught():
    rows = _abi_rows(100)
    p = _tmp("_t_mm.bin")
    write_binframes(p, rows, SCHEMA_ABI)
    with open(p, "rb") as f:
        data = f.read()
    _rm(p)
    _back, rep = parse_binframes(data + b"\x00\x00\x00", SCHEMA_ABI)
    ok = rep.layout_mismatch and rep.leftover_bytes == 3 and not rep.ok()
    return chk("layout_mismatch_caught", ok, f"leftover={rep.leftover_bytes} mismatch={rep.layout_mismatch}")


def test_nonfinite_caught():
    rows = _telem_rows(50)
    rows[10]["energy"] = float("nan")
    p = _tmp("_t_nan.bin")
    write_binframes(p, rows, SCHEMA_TELEM)
    _back, rep = read_binframes(p, SCHEMA_TELEM)
    _rm(p)
    ok = rep.nonfinite >= 1 and not rep.ok()
    return chk("nonfinite_caught", ok, f"nonfinite={rep.nonfinite}")


def test_containment_lift():
    good = containment(_abi_rows(500), u_max=100.0).status
    bad_rows = _abi_rows(500) + [{"frame": 999, "energy": 200.0, "stress": 0.0, "entropy": 0.0,
                                  "ghost": 0, "contained": 0, "hash": 0}]
    bad = containment(bad_rows, u_max=100.0).status
    ok = good == "BOUNDED" and bad == "VIOLATED"
    return chk("containment_lift", ok, f"good={good} over_bound={bad}")


def test_replay_parity_lift():
    a = _abi_rows(400)
    same = replay_parity(a, [dict(r) for r in a]).status
    b = _abi_rows(400)
    b[5]["hash"] ^= 0xFF
    diff = replay_parity(a, b).status
    ok = same == "CLOSED" and diff == "VIOLATED"
    return chk("replay_parity_lift", ok, f"identical={same} perturbed={diff}")


def test_nonliftable_declared():
    nl = dict(non_liftable(_abi_rows(10)))
    ok = any("Ω→V" in k for k in nl) and any("ν→λ" in k for k in nl)
    return chk("nonliftable_declared", ok, f"declared non-liftable: {list(nl.keys())}")


def test_feeds_kernel_auditor():
    rows = with_next(_telem_rows(4000), ("energy",))
    probe = CouplingProbe("omega_to_energy", "real-frame probe", "omega_norm", "energy_next",
                          ("energy",), ("entropy",), True)
    wa = KernelAuditor(probes=(probe,), window=3000).audit(rows)[0]
    honest = all(isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
                 and all(isinstance(l, Limitation) for l in a.limitations) for a in wa.analyses)
    ok = honest and isinstance(wa.posture(), dict)
    return chk("feeds_kernel_auditor", ok, f"posture={wa.posture()}")


def main():
    results = [
        test_roundtrip_abi(),
        test_roundtrip_telem(),
        test_layout_mismatch_caught(),
        test_nonfinite_caught(),
        test_containment_lift(),
        test_replay_parity_lift(),
        test_nonliftable_declared(),
        test_feeds_kernel_auditor(),
    ]
    print("test_binframe_adapter — real BinaryFrame ingest (the B3 lift)\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. parsed ≠ correct; emitted-telemetry ≠ full-state; integrity ≠ truth.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
