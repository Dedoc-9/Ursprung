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
    print("\nGates 2–4 + GeneratorScore (intervention · robustness · gauge):")
    for f, d in r["factors"].items():
        print("   factor %s: intervention=%.2f  robustness=%.3f  gauge_invariant=%s  →  GeneratorScore=%.3f"
              % (f, d["intervention"], d["robustness"], d["gauge_invariant"], d["GeneratorScore"]))

    g, c = r["factors"]["g"], r["factors"]["c"]
    print("\nVERDICT")
    print("  g is the recovered generator: found across every encoder family, responds to do(g), gauge-invariant.")
    print("  c is the confounder TRAP: it reconstructs, is fully recoverable, and correlates with the outcome —")
    print("  yet GeneratorScore(c)=%.2f, because do(c) does not move the outcome. Caught by the intervention gate." % c["GeneratorScore"])
    print("\n  good reconstruction ≠ recovered generator;  generator = invariant ∧ necessary ∧ model-robust.")

    # --- self-check (the verification; numpy-dependent, hence outside the stdlib suite) ---
    checks = {
        "reconstruction_passes_broadly": min(r["reconstruction"].values()) >= 0.6,
        "c_is_recoverable_the_trap": min(d["c"] for d in r["recoverability"].values()) >= 0.9,
        "intervention_separates_them": g["intervention"] >= 0.9 and c["intervention"] <= 0.1,
        "both_robust_so_robustness_alone_cannot_separate": g["robustness"] >= 0.9 and c["robustness"] >= 0.9,
        "gauge_invariant_recoverability": g["gauge_invariant"] and c["gauge_invariant"],
        "generator_score_separates": g["GeneratorScore"] >= 0.9 and c["GeneratorScore"] <= 0.1,
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Phase 1 discipline result did not hold"
    print("\nall %d checks passed — the confounder was caught by intervention, not by reconstruction." % len(checks))
    return r


if __name__ == "__main__":
    main()
