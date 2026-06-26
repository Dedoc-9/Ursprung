# SPDX-License-Identifier: AGPL-3.0-only
"""
differential.py — Phase A.2, Step 6: the differential equivalence harness.

For every model where both engines can answer, they must produce equivalent verification results. This is
what converts "we believe the engines agree" into measured evidence — and it is the safety net for the
symbolic encoding (it catches any drift between the explicit reference and the SMT-backed engine).

Equivalence here (honest, since SMT models are not canonical):
  • same public STATUS (CLOSED / BOUNDED / VIOLATED);
  • for VIOLATED: same SHORTEST witness LENGTH, and the symbolic witness REPLAYS to its trace's terminal
    state through the proven relation (`symbolic proposes, semantics confirm`). Byte-identical event
    sequences are NOT required — two shortest counterexamples are equally valid;
  • for non-VIOLATED: same explored-state count (both fully enumerate within the bound).

`engine ≠ semantics`; `symbolic ≠ magic`; `unsat-at-k ≠ unreachable`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from engine import build_model, VerificationOptions, ExplicitStateBFSEngine   # noqa: E402
from kernel_check import replay_path, DEMO_WORLD                              # noqa: E402
import solver_adapter                                                        # noqa: E402


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

NEVER_DESTROYED = {"nothing_ever_destroyed":
                   (lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime))}

# (label, world_text, max_depth, invariants)
SUITE = [
    ("SMALL closed",   SMALL, 8, None),
    ("SMALL bounded",  SMALL, 1, None),
    ("SMALL violated", SMALL, 3, NEVER_DESTROYED),
    ("DEMO bounded-1", DEMO_WORLD, 1, None),
    ("DEMO bounded-4", DEMO_WORLD, 4, None),
]


def differential(world_text, *, max_depth, invariants=None, include_capture=False) -> dict:
    """Run both engines on one model; return an agreement record."""
    from symbolic_engine import SymbolicEngine     # deferred so this module imports without z3
    model = build_model(world_text, include_capture=include_capture, invariants=invariants)
    opts = VerificationOptions(depth_bound=max_depth)
    ex = ExplicitStateBFSEngine().verify(model, opts)
    sy = SymbolicEngine().verify(model, opts)
    rec = {"status_explicit": ex.status, "status_symbolic": sy.status,
           "agree_status": ex.status == sy.status}
    if ex.status == "VIOLATED":
        ex_len = len(ex.witness) if ex.witness else 0
        sy_len = len(sy.witness) if sy.witness else 0
        rec["len_explicit"], rec["len_symbolic"] = ex_len, sy_len
        rec["agree_length"] = ex_len == sy_len
        rec["symbolic_replays"] = (sy.trace is not None
                                   and replay_path(world_text, list(sy.witness)) == sy.trace.terminal_state)
    else:
        rec["explored_explicit"], rec["explored_symbolic"] = ex.explored_states, sy.explored_states
        rec["agree_explored"] = ex.explored_states == sy.explored_states
    return rec


def agree(rec: dict) -> bool:
    if not rec["agree_status"]:
        return False
    if rec["status_explicit"] == "VIOLATED":
        return bool(rec.get("agree_length") and rec.get("symbolic_replays"))
    return bool(rec.get("agree_explored"))


def run_suite():
    return [(label, differential(w, max_depth=d, invariants=inv)) for (label, w, d, inv) in SUITE]


def main():
    print("differential.py — Phase A.2 Step 6: explicit vs symbolic equivalence\n")
    if not solver_adapter.HAVE_SOLVER:
        print("  SKIPPED: optional solver not installed. `pip install z3-solver` to run the symbolic engine.")
        return
    for label, rec in run_suite():
        print(f"  [{'OK ' if agree(rec) else 'DIFF'}] {label:16s} {rec}")


if __name__ == "__main__":
    main()
