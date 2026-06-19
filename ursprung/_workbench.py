# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/_workbench.py — Sibling-Law bridge to the sealed Reality_Engine workbench (READ-ONLY).

Ursprung is a STANDALONE renderer project. It consumes the Chronicle/Dentatus workbench the same way
AetherPulse/VeriVerse do: it puts the relevant workbench directories on sys.path and imports them
read-only. It NEVER edits or vendors a workbench file. The workbench is the *verification substrate*,
not the renderer.

PIPELINE-ORDERING HAZARD (recorded, not patched-over):
    AetherPulse modules use bare top-level imports (`from _cores import ...`, `import kernel`), and the
    `aether/` sibling exposes generic names like `ghost`, `field`, `regime`. Any Ursprung module that
    entered sys.modules under one of those names would SHADOW the workbench and silently change behavior.
    Mitigation: Ursprung is a package; every Ursprung module is `ursprung.*` and avoids the reserved
    top-level names below. This file is the single point where workbench paths are injected.

Reserved top-level names owned by the workbench (do NOT create `ursprung/<name>.py` that is imported as a
bare top-level module with any of these): kernel, snapshot, _cores, canon, batch, shard, fixedpoint,
ghost, field, regime, coherence, evolve, predictive, stiefel, spd.

CLASSIFICATION: this module is infrastructure for the CORE boundary — it grants read access to the
authoritative kernel. It holds no state and makes no allocation or visual decision.

HONEST BOUND: a read-only import is a *convenience boundary*, not an enforced one — Python cannot stop a
caller from reaching into K's dicts. The enforced invariant lives in `ursprung.verify`
(hash-identity with/without the renderer); this file only locates the substrate.
"""
import os
import sys

# Resolve the workbench root. Override with URSPRUNG_WORKBENCH if the engine lives elsewhere.
_DEFAULT_WB = os.environ.get(
    "URSPRUNG_WORKBENCH",
    os.path.join(os.path.expanduser("~"), "Desktop", "Reality_Engine"),
)


def _resolve_workbench():
    """Find Reality_Engine. Tries the env/default, then a few sibling-relative guesses. Fail LOUDLY."""
    candidates = [
        _DEFAULT_WB,
        # bash/VM mount used during development:
        "/sessions/determined-admiring-ramanujan/mnt/Reality_Engine",
    ]
    for c in candidates:
        if c and os.path.isdir(os.path.join(c, "AetherPulse")):
            return c
    raise RuntimeError(
        "Reality_Engine workbench not found. Set URSPRUNG_WORKBENCH to its path. Tried: %r" % candidates
    )


WORKBENCH_ROOT = _resolve_workbench()
_AETHERPULSE = os.path.join(WORKBENCH_ROOT, "AetherPulse")

# AetherPulse self-protects its own bare imports by inserting its dir at sys.path[0] inside kernel.py;
# we add it here so `import kernel`/`import snapshot` resolve to the workbench copy.
if _AETHERPULSE not in sys.path:
    sys.path.insert(0, _AETHERPULSE)

import kernel as _kernel        # AetherPulse/kernel.py — the deterministic 3-D fixed-point reference kernel
import snapshot as _snapshot    # AetherPulse/snapshot.py — the L1/L2/L3 read-only render seam
# `aether/` is now on sys.path (AetherPulse/_cores added it); fixedpoint defines the integer SCALE.
import fixedpoint as _fp        # aether/fixedpoint.py — fixed-point integer arithmetic

# Re-export under explicit names so Ursprung code never touches bare `kernel`/`snapshot` globals.
K = _kernel
SNAP = _snapshot
# Display scale: a fixed-point coordinate is (value * SCALE). VIEW divides by this to get display units.
# Reading it (never mutating committed state) is a CORE→metrics flow, which is ALLOWED.
SCALE = _fp.SCALE

__all__ = ["K", "SNAP", "SCALE", "WORKBENCH_ROOT"]