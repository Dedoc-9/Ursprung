# SPDX-License-Identifier: AGPL-3.0-only
"""
conformance.py — the engine-conformance gate.

Every `VerificationEngine` must satisfy the SAME public contract, regardless of how it reasons. This module
is the reusable gate: `check_conformance(engine)` runs an engine over a small model suite and checks the
UNIVERSAL contract every backend must meet. New engines (abstract interpreter, a SAT backend, a repair
engine) should pass this before becoming supported — alongside `differential.py` (equivalence with the
explicit reference).

What is contractual (checked here) vs optional (NOT checked here):
  • contractual: returns a `VerificationResult`; status ∈ {CLOSED, BOUNDED, VIOLATED} (no new status);
    VIOLATED ⇒ a `Trace` whose witness REPLAYS to its terminal (else `trace is None`); deterministic public
    result; a non-empty engine label; frontier consistent with status.
  • optional (engine-specific, deliberately NOT required): the `ReachabilityCertificate` (the explicit
    engine emits one on CLOSED; the symbolic engine does not yet) and byte-identical witnesses (SMT models
    are not canonical — only the witness *length* is contractually stable). `contract ≠ optional-artifact`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from engine import build_model, VerificationOptions          # noqa: E402
from interfaces import VerificationResult                    # noqa: E402
from artifacts import Trace                                   # noqa: E402
from kernel_check import replay_path, DEMO_WORLD             # noqa: E402
import solver_adapter                                         # noqa: E402

ALLOWED = {"CLOSED", "BOUNDED", "VIOLATED"}

SMALL = """
world "T"
entity faction_a:
  position 0 0 0
  controls hub
entity hub:
  position 1 0 0
  health 10
  powers leaf
entity leaf:
  position 2 0 0
  health 10
"""

NEVER = {"nothing_ever_destroyed": (lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime))}

# (label, world_text, depth_bound, invariants) — spans CLOSED / BOUNDED / VIOLATED
MODELS = [
    ("closed",       SMALL, 8, None),
    ("bounded",      SMALL, 1, None),
    ("violated",     SMALL, 3, NEVER),
    ("demo-bounded", DEMO_WORLD, 1, None),
]


def engines():
    """The engines to gate: the explicit reference always; the symbolic engine iff its solver is present."""
    from engine import ExplicitStateBFSEngine
    engs = [ExplicitStateBFSEngine()]
    if solver_adapter.HAVE_SOLVER:
        from symbolic_engine import SymbolicEngine
        engs.append(SymbolicEngine())
    return engs


def _run(engine):
    out = {}
    for label, w, d, inv in MODELS:
        vr = engine.verify(build_model(w, invariants=inv), VerificationOptions(depth_bound=d))
        out[label] = (w, d, inv, vr)
    return out


def check_conformance(engine) -> list:
    """Return a list of (check_name, ok, detail) for `engine` against the universal contract."""
    R = []
    runs = _run(engine)
    vrs = [vr for (_w, _d, _inv, vr) in runs.values()]

    R.append(("returns_verification_result",
              all(isinstance(vr, VerificationResult) for vr in vrs),
              "every model → VerificationResult"))

    bad = sorted({vr.status for vr in vrs} - ALLOWED)
    R.append(("status_in_allowed", not bad, f"statuses ⊆ {sorted(ALLOWED)}; offenders {bad or 'none'}"))

    ok = True
    for _label, (w, _d, _inv, vr) in runs.items():
        if vr.status == "VIOLATED":
            good = (isinstance(vr.trace, Trace) and vr.witness is not None
                    and replay_path(w, list(vr.witness)) == vr.trace.terminal_state)
        else:
            good = vr.trace is None
        ok = ok and good
    R.append(("violation_trace_and_replay", ok, "VIOLATED ⇒ Trace whose witness replays; else trace None"))

    ok = True
    for _label, (w, d, inv, vr) in runs.items():
        # re-verify; compare only the contractually-stable projection (witness LENGTH, not exact events)
        vr2 = engine.verify(build_model(w, invariants=inv), VerificationOptions(depth_bound=d))
        a = (vr.status, vr.explored_states, vr.frontier_exhausted, tuple(vr.violations), len(vr.witness or ()))
        b = (vr2.status, vr2.explored_states, vr2.frontier_exhausted, tuple(vr2.violations), len(vr2.witness or ()))
        ok = ok and a == b
    R.append(("deterministic", ok, "stable status / explored / violations / witness-length"))

    R.append(("engine_labelled",
              all(isinstance(vr.engine, str) and vr.engine for vr in vrs),
              f"engine={vrs[0].engine!r}"))

    ok = True
    for _label, (_w, _d, _inv, vr) in runs.items():
        if vr.status == "CLOSED" and not vr.frontier_exhausted:
            ok = False
        if vr.status == "BOUNDED" and vr.frontier_exhausted:
            ok = False
    R.append(("frontier_consistency", ok, "CLOSED ⇒ frontier exhausted; BOUNDED ⇒ not"))

    return R


def main():
    print("conformance.py — engine-conformance gate (universal contract)\n")
    for engine in engines():
        results = check_conformance(engine)
        passed = sum(1 for _n, ok, _d in results if ok)
        print(f"  engine: {engine.verify(build_model(SMALL), VerificationOptions(depth_bound=1)).engine}")
        for name, ok, detail in results:
            print(f"    [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
        print(f"    → {passed}/{len(results)}\n")


if __name__ == "__main__":
    main()
