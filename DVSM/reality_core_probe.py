# SPDX-License-Identifier: AGPL-3.0-only
"""
reality_core_probe.py — the verification BACKEND for the Rust `dvsm_reality_core` product. It ingests a
telemetry trace the Rust core emits (CSV: frame,x0,x1,stress,sphere_res,stiefel_res,residual_ortho,health)
and turns the core's CLAIMS into MEASURED obligations using the existing DVSM auditors. `claim → measurement`.

Three audits, kernel-relative (about the real emitted trace, not a reference):

  1. INVARIANTS — every frame must satisfy the Layer-1 contract: stress ∈ [0,2], ‖s‖-1 ≈ 0, ‖WᵀW-I‖ ≈ 0,
     ‖Wᵀ R‖ ≈ 0. Graded CLOSED / BOUNDED / VIOLATED with the worst-frame witness.
  2. AIR-GAP — the soft `observation ≠ authority` test: does a DIAGNOSTIC (stress) leak into the FUTURE INPUT
     beyond the legitimate autoregressive driver? Run through `coupling_audit` (CMI + shuffle null + (Z,W)
     mis-spec). A clean core has exogenous inputs ⇒ AIR_GAP_HELD; a controller that steers the next input
     from stress ⇒ OBSERVER_CONTAMINATION. (The Rust type system already forbids Layer-2→geometry writes;
     this measures the *informational* feedback the types cannot see. `borrow-checker-clean ≠ air-gap-sound`.)
  3. REPLAY — two traces from the same seed/schedule must be identical (determinism / DVSM-6, kernel-relative).

`integrity ≠ truth`; `proves-the-procedure ≠ proves-the-phenomenon`; `undetected ≠ absent`.
"""
from __future__ import annotations

import csv
import os
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))
from coupling_audit import CouplingSpec, audit_coupling, CouplingResult     # noqa: E402
from invariant_ledger import ObligationResult, CLOSED, BOUNDED, VIOLATED    # noqa: E402

STRESS_MAX = 2.0
INV_TOL = 1e-6


def read_trace(path: str) -> List[Dict[str, float]]:
    """Parse a reality_core telemetry CSV into a list of row dicts (numeric fields coerced to float)."""
    rows: List[Dict[str, float]] = []
    with open(path, newline="") as f:
        for rec in csv.DictReader(f):
            row: Dict[str, float] = {}
            for k, v in rec.items():
                if k == "health":
                    row[k] = v  # type: ignore
                else:
                    row[k] = float(v)
            rows.append(row)
    return rows


def _with_next(rows: List[Dict[str, float]], fields: Tuple[str, ...]) -> List[Dict[str, float]]:
    out = []
    for a, b in zip(rows, rows[1:]):
        r = dict(a)
        for fld in fields:
            r[fld + "_next"] = b[fld]
        out.append(r)
    return out


# ---- 1. invariant audit (kernel-relative) --------------------------------------------------------
def audit_invariants(rows: List[Dict[str, float]], *, tol: float = INV_TOL) -> List[ObligationResult]:
    def worst(field: str) -> Tuple[float, int]:
        w, wi = 0.0, -1
        for r in rows:
            v = abs(float(r.get(field, 0.0)))
            if v > w:
                w, wi = v, int(r.get("frame", -1))
        return w, wi

    out: List[ObligationResult] = []

    smax = max((float(r["stress"]) for r in rows), default=float("nan"))
    smin = min((float(r["stress"]) for r in rows), default=float("nan"))
    out.append(ObligationResult(
        "RC-stress-bounded", "every frame's stress B(t) lies in [0,2]",
        CLOSED if (0.0 <= smin and smax <= STRESS_MAX) else VIOLATED,
        f"stress in [{smin:.4f}, {smax:.4f}] over {len(rows)} frames",
        "that the model is correct — only that the bounded-stress invariant held on this trace",
        "a frame with stress outside [0,2]"))

    for field, oid, name in (
        ("sphere_res", "RC-sphere", "‖s‖ = 1 (spherical state invariant)"),
        ("stiefel_res", "RC-stiefel", "WᵀW = I (Stiefel frame invariant)"),
        ("residual_ortho", "RC-residual-ortho", "R ⟂ span(W) (orthogonal residual)"),
    ):
        w, wi = worst(field)
        out.append(ObligationResult(
            oid, name, BOUNDED if w < tol else VIOLATED,
            f"max|{field}| = {w:.2e} (frame {wi}); tol={tol:.0e}",
            "the invariant for ALL inputs — only for the frames in this trace; empirical-boundedness ≠ certified",
            f"a frame with |{field}| ≥ {tol:.0e}"))
    return out


# ---- 2. air-gap audit (telemetry → input feedback) -----------------------------------------------
def audit_airgap(rows: List[Dict[str, float]], *, reps: int = 60) -> CouplingResult:
    """Does the diagnostic `stress(t)` leak into the next input `x0(t+1)` beyond the legitimate driver
    `x0(t)` (stress-conditioned on a candidate confounder `x1`)? Clean ⇒ AIR_GAP_HELD."""
    rn = _with_next(rows, ("x0",))
    spec = CouplingSpec(
        "stress_to_next_input",
        "NO diagnostic → input (observation ≠ authority): stress must not steer the next input",
        x=lambda r: r["stress"],
        y=lambda r: r["x0_next"],
        z=lambda r: (r["x0"],),
        w=lambda r: (r["x1"],),
        identifiable=True)
    return audit_coupling(rn, spec, reps=reps, seed=0)


# ---- 3. replay parity ----------------------------------------------------------------------------
def replay_parity(rows_a: List[Dict[str, float]], rows_b: List[Dict[str, float]]) -> ObligationResult:
    a = [(r.get("frame"), r.get("stress"), r.get("stiefel_res")) for r in rows_a]
    b = [(r.get("frame"), r.get("stress"), r.get("stiefel_res")) for r in rows_b]
    return ObligationResult(
        "RC-replay", "two traces from the same seed/schedule are identical",
        CLOSED if a and a == b else VIOLATED,
        f"{len(a)} vs {len(b)} frames; identical = {a == b}",
        "correctness — integrity ≠ truth; determinism ≠ validity",
        "identical seed yielding divergent traces")


def main():
    if len(sys.argv) < 2:
        print("usage: python reality_core_probe.py <trace.csv> [trace_b.csv]")
        print("  emit a trace with the Rust side:  cargo run --example dump_trace -- trace.csv")
        return
    rows = read_trace(sys.argv[1])
    print(f"reality_core_probe — {len(rows)} frames from {os.path.basename(sys.argv[1])}\n")
    print("  invariants:")
    for o in audit_invariants(rows):
        print(f"    [{o.status:9s}] {o.id:20s} {o.witness}")
    ag = audit_airgap(rows)
    print(f"\n  air-gap: {ag.verdict}  (I(stress;x0_next|x0)={ag.result.cmi:.4f})")
    if len(sys.argv) >= 3:
        rp = replay_parity(rows, read_trace(sys.argv[2]))
        print(f"  replay : {rp.status}  ({rp.witness})")
    print("\n  observation ≠ authority; integrity ≠ truth; proves-the-procedure ≠ proves-the-phenomenon.")


if __name__ == "__main__":
    main()
