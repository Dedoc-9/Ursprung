# SPDX-License-Identifier: AGPL-3.0-only
"""
telemetry_audit.py — a deliverable telemetry anomaly engine: distinguish genuine component degradation from
sensor noise / mis-specification, built on the verified `residual_channel` firewall.

Two sensor streams X, Y and a modeled operating/control state Z (the confounder). The decisive quantities:

    I(X;Y)        — correlation; large simply because the control drives both. NOT a fault.
    I(X;Y | Z)    — residual dependence beyond the modeled control. A fault candidate.
    I(X;Y | Z, W) — residual after ALSO conditioning on a candidate confounder W (e.g. a sensor cross-talk
                    model). This is the decisive discriminator.

DECISION (graded, with the firewall's discipline):
    HEALTHY        — I(X;Y|Z) ≈ shuffle-null: all coupling is explained by the modeled control.
    SENSOR_MISSPEC — I(X;Y|Z) elevated BUT I(X;Y|Z,W) ≈ null: a MISSING confounder W (cross-talk / shared
                     noise source), not a physical fault. Conditioning on the right variable dissolves it.
    FAULT          — I(X;Y|Z) AND I(X;Y|Z,W) both elevated: a genuine unmodeled inter-coordinate channel that
                     SURVIVES the best available conditioning — the signature of real structural degradation.

Why conditioning on MORE (refine with W), not only coarsening: coarsening cannot separate a real channel from a
missing confounder (both can stay positive). Adding the candidate confounder does: a fault survives it, leakage
vanishes. `residual-CMI ≠ fault` until it survives conditioning on the complete modeled state.

BOUNDARIES (stated, load-bearing): the verdict is only as good as the modeled (Z, W); an unmodeled confounder
not in {Z, W} can still masquerade as a fault (you can never condition on the *complete* physical state). The
streams are discretized (Arbitrary-Boundary Law). This proves a property of the DECISION PROCEDURE on the
modeled streams, not a physical diagnosis. `proves-the-procedure ≠ proves-the-fault`; `integrity ≠ truth`.
"""
from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
from residual_channel import (conditional_mutual_information, mutual_information, shuffle_null)  # noqa: E402
from artifacts import AnalysisResult, Finding, Limitation                                       # noqa: E402

K = 3                  # discretization levels per stream
N = 40000              # samples (tight MI estimate + null)
MARGIN = 0.03          # absolute CMI margin above the shuffle null to count as "elevated"


def _noisy(v, rng, p=0.3):
    return v if rng.random() >= p else rng.randrange(K)


def _mix(a, b):
    return (a + b) % K


# ---- synthetic sensor streams (each sample is (x, y, z, w)) ---------------------------------------
def gen_healthy(n: int = N, seed: int = 1):
    """The control Z drives both sensors; given Z they are independent (no fault, no cross-talk)."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        z, w = rng.randrange(K), rng.randrange(K)
        out.append((_noisy(z, rng), _noisy(z, rng), z, w))
    return out


def gen_fault(n: int = N, seed: int = 2):
    """A real fault: a direct X→Y coupling beyond the control (and independent of the candidate confounder W)."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        z, w = rng.randrange(K), rng.randrange(K)
        x = _noisy(z, rng)
        y = _noisy(_mix(z, x), rng)            # Y depends on X ⇒ residual survives conditioning on (Z, W)
        out.append((x, y, z, w))
    return out


def gen_sensor_misspec(n: int = N, seed: int = 3):
    """A MISSING confounder: a hidden cross-talk source W drives both sensors; the control Z does not capture it.
    Residual appears under Z alone but DISSOLVES once W is conditioned on — it is not a fault."""
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        z, w = rng.randrange(K), rng.randrange(K)
        x = _noisy(_mix(z, w), rng)
        y = _noisy(_mix(z, w), rng)            # X,Y share the hidden W ⇒ residual under Z, gone under (Z,W)
        out.append((x, y, z, w))
    return out


@dataclass(frozen=True)
class TelemetryResult:
    decision: str            # HEALTHY | SENSOR_MISSPEC | FAULT
    mi: float
    cmi_Z: float
    cmi_ZW: float
    null_Z: float
    null_ZW: float

    def as_analysis(self) -> AnalysisResult:
        findings = (
            Finding("CORRELATION", "telemetry", f"I(X;Y)={self.mi:.4f} (control-confounded; not a fault)"),
            Finding("RESIDUAL_GIVEN_CONTROL", "telemetry", f"I(X;Y|Z)={self.cmi_Z:.4f} vs null {self.null_Z:.4f}"),
            Finding("RESIDUAL_GIVEN_CONTROL_AND_CONFOUNDER", "telemetry",
                    f"I(X;Y|Z,W)={self.cmi_ZW:.4f} vs null {self.null_ZW:.4f}"),
            Finding("DECISION", "telemetry", self.decision),
        )
        limitations = (
            Limitation("telemetry", "verdict is relative to the MODELED (Z,W); an unmodeled confounder can "
                                    "masquerade as a fault. residual-CMI ≠ fault until it survives the complete "
                                    "modeled state"),
            Limitation("method", "streams are discretized (Arbitrary-Boundary Law); proves a property of the "
                                 "decision procedure, not a physical diagnosis. proves-the-procedure ≠ proves-the-fault"),
        )
        return AnalysisResult(source_trace=(), scope="telemetry", findings=findings, limitations=limitations)


def diagnose(samples, margin: float = MARGIN) -> TelemetryResult:
    """Classify a window of (x,y,z,w) telemetry samples as HEALTHY / SENSOR_MISSPEC / FAULT."""
    xy = [(x, y) for x, y, _z, _w in samples]
    xyz = [(x, y, z) for x, y, z, _w in samples]
    xyzw = [(x, y, (z, w)) for x, y, z, w in samples]
    mi = mutual_information(xy)
    cmi_Z, null_Z = conditional_mutual_information(xyz), shuffle_null(xyz)
    cmi_ZW, null_ZW = conditional_mutual_information(xyzw), shuffle_null(xyzw)
    elevated_Z = cmi_Z > null_Z + margin
    elevated_ZW = cmi_ZW > null_ZW + margin
    if not elevated_Z:
        decision = "HEALTHY"
    elif not elevated_ZW:
        decision = "SENSOR_MISSPEC"            # a missing confounder, not a fault
    else:
        decision = "FAULT"                     # residual survives the best conditioning
    return TelemetryResult(decision, mi, cmi_Z, cmi_ZW, null_Z, null_ZW)


def main():
    print("telemetry_audit.py — fault vs sensor mis-specification, via residual_channel\n")
    for label, gen in [("healthy", gen_healthy), ("sensor mis-spec (missing W)", gen_sensor_misspec),
                       ("fault (real channel)", gen_fault)]:
        r = diagnose(gen())
        print(f"  {label:28s} → {r.decision:14s}  I(X;Y)={r.mi:.3f}  I(X;Y|Z)={r.cmi_Z:.3f}  "
              f"I(X;Y|Z,W)={r.cmi_ZW:.3f}  (null≈{r.null_Z:.3f})")
    print("\n  a missing confounder dissolves under (Z,W) → SENSOR_MISSPEC; a real fault survives → FAULT.")
    print("  conditioning on MORE separates them (coarsening cannot). residual-CMI ≠ fault; integrity ≠ truth.")


if __name__ == "__main__":
    main()
