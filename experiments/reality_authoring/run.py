# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_authoring/run.py — a developer (and an algorithm, a model, the environment) author a world.

    python3 experiments/reality_authoring/run.py     # stdlib only; deterministic

Demonstrates that a world can stay editable while the source of every structure stays inspectable — no origin
privileged, none erased — and that the runtime can answer questions ordinary engines cannot: designed vs
emerged, what collapses if an edit is removed, and what is stable under the world's own transformations.
"""
from __future__ import annotations

from reality import Edit, World


def main():
    w = World()
    g = w.apply(Edit("gravity", 1.0, 0.5, "developer", "gameplay_constraint", "world_v12", survival_tests=[True]))
    w.apply(Edit("friction", 0.3, 0.22, "algorithm", "auto_tuned_for_stability", "world_v12", survival_tests=[True]))
    w.apply(Edit("jump_height", None, 2.4, "algorithm", "derived_from_gravity", "world_v12", depends_on=g.digest(), survival_tests=[True]))
    w.apply(Edit("flocking", None, "cohesion", "environment", "appeared_after_density_change", "world_v12", survival_tests=[False]))
    w.apply(Edit("latent_factor_3", None, "texture_axis", "learned_model", "emerged_in_training", "world_v12", survival_tests=[True]))
    w.apply(Edit("momentum_conservation", None, "invariant", "environment", "holds_across_all_edits", "world_v12", survival_tests=[True, True, True]))

    print("REALITY AUTHORING RUNTIME — an edit is an event with identity, not a mutation\n")
    for t in w.history:
        c = w.classify(t)
        tag = "designed" if c["designed"] else ("emerged" if c["emerged"] else "?")
        print("   %-22s = %-12s [%s] sources=%s" % (t, w.value(t), tag, c["sources"]))
    print("\n   provenance_of(jump_height):", w.provenance_of("jump_height"))

    designed = w.classify("gravity")
    emerged = w.classify("flocking")
    # capture source-of-structure facts BEFORE the destructive edit-removal below
    all_sources = {s for t in w.history for s in w.origin(t)}
    origins_nonempty = all(w.origin(t) for t in w.history)
    friction_authoring = w.classify("friction")
    before = w.value("jump_height")
    w.remove("gravity", 0)                      # remove the foundational edit
    after = w.value("jump_height")              # its dependent collapses
    print("\n   removed the gravity edit → jump_height %s → %s (collapsed: %s)" % (before, after, w.collapsed_targets()))
    stable = w.stable_under_transformations()
    print("   stable under the world's own transformations (discovered):",
          [t for t, ok in stable.items() if ok])

    checks = {
        "1_edit_is_an_event_with_identity": g.old == 1.0 and g.new == 0.5 and g.digest() != w.history["friction"][0].digest(),
        "2_source_of_structure_spans_all_origins": {"developer", "algorithm", "environment", "learned_model"} <= all_sources,
        "2_no_origin_disappears": origins_nonempty,
        "3_designed_vs_emerged": designed["designed"] and emerged["emerged"] and not emerged["designed"],
        "3_machine_authoring_is_authoring_not_privileged_human": friction_authoring["designed"] and "algorithm" in friction_authoring["sources"],
        "4_remove_edit_collapses_dependents": before == 2.4 and after is None and "jump_height" in w.collapsed_targets(),
        "4_stable_under_own_transformations_is_discovered": stable["momentum_conservation"] is True and stable["flocking"] is False,
    }
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "Reality Authoring Runtime did not hold"
    print("\nall %d checks passed — the world stayed editable; every source of structure stayed inspectable." % len(checks))
    return checks


if __name__ == "__main__":
    main()
