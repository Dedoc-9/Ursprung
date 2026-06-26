# SPDX-License-Identifier: AGPL-3.0-only
"""
test_transition.py — Phase A.2 Step 2 proofs (validity-not-outcome): the extracted relation T(s,a,s')
preserves the reference engine's meaning exactly.

  1. record_shape             — Transition has source/action/target; Action has kind/target
  2. action_is_value          — Action is a frozen, comparable, hashable value
  3. deterministic_order      — actions() and successors() return a stable order across calls
  4. successors_match_legacy  — per-state, T's (action, target) set equals the legacy inline successors
  5. reachable_graph_matches  — BFS over T reaches exactly the legacy reachable state set
  6. step_matches_successor   — step(s, a).target equals the successor produced for a in successors(s)
  7. records_are_frozen       — State / Transition are immutable
  8. determinism_across_inst  — two relations from the same world give identical initial successors

Run:  python3 test_transition.py
"""
from __future__ import annotations

import dataclasses

from transition import Action, State, Transition, TransitionRelation
from kernel_check import WorldSim, build_alphabet, _snapshot_state, _restore_state, _sig

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


def _norm_tuple(t):
    """Normalize a build_alphabet tuple to (kind, target, amount, faction) for comparison."""
    return (t[0], t[1], t[2] if len(t) > 2 else 0, t[3] if len(t) > 3 else "")


def _norm_action(a: Action):
    return (a.kind, a.target, a.amount, a.faction)


def legacy_successors(world_text, snapshot):
    """The reference engine's inline successor computation, reproduced independently for differential check."""
    base = WorldSim(world_text)
    out = []
    for a in build_alphabet(base):
        _restore_state(base, snapshot)
        try:
            base.apply_event(*a)
        except Exception:
            continue
        out.append((_norm_tuple(a), _sig(_snapshot_state(base))))
    return set(out)


def legacy_reachable(world_text):
    base = WorldSim(world_text)
    alpha = build_alphabet(base)
    init = _snapshot_state(base)
    seen, stack = {_sig(init)}, [init]
    while stack:
        st = stack.pop()
        for a in alpha:
            _restore_state(base, st)
            try:
                base.apply_event(*a)
            except Exception:
                continue
            ns = _snapshot_state(base)
            sg = _sig(ns)
            if sg not in seen:
                seen.add(sg)
                stack.append(ns)
    return seen


def relation_reachable(tr: TransitionRelation):
    s0 = tr.initial()
    seen, stack = {s0.sig}, [s0]
    while stack:
        s = stack.pop()
        for t in tr.successors(s):
            if t.target.sig not in seen:
                seen.add(t.target.sig)
                stack.append(t.target)
    return seen


def chk(name, ok, detail):
    return (name, ok, detail)


def test_record_shape():
    tr = TransitionRelation(SMALL)
    t = tr.successors(tr.initial())[0]
    ok = (isinstance(t, Transition) and isinstance(t.source, State) and isinstance(t.target, State)
          and isinstance(t.action, Action) and hasattr(t.action, "kind") and hasattr(t.action, "target"))
    return chk("record_shape", ok, f"Transition(source,action,target) with Action(kind,target): {ok}")


def test_action_is_value():
    a1 = Action("destroy", "hub")
    a2 = Action("destroy", "hub")
    ok = (a1 == a2 and hash(a1) == hash(a2) and len({a1, a2}) == 1 and a1.as_args()[0] == "destroy")
    return chk("action_is_value", ok, f"value equality + hashable: {ok}")


def test_deterministic_order():
    tr = TransitionRelation(SMALL)
    s0 = tr.initial()
    a1 = [str(a) for a in tr.actions(s0)]
    a2 = [str(a) for a in tr.actions(s0)]
    s1 = [str(t.action) for t in tr.successors(s0)]
    s2 = [str(t.action) for t in tr.successors(s0)]
    return chk("deterministic_order", a1 == a2 and s1 == s2, f"actions+successors order stable: {a1 == a2 and s1 == s2}")


def test_successors_match_legacy():
    tr = TransitionRelation(SMALL)
    mismatches = 0
    checked = 0
    # compare on initial + all reachable states discovered through the relation
    seen = {}
    s0 = tr.initial()
    frontier = [s0]
    seen[s0.sig] = s0
    while frontier:
        s = frontier.pop()
        for t in tr.successors(s):
            if t.target.sig not in seen:
                seen[t.target.sig] = t.target
                frontier.append(t.target)
    for s in seen.values():
        rel = {(_norm_action(t.action), t.target.sig) for t in tr.successors(s)}
        leg = legacy_successors(SMALL, s.snapshot)
        checked += 1
        if rel != leg:
            mismatches += 1
    return chk("successors_match_legacy", mismatches == 0,
               f"{checked} states checked, {mismatches} mismatch(es) vs legacy inline successors")


def test_reachable_graph_matches():
    tr = TransitionRelation(SMALL)
    ok = relation_reachable(tr) == legacy_reachable(SMALL)
    return chk("reachable_graph_matches", ok,
               f"relation reaches {len(relation_reachable(tr))} states == legacy {len(legacy_reachable(SMALL))}")


def test_step_matches_successor():
    tr = TransitionRelation(SMALL)
    s0 = tr.initial()
    succ = tr.successors(s0)
    a = succ[0].action
    ok = tr.step(s0, a).target.sig == succ[0].target.sig
    return chk("step_matches_successor", ok, f"step(s,a).target == successors(s)[a].target: {ok}")


def test_records_are_frozen():
    tr = TransitionRelation(SMALL)
    t = tr.successors(tr.initial())[0]
    frozen = 0
    for obj, fld, val in [(t, "action", None), (t.source, "sig", ())]:
        try:
            setattr(obj, fld, val)
        except dataclasses.FrozenInstanceError:
            frozen += 1
    return chk("records_are_frozen", frozen == 2, f"State + Transition immutable: {frozen == 2}")


def test_determinism_across_inst():
    a = TransitionRelation(SMALL)
    b = TransitionRelation(SMALL)
    sa = [(_norm_action(t.action), t.target.sig) for t in a.successors(a.initial())]
    sb = [(_norm_action(t.action), t.target.sig) for t in b.successors(b.initial())]
    return chk("determinism_across_inst", sa == sb, f"two relations agree on initial successors: {sa == sb}")


def main():
    results = [
        test_record_shape(),
        test_action_is_value(),
        test_deterministic_order(),
        test_successors_match_legacy(),
        test_reachable_graph_matches(),
        test_step_matches_successor(),
        test_records_are_frozen(),
        test_determinism_across_inst(),
    ]
    print("test_transition — Phase A.2 Step 2: extracted transition relation T(s,a,s') (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:26s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: T is a first-class record of frozen "
          f"value-typed\n  actions, generated in a deterministic order, whose per-state successors and whose "
          f"whole reachable\n  graph match the reference engine's legacy inline behavior EXACTLY — the "
          f"extraction changed no\n  meaning. relation ≠ search; extracted ≠ rewired.")
    assert passed == total, f"{total - passed} check(s) failed — the extraction changed the meaning"


if __name__ == "__main__":
    main()
