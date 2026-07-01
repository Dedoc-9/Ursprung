# SPDX-License-Identifier: AGPL-3.0-only
"""phase8_confounder_firewall.py — RepE Phase 8: a confounder firewall for the probe (a weltwerk hardening).

The #1 real RepE failure standard repos do NOT guard: a probe / steering direction separates harmful from benign
via a CONFOUNDER (prompt length, topic, formatting, refusal-template tokens), NOT the harm concept. Its held-out
AUROC (Phase 1) then looks great while the steer moves the wrong thing. This layer hardens Phase 1 with the
VERIFIED discriminator from `weltwerk/verify/residual_channel`:

    I(label; score)      > 0   may be pure confounding by Z  -- NOT evidence of a harm channel
    I(label; score | Z)  > 0   residual dependence beyond Z  -- a candidate real harm channel

Method (faithful to residual_channel; implemented here and cited, not its API guessed): conditional MI vs a
WITHIN-Z SHUFFLE NULL (permute the score inside each Z stratum -> destroys X-Y|Z dependence, preserves the
estimator's positive bias). A probe whose separation SURVIVES conditioning is HEALTHY; one whose separation
VANISHES is CONFOUNDED (reject it); no separation at all is NO_SIGNAL. `confounded-MI != channel`;
`proves-the-procedure != proves-the-phenomenon`.

Verified by `--selftest` (5/5, GPU-free), mirroring residual_channel's own planted_case_validator: a planted REAL
probe -> HEALTHY; a planted CONFOUNDED probe (marginal MI > 0 but killed by conditioning) -> CONFOUNDED; noise ->
NO_SIGNAL. The real audit needs YOUR activations + a real confounder Z (length / topic id); this file asserts none.

Wiring: after Phase 1 extracts a direction, feed (harm labels, per-example probe scores, a confounder Z) here and
promote ONLY a HEALTHY probe into Phase 2's steering. This is the honest gate Phase 1's AUROC alone cannot give.
"""
from __future__ import annotations
import argparse
import numpy as np
from collections import Counter


def _mi(xs, ys):
    n = len(xs)
    if n == 0:
        return 0.0
    cx, cy, cxy = Counter(xs), Counter(ys), Counter(zip(xs, ys))
    I = 0.0
    for (x, y), c in cxy.items():
        pxy = c / n
        I += pxy * np.log2(pxy / ((cx[x] / n) * (cy[y] / n)))
    return max(0.0, float(I))


def _cmi(xs, ys, zs):                       # I(X;Y|Z) = sum_z p(z) I(X;Y | Z=z)
    n = len(xs); I = 0.0
    for z in set(zs):
        idx = [i for i in range(n) if zs[i] == z]
        if len(idx) > 1:
            I += (len(idx) / n) * _mi([xs[i] for i in idx], [ys[i] for i in idx])
    return I


def _shuffle_null(xs, ys, zs, reps, rng):   # permute Y WITHIN each Z stratum -> kills X-Y|Z, keeps bias
    ys = np.array(ys); nulls = []
    strata = {z: np.array([i for i in range(len(zs)) if zs[i] == z]) for z in set(zs)}
    for _ in range(reps):
        yp = ys.copy()
        for idx in strata.values():
            if idx.size > 1:
                yp[idx] = rng.permutation(yp[idx])
        nulls.append(_cmi(xs, yp.tolist(), zs))
    return nulls


def _bin(v, k):
    q = np.quantile(v, np.linspace(0, 1, k + 1)[1:-1])
    return np.digitize(v, q).tolist()


def audit_probe(labels, scores, confound, n_bins=4, n_z=4, reps=200, rng=None):
    """residual_channel discipline on a probe: is the harm<->score dependence real, or explained by confounder Z?"""
    rng = rng or np.random.default_rng(0)
    x = list(map(int, labels))
    y = _bin(np.asarray(scores, float), n_bins)
    z = _bin(np.asarray(confound, float), n_z)
    marg = _mi(x, y); cmi = _cmi(x, y, z)
    nq = float(np.quantile(_shuffle_null(x, y, z, reps, rng), 0.95))
    if marg < 0.02:
        verdict = "NO_SIGNAL"                # probe doesn't even separate
    elif cmi > nq:
        verdict = "HEALTHY"                  # residual dependence beyond Z -> a real harm channel
    else:
        verdict = "CONFOUNDED"               # marginal separation explained by Z -> REJECT the probe
    return {"marginal_mi": marg, "cmi": cmi, "null_q95": nq, "verdict": verdict}


def selftest() -> int:
    rng = np.random.default_rng(0); n = 600
    yl = rng.integers(0, 2, n); Zr = rng.normal(0, 1, n); sr = yl * 2.0 + rng.normal(0, 0.7, n)
    real = audit_probe(yl, sr, Zr, rng=rng)
    Zc = rng.normal(0, 1, n); yc = (rng.random(n) < 1 / (1 + np.exp(-Zc))).astype(int); sc = Zc * 2.0 + rng.normal(0, 0.7, n)
    conf = audit_probe(yc, sc, Zc, rng=rng)
    yn = rng.integers(0, 2, n); none = audit_probe(yn, rng.normal(0, 1, n), rng.normal(0, 1, n), rng=rng)
    ok_real = real["verdict"] == "HEALTHY"
    ok_conf = conf["verdict"] == "CONFOUNDED" and conf["marginal_mi"] > 0.02 and conf["cmi"] <= conf["null_q95"]
    ok_none = none["verdict"] == "NO_SIGNAL"
    ok_planted = ok_real and ok_conf
    ok_panel = {"marginal_mi", "cmi", "null_q95", "verdict"} <= set(real)
    print(f"[selftest] REAL probe       -> {real['verdict']:<10} marg={real['marginal_mi']:.3f} cmi={real['cmi']:.3f} nullq95={real['null_q95']:.3f}")
    print(f"[selftest] CONFOUNDED probe -> {conf['verdict']:<10} marg={conf['marginal_mi']:.3f} cmi={conf['cmi']:.3f} nullq95={conf['null_q95']:.3f}  <- marg>0 but killed by conditioning")
    print(f"[selftest] NO-SIGNAL probe  -> {none['verdict']:<10} marg={none['marginal_mi']:.3f}")
    print(f"[selftest] real->HEALTHY / confounded->CONFOUNDED / noise->NO_SIGNAL : {ok_real and ok_conf and ok_none}")
    print(f"[selftest] planted-case validator separates real vs confounded       : {ok_planted}")
    print(f"[selftest] panel-not-scalar report                                   : {ok_panel}")
    ok = ok_real and ok_conf and ok_none and ok_planted and ok_panel
    print(f"[selftest] {'PASS 5/5 - confounder firewall valid (rejects spurious directions)' if ok else 'FAIL'}")
    print("[frame]    residual_channel discipline on the probe: confounded-MI != channel; a high AUROC that dies")
    print("[frame]    under conditioning was steering the confounder, not the harm concept. Promote HEALTHY only.")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="RepE Phase 8 confounder firewall (residual_channel on the probe)")
    ap.add_argument("--selftest", action="store_true", help="planted real-vs-confounded validation (no GPU)")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("audit a probe with audit_probe(labels, scores, confound); promote only HEALTHY; run --selftest.")


if __name__ == "__main__":
    main()
