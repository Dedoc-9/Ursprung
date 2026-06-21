# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_authoring/reality.py — Reality Authoring Runtime: an edit is an event with identity.

Not a game engine, not a world simulator. A system where **every change to reality is itself a first-class
object, and every object carries the conditions under which it came to exist.** This is the layer where
`identity includes provenance` (Law 6) stops being an epistemic discipline and becomes an architecture.

The question this runtime answers is not "can the system preserve provenance?" (established) but:

    Can a world remain EDITABLE while preserving the distinction between authored, learned, and discovered
    structure?

So an edit is not a mutation. Instead of `world.gravity = 0.5`, you get an `Edit` event with identity:
target, old → new, **source**, justification, scope, and the survival tests it has (or hasn't) passed. The
world remembers not just what it is, but how it became that way — a World Artifact Graph:

    intent → edit → world-state change → observed behaviour → survival tests → current world claim

The non-anthropocentric invariant (the important correction): the goal is not that *the developer* stays
legible. It is that **the source of structure remains inspectable** — and the runtime does NOT privilege the
human. A source is one of {developer, algorithm, learned_model, external_data, environment}; machine authoring
is authoring; an emergent pattern names its environment; a learned factor names its model. No origin is allowed
to disappear into consistency.

It then answers questions ordinary engines cannot: was this behaviour designed or did it emerge? which
structure is inherited from which source? if I remove this edit, what collapses? and — the bridge to generated
worlds — **which parts of the world are stable under its own transformations** (the discovered constraints, as
opposed to the authored rules and the emergent patterns).

CLASSIFICATION: discipline / architecture (stdlib only, deterministic). HONEST BOUND: this is the authoring and
provenance layer, not a renderer or a physics solver — it records and classifies the *origin* and *survival* of
world structure; it does not simulate the world at fidelity or verify that a survival test was run in good
faith (`declared ≠ verified`). A real-time, high-fidelity, learned-world version needs the real substrate (the
un-faked frontier). Separators: edit ≠ mutation; designed ≠ emerged; authored ≠ discovered; source-of-structure
must remain inspectable (no origin privileged, none erased).
"""
from __future__ import annotations

import hashlib
import json

# the source taxonomy — the runtime privileges none of these
SOURCES = ("developer", "algorithm", "learned_model", "external_data", "environment")
DESIGNING = ("developer", "algorithm")        # deliberate authoring (human OR machine — not privileged)


def _digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:12]


class Edit:
    """A change to reality, as a first-class historical object — never a silent mutation."""
    __slots__ = ("target", "old", "new", "source", "justification", "scope", "depends_on", "survival_tests")

    def __init__(self, target, old, new, source, justification, scope, depends_on=None, survival_tests=()):
        if source not in SOURCES:
            raise ValueError("unknown source %r (must be one of %r)" % (source, SOURCES))
        self.target, self.old, self.new = target, old, new
        self.source, self.justification, self.scope = source, justification, scope
        self.depends_on = depends_on                 # digest of the edit this one is derived from
        self.survival_tests = list(survival_tests)

    def survives(self):
        """Did this edit survive its perturbations? True/False, or None if it was never tested."""
        return all(self.survival_tests) if self.survival_tests else None

    def digest(self):
        return _digest({"target": self.target, "old": self.old, "new": self.new, "source": self.source,
                        "justification": self.justification, "scope": self.scope, "depends_on": self.depends_on})

    def __repr__(self):
        return "<Edit %s %s→%s by %s>" % (self.target, self.old, self.new, self.source)


class World:
    """A world whose state is the *consequence* of an inspectable edit history (the World Artifact Graph)."""

    def __init__(self):
        self.history = {}                            # target -> [Edit] (in order)

    def apply(self, edit):
        self.history.setdefault(edit.target, []).append(edit)
        return edit

    def _orphaned(self, edit):
        """An edit whose dependency has been removed has lost its license — it no longer holds."""
        if edit.depends_on is None:
            return False
        return not any(e.digest() == edit.depends_on for h in self.history.values() for e in h)

    def value(self, target):
        live = [e for e in self.history.get(target, []) if not self._orphaned(e)]
        return live[-1].new if live else None

    def origin(self, target):
        """The set of sources that produced this object — the inspectable source-of-structure."""
        return {e.source for e in self.history.get(target, [])}

    def classify(self, target):
        """Designed (a deliberate edit by developer/algorithm) vs emerged (appeared via environment/learned
        model with no authoring edit) vs learned (a learned-model source). Axes, not exclusive."""
        srcs = self.origin(target)
        designed = bool(srcs & set(DESIGNING))
        return {"sources": sorted(srcs), "designed": designed,
                "emerged": (not designed) and bool(srcs & {"environment", "learned_model"}),
                "learned": "learned_model" in srcs}

    def remove(self, target, index):
        """Remove an edit — and let everything that depended on it collapse (lose its value). 'If I remove this
        assumption, what collapses?'"""
        self.history[target].pop(index)

    def collapsed_targets(self):
        """Targets whose current value is None because a dependency was removed (downstream collapse)."""
        return [t for t in self.history if self.history[t] and self.value(t) is None]

    def stable_under_transformations(self):
        """Which structure survives the world's own transformations — the DISCOVERED constraints, as opposed to
        authored rules and emergent patterns. The bridge to generated worlds."""
        return {t: (self.history[t][-1].survives() is True) for t in self.history if self.history[t]}

    def provenance_of(self, target):
        """The full lineage of a world object: every edit, its source, justification, and survival."""
        return [{"old": e.old, "new": e.new, "source": e.source, "justification": e.justification,
                 "survives": e.survives(), "digest": e.digest()} for e in self.history.get(target, [])]
