# SPDX-License-Identifier: AGPL-3.0-only
"""
rin_analysis.py — Phase 17: graph analyses over a residue interaction network.

Step 2: turn a RIN into per-residue scores that are *hypotheses* about which residues mediate allostery.
The centrality measures here are ESTABLISHED methods — betweenness centrality and reach are textbook, used
across structural-allostery work; no novelty is claimed for them. The one piece in the project's own idiom
is the **Potential ⊇ Actual** split: a perturbation can *reach* much of a connected protein (Potential),
but an attenuating signal is actually *carried* by a sparse set of residues (Actual). The residues where a
lot of signal flows are the ones worth flagging — `reachable ≠ carrying`.

Everything is pure-stdlib and deterministic so it runs anywhere and is reproducible.
"""
from __future__ import annotations

from collections import deque


def reach(adj, src):
    """Potential: every residue reachable from src (its connected component, undirected)."""
    seen, q = {src}, deque([src])
    while q:
        x = q.popleft()
        for y in adj.get(x, ()):
            if y not in seen:
                seen.add(y); q.append(y)
    return seen


def betweenness(adj):
    """Shortest-path betweenness centrality (Brandes), unweighted undirected. ESTABLISHED method."""
    nodes = list(adj)
    bc = {v: 0.0 for v in nodes}
    for s in nodes:
        S, P = [], {w: [] for w in nodes}
        sigma = {w: 0 for w in nodes}; sigma[s] = 1
        d = {w: -1 for w in nodes}; d[s] = 0
        Q = deque([s])
        while Q:
            v = Q.popleft(); S.append(v)
            for w in adj[v]:
                if d[w] < 0:
                    d[w] = d[v] + 1; Q.append(w)
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]; P[w].append(v)
        delta = {w: 0.0 for w in nodes}
        while S:
            w = S.pop()
            for v in P[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]
    return {v: bc[v] / 2.0 for v in nodes}     # undirected ⇒ halve


def attenuating_flow(adj, src, alpha: float = 0.6, iters: int = 200):
    """ACTUAL: steady-state signal concentration under damped diffusion with constant injection at src.
    f[src] held at 1; each step every node pushes alpha/deg of its signal to neighbours. Signal decays with
    graph distance, so most reachable residues carry little — the Potential ⊇ Actual sparsity, on a protein."""
    f = {n: 0.0 for n in adj}
    if src not in f:
        return f
    f[src] = 1.0
    for _ in range(iters):
        nf = {n: 0.0 for n in adj}
        for u in adj:
            deg = len(adj[u])
            if deg == 0 or f[u] == 0.0:
                continue
            share = f[u] * alpha / deg
            for v in adj[u]:
                nf[v] += share
        nf[src] = 1.0                            # clamp the source (constant perturbation)
        f = nf
    return f


def potential_vs_actual(adj, src, frac: float = 0.05):
    """Split reachable residues into 'carrying' (flow ≥ frac·max) vs 'reachable-only' (the Actual ⊆ Potential
    gap). Returns the sets + the flow map. This is where the allocator idea lands: attend to what carries."""
    reachable = reach(adj, src)
    flow = attenuating_flow(adj, src)
    peak = max(flow.values()) or 1.0
    carrying = {n for n in reachable if n != src and flow[n] >= frac * peak}
    reachable_only = {n for n in reachable if n != src and n not in carrying}
    return {"potential": reachable, "carrying": carrying, "reachable_only": reachable_only, "flow": flow}


def mediators(adj, allo, active):
    """Residues whose KNOCKOUT disconnects allo from active (cut vertices on the allo→active relation).
    The hypothesis's 'essential transmitters' — candidate uncoupling mutations / drug sites."""
    if active not in reach(adj, allo):
        return []
    out = []
    for r in adj:
        if r in (allo, active):
            continue
        sub = {k: [x for x in v if x != r] for k, v in adj.items() if k != r}
        if active not in reach(sub, allo):
            out.append(r)
    return sorted(out)


def main():
    import pdb_rin
    rin = pdb_rin.build_rin(pdb_rin.synthetic_pdb())
    adj = rin["adj"]
    print("rin_analysis.py — Phase 17: established analyses + Potential ⊇ Actual flow\n")
    bc = betweenness(adj)
    top = sorted(bc, key=lambda v: -bc[v])[:3]
    print(f"  betweenness (established) top: {[(t, round(bc[t],2)) for t in top]}")
    pa = potential_vs_actual(adj, "ALA1")
    print(f"  perturb ALA1 → Potential (reachable) {len(pa['potential'])}, "
          f"Carrying {sorted(pa['carrying'])}, Reachable-only {sorted(pa['reachable_only'])}")
    print("  betweenness = established hypothesis; carrying-set = the Actual ⊆ Potential signal. reachable ≠ carrying.")


if __name__ == "__main__":
    main()
