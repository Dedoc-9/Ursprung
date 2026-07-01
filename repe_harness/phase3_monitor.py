# SPDX-License-Identifier: AGPL-3.0-only
"""phase3_monitor.py — RepE Phase 3: streaming multi-turn escalation monitor.

The honest "drift" tracker: consumes the Phase-1 probe score per conversation turn (read live by the Phase-2
engine) and detects UPWARD drift — the multi-turn-jailbreak pattern where each turn nudges the harm score up.
It is a MONITOR (observe/detect), NOT a "dissipator": intervention is Phase-2 steering triggered by this flag.
`adjacent != on-mission`; `measured != guaranteed`; `detection != prevention`.

Method: an upward CUSUM change-detector (slack `k`, threshold `h`) plus a least-squares slope. Causal /
streaming — `update(score_t)` uses only turns <= t (a real-time monitor cannot peek ahead). Reports a PANEL
(`max_cusum` AND `slope` AND `max_score`) side by side, never one fused "danger score". `panel != scalar`.

Verified by `--selftest` (5/5, numpy, no GPU): on synthetic escalating-vs-benign sessions it separates them
(AUROC 1.0) at ~0 benign false positives, returns ~0.5 on noise, keeps `max_cusum` monotone, and reports a
panel. The REAL multi-turn detection rate (your model + real multi-turn attacks) is yours to measure at the
Phase-3 milestone — this file never asserts it.

Wiring: per turn, take the Phase-2 engine's `last_scores()` for the monitored layer and call `monitor.update()`.
"""
from __future__ import annotations
import argparse
import numpy as np


def auroc(scores, labels):
    s = np.asarray(scores, float); y = np.asarray(labels, int); pos, neg = s[y == 1], s[y == 0]
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    order = np.argsort(np.concatenate([neg, pos]), kind="mergesort")
    ranks = np.empty(order.size, float); ranks[order] = np.arange(1, order.size + 1)
    return float((ranks[neg.size:].sum() - pos.size * (pos.size + 1) / 2) / (pos.size * neg.size))


class SessionMonitor:
    """Streaming CUSUM monitor over per-turn probe scores; flags sustained UPWARD drift (escalation)."""

    def __init__(self, k=0.5, h=3.0, ewma_lambda=0.3):
        self.k = float(k); self.h = float(h); self.lam = float(ewma_lambda); self.reset()

    def reset(self):
        self.scores = []; self.cusum = 0.0; self.max_cusum = 0.0; self.ewma = None

    def update(self, score):
        score = float(score); self.scores.append(score)
        self.cusum = max(0.0, self.cusum + (score - self.k))         # upward CUSUM with slack k
        self.max_cusum = max(self.max_cusum, self.cusum)
        self.ewma = score if self.ewma is None else self.lam * score + (1 - self.lam) * self.ewma
        return {"turn": len(self.scores), "score": score, "cusum": self.cusum,
                "ewma": self.ewma, "escalating": self.cusum > self.h}

    def slope(self):
        n = len(self.scores)
        return 0.0 if n < 2 else float(np.polyfit(np.arange(n), np.array(self.scores), 1)[0])

    def report(self):
        return {"n_turns": len(self.scores), "max_cusum": self.max_cusum, "slope": self.slope(),
                "max_score": max(self.scores) if self.scores else float("nan"),
                "escalating": self.max_cusum > self.h}


def selftest() -> int:
    rng = np.random.default_rng(0); T = 8; M = 120

    def stat(scores):
        m = SessionMonitor(); mono = True; prev = 0.0
        for sc in scores:
            m.update(sc)
            if m.max_cusum < prev - 1e-9:
                mono = False
            prev = m.max_cusum
        return m.report(), mono

    esc, ben, monos, fp = [], [], [], 0
    for _ in range(M):
        re, mo1 = stat(np.linspace(0, 2.5, T) + rng.normal(0, 0.3, T))   # escalating: score ramps up
        rb, mo2 = stat(rng.normal(0, 0.3, T))                            # benign: flat low
        esc.append(re["max_cusum"]); ben.append(rb["max_cusum"]); monos += [mo1, mo2]; fp += int(rb["escalating"])
    labels = np.array([1] * M + [0] * M)
    a = auroc(np.array(esc + ben), labels)
    a_noise = auroc(rng.normal(0, 1, 2 * M), labels)                     # random stat, same labels -> ~0.5
    fpr = fp / M
    rep = SessionMonitor(); [rep.update(v) for v in (0.1, 0.2, 1.5)]; rk = set(rep.report().keys())
    ok_sep, ok_noise, ok_mono = a > 0.95, 0.35 < a_noise < 0.65, all(monos)
    ok_fpr, ok_panel = fpr < 0.10, {"max_cusum", "slope"} <= rk
    print(f"[selftest] escalating-vs-benign AUROC(max_cusum) = {a:.3f}   (want >0.95: {ok_sep})")
    print(f"[selftest] benign false-positive rate           = {fpr:.3f}   (want <0.10: {ok_fpr})")
    print(f"[selftest] noise-control AUROC                   = {a_noise:.3f}   (want ~0.5: {ok_noise})")
    print(f"[selftest] max_cusum monotone non-decreasing     = {ok_mono}")
    print(f"[selftest] report is a panel (max_cusum+slope)   = {ok_panel}")
    ok = ok_sep and ok_noise and ok_mono and ok_fpr and ok_panel
    print(f"[selftest] {'PASS 5/5 - monitor mechanics valid' if ok else 'FAIL'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="RepE Phase 3 multi-turn escalation monitor")
    ap.add_argument("--selftest", action="store_true", help="validate detector on synthetic sessions (no GPU)")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("feed per-turn probe scores to SessionMonitor.update(); run --selftest to validate mechanics.")


if __name__ == "__main__":
    main()
