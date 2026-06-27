# SPDX-License-Identifier: AGPL-3.0-only
"""
test_snow_infotheory.py — the decisive channel/compression/manifold proofs (validity-not-outcome). Pure-stdlib.

  1. shared_cause_no_channel    — under standard physics (H0): I(X;Y) > 0 (confounded by the shared field) but
                                  I(X;Y|field) ≈ the shuffle null ≈ 0. Confounded MI is NOT a channel.
  2. injected_channel_detected  — under H2 (a real inter-arm channel): I(X;Y|field) ≫ null and ≫ H0 — so the
                                  protocol CAN distinguish a language-channel from shared cause (falsifier valid).
  3. compression_equals_channel — the compression gain over a conditional-independence model equals I(X;Y|field)
                                  exactly: ≈0 for H0, ≈CMI for H2. "Compression finds hidden structure" only if
                                  a channel exists.
  4. manifold_dim_equals_controls— the corpus manifold's effective dimension == the number of physical control
                                  parameters; a spurious parameter adds no dimension.
  5. determinism                — seeded runs agree.

Sound iff 5/5: the ONLY hypothesis-relevant signal (conditional MI between branches) is zero under standard
physics and detectable when truly present — so the language hypothesis is falsifiable, and conventional crystal
growth is sufficient unless a real conditional channel is measured. `confounded-MI ≠ channel`; `manifold ≠ meaning`.

Run:  python3 test_snow_infotheory.py
"""
from __future__ import annotations

from snow_infotheory import (channel_test, compression_gain, gen_H0, gen_H2, manifold_dimension)

_C = channel_test()


def chk(name, ok, detail):
    return (name, ok, detail)


def test_shared_cause_no_channel():
    ok = (_C["H0_MI"] > 0.02                              # arms ARE correlated (shared field)
          and abs(_C["H0_CMI"] - _C["H0_null"]) < 0.01    # but conditional MI ≈ the bias floor
          and _C["H0_CMI"] < 0.02)
    return chk("shared_cause_no_channel", ok,
               f"MI={_C['H0_MI']:.4f}>0 but CMI={_C['H0_CMI']:.4f} ≈ null={_C['H0_null']:.4f}")


def test_injected_channel_detected():
    ok = (_C["H2_CMI"] > 0.05 and _C["H2_CMI"] > 5 * _C["H2_null"] and _C["H2_CMI"] > _C["H0_CMI"])
    return chk("injected_channel_detected", ok,
               f"H2 CMI={_C['H2_CMI']:.4f} ≫ null={_C['H2_null']:.4f} and ≫ H0 CMI={_C['H0_CMI']:.4f}")


def test_compression_equals_channel():
    g0 = compression_gain(gen_H0()[1])
    g2 = compression_gain(gen_H2()[1])
    ok = (abs(g0 - _C["H0_CMI"]) < 1e-9 and abs(g2 - _C["H2_CMI"]) < 1e-9
          and abs(g0) < 0.02 and g2 > 0.05)
    return chk("compression_equals_channel", ok,
               f"gain_H0={g0:.4f}≈0 ; gain_H2={g2:.4f}≈CMI (compression gain == conditional MI)")


def test_manifold_dim_equals_controls():
    m = manifold_dimension()
    ok = (m["effective_dim"] == m["n_physical_controls"] == 2
          and "spurious" not in m["depends_on"] and {"temp", "supersat"} <= set(m["depends_on"]))
    return chk("manifold_dim_equals_controls", ok,
               f"effective_dim={m['effective_dim']} == controls=2; depends_on={m['depends_on']}")


def test_determinism():
    ok = channel_test() == _C
    return chk("determinism", ok, f"repeated channel_test agrees: {ok}")


def main():
    results = [
        test_shared_cause_no_channel(),
        test_injected_channel_detected(),
        test_compression_equals_channel(),
        test_manifold_dim_equals_controls(),
        test_determinism(),
    ]
    print("test_snow_infotheory — conditional mutual information is the decisive test\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:30s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: conditional MI between branches is ≈0 under "
          f"standard\n  physics and detectable when a real channel is injected; compression gain == that "
          f"conditional MI;\n  the manifold is the physical control space. The language hypothesis is falsifiable "
          f"— and not met by H0.")
    assert passed == total, f"{total - passed} check(s) failed — channel/compression/manifold claims not established"


if __name__ == "__main__":
    main()
