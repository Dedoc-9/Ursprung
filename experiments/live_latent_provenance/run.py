# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/live_latent_provenance/run.py — provenance-preserving compression under runtime constraints.

    python3 experiments/live_latent_provenance/run.py     # stdlib only; deterministic

NOT a real-time claim (that needs real silicon — the un-faked frontier). This tests the
architectural property that licenses one: a runtime can compress its hot path to a single digest
and still recover the full lineage, and an optimization that SEVERS provenance is a distinct,
catchable failure mode — never a silent fallback to `unknown`.
"""
from __future__ import annotations

import copy

from compression import (
    LiveObject,
    ProvenanceStore,
    SeveranceError,
    admit_to_frame,
    optimize_compress,
    optimize_sever,
)


def main():
    store = ProvenanceStore()
    record = {
        "origin": "developer",
        "edit_lineage": ["gravity 1.0 -> 0.5"],
        "assumptions": [],
        "survival_tests": [True],
        "failures": [],
        "verification_status": "declared",
    }
    gravity = LiveObject(state={"gravity": 0.5}, transform="identity")
    store.compress(gravity, record)  # the hot-path object now carries only a digest

    # representation change in the hot path: pack the state, swap the transform — keep the digest
    reencoded = gravity.reencode(state=b"\x00\x00", transform="packed")

    # THE SEVERANCE TEST
    severed = optimize_sever(gravity)
    severed_res = store.resolve(severed)

    fresh = LiveObject(state={"x": 1}, transform="identity")          # never recorded -> UNACCOUNTED
    dangling = LiveObject(state={"y": 2}, transform="identity", provenance_digest="deadbeefcafe")

    print("PROVENANCE-PRESERVING COMPRESSION UNDER RUNTIME CONSTRAINTS\n")
    print("   hot-path object:", {"state": gravity.state, "transform": gravity.transform,
                                   "provenance_digest": gravity.provenance_digest})
    print("   resolve(digest) →", store.resolve(gravity)["provenance"]["edit_lineage"],
          "from", store.resolve(gravity)["provenance"]["origin"])
    print("   sever the digest → object still holds", severed.state, "but provenance is",
          severed_res["status"])

    fields = {"origin", "edit_lineage", "assumptions", "survival_tests", "failures", "verification_status"}

    checks = {
        "1_hot_path_carries_only_a_digest":
            set(LiveObject.__dataclass_fields__) == {"state", "transform", "provenance_digest"}
            and isinstance(gravity.provenance_digest, str) and len(gravity.provenance_digest) == 12,
        "2_digest_resolves_to_full_provenance":
            store.resolve(gravity)["status"] == "resolved"
            and fields <= set(store.resolve(gravity)["provenance"]),
        "3_compression_conserves_provenance":
            store.resolve(gravity)["provenance"]["edit_lineage"] == ["gravity 1.0 -> 0.5"],
        "4_provenance_identity_survives_representation_change":
            reencoded.state != gravity.state
            and store.resolve(reencoded)["provenance"] == store.resolve(gravity)["provenance"],
        "5_severance_is_a_distinct_failure_not_unknown":
            severed_res["status"] == "PROVENANCE_SEVERED" and severed.state == {"gravity": 0.5},
        "6_severed_differs_from_unaccounted":
            store.resolve(fresh)["status"] == "UNACCOUNTED"
            and severed_res["status"] == "PROVENANCE_SEVERED",
        "7_dangling_digest_is_severed_too":
            store.resolve(dangling)["status"] == "PROVENANCE_SEVERED",
        "8_optimization_may_compress_not_sever":
            store.is_traceable(optimize_compress(store, copy.copy(gravity)))
            and store.resolve(optimize_sever(copy.copy(gravity)))["status"] == "PROVENANCE_SEVERED",
        "9_frame_admits_traceable_refuses_severed":
            _admits(store, gravity) and not _admits(store, severed) and not _admits(store, fresh),
    }

    print("\nself-check:")
    for k, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + k)
    assert all(checks.values()), "provenance-preserving compression did not hold"
    print("\nall %d checks passed — execution is compressed, provenance is conserved." % len(checks))
    print("the world may become faster, smaller, learned, generated, distributed, or optimized;")
    print("it may not become untraceable.")
    return checks


def _admits(store, obj) -> bool:
    try:
        admit_to_frame(store, obj)
        return True
    except SeveranceError:
        return False


if __name__ == "__main__":
    main()
