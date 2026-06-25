# SPDX-License-Identifier: AGPL-3.0-only
"""
test_splat_dsl.py — Phase 14 proofs (validity-not-outcome): the text→splat compiler's guarantees hold.

  1. compiles_and_counts     — a valid scene compiles; primitive densities sum to the splat count
  2. determinism_hash        — same text ⇒ identical content hash (provenance handle)
  3. seed_changes_output     — a different seed ⇒ different hash (the seed actually drives sampling)
  4. unknown_command_error   — a bad command yields a structured {line, kind, message}, not a crash
  5. bad_number_error        — a non-numeric parameter is reported as bad_number with its line
  6. invariants_hold         — every emitted splat has positive scale, finite position, opacity in range
  7. over_cap_rejected       — exceeding the splat cap is reported, not emitted
  8. round_trip              — compiled splats encode/decode back to the same count (mirrors the contract)

Run:  python3 test_splat_dsl.py
"""
from __future__ import annotations

import math

from splat_dsl import MAX_DENSITY, MAX_SPLATS, compile_scene
from splat_format import decode_scene, encode_scene


def check(name, ok, detail):
    return (name, ok, detail)


def test_compiles_and_counts():
    r = compile_scene("seed 1\ntorus pos 0 0 0 R 2 r 0.6 color rainbow density 1000 gscale 0.05\n"
                      "sphere pos 0 0 0 radius 1 color 255 0 0 density 500 gscale 0.05")
    return check("compiles_and_counts", r["ok"] and r["count"] == 1500, f"ok={r['ok']}, count={r.get('count')}")


def test_determinism_hash():
    t = "seed 3\ntorus pos 0 1 0 R 2 r 0.6 color rainbow density 2000 gscale 0.05"
    a, b = compile_scene(t), compile_scene(t)
    return check("determinism_hash", a["hash"] == b["hash"], f"hash {a['hash'][:12]} == {b['hash'][:12]}")


def test_seed_changes_output():
    base = "torus pos 0 1 0 R 2 r 0.6 color rainbow density 2000 gscale 0.05"
    a = compile_scene("seed 1\n" + base); b = compile_scene("seed 2\n" + base)
    return check("seed_changes_output", a["hash"] != b["hash"], f"seed1≠seed2 hash: {a['hash'] != b['hash']}")


def test_unknown_command_error():
    r = compile_scene("torus pos 0 0 0 color rainbow density 10\nspere radius 1")
    e = r.get("errors", [])
    ok = (not r["ok"]) and any(x["kind"] == "unknown_command" and x["line"] == 2 for x in e)
    return check("unknown_command_error", ok, f"errors={[(x['line'],x['kind']) for x in e]}")


def test_bad_number_error():
    r = compile_scene("box pos 0 0 0 size notanumber density 10 gscale 0.05")
    e = r.get("errors", [])
    ok = (not r["ok"]) and any(x["kind"] == "bad_number" for x in e)
    return check("bad_number_error", ok, f"errors={[(x['line'],x['kind']) for x in e]}")


def test_invariants_hold():
    r = compile_scene("seed 5\ntorus pos 0 1 0 R 2 r 0.6 color rainbow density 1500 gscale 0.05\n"
                      "plane pos 0 0 0 size 8 color 40 40 40 density 1000 gscale 0.08 axis xz")
    ok = r["ok"] and all(all(c > 0 for c in s.scale) and all(math.isfinite(c) for c in s.pos)
                         and 0 <= s.color[3] <= 255 for s in r["splats"])
    return check("invariants_hold", ok, f"all splats valid={ok} over {r.get('count')} splats")


def test_over_cap_rejected():
    # each primitive is individually legal (density ≤ MAX_DENSITY) but together they exceed MAX_SPLATS
    line = f"box pos 0 0 0 size 2 color 255 255 255 density {MAX_DENSITY} gscale 0.05\n"
    r = compile_scene(line * 3)              # 3 × 100k = 300k > 200k cap
    ok = (not r["ok"]) and any(x["kind"] == "over_cap" for x in r.get("errors", []))
    return check("over_cap_rejected", ok, f"over_cap reported={ok} (3×{MAX_DENSITY} > {MAX_SPLATS})")


def test_round_trip():
    r = compile_scene("seed 2\nsphere pos 0 1 0 radius 1 color rainbow density 800 gscale 0.05")
    dec = decode_scene(encode_scene(r["splats"]))
    return check("round_trip", len(dec) == r["count"], f"{r['count']} → encode → decode {len(dec)}")


def main():
    results = [
        test_compiles_and_counts(),
        test_determinism_hash(),
        test_seed_changes_output(),
        test_unknown_command_error(),
        test_bad_number_error(),
        test_invariants_hold(),
        test_over_cap_rejected(),
        test_round_trip(),
    ]
    print("test_splat_dsl — Phase 14: the text→splat compiler (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: scenes compile deterministically to a"
          f"\n  content-hashed splat cloud, the seed drives sampling, bad input returns structured per-line"
          f"\n  errors (not crashes), every splat satisfies the invariants, the cap is enforced, and the"
          f"\n  output round-trips through the verified .splat contract.")
    assert passed == total, f"{total - passed} check(s) failed — the text→splat compiler is not sound"


if __name__ == "__main__":
    main()
