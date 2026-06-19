# Render Verification Record — template

Every new renderer feature is an **experiment, not an architectural invasion.** Before a feature
(Nanite-like triangle allocation, AI upscaling, ray tracing, foveated rendering, a new culler, a denoiser)
is admitted, it must produce a record that proves it is observer-only and that its numbers were *measured*,
not asserted.

Two ways to produce one:

1. **Emitted (preferred).** `ursprung.render_record.evaluate_feature(...)` runs the candidate alongside the
   CORE trajectory and returns a `RenderVerificationRecord` with real content hashes, the
   CORE-trajectory-changed verdict, the measured frame budget, and any ghosts. Call `.to_markdown()`.
   The record's `admissible()` is the cardinal invariant as a boolean: a non-CORE feature is admissible only
   if it did **not** change the committed trajectory.
2. **Hand-filled** (for features not yet wired to the harness) — copy the block below.

```
## Render Verification Record — <feature> — <date>

Feature:                <name>
Layer:                  CORE / VIEW / ALLOCATOR / OBSERVER
Effect:                 <what this feature changes>
Non-effect (invariant): <what MUST remain unchanged — e.g. the committed CORE trajectory>
Conventions used:       <convention-set digest from ursprung.conventions.LEDGER.digest()>

Input snapshot hash:    <l1_hash of the representative committed state>
Renderer config hash:   <canon_hash of the renderer config / knobs>
Output artifact hash:   <canon_hash of the produced frame / allocation>

CORE trajectory changed:   YES / NO        # NO for any non-CORE feature, or it is REJECTED
VIEW divergence:           expected / unexpected

Measured:
  hardware:      <cpu/gpu/build>
  resolution:    <e.g. 1920x1080>
  scene:         <named scene + entity count>
  frame budget:  <ms>   # OBSERVABLE, never a gate (target band ≈ 4.13 ms ≈ 242 fps)

Known ghosts:            # attention signals; classify each before patching
  <category>/<origin>: <detail>           # e.g. spatial/boundary_choice: edge seam — footprint of 'pixel_coverage'

Verdict: ADMISSIBLE / REJECTED
Scope: integrity ≠ truth — measured on the tested world only; not a universal-superiority claim.
       A benchmark measures the benchmark's world; it does not prove universal superiority.
```

## The four required declarations (per feature)

```
TYPE:        CORE / VIEW / ALLOCATOR / OBSERVER
EFFECT:      what changes
NON-EFFECT:  what must remain unchanged
EVIDENCE:    how it was verified (the record above + the command that produced it)
```

## Why this turns capabilities into experiments

The biggest risk now is not lack of capability — it is **too many interesting capabilities trying to become
the center of gravity.** A record forces each one to declare its layer, prove it did not seize authority, and
measure rather than assert. Success is not one dominant feature; it is a **pool of composable results** that
each stay on their side of the membrane. The record is the counterweight (see `docs/LLM_ON_TRACK.md`).
