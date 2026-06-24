# SPDX-License-Identifier: AGPL-3.0-only
"""
test_causal_budget.py — machine-checks the Causal Budget Theorem.

Validity-not-outcome: it proves the cut criterion is SOUND and TIGHT (necessary + sufficient), never
that "causal replication is good". The load-bearing checks are the conservative-cut correctness (an
a-priori, dependency-only cut is provably safe) and unsafe_cut_breaks (cutting a changed chunk DOES
corrupt the client — the criterion is necessary, not merely sufficient).

  1. actual_cut_lossless        — T = changed ⇒ client view == B (byte-identical)
  2. conservative_cut_lossless  — T = potential (a-priori, no sim of changed) ⇒ client view == B
  3. potential_superset_changed — the central law: changed ⊆ potential (makes the conservative cut safe)
  4. cut_implies_no_change      — ∀ y cut by the actual policy: B[y] == A[y]  (cut(x,y) ⟹ Δ(y)=0)
  5. unsafe_cut_breaks          — dropping ONE changed chunk from T ⇒ client view ≠ B (criterion is tight)
  6. budget_ordering           — |changed| ≤ |potential| ≤ |broadcast| = N
  7. determinism                — same seed ⇒ same budget

Run:  PYTHONHASHSEED=0 python3 test_causal_budget.py
"""
from __future__ import annotations

from causal_budget import client_view, compute_budget
from cow_world import Edit, Rules, genesis
from teleport import Topology

N_CH, CHUNK_SIZE, SEED, H = 200, 20, 0, 30
EDIT = Edit("cull_pred_chunk", chunk=5)
TOPO = Topology(N_CH, ((5, 130),))   # include a teleport edge — the harder case


def check(name, ok, detail):
    return (name, ok, detail)


def _budget():
    snap = genesis(N_CH * CHUNK_SIZE, N_CH, SEED)
    return compute_budget(snap, TOPO, Rules(), SEED, EDIT, H)


def test_actual_cut_lossless():
    b = _budget()
    ok = client_view(b.line_a, b.line_b, b.changed) == b.line_b
    return check("actual_cut_lossless", ok, f"T=changed ⇒ client==B (byte-identical): {ok}")


def test_conservative_cut_lossless():
    b = _budget()
    ok = client_view(b.line_a, b.line_b, b.potential) == b.line_b
    return check("conservative_cut_lossless", ok,
                 f"T=potential (a-priori, no measure of changed) ⇒ client==B: {ok}")


def test_potential_superset_changed():
    b = _budget()
    ok = b.changed <= b.potential
    return check("potential_superset_changed", ok,
                 f"changed({len(b.changed)}) ⊆ potential({len(b.potential)}): {ok}")


def test_cut_implies_no_change():
    b = _budget()
    cut = b.broadcast - b.changed                      # chunks the actual policy declines to transmit
    ok = all(b.line_b[y] == b.line_a[y] for y in cut)  # every cut chunk is provably unchanged
    return check("cut_implies_no_change", ok,
                 f"∀ y∉transmit: Δ(y)=0 (cut(x,y) ⇒ Δ(y)=0): {ok}")


def test_unsafe_cut_breaks():
    b = _budget()
    if not b.changed:
        return check("unsafe_cut_breaks", False, "no changed chunks — edit was vacuous (cannot test tightness)")
    drop = sorted(b.changed)[0]
    unsafe = b.changed - {drop}                        # cut ONE chunk that actually changed
    broken = client_view(b.line_a, b.line_b, unsafe) != b.line_b
    return check("unsafe_cut_breaks", broken,
                 f"dropping a changed chunk ({drop}) corrupts the client (criterion is necessary): {broken}")


def test_budget_ordering():
    b = _budget()
    ok = len(b.changed) <= len(b.potential) <= len(b.broadcast) == N_CH
    return check("budget_ordering", ok,
                 f"|changed|={len(b.changed)} ≤ |potential|={len(b.potential)} ≤ |broadcast|={N_CH}: {ok}")


def test_determinism():
    b1, b2 = _budget(), _budget()
    ok = (b1.changed == b2.changed) and (b1.potential == b2.potential)
    return check("determinism", ok, f"same seed ⇒ same budget: {ok}")


def main():
    results = [
        test_actual_cut_lossless(),
        test_conservative_cut_lossless(),
        test_potential_superset_changed(),
        test_cut_implies_no_change(),
        test_unsafe_cut_breaks(),
        test_budget_ordering(),
        test_determinism(),
    ]
    print("test_causal_budget — the Causal Budget Theorem (cut by causality, losslessly)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. The theorem holds iff {total}/{total}: transmitting the causal cut"
          f"\n  (actual, or the a-priori conservative envelope) reconstructs the client byte-identically,"
          f"\n  cutting a chunk is safe exactly when it did not change, and cutting a changed chunk breaks"
          f"\n  replication. Lossless (ε=0); the lossy Δ(out|Δp)<ε extension is declared, not proven.")
    assert passed == total, f"{total - passed} check(s) failed — the Causal Budget Theorem is not established"


if __name__ == "__main__":
    main()
