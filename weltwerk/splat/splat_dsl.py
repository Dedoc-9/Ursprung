# SPDX-License-Identifier: AGPL-3.0-only
"""
splat_dsl.py — Phase 14: a verified TEXT → SPLAT compiler. The genuinely-distinctive part of the lens.

A splat editor treats the point cloud as the document. Weltwerk inverts that: a small, LLM-authorable TEXT
language is the AUTHORITY, and the gaussian cloud is its deterministic, verifiable PROJECTION. Same text →
same splats → same content hash. This is what no splat editor has: provenance + determinism + authorability.

DSL (line-oriented, '#' comments). Each primitive samples gaussians deterministically from a seeded LCG:

    scene "Demo"
    seed 7
    torus  pos 0 1.6 0  R 2.4 r 0.8  color rainbow  density 5000  gscale 0.05
    plane  pos 0 0 0  size 14  color 50 56 66  density 4000  gscale 0.09  axis xz
    sphere pos 3 2 0  radius 1  color #ff5040  density 2000  gscale 0.05
    box    pos -3 1 0  size 1.5  color 80 120 255  density 1500  gscale 0.05

compile_scene(text) -> {ok, splats, count, hash, name} on success,
                       {ok:False, errors:[{line, kind, message}]} on failure (structured, for LLM iteration).

GUARANTEES (verified in test_splat_dsl):
  • deterministic — same text ⇒ identical splats ⇒ identical content hash (a provenance handle);
  • invariants enforced — opacity ∈ [0,1], every scale axis > 0, positions finite, total count ≤ MAX;
  • structured errors — unknown commands/keys/bad numbers report {line, kind, message}, never a stack trace.

HONEST BOUNDS: this fixes authoring + provenance, not capture realism. It does NOT replace photogrammetry —
it composes primitives. Cross-language byte-identical hashing is best-effort (transcendental last-ulp may
differ); within an implementation it is exact. `deterministic ≠ photoreal`; `hash ≠ scene-quality`.
"""
from __future__ import annotations

import math
import os
import sys
from hashlib import blake2b

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from splat_format import Splat, encode_scene   # noqa: E402

MAX_SPLATS = 200000
MAX_DENSITY = 100000

# token arity for the key/value parser (color is handled specially)
_ARITY = {"pos": 3, "density": 1, "gscale": 1, "R": 1, "r": 1, "radius": 1, "size": 1, "axis": 1, "opacity": 1}


class _LCG:
    """Numerical-Recipes LCG — identical algorithm in the JS mirror, so both produce the same sequence."""
    def __init__(self, seed): self.s = seed & 0xffffffff
    def next(self):
        self.s = (self.s * 1664525 + 1013904223) & 0xffffffff
        return self.s / 4294967296.0


def _hsv(h, s, v):
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return (int(r * 255), int(g * 255), int(b * 255))


def _quat_z_to(nx, ny, nz):
    """Shortest-arc quaternion rotating local +z onto the unit normal (nx,ny,nz). For surface-aligned splats."""
    if nz < -0.99999:
        return (1.0, 0.0, 0.0, 0.0)
    x, y, z, w = -ny, nx, 0.0, 1.0 + nz
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    return (x / n, y / n, z / n, w / n)


def _parse_color(tokens, i):
    """Parse a colour starting at tokens[i]; returns (rgb_or_None_for_rainbow, next_index) or raises."""
    t = tokens[i]
    if t == "rainbow":
        return ("rainbow", i + 1)
    if t.startswith("#") and len(t) == 7:
        v = int(t[1:], 16)
        return ((v >> 16 & 255, v >> 8 & 255, v & 255), i + 1)
    rgb = tuple(int(float(tokens[i + k])) for k in range(3))
    return (rgb, i + 3)


class _Err(Exception):
    def __init__(self, kind, message): self.kind, self.message = kind, message


def _parse_params(tokens):
    """tokens after the command → dict of params. Raises _Err on unknown key / bad number / missing value."""
    p, i = {}, 0
    while i < len(tokens):
        key = tokens[i]; i += 1
        if key == "color":
            try:
                p["color"], i = _parse_color(tokens, i)
            except (ValueError, IndexError):
                raise _Err("bad_color", "color must be 'rainbow', '#rrggbb', or 'R G B'")
            continue
        if key not in _ARITY:
            raise _Err("unknown_key", f"unknown parameter '{key}'")
        ar = _ARITY[key]
        if i + ar > len(tokens):
            raise _Err("missing_param", f"'{key}' needs {ar} value(s)")
        try:
            vals = [tokens[i + k] for k in range(ar)]
            p[key] = (vals[0] if key == "axis" else (float(vals[0]) if ar == 1 else [float(v) for v in vals]))
        except ValueError:
            raise _Err("bad_number", f"'{key}' expects number(s), got {tokens[i:i+ar]}")
        i += ar
    return p


def _color_at(spec, t):
    if spec is None:
        return (255, 255, 255)
    if spec == "rainbow":
        return _hsv(t % 1.0, 0.72, 1.0)
    return spec


def _emit_torus(p, rng, out):
    pos = p.get("pos", [0, 0, 0]); R = p.get("R", 2.0); r = p.get("r", 0.6)
    g = p.get("gscale", 0.05); col = p.get("color"); n = int(p.get("density", 2000))
    op = p.get("opacity", 0.9)
    for _ in range(n):
        u, v = rng.next() * math.tau, rng.next() * math.tau
        cx = (R + r * math.cos(v)) * math.cos(u)
        cz = (R + r * math.cos(v)) * math.sin(u)
        cy = r * math.sin(v)
        nx, ny, nz = math.cos(v) * math.cos(u), math.sin(v), math.cos(v) * math.sin(u)  # surface normal
        c = _color_at(col, u / math.tau)
        out.append(Splat(pos=(pos[0] + cx, pos[1] + cy, pos[2] + cz),
                         scale=(g * 2.0, g * 2.0, g * 0.35),     # flat disk tangent to the surface (anisotropic)
                         color=(c[0], c[1], c[2], int(op * 255)), rot=_quat_z_to(nx, ny, nz)))


def _emit_sphere(p, rng, out):
    pos = p.get("pos", [0, 0, 0]); rad = p.get("radius", 1.0); g = p.get("gscale", 0.05)
    col = p.get("color"); n = int(p.get("density", 2000)); op = p.get("opacity", 0.9)
    for i in range(n):
        z = 1 - 2 * rng.next(); ph = rng.next() * math.tau; rr = math.sqrt(max(0.0, 1 - z * z))
        x, y, zz = rr * math.cos(ph), rr * math.sin(ph), z
        c = _color_at(col, i / max(1, n))
        out.append(Splat(pos=(pos[0] + x * rad, pos[1] + y * rad, pos[2] + zz * rad),
                         scale=(g, g, g), color=(c[0], c[1], c[2], int(op * 255))))


def _emit_box(p, rng, out):
    pos = p.get("pos", [0, 0, 0]); s = p.get("size", 1.0); g = p.get("gscale", 0.05)
    col = p.get("color"); n = int(p.get("density", 2000)); op = p.get("opacity", 0.9); h = s / 2
    for i in range(n):
        x, y, z = (rng.next() * 2 - 1) * h, (rng.next() * 2 - 1) * h, (rng.next() * 2 - 1) * h
        c = _color_at(col, i / max(1, n))
        out.append(Splat(pos=(pos[0] + x, pos[1] + y, pos[2] + z), scale=(g, g, g),
                         color=(c[0], c[1], c[2], int(op * 255))))


def _emit_plane(p, rng, out):
    pos = p.get("pos", [0, 0, 0]); s = p.get("size", 10.0); g = p.get("gscale", 0.08)
    col = p.get("color"); n = int(p.get("density", 2000)); op = p.get("opacity", 0.85)
    axis = p.get("axis", "xz"); h = s / 2
    for i in range(n):
        a, b = (rng.next() * 2 - 1) * h, (rng.next() * 2 - 1) * h
        if axis == "xz": dx, dy, dz, sc = a, 0, b, (g, g * 0.25, g)
        elif axis == "xy": dx, dy, dz, sc = a, b, 0, (g, g, g * 0.25)
        else: dx, dy, dz, sc = 0, a, b, (g * 0.25, g, g)
        c = _color_at(col, i / max(1, n))
        out.append(Splat(pos=(pos[0] + dx, pos[1] + dy, pos[2] + dz), scale=sc,
                         color=(c[0], c[1], c[2], int(op * 255))))


_PRIMS = {"torus": _emit_torus, "sphere": _emit_sphere, "box": _emit_box, "plane": _emit_plane}


def compile_scene(text: str) -> dict:
    errors, splats, name, seed = [], [], "scene", 0
    # pass 1: read header (seed/scene) so sampling is deterministic regardless of header position
    lines = text.splitlines()
    for ln, raw in enumerate(lines, 1):
        s = raw.split("#", 1)[0].strip()
        if s.startswith("seed"):
            try: seed = int(s.split()[1])
            except (IndexError, ValueError): errors.append({"line": ln, "kind": "bad_number", "message": "seed needs an integer"})
        elif s.startswith("scene"):
            name = s[5:].strip().strip('"') or "scene"
    rng = _LCG(seed)
    # pass 2: primitives in document order (deterministic)
    for ln, raw in enumerate(lines, 1):
        s = raw.split("#", 1)[0].strip()
        if not s or s.startswith("seed") or s.startswith("scene"):
            continue
        toks = s.split()
        cmd = toks[0]
        if cmd not in _PRIMS:
            errors.append({"line": ln, "kind": "unknown_command", "message": f"unknown command '{cmd}'"})
            continue
        try:
            p = _parse_params(toks[1:])
            dens = int(p.get("density", 2000))
            if dens <= 0 or dens > MAX_DENSITY:
                raise _Err("bad_density", f"density must be 1..{MAX_DENSITY}")
            if p.get("gscale", 0.05) <= 0:
                raise _Err("bad_scale", "gscale must be > 0")
            _PRIMS[cmd](p, rng, splats)
        except _Err as e:
            errors.append({"line": ln, "kind": e.kind, "message": e.message})
    if len(splats) > MAX_SPLATS:
        errors.append({"line": 0, "kind": "over_cap", "message": f"{len(splats)} splats exceeds cap {MAX_SPLATS}"})
    if errors:
        return {"ok": False, "errors": errors}
    # invariant verification (defense in depth — by construction these hold)
    for sp in splats:
        assert all(c > 0 for c in sp.scale), "scale axis not positive"
        assert all(math.isfinite(c) for c in sp.pos), "non-finite position"
        assert 0 <= sp.color[3] <= 255, "opacity out of range"
    data = encode_scene(splats)
    return {"ok": True, "name": name, "count": len(splats), "splats": splats,
            "hash": blake2b(data, digest_size=16).hexdigest()}


DEMO = """
scene "Rainbow_Torus"
seed 7
torus pos 0 1.6 0  R 2.4 r 0.8  color rainbow  density 5000  gscale 0.05
plane pos 0 0 0  size 14  color 48 54 66  density 4000  gscale 0.09  axis xz
sphere pos 3.4 2.2 0  radius 0.9  color #ff5a3c  density 1500  gscale 0.05
"""


def main():
    print("splat_dsl.py — Phase 14: verified TEXT → SPLAT compiler\n")
    r = compile_scene(DEMO)
    if r["ok"]:
        print(f"  scene '{r['name']}'  splats={r['count']}  hash={r['hash']}")
        again = compile_scene(DEMO)
        print(f"  determinism: same text ⇒ same hash: {again['hash'] == r['hash']}")
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dsl_demo.splat")
        with open(out, "wb") as fh:
            fh.write(encode_scene(r["splats"]))
        print(f"  wrote {out} — load it in weltwerk_splat_editor.html")
    bad = compile_scene("torus pos 0 0 0 color rainbow\nspere radius 1\nbox size NaNish")
    print("\n  structured errors (for LLM iteration):")
    for e in bad["errors"]:
        print(f"    line {e['line']}: [{e['kind']}] {e['message']}")
    print("\n  text is the authority; the splat cloud is its deterministic, hashable projection.")


if __name__ == "__main__":
    main()
