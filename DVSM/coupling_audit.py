# SPDX-License-Identifier: AGPL-3.0-only
"""
coupling_audit.py — the FORBIDDEN-FEEDBACK-COUPLING firewall for DVSM, built on weltwerk/verify/residual_channel.

The DVSM deployment manifest (ReadMe.rs §5) forbids specific couplings and names "Observer Contamination —
diagnostics begin influencing state evolution" as a failure mode. Today those guarantees are enforced only
by Rust's borrow checker (no *syntactic* write) and by inspection. This module enforces them EMPIRICALLY: a
diagnostic channel X must carry NO information about a future dynamics channel Y beyond the legitimate
drivers Z. The honest discriminator is the confounder-conditioned mutual information:

    I(X ; Y_next | Z_legit)  ≈ null   ⇒  AIR_GAP_HELD          (the borrow-checker promise is also informational)
    I(X ; Y_next | Z_legit)  > null   ⇒  a residual leak; stress it with a candidate confounder W:
        stable under (Z, W)           ⇒  OBSERVER_CONTAMINATION (a real forbidden coupling)
        dissolves under (Z, W)        ⇒  CONFOUNDED_ARTIFACT    (explained by a missing confounder, not a leak)

`borrow-checker-clean ≠ air-gap-sound`: the type system proves no syntactic write; the CMI audit probes for an
informational leak the types cannot see. `residual-CMI ≠ channel` until mis-specification-stable.

IDENTIFIABILITY BOUNDARY (load-bearing, recorded honestly): a coupling is detectable from telemetry only if
the diagnostic X has variance INDEPENDENT of the conditioning set Z. `Ω→V` and `ν→λ` are identifiable (Ω is a
slow independent accumulation; λ has no legitimate driver, so Z is empty). A diagnostic that is itself a
near-deterministic FUNCTION of legit state (e.g. stiffness ≈ 2|z₀|) is UNIDENTIFIABLE by conditioning —
"stiffness→z" is indistinguishable from "z→z". `undetected ≠ absent`; the firewall states where it is blind.

Every verdict routes through the shared honesty contract (AnalysisResult) and registers a graded Claim.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))
from residual_channel import audit, ResidualChannelResult          # noqa: E402
from artifacts import AnalysisResult, Finding, Limitation           # noqa: E402
from claim_ledger import Claim                                      # noqa: E402

from dvsm_reference import StepRecord                               # noqa: E402

K = 3            # bins per channel
REPS = 60        # shuffle-null reps per audit


# ---- quantile binning (each channel → ~K equal-mass symbols) -------------------------------------
def _quantile_edges(values: Sequence[float], k: int) -> List[float]:
    xs = sorted(values)
    if not xs:
        return []
    return [xs[min(len(xs) - 1, int(len(xs) * q / k))] for q in range(1, k)]


def _binner(values: Sequence[float], k: int) -> Callable[[float], int]:
    edges = _quantile_edges(values, k)

    def f(v: float) -> int:
        lo = 0
        for e in edges:
            if v <= e:
                return lo
            lo += 1
        return lo
    return f


# ---- coupling specification ----------------------------------------------------------------------
@dataclass(frozen=True)
class CouplingSpec:
    """One forbidden coupling. X = the diagnostic (source); Y = the future dynamics (target); Z = the
    LEGITIMATE determinants of Y; W = a candidate confounder for the mis-specification stress."""
    name: str
    manifest_rule: str
    x: Callable[[StepRecord], float]
    y: Callable[[StepRecord], float]
    z: Callable[[StepRecord], Tuple[float, ...]]
    w: Callable[[StepRecord], Tuple[float, ...]]
    identifiable: bool = True
    note: str = ""


# the manifest's forbidden couplings (ReadMe.rs §5 + dvsm_one_file "Ω isolated witness, no backfeed")
COUPLINGS: Tuple[CouplingSpec, ...] = (
    CouplingSpec(
        "omega_to_v", "NO Ω → V (long-term drift cannot influence instantaneous velocity)",
        x=lambda r: r.omega0, y=lambda r: r.v0_next,
        z=lambda r: (r.drive, r.v0), w=lambda r: (r.s0,),
        identifiable=True),
    CouplingSpec(
        "novelty_to_lambda", "NO ν → λ (novelty spikes cannot modulate global dissipation)",
        x=lambda r: r.novelty, y=lambda r: r.lambda_eff,
        z=lambda r: (0.0,), w=lambda r: (r.z_energy,),
        identifiable=True),
    CouplingSpec(
        "stiffness_to_z", "NO Stiffness → Dynamics (V17-K outputs are diagnostic-only)",
        x=lambda r: r.stiffness, y=lambda r: r.z0_next,
        z=lambda r: (r.drive, r.z0), w=lambda r: (r.s0,),
        identifiable=False,
        note="stiffness ≈ 2|z₀| is a near-function of the conditioned z₀ ⇒ unidentifiable by conditioning."),
)
_BY_NAME = {c.name: c for c in COUPLINGS}

_VERDICT = {
    "CONSISTENT_WITH_NULL": "AIR_GAP_HELD",
    "RESIDUAL_MISSPEC_STABLE": "OBSERVER_CONTAMINATION",
    "RESIDUAL_MISSPEC_FRAGILE": "CONFOUNDED_ARTIFACT",
    "RESIDUAL_DEPENDENCE": "SUSPECT_UNSTRESSED",
}
# UNIDENTIFIABLE: for a coupling whose diagnostic is a near-deterministic function of the conditioned legit
# state, a positive CMI cannot be told apart from binning-resolution confounding. The firewall DECLINES to
# rule rather than emit a false OBSERVER_CONTAMINATION. This is an epistemic state (not measured), not a
# verdict of clean. `detected-on-unidentifiable ≠ contamination`.


@dataclass(frozen=True)
class CouplingResult:
    name: str
    manifest_rule: str
    verdict: str                 # AIR_GAP_HELD | OBSERVER_CONTAMINATION | CONFOUNDED_ARTIFACT | UNIDENTIFIABLE | SUSPECT_UNSTRESSED
    result: ResidualChannelResult
    identifiable: bool
    note: str

    def as_analysis(self) -> AnalysisResult:
        r = self.result
        findings = (
            Finding("MANIFEST_RULE", "forbidden-coupling", self.manifest_rule),
            Finding("RESIDUAL_CMI", "forbidden-coupling",
                    f"I(X;Y_next|Z)={r.cmi:.4f} vs null {r.null_mean:.4f}±{r.null_std:.4f} (z={r.z_score:.1f})"),
            Finding("VERDICT", "forbidden-coupling", self.verdict),
        )
        lims = [
            Limitation("forbidden-coupling", "a verdict is about THIS trace + the MODELED legit set Z; "
                                             "residual-CMI ≠ channel until mis-specification-stable"),
            Limitation("forbidden-coupling", "AIR_GAP_HELD is absence-of-evidence at this window/conditioning, "
                                             "not proof of no coupling. proves-the-procedure ≠ proves-the-phenomenon"),
        ]
        if not self.identifiable:
            lims.append(Limitation("identifiability", self.note + " undetected ≠ absent"))
        return AnalysisResult(source_trace=(), scope="forbidden-coupling",
                              findings=findings, limitations=tuple(lims))

    def as_claim(self) -> Claim:
        r = self.result
        if self.verdict == "OBSERVER_CONTAMINATION":
            return Claim(f"COUP::{self.name}",
                         f"the forbidden coupling '{self.name}' carries residual information into dynamics.",
                         "MEASURED", f"I(X;Y_next|Z)={r.cmi:.3f} > null, stable under (Z,W).",
                         "a precise mechanism or magnitude in the Rust kernel — only that the reference trace leaks.",
                         "the residual dissolves under a further candidate confounder or finer windowing.")
        if self.verdict == "CONFOUNDED_ARTIFACT":
            return Claim(f"COUP::{self.name}",
                         f"an apparent '{self.name}' leak dissolves under (Z,W): a missing-confounder artifact.",
                         "MEASURED", "I(X;Y_next|Z) elevated but ≈ null under (Z,W).",
                         "that the air-gap holds — only that THIS residual is confounder-explained.",
                         "the residual survives every candidate confounder ⇒ promote to contamination.")
        if self.verdict == "UNIDENTIFIABLE":
            return Claim(f"COUP::{self.name}",
                         f"'{self.name}' is unidentifiable from telemetry: the diagnostic is a function of the "
                         f"conditioned legit state.", "NOT_MEASURED", self.note or "diagnostic ⊂ conditioning set.",
                         "presence OR absence of the coupling — the method cannot separate leak from confounding.",
                         "an instrument that varies the diagnostic independently of the legit state.")
        if self.verdict == "AIR_GAP_HELD":
            return Claim(f"COUP::{self.name}",
                         f"no residual dependence for '{self.name}' beyond the legitimate drivers Z.",
                         "MEASURED", f"I(X;Y_next|Z)={r.cmi:.3f} ≈ shuffle null.",
                         "absence of the coupling in the Rust kernel — only that none is visible here.",
                         "a residual appears under finer windowing, a richer Z, or the real kernel trace.")
        return Claim(f"COUP::{self.name}",
                     f"'{self.name}' shows residual dependence but was not mis-specification-stressed.",
                     "UNDERDETERMINED", "residual detected; no misspec_fn ran.",
                     "whether the residual is a channel or an artifact.",
                     "running the (Z,W) stress resolves it.")


# ---- the audit -----------------------------------------------------------------------------------
def audit_coupling(trace: List[StepRecord], spec: CouplingSpec, *, k: int = K, reps: int = REPS,
                   seed: int = 0) -> CouplingResult:
    """Test whether diagnostic X leaks into future dynamics Y beyond legitimate drivers Z (stress with W)."""
    xs_raw = [spec.x(r) for r in trace]
    ys_raw = [spec.y(r) for r in trace]
    z_dims = list(zip(*[spec.z(r) for r in trace]))          # tuple of per-dim series
    w_dims = list(zip(*[spec.w(r) for r in trace]))

    bx, by = _binner(xs_raw, k), _binner(ys_raw, k)
    z_binners = [_binner(d, k) for d in z_dims]
    w_binners = [_binner(d, k) for d in w_dims]

    xs = [bx(v) for v in xs_raw]
    ys = [by(v) for v in ys_raw]
    zs = [tuple(b(d[i]) for b, d in zip(z_binners, z_dims)) for i in range(len(trace))]
    ws = [tuple(b(d[i]) for b, d in zip(w_binners, w_dims)) for i in range(len(trace))]

    samples = list(zip(xs, ys, zs))

    def refine_w(_s):                                        # re-condition on (Z, W): the decisive stress
        return [(xs[i], ys[i], (zs[i], ws[i])) for i in range(len(trace))]

    r = audit(samples, reps=reps, seed=seed, misspec_fns=(refine_w,))
    verdict = _VERDICT.get(r.decision, "SUSPECT_UNSTRESSED")
    if not spec.identifiable:
        verdict = "UNIDENTIFIABLE"          # decline to rule — the method cannot separate leak from confounding
    return CouplingResult(spec.name, spec.manifest_rule, verdict, r, spec.identifiable, spec.note)


def audit_all(trace: List[StepRecord], *, k: int = K, reps: int = REPS, seed: int = 0) -> List[CouplingResult]:
    """Audit every manifest coupling — side by side, NO fused scalar. The plurality IS the finding."""
    return [audit_coupling(trace, c, k=k, reps=reps, seed=seed) for c in COUPLINGS]


# ---- planted-case validator (proves the PROCEDURE, on identifiable couplings) ---------------------
def planted_validator(*, n: int = 6000, reps: int = REPS) -> dict:
    """For each identifiable coupling: a clean trace must read AIR_GAP_HELD and a trace with that coupling
    planted must read OBSERVER_CONTAMINATION. Sound iff the procedure separates them."""
    from dvsm_reference import gen_clean, gen_contaminated
    out = {}
    for c in COUPLINGS:
        if not c.identifiable:
            continue
        clean = audit_coupling(gen_clean(n, seed=1), c, reps=reps, seed=11)
        dirty = audit_coupling(gen_contaminated(c.name, n, seed=2), c, reps=reps, seed=22)
        out[c.name] = {
            "clean_verdict": clean.verdict, "clean_cmi": clean.result.cmi,
            "dirty_verdict": dirty.verdict, "dirty_cmi": dirty.result.cmi,
            "separates": clean.verdict == "AIR_GAP_HELD" and dirty.verdict == "OBSERVER_CONTAMINATION",
        }
    return out


def main():
    print("coupling_audit.py — forbidden-feedback-coupling firewall (borrow-checker-clean ≠ air-gap-sound)\n")
    v = planted_validator()
    for name, r in v.items():
        print(f"  {name:20s} clean={r['clean_verdict']:22s}(CMI={r['clean_cmi']:.3f})  "
              f"planted={r['dirty_verdict']:22s}(CMI={r['dirty_cmi']:.3f})  separates={r['separates']}")
    print("\n  a CHANNEL/OBSERVER_CONTAMINATION verdict = a diagnostic leaks into dynamics; AIR_GAP_HELD is")
    print("  absence-of-evidence, not proof. residual-CMI ≠ channel; proves-the-procedure ≠ proves-the-phenomenon.")


if __name__ == "__main__":
    main()
