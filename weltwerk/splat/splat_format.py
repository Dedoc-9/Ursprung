# SPDX-License-Identifier: AGPL-3.0-only
"""
splat_format.py — Phase 13: the .splat DATA CONTRACT (verified). The Gaussian-splat editor is a projection
LENS; this is the one piece that must be exact — the on-disk encoding the renderer reads and writes.

A Gaussian splat is a 3D anisotropic blob: position, scale (covariance), colour, opacity, orientation.
The common community ".splat" record (antimatter15 layout) is 32 bytes, little-endian:

    offset  bytes  field
    0       12     position  (3 × float32)
    12      12     scale     (3 × float32)         -- per-axis std-dev of the gaussian
    24       4     colour    (4 × uint8 RGBA)      -- A = opacity
    28       4     rotation  (4 × uint8)           -- quaternion, each component (q*128 + 128) clamped 0..255

This module encodes/decodes that record and whole scenes, and generates a synthetic scene so the editor
runs with zero assets. It is pure stdlib and deterministic — the editor's JS mirrors it byte-for-byte.

`encoding ≠ scene-truth`: this fixes the *container*, not what a good capture looks like. Full 3D-covariance
EWA splatting and training (COLMAP/optimisation) are out of scope — see the README.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass, field

SPLAT_BYTES = 32


@dataclass
class Splat:
    pos: tuple = (0.0, 0.0, 0.0)
    scale: tuple = (0.05, 0.05, 0.05)
    color: tuple = (255, 255, 255, 255)   # RGBA 0..255
    rot: tuple = (0.0, 0.0, 0.0, 1.0)     # quaternion (x,y,z,w), components in -1..1


def _q_enc(c: float) -> int:
    return max(0, min(255, int(round(c * 128 + 128))))


def _q_dec(b: int) -> float:
    return (b - 128) / 128.0


def encode_splat(s: Splat) -> bytes:
    return (struct.pack("<3f", *s.pos)
            + struct.pack("<3f", *s.scale)
            + bytes(max(0, min(255, int(c))) for c in s.color)
            + bytes(_q_enc(c) for c in s.rot))


def decode_splat(b: bytes) -> Splat:
    if len(b) != SPLAT_BYTES:
        raise ValueError(f"a .splat record is {SPLAT_BYTES} bytes, got {len(b)}")
    pos = struct.unpack_from("<3f", b, 0)
    scale = struct.unpack_from("<3f", b, 12)
    color = tuple(b[24:28])
    rot = tuple(_q_dec(x) for x in b[28:32])
    return Splat(pos=pos, scale=scale, color=color, rot=rot)


def encode_scene(splats) -> bytes:
    return b"".join(encode_splat(s) for s in splats)


def decode_scene(data: bytes):
    if len(data) % SPLAT_BYTES != 0:
        raise ValueError(f"scene length {len(data)} is not a multiple of {SPLAT_BYTES}")
    return [decode_splat(data[i:i + SPLAT_BYTES]) for i in range(0, len(data), SPLAT_BYTES)]


def make_synthetic(n: int = 6000, seed: int = 0):
    """A recognisable assetless scene: a glowing torus + a ground disk of splats. Deterministic.
    Gives the editor something to render/edit when no capture is loaded."""
    import random
    rng = random.Random(seed)
    out = []
    # torus (R, r) coloured by angle — anisotropic gaussians tangent to the surface
    R, r = 2.4, 0.8
    for _ in range(int(n * 0.6)):
        u, v = rng.uniform(0, math.tau), rng.uniform(0, math.tau)
        x = (R + r * math.cos(v)) * math.cos(u)
        z = (R + r * math.cos(v)) * math.sin(u)
        y = r * math.sin(v) + 1.6
        hue = (u / math.tau)
        col = _hsv(hue, 0.7, 1.0)
        out.append(Splat(pos=(x, y, z), scale=(0.05, 0.05, 0.05), color=(col[0], col[1], col[2], 230)))
    # ground disk
    for _ in range(int(n * 0.4)):
        a, rad = rng.uniform(0, math.tau), math.sqrt(rng.random()) * 7
        x, z = math.cos(a) * rad, math.sin(a) * rad
        g = 40 + int(rng.random() * 50)
        out.append(Splat(pos=(x, 0.0, z), scale=(0.09, 0.02, 0.09), color=(g, g + 6, g + 16, 200)))
    return out


def _hsv(h, s, v):
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return (int(r * 255), int(g * 255), int(b * 255))


def main():
    print("splat_format.py — Phase 13: the .splat data contract (32-byte record)\n")
    s = Splat(pos=(1.0, 2.0, 3.0), scale=(0.1, 0.2, 0.3), color=(200, 100, 50, 240), rot=(0.0, 0.0, 0.0, 1.0))
    b = encode_splat(s); d = decode_splat(b)
    print(f"  record size: {len(b)} bytes (expect {SPLAT_BYTES})")
    print(f"  pos round-trip: {d.pos}  colour: {d.color}")
    scene = make_synthetic(2000)
    enc = encode_scene(scene); dec = decode_scene(enc)
    print(f"  synthetic scene: {len(scene)} splats → {len(enc)} bytes → decoded {len(dec)} splats")
    # write a loadable .splat next to this file so the editor (or any viewer) can open it
    import os
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic.splat")
    with open(out, "wb") as fh:
        fh.write(enc)
    print(f"  wrote {out}  ({len(enc)} bytes) — drop it into weltwerk_splat_editor.html")
    print("\n  the editor's JS mirrors this exact layout; this contract is the only verified part of a lens.")


if __name__ == "__main__":
    main()
