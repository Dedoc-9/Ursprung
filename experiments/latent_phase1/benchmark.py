# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase1/benchmark.py — the harness that can FAIL a latent space for the right reasons.

This is the first artifact, on purpose. The benchmark embodies the epistemology; an autoencoder is just one
candidate explanation fed into it. If the autoencoder came first, reconstruction accuracy would quietly start
acting as truth again — the exact failure the project's discipline exists to prevent.

The harness is **encoder-agnostic**: it takes a world (true factors + outcome + an intervention callback) and a
set of trained latents `{name: Z}` from a model class 𝓕, and scores each candidate FACTOR through four
progressively harder gates. Gate 1 is allowed to pass almost anything; a factor is not "recovered" until it
survives Gates 2–4.

    Gate 1  reconstruction       can the latent reproduce the observable?       catches: underfit latents
    Gate 2  intervention         does the factor's variable change the outcome?  catches: confounders-as-causes
    Gate 3  model-class robust.   does the factor survive a change of encoder?    catches: encoder-specific artifacts
    Gate 4  gauge invariance      does the metric survive latent rotations?       catches: coordinate-system illusions

    GeneratorScore(factor) = intervention_sensitivity · robustness_across_𝓕 · gauge_invariance

The learned analogue of the criterion the project converged on symbolically:
    generator = invariant ∧ necessary ∧ model-robust.

All recoverability is measured with a **gauge-invariant** statistic — the R² of predicting a factor from the
*column space* of the latent — never from a single latent dimension (which is gauge-dependent: it changes when
you rotate the latent). `good reconstruction ≠ recovered generator`; `gauge-dependent ≠ real`.
"""
from __future__ import annotations

import numpy as np


# --- gauge-invariant primitive -----------------------------------------------------------------

def recover_r2(target, Z):
    """R² of predicting `target` from the latent `Z` (with bias). Depends only on Z's column space, so it is
    INVARIANT under any invertible reparameterization of Z (rotation/relabel/rescale) — a gauge-invariant
    measure of *how recoverable* the factor is, not *which dimension* carries it."""
    Zb = np.c_[Z, np.ones(len(Z))]
    w, *_ = np.linalg.lstsq(Zb, target, rcond=None)
    pred = Zb @ w
    ss = float(((target - pred) ** 2).sum())
    tot = float(((target - target.mean()) ** 2).sum())
    return max(0.0, 1.0 - ss / tot)


def reconstruction_r2(X, X_hat):
    return max(0.0, 1.0 - float(((X - X_hat) ** 2).sum()) / float(((X - X.mean(0)) ** 2).sum()))


def _random_rotation(k, seed):
    """A random orthogonal k×k matrix (a gauge transformation of the latent)."""
    a = np.random.default_rng(seed).standard_normal((k, k))
    q, _ = np.linalg.qr(a)
    return q


# --- the four gates ----------------------------------------------------------------------------

def gate1_reconstruction(latents):
    """{name: (Z, X_hat)} → {name: recon R²}. The entry gate: high is necessary, never sufficient."""
    return {n: round(reconstruction_r2_from(Zxh), 3) for n, Zxh in latents.items()}


def reconstruction_r2_from(Zxh):
    Z, X_hat, X = Zxh
    return reconstruction_r2(X, X_hat)


def gate2_intervention(world, factor, intervention_fn):
    """Necessity by intervention: does do(factor) move the OUTCOME? Independent of any latent — a property of
    the world the latent claims to have captured. (correlation with the outcome is NOT enough — the confounder
    has it.)"""
    return round(float(intervention_fn(world, factor)), 3)


def gate3_robustness(latents, target):
    """Does the factor survive a change of encoder? = min over the model class 𝓕 of gauge-invariant
    recoverability. A factor only one encoder finds is an artifact, not a recovered structure."""
    return round(min(recover_r2(target, Z) for (Z, _x, _X) in latents.values()), 3)


def gate4_gauge(Z, target, n_rotations=8):
    """Is the recoverability metric gauge-invariant? Rotate the latent many ways; recover_r2 must not move.
    Returns (invariant?, per_dim_corr_spread) — the spread shows the per-dimension reading IS gauge-dependent,
    which is exactly why we never score on it."""
    base = recover_r2(target, Z)
    k = Z.shape[1]
    rotated = [recover_r2(target, Z @ _random_rotation(k, s).T) for s in range(n_rotations)]
    invariant = all(abs(r - base) < 1e-6 for r in rotated)
    # per-dimension correlation, by contrast, changes under rotation (gauge-dependent)
    def dim_corrs(Zx):
        return [abs(np.corrcoef(Zx[:, i], target)[0, 1]) for i in range(k)]
    spread = round(float(np.std(dim_corrs(Z @ _random_rotation(k, 1).T)) - np.std(dim_corrs(Z))), 4)
    return invariant, spread


# --- the composite ------------------------------------------------------------------------------

def generator_gate(world, factor, latents, intervention_fn, reference_encoder,
                   interv_thresh=0.5, robust_thresh=0.9):
    """The verdict is a GATE, not a scalar. A factor is a *robust causal candidate* only if it passes all three
    gates; the composite number is explicitly SECONDARY and must never be read as a confidence ranking (that is
    the one-dimensional object the rest of the project spent itself dismantling — see ledgers/trajectory).

    HONEST, and load-bearing (the deepest caveat): passing the gate means *causally-relevant ∧ robust ∧
    gauge-invariant* — it does NOT mean "the deepest generator." A mediator on the path `g → x → y` survives the
    intervention gate too: it is causally relevant and may be encoder-robust, yet `x ≠ g`. Telling a root cause
    from a mediator needs the *intervention topology* (do(g) moves x; do(x) does not move g), which a single
    outcome-intervention test does not capture. So this gate yields **generator candidates**, not generators.
    `survives intervention ≠ (root) generator`."""
    interv = gate2_intervention(world, factor, intervention_fn)
    robust = gate3_robustness(latents, world[factor])
    Zref = latents[reference_encoder][0]
    gauge_ok, _spread = gate4_gauge(Zref, world[factor])
    passes = {"intervention_pass": interv >= interv_thresh,
              "robustness_pass": robust >= robust_thresh,
              "gauge_pass": bool(gauge_ok)}
    return {"passes": passes,
            "all_pass": all(passes.values()),               # the PRIMARY verdict (a boolean gate)
            "intervention": interv, "robustness": robust, "gauge_invariant": bool(gauge_ok),
            "composite_secondary": round(interv * robust * (1.0 if gauge_ok else 0.0), 3)}  # secondary, NOT a ranking


def report(world, latents, intervention_fn, factors=("g", "c"), reference_encoder=None):
    """Full Phase-1 report: Gate 1 per encoder, then per-factor Gates 2–4 + GeneratorScore."""
    reference_encoder = reference_encoder or next(iter(latents))
    out = {"reconstruction": gate1_reconstruction({n: (Z, Xh, world["X"]) for n, (Z, Xh) in latents.items()}),
           "recoverability": {}, "factors": {}}
    lat3 = {n: (Z, Xh, world["X"]) for n, (Z, Xh) in latents.items()}
    for n, (Z, _Xh, _X) in lat3.items():
        out["recoverability"][n] = {f: round(recover_r2(world[f], Z), 3) for f in factors}
    for f in factors:
        out["factors"][f] = generator_gate(world, f, lat3, intervention_fn, reference_encoder)
    return out
