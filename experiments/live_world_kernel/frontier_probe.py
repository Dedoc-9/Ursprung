# SPDX-License-Identifier: AGPL-3.0-only
"""
frontier_probe.py — instrument the dependency frontier; do NOT enforce it.

The discipline forbids promoting a frontier *discovery* into a kernel *law* before measuring where the
frontier actually lives. So this is not the barrier. It is the instrument that earns (or refuses) the barrier:

    observe → measure → locate frontier → choose mechanism      (NOT: choose → build → justify)

The runtime here deliberately LETS DEPENDENCY OUTRUN COMMITMENT — a committed/derived fact may reference an
uncommitted candidate, an observer may act on one — because the question is not "can we forbid that?" but
"does the system fail when we allow it, and where does the failure come from?"

FAILURE SIGNAL: a CONTRADICTED DEPENDENCY — a dependent referenced a candidate that then changed or vanished
without compensation. The instrument records it after the fact (never blocks it) and tags its SOURCE:
    commit-mediated   — formed through a derived commit (detectable at the commit boundary; a barrier could
                        prevent it by requiring dependencies on promoted facts only).
    observer-mediated — formed out of band (an observer saw a candidate and acted); a commit barrier cannot
                        see it, so it is only partially enforceable — policy, not law.

THREE OUTCOMES the instrument can reveal (all valuable, none assumed):
    ALIGNED            no contradiction — the frontier already coincides with commit; a barrier is redundant.
    NEEDS_PROMOTION    contradictions, all commit-mediated on unpromoted candidates — a barrier is EARNED.
    OBSERVER_DEPENDENT at least one contradiction is out of band — barrier insufficient; conservatism premium.

SEALED OBSERVER (the reflexive guard): the telemetry is append-only and is NEVER read back by world ops, and
classification is a PURE function over it — `telemetry ≠ control`, `observation ≠ intervention`. An instrument
that moved the world it measures would be measuring its own shadow.

APPARATUS, NO VERDICT. This locates the frontier; the choice to enforce a barrier remains the user's.

Run:  PYTHONHASHSEED=0 python3 frontier_probe.py
"""
from __future__ import annotations

from hashlib import blake2b

OUTCOMES = ("ALIGNED", "NEEDS_PROMOTION", "OBSERVER_DEPENDENT", "POST_COMMIT_MUTATION")


class Runtime:
    """A world that does NOT enforce a dependency barrier, with a sealed instrument attached."""

    def __init__(self):
        self.clock = 0
        self.version: dict[str, int] = {}   # live candidate -> version (absent once discarded)
        self.promoted: set[str] = set()     # candidates promoted to committed facts
        self.deps: list[dict] = []          # dependents (commit- or observer-mediated)
        self.telemetry: list[tuple] = []    # SEALED, append-only — never read by world ops
        self.contradictions: list[dict] = []

    # --- sealed telemetry: append only, no world op ever reads it ---
    def _log(self, kind, subject, refs=(), meta=None):
        self.clock += 1
        self.telemetry.append((self.clock, kind, subject, tuple(refs), meta or {}))

    # --- possibility space: candidates are freely mutable ---
    def new_candidate(self, cid):
        self.version[cid] = 1
        self._log("candidate_created", cid)

    def mutate(self, cid):
        self.version[cid] = self.version.get(cid, 0) + 1
        self._log("candidate_mutated", cid, meta={"version": self.version[cid]})
        self._detect(cid)

    def discard(self, cid):
        self._log("candidate_discarded", cid)
        self.version.pop(cid, None)
        self._detect(cid, discarded=True)

    def read(self, reader, cid):
        self._log("read", reader, refs=(cid,))

    def promote(self, cid):
        self.promoted.add(cid)
        self._log("promoted", cid)

    # --- dependency formation (NOT blocked, even if it outruns commitment) ---
    def derived_commit(self, dep_id, cid):
        self._log("derived_commit", dep_id, refs=(cid,), meta={"target_promoted": cid in self.promoted})
        self.deps.append({"dep_id": dep_id, "source": "commit", "target": cid,
                          "observed_version": self.version.get(cid),
                          "target_promoted": cid in self.promoted, "compensated": False})

    def externalize(self, dep_id, cid):
        self._log("externalized", dep_id, refs=(cid,), meta={"target_promoted": cid in self.promoted})
        self.deps.append({"dep_id": dep_id, "source": "observer", "target": cid,
                          "observed_version": self.version.get(cid),
                          "target_promoted": cid in self.promoted, "compensated": False})

    def compensate(self, dep_id):
        for d in self.deps:
            if d["dep_id"] == dep_id:
                d["compensated"] = True
        self._log("compensated", dep_id)

    def rollback_attempt(self, cid):
        self._log("rollback_attempt", cid)

    # --- contradiction detection: AFTER the fact, never a block ---
    def _detect(self, cid, discarded=False):
        cur = None if discarded else self.version.get(cid)
        for d in self.deps:
            if d["target"] != cid or d["compensated"]:
                continue
            stale = discarded or (d["observed_version"] is not None and cur is not None and cur != d["observed_version"])
            if stale:
                c = {"dep_id": d["dep_id"], "source": d["source"], "target": cid,
                     "target_promoted_at_dep": d["target_promoted"], "discarded": discarded}
                self.contradictions.append(c)
                self._log("contradicted_dependency", d["dep_id"], refs=(cid,), meta=c)

    def world_digest(self) -> str:
        s = repr((sorted(self.version.items()), sorted(self.promoted),
                  [(d["dep_id"], d["source"], d["target"], d["observed_version"], d["compensated"]) for d in self.deps],
                  len(self.contradictions)))
        return blake2b(s.encode(), digest_size=8).hexdigest()


# --- classification: a PURE function over what the instrument recorded (no world mutation) ---
def classify(rt: Runtime) -> str:
    cons = rt.contradictions
    if not cons:
        return "ALIGNED"
    if any(c["source"] == "observer" for c in cons):
        return "OBSERVER_DEPENDENT"            # at least one out-of-band → a commit barrier cannot prevent it
    if all(c["source"] == "commit" and not c["target_promoted_at_dep"] for c in cons):
        return "NEEDS_PROMOTION"               # all commit-mediated on unpromoted targets → a barrier is earned
    return "POST_COMMIT_MUTATION"              # contradiction despite promotion = mutating committed truth (other bug)


def barrier_would_prevent(outcome: str):
    return {"ALIGNED": "n/a (no contradiction)", "NEEDS_PROMOTION": "yes (promote-first)",
            "OBSERVER_DEPENDENT": "no (out of band)", "POST_COMMIT_MUTATION": "no (different violation)"}[outcome]


# --- three scenarios, each engineered to exhibit one outcome ---
def scenario_aligned() -> Runtime:
    rt = Runtime()
    rt.new_candidate("tree")
    rt.mutate("tree"); rt.mutate("tree")     # free mutation in possibility space — no dependents yet
    rt.promote("tree")                        # promote BEFORE anything depends on it
    rt.derived_commit("nav1", "tree")         # dependency forms on a PROMOTED (committed) fact
    return rt                                 # committed facts are not mutated afterward → no contradiction


def scenario_needs_promotion() -> Runtime:
    rt = Runtime()
    rt.new_candidate("tree")
    rt.derived_commit("nav1", "tree")         # commit-mediated dependency OUTRUNS commitment (tree unpromoted) — allowed
    rt.mutate("tree")                         # tree was still a possibility → nav1's premise moved → contradiction
    return rt


def scenario_observer_dependent() -> Runtime:
    rt = Runtime()
    rt.new_candidate("tree")
    rt.externalize("player_saw", "tree")      # observer-mediated dependency, out of band (never via commit)
    rt.discard("tree")                        # candidate vanishes → the observer's premise is gone → contradiction
    return rt


def main() -> None:
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<38} {detail}")

    print("frontier_probe — instrument the dependency boundary; observe, DO NOT enforce.")
    print("Lets dependency outrun commitment, then asks where the failure came from. Apparatus, no verdict.\n")

    runs = {"aligned": scenario_aligned(), "needs_promotion": scenario_needs_promotion(),
            "observer_dependent": scenario_observer_dependent()}
    verdicts = {name: classify(rt) for name, rt in runs.items()}

    print("  scenario             outcome             contradiction source   commit-barrier would prevent?")
    for name, rt in runs.items():
        o = verdicts[name]
        src = rt.contradictions[0]["source"] if rt.contradictions else "—"
        print(f"    {name:<18} {o:<19} {src:<22} {barrier_would_prevent(o)}")
    print()

    # the instrument classified each scenario into the outcome it was engineered to exhibit
    check("aligned_classified", verdicts["aligned"] == "ALIGNED" and not runs["aligned"].contradictions,
          "no contradiction → frontier already coincides with commit (barrier redundant)")
    check("needs_promotion_classified",
          verdicts["needs_promotion"] == "NEEDS_PROMOTION"
          and runs["needs_promotion"].contradictions[0]["source"] == "commit"
          and not runs["needs_promotion"].contradictions[0]["target_promoted_at_dep"],
          "commit-mediated contradiction on an unpromoted candidate → a barrier is EARNED")
    check("observer_dependent_classified",
          verdicts["observer_dependent"] == "OBSERVER_DEPENDENT"
          and runs["observer_dependent"].contradictions[0]["source"] == "observer",
          "out-of-band contradiction → barrier insufficient; partial policy only")

    # observe, not enforce: the runtime ALLOWED the dependency to outrun commitment
    s2 = runs["needs_promotion"]
    allowed = any(k == "derived_commit" and m.get("target_promoted") is False
                  for (_, k, _, _, m) in s2.telemetry) and len(s2.deps) == 1
    check("dependency_allowed_to_outrun", allowed,
          "nav1 committed against an UNPROMOTED candidate — recorded, never blocked (observe ≠ enforce)")

    # source attribution distinguishes the two failure modes (the basis for outcome 2 vs 3)
    check("source_attribution",
          runs["needs_promotion"].contradictions[0]["source"] == "commit"
          and runs["observer_dependent"].contradictions[0]["source"] == "observer",
          "commit-mediated vs observer-mediated told apart — the basis for 'earned' vs 'partial'")

    # the instrument is sealed: classification is pure; world state and telemetry are untouched by observing
    rt = runs["needs_promotion"]
    d_before, n_before = rt.world_digest(), len(rt.telemetry)
    _ = [classify(rt) for _ in range(3)]
    check("instrument_is_sealed",
          rt.world_digest() == d_before and len(rt.telemetry) == n_before,
          "classify() is pure: world digest and telemetry unchanged by being observed (telemetry ≠ control)")

    # apparatus, no verdict: the probe emits classifications only, never a recommendation to enforce
    check("apparatus_no_verdict", all(v in OUTCOMES for v in verdicts.values()),
          "outputs are frontier classifications, never 'enforce the barrier' — the choice stays the user's")

    print(f"\n{passed}/{total} checks. The instrument located the frontier in each scenario WITHOUT enforcing one:")
    print("ALIGNED (frontier = commit, barrier redundant), NEEDS_PROMOTION (commit-mediated, on an unpromoted")
    print("candidate — a barrier would be EARNED), OBSERVER_DEPENDENT (out of band — a commit barrier cannot")
    print("prevent it; only policy + a conservatism premium can). It distinguishes the two failure sources, it")
    print("let dependency outrun commitment rather than forbidding it, and it stayed a sealed observer of the")
    print("world it measured. NO VERDICT on whether to enforce the barrier — that choice is yours, now informed")
    print("by where the frontier actually falls. The architecture earns its boundaries; it does not assume them.")
    assert passed == total, "the frontier instrument failed its own self-test"


if __name__ == "__main__":
    main()
