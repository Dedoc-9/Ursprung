# SPDX-License-Identifier: AGPL-3.0-only
"""
certificate_compiler.py — Leap 1 / Branch B: the inductive `ConstraintCertificate` and a no-search 1-step
inductiveness checker. A *compact algebraic reason* a bad state is unreachable, checkable WITHOUT computing the
reachable set.

The explicit `ReachabilityCertificate` (PO-8) records the whole reachable set, so checking it costs about what
producing it did. An inductive invariant `Inv` is different: if it satisfies the three local conditions

    C1   Init ⊆ Inv                         (initiation)
    C2   Inv ∧ T ⊆ Inv′   (i.e. ∀ s∈Inv, ∀ s′∈T(s): s′∈Inv)   (consecution / closed under T)
    C3   Inv ⊆ Safe                         (safety)

then `reachable ⊆ Inv ⊆ Safe`, so the system is safe — proven by a single inductive pass, with NO fixpoint
iteration, NO frontier/queue, and NO path reconstruction. Producing a certificate is search; CHECKING a given
one is one pass. `verify ≠ prove`.

HONEST GRADING (no overclaim — this is the whole point of the repo):
  • The checker + the 1-step soundness argument: **DEMONSTRATED** (this file, pure-stdlib, tested).
  • AUTO-DERIVING a good `Inv` from the relation: **PLAUSIBLE-BUT-UNVERIFIED** — NOT implemented here. A user
    supplies `Inv`; we only check it. `checking ≠ finding`.
  • The size-INDEPENDENT asymmetry (one solver query for C2 over the transition RULE, independent of
    |reachable|): **DEMONSTRATED-ACHIEVABLE via the optional z3 path** (`solver_adapter.py`), NOT in this
    pure-stdlib file. Here C2/C3 are checked over a supplied finite `universe`, so the cost is comparable to
    BFS — the same honest caveat the explicit certificate carries. `pure-stdlib-check ≠ size-independent`.

Cross-check (PO-4 style): `cross_check` independently computes the reachable set and confirms `reachable ⊆ Inv`
and all-reachable-safe, so a certificate that fails to cover a reachable state, or admits an unsafe one, is
caught. A failing check returns a MINIMAL REASON (which condition + a witness state) — an unsat-core-style
diagnostic. `integrity ≠ truth`; `holds-here ≠ true`.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Tuple


@dataclass(frozen=True)
class ConstraintCertificate:
    """A compact algebraic reason: a predicate invariant `inv`, the safety predicate `safe`, and a
    human/audit `reason`. Checked by 1-step inductiveness — no reachable set required to state it."""
    name: str
    inv: Callable[[Any], bool]
    safe: Callable[[Any], bool]
    reason: str = ""


@dataclass(frozen=True)
class InductiveResult:
    valid: bool
    c1_initiation: bool
    c2_consecution: bool
    c3_safety: bool
    failing_condition: Optional[str]      # None | "C1_init_not_in_inv" | "C2_not_closed" | "C3_inv_not_safe"
    witness: Any                          # the state (C1/C3) or (s, s') edge (C2) that breaks it
    inv_states_checked: int


def check_certificate(init_states: Iterable, successors: Callable, universe: Iterable,
                      cert: ConstraintCertificate) -> InductiveResult:
    """Verify C1/C2/C3 by a single inductive pass over `universe` (the finite carrier for this pure-stdlib
    check). No reachability search, no fixpoint. Returns the first violated condition + a witness, if any."""
    inits = list(init_states)
    c1 = all(cert.inv(s) for s in inits)
    c1_witness = next((s for s in inits if not cert.inv(s)), None)

    c2 = True
    c3 = True
    c2_witness = c3_witness = None
    checked = 0
    for s in universe:
        if not cert.inv(s):
            continue
        checked += 1
        if c3 and not cert.safe(s):
            c3, c3_witness = False, s
        if c2:
            for t in successors(s):
                if not cert.inv(t):
                    c2, c2_witness = False, (s, t)
                    break

    valid = c1 and c2 and c3
    failing, witness = None, None
    if not c1:
        failing, witness = "C1_init_not_in_inv", c1_witness
    elif not c2:
        failing, witness = "C2_not_closed", c2_witness
    elif not c3:
        failing, witness = "C3_inv_not_safe", c3_witness
    return InductiveResult(valid, c1, c2, c3, failing, witness, checked)


def bfs_reachable(init_states: Iterable, successors: Callable) -> Tuple[frozenset, int]:
    """Independent ground truth: the reachable set by fixpoint BFS, plus the number of state-expansions
    (the cost a producer pays — contrast with the single pass `check_certificate` makes)."""
    seen = set(init_states)
    q = deque(seen)
    expansions = 0
    while q:
        s = q.popleft()
        expansions += 1
        for t in successors(s):
            if t not in seen:
                seen.add(t)
                q.append(t)
    return frozenset(seen), expansions


def cross_check(init_states: Iterable, successors: Callable, cert: ConstraintCertificate) -> dict:
    """PO-4-style independent validation: does the inductive certificate actually cover the real reachable set,
    and is that set safe? Catches a cert that excludes a reachable state or admits an unsafe one."""
    reachable, _ = bfs_reachable(init_states, successors)
    subset = all(cert.inv(s) for s in reachable)
    safe = all(cert.safe(s) for s in reachable)
    return {"reachable_subset_of_inv": subset, "all_reachable_safe": safe, "reachable_count": len(reachable)}


def minimal_reason(result: InductiveResult) -> str:
    """An unsat-core-style compact reason a certificate failed (or why it holds)."""
    if result.valid:
        return "valid: Init ⊆ Inv ∧ Inv closed under T ∧ Inv ⊆ Safe ⇒ reachable ⊆ Safe (no search)"
    table = {
        "C1_init_not_in_inv": f"C1 fails: initial state {result.witness!r} ∉ Inv",
        "C2_not_closed": f"C2 fails: edge {result.witness!r} leaves Inv (Inv not closed under T)",
        "C3_inv_not_safe": f"C3 fails: state {result.witness!r} ∈ Inv but ∉ Safe",
    }
    return table.get(result.failing_condition, "unknown failure")


# ---- a small transparent demo domain: a length-N chain 0→1→…→N -----------------------------------
def chain(n: int):
    init = [0]
    universe = list(range(n + 1))
    succ = lambda i: ([i + 1] if i < n else [])
    return init, succ, universe


def main():
    print("certificate_compiler.py — Leap 1: inductive ConstraintCertificate (no-search 1-step check)\n")
    n = 6
    init, succ, universe = chain(n)

    good = ConstraintCertificate("in_range", lambda i: 0 <= i <= n, lambda i: i != n + 99,
                                 reason="0≤i≤n is closed under i→i+1 (capped at n) and never hits the bad state")
    r = check_certificate(init, succ, universe, good)
    print(f"  GOOD cert : valid={r.valid}  C1={r.c1_initiation} C2={r.c2_consecution} C3={r.c3_safety}  "
          f"checked={r.inv_states_checked} states (one pass)")
    print(f"            : {minimal_reason(r)}")
    print(f"            : cross-check {cross_check(init, succ, good)}")

    tight = ConstraintCertificate("too_tight", lambda i: i <= 2, lambda i: True,
                                  reason="i≤2 is NOT closed: 2→3 escapes")
    r2 = check_certificate(init, succ, universe, tight)
    print(f"  TIGHT cert: valid={r2.valid}  → {minimal_reason(r2)}")

    # honest cost note: pure-stdlib check scans the universe, so cost ~ BFS here; size-independence needs z3.
    _, exp = bfs_reachable(init, succ)
    print(f"\n  cost: BFS expansions={exp} (fixpoint) vs inductive pass touched={r.inv_states_checked} (one pass,"
          f" no queue/paths).")
    print("  size-INDEPENDENT C2 (one query over the transition RULE) is the z3 path — DEMONSTRATED-ACHIEVABLE,")
    print("  not in this pure-stdlib file. Auto-deriving Inv is PLAUSIBLE-UNVERIFIED (a user supplies it). verify ≠ prove.")


if __name__ == "__main__":
    main()
