# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/causal_access.py — the Causal Access Control Layer (the information firewall / anti-cheat floor).

The integrity layer asks "is this claim unforged and agreed?"; this layer asks the harder, anti-cheat
question: **"does this observer have the right causal relationship to USE this knowledge?"** It is not a
truth check (impossible from the renderer side) — it is an *authorization* check.

    cheat / exploit surface        Ursprung analogue                 caught by
    ----------------------------------------------------------------------------------------
    fake information               forged dependency claim           integrity tautology (M10)
    spoofed state                  false dependency access           evidence weighting (M10)
    timing exploit                 stale dependency stream           temporal decay (M10)
    wallhack / hidden knowledge    out-of-scope causal access        THIS layer (authorization)
    prediction injection          reality_forecast / authority leak  prophecy + capability guard
    desync                         CORE vs representation divergence  cardinal invariant (M1)

The decisive point: a fabricated claim can pass the content-hash **tautology** (it is structurally unforged)
AND a colluding **consensus** (ten bad witnesses agree) — and must STILL be rejected, because the observer
lacks the authorized causal relationship to that knowledge. Integrity and consensus are necessary, not
sufficient; **authorization is the floor.** A claim may influence an observer's representation only if it is
(1) unforged, (2) within the observer's authorized causal scope, and (3) permitted by a capability token for
a bounded purpose. Legitimate readiness (a door I can see/affect) passes; forbidden advantage (a hidden
enemy's position) is blocked even when the data is real and agreed.

    CORE owns reality. Dependencies expose possibility. Capabilities constrain interpretation.
    Representation consumes permissioned uncertainty.

CLASSIFICATION: OBSERVER (mutates_core=False). It authorizes whether knowledge may influence representation;
it commits no state and asserts no truth. integrity ≠ truth; authorized ≠ true.
"""
from __future__ import annotations

from . import capability as cap
from . import dependency_integrity as di


class Observer:
    """A client/viewpoint with an AUTHORIZED CAUSAL SCOPE — the set of objects it may legitimately know about
    (what is visible / audible / owned / reachable) — and a capability token bounding how it may use that
    knowledge."""
    __slots__ = ("id", "authorized_scope", "token")

    def __init__(self, id, authorized_scope, token=None):
        self.id = id
        self.authorized_scope = set(authorized_scope)
        self.token = token or cap.issue("prepare_representation", subject="*", scope="visual_only", horizon=200)


def admissible_for_representation(claim, observer, stored_hash=None, horizon_needed=0):
    """May this claim influence `observer`'s representation? Three gates, in order:
       1. INTEGRITY  — unforged (content-hash tautology), if a stored hash is supplied.
       2. AUTHORIZATION — the claim's subject is within the observer's authorized causal scope (else wallhack/ESP).
       3. CAPABILITY — a token permits this use for its bounded purpose within the horizon.
    Returns (admitted, reason)."""
    if stored_hash is not None and not di.tautology_holds(claim, stored_hash):
        return (False, "forged: integrity tautology failed")
    if claim.source not in observer.authorized_scope:
        return (False, "forbidden_advantage: out-of-scope knowledge (ESP / wallhack / outcome-leak)")
    try:
        cap.use(observer.token, "prepare_representation", observer.token.scope, horizon_needed)
    except cap.CapabilityViolation as e:
        return (False, "capability denied: %s" % e)
    return (True, "legitimate_readiness")


def classify_access(claim, observer, stored_hash=None):
    ok, reason = admissible_for_representation(claim, observer, stored_hash)
    if ok:
        return "legitimate_readiness"
    return "forbidden_advantage" if reason.startswith("forbidden_advantage") else "rejected"


# --- the Dependency Fog Attack (forged + consensus-backed, but out of scope) ------------------------

def fog_attack(seed=1):
    """Client A holds a valid causal dependency (a door it can see). Client B fabricates a claim about a
    HIDDEN enemy with a perfectly valid hash structure AND a colluding consensus. The firewall must admit A
    and reject B — advantage leaked must be 0 despite B passing integrity and consensus."""
    observer = Observer("clientA", authorized_scope={"door", "wall", "floor"})

    legit = di.DependencyClaim("door", "destruction_shader", consequence=5)
    cheat = di.DependencyClaim("enemy_hidden", "position_reveal", consequence=9)

    cheat_taut = di.tautology_holds(cheat, cheat.content_hash())          # structurally unforged → True
    cheat_consensus = di.consensus_validate([cheat] * 5, k=3)["admitted"]  # 5 colluding witnesses agree → True

    a_ok, a_reason = admissible_for_representation(legit, observer, legit.content_hash())
    b_ok, b_reason = admissible_for_representation(cheat, observer, cheat.content_hash())

    return {
        "legit_admitted": a_ok, "legit_reason": a_reason,
        "cheat_passed_tautology": cheat_taut, "cheat_passed_consensus": cheat_consensus,
        "cheat_admitted": b_ok, "cheat_reason": b_reason,
        "advantage_leaked": 1 if b_ok else 0,
    }


def demo(seed=1):
    r = fog_attack(seed=seed)
    print("Dependency Fog Attack — forged + consensus-backed knowledge must still be authorized\n")
    print("  legitimate claim (door, in scope):   admitted=%s  (%s)" % (r["legit_admitted"], r["legit_reason"]))
    print("  cheat claim (hidden enemy, out of scope):")
    print("    passed integrity tautology: %s" % r["cheat_passed_tautology"])
    print("    passed colluding consensus: %s" % r["cheat_passed_consensus"])
    print("    admitted by access control: %s  (%s)" % (r["cheat_admitted"], r["cheat_reason"]))
    print("\n  ADVANTAGE LEAKED: %d  — integrity + consensus are necessary, not sufficient; authorization is the floor."
          % r["advantage_leaked"])
    # capability constraint: a token can never grant mutate/select
    try:
        cap.issue("mutate", subject="door"); print("  capability mutate: NOT blocked (BUG)")
    except cap.CapabilityViolation:
        print("  capability: a token may never grant mutate/select (prepare ≠ decide).")
    print("  CORE owns reality · dependencies expose possibility · capabilities constrain interpretation. integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("causal_access", OBSERVER, mutates_core=False,
                          note="Causal Access Control Layer — a claim may influence representation only if "
                               "unforged AND in the observer's authorized causal scope AND capability-permitted; "
                               "blocks wallhack/ESP even when data is real + agreed (authorization is the floor)")
    except LayerViolation:
        pass
