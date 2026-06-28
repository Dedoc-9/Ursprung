# SPDX-License-Identifier: AGPL-3.0-only
"""
snow_infotheory.py — the snowflake instance of the domain-agnostic causal diagnostic in
`weltwerk/verify/residual_channel.py`. The estimators and the shuffle-null live there now; this module is one
CALLER that supplies snowflake-flavored generators (shared field vs injected inter-arm channel) and the
compression/manifold views. `proves-the-procedure ≠ proves-the-phenomenon`.

The decisive question is unchanged: is there dependence between branches beyond the shared growth field?

    I(X;Y)        > 0   ← confounded by the shared field (standard physics). Not a language.
    I(X;Y | field)> 0   ← a genuine inter-branch channel — information beyond shared cause.

Standard crystal-growth physics predicts I(X;Y|field) = 0; a "language" needs a real channel. See
`snowflake/LANGUAGE_AUDIT.md` and `residual_channel.py` for the general procedure and its limits.
"""
from __future__ import annotations

import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))
from snow_grammar import _mode                                   # noqa: E402  (field→growth-mode law)
from residual_channel import (entropy, cond_entropy, mutual_information,           # noqa: E402,F401
                              conditional_mutual_information, compression_gain,
                              shuffle_null as _shuffle_null)

K = 3                  # alphabet size for the arm token in the synthetic channel experiment
N = 40000              # samples (large enough that MI estimator bias is small and the null is tight)


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


# ---- semantic manifold: dimension == number of physical control parameters -----------------------
def _feature(temp_c, supersat, spurious):
    return _mode(temp_c, supersat)


def manifold_dimension() -> dict:
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
    print("snow_infotheory.py — branch-channel test via residual_channel.py (the general diagnostic)\n")
    c = channel_test()
    print("  CHANNEL TEST (bits):")
    print(f"    H0 (shared cause, no channel): MI={c['H0_MI']:.4f}  CMI={c['H0_CMI']:.4f}  null={c['H0_null']:.4f}")
    print(f"    H2 (injected inter-arm chan.): MI={c['H2_MI']:.4f}  CMI={c['H2_CMI']:.4f}  null={c['H2_null']:.4f}")
    g0 = compression_gain(gen_H0()[1])
    g2 = compression_gain(gen_H2()[1])
    print(f"  COMPRESSION = CHANNEL:  gain_H0={g0:.4f} bits (≈0)   gain_H2={g2:.4f} bits (≈ CMI {c['H2_CMI']:.4f})")
    m = manifold_dimension()
    print(f"  SEMANTIC MANIFOLD:  effective_dim={m['effective_dim']} == physical controls={m['n_physical_controls']}")
    print("\n  conditional MI ≈ 0 under standard physics; the general procedure lives in residual_channel.py.")


if __name__ == "__main__":
    main()
