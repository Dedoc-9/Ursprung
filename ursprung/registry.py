# SPDX-License-Identifier: AGPL-3.0-only
"""
ursprung/registry.py — the system-classification register (the rule, as data, not as prose).

Every Ursprung subsystem declares which layer it belongs to. The classification is the load-bearing
boundary of the whole renderer:

    CORE       affects committed simulation / replay identity        (may mutate the authoritative trajectory)
    VIEW       affects presentation only                              (read-only consumer of a snapshot)
    ALLOCATOR  chooses WHERE computation is spent (LOD/cull/quality)  (decides effort, never truth)
    OBSERVER   measures, ranks, or reports                            (attention/diagnostics, never truth)

THE ONE LAW (mechanical, enforced at registration time):
    Only CORE systems may declare `mutates_core=True`.
    A VIEW/ALLOCATOR/OBSERVER that claims it mutates the authoritative trajectory is rejected at registration.

This mirrors the workbench discipline of keeping the boundary as DATA a reader inherits even if they never
read the docs (cf. toolkit's `!=` family living inside artifacts). It does NOT, by itself, prove a VIEW
system is side-effect free — that is proven empirically by `ursprung.verify` (hash-identity with/without the
renderer). The register states intent; the harness checks reality. integrity ≠ truth, applied to our own
layering: a declared label is not a proof of behavior.
"""
from __future__ import annotations

CORE = "CORE"
VIEW = "VIEW"
ALLOCATOR = "ALLOCATOR"
OBSERVER = "OBSERVER"

LAYERS = (CORE, VIEW, ALLOCATOR, OBSERVER)

# Only this layer is permitted to influence the authoritative world trajectory / replay identity.
_MAY_MUTATE_CORE = {CORE}


class LayerViolation(Exception):
    """Raised when a non-CORE system claims authority over the committed trajectory. Fail closed."""


class System:
    __slots__ = ("name", "layer", "mutates_core", "note")

    def __init__(self, name, layer, mutates_core, note):
        self.name = name
        self.layer = layer
        self.mutates_core = mutates_core
        self.note = note

    def __repr__(self):
        flag = " mutates_core" if self.mutates_core else ""
        return "<System %s [%s]%s>" % (self.name, self.layer, flag)


class Registry:
    """A small in-process register of declared subsystems and their layer classification."""

    def __init__(self):
        self._systems = {}

    def register(self, name, layer, mutates_core=False, note=""):
        if layer not in LAYERS:
            raise LayerViolation("unknown layer %r (expected one of %r)" % (layer, LAYERS))
        if mutates_core and layer not in _MAY_MUTATE_CORE:
            raise LayerViolation(
                "%s is %s but declares mutates_core=True — only %s may affect the authoritative "
                "trajectory. (LOD/culling/reconstruction/neural decide WHERE effort goes, never WHAT is true.)"
                % (name, layer, "/".join(sorted(_MAY_MUTATE_CORE)))
            )
        if name in self._systems:
            raise LayerViolation("system %r already registered" % name)
        sys_obj = System(name, layer, mutates_core, note)
        self._systems[name] = sys_obj
        return sys_obj

    def get(self, name):
        return self._systems[name]

    def by_layer(self, layer):
        return [s for s in self._systems.values() if s.layer == layer]

    def all(self):
        return list(self._systems.values())

    def authoritative_systems(self):
        """The ONLY systems allowed to move the Weltlinie. Anything else touching it is a bug."""
        return [s for s in self._systems.values() if s.mutates_core]


# A module-level register the demo/harness populate so the layering is inspectable at runtime.
REGISTRY = Registry()