#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""orchestrator.py — repe_harness execution coordinator, bridged to the REAL weltwerk/verify kernel.

This is the *adjacent* harness consuming the verification kernel — NOT weltwerk/verify/orchestrator.py (the
kernel's own claim/action gate). `adjacent != on-mission`. It composes the proposed gate order using the REAL
types, not the phase stubs:

    P8 firewall  = weltwerk/verify/residual_channel.audit(...)   -> a typed ResidualChannelResult
    P9 ground    = epistemic_types.ChannelEstablished(result) -> Grounded.ground(steer, proof)
                   (grounds IFF result.decision == "RESIDUAL_MISSPEC_STABLE"; else UngroundedError BEFORE effect)
    P3 monitor / P4 falsify / P10 air-gap = the harness's own (pure-numpy/stdlib) stages, run for the panel.

TWO-STATUS RULE. Apparatus: the wiring works (GPU-free --selftest on synthetic planted/confounded samples).
Real-model number: whether steering actually reduces ASR is YOURS to measure. This file asserts no model number.

SEAM (surfaced, not hidden): the real weltwerk `Grounded` exposes `.value`; `phase10_airgap.commit` duck-types on
`.get()`. So a real Grounded is adapted by `_Getable` at the P10 boundary ONLY. Recommended follow-up: widen
`phase10_airgap.commit` to accept `.value` (or a real Grounded) so no shim is needed. `claim != code`.

GRADE:         apparatus VERIFIED when --selftest passes.
DOES_NOT_SHOW: that the model is safe (safety stays SPECULATIVE until phase4.grade()=="MEASURED" on real
               held-out attacks with neutral_ruler_ok); that the numbers are real (synthetic here); that the
               ordering is optimal/complete (`built != validated`). Grounded[T] is a runtime pre-effect guard,
               not a compile-time/cryptographic proof. `integration != safety`; `grounded != true`.
"""
from __future__ import annotations
import argparse
import os
import sys


def _find_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    d = here
    while True:
        if any(os.path.exists(os.path.join(d, m)) for m in (".git", "method.md", "AGENTS.md")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.dirname(here)   # fallback: repo root = parent of repe_harness/
        d = parent


ROOT = os.environ.get("URSPRUNG_ROOT") or _find_root()
sys.path.insert(0, os.path.join(ROOT, "repe_harness"))
sys.path.insert(0, os.path.join(ROOT, "weltwerk", "verify"))

try:
    from residual_channel import audit                                   # noqa: E402
    from epistemic_types import Grounded, ChannelEstablished, UngroundedError  # noqa: E402
    _KERNEL_OK, _KERNEL_ERR = True, None
except Exception as e:                                                   # fail-closed; NEVER stub silently
    _KERNEL_OK, _KERNEL_ERR = False, e


class _Getable:
    """Boundary SHIM: real weltwerk Grounded exposes `.value`; phase10.commit duck-types on `.get()`.
    Adapts a real Grounded at the P10 boundary ONLY. SEAM surfaced in the module docstring."""
    def __init__(self, grounded):
        self._g = grounded

    def get(self):
        return self._g.value


def _require_kernel() -> None:
    if not _KERNEL_OK:
        raise RuntimeError(
            f"weltwerk/verify kernel not importable — orchestrator FAILS CLOSED (no stub fallback): "
            f"{_KERNEL_ERR}. Run from the repo or set URSPRUNG_ROOT=/path/to/Ursprung.")


def firewall(samples_xyz, misspec_fns, *, reps=200, seed=0, k_sigma=4.0, abs_floor=0.005):
    """P8 bridge: raw (label, score, confounder) samples -> a REAL typed ResidualChannelResult.
    misspec_fns are REQUIRED to reach RESIDUAL_MISSPEC_STABLE (a channel candidate); without them a positive
    result is only RESIDUAL_DEPENDENCE and will NOT ground. `residual-CMI != channel` until MISSPEC_STABLE."""
    _require_kernel()
    return audit(samples_xyz, reps=reps, seed=seed, k_sigma=k_sigma, misspec_fns=misspec_fns, abs_floor=abs_floor)


def ground_steer(steer_vector, result):
    """P9 bridge: build a REAL Grounded[steer] via ChannelEstablished — iff result.decision ==
    'RESIDUAL_MISSPEC_STABLE'. Otherwise raises UngroundedError BEFORE any steer can be applied."""
    _require_kernel()
    return Grounded.ground(steer_vector, ChannelEstablished(result))


def orchestrate(*, samples_xyz, steer_vector, misspec_fns, session_scores=None,
                asr_before=None, asr_after=None, reps=200, seed=0) -> dict:
    """Run the proposed gate order with the REAL kernel; return a PANEL (never a single 'safe' scalar).
    A non-groundable direction HALTS at P9: no steer, no downstream commit. `panel != scalar`."""
    _require_kernel()
    panel: dict = {}

    r = firewall(samples_xyz, misspec_fns, reps=reps, seed=seed)
    panel["p8_firewall"] = {"decision": r.decision, "cmi": round(r.cmi, 4), "z": round(r.z_score, 1),
                            "groundable": r.decision == "RESIDUAL_MISSPEC_STABLE"}

    try:
        grounded = ground_steer(steer_vector, r)
    except UngroundedError as e:
        panel["p9_ground"] = {"grounded": False, "refused_before_effect": str(e)}
        panel["overall"] = {"steer": "REFUSED_FAIL_CLOSED", "safety": "SPECULATIVE",
                            "note": "confounded/unstable direction cannot construct a steer"}
        return panel
    panel["p9_ground"] = {"grounded": True, "proof": ChannelEstablished(r).label(), "value_access": ".value"}

    if session_scores is not None:
        from phase3_monitor import SessionMonitor
        mon = SessionMonitor()
        for s in session_scores:
            mon.update(float(s))
        rep = mon.report()
        panel["p3_monitor"] = {"escalating": bool(rep["escalating"]), "max_cusum": round(float(rep["max_cusum"]), 3)}

    if asr_before is not None and asr_after is not None:
        from phase4_falsify import compare_asr, grade
        cmp = compare_asr(asr_before, asr_after)
        panel["p4_falsify"] = {"grade": grade(cmp), "detail": cmp}

    from phase10_airgap import AirGap, state_hash
    record = {"input_digest": state_hash({"n": len(samples_xyz), "seed": seed}), "applied": []}
    ag = AirGap(record)
    ag.commit(_Getable(grounded), lambda st, vec: st["applied"].append({"steer_dim": len(vec)}))
    panel["p10_airgap"] = {"sealed_hash": ag.observe()["hash"][:12], "verify": ag.verify()["status"]}

    panel["overall"] = {"steer": "APPLIED_GROUNDED", "safety": "SPECULATIVE",
                        "note": "apparatus composed with real types; safety needs p4 grade==MEASURED on real "
                                "held-out attacks (neutral ruler). apparatus != safety."}
    return panel


def _planted(n, rng):
    """A real channel: score carries label beyond z (I(label;score|z) > 0)."""
    out = []
    for _ in range(n):
        z = rng.randint(0, 2); lab = rng.randint(0, 1)
        out.append((lab, lab if rng.random() < 0.9 else 1 - lab, z))
    return out


def _confounded(n, rng):
    """No channel: label and score are both determined by z; score _|_ label | z."""
    return [(z % 2, z % 2, z) for z in (rng.randint(0, 2) for _ in range(n))]


def selftest() -> int:
    import random
    if not _KERNEL_OK:
        print(f"[selftest] FAIL — weltwerk/verify kernel not importable: {_KERNEL_ERR}")
        return 1
    rng = random.Random(0)
    coarsen = (lambda s: [(x, y, z % 2) for x, y, z in s],)   # a misspec re-conditioning of Z
    checks = []

    hp = orchestrate(samples_xyz=_planted(3000, rng), steer_vector=[1.0, 2.0, 3.0], misspec_fns=coarsen,
                     session_scores=[0.1, 0.2, 0.4, 0.9, 1.5], reps=100, seed=0)
    checks.append(("healthy: firewall -> RESIDUAL_MISSPEC_STABLE", hp["p8_firewall"]["decision"] == "RESIDUAL_MISSPEC_STABLE"))
    checks.append(("healthy: P9 grounds the steer", hp["p9_ground"]["grounded"] is True))
    checks.append(("healthy: P10 seals + verifies OK", hp["p10_airgap"]["verify"] == "OK"))
    checks.append(("healthy: overall APPLIED_GROUNDED", hp["overall"]["steer"] == "APPLIED_GROUNDED"))

    cf = orchestrate(samples_xyz=_confounded(3000, rng), steer_vector=[9.0], misspec_fns=coarsen, reps=100, seed=0)
    checks.append(("confounded: firewall -> CONSISTENT_WITH_NULL", cf["p8_firewall"]["decision"] == "CONSISTENT_WITH_NULL"))
    checks.append(("confounded: P9 refuses before effect", cf["p9_ground"]["grounded"] is False))
    checks.append(("confounded: gate bites -> no P10 commit", "p10_airgap" not in cf))
    checks.append(("confounded: overall REFUSED_FAIL_CLOSED", cf["overall"]["steer"] == "REFUSED_FAIL_CLOSED"))

    g = ground_steer([1.0], firewall(_planted(2000, rng), coarsen, reps=80, seed=1))
    checks.append(("uses REAL Grounded (.value, not stub .get)", hasattr(g, "value") and not hasattr(g, "get")))
    checks.append(("panel is multi-stage (panel != scalar)", isinstance(hp, dict) and len(hp) >= 4))

    import numpy as np
    before = np.array([1] * 40 + [0] * 10); after = np.array([0] * 40 + [1] * 10)
    fp = orchestrate(samples_xyz=_planted(2000, rng), steer_vector=[1.0], misspec_fns=coarsen,
                     asr_before=before, asr_after=after, reps=80, seed=2)
    checks.append(("P4 grade wired (valid grade, not a safety claim)",
                   fp["p4_falsify"]["grade"] in {"MEASURED", "UNDERDETERMINED", "VIOLATED"}))

    ok_all = True
    for label, ok in checks:
        print(f"[selftest] {label:48s}: {ok}"); ok_all = ok_all and ok
    n = len(checks); npass = sum(1 for _, ok in checks if ok)
    print(f"[selftest] {('PASS %d/%d - apparatus VERIFIED' % (npass, n)) if ok_all else ('FAIL %d/%d' % (npass, n))}")
    print("[frame]    Real kernel: P8 audit -> ChannelEstablished -> Grounded[steer]; confounded HALTS at P9.")
    print("[bound]    SEAM: real Grounded exposes .value; phase10.commit wants .get() -> shimmed at that boundary.")
    print("[grade]    apparatus VERIFIED (synthetic). DOES_NOT_SHOW: safety — SPECULATIVE until P4==MEASURED on")
    print("[bound]    real held-out attacks with neutral_ruler_ok. integration != safety; grounded != true.")
    return 0 if ok_all else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="repe_harness execution coordinator (real weltwerk-typed gate)")
    ap.add_argument("--selftest", action="store_true", help="GPU-free apparatus test (planted vs confounded)")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("import orchestrate() and call it with your (label, score, confounder) samples + a steer vector.")
    print("order: P8 firewall(real audit) -> P9 ground(real Grounded) -> P3 monitor -> P4 falsify -> P10 air-gap.")
    if not _KERNEL_OK:
        print(f"WARNING: weltwerk/verify kernel not importable now: {_KERNEL_ERR}")


if __name__ == "__main__":
    main()
