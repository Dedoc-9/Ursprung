# SPDX-License-Identifier: AGPL-3.0-only
"""
test_epistemic_types.py — the epistemic type system refuses ungrounded synthesis (validity-not-outcome).

  1. ground_valid          — a value with a grounded proof constructs; its raw value is accessible.
  2. ground_invalid_raises — a value with an ungrounded proof raises UngroundedError (no bypass, even by direct
                            dataclass construction).
  3. gate_blocks_raw       — a @require_grounded applier raises on a raw value BEFORE its body runs (no state
                            transition), and runs only on a Grounded value.
  4. adapters_map_artifacts— EngineClosed(CLOSED)/SupportedClaim(ESTABLISHED)/ChannelEstablished(stable) ground;
                            their negatives do not. The proof reflects the verifier's verdict, nothing else.
  5. synthesis_gate        — a mixed candidate stream yields Grounded only for grounded ones; the ungrounded
                            never become Grounded (so can never reach an applier). The compiler rejects them.
  6. as_analysis_honest    — a Grounded value projects to an AnalysisResult with scope + ≥1 limitation.

Sound iff 6/6: a value cannot be grounded — or applied — without a verifier-issued proof; ungrounded synthesis
fails before any transition. The type forbids ungrounded states; it grants no new authority. `grounded ≠ true`.

Run:  python3 test_epistemic_types.py
"""
from __future__ import annotations

from epistemic_types import (Grounded, Grounding, UngroundedError, require_grounded, synthesize_gate,
                             EngineClosed, SupportedClaim, ChannelEstablished, Attested)
from artifacts import AnalysisResult, Limitation


class _Cert:
    def __init__(self, status): self.status = status


class _Claim:
    def __init__(self, grade): self.grade = grade


class _RCR:
    def __init__(self, decision): self.decision = decision


def chk(name, ok, detail):
    return (name, ok, detail)


def test_ground_valid():
    g = Grounded.ground("action", Attested(True, "ok"))
    ok = g.value == "action" and g.proof.is_grounded()
    return chk("ground_valid", ok, f"value={g.value!r} grounded={g.proof.is_grounded()}")


def test_ground_invalid_raises():
    raised_factory = raised_direct = False
    try:
        Grounded.ground("action", Attested(False, "ungrounded"))
    except UngroundedError:
        raised_factory = True
    try:
        Grounded("action", Attested(False))          # direct construction must ALSO be gated (no bypass)
    except UngroundedError:
        raised_direct = True
    return chk("ground_invalid_raises", raised_factory and raised_direct,
               f"factory_raised={raised_factory}, direct_raised={raised_direct}")


def test_gate_blocks_raw():
    log = []

    @require_grounded("action")
    def apply_action(action, log):
        log.append(action.value)
        return True

    raised = False
    try:
        apply_action(action="raw", log=log)          # raw value: must raise BEFORE body
    except UngroundedError:
        raised = True
    ran = apply_action(action=Grounded.ground("ok", Attested(True)), log=log)
    ok = raised and ran is True and log == ["ok"]      # only the grounded action caused a 'transition'
    return chk("gate_blocks_raw", ok, f"raw_blocked={raised}; grounded_ran={ran}; log={log}")


def test_adapters_map_artifacts():
    pos = (EngineClosed(_Cert("CLOSED")).is_grounded()
           and SupportedClaim(_Claim("ESTABLISHED")).is_grounded()
           and ChannelEstablished(_RCR("RESIDUAL_MISSPEC_STABLE")).is_grounded())
    neg = (not EngineClosed(_Cert("VIOLATED")).is_grounded()
           and not SupportedClaim(_Claim("SPECULATIVE")).is_grounded()
           and not ChannelEstablished(_RCR("CONSISTENT_WITH_NULL")).is_grounded())
    return chk("adapters_map_artifacts", pos and neg, f"positives_ground={pos}; negatives_reject={neg}")


def test_synthesis_gate():
    candidates = [("a", _Cert("CLOSED")), ("b", _Cert("VIOLATED")), ("c", _Cert("CLOSED"))]
    accepted, rejected = synthesize_gate(candidates, EngineClosed)
    ok = ([g.value for g in accepted] == ["a", "c"] and [v for v, _why in rejected] == ["b"]
          and all(isinstance(g, Grounded) for g in accepted))
    return chk("synthesis_gate", ok, f"accepted={[g.value for g in accepted]} rejected={[v for v,_ in rejected]}")


def test_as_analysis_honest():
    a = Grounded.ground("x", Attested(True, "engine=CLOSED")).as_analysis()
    ok = (isinstance(a, AnalysisResult) and a.scope and len(a.limitations) >= 1
          and all(isinstance(l, Limitation) and l.scope and l.claim for l in a.limitations))
    return chk("as_analysis_honest", ok, f"scope={a.scope!r} limitations={len(a.limitations)}")


def main():
    results = [
        test_ground_valid(),
        test_ground_invalid_raises(),
        test_gate_blocks_raw(),
        test_adapters_map_artifacts(),
        test_synthesis_gate(),
        test_as_analysis_honest(),
    ]
    print("test_epistemic_types — Grounded[T] forbids ungrounded synthesis\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: a value cannot be grounded or applied without "
          f"a verifier-\n  issued proof; ungrounded synthesis fails before any state transition; the type grants "
          f"no authority.\n  grounded ≠ true; improved_map ≠ changed_criterion.")
    assert passed == total, f"{total - passed} check(s) failed — epistemic gate not enforced"


if __name__ == "__main__":
    main()
