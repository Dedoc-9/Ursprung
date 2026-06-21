# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/latent_phase5/representation.py — provenance-preserving learning: the latent is a coordinate
system, the provenance-qualified claim is the invariant.

Phase 4 showed the provenance contract survives a learned representation. Phase 5 makes the consequence
explicit: **representation is free, epistemic status is conserved.** A `Representation` is not just a latent —
it carries the developer's declared choices (a *creator manifest*) and a provenance-qualified *claim*, and that
claim — not the latent vector — is its identity.

The objective is deliberately NOT "find the truth." It is: *find representations whose claims remain
inspectable after learning*, and refuse the re-anthropomorphism failure — the developer is a **named component**
of the object, not a hidden author later mistaken for a discovering machine.

Four properties (the Phase-5 tests):
  1. creator visibility    — the manifest traces which declared choices produced the latent (changing a choice
                             changes the manifest's identity).
  2. intervention honesty  — the claim distinguishes intervention-grounded edges from assumption/correlation
                             (reuses the Phase-3 contract; do(c)=0 ⇒ c→y can only be assumption_load_bearing).
  3. assumption locality   — every assumption-load-bearing edge names its assumption (Phase-3 invariant).
  4. representation humility — two encoders with DIFFERENT latents but the SAME provenance-qualified claim are
                             equivalent; a representation that cannot support the claims (degenerate encoder) is
                             not. The claim is the `graph_digest` from Phase 3 — encoder-independent.

And the scale gauge the Phase-4 bug exposed: standardizing the encoder's input *closes* a scale gauge, so the
claim is invariant under per-column rescaling of the observable — magnitude artifacts cannot manufacture
coherence. `created coherence ≠ discovered coherence`; `latent ≠ truth`; the latent is the coordinate system
through which a provenance-bearing claim is expressed, not the discovery itself.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os

import numpy as np

# reuse the Phase-3 contract unchanged (the claim IS its graph_digest)
_p3 = os.path.join(os.path.dirname(__file__), "..", "latent_phase3", "provenance.py")
_spec = importlib.util.spec_from_file_location("phase3_provenance", _p3)
_pv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pv)
CausalEdge, ProvenanceGraph = _pv.CausalEdge, _pv.ProvenanceGraph
IG, AB = _pv.INTERVENTION_GROUNDED, _pv.ASSUMPTION_LOAD_BEARING

N_DEFAULT, D_DEFAULT = 4000, 10
EDGES = (("g", "m"), ("m", "y"), ("c", "y"))   # the structural edges; c→y is the confounder edge


def make_world(n=N_DEFAULT, d=D_DEFAULT, seed=0, scale=None):
    r = np.random.default_rng(seed)
    g = r.standard_normal(n); m = g + 0.3 * r.standard_normal(n); c = 0.6 * g + 0.8 * r.standard_normal(n)
    A = r.standard_normal((d, 3))
    X = np.c_[g, m, c] @ A.T + 0.01 * r.standard_normal((n, d))
    if scale is not None:                       # per-column rescaling = a scale gauge transform of the observable
        X = X * np.asarray(scale)
    return {"X": X, "g": g, "m": m, "c": c, "y": m.copy()}


def encoder(X, k=3, seed=1):
    """A standardized linear encoder, with a seed-dependent rotation so different seeds give different latent
    COORDINATES (same information, different basis). Standardization closes the scale gauge."""
    r = np.random.default_rng(seed)
    mu = X.mean(0); sd = X.std(0) + 1e-8; Xc = (X - mu) / sd
    _u, _s, Vt = np.linalg.svd(Xc, full_matrices=False)
    Z = Xc @ Vt[:k].T
    rot, _ = np.linalg.qr(r.standard_normal((k, k)))
    return Z @ rot.T


def _r2(target, Z):
    Zb = np.c_[Z, np.ones(len(Z))]
    w, *_ = np.linalg.lstsq(Zb, target, rcond=None)
    pred = Zb @ w
    return max(0.0, 1.0 - float(((target - pred) ** 2).sum()) / float(((target - target.mean()) ** 2).sum()))


def recovers_all(world, Z, thresh=0.9):
    return all(_r2(world[f], Z) >= thresh for f in ("g", "m", "c"))


def _do_moves_outcome(node):
    """Ground-truth do() on the known synthetic world: g and m move the outcome; c does not."""
    return 1.0 if node in ("g", "m") else 0.0


class Representation:
    """A learned latent bundled with the developer's declared choices and a provenance-qualified claim."""

    def __init__(self, latent, world, manifest):
        self.latent = latent
        self.manifest = manifest                # the creator, named: a component of the object's identity
        self._world = world

    def manifest_digest(self):
        return hashlib.sha256(json.dumps(self.manifest, sort_keys=True).encode()).hexdigest()[:12]

    def provenance_graph(self):
        """Build the factor-labeled provenance graph through the Phase-3 contract. An edge is
        intervention_grounded only if the developer's declared intervention access includes its source AND a
        real do() moves the outcome; otherwise it is assumption_load_bearing with its assumption declared."""
        access = set(self.manifest["intervention_access"])
        assumption = {"type": self.manifest["assumptions"][0]}
        edges = []
        for (s, d) in EDGES:
            grounded = (s in access) and _do_moves_outcome(s) >= 0.9
            edges.append(CausalEdge(s, d, IG) if grounded else CausalEdge(s, d, AB, assumption))
        return ProvenanceGraph(edges)

    def claim(self):
        """The provenance-qualified claim — the identity of the representation. The latent COORDINATES do not
        appear in it; an incomplete representation cannot make it."""
        if not recovers_all(self._world, self.latent):
            missing = [f for f in ("g", "m", "c") if _r2(self._world[f], self.latent) < 0.9]
            return "INCOMPLETE:" + ",".join(missing)
        return self.provenance_graph().digest({self.manifest["assumptions"][0]})

    def per_dim_identity(self):
        """The latent's per-dimension correlation with g — gauge-ambiguous (changes with the coordinate basis)."""
        return [round(abs(np.corrcoef(self.latent[:, i], self._world["g"])[0, 1]), 2)
                for i in range(self.latent.shape[1])]


def build_representation(world, encoder_family, k=3, seed=1, intervention_access=("g", "m"),
                         assumptions=("invariance",), objective="reconstruction"):
    Z = encoder(world["X"], k=k, seed=seed)
    manifest = {"encoder_family": encoder_family, "objective": objective, "data_seed": world.get("seed", 0),
                "k": k, "intervention_access": list(intervention_access), "assumptions": list(assumptions)}
    return Representation(Z, world, manifest)
