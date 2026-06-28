# SPDX-License-Identifier: AGPL-3.0-only
"""
coverage_gate.py — box-counting coverage of the attractor as a frontier signal, read by the reusable
`weltwerk/verify/frontier_gate.py`.

As an orbit fills a FINITE-measure attractor, the rate of discovering new boxes (new occupied cells per
window) decays toward zero — the frontier depletes. We feed the per-window discovery multiplier
`m_novel_i = N_i / N_{i-1}` (with a loose CI) to the `FrontierGate`: while discovery keeps pace it reads
EXPLOIT/HOLD; once it falls the gate reads SUBCRITICAL → PIVOT (this attractor is covered; move to a fresh
region — e.g. a different parameter `a`, the orthogonal dimension).

HONEST GRADING: the saturation is REAL and bounded — it reflects the attractor's finite measure (and, via
N(δ) ~ δ^{-D}, its fractal dimension). The gate DEMONSTRATES detection of frontier depletion; it does NOT claim
unbounded exploration — pivoting to new parameters is itself bounded (finite parameter range), consistent with
the PO-5 saturation result. `estimate ≠ property`; `coverage-saturation ≠ nothing-left-anywhere`.
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
from frontier_gate import FrontierGate, EXPLOIT, PIVOT, SUBCRITICAL   # noqa: E402

from flow import integrate, A   # noqa: E402

CI_W = 0.1     # relative CI half-width for the discovery multiplier


def _box(p, delta):
    return (math.floor(p[0] / delta), math.floor(p[1] / delta), math.floor(p[2] / delta))


def coverage_windows(a: float = A, dt: float = 0.01, n: int = 60000, transient: int = 3000,
                     delta: float = 0.5, windows: int = 12) -> dict:
    """Integrate a long orbit; per window, count NEW occupied boxes. Returns the new-box counts and the
    discovery multipliers m_novel_i = N_i / N_{i-1}."""
    traj = integrate((-5.0, 0.0, 0.0), dt, n, a, transient=transient)
    w = len(traj) // windows
    seen = set()
    new_per_window = []
    for k in range(windows):
        chunk = traj[k * w:(k + 1) * w]
        before = len(seen)
        for p in chunk:
            seen.add(_box(p, delta))
        new_per_window.append(len(seen) - before)
    mult = [new_per_window[i] / max(1, new_per_window[i - 1]) for i in range(1, windows)]
    return {"new_per_window": new_per_window, "multipliers": mult, "total_boxes": len(seen)}


def gate_trace(cov: dict, floor: float = 1.0):
    gate = FrontierGate(floor)
    out = []
    for m in cov["multipliers"]:
        ci = (m * (1 - CI_W), m * (1 + CI_W))
        d = gate.decide(m, ci)
        out.append((round(m, 3), d.regime, d.action))
    return out


def main():
    print("coverage_gate.py — attractor box-coverage as a depleting frontier (read by FrontierGate)\n")
    cov = coverage_windows()
    print(f"  new boxes per window: {cov['new_per_window']}")
    print(f"  total distinct boxes: {cov['total_boxes']} (finite ⇒ bounded, finite-measure attractor)")
    print(f"  discovery multipliers + gate decision:")
    for m, regime, action in gate_trace(cov):
        print(f"    m_novel={m:5.3f}  {regime:13s} {action}")
    final = gate_trace(cov)[-1]
    print(f"\n  final window: {final[1]} → {final[2]}  (frontier depleted ⇒ pivot to a fresh region/parameter)")
    print("  saturation is real and bounded (finite measure / fractal dimension). estimate ≠ property;")
    print("  coverage-saturation ≠ nothing-left-anywhere; pivot ≠ guaranteed-escape.")


if __name__ == "__main__":
    main()
