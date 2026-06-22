# SPDX-License-Identifier: AGPL-3.0-only
"""
klein_probe.py — the Klein / non-orientability diagnostic: catch a local convention promoted to a global lie.

This is the one topology analogy that survives as *actual implementable mathematics*, not metaphor. "Non-
orientable" has an exact discrete form: a SIGNED graph in which some cycle has sign-product −1. Following such
a cycle returns you to the start with the side reversed — which is precisely the failure the metaphor names:

    "If I follow this boundary through all of its consequences, does it return me to where I started with the
     meanings reversed? If yes, the architecture is confusing a coordinate choice for ontology."

The model: architectural boundaries are signed edges between elements.
    sign +1  the two elements are on the SAME side under that boundary
    sign −1  they are on OPPOSITE sides
A consistent GLOBAL side-assignment (orientation) exists iff there is no frustrated cycle (sign-product −1) —
the discrete definition of orientability, the same test used on triangulated surfaces.

What the diagnostic asserts:
    ORIENTABLE       the local boundaries cohere into one consistent global cut — safe to treat as a unit.
    NON_ORIENTABLE   following the boundaries reverses orientation on a cycle — the "single global boundary"
                     claim is impossible; the boundaries are real LOCALLY but a lie if promoted to one frame.

Crucially: every boundary is fine *locally* (any single edge / acyclic part is 2-colorable); non-orientability
is a GLOBAL property of a cycle. So the diagnostic fires only on the *promotion* — "these locals imply one
global boundary" — never on the boundaries merely existing. It is a cold-layer ADVERSARIAL QUESTION: not the
kernel, not a protocol, not a partition strategy, not a proof. It does not say merge or split; it says only
whether the global claim is consistent — where the system might be believing its own abstraction.

HONEST SCOPE: the orientability test (signed-cycle frustration) is exact topology. Encoding a given
architectural boundary into a +1/−1 edge is a DECLARED model (`declared ≠ verified`). The math is real; which
edges and signs describe your system is a convention you assert.

Run:  PYTHONHASHSEED=0 python3 klein_probe.py
"""
from __future__ import annotations

from collections import defaultdict


def orient(edges):
    """Pure. Try to assign every element a global side (+1/−1) consistent with all signed boundaries.
    Returns (True, side_map) if orientable, else (False, conflict) where conflict shows a single element
    forced to OPPOSITE sides — the reversal that proves a frustrated cycle."""
    adj = defaultdict(list)
    nodes = set()
    for (u, v, s, _b) in edges:
        adj[u].append((v, s))
        adj[v].append((u, s))
        nodes.add(u); nodes.add(v)
    side: dict = {}
    for start in sorted(nodes):
        if start in side:
            continue
        side[start] = 1
        stack = [start]
        while stack:
            u = stack.pop()
            for (v, s) in adj[u]:
                want = side[u] * s
                if v not in side:
                    side[v] = want
                    stack.append(v)
                elif side[v] != want:
                    return (False, {"element": v, "wanted": want, "had": side[v], "reached_via": u})
    return (True, dict(side))


def orientable(edges) -> bool:
    return orient(edges)[0]


def classify(edges) -> str:
    return "ORIENTABLE" if orientable(edges) else "NON_ORIENTABLE"


def boundary_types(edges) -> set:
    return {b for (_u, _v, _s, b) in edges}


def edges_of_type(edges, b):
    return [e for e in edges if e[3] == b]


# --- two systems of boundaries over the same kind of architecture ---

# COHERENT: editor inside the world's mechanism (+), history private vs observable world (−), history vs
# editor opposite (−). The cycle closes consistently (sign-product (+)(−)(−) = +1): one global cut exists.
COHERENT = [
    ("editor", "world", +1, "membership"),
    ("world", "history", -1, "contract"),
    ("history", "editor", -1, "contract"),
]

# EMBEDDED OBSERVER: "the observer is OUTSIDE the world" (−), "the observation is the observer's own act" (+),
# "the event lands in the world's history" (+). The loop world→observer→event→world has sign-product
# (−)(+)(+) = −1 — frustrated. There is no consistent global "outside": the recorder is in the recorded.
OBSERVER = [
    ("world", "observer", -1, "observer/observed"),
    ("observer", "event", +1, "membership"),
    ("event", "world", +1, "dependency"),
]


def main() -> None:
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<38} {detail}")

    print("klein_probe — does a boundary stay a useful LOCAL convention, or become an impossible GLOBAL claim?")
    print("Signed-cycle frustration = non-orientability = 'follow it and the meaning reverses'. Cold-layer; no verdict.\n")

    print(f"  COHERENT system  → {classify(COHERENT)}   (the local boundaries cohere into one consistent global cut)")
    print(f"  EMBEDDED OBSERVER → {classify(OBSERVER)}  (world→observer→event→world reverses orientation)\n")

    # 1. every boundary is orientable LOCALLY — a single signed edge is always 2-colorable
    each_edge_ok = all(orientable([e]) for e in COHERENT + OBSERVER)
    each_type_ok = all(orientable(edges_of_type(OBSERVER, b)) for b in boundary_types(OBSERVER))
    check("each_boundary_locally_orientable", each_edge_ok and each_type_ok,
          "single edges and single-boundary subgraphs are all orientable — local two-sidedness always works")

    # 2. a coherent system unifies into one global cut
    ok2, side2 = orient(COHERENT)
    check("coherent_system_is_orientable", ok2 and classify(COHERENT) == "ORIENTABLE",
          f"global side-assignment exists {side2} — safe to treat the locals as one boundary")

    # 3. the embedded-observer loop is non-orientable — no consistent global 'outside'
    ok3, conflict = orient(OBSERVER)
    check("embedded_observer_is_non_orientable", (not ok3) and classify(OBSERVER) == "NON_ORIENTABLE",
          "the recorder is in the recorded: 'observer is outside the world' cannot hold globally")

    # 4. the failure is GLOBAL, not local — drop any one edge of the frustrated cycle and orientability returns
    restored = all(orientable(OBSERVER[:i] + OBSERVER[i + 1:]) for i in range(len(OBSERVER)))
    check("failure_is_global_not_local", restored,
          "removing ANY single boundary restores orientability — the lie lives in the cycle, not an edge (locality escape)")

    # 5. the test IS the reversal — a single element is forced to opposite sides (returns with meaning reversed)
    check("test_is_the_reversal",
          (not ok3) and conflict["wanted"] == -conflict["had"],
          f"element '{conflict['element']}' forced to {conflict['had']} and {conflict['wanted']} — orientation reversed on the loop")

    # 6. the diagnostic fires ONLY on the global-promotion claim — kept as separate locals, all boundaries are fine
    per_boundary_fine = all(orientable(edges_of_type(OBSERVER, b)) for b in boundary_types(OBSERVER))
    unified_fails = not orientable(OBSERVER)
    check("fires_only_on_global_promotion", per_boundary_fine and unified_fails,
          "each boundary alone: orientable; 'these imply ONE global boundary': non-orientable — the claim is the failure")

    # 7. sealed instrument, no verdict — pure functions, no mutation, emits a classification not an action
    snapshot = list(OBSERVER)
    _ = orient(OBSERVER); _ = classify(OBSERVER)
    pure = OBSERVER == snapshot and classify(OBSERVER) in ("ORIENTABLE", "NON_ORIENTABLE")
    check("instrument_is_sealed_no_verdict", pure,
          "orient/classify are pure; output is a label, never 'merge' or 'split' — observation ≠ intervention")

    print(f"\n{passed}/{total} checks. The diagnostic computed orientability exactly (signed-cycle frustration —")
    print("real topology, not metaphor): a COHERENT set of boundaries unifies into one global cut, while the")
    print("EMBEDDED-OBSERVER loop does not — there is no consistent global 'outside' from which the system")
    print("observes itself, and trying to claim one returns you with the orientation reversed. The failure is")
    print("global, not local (every boundary is fine alone); it fires only on the promotion of locals to a single")
    print("global boundary; and it issues NO verdict — it does not say merge or split, only whether the global")
    print("claim is a lie. A cold-layer adversarial test for the moment the architecture worships a boundary it")
    print("only needed to draw. (The orientability test is exact; the encoding of boundaries into signs is declared.)")
    assert passed == total, "the Klein diagnostic failed its own self-test"


if __name__ == "__main__":
    main()
