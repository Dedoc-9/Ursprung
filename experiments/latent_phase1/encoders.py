# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase1/encoders.py — the model class 𝓕 = {E1, E2, E3}, candidates fed to the benchmark.

These are the latent analogue of the symbolic models in perception/model_relativity (F1, F2, F3). They are
*candidates*, not authorities — the benchmark decides whether what they recover is a generator or an artifact.
Three different families on purpose, so model-class robustness (Gate 3) and gauge invariance (Gate 4) are real
tests and not a single encoder admiring itself. Each is seeded → reproducible.

    E1  PCA (linear AE optimum, closed-form via SVD)
    E2  linear autoencoder trained by gradient descent (recovers the same subspace in a DIFFERENT basis → gauge)
    E3  nonlinear (tanh) MLP autoencoder trained by gradient descent

Each returns (Z, X_hat): the latent and the reconstruction.
"""
from __future__ import annotations

import numpy as np


def e1_pca(X, k=2):
    """PCA — the optimal linear autoencoder, closed form."""
    mean = X.mean(0)
    Xc = X - mean
    _u, _s, Vt = np.linalg.svd(Xc, full_matrices=False)
    V = Vt[:k]
    Z = Xc @ V.T
    return Z, Z @ V + mean


def e2_linear_ae(X, k=2, steps=8000, lr=0.05, seed=1):
    """Linear AE by gradient descent — converges to the PCA subspace but in its own basis (a gauge difference)."""
    rng = np.random.default_rng(seed)
    mean = X.mean(0)
    Xc = X - mean
    d = X.shape[1]
    We = rng.standard_normal((d, k)) * 0.1
    Wd = rng.standard_normal((k, d)) * 0.1
    for _ in range(steps):
        Z = Xc @ We
        X_hat = Z @ Wd
        grad = (X_hat - Xc) * 2.0 / len(X)
        gWd = Z.T @ grad
        gWe = Xc.T @ (grad @ Wd.T)
        We -= lr * gWe
        Wd -= lr * gWd
    Z = Xc @ We
    return Z, Z @ Wd + mean


def e3_mlp_ae(X, k=2, h=16, steps=9000, lr=0.02, seed=2):
    """Nonlinear (tanh) MLP autoencoder by gradient descent — a genuinely different family."""
    rng = np.random.default_rng(seed)
    mean = X.mean(0)
    Xc = X - mean
    d = X.shape[1]
    W1 = rng.standard_normal((d, h)) * 0.1
    W2 = rng.standard_normal((h, k)) * 0.1
    W3 = rng.standard_normal((k, h)) * 0.1
    W4 = rng.standard_normal((h, d)) * 0.1
    for _ in range(steps):
        H1 = np.tanh(Xc @ W1)
        Z = H1 @ W2
        H2 = np.tanh(Z @ W3)
        X_hat = H2 @ W4
        dXh = (X_hat - Xc) * 2.0 / len(X)
        dW4 = H2.T @ dXh
        dH2 = (dXh @ W4.T) * (1 - H2 ** 2)
        dW3 = Z.T @ dH2
        dZ = dH2 @ W3.T
        dW2 = H1.T @ dZ
        dH1 = (dZ @ W2.T) * (1 - H1 ** 2)
        dW1 = Xc.T @ dH1
        W1 -= lr * dW1; W2 -= lr * dW2; W3 -= lr * dW3; W4 -= lr * dW4
    H1 = np.tanh(Xc @ W1)
    Z = H1 @ W2
    return Z, np.tanh(Z @ W3) @ W4 + mean


def model_class(X):
    """𝓕 = {E1, E2, E3} — the admissible class of latent explanations for this observable."""
    return {"E1_pca": e1_pca(X), "E2_linear_ae": e2_linear_ae(X), "E3_mlp_ae": e3_mlp_ae(X)}
