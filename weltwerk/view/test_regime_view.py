# SPDX-License-Identifier: AGPL-3.0-only
"""
test_regime_view.py — validity-not-outcome for the regime-aware view.

It proves the renderer shows MEASURED structure, faithfully — not that any region is sparse or dense
(that is what the map reports). The load-bearing check is that an edit's actual divergence never leaves
the reachability cone (no superluminal causality), and that the regime measure is deterministic and
well-defined.

  1. determinism             — same world ⇒ identical regime map
  2. footprint_within_cone   — every edit's actual divergence ⊆ reachability ball radius H
  3. regime_well_defined     — measured spread ∈ [0,1]; every chunk gets exactly one regime class
  4. classes_consistent      — footprint classes ⊆ {committed,potential,actual}; actual ⊆ potential∪actual

Run:  PYTHONHASHSEED=0 python3 test_regime_view.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scale"))

from amplify import cone                                            # noqa: E402
from regime_view import (BAND, DELTA, EPS, H, N, TAU, build_data,   # noqa: E402
                         diverged, gains, het_run, initial, perturb)


def check(name, ok, detail):
    return (name, ok, detail)


def test_determinism():
    a = build_data()["regime"]
    b = build_data()["regime"]
    return check("determinism", a == b, f"identical regime map across runs: {a == b}")


def test_footprint_within_cone():
    rs = gains()
    s0 = initial(N)
    base = het_run(s0, rs, EPS, H)
    ok = True
    for c in (8, 32, 25):
        b = het_run(perturb(s0, c, DELTA), rs, EPS, H)
        within = all(diverged(base[t], b[t], TAU) <= cone(c, N, t) for t in range(H + 1))
        ok = ok and within
    return check("footprint_within_cone", ok,
                 f"actual divergence ⊆ reachability cone ∀t for every edit: {ok}")


def test_regime_well_defined():
    d = build_data()
    fracs = d["regime_frac"]
    classes = d["regime"]
    ok = all(0.0 <= f <= 1.0 for f in fracs) and len(classes) == N \
        and all(c in ("sparse", "marginal", "chaotic") for c in classes)
    return check("regime_well_defined", ok,
                 f"spread∈[0,1], {N} chunks each one of 3 classes: {ok}")


def test_classes_consistent():
    d = build_data()
    ok = True
    for name, fp in d["footprints"].items():
        cl = fp["classes"]
        ok = ok and len(cl) == N and all(x in ("committed", "potential", "actual") for x in cl)
    return check("classes_consistent", ok, f"footprint classes valid ∀ scenario: {ok}")


def main():
    results = [
        test_determinism(),
        test_footprint_within_cone(),
        test_regime_well_defined(),
        test_classes_consistent(),
    ]
    print("test_regime_view — the regime-aware view renders measured structure (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Faithful iff {total}/{total}: the regime map is a deterministic,"
          f"\n  well-defined measurement and every edit footprint stays within the causal cone. Which"
          f"\n  regions are sparse vs chaotic is reported, not presumed.")
    assert passed == total, f"{total - passed} check(s) failed — the regime view is not faithful"


if __name__ == "__main__":
    main()
