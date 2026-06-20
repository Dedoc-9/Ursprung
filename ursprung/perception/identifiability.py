# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/identifiability.py — agency verification: is there a stable generator to recover at all?

Every prior layer assumed *operational self-determinism*: given enough observations, a capable observer can
recover the generating process — `(A,O) ⇒ G ⇒ future`. The adversary wins by reconstruction. But that assumes
the system *is* a stable generator. If `G_t ≠ G_{t+1}` — no persistent policy — then the latent variable the
observer is trying to infer **does not exist as a fixed object**. Leakage is not *bounded*; it is *undefined*,
because the assumed secret is the wrong type.

So the adversary moves up a level. The old adversary asked *"can I recover the agent?"*; the new one asks
*"is there an agent to recover?"* — it attacks **coherence**, not secrecy. This module measures
**identifiability**: how many stable generators (from the observer's hypothesis class) are consistent with the
observed behaviour. Three regimes:

  1. **identifiable**     — exactly one stable generator fits   (`A → G`; high intent leakage)
  2. **ambiguous**        — several fit                          (`A → {G₁,G₂,…}`; the §intent ambiguity defense)
  3. **non-identifiable** — none fit                            (`A ↛ G`; no stable policy explains the behaviour)

Regime 3 looks like the ultimate privacy move — *just don't have a fixed policy* — and it is the limit of a
meta-policy `G* = argmax(usefulness − predictability)`, an *anti-policy* that maintains irreducible ambiguity.
But it springs the identity trap: a non-identifiable trajectory is equally consistent with **adaptation,
learning, stochasticity, conflict, brokenness, or deception** — the observer detects "no stable generator" but
*cannot tell which*. And — the load-bearing honesty — "non-identifiable" is only ever **relative to the
observer's generator class** (M21 again): a richer class may identify what a poorer one cannot.

Hence the new separators: `privacy ≠ unpredictability`, `adaptation ≠ inconsistency`, `learning ≠ drift`,
`non-identifiability ≠ freedom`. The hardest benchmark is no longer "recover the secret" but: *given behaviour
alone, can an observer distinguish a coherent adaptive agent from a system that merely produces acceptable
trajectories?* — and the answer here is **no**, which is the point.

And the noise floor: if even the policy is gone and the only invariant is the noise process `N_t → A_t`, intent
leakage becomes **entropy leakage** `I(N;A,O)` — the observer recovers the *stochastic character* (the generator
class), not a goal. "Become noise" is therefore not perfect privacy: only true maximum-entropy noise hides its
character; a biased or periodic generator leaks which one it is. So **noise ≠ ignorance** and
**unpredictability ≠ agency** — and the only generator with no recoverable structure (uniform) is also the one
with no purpose. The secret relocates from goal to stochastic character; it is not eliminated.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy candidate-generator class; identifiability is
class-relative by construction; the real object is sequential agency verification under rich policy spaces,
open. opacity ≠ privacy; unpredictability ≠ intelligence/agency; non-identifiability ≠ freedom; noise ≠
ignorance; simulation ≠ physics.
"""
from __future__ import annotations

from math import log2

try:
    from ..channel_discovery import mutual_information
except Exception:                                            # pragma: no cover - standalone fallback
    from collections import Counter as _Counter

    def mutual_information(pairs):
        n = len(pairs)
        if n == 0:
            return 0.0
        px = _Counter(x for x, _ in pairs)
        py = _Counter(y for _, y in pairs)
        pxy = _Counter(pairs)
        m = 0.0
        for (x, y), c in pxy.items():
            j = c / n
            m += j * log2(j / ((px[x] / n) * (py[y] / n)))
        return max(0.0, m)


CONTEXTS = (0, 1, 2, 3)
ACTIONS = ("advance", "hold", "retreat")

# the observer's hypothesis class: the stable generators it can recognize (context → action policies)
CANDIDATES = {
    "G1": ("advance", "advance", "hold", "hold"),
    "G2": ("advance", "hold", "hold", "retreat"),
    "G3": ("hold", "hold", "retreat", "retreat"),
}


def consistent_generators(observed, candidates=None):
    """The stable generators (from the class) consistent with every observed (context, action) pair."""
    candidates = candidates if candidates is not None else CANDIDATES
    return [g for g, pol in candidates.items() if all(pol[c] == a for c, a in observed)]


def regime(observed, candidates=None):
    """identifiable (exactly one fits) · ambiguous (several) · non-identifiable (none)."""
    n = len(consistent_generators(observed, candidates))
    if n == 0:
        return "non-identifiable"
    if n == 1:
        return "identifiable"
    return "ambiguous"


# --- example behaviours ----------------------------------------------------------------------------

# a coherent agent that follows G1 everywhere → exactly G1 fits
COHERENT = [(c, CANDIDATES["G1"][c]) for c in CONTEXTS]

# observed only where G1 and G2 agree (contexts 0 and 2) → both fit → ambiguous
AMBIGUOUS_OBS = [(0, "advance"), (2, "hold")]

# an agent whose rule is OUTSIDE the class (a context-parity rule) → no stable candidate fits
def _adaptive_beyond_class(c):
    return "retreat" if (c % 2 == 0) else "advance"
ADAPTIVE_BEYOND = [(c, _adaptive_beyond_class(c)) for c in CONTEXTS]

# a (deterministic) "random/incoherent" sequence → also no stable candidate fits
RANDOM_LIKE = [(0, "retreat"), (1, "retreat"), (2, "advance"), (3, "hold")]


def usefulness_minus_predictability(observed):
    """The anti-policy's objective proxy: stay acceptable (some actions are useful) while minimizing how many
    generators you confirm. Lower consistent-count = less predictable. Returned as (utility_ok, predictability)."""
    fits = len(consistent_generators(observed))
    predictability = fits                       # how pinned-down the agent is (fewer fits = more anti-policy)
    utility_ok = any(a != "hold" for _, a in observed)   # toy: it still does *something*
    return utility_ok, predictability


# --- the noise floor: if the only invariant is N_t, the secret RELOCATES to the stochastic character ----

# If `G_t ≠ G_{t+1}` and the one invariant is the noise process `N_t → A_t`, intent leakage becomes ENTROPY
# leakage `I(N ; A,O)`: the observer no longer extracts a goal, it extracts the *kind of randomness*. But
# "become noise" is not perfect privacy — only true maximum-entropy noise hides its character; a biased or
# structured generator leaks which generator it is. noise ≠ ignorance; even noise has recoverable structure.
NOISE_GENERATORS = {
    "uniform":  ("A", "B", "C", "A", "B", "C"),       # balanced — maximal entropy, no exploitable structure...
    "biased":   ("A", "A", "A", "A", "B", "C"),       # skewed — the bias is the signature
    "periodic": ("A", "B", "A", "B", "A", "B"),       # structured — the period is the signature
}


def _character(seq):
    """The stochastic CHARACTER an observer recovers — the action-frequency profile, not the order."""
    return tuple(sorted(seq))


def noise_character_leakage():
    """`I(N ; behaviour)`: how recoverable the *generator class* is from behaviour, when the secret is the
    noise process rather than a goal."""
    return mutual_information([(k, _character(s)) for k, s in NOISE_GENERATORS.items()])


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    out["coherent_regime"] = regime(COHERENT)
    out["ambiguous_regime"] = regime(AMBIGUOUS_OBS)
    out["adaptive_beyond_regime"] = regime(ADAPTIVE_BEYOND)
    out["random_regime"] = regime(RANDOM_LIKE)
    # the three regimes are exhibited
    out["identifiable_exists"] = out["coherent_regime"] == "identifiable"
    out["ambiguous_exists"] = out["ambiguous_regime"] == "ambiguous"
    out["non_identifiable_exists"] = out["adaptive_beyond_regime"] == "non-identifiable"
    # the identity trap: a coherent-but-beyond-class agent and a random sequence get the SAME verdict
    out["coherent_adaptive_indistinguishable_from_generatorless"] = (
        out["adaptive_beyond_regime"] == out["random_regime"] == "non-identifiable")
    # but "non-identifiable" is RELATIVE to the observer's class: enrich the class → it becomes identifiable
    richer = dict(CANDIDATES)
    richer["G_parity"] = tuple(_adaptive_beyond_class(c) for c in CONTEXTS)
    out["non_identifiability_is_class_relative"] = regime(ADAPTIVE_BEYOND, richer) == "identifiable"
    # the anti-policy stays acceptable while minimizing predictability (usefulness − predictability)
    util_ok, pred = usefulness_minus_predictability(ADAPTIVE_BEYOND)
    out["antipolicy_useful"] = util_ok
    out["antipolicy_unpredictable"] = pred == 0          # zero generators confirmed
    # the noise floor: "becoming noise" relocates the secret to the stochastic character — it does not remove it
    out["noise_character_leakage"] = round(noise_character_leakage(), 3)
    out["noise_character_recoverable"] = noise_character_leakage() > 0    # even noise leaks which generator it is
    out["secret_relocated_not_eliminated"] = out["noise_character_recoverable"]
    return out


def demo():
    r = crucible()
    print("Agency verification — is there a stable generator to recover at all? (identity under observation)\n")
    print("  the observer asks not 'which goal?' but 'is there a coherent self here?' — three regimes:\n")
    print("    coherent (follows G1)         → %s" % r["coherent_regime"])
    print("    observed only where G1≡G2     → %s" % r["ambiguous_regime"])
    print("    rule outside the class        → %s" % r["adaptive_beyond_regime"])
    print("    random / incoherent sequence  → %s" % r["random_regime"])
    print()
    print("  · the identity trap: a coherent agent whose rule is beyond the class and a generatorless random")
    print("    sequence get the SAME verdict ('non-identifiable'): %s — opacity ≠ privacy, unpredictability ≠ intelligence."
          % r["coherent_adaptive_indistinguishable_from_generatorless"])
    print("  · but 'non-identifiable' is RELATIVE to the observer's generator class: enrich the class and the")
    print("    same behaviour becomes identifiable: %s (M21 again — non-identifiability ≠ freedom)."
          % r["non_identifiability_is_class_relative"])
    print("  · the anti-policy G* = argmax(usefulness − predictability) stays useful (%s) while confirming zero"
          % r["antipolicy_useful"])
    print("    generators (%s) — the limit case, where the hidden object is the *absence* of a stable object."
          % r["antipolicy_unpredictable"])
    print("  · the noise floor: even if the only invariant is the noise process, the observer recovers its")
    print("    CHARACTER (I(N;behaviour)=%.3f > 0) — 'become noise' relocates the secret to the stochastic"
          % r["noise_character_leakage"])
    print("    character, it does not remove it. noise ≠ ignorance; unpredictability ≠ agency.")
    print("\n  the hardest boundary: given behaviour alone, a coherent adaptive agent and a mere trajectory-")
    print("  producer are indistinguishable. privacy ≠ unpredictability; learning ≠ drift; non-identifiability ≠ freedom.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.identifiability", OBSERVER, mutates_core=False,
                          note="agency verification: is there a stable generator to recover? three regimes "
                               "(identifiable / ambiguous / non-identifiable). a non-identifiable trajectory is "
                               "equally consistent with adaptation/learning/noise/deception/brokenness — and "
                               "non-identifiability is class-relative (M21). opacity ≠ privacy; non-identifiability ≠ freedom")
    except LayerViolation:
        pass
