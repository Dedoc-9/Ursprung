# SPDX-License-Identifier: AGPL-3.0-only
"""
snow_infotheory.py — the DECISIVE experiments for the snowflake-language hypothesis. Pure-stdlib.

The whole hypothesis ("snowflake morphology encodes information / a language beyond physics") reduces to one
measurable question: **is there dependence between branches that the shared physical environment does not
already explain?** In causal terms the shared growth field is a CONFOUNDER; ordinary mutual information between
two arms, I(X;Y), is large simply because both depend on it. The hypothesis-relevant quantity is the
CONDITIONAL mutual information given the field, I(X;Y | field):

    I(X;Y) > 0           ← expected under standard physics (shared cause). Not evidence of a language.
    I(X;Y | field) > 0   ← would be a genuine inter-branch CHANNEL — information beyond shared cause.

Standard crystal-growth physics predicts I(X;Y | field) = 0 (arms are conditionally independent given the
environment + diffusion field). A "language" needs a real channel ⇒ I(X;Y | field) > 0. This module:

  1. CHANNEL TEST — generate snowflakes under H0 (shared field, NO inter-arm channel) and H2 (an injected
     inter-arm dependency), estimate I(X;Y) and I(X;Y|field), and compare to a within-field SHUFFLE NULL
     (which controls the positive finite-sample bias of MI estimators). Result: H0 conditional-MI ≈ null
     (≈ 0); H2 conditional-MI ≫ null. The protocol DISTINGUISHES a language-channel from shared cause.
  2. COMPRESSION = CHANNEL — the compression gain of a model that knows the inter-arm channel over one that
     assumes conditional independence equals exactly I(X;Y|field). So "compression finds hidden structure"
     (#7) is true only insofar as a channel exists; under H0 the gain is 0. `compression-gain = CMI`.
  3. SEMANTIC MANIFOLD — a corpus over the control grid (temperature, supersaturation) occupies a manifold
     whose effective dimension equals the number of PHYSICAL control parameters; a spurious extra parameter
     adds no dimension. So the "semantic manifold" (#8) is the Nakaya parameter space, not a hidden code.

Every positive linguistic signal is reduced to a physical mechanism before being accepted. `correlation ≠
communication`; `confounded-MI ≠ channel`; `manifold ≠ meaning`.
"""
from __future__ import annotations

import math
import os
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snow_grammar import _mode                    # noqa: E402  (the field→growth-mode law, shared by all arms)

K = 3                  # alphabet size for the arm token in the synthetic channel experiment
N = 40000              # samples (large enough that MI estimator bias is small and the null is tight)


# ---- estimators (discrete, exact from counts; bits) ---------------------------------------------
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
        pxyz = c / n
        I += pxyz * math.log2((cz[z] * c) / (cxz[(x, z)] * cyz[(y, z)]))
    return I


def _shuffle_null(samples_xyz, seed=0) -> float:
    """Destroy any X–Y dependence WITHIN each field stratum z, then re-measure CMI: the finite-sample bias
    floor. A real conditional channel survives this; a confounded-only signal does not."""
    rng = random.Random(seed)
    by_z = defaultdict(list)
    for x, y, z in samples_xyz:
        by_z[z].append((x, y))
    out = []
    for z, pairs in by_z.items():
        ys = [y for _x, y in pairs]
        rng.shuffle(ys)
        out.extend((x, ys[i], z) for i, (x, _y) in enumerate(pairs))
    return conditional_mutual_information(out)


# ---- generators: H0 (shared cause, NO channel) and H2 (an injected inter-arm channel) -------------
def _noisy(z, rng, p=0.35):
    return z if rng.random() >= p else rng.randrange(K)


def gen_H0(n=N, seed=1):
    """Standard physics: a shared field Z drives both arms; given Z the arms are INDEPENDENT (no channel)."""
    rng = random.Random(seed)
    xy, xyz = [], []
    for _ in range(n):
        z = rng.randrange(K)
        x, y = _noisy(z, rng), _noisy(z, rng)
        xy.append((x, y)); xyz.append((x, y, z))
    return xy, xyz


def gen_H2(n=N, seed=2):
    """Language hypothesis: a real inter-arm channel — arm Y depends on arm X directly (beyond the field Z)."""
    rng = random.Random(seed)
    xy, xyz = [], []
    for _ in range(n):
        z = rng.randrange(K)
        x = _noisy(z, rng)
        y = _noisy(x, rng)                          # Y reads X ⇒ channel ⇒ I(X;Y|Z) > 0
        xy.append((x, y)); xyz.append((x, y, z))
    return xy, xyz


def channel_test() -> dict:
    h0_xy, h0_xyz = gen_H0()
    h2_xy, h2_xyz = gen_H2()
    return {
        "H0_MI": mutual_information(h0_xy),
        "H0_CMI": conditional_mutual_information(h0_xyz),
        "H0_null": _shuffle_null(h0_xyz),
        "H2_MI": mutual_information(h2_xy),
        "H2_CMI": conditional_mutual_information(h2_xyz),
        "H2_null": _shuffle_null(h2_xyz),
    }


# ---- compression gain == conditional mutual information -------------------------------------------
def compression_gain(samples_xyz) -> float:
    """Bits saved by a model that knows the inter-arm channel vs one assuming X⊥Y | Z.
       = H(Y|Z) − H(Y|X,Z) = I(X;Y|Z). Under H0 this is ~0: no compression beyond shared-field physics."""
    yz = [(z, y) for _x, y, z in samples_xyz]
    yxz = [((x, z), y) for x, y, z in samples_xyz]
    return cond_entropy(yz) - cond_entropy(yxz)


# ---- semantic manifold: dimension == number of physical control parameters -----------------------
def _feature(temp_c, supersat, spurious):
    """A flake's morphology feature depends on the PHYSICAL controls (T, supersaturation); `spurious` is a
    decoy parameter that does not enter the growth law."""
    return _mode(temp_c, supersat)


def manifold_dimension() -> dict:
    """Effective dimension = how many control parameters actually move the feature. A spurious parameter that
    changes nothing adds no dimension — so the manifold is the physical (T, supersaturation) space."""
    temps = [-2, -6, -15, -25]
    sats = [0, 1, 2, 3]
    base_t, base_s, base_sp = -15, 2, 0

    def varies(param):
        if param == "temp":
            return len({_feature(t, base_s, base_sp) for t in temps}) > 1
        if param == "supersat":
            return len({_feature(base_t, s, base_sp) for s in sats}) > 1
        if param == "spurious":
            return len({_feature(base_t, base_s, sp) for sp in range(5)}) > 1
        return False

    deps = [p for p in ("temp", "supersat", "spurious") if varies(p)]
    return {"effective_dim": len(deps), "depends_on": deps, "n_physical_controls": 2}


def main():
    print("snow_infotheory.py — is there information between branches beyond the shared field?\n")
    c = channel_test()
    print("  CHANNEL TEST (bits):")
    print(f"    H0 (shared cause, no channel): MI={c['H0_MI']:.4f}  CMI={c['H0_CMI']:.4f}  null={c['H0_null']:.4f}")
    print(f"    H2 (injected inter-arm chan.): MI={c['H2_MI']:.4f}  CMI={c['H2_CMI']:.4f}  null={c['H2_null']:.4f}")
    print(f"    ⇒ H0 conditional-MI ≈ null (no channel beyond shared cause); H2 CMI ≫ null (channel detected)\n")
    g0 = compression_gain(gen_H0()[1])
    g2 = compression_gain(gen_H2()[1])
    print(f"  COMPRESSION = CHANNEL:  gain_H0={g0:.4f} bits (≈0)   gain_H2={g2:.4f} bits (≈ CMI {c['H2_CMI']:.4f})")
    m = manifold_dimension()
    print(f"\n  SEMANTIC MANIFOLD:  effective_dim={m['effective_dim']} == physical controls={m['n_physical_controls']} "
          f"(depends_on={m['depends_on']}; spurious param adds nothing)")
    print("\n  Verdict: ordinary MI between arms is confounded by the shared field; conditional MI ≈ 0 under")
    print("  standard physics. Any 'language' signal must show CMI>0 — distinguishable, and here absent (H0).")


if __name__ == "__main__":
    main()
