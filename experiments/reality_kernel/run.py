# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/run.py — the kernel earns existence by NOT collapsing categories.

    python3 experiments/reality_kernel/run.py     # stdlib only; deterministic

The first kernel benchmark is not speed — it is whether consolidation preserves distinctions. The
last check is a real differential against the OLD `WorldWithIgnorance` bench (imported, not
reconstructed): the kernel must reproduce every diagnosis and refine the old three-way status into the
four-way existence without losing information. The Python runtime becomes the specification Rust must
later preserve.
"""
from __future__ import annotations

import importlib.util
import os

from artifact import Artifact
from commit import CommitReceipt, SeveranceError
from event import Event
from kernel import RealityKernel


def _load(name, *parts):
    spec = importlib.util.spec_from_file_location(name, os.path.join(os.path.dirname(__file__), *parts))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# the OLD bench, imported for the migration differential
_nonrec = _load("rk_old_nonrec", "..", "reality_authoring", "nonrecovery.py")
WorldWithIgnorance, NonRecovery, Edit = _nonrec.WorldWithIgnorance, _nonrec.NonRecovery, _nonrec.Edit


def _fails(fn):
    try:
        fn()
        return False
    except (ValueError, SeveranceError):
        return True


SEV = {"signal_present": False, "alternative_cause_matches": False,
       "resolves_under_richer_admissibility": False, "resolves_under_richer_observer": False}
ASM = {"signal_present": True, "alternative_cause_matches": False,
       "resolves_under_richer_admissibility": True, "resolves_under_richer_observer": False}
RSC = {"signal_present": True, "alternative_cause_matches": False,
       "resolves_under_richer_admissibility": False, "resolves_under_richer_observer": True}

TARGETS = ["gravity", "relation_R", "relation_S", "relation_T", "relation_NEVER_ASKED"]


def _refines(old_status, k_exist):
    return ((old_status == "present" and k_exist == "present")
            or (old_status == "UNACCOUNTED" and k_exist == "unaccounted")
            or (old_status == "absent_or_unresolved" and k_exist in ("absent", "unresolved")))


def main():
    k = RealityKernel()
    good = k.apply(Event("gravity", 1.0, 0.5, "developer", survival=[True], justification="gameplay_constraint"))
    k.record_nonrecovery("relation_R", SEV, "analysis_v3")
    k.record_nonrecovery("relation_S", ASM, "analysis_v3", missing="instrument_validity_A")
    k.record_nonrecovery("relation_T", RSC, "analysis_v3")
    q = {t: k.query(t) for t in TARGETS}

    # build the SAME scenario in the old bench and compare
    old = WorldWithIgnorance()
    old.apply(Edit("gravity", 1.0, 0.5, "developer", "gameplay_constraint", "world_v12", survival_tests=[True]))
    old.record_nonrecovery(NonRecovery("relation_R", SEV, "analysis_v3"))
    old.record_nonrecovery(NonRecovery("relation_S", ASM, "analysis_v3", missing_admissibility="instrument_validity_A"))
    old.record_nonrecovery(NonRecovery("relation_T", RSC, "analysis_v3"))
    diagnoses_match = all(q[t].get("diagnosis") == old.explain(t).get("why") for t in TARGETS)
    existence_refines = all(_refines(old.explain(t)["status"], q[t]["existence"]) for t in TARGETS)

    checks = {
        "1_artifact_without_provenance_fails": _fails(lambda: Artifact("rule", 0.5, {})),
        "2_event_without_source_fails": _fails(lambda: Event("g", 1.0, 0.5, "")),
        "3_commit_without_receipt_fails":
            _fails(lambda: CommitReceipt("g", 1.0, 0.5, "developer", (), ""))          # no digest → no receipt
            and _fails(lambda: k.apply(Event("x", 0, 1, "developer"), requires="deadbeefcafe"))  # severed prereq
            and "x" not in k.world.history,                                            # ...state did NOT advance
        "4_query_distinguishes_four":
            (q["gravity"]["existence"], q["relation_R"]["existence"], q["relation_S"]["existence"],
             q["relation_NEVER_ASKED"]["existence"]) == ("present", "absent", "unresolved", "unaccounted"),
        "5_compression_preserves_resolvability":
            len(good.provenance_digest) == 12 and k.provenance_of("gravity")[0]["source"] == "developer",
        "6_migration_reproduces_old_diagnoses_and_refines": diagnoses_match and existence_refines,
        "7_receipt_is_record_not_authorization":
            set(CommitReceipt.__dataclass_fields__) == {"target", "previous", "new", "source",
                                                        "dependencies", "provenance_digest"}
            and not any(w in CommitReceipt.__dataclass_fields__ for w in ("allowed", "authorized", "permitted")),
    }

    print("REALITY KERNEL — consolidation earns existence by not collapsing categories\n")
    for t in TARGETS:
        print("   %-22s → %s" % (t, {kk: q[t][kk] for kk in ("existence", "diagnosis", "resolution_path")}))
    print("\nself-check:")
    for kk, v in checks.items():
        print(("  ok   " if v else "  FAIL ") + kk)
    assert all(checks.values()), "kernel consolidation collapsed a category"
    print("\nall %d checks passed — present/absent/unresolved/unaccounted stay distinct; the old "
          "diagnoses are reproduced." % len(checks))
    return checks


if __name__ == "__main__":
    main()
