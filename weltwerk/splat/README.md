<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# weltwerk/splat — Gaussian Splat Lens + Editor

A from-scratch, in-browser **3D Gaussian-splat renderer and editor**, built as another **replaceable
Weltwerk projection**. In the project's terms a splat scene is a `GeometryAdapter` / lens — a
*representation*, never authority. You can edit the representation all you like; it does not define truth.
This is the same separator the whole project rests on: `observation ≠ authority`. The lenses so far are
text → wireframe → voxel → meshes → FPS city → **gaussian splats**.

## Files

| File | Role | Grade |
|---|---|---|
| `splat_format.py` | the `.splat` 32-byte **data contract** (encode/decode/scene/synthetic) | MEASURED |
| `test_splat_format.py` | 8 tests: layout, exactness, quantization, round-trip, rejection, determinism | MEASURED (8/8) |
| `weltwerk_splat_editor.html` | the WebGL renderer + editor (JS mirrors the contract) | IMPLEMENTED |
| `synthetic.splat` | a loadable scene emitted by `splat_format.py` (optional) | — |

## Run

```powershell
cd "weltwerk\splat"; python test_splat_format.py; python splat_format.py
```

`test_splat_format.py` → **8/8**; `splat_format.py` writes `synthetic.splat`. Then open
`weltwerk_splat_editor.html`. It loads a synthetic scene immediately (no assets needed). Drag a real
`.splat` (or basic `.ply`) onto the window to view/edit it; **Export .splat** to save your edits.

Controls: drag = orbit · wheel = zoom · shift+drag = pan · **Erase brush** (click/drag to delete splats) ·
**Crop box** (slider-positioned box → cut inside / keep inside / recolor / set opacity) · Synthetic / Load / Export.

## MEASURED (verified by `test_splat_format.py`, 8/8)

- A splat record is **exactly 32 bytes** with the documented layout (position@0, scale@12, colour@24, rot@28).
- Position and colour survive encode→decode **exactly**; rotation within the 1/128 quantization bound.
- Whole scenes **round-trip**; malformed (non-multiple-of-32) buffers are **rejected**; the synthetic scene
  is **deterministic**. The editor's JS mirrors this byte-for-byte, so a file written by one is read by the other.

## IMPLEMENTED (the editor — exercised on open, not auto-tested)

- **From-scratch splat renderer:** instanced quads, each shaded as a 2D Gaussian (`exp(-r²)`), depth-sorted
  back-to-front with alpha blending and `depthWrite=false` — the splat look, written by hand in a
  `RawShaderMaterial`, no splat library.
- **Per-splat** colour, opacity, and size; a global size slider.
- **Editing:** erase brush (ray-distance delete), 3D crop box (cut-inside / keep-inside), recolor and set
  opacity inside the box.
- **Load** `.splat` (full) and `.ply` (binary, position + RGB or `f_dc` spherical-harmonic DC term,
  best-effort, auto-subsampled for the browser); **Export** `.splat` (mirrors the contract).
- Orbit/zoom/pan camera, FPS + splat-count HUD, drag-and-drop.

## VISION (not built; would extend, not replace)

- **Full 3D-covariance EWA splatting** (anisotropic projected ellipses from a real covariance, proper
  spherical-harmonic view-dependent colour) — here approximated with screen-facing isotropic-ish gaussian
  billboards. This is the honest gap between "looks like splats" and "is a reference splatter."
- A **capture/training pipeline** (SfM/COLMAP + optimisation) to *create* splats — out of scope; this tool
  views and edits existing scenes.
- GPU radix-sort for millions of splats (current sort is CPU, throttled, comfortable to ~10–120k).
- The **causal-lens** version (Phase 13b idea): map splat clusters to Weltwerk entities so destroying a node
  visibly degrades its splats — the strongest "the renderer is just a lens" demonstration. Deferred.

## NOT CLAIMED

- **Not** reference-quality 3D Gaussian splatting, not photoreal novel-view synthesis, not a trainer, not
  real-time millions of splats. A faithful, hand-written *approximation* of the splat representation and a
  usable editor over the **verified** `.splat` contract.
- The lens holds **no authority**. Editing splats changes a representation; in a full Weltwerk pipeline the
  causal `.wrk` graph remains the source of truth and the splats are one of its projections.
