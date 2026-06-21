# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase4/encoder.py — the learned representation families (the thing under test).

These replace the hand-written latent factors with LEARNED latent coordinates. Three families so robustness
(Tier 3) is a real test and not one encoder admiring itself. Seeded → reproducible. The latent is *learned*;
the discipline objects it feeds must remain unchanged — that is the whole experiment.
"""
from __future__ import annotations

import numpy as np


def ae_pca(X, k=3):
    """Linear AE optimum (PCA, closed form)."""
    m = X.mean(0)
    _u, _s, Vt = np.linalg.svd(X - m, full_matrices=False)
    V = Vt[:k]
    Z = (X - m) @ V.T
    return Z, Z @ V + m


def ae_linear(X, k=3, steps=12000, lr=0.01, seed=1):
    """Linear AE by gradient descent — same subspace, different basis (gauge). X is standardized per-dim so
    the GD is well-conditioned on correlated factors (else it diverges)."""
    rng = np.random.default_rng(seed)
    mu = X.mean(0); sd = X.std(0) + 1e-8; Xc = (X - mu) / sd
    d = X.shape[1]
    We = rng.standard_normal((d, k)) * 0.1; Wd = rng.standard_normal((k, d)) * 0.1
    for _ in range(steps):
        Z = Xc @ We; grad = (Z @ Wd - Xc) * 2.0 / len(X)
        We -= lr * (Xc.T @ (grad @ Wd.T)); Wd -= lr * (Z.T @ grad)
    Z = Xc @ We
    return Z, (Z @ Wd) * sd + mu


def ae_mlp(X, k=3, h=24, steps=12000, lr=0.01, seed=2):
    """Nonlinear (tanh) MLP autoencoder — a genuinely different family. X standardized per-dim for stable GD."""
    rng = np.random.default_rng(seed)
    mu = X.mean(0); sd = X.std(0) + 1e-8; Xc = (X - mu) / sd
    d = X.shape[1]
    W1 = rng.standard_normal((d, h)) * 0.1; W2 = rng.standard_normal((h, k)) * 0.1
    W3 = rng.standard_normal((k, h)) * 0.1; W4 = rng.standard_normal((h, d)) * 0.1
    for _ in range(steps):
        H1 = np.tanh(Xc @ W1); Z = H1 @ W2; H2 = np.tanh(Z @ W3); Xh = H2 @ W4
        d_ = (Xh - Xc) * 2.0 / len(X)
        dW4 = H2.T @ d_; dH2 = (d_ @ W4.T) * (1 - H2 ** 2)
        dW3 = Z.T @ dH2; dZ = dH2 @ W3.T
        dW2 = H1.T @ dZ; dH1 = (dZ @ W2.T) * (1 - H1 ** 2); dW1 = Xc.T @ dH1
        W1 -= lr * dW1; W2 -= lr * dW2; W3 -= lr * dW3; W4 -= lr * dW4
    H1 = np.tanh(Xc @ W1); Z = H1 @ W2
    return Z, (np.tanh(Z @ W3) @ W4) * sd + mu


def families(X):
    """The encoder model class — the latent analogue of the symbolic 𝓕."""
    return {"AE_pca": ae_pca(X), "AE_linear": ae_linear(X), "AE_mlp": ae_mlp(X)}
