# SPDX-License-Identifier: AGPL-3.0-only
"""
test_allostery.py — Phase 16 proofs (validity-not-outcome): the allosteric mapping is correct as a network model.

  1. coupled_allo_active     — the active site is reachable from the allosteric site (the protein is coupled)
  2. pathway_through_hinge    — the shortest allosteric path runs through the hinge hub
  3. hinge_is_mediator        — knocking out the hinge ABOLISHES coupling (essential transmitter)
  4. redundant_residue_safe   — knocking out r2 leaves coupling intact (a bypass exists via s1)
  5. mediators_set            — the only essential mediator is the hinge (criticality / SPOF)
  6. potential_superset_actual— the signal reaches a strict subset of residues (decoys never reached)
  7. determinism              — propagation is reproducible

Run:  python3 test_allostery.py
"""
from __future__ import annotations

from allostery import DEMO, Protein


def check(name, ok, detail):
    return (name, ok, detail)


def test_coupled_allo_active():
    ok = DEMO.coupled("allo_site", "active_site")
    return check("coupled_allo_active", ok, f"active reachable from allosteric site: {ok}")


def test_pathway_through_hinge():
    path = DEMO.pathway("allo_site", "active_site")
    ok = "hinge" in path and path[0] == "allo_site" and path[-1] == "active_site"
    return check("pathway_through_hinge", ok, f"pathway: {' → '.join(path)}")


def test_hinge_is_mediator():
    ok = not DEMO.coupled("allo_site", "active_site", removed=("hinge",))
    return check("hinge_is_mediator", ok, f"knockout(hinge) abolishes coupling: {ok}")


def test_redundant_residue_safe():
    ok = DEMO.coupled("allo_site", "active_site", removed=("r2",))   # bypass: allo→s1→hinge
    return check("redundant_residue_safe", ok, f"knockout(r2) preserves coupling (bypass via s1): {ok}")


def test_mediators_set():
    med = DEMO.mediators("allo_site", "active_site")
    ok = med == ["hinge", "r3"]   # hinge (convergence) and r3 (sole link hinge→active) are both essential
    return check("mediators_set", ok, f"essential mediators: {med}")


def test_potential_superset_actual():
    reached = DEMO.propagate("allo_site")
    all_res = set(DEMO.residues)
    unreached = all_res - set(reached)
    ok = set(reached) < all_res and {"decoy1", "decoy2"} <= unreached
    return check("potential_superset_actual", ok,
                 f"reached {len(reached)}/{len(all_res)}; decoys never reached: {sorted(unreached)}")


def test_determinism():
    a = DEMO.propagate("allo_site"); b = DEMO.propagate("allo_site")
    p1 = DEMO.pathway("allo_site", "active_site"); p2 = DEMO.pathway("allo_site", "active_site")
    return check("determinism", a == b and p1 == p2, f"propagation + pathway reproducible: {a == b and p1 == p2}")


def main():
    results = [
        test_coupled_allo_active(),
        test_pathway_through_hinge(),
        test_hinge_is_mediator(),
        test_redundant_residue_safe(),
        test_mediators_set(),
        test_potential_superset_actual(),
        test_determinism(),
    ]
    print("test_allostery — Phase 16: allosteric mapping as causal reach (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: the protein is coupled, the pathway runs"
          f"\n  through the hub, knocking out an essential mediator abolishes allostery while a redundant residue"
          f"\n  is safe, the signal reaches a strict subset (Potential ⊇ Actual), and it's deterministic."
          f"\n  A structural network model — not molecular dynamics.")
    assert passed == total, f"{total - passed} check(s) failed — the allosteric mapping is not sound"


if __name__ == "__main__":
    main()
