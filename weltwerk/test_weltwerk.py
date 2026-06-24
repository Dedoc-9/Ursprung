# SPDX-License-Identifier: AGPL-3.0-only
"""
test_weltwerk.py — validity-not-outcome self-test for the Weltwerk slice.

DISCIPLINE (the one this project keeps re-learning): a self-test must verify that the apparatus is
VALID and the classifier is SOUND — never that reality came out the way we hoped. Nowhere does this
file assert "the intervention improved the world." It asserts:

  1. determinism / replay     — same seed ⇒ bitwise-identical trajectory; a clone resumes the same dice
  2. shadow isolation         — forking and running shadows never mutates the committed Weltlinie
  3. diff soundness           — identity ⇒ empty diff; a real edit ⇒ a detected (non-empty) diff;
                                reported deltas match an independent recomputation
  4. commit / discard         — discard leaves truth untouched; commit writes the edit at the present
                                tick and does NOT install the simulated horizon (prediction ≠ trajectory)

`experiment-ran ≠ hypothesis-confirmed`.  Run:  PYTHONHASHSEED=0 python3 test_weltwerk.py
"""
from __future__ import annotations

from fork import (cull_species, fork, identity, remove_resource, set_param)
from world import genesis


def check(name: str, ok: bool, detail: str) -> tuple[str, bool, str]:
    return (name, ok, detail)


def test_determinism_and_replay():
    a = genesis(seed=7).run(30)
    b = genesis(seed=7).run(30)
    same = a.state_hash() == b.state_hash()
    # a clone resumes the identical PRNG stream: clone-then-run == run
    base = genesis(seed=7).run(10)
    cl = base.clone()
    h_orig = genesis(seed=7).run(20).state_hash()
    h_clone = cl.run(10).state_hash()
    clone_ok = (cl.state_hash() == h_orig) and (base.state_hash() != h_orig or True)
    return check("determinism_and_replay",
                 same and clone_ok and h_clone == h_orig,
                 f"two seed-7 runs identical={same}; clone resumes same stream={clone_ok}")


def test_shadow_isolation():
    w = genesis(seed=3).run(8)
    before = w.state_hash()
    f = fork(w, cull_species("predator"), horizon=25)
    # running the shadows to completion happened inside fork(); committed must be byte-identical
    after = w.state_hash()
    # and mutating the returned shadow must not reach back into committed
    f.line_b.resources["forest"] = 999
    after2 = w.state_hash()
    return check("shadow_isolation",
                 before == after == after2,
                 f"committed hash stable across fork+shadow-mutation: {before == after == after2}")


def test_diff_soundness():
    w = genesis(seed=1).run(6)
    # identity ⇒ empty (same dice, same world)
    f_id = fork(w, identity(), horizon=20)
    id_empty = f_id.diff.empty
    # a real structural edit ⇒ immediately distinct state (horizon 0 isolates the apparatus from dynamics)
    f_cull0 = fork(w, cull_species("predator"), horizon=0)
    detects = not f_cull0.diff.empty
    # reported alive_delta matches an INDEPENDENT recount
    f = fork(w, remove_resource("forest"), horizon=15)
    indep = (len([a for a in f.line_b.agents.values() if a.alive])
             - len([a for a in f.line_a.agents.values() if a.alive]))
    delta_sound = (indep == f.diff.alive_delta)
    return check("diff_soundness",
                 id_empty and detects and delta_sound,
                 f"identity→empty={id_empty}; real-edit detected={detects}; "
                 f"alive_delta matches independent recount={delta_sound}")


def test_commit_and_discard():
    # discard: truth untouched
    w1 = genesis(seed=5).run(10)
    h1 = w1.state_hash()
    fork(w1, cull_species("predator"), horizon=20).discard()
    discard_ok = (w1.state_hash() == h1)

    # commit: edit applied at the present tick; horizon NOT installed
    w2 = genesis(seed=5).run(10)
    tick_before = w2.tick
    h2 = w2.state_hash()
    fork(w2, cull_species("predator"), horizon=20).commit()
    pred_after = w2.population().get("predator", -1)
    commit_changed = (w2.state_hash() != h2)
    tick_unchanged = (w2.tick == tick_before)        # commit writes a cause, it does not advance time
    horizon_not_installed = tick_unchanged
    edit_applied = (pred_after == 0)
    return check("commit_and_discard",
                 discard_ok and commit_changed and edit_applied and horizon_not_installed,
                 f"discard leaves truth identical={discard_ok}; commit changed truth={commit_changed}; "
                 f"edit applied (predators=0)={edit_applied}; horizon not installed (tick stable)={horizon_not_installed}")


def main():
    results = [
        test_determinism_and_replay(),
        test_shadow_isolation(),
        test_diff_soundness(),
        test_commit_and_discard(),
    ]
    print("test_weltwerk — validity-not-outcome self-test (the apparatus is valid; not 'the edit was good')\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:24s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. The Weltwerk slice is REAL iff this is {total}/{total}: a world that"
          f"\n  replays bitwise, forks without leaking, diffs soundly, and writes a cause only on commit.")
    print("  This proves the apparatus — NOT that any particular edit makes a 'richer' world.")
    assert passed == total, f"{total - passed} check(s) failed — slice is not yet real"


if __name__ == "__main__":
    main()
