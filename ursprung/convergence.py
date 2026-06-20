# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/convergence.py — Convergence Surface / Distributed Reality Reconciliation (M17): correction ≠ cause.

M10–M16 were single-world, multi-observer: one committed Weltlinie, many clients each denied a different
slice of it. M17 is the dual. The system can now hide information — but it must survive DISAGREEMENT. Two
legitimate observers hold different partial realities and both must converge on the committed state without
the convergence process itself leaking:

    CLIENT A: "I saw input X, predicted state A"
    CLIENT B: "I saw input Y, predicted state B"
    SERVER:   "Committed state is C"

A normal engine reconciles by correction: wrong prediction → snap → replay. But the Ursprung stack has made
*snapping itself* suspicious — the correction magnitude leaks hidden state, its timing leaks causality, the
objects corrected reveal dependency structure, the rollback cost reveals which futures were expensive, and
different observers receiving different corrections leaks policy. The new currency:

    **Convergence Debt** = the observable cost of making multiple private representations become one reality.

M16 already foreshadowed this: a shader hitch is a *local* correction event; a rollback is a *temporal*
correction event. Both are "the system revealing that reality had to be repaired." Execution privacy and
reconciliation are the same class of problem; M17 is that class on the time axis.

Four mechanisms + the unifying invariant, each with a negative control:

  1. RECONCILIATION SIGNATURE DEBT — rollback is a side channel: an exact correction distance is hidden
     information (A rolls back 2 frames, B rolls back 40 → B's causal neighborhood had something important).
     The fix (M15/M16, again) is a BOUNDED FAMILY {none, small, medium, large}, not an exact distance.
  2. DIVERGENCE FIREWALL — M14 stopped many-observers → hidden-fact; M17 stops observer-disagreements →
     hidden-fact. A client receives "the world changed," never "…because the server corrected a hidden
     collision 37 m away involving entity 184," unless causally entitled.
  3. CONVERGENCE READINESS — the M7/M9 readiness question turns: not "what representation do I need before the
     future happens?" but "what representation do I need so that the correction itself is cheap?" A prepared
     representation avoids an *observable reconciliation event*, not merely a hitch.
  4. DISTRIBUTED CORRECTION RECONSTRUCTION — the most dangerous attacker is no longer the wallhacker but a
     fleet of honest clients observing their own corrections and comparing notes: a distributed microscope.
     The M12/M13 machinery returns, now over NETWORK behavior — each correction harmless, the union reconstructs.

  INVARIANT (correction ≠ cause): a correction may reveal THAT reality changed, never WHY / WHERE / WHO it was
  repaired. This is `consequence ≠ mechanism` (M14) and `image ≠ generator` (M15) on the convergence axis.

CLASSIFICATION: OBSERVER (mutates_core=False). Only the SERVER/CORE commits the reconciled trajectory; this
layer shapes how the correction is *presented* to each client. It never selects the committed state.
correction ≠ cause; convergence ≠ disclosure; integrity ≠ truth.

HONEST BOUND: declared correction-distance / bit / fragment proxies, not measured netcode under real latency,
jitter, and packet loss. Convergence is only meaningful against REAL divergence — this is the first layer in
the arc that cannot be validated with constructed numbers; it needs an authoritative server and real clients.
The model gives the SHAPE; the proof is contact with the network. integrity ≠ truth.
"""
from __future__ import annotations


# --- 1. Reconciliation Signature Debt (rollback is a side channel) ----------------------------------

CORRECTION_FAMILY = ("none", "small", "medium", "large")


def correction_bucket(distance):
    """Map an exact rollback distance to a bounded family. The client learns the family, not the distance."""
    d = abs(int(distance))
    if d == 0:
        return "none"
    if d <= 4:
        return "small"
    if d <= 16:
        return "medium"
    return "large"


def exposed_correction(distance, mode):
    """exact: the raw rollback distance (invertible — the correction IS the hidden information).
    bucketed: a member of the bounded family (reveals only the coarse class)."""
    if mode == "exact":
        return abs(int(distance))
    if mode == "bucketed":
        return correction_bucket(distance)
    raise ValueError("mode must be exact|bucketed")


def reconciliation_recoverable_levels(distances, mode):
    """How many distinct correction states an observer can distinguish from the exposed reconciliation."""
    return len({exposed_correction(d, mode) for d in distances})


def reconciliation_signature_debt(distances, mode):
    """The count of distinguishable correction states leaked. exact ⇒ ~one per distance; bucketed ⇒ ≤4."""
    return reconciliation_recoverable_levels(distances, mode)


# --- 2. Divergence Firewall (disagreement must not reconstruct a hidden fact) -----------------------

def divergence_disclosure(correction, observer_entitled):
    """What a client is told about a correction. Entitled ⇒ the full, honest, in-scope detail. Otherwise ⇒
    only that the world changed (the repair detail — object/distance/cause — is stripped)."""
    if observer_entitled:
        return dict(correction)
    return {"changed": bool(correction.get("changed", True))}


def disclosure_bits(disclosure):
    """A crude information proxy: how many non-trivial fields the client receives."""
    return sum(1 for k, v in disclosure.items() if v not in (None, False))


# --- 3. Convergence Readiness (prepared so the correction itself is cheap) --------------------------

def correction_signature(hidden_event_near, prepared):
    """The observable cost of applying a correction. prepared ⇒ baseline (no observable reconciliation event);
    unprepared ⇒ a large rollback spike exactly when a hidden event is near (the cost reveals the event)."""
    if prepared:
        return 1                                    # constant: correction is absorbed, not observed
    return 40 if hidden_event_near else 1           # a 40-frame rollback when the hidden event is near


def convergence_readiness_debt(prepared):
    """|signature(event near) − signature(no event)|. 0 ⇒ correction cost reveals nothing about the event."""
    return abs(correction_signature(True, prepared) - correction_signature(False, prepared))


# --- 4. Distributed Correction Reconstruction (honest clients as a distributed microscope) ----------

def per_client_reconstruction(client_corrections, event_bits):
    return {c: min(1.0, bits / max(1, event_bits)) for c, bits in client_corrections.items()}


def distributed_correction_reconstruction(client_corrections, event_bits):
    """The fleet as one sensor: the union of every client's observed correction information."""
    total = sum(client_corrections.values())
    return min(1.0, total / max(1, event_bits))


def distributed_correction_firewall(client_corrections, event_bits, threshold=0.5):
    """Admit correction disclosures across ALL clients only while the cumulative reconstruction stays under
    threshold; cap the cross-client union even though each client is individually harmless."""
    cap = threshold * event_bits
    cumulative = 0
    admitted, blocked = [], []
    for c in sorted(client_corrections):
        bits = client_corrections[c]
        if cumulative + bits <= cap:
            cumulative += bits
            admitted.append(c)
        else:
            blocked.append(c)
    return {"reconstruction": min(1.0, cumulative / max(1, event_bits)),
            "admitted": admitted, "blocked": blocked}


# --- the unifying invariant: correction ≠ cause -----------------------------------------------------

CHANGE_FACTS = {"world_changed", "state_updated"}
REPAIR_DETAILS = {"corrected_object", "rollback_distance", "collision_cause", "entity_id", "futures_cost"}


def admissible_correction_disclosure(kind, observer_entitled=False):
    """A correction may reveal THAT reality changed; it may not reveal WHY / WHERE / WHO it was repaired,
    unless the observer is causally entitled. correction ≠ cause."""
    if observer_entitled:
        return True
    return (kind in CHANGE_FACTS) and (kind not in REPAIR_DETAILS)


# --- the convergence crucible -----------------------------------------------------------------------

def crucible():
    out = {}
    distances = list(range(0, 41))
    # 1. reconciliation signature: exact distance is invertible; the bounded family is not
    out["recon_exact_levels"] = reconciliation_signature_debt(distances, "exact")
    out["recon_bucketed_levels"] = reconciliation_signature_debt(distances, "bucketed")
    # 2. divergence firewall: an unentitled client learns "world changed", not the repair detail
    correction = {"changed": True, "corrected_object": 184, "rollback_distance": 37, "collision_cause": "hit"}
    out["disclosure_entitled_bits"] = disclosure_bits(divergence_disclosure(correction, True))
    out["disclosure_unentitled_bits"] = disclosure_bits(divergence_disclosure(correction, False))
    # 3. convergence readiness: a prepared correction is unobservable; an unprepared one spikes
    out["readiness_unprepared"] = convergence_readiness_debt(prepared=False)
    out["readiness_prepared"] = convergence_readiness_debt(prepared=True)
    # 4. distributed correction reconstruction: 4 honest clients, 15 bits each (each 0.23 < 0.5)
    fleet = {"A": 15, "B": 15, "C": 15, "D": 15}
    per = per_client_reconstruction(fleet, event_bits=64)
    out["per_client_each_safe"] = all(v <= 0.5 for v in per.values())
    out["fleet_union"] = distributed_correction_reconstruction(fleet, event_bits=64)
    out["fleet_firewalled"] = distributed_correction_firewall(fleet, event_bits=64, threshold=0.5)["reconstruction"]
    # 5. correction != cause
    out["change_fact_ok"] = admissible_correction_disclosure("world_changed", observer_entitled=False)
    out["repair_detail_blocked"] = not admissible_correction_disclosure("rollback_distance", observer_entitled=False)
    out["entitled_sees_detail"] = admissible_correction_disclosure("rollback_distance", observer_entitled=True)
    return out


def demo():
    r = crucible()
    print("Convergence Surface / Distributed Reality Reconciliation — correction ≠ cause\n")
    print("  1. reconciliation signature: exact rollback distance=%d distinguishable states vs bounded family=%d"
          % (r["recon_exact_levels"], r["recon_bucketed_levels"]))
    print("  2. divergence firewall: entitled client learns %d fields; unentitled learns %d ('world changed')"
          % (r["disclosure_entitled_bits"], r["disclosure_unentitled_bits"]))
    print("  3. convergence readiness: unprepared correction debt=%d (a visible rollback) vs prepared=%d"
          % (r["readiness_unprepared"], r["readiness_prepared"]))
    print("  4. distributed: each client alone safe=%s; fleet union reconstructs=%.2f; firewalled=%.2f"
          % (r["per_client_each_safe"], r["fleet_union"], r["fleet_firewalled"]))
    print("  5. correction ≠ cause: 'world changed' ok=%s; repair detail blocked=%s; entitled sees detail=%s"
          % (r["change_fact_ok"], r["repair_detail_blocked"], r["entitled_sees_detail"]))
    print("\n  a shader hitch is a local correction; a rollback is a temporal one — both reveal that reality")
    print("  had to be repaired. a correction may reveal THAT, never WHY/WHERE/WHO. integrity ≠ truth.")
    return r


def register():
    from .registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("convergence", OBSERVER, mutates_core=False,
                          note="Convergence Surface / Distributed Reality Reconciliation — reconciliation "
                               "signature debt + divergence firewall + convergence readiness + distributed "
                               "correction reconstruction + correction≠cause")
    except LayerViolation:
        pass
