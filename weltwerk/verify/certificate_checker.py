# SPDX-License-Identifier: AGPL-3.0-only
"""
certificate_checker.py — Proof Obligation PO-8: an INDEPENDENT checker that validates a CLOSED
`ReachabilityCertificate` WITHOUT re-running the search.

Today `ReachabilityCertificate.verify()` re-runs the engine — as expensive as proving, and not independent.
This checker instead verifies the *inductive-invariant* property directly:

  **Theorem (Certificate Soundness).** Let `S` be the certificate's recorded state set. If
    (1) the initial state ∈ S,
    (2) every invariant holds on every state in S, and
    (3) S is closed under the transition relation (every successor of every s ∈ S is in S),
  then the reachable set ⊆ S and no reachable state violates an invariant — so `CLOSED` is justified
  *independently of the engine that produced the certificate*.

Proof sketch: (1)+(3) make S a superset of the reachable set (induction on path length: init ∈ S, and S is
closed under successors). (2) gives invariants on all of S, hence on the reachable subset. ∎

The checker runs no BFS/queue/visited logic — it checks a local property of each recorded state. It shares
only *canonicalization* (`_sig`) and the *alphabet* and the *semantics* (`apply_event`) — the specs both the
prover and an auditor must obey — never the engine's search. `checker ≠ prover`; `re-run ≠ independent-check`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sim"))
from world_sim import WorldSim                                          # noqa: E402
from kernel_check import _sig, _snapshot_state, _restore_state, build_alphabet   # noqa: E402  (specs, not search)
from artifacts import normalize_invariants                             # noqa: E402


def check_certificate(world_text, invariants, cert) -> bool:
    """Independently validate a CLOSED ReachabilityCertificate. True iff init∈S, invariants hold on all of S,
    and S is closed under the transition relation. No search is performed."""
    if cert is None or getattr(cert, "status", None) != "CLOSED":
        return False
    invs = normalize_invariants(invariants)
    base = WorldSim(world_text)
    max_h = {k: base.runtime[k]["max"] for k in base.cg.nodes}
    alphabet = build_alphabet(base)
    S = set(cert.explored_state_sigs)

    # (1) init ∈ S
    if _sig(_snapshot_state(WorldSim(world_text))) not in S:
        return False

    for sig in S:
        runtime = {k: {"alive": a, "status": s, "health": h, "max": max_h.get(k, h)}
                   for (k, a, s, h) in sig[0]}
        st = (runtime, dict(sig[1]))

        # (2) invariants hold on this recorded state
        _restore_state(base, st)
        for _name, inv in invs.items():
            try:
                ok = inv.predicate(base)
            except Exception:
                ok = False
            if not ok:
                return False

        # (3) closure: every successor is also recorded
        for act in alphabet:
            _restore_state(base, st)
            try:
                base.apply_event(*act)
            except Exception:
                continue
            if _sig(_snapshot_state(base)) not in S:
                return False

    return True


def main():
    from kernel_check import check, DEFAULT_INVARIANTS
    small = ('world "T"\n'
             'entity faction_a:\n  position 0 0 0\n  controls hub\n'
             'entity hub:\n  position 1 0 0\n  health 10\n  powers leaf\n'
             'entity leaf:\n  position 2 0 0\n  health 10\n')
    print("certificate_checker.py — PO-8: independent (no-search) certificate validation\n")
    cert = check(small, max_depth=12).certificate
    print(f"  CLOSED certificate present: {cert is not None}")
    print(f"  independent check_certificate: {check_certificate(small, DEFAULT_INVARIANTS, cert)}")
    print("  A valid certificate is now an auditable proof object, not a re-run of the prover.")


if __name__ == "__main__":
    main()
