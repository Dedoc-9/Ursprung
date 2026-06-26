# SPDX-License-Identifier: AGPL-3.0-only
"""
pdb_rin.py — Phase 17: real PDB structure → residue interaction network (RIN).

Step 1 of an *evaluation framework* for graph-based allostery hypotheses. This parses a real PDB file
(no Biopython dependency — fixed-column ATOM records) into a contact graph: one node per residue at its
Cβ (Cα for glycine / missing Cβ), an undirected edge when two residues' representative atoms are within a
cutoff (default 8 Å), skipping trivial sequence neighbours (|Δresseq| ≥ 2). This is the standard RIN
construction used across the structural-allostery literature — claimed as established method, not novel.

`contact ≠ coupling`: a spatial contact graph is a *model* of which residues could communicate; it is not
measured energetic or dynamic coupling. It is the input a hypothesis is built on, and the thing the
evaluation harness then holds accountable against experiment.
"""
from __future__ import annotations

import math


def _atom_line(serial, atom, res, chain, resi, x, y, z):
    """Build a column-correct PDB ATOM record (used only for the synthetic self-test fixture)."""
    return (f"ATOM  {serial:>5} {atom:<4} {res:>3} {chain}{resi:>4}    "
            f"{x:>8.3f}{y:>8.3f}{z:>8.3f}  1.00  0.00           C")


def parse_pdb(text: str):
    """Parse ATOM records → ordered list of residues [{chain, resi, resname, atom, xyz}]. One representative
    coord per residue: Cβ if present, else Cα. Column-based (robust to whitespace in real PDBs)."""
    best = {}          # (chain,resi) -> {resname, ca, cb, order}
    order = 0
    for ln in text.splitlines():
        if not ln.startswith(("ATOM", "HETATM")):
            continue
        try:
            atom = ln[12:16].strip()
            res = ln[17:20].strip()
            chain = ln[21]
            resi = int(ln[22:26])
            x, y, z = float(ln[30:38]), float(ln[38:46]), float(ln[46:54])
        except (ValueError, IndexError):
            continue
        key = (chain, resi)
        if key not in best:
            best[key] = {"chain": chain, "resi": resi, "resname": res, "ca": None, "cb": None, "order": order}
            order += 1
        if atom == "CA":
            best[key]["ca"] = (x, y, z)
        elif atom == "CB":
            best[key]["cb"] = (x, y, z)
    residues = []
    for v in sorted(best.values(), key=lambda d: d["order"]):
        xyz = v["cb"] or v["ca"]
        if xyz is None:
            continue
        residues.append({"chain": v["chain"], "resi": v["resi"], "resname": v["resname"],
                         "label": f"{v['resname']}{v['resi']}", "xyz": xyz})
    return residues


def contact_map(residues, cutoff: float = 8.0, seq_sep: int = 2):
    """Undirected edges (i, j) where the representative atoms are within `cutoff` Å and the residues are at
    least `seq_sep` apart in sequence (skip trivial backbone neighbours). Indices into `residues`."""
    edges = set()
    n = len(residues)
    cut2 = cutoff * cutoff
    for i in range(n):
        xi, yi, zi = residues[i]["xyz"]
        ci, ri = residues[i]["chain"], residues[i]["resi"]
        for j in range(i + 1, n):
            if residues[j]["chain"] == ci and abs(residues[j]["resi"] - ri) < seq_sep:
                continue
            xj, yj, zj = residues[j]["xyz"]
            d2 = (xi - xj) ** 2 + (yi - yj) ** 2 + (zi - zj) ** 2
            if d2 <= cut2:
                edges.add((i, j))
    return edges


def build_rin(text: str, cutoff: float = 8.0):
    """PDB text → {residues, adj (undirected, by label), labels, edges(by index)}."""
    residues = parse_pdb(text)
    edges = contact_map(residues, cutoff)
    labels = [r["label"] for r in residues]
    adj = {lab: [] for lab in labels}
    for i, j in edges:
        adj[labels[i]].append(labels[j])
        adj[labels[j]].append(labels[i])
    return {"residues": residues, "adj": adj, "labels": labels, "edges": edges}


def synthetic_pdb():
    """A 6-residue β-hairpin micro-structure (NOT a real protein — a deterministic fixture for the parser).
    Two strands so cross-strand residues contact (r1–r6, r2–r5, r3–r4 ~5 Å); ends are far apart."""
    coords = [("ALA", 1, 0.0, 0.0, 0.0), ("VAL", 2, 5.0, 0.0, 0.0), ("LEU", 3, 10.0, 0.0, 0.0),
              ("LEU", 4, 10.0, 5.0, 0.0), ("VAL", 5, 5.0, 5.0, 0.0), ("ALA", 6, 0.0, 5.0, 0.0)]
    return "\n".join(_atom_line(i + 1, "CB", res, "A", resi, x, y, z)
                     for i, (res, resi, x, y, z) in enumerate(coords)) + "\nEND\n"


def main():
    print("pdb_rin.py — Phase 17: PDB structure → residue interaction network\n")
    rin = build_rin(synthetic_pdb())
    print(f"  parsed {len(rin['residues'])} residues; {len(rin['edges'])} contacts (≤8 Å, seq-sep ≥2)")
    print(f"  residues: {rin['labels']}")
    for lab in rin["labels"]:
        print(f"    {lab:>6} contacts: {sorted(rin['adj'][lab])}")
    print("\n  drop a REAL .pdb into build_rin(open('file.pdb').read()) — same construction, real coordinates.")
    print("  contact ≠ coupling: this is the model's input, not measured energetic coupling.")


if __name__ == "__main__":
    main()
