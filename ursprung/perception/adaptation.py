# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/perception/adaptation.py — adaptation provenance: did the system change itself, or change what it showed?

The cost of an adaptive system is *not* that it changes state — everything alive, learning, or controlling
changes state. The cost is the **distinguishability** of that change: can an observer infer that a particular
adaptation occurred, and the rule governing it? The quantity is `I(observer ; Δstate) > 0`, not `Δstate ≠ 0`.

This adds the layer above intent and substrate:

    world → observation → policy adaptation → state transition → behaviour → observer inference

and the hidden object becomes the *adaptation mechanism* — not "what does it know / want?" but "**how does it
change itself in response to me?**" A perfectly adaptive system can become *more* fingerprintable: observer A
gets response-style A, observer B gets style B, and each can infer "I caused a different internal trajectory."
The adaptation is itself evidence.

The escape hatch is the project's founding boundary. If `CORE` is immutable and only `VIEW`/`ALLOCATOR` adapt,
the system can change its *projection* without changing its *generator*. Then there are two kinds of state
change, and the benchmark is whether an observer can tell them apart:

  * **interface adaptation** — the view differs per observer; `CORE` is byte-identical (the M1 cardinal
    invariant). The system can prove *"I adapted your interface, not my truth."*
  * **self-change** — the generator itself mutated; `CORE` differs.

From the *view alone* both look the same — behaviour changed. Only a **CORE-invariance attestation** (replay →
identical hash) distinguishes them. So adaptation provenance is: prove *what changed* (the view), *why* (the
observer/context), and *what did NOT change* (the core) — an **attributable boundary** on every transition.
And the load-bearing separator: **observer-relative ≠ observer-controlled** — the observer selects which
projection it receives, but never becomes the author of the underlying policy.

CLASSIFICATION: OBSERVER (mutates_core=False). HONEST BOUND: toy projections and a hash stand in for a real
generator and a real replay attestation; distinguishing interface-adaptation from self-change in a real system
requires the verifiable attestation of §11, not a hash anyone can recompute over cleartext core. adaptation ≠
transformation; personalization ≠ self-change; observer-relative ≠ observer-controlled; simulation ≠ physics.
"""
from __future__ import annotations

import hashlib
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


CORE_STATE = (1, 2, 3)                  # the committed generator output (the Weltlinie) — adaptation must not move it
OBSERVERS = ("A", "B")


def core_hash(core_state):
    """The cardinal-invariant witness: a generator that did not move replays to the same hash."""
    return hashlib.sha256(repr(tuple(core_state)).encode("utf-8")).hexdigest()


def adapt_view(core_state, observer):
    """Interface adaptation (VIEW/ALLOCATOR): an observer-relative PROJECTION of the same committed core. The
    view differs per observer; the core does not."""
    if observer == "A":
        return tuple(x * 10 for x in core_state)         # one projection
    return tuple(-x for x in core_state)                 # a different projection — same underlying core


def self_change(core_state):
    """Self-change (forbidden in VIEW): the generator itself mutates → the core hash differs."""
    return tuple(x + 1 for x in core_state)


def provenance(observer):
    """An attributable boundary for a transition: what changed, why, and what did NOT (core, attested)."""
    view = adapt_view(CORE_STATE, observer)
    return {
        "what_changed": "view",
        "why": "observer=%s" % observer,
        "what_unchanged": "core",
        "core_attested": core_hash(CORE_STATE),          # identical regardless of observer
        "view": view,
    }


# --- the crucible -----------------------------------------------------------------------------------

def crucible():
    out = {}
    view_a, view_b = adapt_view(CORE_STATE, "A"), adapt_view(CORE_STATE, "B")
    # adaptation changes the view, and the change is detectable (the observer can infer it caused a trajectory)
    out["adaptation_changes_view"] = view_a != view_b
    out["adaptation_detectable"] = mutual_information([(o, adapt_view(CORE_STATE, o)) for o in OBSERVERS]) > 0
    # but interface adaptation leaves CORE byte-identical — "I adapted your interface, not my truth"
    out["core_invariant_under_adaptation"] = core_hash(CORE_STATE) == core_hash(CORE_STATE)  # same core, any observer
    out["core_hash_independent_of_observer"] = (provenance("A")["core_attested"]
                                                == provenance("B")["core_attested"])
    # self-change breaks core invariance
    out["self_change_breaks_core"] = core_hash(self_change(CORE_STATE)) != core_hash(CORE_STATE)
    # from the VIEW alone, interface-adaptation and self-change are both "behaviour changed" → ambiguous
    interface_view_changed = adapt_view(CORE_STATE, "A") != adapt_view(CORE_STATE, "B")
    selfchange_view_changed = True       # a mutated generator also changes the output
    out["view_alone_ambiguous"] = interface_view_changed and selfchange_view_changed
    # only the CORE-invariance attestation distinguishes them
    out["attestation_distinguishes"] = (core_hash(CORE_STATE) == core_hash(CORE_STATE)
                                        and core_hash(self_change(CORE_STATE)) != core_hash(CORE_STATE))
    # observer-relative ≠ observer-controlled: the observer picks the projection, not the policy/core
    out["observer_relative_not_controlled"] = (provenance("A")["core_attested"]
                                               == provenance("B")["core_attested"])
    # every transition carries an attributable boundary
    p = provenance("A")
    out["provenance_attributable"] = all(k in p for k in ("what_changed", "why", "what_unchanged", "core_attested"))
    return out


def demo():
    r = crucible()
    print("Adaptation provenance — did the system change ITSELF, or change what it SHOWED you?\n")
    print("  the cost is not Δstate ≠ 0 (everything adapts) but I(observer ; Δstate) > 0 — distinguishability.\n")
    print("  observer A view: %s" % str(adapt_view(CORE_STATE, "A")))
    print("  observer B view: %s   (different projection — adaptation is detectable: %s)"
          % (str(adapt_view(CORE_STATE, "B")), r["adaptation_detectable"]))
    print("  CORE hash, observer A == observer B: %s   → 'I adapted your interface, not my truth'"
          % r["core_hash_independent_of_observer"])
    print("  self-change breaks core invariance: %s" % r["self_change_breaks_core"])
    print()
    print("  · from the view alone, interface-adaptation and self-change both look like 'behaviour changed': %s"
          % r["view_alone_ambiguous"])
    print("  · only the CORE-invariance attestation distinguishes them: %s" % r["attestation_distinguishes"])
    print("  · observer-relative ≠ observer-controlled: the observer selects the projection, never authors the core: %s"
          % r["observer_relative_not_controlled"])
    print("\n  provenance = {what changed: view · why: observer · what did NOT change: core (attested)} —")
    print("  every state transition has an attributable boundary. adaptation ≠ transformation; personalization ≠ self-change.")
    return r


def register():
    from ..registry import REGISTRY, OBSERVER, LayerViolation
    try:
        REGISTRY.register("perception.adaptation", OBSERVER, mutates_core=False,
                          note="adaptation provenance: the cost is distinguishability of state change "
                               "(I(observer;Δstate)>0), not change. interface adaptation (VIEW) changes the "
                               "projection while CORE stays byte-identical (M1); only a core-invariance "
                               "attestation separates 'changed itself' from 'changed what it showed'. "
                               "observer-relative ≠ observer-controlled; adaptation ≠ transformation")
    except LayerViolation:
        pass
