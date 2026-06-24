# SPDX-License-Identifier: AGPL-3.0-only
"""
test_causal_metrics.py — Phase 4 instrumentation proofs (validity-not-outcome).

Costs are deterministic op-counts; the warning fires honestly on coupled worlds. No latency is asserted.

  1. deterministic        — same world+event ⇒ identical metrics
  2. transport_saving     — causal sends fewer bytes than naive (event vs records)
  3. warning_dense_only   — dense world warns "compression unavailable"; sparse world does not
  4. replay_cheaper_sparse— in a sparse world, replay ops < snapshot bytes-equivalent (footprint ≪ N)
  5. footprint_fraction   — dense footprint fraction > sparse (the regime-dependence, measured)

Run:  PYTHONHASHSEED=0 python3 test_causal_metrics.py
"""
from __future__ import annotations

from causal_metrics import instrument_event
from causal_net import DENSE_WORLD, SPARSE_WORLD


def check(name, ok, detail):
    return (name, ok, detail)


def test_deterministic():
    a = instrument_event(SPARSE_WORLD, "generator")
    b = instrument_event(SPARSE_WORLD, "generator")
    return check("deterministic", a == b, f"same world+event ⇒ identical metrics: {a == b}")


def test_transport_saving():
    m = instrument_event(DENSE_WORLD, "generator")
    ok = m["replication_causal_bytes"] < m["replication_naive_bytes"] and m["transport_saving"] > 0
    return check("transport_saving", ok,
                 f"causal {m['replication_causal_bytes']}B < naive {m['replication_naive_bytes']}B "
                 f"({int(m['transport_saving']*100)}%)")


def test_warning_dense_only():
    dense = instrument_event(DENSE_WORLD, "generator")
    sparse = instrument_event(SPARSE_WORLD, "generator")
    ok = dense["warning"] is not None and sparse["warning"] is None
    return check("warning_dense_only", ok,
                 f"dense warns={dense['warning'] is not None}; sparse silent={sparse['warning'] is None}")


def test_replay_cheaper_sparse():
    m = instrument_event(SPARSE_WORLD, "generator")
    # sparse: footprint ≪ N ⇒ replaying the event touches far less than a full snapshot
    ok = m["footprint"] < m["world_entities"]
    return check("replay_cheaper_sparse",
                 ok, f"sparse footprint {m['footprint']} < world {m['world_entities']}")


def test_footprint_fraction():
    dense = instrument_event(DENSE_WORLD, "generator")["footprint_fraction"]
    sparse = instrument_event(SPARSE_WORLD, "generator")["footprint_fraction"]
    return check("footprint_fraction", dense > sparse,
                 f"dense {dense} > sparse {sparse} (regime-dependence, measured)")


def main():
    results = [
        test_deterministic(),
        test_transport_saving(),
        test_warning_dense_only(),
        test_replay_cheaper_sparse(),
        test_footprint_fraction(),
    ]
    print("test_causal_metrics — Phase 4 cost instrumentation (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: metrics deterministic, causal transport"
          f"\n  cheaper, the 'compression unavailable' warning fires on dense (not sparse) worlds, and the"
          f"\n  measured footprint fraction is regime-dependent. Op-counts only; no latency claimed.")
    assert passed == total, f"{total - passed} check(s) failed — instrumentation is not sound"


if __name__ == "__main__":
    main()
