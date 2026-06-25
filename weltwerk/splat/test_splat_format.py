# SPDX-License-Identifier: AGPL-3.0-only
"""
test_splat_format.py — Phase 13 proofs (validity-not-outcome): the .splat data contract is exact.

The renderer is a lens, but its on-disk encoding must be byte-exact or every viewer disagrees.

  1. record_is_32_bytes      — one splat encodes to exactly 32 bytes
  2. field_layout            — position at offset 0, colour at offset 24 (the documented layout)
  3. position_exact          — float32 position survives encode→decode exactly
  4. color_exact             — uint8 RGBA survives exactly
  5. quat_quantization       — rotation round-trips within the 1/128 quantization tolerance
  6. scene_round_trip        — a whole scene encodes and decodes to the same count + positions
  7. bad_length_rejected     — a non-multiple-of-32 buffer is rejected
  8. determinism             — the synthetic scene is identical across runs

Run:  python3 test_splat_format.py
"""
from __future__ import annotations

import struct

from splat_format import (SPLAT_BYTES, Splat, decode_scene, decode_splat, encode_scene,
                          encode_splat, make_synthetic)


def check(name, ok, detail):
    return (name, ok, detail)


def test_record_is_32_bytes():
    b = encode_splat(Splat())
    return check("record_is_32_bytes", len(b) == 32, f"len={len(b)}")


def test_field_layout():
    s = Splat(pos=(1.0, 2.0, 3.0), color=(11, 22, 33, 44))
    b = encode_splat(s)
    pos = struct.unpack_from("<3f", b, 0)
    col = tuple(b[24:28])
    return check("field_layout", pos == (1.0, 2.0, 3.0) and col == (11, 22, 33, 44),
                 f"pos@0={pos}, colour@24={col}")


def test_position_exact():
    s = Splat(pos=(1.25, -3.5, 7.75))     # exact in float32
    d = decode_splat(encode_splat(s))
    return check("position_exact", d.pos == (1.25, -3.5, 7.75), f"pos={d.pos}")


def test_color_exact():
    d = decode_splat(encode_splat(Splat(color=(200, 100, 50, 240))))
    return check("color_exact", d.color == (200, 100, 50, 240), f"colour={d.color}")


def test_quat_quantization():
    s = Splat(rot=(0.0, 0.5, -0.5, 1.0))
    d = decode_splat(encode_splat(s))
    err = max(abs(a - b) for a, b in zip(s.rot, d.rot))
    return check("quat_quantization", err <= 1 / 128 + 1e-9, f"max component error {round(err,5)} ≤ 1/128")


def test_scene_round_trip():
    scene = make_synthetic(500)
    dec = decode_scene(encode_scene(scene))
    same_n = len(dec) == len(scene)
    same_pos = all(decode_splat(encode_splat(a)).pos == b.pos for a, b in zip(scene, dec))
    return check("scene_round_trip", same_n and same_pos, f"{len(scene)} → {len(dec)} splats, positions preserved={same_pos}")


def test_bad_length_rejected():
    raised = False
    try:
        decode_scene(b"\x00" * 30)        # not a multiple of 32
    except ValueError:
        raised = True
    return check("bad_length_rejected", raised, f"non-multiple-of-32 rejected={raised}")


def test_determinism():
    a = encode_scene(make_synthetic(300)); b = encode_scene(make_synthetic(300))
    return check("determinism", a == b, f"synthetic scene identical across runs: {a == b}")


def main():
    results = [
        test_record_is_32_bytes(),
        test_field_layout(),
        test_position_exact(),
        test_color_exact(),
        test_quat_quantization(),
        test_scene_round_trip(),
        test_bad_length_rejected(),
        test_determinism(),
    ]
    print("test_splat_format — Phase 13: the .splat data contract (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a splat is exactly 32 bytes with the"
          f"\n  documented layout, position/colour survive exactly, rotation within quantization, scenes"
          f"\n  round-trip, malformed buffers are rejected, and the synthetic scene is deterministic.")
    assert passed == total, f"{total - passed} check(s) failed — the .splat contract is not exact"


if __name__ == "__main__":
    main()
