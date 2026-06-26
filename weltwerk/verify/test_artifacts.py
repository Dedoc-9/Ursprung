# SPDX-License-Identifier: AGPL-3.0-only
"""
test_artifacts.py — Phase A.2 Step 4 proofs (validity-not-outcome): verification outputs are durable,
reusable, and honest artifacts — with NO behavior change to the engine.

  1. trace_replay_equivalent     — Trace.events == the witness; replay reproduces terminal_state; frozen
  2. trace_length_invariant      — len(events) == length-1 is enforced (bad construction raises)
  3. invariant_is_value_type     — Invariant carries name/predicate/explanation/severity; normalize wraps
  4. invariant_promotion_safe    — Invariant objects vs bare predicates give identical results
  5. violation_metadata + label≠control — Violations carry explanation/severity; severity changes nothing
  6. certificate_only_on_closed  — CLOSED has a certificate; BOUNDED/VIOLATED do not (no fake proofs)
  7. certificate_verifies        — certificate.verify re-derives the facts; rejects a different run
  8. contract_carries_artifacts  — VerificationResult exposes certificate (CLOSED) and trace (VIOLATED)

Run:  python3 test_artifacts.py
"""
from __future__ import annotations

import dataclasses

from artifacts import Trace, Invariant, Violation, ReachabilityCertificate, normalize_invariants
from engine import build_model, ExplicitStateBFSEngine, VerificationOptions
from kernel_check import check, replay_path, DEFAULT_INVARIANTS

SMALL = """
world "T"
entity faction_a:
  position 0 0 0
  controls hub
entity hub:
  position 1 0 0
  health 10
  powers leaf
entity leaf:
  position 2 0 0
  health 10
"""

NEVER_DESTROYED = {"nothing_ever_destroyed":
                   Invariant("nothing_ever_destroyed",
                             lambda sim: all(sim.runtime[e]["alive"] for e in sim.runtime),
                             "No entity may ever be destroyed.", "critical")}


def chk(name, ok, detail):
    return (name, ok, detail)


def test_trace_replay_equivalent():
    r = check(SMALL, max_depth=3, invariants=NEVER_DESTROYED)
    tr = r.trace
    ok = (isinstance(tr, Trace) and tr.events == tuple(r.ghost.path)
          and replay_path(SMALL, list(tr.events)) == tr.terminal_state)
    try:
        tr.length = 0
        frozen = False
    except dataclasses.FrozenInstanceError:
        frozen = True
    return chk("trace_replay_equivalent", ok and frozen,
               f"events match witness + replay→terminal: {ok}; frozen: {frozen}")


def test_trace_length_invariant():
    raised = False
    try:
        Trace(events=(("destroy", "hub"),), states=("s0", "s1"), length=5, terminal_state="s1")
    except ValueError:
        raised = True
    good = check(SMALL, max_depth=3, invariants=NEVER_DESTROYED).trace
    ok = raised and len(good.events) == good.length - 1
    return chk("trace_length_invariant", ok, f"bad raises={raised}; good len(events)==length-1={len(good.events) == good.length - 1}")


def test_invariant_is_value_type():
    inv = Invariant("x", lambda s: True, "why", "critical")
    norm = normalize_invariants({"a": (lambda s: True), "b": inv})
    ok = (inv.explanation == "why" and inv.severity == "critical"
          and isinstance(norm["a"], Invariant) and norm["b"] is inv and norm["a"].name == "a")
    return chk("invariant_is_value_type", ok, f"wraps bare + passes Invariant through: {ok}")


def test_invariant_promotion_safe():
    bare = {name: inv.predicate for name, inv in DEFAULT_INVARIANTS.items()}
    r1 = check(SMALL, max_depth=8)                       # DEFAULT_INVARIANTS (Invariant objects)
    r2 = check(SMALL, max_depth=8, invariants=bare)      # equivalent bare predicates
    ok = ((r1.status, r1.states_explored, len(r1.violations))
          == (r2.status, r2.states_explored, len(r2.violations)))
    return chk("invariant_promotion_safe", ok, f"Invariant vs bare identical: {ok}")


def test_violation_metadata_and_label_not_control():
    crit = {"always_false": Invariant("always_false", lambda s: False, "fails by design", "critical")}
    triv = {"always_false": Invariant("always_false", lambda s: False, "fails by design", "trivial")}
    rc = check(SMALL, max_depth=1, invariants=crit)
    rt = check(SMALL, max_depth=1, invariants=triv)
    g = rc.ghost
    ok = (g.explanation == "fails by design" and g.severity == "critical"
          and rc.status == rt.status == "VIOLATED")          # severity changed nothing → label ≠ control
    return chk("violation_metadata_and_label_not_control", ok,
               f"explanation/severity carried={g.explanation!r}/{g.severity!r}; severity inert={rc.status == rt.status}")


def test_certificate_only_on_closed():
    closed = check(SMALL, max_depth=8)
    bounded = check(SMALL, max_depth=1)
    violated = check(SMALL, max_depth=3, invariants=NEVER_DESTROYED)
    ok = (isinstance(closed.certificate, ReachabilityCertificate)
          and bounded.certificate is None and violated.certificate is None)
    return chk("certificate_only_on_closed", ok,
               f"CLOSED has cert={closed.certificate is not None}, BOUNDED/VIOLATED none")


def test_certificate_verifies():
    model = build_model(SMALL)
    opts = VerificationOptions(depth_bound=8)
    r = ExplicitStateBFSEngine().run(model, opts)
    cert = r.certificate
    reproduces = cert.verify(model, opts)
    rejects = cert.verify(model, VerificationOptions(depth_bound=1))   # different run ⇒ no matching cert
    facts = (len(cert.explored_state_sigs) == r.states_explored
             and cert.transition_count == r.transitions
             and cert.invariant_names == tuple(sorted(DEFAULT_INVARIANTS)))
    ok = reproduces and not rejects and facts
    return chk("certificate_verifies", ok, f"reproduces={reproduces} rejects-other={not rejects} facts={facts}")


def test_contract_carries_artifacts():
    eng = ExplicitStateBFSEngine()
    vr_closed = eng.verify(build_model(SMALL), VerificationOptions(depth_bound=8))
    vr_viol = eng.verify(build_model(SMALL, invariants=NEVER_DESTROYED), VerificationOptions(depth_bound=3))
    ok = (vr_closed.certificate is not None and vr_closed.trace is None
          and vr_viol.certificate is None and isinstance(vr_viol.trace, Trace))
    return chk("contract_carries_artifacts", ok,
               f"CLOSED→certificate, VIOLATED→trace through the contract: {ok}")


def main():
    results = [
        test_trace_replay_equivalent(),
        test_trace_length_invariant(),
        test_invariant_is_value_type(),
        test_invariant_promotion_safe(),
        test_violation_metadata_and_label_not_control(),
        test_certificate_only_on_closed(),
        test_certificate_verifies(),
        test_contract_carries_artifacts(),
    ]
    print("test_artifacts — Phase A.2 Step 4: durable verification artifacts (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:36s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: Trace is immutable and replay-equivalent, "
          f"the\n  length invariant is enforced, Invariant promotion changes no evaluation, severity is inert "
          f"(label ≠\n  control), only CLOSED carries a (re-derivable) certificate, and the public contract "
          f"exposes both\n  artifacts. Outputs got richer; the engine did not change. additive ≠ breaking.")
    assert passed == total, f"{total - passed} check(s) failed — artifacts are not sound"


if __name__ == "__main__":
    main()
