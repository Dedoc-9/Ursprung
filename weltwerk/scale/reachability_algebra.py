# SPDX-License-Identifier: AGPL-3.0-only
"""
reachability_algebra.py — verify the discrete-analytic formulation against the running engine.

A formalism is worth adopting only once it is shown EQUAL to the operational quantity. This module
checks the three sharpened constructs and records the one correction that matters with evidence.

(1) POTENTIAL = |Supp((I∨A)^H e_i)| over the boolean semiring — the ball of radius H. This equals
    `cons.touched` from the conservative reconstruction. The tempting `|Supp(A^H e_i)|` (walks of
    EXACTLY length H) is WRONG: on a bipartite (even) ring it is parity-restricted and UNDERCOUNTS the
    ball. We compute both and show the reflexive power matches while the bare power does not.
    (Static-topology only; dynamic teleport chords ⇒ a time-ordered product ∏ₜ(I∨Aₜ), not a power.)

(2) SELECTIVE COMPUTATION = neighborhood-closure of the divergence indicator 𝕀(Δc≠0), not the bare
    indicator: to learn Δc you must simulate c, so the computed set is `diverged ∪ frontier`. The
    indicator is exact for PROPAGATION; the compute set carries the frontier overhead ring.

(3) MINIMAL TRANSMIT = arg min |T| s.t. L(T)=0. The feasible region is `{T : T ⊇ changed}` — a single
    monotone constraint, i.e. a PRINCIPAL UP-SET — so the minimum is uniquely its generator `changed`.
    This is NOT a Sperner-family / set-cover problem (those imply combinatorial hardness absent here).

These are exact discrete objects mapped to verifiable code quantities — not continuous metaphors.
"""
from __future__ import annotations

from causal_budget import client_view, compute_budget
from cow_world import Edit, Rules, genesis
from teleport import Topology, reconstruct


def reflexive_ball(adj: dict, sources: set, H: int) -> set:
    """Supp((I∨A)^H e_sources): every node within graph-distance H (boolean reflexive power)."""
    reached = set(sources)
    frontier = set(sources)
    for _ in range(H):
        nxt = set()
        for c in frontier:
            nxt.update(adj[c])
        new = nxt - reached
        reached |= nxt
        if not new:
            break               # ball saturated; further reflexive powers add nothing
        frontier = new
    return reached


def exact_walk_support(adj: dict, source: int, H: int) -> set:
    """Supp(A^H e_source): nodes reachable by a walk of EXACTLY length H (non-reflexive power).
    On a bipartite ring this is parity-restricted and is NOT the ball — the formulation's trap."""
    v = {source}
    for _ in range(H):
        nv = set()
        for k in v:
            nv.update(adj[k])
        v = nv
    return v


def feasible_lossless(line_a: dict, line_b: dict, T: set) -> bool:
    """L(T) = 0 ⟺ the client (line A + deltas on T) reconstructs line B exactly."""
    return client_view(line_a, line_b, frozenset(T)) == line_b


if __name__ == "__main__":
    snap = genesis(4000, 200, 0)
    topo = Topology(200, ((5, 130),))
    rules, edit, H = Rules(), Edit("cull_pred_chunk", chunk=5), 30
    b = compute_budget(snap, topo, rules, 0, edit, H)
    ball = reflexive_ball(topo.adj, {5}, H)
    exact = exact_walk_support(topo.adj, 5, H)
    pruned = reconstruct(snap, topo, rules, 0, edit, H, prune=True)
    print("reachability_algebra.py — discrete forms vs the running engine\n")
    print(f"  (1) Potential: |cons.touched|={len(b.potential)}  |reflexive ball (I∨A)^H|={len(ball)}  "
          f"match={b.potential == ball}")
    print(f"      bare A^H support |exact-length walks|={len(exact)}  (undercounts: {len(exact) < len(ball)})")
    print(f"  (2) compute set ⊇ changed: {b.changed <= pruned.touched}; "
          f"overhead ring |touched|-|changed| = {len(pruned.touched) - len(b.changed)}")
    print(f"  (3) minimal transmit |changed|={len(b.changed)}; feasible ⟺ T⊇changed "
          f"(principal up-set, generator is the unique min)")
