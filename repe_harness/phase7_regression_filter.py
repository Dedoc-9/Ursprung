# SPDX-License-Identifier: AGPL-3.0-only
"""phase7_regression_filter.py — RepE Phase 7: Automated Regression Filter for steering vectors / probes.

NOT an RSI engine. `regression-filter != self-improvement-engine`. It solves the real production problem the
RepE arc surfaces: steering vectors and probes DEGRADE over time (distribution shift, safety drift), and naive
"retrain and replace" can silently make things WORSE via proxy-exploitation. This layer is the promotion-gate
discipline of `weltwerk`/`live_world_kernel`'s rsi_engine applied to vector maintenance.

A candidate vector REPLACES the incumbent ONLY if it passes all three gates:
  1. external gain  -- higher on a HELD-OUT eval it was NOT fit on (not the proxy/train metric)
  2. replication    -- the gain holds across >= rep_frac of seeds/splits (not one lucky draw)
  3. calibration    -- the proxy gain does NOT run ahead of the external gain (catches overfit; the runaway
                       signature m_hat > 1 >= m_verified)
Any gate fails -> REJECT, keep the incumbent (regression prevented). Plus drift detection: flag when the
incumbent's own held-out score falls below a safety floor (time to refresh).

The promotion RATE it reports is a bounded acceptance fraction in [0,1] -- a filter's selectivity, NOT a
branching multiplier that could exceed 1. Consistent with the arc's measured `m_verified <= 1`: this BOUNDS
regressions; it does not manufacture open-ended improvement. `iteration != open-ended`;
`promoted != better-in-the-world`.

Verified by `--selftest` (GPU-free, synthetic): promotes a genuinely-better candidate; REJECTS a proxy-overfit
one (uncalibrated), a non-replicated lucky one, and a no-gain one; never promotes on proxy alone; detects drift.
The real vector performance is measured by YOU on your model + held-out evals; this file asserts no such number.
"""
from __future__ import annotations
import argparse
import numpy as np


def promotion_gate(incumbent_ext, cand_ext, incumbent_proxy, cand_proxy, rep_frac=0.6, cal_tol=0.01):
    """*_ext: per-seed HELD-OUT scores (higher=better). *_proxy: scalar train/dev score. Promote iff external
    gain > 0 AND replicated across seeds AND calibrated (proxy not ahead of external)."""
    inc = np.asarray(incumbent_ext, float); can = np.asarray(cand_ext, float)
    gains = can - inc
    external_gain = float(gains.mean())
    replicated = bool((gains > 0).mean() >= rep_frac)
    proxy_gain = float(cand_proxy - incumbent_proxy)
    calibrated = bool((proxy_gain - external_gain) <= cal_tol)
    promote = bool(external_gain > 0 and replicated and calibrated)
    reason = ("PROMOTE" if promote else
              "no-external-gain" if external_gain <= 0 else
              "not-replicated" if not replicated else "uncalibrated(proxy-overfit)")
    return {"promote": promote, "external_gain": external_gain, "replicated": replicated,
            "proxy_gain": proxy_gain, "calibrated": calibrated, "reason": reason}


def drift_flag(held_out_series, floor):
    """Flag when the incumbent's latest held-out score falls below the safety floor (drift -> needs refresh)."""
    s = list(map(float, held_out_series))
    return {"drifted": bool(s[-1] < floor), "latest": s[-1], "floor": floor}


def promotion_rate(gate_results):
    """Bounded acceptance fraction in [0,1] — a FILTER'S selectivity, NOT a branching multiplier (never > 1)."""
    return float(np.mean([g["promote"] for g in gate_results])) if gate_results else float("nan")


def selftest() -> int:
    rng = np.random.default_rng(0); S = 5
    base = 0.70 + rng.normal(0, 0.01, S); inc_proxy = 0.72
    genuine = promotion_gate(base, base + 0.10, inc_proxy, inc_proxy + 0.10)
    overfit = promotion_gate(base, base + rng.normal(0, 0.01, S), inc_proxy, inc_proxy + 0.50)
    lucky = base.copy(); lucky[0] += 0.6; lucky[1:] -= 0.15
    nonrep = promotion_gate(base, lucky, inc_proxy, inc_proxy + 0.05)
    nogain = promotion_gate(base, base + rng.normal(0, 0.01, S), inc_proxy, inc_proxy)
    ok_gen = genuine["promote"] is True
    ok_over = overfit["promote"] is False and overfit["calibrated"] is False
    ok_rep = nonrep["promote"] is False and nonrep["replicated"] is False
    ok_none = nogain["promote"] is False
    ok_inv = not overfit["promote"]
    ok_drift = (drift_flag([0.9, 0.85, 0.8, 0.6], 0.7)["drifted"] is True
                and drift_flag([0.9, 0.88, 0.86], 0.7)["drifted"] is False)
    rate = promotion_rate([genuine, overfit, nonrep, nogain])
    ok_bounded = 0.0 < rate < 1.0
    ok_panel = {"external_gain", "replicated", "proxy_gain", "calibrated"} <= set(genuine.keys())
    print(f"[selftest] genuine held-out gain -> PROMOTE       : {ok_gen}  ({genuine['reason']})")
    print(f"[selftest] proxy-overfit -> REJECT (uncalibrated) : {ok_over}  ({overfit['reason']})")
    print(f"[selftest] one-lucky-seed -> REJECT (not repl.)   : {ok_rep}  ({nonrep['reason']})")
    print(f"[selftest] no gain -> REJECT                      : {ok_none}  ({nogain['reason']})")
    print(f"[selftest] invariant: never promote on proxy alone: {ok_inv}")
    print(f"[selftest] drift detection (below/above floor)    : {ok_drift}")
    print(f"[selftest] promotion rate {rate:.2f} in (0,1), bounded : {ok_bounded}  (a filter rate, NOT a multiplier)")
    print(f"[selftest] panel-not-scalar report                : {ok_panel}")
    ok = all([ok_gen, ok_over, ok_rep, ok_none, ok_inv, ok_drift, ok_bounded, ok_panel])
    print(f"[selftest] {'PASS 8/8 - regression filter valid (rejects overfit/lucky/no-gain, keeps incumbent)' if ok else 'FAIL'}")
    print("[frame]    Automated Regression Filter: prevents vector regressions + flags drift. NOT an RSI engine;")
    print("[frame]    promotion rate is bounded selectivity (m_verified-style <= 1), never open-ended.")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="RepE Phase 7 automated regression filter (promotion gate + drift)")
    ap.add_argument("--selftest", action="store_true", help="validate the gate + drift logic on synthetic scores")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("gate candidate vectors with promotion_gate(); track incumbents with drift_flag(); run --selftest.")


if __name__ == "__main__":
    main()
