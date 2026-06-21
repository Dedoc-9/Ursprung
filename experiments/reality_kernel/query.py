# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/query.py — Query: provenance-aware observation of existence AND absence.

The genuinely new surface of the kernel. A normal engine answers "what is here?"; this answers, for
any target:

    existence        present | absent | unresolved | unaccounted
    provenance       the lineage (if present)
    diagnosis        why absent/unresolved (the failure taxonomy)
    resolution_path  what would change the status

This is a strict refinement of the Reality Authoring `explain()`: that bench merged absent and
unresolved into one `absent_or_unresolved` status; the kernel splits them by tier (an ABSOLUTE
failure means absent with no remedy; a RELATIVE one means unresolved, with a path). No information is
lost — one distinction is gained. `provenance_of` / `provenance_of_nonrecovery` expose the two halves.
"""
from __future__ import annotations

_ABSOLUTE = ("severance", "indistinguishability")
_RESOLUTION = {"severance": "none", "indistinguishability": "none",
               "resource_limit": "allocate"}   # assumption_limit handled inline (needs the missing condition)


def provenance_of(world, target):
    return world.provenance_of(target)


def provenance_of_nonrecovery(nonrecovery, target):
    return nonrecovery.get(target)


def query(world, nonrecovery, target) -> dict:
    """The unified four-way answer. Present iff there is live, non-orphaned history; else a recorded
    non-recovery (absent if absolute, unresolved if relative); else the silent gap, UNACCOUNTED."""
    if world.history.get(target) and world.value(target) is not None:
        return {"existence": "present", "provenance": world.provenance_of(target),
                "diagnosis": None, "resolution_path": "none_needed"}
    nr = nonrecovery.get(target)
    if nr:
        failure = nr["diagnosis"]["failure"]
        existence = "absent" if failure in _ABSOLUTE else "unresolved"
        if failure == "assumption_limit":
            resolution = "declare:%s" % (nr.get("missing") or "admissibility")
        else:
            resolution = _RESOLUTION.get(failure, "investigate")
        return {"existence": existence, "provenance": None, "diagnosis": failure,
                "tier": nr["diagnosis"]["tier"], "observer_independent": nr["diagnosis"]["observer_independent"],
                "missing": nr.get("missing"), "resolution_path": resolution}
    return {"existence": "unaccounted", "provenance": None, "diagnosis": None,
            "resolution_path": "investigate"}


# `explain` is the same unified answer under the Reality Authoring name (the consolidated successor).
explain = query
