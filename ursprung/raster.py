# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/raster.py — the VIEW vertical slice: a deterministic reference rasterizer.

The first contact between the five laws and an actual rasterizer. The pipeline, each stage a declared
deterministic CONVENTION (Arbitrary-Boundary Law), each with a known ghost:

    projection  → coverage → sampling → rasterization → image
    (camera)      (top-left)  (k spp)    (nearest depth)  (framebuffer)

This is a CPU reference (the slow, obviously-correct oracle — like AetherPulse is for the kernel), not a GPU
engine. It consumes a VIEW VisualFrame (pure observables: screen-space sprites) and produces a content-
addressable framebuffer. It NEVER touches CORE — it only reads the frame — so the cardinal invariant holds by
construction (proven empirically in raster_bench / tests).

CLASSIFICATION: VIEW (mutates_core=False). Float projection is fine here (presentation, not committed state);
the framebuffer is quantized to integer pixel indices so it can be content-hashed deterministically.

HONEST BOUND: a reference rasterizer over screen-space boxes at 1 sample/pixel — it proves the pipeline is
deterministic and observer-only and that each stage is a declared convention; it is not a production raster
path, and the aliasing-error model (`aliasing_error`) is a declared proxy, not measured silicon error.
`integrity ≠ truth`.
"""
from __future__ import annotations

import hashlib

# Each stage names the convention it obeys (see conventions.py / Arbitrary-Boundary Law).
CONVENTIONS = {
    "projection": "perspective camera (view_layer.Camera); world→screen is a lossy VIEW transform",
    "coverage": "pixel-center sample + top-left fill rule (half-open [left,right) × [top,bottom))",
    "sampling": "k samples/pixel (k=1 reference); the fidelity an ALLOCATOR distributes is k per region",
    "rasterization": "nearest-depth wins (a deterministic z-resolution convention, not physical occlusion)",
}

# The ghost each stage can emit (footprint of its boundary choice, not an error).
STAGE_GHOSTS = {
    "coverage": "spatial/boundary_choice — edge pixels assigned by the top-left rule",
    "sampling": "spatial/approximation — aliasing where k is low (under-sampled edges)",
    "rasterization": "spatial/boundary_choice — z-ties resolved by the nearest-wins convention",
}


class Framebuffer:
    """A quantized image: width×height of integer indices (-1 = background). Content-addressable."""
    __slots__ = ("width", "height", "pixels", "index_of")

    def __init__(self, width, height, pixels, index_of):
        self.width = width
        self.height = height
        self.pixels = pixels            # list[int] length width*height; -1 background else sprite index
        self.index_of = index_of        # {sprite_id: index} (sorted, deterministic)

    def content_hash(self):
        h = hashlib.sha256()
        h.update(("%dx%d|" % (self.width, self.height)).encode())
        h.update(bytes((p + 1) & 0xFF for p in self.pixels))   # +1 so -1→0; deterministic byte image
        return h.hexdigest()

    def coverage_counts(self):
        """Pixels covered per sprite id — an observable, useful for the bench."""
        out = {sid: 0 for sid in self.index_of}
        rev = {idx: sid for sid, idx in self.index_of.items()}
        for p in self.pixels:
            if p >= 0:
                out[rev[p]] += 1
        return out


def _screen_box(sprite):
    """Screen-space AABB of a projected sprite (center x,y; half-extent = size). Floats (VIEW-only)."""
    x, y, s = sprite["x"], sprite["y"], sprite["size"]
    return (x - s, y - s, x + s, y + s)   # left, top, right, bottom


def rasterize(frame, width=64, height=40):
    """projection→coverage→sampling→raster, at 1 spp. Deterministic: same frame → same framebuffer hash.
    Reads `frame` only; never a world. Nearest-depth sprite wins each pixel; top-left half-open coverage."""
    ids = sorted(s["id"] for s in frame.sprites)
    index_of = {sid: i for i, sid in enumerate(ids)}
    pixels = [-1] * (width * height)
    depth = [float("inf")] * (width * height)
    for s in frame.sprites:
        if not s.get("visible") or s["x"] is None:
            continue
        left, top, right, bottom = _screen_box(s)
        d = s["depth"]
        # iterate the pixel range the box could touch (clamped to the framebuffer)
        x0 = max(0, int(left + 0.5)); x1 = min(width - 1, int(right - 0.5))
        y0 = max(0, int(top + 0.5)); y1 = min(height - 1, int(bottom - 0.5))
        idx = index_of[s["id"]]
        for py in range(y0, y1 + 1):
            cy = py + 0.5
            if not (top <= cy < bottom):     # top-left half-open rule (vertical)
                continue
            row = py * width
            for px in range(x0, x1 + 1):
                cx = px + 0.5
                if not (left <= cx < right):  # top-left half-open rule (horizontal)
                    continue
                p = row + px
                if d < depth[p]:              # nearest-depth wins (the z convention)
                    depth[p] = d
                    pixels[p] = idx
    return Framebuffer(width, height, pixels, index_of)


def aliasing_error(size, samples):
    """Declared edge-aliasing proxy: error ≈ edge_perimeter / samples (more samples ⇒ less aliasing). A box
    of half-extent `size` has perimeter ≈ 8·size in screen units. Integer, deterministic. A MODEL, not
    measured silicon error (honest bound)."""
    perimeter = max(1, int(8 * size))
    return perimeter * 1000 // max(1, samples)    # ‰-scaled so integer math keeps resolution
