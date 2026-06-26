# SPDX-License-Identifier: AGPL-3.0-only
"""
allostery.py — Phase 16: allosteric mapping as causal reach over a residue coupling graph.

Allostery is regulation at a distance: an effector binds one site (the ALLOSTERIC site) and changes activity
at a DIFFERENT, distant site (the ACTIVE site). The signal travels through the protein's internal coupling.
Modelling a protein as a **residue interaction network** (residues = nodes, contacts/couplings = edges) and
asking which residues a perturbation reaches is an established structural method for finding allosteric
pathways — and it is exactly Weltwerk's central object: *Potential ⊇ Actual* over a directed graph.

This maps the field's terms onto the project's verified primitives:

    perturb the allosteric site   →  reach over the coupling graph        (signal wavefront)
    allosteric pathway            →  shortest allo → active path
    essential mediator residue    →  criticality / SPOF: removing it disconnects allo from active
                                      (= an allosteric-uncoupling mutation, or a drug target)
    a redundant residue           →  off the only path / has a bypass: knockout leaves coupling intact

HONEST SCOPE (Dentatus): this is a STRUCTURAL / network abstraction. It is NOT molecular dynamics, NOT
energetics, NOT a predictor of real conformational change or binding free energy. `graph-reach ≠
free-energy coupling`; `network-pathway ≠ measured signal`. It identifies *which residues could mediate*
under a contact model, an attention/allocation signal for where to look — not proof of mechanism.
"""
from __future__ import annotations

from collections import deque


class Protein:
    """A residue coupling graph. edges are DIRECTED for signal flow (allosteric site → active site)."""
    def __init__(self, residues, contacts):
        self.residues = list(residues)
        self.adj = {r: [] for r in self.residues}
        for a, b in contacts:
            self.adj.setdefault(a, []); self.adj.setdefault(b, [])
            if a not in self.residues: self.residues.append(a)
            if b not in self.residues: self.residues.append(b)
            self.adj[a].append(b)

    def propagate(self, source, removed=()):
        """BFS wavefront from a perturbed residue: {residue: hop-distance}. Removed residues are knocked out."""
        removed = set(removed)
        if source in removed:
            return {}
        dist, q = {source: 0}, deque([source])
        while q:
            x = q.popleft()
            for y in self.adj.get(x, ()):
                if y in removed or y in dist:
                    continue
                dist[y] = dist[x] + 1
                q.append(y)
        return dist

    def coupled(self, allo, active, removed=()):
        return active in self.propagate(allo, removed)

    def pathway(self, allo, active, removed=()):
        """Shortest allosteric path allo → active (the residues that carry the signal), or [] if uncoupled."""
        removed = set(removed)
        if allo in removed or active in removed:
            return []
        prev, q = {allo: None}, deque([allo])
        while q:
            x = q.popleft()
            if x == active:
                p = [active]
                while prev[p[-1]] is not None:
                    p.append(prev[p[-1]])
                return p[::-1]
            for y in self.adj.get(x, ()):
                if y in removed or y in prev:
                    continue
                prev[y] = x
                q.append(y)
        return []

    def mediators(self, allo, active):
        """Residues whose KNOCKOUT disconnects allo from active — the essential transmitters. These are the
        allosteric-uncoupling mutations / candidate drug sites. (= criticality / single points of failure.)"""
        if not self.coupled(allo, active):
            return []
        return sorted(r for r in self.residues
                      if r not in (allo, active) and not self.coupled(allo, active, removed=(r,)))


# --- a small demo protein: two input paths converge on a HINGE, then one route to the active site ---
#   allo_site ─▶ r1 ─▶ r2 ─┐
#                          ├─▶ hinge ─▶ r3 ─▶ active_site
#   allo_site ─▶ s1 ───────┘
#   (decoy1, decoy2: surface residues off the pathway — show Potential ⊇ Actual)
DEMO = Protein(
    residues=["allo_site", "r1", "r2", "s1", "hinge", "r3", "active_site", "decoy1", "decoy2"],
    contacts=[("allo_site", "r1"), ("r1", "r2"), ("r2", "hinge"),
              ("allo_site", "s1"), ("s1", "hinge"),
              ("hinge", "r3"), ("r3", "active_site"),
              ("decoy1", "decoy2")],            # decoys: a separate little patch, never reached from allo_site
)


def main():
    p = DEMO
    print("allostery.py — Phase 16: allosteric mapping as reach over a residue coupling graph\n")
    wave = p.propagate("allo_site")
    print(f"  perturb allo_site → signal reaches {len(wave)} of {len(p.residues)} residues "
          f"(Potential ⊇ Actual; decoys untouched: {[r for r in p.residues if r not in wave]})")
    path = p.pathway("allo_site", "active_site")
    print(f"  allosteric pathway: {' → '.join(path)}")
    med = p.mediators("allo_site", "active_site")
    print(f"  essential mediator residues (knockout uncouples allostery): {med}")
    print("\n  mutation experiments:")
    for r in ["hinge", "r2"]:
        still = p.coupled("allo_site", "active_site", removed=(r,))
        print(f"    knock out {r:>6}: allosteric coupling {'PRESERVED' if still else 'ABOLISHED'} "
              f"({'redundant residue' if still else 'essential mediator — a drug target / uncoupling mutation'})")
    print("\n  the protein is a causal world: a perturbation propagates by coupling; the active site changes")
    print("  because the graph carries the signal — not because anything edited the active site directly.")
    print("  NOT claimed: molecular dynamics, energetics, real conformational change. graph-reach ≠ free-energy.")


if __name__ == "__main__":
    main()
