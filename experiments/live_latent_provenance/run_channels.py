# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/live_latent_provenance/run_channels.py — the channel split makes the failure unspeakable.

    python3 experiments/live_latent_provenance/run_channels.py     # stdlib only; deterministic

The probe named the danger: an optimization drops a state-changing event under backpressure, the
world advances anyway, and an UNACCOUNTED gap appears. These checks show the type boundary makes that
program state unreachable — not merely discouraged.
"""
from __future__ import annotations

from channels import Commit, CommitChannel, ResolveRing
from compression import ProvenanceStore, SeveranceError


def main():
    store = ProvenanceStore()
    good = store.commit({"origin": "developer", "edit_lineage": ["gravity 1.0 -> 0.5"]})
    world = {}
    cc = CommitChannel(store)
    ring = ResolveRing(capacity=4)

    # 1. an unprovenanced commit cannot be constructed (None / UNRECORDED / "")
    cannot_construct = 0
    for bad in (None, "<unrecorded>", ""):
        try:
            Commit(target="gravity", new_state=0.5, provenance_digest=bad)
        except ValueError:
            cannot_construct += 1

    # 2. a traceable commit advances state through the never-drop path
    cc.apply(Commit("gravity", 0.5, good), world)

    # 3. a commit whose provenance is severed/dangling is REFUSED — state does not advance
    state_before = dict(world)
    refused = False
    try:
        cc.apply(Commit("gravity", 9.9, "deadbeefcafe"), world)  # dangling digest
    except SeveranceError:
        refused = True

    # 5. ResolveRing drops on full, counted, and never raises
    for i in range(10):
        ring.offer("d%d" % i)

    checks = {
        "1_unprovenanced_commit_cannot_be_constructed": cannot_construct == 3,
        "2_traceable_commit_advances_state": world.get("gravity") == 0.5 and cc.applied == 1,
        "3_severed_commit_is_refused_state_unchanged":
            refused and world == state_before and cc.refused == 1,
        "4_commit_channel_has_no_drop_path":
            not any(hasattr(cc, a) for a in ("offer", "full", "drop", "capacity")),
        "5_resolve_ring_drops_on_full_counted": ring.dropped > 0,
        "6_resolve_ring_cannot_advance_state": not hasattr(ring, "apply"),
        "7_dropping_a_commit_is_unreachable":
            # state advances ONLY via CommitChannel.apply (no drop path) and the droppable ring has
            # no apply — so "a full buffer dropped a state change" is not expressible.
            (not hasattr(ring, "apply")) and (not hasattr(cc, "offer")),
    }

    print("CHANNEL SPLIT — the provenance gap is unspeakable, not merely discouraged\n")
    print("   commits applied:", cc.applied, " commits refused:", cc.refused,
          " resolve requests dropped:", ring.dropped)
    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "channel split did not hold"
    print("\nall %d checks passed — state advances only through the never-drop, provenance-required path."
          % len(checks))
    return checks


if __name__ == "__main__":
    main()
