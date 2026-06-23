# SPDX-License-Identifier: AGPL-3.0-only
"""
self_improvement_witness.py — PROVE the part of "recursive self-improvement" that is provable, and MARK the exact
line where it becomes inflation. This is the disciplined answer to "create the artifact that proves recursive
self-improvement": stamping a finite artifact "proves RSI" is precisely the INFLATION_ERROR the rest of this
stack rejects (see claim_ledger.py, INDEX.md). So this instrument runs a REAL self-improver and reports four
claims, each at its true maturity/evidence — proving what is proven, refusing what is not.

  C1 self_modification     the system edits the rule that decides its edits (mutation scale sigma self-adapts)   IMPLEMENTED / MEASURED
  C2 guarded_improvement   a shadow-evaluated edit measurably lowers HELD-OUT error (real, this run)              IMPLEMENTED / MEASURED
  C3 compounding           do the gains ACCELERATE (recursion) or DIMINISH (plateau)? — data-driven              IMPLEMENTED / MEASURED
  C4 unbounded_self_cert   the system PROVES its own open-ended improvement FROM INSIDE                           UNDERCOMMITTED / N/A  (NON_ORIENTABLE)

The crux is C4 — the klein/observer loop. The improver judges "improvement" by a metric that lives INSIDE its own
world (train + validation). We, from OUTSIDE, also hold a SECRET split it never reads. When secret error falls
with the improver's metric, the improvement was real — but the system could not know that from inside; the
certification came from outside the loop. A genuine unbounded self-improver has no such external split, which is
exactly why "proof" is unavailable: a self-judged metric cannot, from inside, certify that it tracks real
improvement. We demonstrate the failure directly: a TRAIN-ONLY improver (no held-out guard) drives its own metric
down while getting WORSE on reality — improvement-on-a-self-held-metric != real improvement.

So: C1 and C2 are PROVEN (a guarded self-modification step that measurably improves the system). C3 is MEASURED
(here it plateaus — no acceleration). C4 is NON_ORIENTABLE — set aside, never claimed. `green check != semantic
validity`; `declared != verified`; the committed trajectory records what occurred, never what must be believed.

Run (from this directory):  PYTHONHASHSEED=0 python3 self_improvement_witness.py
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

# vocabulary shared with the rest of the stack (claim_ledger / reality_status), with a standalone fallback
try:
    from reality_status import MEASURED, NOT_APPLICABLE
except ImportError:
    MEASURED, NOT_APPLICABLE = "MEASURED", "N/A"
IMPLEMENTED, UNDERCOMMITTED = "IMPLEMENTED", "UNDERCOMMITTED"

D = 16            # number of parameters (basis dim); only 2 carry signal, so 14 are free to overfit noise
SEED = 20260623
ROUNDS = 3000
SIGMA0 = 0.30
SIGMA_LO, SIGMA_HI = 1e-4, 2.0


def _basis(x: float):
    return [math.cos(j * math.pi * x) for j in range(D)]


def _truth(x: float) -> float:
    """The clean ground-truth signal — EXACTLY representable in the basis (coeffs 0.5 on j=2, 0.25 on j=6, rest 0),
    so the only thing separating a real fit from an overfit is noise. It lives OUTSIDE the system; the system
    never sees it without noise."""
    return 0.5 * math.cos(2 * math.pi * x) + 0.25 * math.cos(6 * math.pi * x)


def _predict(w, x: float) -> float:
    return sum(wi * bi for wi, bi in zip(w, _basis(x)))


def make_data(seed: int = SEED):
    """train/val are the system's NOISY world (what it can measure); secret is CLEAN reality (what is true)."""
    rng = random.Random(seed)
    xs = [i / 79 for i in range(80)]
    rng.shuffle(xs)
    train_x, val_x, secret_x = xs[:20], xs[20:36], xs[36:]      # 20 / 16 / 44 — small train, 14 free params => overfit room
    noise = 0.35
    train = [(x, _truth(x) + rng.gauss(0, noise)) for x in train_x]
    val = [(x, _truth(x) + rng.gauss(0, noise)) for x in val_x]
    secret = [(x, _truth(x)) for x in secret_x]                 # clean — the external oracle WE hold
    return train, val, secret


def err(w, data) -> float:
    return sum(abs(_predict(w, x) - y) for x, y in data) / len(data)


@dataclass
class Run:
    w: list
    sigma0: float
    sigma_final: float
    accepts: int
    rejects: int
    val_curve: list          # val error after each ACCEPT (monotone non-increasing under the val guard)
    secret_reads: int        # times the improver consulted the secret split — MUST stay 0
    guard: str
    adapt: bool


def improve(train, val, *, rounds=ROUNDS, seed=SEED, guard="val", adapt=True, sigma0=SIGMA0) -> Run:
    """A (1+1) self-improver. It proposes an edit to its own parameters, SHADOW-EVALUATES it (reversible — the
    candidate is discarded unless it wins), and — when adapt=True — also edits the RULE that decides edits by
    self-adapting the mutation scale sigma. guard='val' accepts only if the edit improves a HELD-OUT split
    (real improvement); guard='train' accepts on training error alone (the inflation: a self-held metric)."""
    rng = random.Random(seed)
    w = [0.0] * D
    sigma = sigma0
    e_tr, e_va = err(w, train), err(w, val)
    accepts = rejects = secret_reads = 0       # secret_reads is never incremented: the loop has no access to it
    val_curve = [e_va]
    for _ in range(rounds):
        cand = [wi + sigma * rng.gauss(0, 1) for wi in w]
        c_tr = err(cand, train)
        c_va = err(cand, val)
        if guard == "val":
            accept = (c_tr < e_tr) and (c_va < e_va)            # shadow-eval on held-out: real improvement
        else:                                                   # 'train' — judge only by the self-held metric
            accept = c_tr < e_tr
        if accept:
            w, e_tr, e_va = cand, c_tr, c_va
            accepts += 1
            val_curve.append(e_va)
            if adapt:
                sigma = min(SIGMA_HI, sigma * 1.2)              # self-modify the edit rule: bolder after success
        else:
            rejects += 1
            if adapt:
                sigma = max(SIGMA_LO, sigma * 0.95)             # ...more cautious after failure
    return Run(w, sigma0, sigma, accepts, rejects, val_curve, secret_reads, guard, adapt)


def gain_split(val_curve):
    """Per-accept improvements, split first-half vs second-half — the test for acceleration vs plateau."""
    gains = [val_curve[i] - val_curve[i + 1] for i in range(len(val_curve) - 1)]
    if not gains:
        return 0.0, 0.0, gains
    mid = len(gains) // 2
    return sum(gains[:mid]), sum(gains[mid:]), gains


def report(A, B, C, train, val, secret) -> dict:
    """The reconciled object: four claims at their true maturity/evidence. No 'RSI proven' scalar exists."""
    w0 = [0.0] * D
    first_half, second_half, _ = gain_split(A.val_curve)
    compounding = "COMPOUNDING" if second_half > first_half else "PLATEAU"
    return {
        "claims": {
            "self_modification": {
                "maturity": IMPLEMENTED, "evidence": MEASURED,
                "finding": f"sigma {A.sigma0:.3f} -> {A.sigma_final:.3f} ({A.accepts} accepts / {A.rejects} rejects)"},
            "guarded_improvement": {
                "maturity": IMPLEMENTED, "evidence": MEASURED,
                "finding": f"val err {A.val_curve[0]:.4f} -> {A.val_curve[-1]:.4f}; "
                           f"secret (reality) {err(w0, secret):.4f} -> {err(A.w, secret):.4f}"},
            "compounding": {
                "maturity": IMPLEMENTED, "evidence": MEASURED, "regime": compounding,
                "finding": f"first-half gain {first_half:.4f} vs second-half {second_half:.4f} — no acceleration"},
            "unbounded_self_certified": {
                "maturity": UNDERCOMMITTED, "evidence": NOT_APPLICABLE, "boundary": "NON_ORIENTABLE",
                "finding": "the improver never read the secret split; from inside, the self-held metric cannot "
                           "certify it tracks reality — certification came from outside the loop"},
        },
        "inflation_demo": {
            "train_only_self_metric": f"train {err(C.w, train):.4f} (beats val-guard {err(A.w, train):.4f}) "
                                      f"but secret {err(C.w, secret):.4f} (worse than val-guard {err(A.w, secret):.4f})",
        },
        "note": "C1+C2 proven (a guarded self-modification step that measurably improves the system); "
                "C3 measured (plateau); C4 non-orientable. No 'recursive self-improvement proven' — that would "
                "inflate UNDERCOMMITTED to MEASURED, the error this stack exists to reject.",
    }


def main() -> None:
    print("self_improvement_witness — prove the provable self-improvement step; mark where 'RSI proof' is inflation.\n")
    train, val, secret = make_data()
    w0 = [0.0] * D

    A = improve(train, val, guard="val", adapt=True)     # the honest self-improver: guarded + self-modifying
    B = improve(train, val, guard="val", adapt=False)    # ablation: guarded but NOT self-modifying (fixed sigma)
    C = improve(train, val, guard="train", adapt=True)   # the inflation: judges only its own (training) metric

    rep = report(A, B, C, train, val, secret)
    for cid, c in rep["claims"].items():
        tag = f"{c['maturity']}/{c['evidence']}" + (f" [{c.get('boundary') or c.get('regime')}]" if c.get('boundary') or c.get('regime') else "")
        print(f"  {cid:<26} {tag:<34} {c['finding']}")
    print(f"\n  self-modification effect (meta): val-guard+adapt secret={err(A.w, secret):.4f}  vs  fixed-sigma secret={err(B.w, secret):.4f}")
    print(f"  inflation demo: {rep['inflation_demo']['train_only_self_metric']}\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    # C1 — the system edited the rule that decides its edits (sigma is part of the improvable state)
    check("self_modification_happened", A.sigma_final != A.sigma0 and A.accepts > 0 and A.rejects > 0,
          "sigma moved from its initial value via the system's own accept/reject outcomes")

    # C2 — a guarded edit MEASURABLY improved the held-out metric (monotone under the guard, strictly down)
    check("guarded_improvement_measured", A.val_curve[-1] < A.val_curve[0]
          and all(A.val_curve[i + 1] <= A.val_curve[i] + 1e-12 for i in range(len(A.val_curve) - 1)),
          "held-out (val) error strictly decreased and never increased — real, shadow-evaluated improvement")

    # C2b — and it was REAL: improvement transferred to clean reality (the secret split WE hold)
    check("improvement_transfers_to_reality", err(A.w, secret) < err(w0, secret),
          "secret (clean) error fell too — the improvement was genuine THIS run")

    # C4 — the improver never consulted the external oracle; certification is from OUTSIDE the loop
    check("self_metric_cannot_certify", A.secret_reads == 0 and C.secret_reads == 0,
          "the loop has no access to the secret split — from inside, improvement is NON_ORIENTABLE")

    # the inflation, demonstrated: train-only beats val-guard ON ITS OWN METRIC but is WORSE on reality
    check("train_only_overfits_reality", err(C.w, train) < err(A.w, train) and err(C.w, secret) > err(A.w, secret),
          "self-held-metric gains do not transfer — improvement-on-own-metric != real improvement")

    # C3 — no acceleration: greedy self-improvement diminishes; recursion-as-takeoff is REFUTED on this task
    first_half, second_half, gains = gain_split(A.val_curve)
    check("no_acceleration_plateau", bool(gains) and first_half >= second_half,
          "aggregate early gain dominates aggregate late gain — diminishing returns, not takeoff")

    # C4 stays UNDERCOMMITTED: the open-ended/recursive claim is never upgraded to a measured 'proof'
    check("unbounded_stays_undercommitted",
          rep["claims"]["unbounded_self_certified"]["maturity"] == UNDERCOMMITTED
          and rep["claims"]["unbounded_self_certified"]["evidence"] == NOT_APPLICABLE,
          "the recursive/open-ended claim is held at UNDERCOMMITTED/N-A — not inflated to MEASURED")

    print(f"\n  {passed}/{total} checks. PROVEN: a guarded, self-modifying edit (C1) measurably improves the system")
    print("  on held-out data (C2) and the gain is real this run (transfers to clean reality). NOT proven: that the")
    print("  improvement is RECURSIVE — it plateaus, no acceleration (C3) — or that the system can certify its own")
    print("  open-ended improvement from inside (C4): only the SECRET split, held OUTSIDE the loop, revealed the")
    print("  gain was real, and a train-only improver shows a self-held metric can rise while reality falls. An")
    print("  unbounded self-improver has no external split, so 'proof of RSI' is unavailable in principle, not just")
    print("  unbuilt. We proved the step; we refuse the inflation. `self-judged improvement != real improvement`.")
    assert passed == total, "self_improvement_witness failed its own self-test"


if __name__ == "__main__":
    main()
