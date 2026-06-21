# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/_evidence.py — load the already-verified benches as EVIDENCE MODULES.

The kernel is a *consolidation*, not a rewrite: it REUSES the verified Reality Authoring world/edit
and the failure-taxonomy diagnosis rather than reimplementing them. Keeping the old experiments as
imported evidence is what makes the migration differential identical by construction — the history
that earned these objects stays visible and executable, not paraphrased.
"""
from __future__ import annotations

import importlib.util
import os

_here = os.path.dirname(__file__)


def _load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_here, *parts))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_reality = _load("rk_reality", "..", "reality_authoring", "reality.py")
_failure = _load("rk_failure", "..", "failure_taxonomy", "failure.py")

World, Edit = _reality.World, _reality.Edit
diagnose = _failure.diagnose
