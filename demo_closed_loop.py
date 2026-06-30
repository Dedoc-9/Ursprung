# SPDX-License-Identifier: AGPL-3.0-only
"""demo_closed_loop.py — the Ursprung Channel Profiler v0.1 thesis, in code.

Closes the loop: MEASURE leakage I(S;O) (with CIs) -> if confidently ABOVE the declared budget, the host (opt-in,
advisory) SHRINKS the detail radius -> the channel changes, the window resets -> RE-MEASURE -> converge below budget.

Honest scoping baked in:
* The environment here is i.i.d. (each frame the hidden state is drawn independently) -- a STOCHASTIC environment
  whose channel has a stationary, analytically-known leakage. A pure greedy *trajectory* NPC parks at a wall and
  its leakage collapses to ~0 (nothing to mediate), so it is a poor demo; that is itself a finding, noted here.
  `trajectory-parks != stationary-channel`.
* The loop is ADVISORY: the profiler emits a CapacityReport with a suggested fidelity; the scene chooses to honor
  it. `telemetry != control`.
* Adaptation reduces leakage by SHRINKING the detail radius (larger radius = more detail = more leakage). This is
  the corrected knob direction.

Run:  python demo_closed_loop.py   ->   prints a convergence table, writes demo_metrics.jsonl, optional PNG.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import List, Optional, Tuple

_ROOT = os.path.dirname(os.path.abspath(__file__))
_TOY = os.path.join(_ROOT, "experiments", "toy_scene")
for _p in (_ROOT, _TOY):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from channel_profiler.estimator import MillerMadowEstimator  # noqa: E402
from channel_profiler.messages import CapacityReport, SessionConfig  # noqa: E402
from channel_profiler.window_manager import WindowManager  # noqa: E402
from scene import ToyGridScene  # noqa: E402

BUDGET = 2.5          # bits/step the host declares acceptable
START_RADIUS = 4      # high fidelity => high leakage (analytic ~ 5.84 bits)
WINDOW = 2500         # samples per estimation window (>> joint support => ESTIMATED)
MAX_WINDOWS = 8
LOG_PATH = os.path.join(_ROOT, "demo_metrics.jsonl")


def _classify(estimate, budget: float, fidelity: float) -> Tuple[str, Optional[float]]:
    """Map an estimate + budget to a gate verdict (confidently above / below, or straddling)."""
    if estimate.verdict != "ESTIMATED":
        return "UNDERDETERMINED", None
    if estimate.ci_lower > budget:
        return "ABOVE_BUDGET", max(0.0, fidelity - 1.0)   # advisory: shrink the detail radius
    if estimate.ci_upper < budget:
        return "BELOW_BUDGET", None
    return "AT_BUDGET", None  # CI straddles the budget -- hold, don't thrash


def _log(fp, **kw) -> None:
    kw["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    fp.write(json.dumps(kw) + "\n")


def run() -> List[dict]:
    cfg = SessionConfig(session_id="demo", budget_bits_per_step=BUDGET, window_size=WINDOW)
    scene = ToyGridScene(seed=0, radius=START_RADIUS, session_id="demo")
    est = MillerMadowEstimator(bootstrap=400, seed=0)
    wm = WindowManager(cfg)
    history: List[dict] = []

    with open(LOG_PATH, "w") as fp:
        frame = 0
        for window_i in range(MAX_WINDOWS):
            triggered = False
            while not triggered:
                s = scene.sample_iid()
                frame += 1
                triggered = wm.push(s)
                if wm.reset_signal:
                    est.reset_window()
                est.ingest(s)
                _log(fp, session="demo", frame=frame, event="sample",
                     secret=str(s.secret_tags), obs=str(s.observation_tags["view"]), fidelity=s.fidelity_level)

            e = est.estimate()
            verdict, suggested = _classify(e, BUDGET, scene.current_fidelity)
            _ = CapacityReport(
                session_id="demo", window_start=frame - WINDOW + 1, window_end=frame,
                estimate=e, budget=BUDGET, verdict=verdict, suggested_fidelity=suggested,
            )
            _log(fp, session="demo", frame=frame, event="estimate", radius=scene.current_fidelity,
                 mi=e.mi_estimate, ci_lo=e.ci_lower, ci_hi=e.ci_upper, n=e.n_samples, verdict=e.verdict)
            _log(fp, session="demo", frame=frame, event="threshold", status=verdict, budget=BUDGET,
                 suggested_fidelity=suggested)
            history.append({"window": window_i, "radius": scene.current_fidelity, "mi": e.mi_estimate,
                            "ci_lo": e.ci_lower, "ci_hi": e.ci_upper, "verdict": verdict})

            if verdict == "ABOVE_BUDGET":
                old = scene.current_fidelity
                scene.apply_fidelity(suggested)  # host opts in to the advisory
                _log(fp, session="demo", frame=frame, event="fidelity_change",
                     old=old, new=scene.current_fidelity, source="client_adapted")
                wm.clear()
                est.reset_window()
            elif verdict == "BELOW_BUDGET":
                break
            else:  # AT_BUDGET / UNDERDETERMINED -- hold without thrashing
                break

    return history


def _print_summary(history: List[dict]) -> None:
    print(f"\nClosed-loop convergence (budget = {BUDGET:.2f} bits/step):\n")
    print("  win  radius   MI (bits)   95% CI            verdict        leakage bar (: = budget)")
    scale = 6.0
    bcol = int(round(BUDGET / scale * 30))
    for h in history:
        mi = h["mi"] or 0.0
        n = int(round(mi / scale * 30))
        bar = "".join("#" if i < n else (":" if i == bcol else " ") for i in range(31))
        ci = f"[{h['ci_lo']:.2f},{h['ci_hi']:.2f}]" if h["ci_lo"] is not None else "(n/a)"
        print(f"  {h['window']:>3}  {h['radius']:>5.0f}   {mi:8.3f}   {ci:<16} {h['verdict']:<13}  {bar}")
    last = history[-1]
    converged = last["verdict"] == "BELOW_BUDGET"
    print(f"\n  result: {'CONVERGED below budget' if converged else 'held at budget (CI straddles)'} "
          f"at radius {last['radius']:.0f}, MI {last['mi']:.3f} bits.")
    print(f"  log: {os.path.basename(LOG_PATH)}  ·  estimate != capacity; measured != guaranteed; telemetry != control")


def _maybe_plot(history: List[dict]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("  (matplotlib not available -- skipping PNG; the table above is the result)")
        return
    xs = [h["window"] for h in history]
    mis = [h["mi"] or 0.0 for h in history]
    los = [h["ci_lo"] or 0.0 for h in history]
    his = [h["ci_hi"] or 0.0 for h in history]
    lo_err = [max(0.0, m - l) for m, l in zip(mis, los)]  # clamp: bootstrap CI need not bracket the point
    hi_err = [max(0.0, h - m) for m, h in zip(his, mis)]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(xs, mis, yerr=[lo_err, hi_err], fmt="o-", capsize=4, label="measured I(S;O)")
    ax.axhline(BUDGET, ls="--", color="r", label=f"budget {BUDGET} bits")
    for h in history:
        if h["verdict"] == "ABOVE_BUDGET":
            ax.annotate(f"shrink r->{h['radius'] - 1:.0f}", (h["window"], h["mi"] or 0.0), fontsize=8)
    ax.set_xlabel("estimation window")
    ax.set_ylabel("bits / step")
    ax.set_title("Closed-loop QIF profiling -- measure -> adapt -> re-measure")
    ax.legend()
    out = os.path.join(_ROOT, "demo_convergence.png")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"  plot: {os.path.basename(out)}")


if __name__ == "__main__":
    hist = run()
    _print_summary(hist)
    _maybe_plot(hist)
