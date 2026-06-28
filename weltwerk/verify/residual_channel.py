# SPDX-License-Identifier: AGPL-3.0-only
"""
residual_channel.py — a domain-agnostic causal diagnostic: is there dependence between X and Y that the
conditioning set Z does NOT explain? (Extracted from the snowflake study; nothing here mentions snowflakes.)

The question "is observed correlation a real signal or just an unobserved-confounder leak?" appears everywhere
— biological patterning, market co-movement, neural assemblies, A/B telemetry, swap branches. The honest
discriminator is the CONDITIONAL mutual information given the modeled confounder/field Z:

    I(X;Y)        > 0   ← may be pure confounding by Z. NOT evidence of a channel.
    I(X;Y | Z)    > 0   ← residual dependence beyond Z — a candidate channel.

The estimator's finite-sample bias is positive, so a raw `I(X;Y|Z) > 0` proves nothing. We therefore compare
it to a WITHIN-Z SHUFFLE NULL (permute Y inside each Z stratum, destroying any conditional X–Y dependence while
preserving the bias). A signal that exceeds the null distribution is *residual dependence*; whether it is a
genuine channel or merely Z mis-specification (an incomplete confounder) is decided by MIS-SPECIFICATION
STRESS: re-condition on perturbed/coarsened Z — a real channel is stable, leakage is not.

What this module PROVES is a property of the DECISION PROCEDURE, validated on PLANTED cases:
`planted_case_validator` runs the audit on a known-null generator and a known-channel generator and checks the
procedure separates them. It does NOT prove anything about any real system. `proves-the-procedure ≠
proves-the-phenomenon`; `residual-CMI ≠ channel` until mis-specification-stable; `confounded-MI ≠ channel`.

Outputs route through the shared honesty contract (`AnalysisResult`): scope + ≥1 limitation, always.
"""
from __future__ import annotations

import math
import os
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artifacts import AnalysisResult, Finding, Limitation        # noqa: E402  (honesty contract, reused)


# ---- discrete estimators (exact from counts; bits) ----------------------------------------------
def entropy(xs) -> float:
    n = len(xs)
    c = Counter(xs)
    return -sum((v / n) * math.log2(v / n) for v in c.values())


def cond_entropy(pairs) -> float:
    """H(Y | X) from a list of (x, y)."""
    n = len(pairs)
    cx = Counter(x for x, _y in pairs)
    cxy = Counter(pairs)
    return sum((c / n) * math.log2(cx[x] / c) for (x, _y), c in cxy.items())


def mutual_information(samples_xy) -> float:
    n = len(samples_xy)
    cx, cy, cxy = Counter(), Counter(), Counter()
    for x, y in samples_xy:
        cx[x] += 1; cy[y] += 1; cxy[(x, y)] += 1
    I = 0.0
    for (x, y), c in cxy.items():
        pxy, px, py = c / n, cx[x] / n, cy[y] / n
        I += pxy * math.log2(pxy / (px * py))
    return I


def conditional_mutual_information(samples_xyz) -> float:
    """I(X;Y | Z) from a list of (x, y, z)."""
    n = len(samples_xyz)
    cz, cxz, cyz, cxyz = Counter(), Counter(), Counter(), Counter()
    for x, y, z in samples_xyz:
        cz[z] += 1; cxz[(x, z)] += 1; cyz[(y, z)] += 1; cxyz[(x, y, z)] += 1
    I = 0.0
    for (x, y, z), c in cxyz.items():
        I += (c / n) * math.log2((cz[z] * c) / (cxz[(x, z)] * cyz[(y, z)]))
    return I


# ---- within-Z shuffle null (the finite-sample bias floor) ----------------------------------------
def shuffle_null(samples_xyz, seed: int = 0) -> float:
    """Permute Y WITHIN each Z stratum (destroys conditional X–Y dependence, preserves the estimator bias),
    then re-measure CMI. A real conditional channel survives this; confounded-only signal does not."""
    rng = random.Random(seed)
    by_z = defaultdict(list)
    for x, y, z in samples_xyz:
        by_z[z].append((x, y))
    out = []
    for _z, pairs in by_z.items():
        ys = [y for _x, y in pairs]
        rng.shuffle(ys)
        out.extend((x, ys[i], _z) for i, (x, _y) in enumerate(pairs))
    return conditional_mutual_information(out)


def shuffle_null_dist(samples_xyz, reps: int = 200, seed: int = 0):
    """A null DISTRIBUTION of CMI under the within-Z shuffle — its mean/std set the detection threshold."""
    return [shuffle_null(samples_xyz, seed + i) for i in range(reps)]


# ---- the audit -----------------------------------------------------------------------------------
@dataclass(frozen=True)
class ResidualChannelResult:
    n: int
    mi: float
    cmi: float
    null_mean: float
    null_std: float
    null_max: float
    z_score: float
    decision: str                     # CONSISTENT_WITH_NULL | RESIDUAL_DEPENDENCE | RESIDUAL_MISSPEC_STABLE | RESIDUAL_MISSPEC_FRAGILE
    misspec_cmis: Tuple = ()

    def as_analysis(self) -> AnalysisResult:
        findings = (
            Finding("MARGINAL_DEPENDENCE", "conditional-dependence", f"I(X;Y)={self.mi:.4f} bits (may be confounded by Z)"),
            Finding("RESIDUAL_DEPENDENCE", "conditional-dependence",
                    f"I(X;Y|Z)={self.cmi:.4f} vs null {self.null_mean:.4f}±{self.null_std:.4f} (z={self.z_score:.1f})"),
            Finding("DECISION", "conditional-dependence", self.decision),
        )
        limitations = (
            Limitation("conditional-dependence", "Z is the MODELED conditioning set; a positive I(X;Y|Z) is "
                                                 "residual dependence, not proof of a channel. residual-CMI ≠ channel"),
            Limitation("conditional-dependence", "absence is about the modeled system + sample size, not a "
                                                 "general guarantee. proves-the-procedure ≠ proves-the-phenomenon"),
            Limitation("method", "finite-sample MI bias is controlled by the within-Z shuffle null; a positive "
                                 "result must be mis-specification-stable to be a channel candidate"),
        )
        return AnalysisResult(source_trace=(), scope="conditional-dependence",
                              findings=findings, limitations=limitations)


def audit(samples_xyz, *, reps: int = 200, seed: int = 0, k_sigma: float = 4.0,
          misspec_fns: Optional[Tuple[Callable, ...]] = None,
          abs_floor: float = 0.005) -> ResidualChannelResult:
    """Decide whether X and Y carry dependence beyond Z. `misspec_fns` (optional) each map a sample list to a
    RE-CONDITIONED sample list (a different/coarser Z); a true channel stays above null under all of them."""
    xy = [(x, y) for x, y, _z in samples_xyz]
    mi = mutual_information(xy)
    cmi = conditional_mutual_information(samples_xyz)
    nd = shuffle_null_dist(samples_xyz, reps=reps, seed=seed)
    mean = sum(nd) / len(nd)
    var = sum((v - mean) ** 2 for v in nd) / len(nd)
    std = math.sqrt(var)
    nmax = max(nd)
    z = (cmi - mean) / std if std > 0 else (math.inf if cmi > mean + abs_floor else 0.0)
    detected = cmi > max(mean + k_sigma * std, mean + abs_floor, nmax)
    decision = "RESIDUAL_DEPENDENCE" if detected else "CONSISTENT_WITH_NULL"
    misspec_cmis: Tuple = ()
    if detected and misspec_fns:
        cmis, stable = [], True
        for fn in misspec_fns:
            ms = fn(samples_xyz)
            c = conditional_mutual_information(ms)
            # Each re-conditioning has its OWN finite-sample MI bias floor (finer strata ⇒ larger bias), so it
            # must be compared to ITS OWN shuffle null — not to the base null. Comparing a fine (Z,W) re-cond to
            # the coarse base floor falsely reads STABLE on a missing-confounder artifact. `bias ≠ signal`.
            mnull = shuffle_null_dist(ms, reps=max(20, reps // 2), seed=seed)
            mmean = sum(mnull) / len(mnull)
            mstd = (sum((v - mmean) ** 2 for v in mnull) / len(mnull)) ** 0.5
            cmis.append(c)
            if not (c > max(mmean + k_sigma * mstd, mmean + abs_floor)):
                stable = False
        misspec_cmis = tuple(cmis)
        decision = "RESIDUAL_MISSPEC_STABLE" if stable else "RESIDUAL_MISSPEC_FRAGILE"
    return ResidualChannelResult(len(samples_xyz), mi, cmi, mean, std, nmax, z, decision, misspec_cmis)


def compression_gain(samples_xyz) -> float:
    """Bits saved by a channel-aware model over one assuming X ⊥ Y | Z. Identically H(Y|Z) − H(Y|X,Z) = I(X;Y|Z).
    So 'compression finds hidden structure' is true exactly to the extent a residual channel exists."""
    yz = [(z, y) for _x, y, z in samples_xyz]
    yxz = [((x, z), y) for x, y, z in samples_xyz]
    return cond_entropy(yz) - cond_entropy(yxz)


# ---- planted-case validator (proves the PROCEDURE, not a phenomenon) ------------------------------
def planted_case_validator(gen_null: Callable, gen_channel: Callable, *, reps: int = 100, seed: int = 0) -> dict:
    """Run the audit on a generator with NO residual channel and one with an injected channel; the procedure
    is sound iff it separates them (null → CONSISTENT_WITH_NULL, channel → RESIDUAL_*)."""
    r0 = audit(gen_null(), reps=reps, seed=seed)
    r2 = audit(gen_channel(), reps=reps, seed=seed)
    return {
        "null_decision": r0.decision, "null_cmi": r0.cmi, "null_z": r0.z_score,
        "channel_decision": r2.decision, "channel_cmi": r2.cmi, "channel_z": r2.z_score,
        "separates": r0.decision == "CONSISTENT_WITH_NULL" and r2.decision.startswith("RESIDUAL"),
    }


# ---- self-contained demo generators (generic; not domain-specific) -------------------------------
def demo_gen_null(n: int = 20000, k: int = 3, seed: int = 1):
    """X, Y both driven by a shared confounder Z; given Z they are INDEPENDENT (no channel)."""
    rng = random.Random(seed)

    def noisy(v):
        return v if rng.random() >= 0.35 else rng.randrange(k)
    out = []
    for _ in range(n):
        z = rng.randrange(k)
        out.append((noisy(z), noisy(z), z))
    return out


def demo_gen_channel(n: int = 20000, k: int = 3, seed: int = 2):
    """A real channel: Y depends on X directly (beyond Z) ⇒ I(X;Y|Z) > 0."""
    rng = random.Random(seed)

    def noisy(v):
        return v if rng.random() >= 0.35 else rng.randrange(k)
    out = []
    for _ in range(n):
        z = rng.randrange(k)
        x = noisy(z)
        out.append((x, noisy(x), z))
    return out


def main():
    print("residual_channel.py — confounder-conditioned dependence audit (domain-agnostic)\n")
    v = planted_case_validator(demo_gen_null, demo_gen_channel)
    print(f"  PLANTED-CASE VALIDATION (proves the procedure):")
    print(f"    null    : CMI={v['null_cmi']:.4f} (z={v['null_z']:.1f}) → {v['null_decision']}")
    print(f"    channel : CMI={v['channel_cmi']:.4f} (z={v['channel_z']:.1f}) → {v['channel_decision']}")
    print(f"    separates null from channel: {v['separates']}")
    print("\n  use: audit(samples_xyz) on YOUR (X, Y, Z=confounder). A positive result is RESIDUAL dependence,")
    print("  a channel candidate only if mis-specification-stable. proves-the-procedure ≠ proves-the-phenomenon.")


if __name__ == "__main__":
    main()
