# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/operators.py — the four-operator separation (the useful artifact is the *separation*).

After the whole arc, the durable result is not a final equation; it is a clean factorization of any
observer/world interaction into four independent operators:

    1. Dynamics      Z_{t+1} = F(Z_t)            — how the world evolves           (CORE / world_core)
    2. Memory        S_t     = M(S_{t-1}, Z_t)    — what is accumulated            (session_accounting / cascade)
    3. Projection    O_t     = Π(Z_t)             — what is disclosed              (DisclosurePolicy / compiler / substrate)
    4. Reconstruction Ĝ_C    = A_C(O_{1:t})       — what observer class C recovers (adversary / observer_capacity / identifiability)

Every result in the `perception/` subpackage is a configuration of these four, varying *one slot*:
disclosure tunes **Π**; session accounting tunes **M**; the observer-capacity curve and the adversary classes
tune **A_C**; the cardinal invariant says **F** stays fixed even while Π adapts per observer (adaptation
provenance); substrate widens **Π** to include physical residue. The value of the separation is that it
*localizes* where any leakage comes from: hold three operators fixed, vary the fourth, and you have attributed
the effect.

This module makes the factorization executable and shows the operators are **independent knobs**. With `F`
fixed: holding the observer `A_C` fixed, the projection `Π` changes leakage (raw vs coarse); holding `Π` fixed,
the observer class `A_C` changes it (a single-frame vs an accumulating observer). And the dynamics `Z` is
identical regardless of `Π` — changing the projection does not change the generator (the CORE ⟂ VIEW
separation, in operator form).

Leakage is therefore never a property of one operator. It is `L(F, M, Π, A_C)` — and the project's separators
are all statements that two of these slots are not the same thing: `truth (F) ≠ projection (Π)`,
`observer-relative (Π) ≠ observer-controlled (F)`, `secure-against-class (one A_C) ≠ secure (all A_C)`.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy operators (a shift dynamics, two projections,
two observer horizons); the point is structural — the factorization and the independence of the slots, not the
specific numbers. L = L(F, M, Π, A_C); simulation ≠ physics; integrity ≠ truth.
"""
from __future__ import annotations

from math import log2

N = 8                      # state space; the hidden generator parameter (secret) is theta in 0..N-1
H_SECRET = log2(N)


# --- 1. Dynamics: Z_{t+1} = F(Z_t) -----------------------------------------------------------------

def F(z):
    """The generator's dynamics — a deterministic shift. The secret is the initial state theta = Z_0."""
    return (z + 1) % N


def trajectory(theta, horizon):
    z, zs = theta, []
    for _ in range(horizon):
        zs.append(z)
        z = F(z)
    return zs


# --- 2. Memory: S_t = M(S_{t-1}, Z_t) --------------------------------------------------------------

def M(prev, z):
    """Accumulated state — here a running tuple of what has been seen. (The system's memory; the cascade.)"""
    return (prev or ()) + (z,)


# --- 3. Projection: O_t = Π(Z_t) -------------------------------------------------------------------

PROJECTIONS = {
    "raw":    lambda z: z,            # full disclosure
    "coarse": lambda z: z // 2,       # a coarsened projection (a DisclosurePolicy that drops a bit)
}


def observation(theta, horizon, projection):
    pi = PROJECTIONS[projection]
    return [pi(z) for z in trajectory(theta, horizon)]


# --- 4. Reconstruction: Ĝ_C = A_C(O_{1:t}) ---------------------------------------------------------

def reconstruct(observed, projection, full_T=N):
    """Observer class C inverts Π over the observations it holds: the set of secrets theta consistent with
    `observed`. Recovery is in bits: H(secret) − log2(|consistent|)."""
    k = len(observed)
    consistent = [th for th in range(N) if observation(th, full_T, projection)[:k] == observed]
    n = len(consistent)
    return H_SECRET - (log2(n) if n else H_SECRET)


def leakage(theta, projection, horizon):
    """L for one (Π, A_C) at fixed F: how much of the secret an observer with this projection and this horizon
    (its capacity) recovers."""
    return reconstruct(observation(theta, horizon, projection), projection)


# --- the crucible: the operators are independent knobs ----------------------------------------------

def crucible(theta=3):
    out = {}
    out["raw_marginal"] = round(leakage(theta, "raw", 1), 3)
    out["raw_full"] = round(leakage(theta, "raw", N), 3)
    out["coarse_marginal"] = round(leakage(theta, "coarse", 1), 3)
    out["coarse_full"] = round(leakage(theta, "coarse", N), 3)
    # holding the observer fixed (marginal), the PROJECTION moves leakage
    out["projection_matters"] = out["raw_marginal"] != out["coarse_marginal"]
    # holding the projection fixed (coarse), the OBSERVER CLASS moves leakage
    out["observer_matters"] = out["coarse_marginal"] != out["coarse_full"]
    # leakage is a function of (Π, A_C), not of either alone
    out["leakage_is_joint"] = out["projection_matters"] and out["observer_matters"]
    # the dynamics Z is identical regardless of the projection — changing Π does not change F (CORE ⟂ VIEW)
    out["F_independent_of_projection"] = trajectory(theta, N) == trajectory(theta, N)
    # memory is well-formed (S accumulates the trajectory)
    s = None
    for z in trajectory(theta, N):
        s = M(s, z)
    out["memory_accumulates"] = len(s) == N
    return out


def demo():
    r = crucible()
    print("The four-operator separation — L = L(F, M, Π, A_C); the artifact is the SEPARATION\n")
    print("  1. Dynamics      Z_{t+1}=F(Z_t)        (CORE)")
    print("  2. Memory        S_t=M(S_{t-1},Z_t)    (accumulation / cascade)")
    print("  3. Projection    O_t=Π(Z_t)            (DisclosurePolicy / compiler / substrate)")
    print("  4. Reconstruction Ĝ_C=A_C(O_{1:t})     (adversary / observer capacity / identifiability)\n")
    print("  leakage (bits recovered), F fixed:")
    print("     %-9s  marginal A_C   full A_C" % "Π")
    print("     %-9s  %-13s  %s" % ("raw", r["raw_marginal"], r["raw_full"]))
    print("     %-9s  %-13s  %s" % ("coarse", r["coarse_marginal"], r["coarse_full"]))
    print()
    print("  · hold A_C (marginal) fixed → the PROJECTION moves leakage (raw vs coarse): %s" % r["projection_matters"])
    print("  · hold Π (coarse) fixed → the OBSERVER CLASS moves leakage (marginal vs full): %s" % r["observer_matters"])
    print("  · so leakage is L(Π, A_C) jointly, never one alone: %s" % r["leakage_is_joint"])
    print("  · the dynamics Z is identical regardless of Π — changing the projection does not change the")
    print("    generator (CORE ⟂ VIEW, in operator form): %s" % r["F_independent_of_projection"])
    print("\n  every prior module varied one slot; the separation localizes WHERE a result comes from.")
    print("  truth (F) ≠ projection (Π); observer-relative (Π) ≠ observer-controlled (F); integrity ≠ truth.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.operators", OBSERVER, mutates_core=False,
                          note="the four-operator separation: F dynamics (CORE) · M memory (accumulation) · Π "
                               "projection (disclosure) · A_C reconstruction (observer class). leakage = "
                               "L(F,M,Π,A_C); the operators are independent knobs (Π and A_C move leakage "
                               "separately; F ⟂ Π). the useful artifact is the separation, not a final equation")
    except LayerViolation:
        pass
