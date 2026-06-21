# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase1/run.py — Phase 1: run the benchmark over the model class, print the report, self-check.

    PYTHONHASHSEED=0 python3 experiments/latent_phase1/run.py

This is the first place the project's machinery stops being illustrative and constrains a real learned
representation. The headline it must produce: reconstruction, recoverability, AND correlation-with-outcome all
FAIL to separate the generator g from the confounder c — only the intervention gate does. The asserts at the
end are the verification (they need numpy, so this lives outside the stdlib suite).
"""
from __future__ import annotations

import numpy as np

from world import make_world, intervention_on_outcome
from encoders import model_class
from benchmark import report


def mediator_caveat(n=4000, seed=7):
    """g → x → y: a mediator x is causally relevant to the outcome and survives the intervention gate, yet
    x ≠ g. Returns (do(g)→outcome, do(x)→outcome); both move the outcome, so the gate alone cannot crown the
    root. (The root/mediator distinction lives in the intervention topology: do(g) moves x; do(x) does not move
    g — not captured by a single outcome-intervention test.)"""
    rng = np.random.default_rng(seed)
    g = rng.standard_normal(n)
    x = g + 0.3 * rng.standard_normal(n)        # mediator carries g's effect
    y = x.copy()                                # outcome depends on x (hence on g, through x)
    def do_outcome(factor):
        if factor == "g":                       # do(g): x follows, y follows
            g2 = rng.standard_normal(n); x2 = g2 + 0.3 * rng.standard_normal(n); y2 = x2
        else:                                   # do(x): y follows directly
            x2 = rng.standard_normal(n); y2 = x2
        return float(min(1.0, np.std(y2 - y) / (np.std(y) + 1e-9)))
    return do_outcome("g"), do_outcome("x")


def main():
    world = make_world(seed=0)
    latents = model_class(world["X"])
    r = report(world, latents, intervention_on_outcome, factors=("g", "c"), reference_encoder="E1_pca")

    print("PHASE 1 — latent benchmark (the harness can fail a latent for the right reasons)\n")
    print("Gate 1  reconstruction R² (entry gate — high is necessary, never sufficient):")
    for n, v in r["reconstruction"].items():
        print("   %-14s %.3f" % (n, v))
    print("\ngauge-invariant recoverability R²(factor | Z), per encoder:")
    for n, d in r["recoverability"].items():
        print("   %-14s g=%.3f  c=%.3f" % (n, d["g"], d["c"]))
    print("\nGates 2–4 — the verdict is a GATE (pass/fail), the composite is SECONDARY (never a ranking):")
    for f, d in r["factors"].items():
        p = d["passes"]
        print("   factor %s: intervention_pass=%s robustness_pass=%s gauge_pass=%s  →  all_pass=%s   (composite_secondary=%.3f)"
              % (f, p["intervention_pass"], p["robustness_pass"], p["gauge_pass"], d["all_pass"], d["composite_secondary"]))

    g, c = r["factors"]["g"], r["factors"]["c"]
    print("\nVERDICT")
    print("  g is a robust causal CANDIDATE: recovered across every encoder family, responds to do(g), gauge-invariant.")
    print("  c is the confounder TRAP: it reconstructs, is fully recoverable, gauge-invariant, and correlates with")
    print("  the outcome — yet it FAILS the gate, because do(c) does not move the outcome. Caught by intervention.")

    # --- the deepest caveat (#4): survives intervention ≠ (root) generator ---
    sg, sx = mediator_caveat()
    print("\nMEDIATOR CAVEAT (g → x → y): a mediator x survives the outcome-intervention gate too.")
    print("  do(g) moves the outcome: %.2f ;  do(x) moves the outcome: %.2f  → BOTH pass." % (sg, sx))
    print("  So passing the gate = 'robust causal candidate', NOT 'the deepest generator'.")
    print("  Telling root from mediator needs the intervention TOPOLOGY (do(g) moves x; do(x) does not move g),")
    print("  which a single outcome-intervention test does not capture. survives intervention ≠ root generator.")

    print("\n  good reconstruction ≠ recovered generator;  observation ≠ intervention;  the gate yields candidates.")

    # --- self-check (the verification; numpy-dependent, hence outside the stdlib suite) ---
    checks = {
        "reconstruction_passes_broadly": min(r["reconstruction"].values()) >= 0.6,
        "c_is_recoverable_the_trap": min(d["c"] for d in r["recoverability"].values()) >= 0.9,
        "intervention_separates_them": g["intervention"] >= 0.9 and c["intervention"] <= 0.1,
        "both_robust_so_robustness_alone_cannot_separate": g["robustness"] >= 0.9 and c["robustness"] >= 0.9,
        "gauge_invariant_recoverability": g["gauge_invariant"] and c["gauge_invariant"],
        "gate_separates_candidate_from_confounder": g["all_pass"] is True and c["all_pass"] is False,
        "mediator_also_passes_so_gate_yields_candidates_not_roots": sg >= 0.9 and sx >= 0.9,
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase 1 discipline result did not hold"
    print("\nall %d checks passed — the confounder was caught by intervention, not by reconstruction." % len(checks))
    return r


if __name__ == "__main__":
    main()
