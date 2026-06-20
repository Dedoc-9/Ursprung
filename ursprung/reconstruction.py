# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/reconstruction.py — Information Reconstruction Debt + the Causal Composition Firewall.

The deepest attack surface after M11: a cheat does not need the forbidden fact — it needs enough *allowed*
fragments to RECONSTRUCT it. No single signal reveals the enemy, but shadow + sound + particle + animation
together can. Each fragment passes the access-control firewall (M11) individually; the leak is in the
**composition**. This is the secure-computing chain the architecture has reached:

    integrity ≠ confidentiality ≠ authorization ≠ harmlessness

So the question is no longer "is this dependency allowed?" but **"does this SET of allowed dependencies
together reconstruct forbidden knowledge?"** Two quantities:

    Reconstruction Score          how much of a hidden fact a fragment SET reconstructs (toward fact_bits).
    Information Reconstruction Debt the reconstruction beyond the safe threshold — what a naive (per-fragment)
                                  firewall would leak. The Causal Composition Firewall caps it.

The firewall admits fragments only while the SET stays below the reconstruction threshold for any hidden
fact; the marginal fragment that would cross it is blocked even though it is individually authorized.

CLASSIFICATION: OBSERVER (mutates_core=False). It measures joint reconstruction and caps composition; it
commits no state and asserts no truth. integrity ≠ truth; authorized ≠ harmless.

HONEST BOUND: fragment "bits" are a declared information-leak proxy (not a measured mutual-information model);
the result is the *shape* (allowed fragments compose into a leak; cap the set, not the piece), not the
constants.
"""
from __future__ import annotations


def reconstruction_score(fragments, fact_bits):
    """Fraction of a hidden fact (needing `fact_bits` to localize) reconstructed by a fragment SET. Fragments
    each contribute partial bits; the combined fraction saturates at 1.0 (fully reconstructed = full leak)."""
    total = sum(max(0, int(f.get("bits", 0))) for f in fragments)
    return min(1.0, total / max(1, fact_bits))


def information_reconstruction_debt(fragments, fact_bits, threshold):
    """How far the allowed fragments reconstruct the forbidden fact BEYOND the safe threshold. > 0 means the
    composition leaks (what a per-fragment firewall would miss)."""
    return max(0.0, reconstruction_score(fragments, fact_bits) - threshold)


def composition_firewall(fragments, fact_bits, threshold):
    """Admit fragments (each individually authorized) only while the SET stays below the reconstruction
    threshold; block the marginal fragment that would cross it and everything after. Returns
    (admitted, blocked). The admitted set provably reconstructs < threshold of any hidden fact."""
    limit = threshold * fact_bits
    admitted, blocked, used = [], [], 0
    for f in fragments:
        b = max(0, int(f.get("bits", 0)))
        if used + b <= limit:
            admitted.append(f); used += b
        else:
            blocked.append(f)
    return admitted, blocked


# --- the composition-leak crucible ------------------------------------------------------------------

def _fragments():
    """Four individually-authorized observation fragments about a hidden enemy. None alone reconstructs it;
    together they do."""
    return [
        {"name": "shadow", "bits": 20},
        {"name": "sound", "bits": 20},
        {"name": "particle", "bits": 30},
        {"name": "animation", "bits": 15},
    ]


def crucible(fact_bits=64, threshold=0.5):
    frags = _fragments()
    each_allowed = all(f["bits"] < threshold * fact_bits for f in frags)   # individually below threshold
    naive = reconstruction_score(frags, fact_bits)                          # per-fragment firewall: all pass
    admitted, blocked = composition_firewall(frags, fact_bits, threshold)
    capped = reconstruction_score(admitted, fact_bits)
    return {
        "each_individually_allowed": each_allowed,
        "naive_reconstruction": naive,                  # what the obvious (per-fragment) firewall leaks
        "debt_without_firewall": information_reconstruction_debt(frags, fact_bits, threshold),
        "composition_firewall_reconstruction": capped,  # capped below threshold
        "admitted": [f["name"] for f in admitted],
        "blocked": [f["name"] for f in blocked],
    }


def demo(fact_bits=64, threshold=0.5):
    r = crucible(fact_bits, threshold)
    print("Causal Composition Firewall — allowed fragments must not jointly reconstruct forbidden knowledge\n")
    print("  each fragment individually allowed: %s" % r["each_individually_allowed"])
    print("  reconstruction without composition firewall: %.2f  (debt beyond %.0f%% threshold: %.2f) → LEAK"
          % (r["naive_reconstruction"], threshold * 100, r["debt_without_firewall"]))
    print("  reconstruction WITH composition firewall:    %.2f  (admitted %s; blocked %s)"
          % (r["composition_firewall_reconstruction"], r["admitted"], r["blocked"]))
    print("\n  a cheat needs only enough allowed fragments to reconstruct the fact; cap the SET, not the piece.")
    print("  integrity ≠ confidentiality ≠ authorization ≠ harmlessness. integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("reconstruction", OBSERVER, mutates_core=False,
                          note="Causal Composition Firewall — caps Information Reconstruction Debt so a SET of "
                               "individually-authorized fragments cannot jointly reconstruct forbidden knowledge")
    except LayerViolation:
        pass
