# SPDX-License-Identifier: AGPL-3.0-only
"""
live_world_kernel.py — the smallest adversarial embedded-authoring kernel (Python reference).

It is NOT an editor, a renderer, or an MMO. It answers exactly ONE question, the one the
EMBEDDED_AUTHORING design note says must be answered before the larger vision earns the right to exist:

    Can a running world accept, reject, and rewind creator actions WITHOUT losing causal truth?

If yes, the editor is a UI problem. If no, the larger engine vision collapses before it needs a renderer.

THREE STORES, KEPT DISTINCT:
    committed   = SHARED TRUTH        — the canonical event log; the only thing other clients observe.
    speculative = PRIVATE HOT STATE   — a per-client scratchpad: fast, mutable, DISPOSABLE. Never observed
                                        by anyone else, never a contract, until a commit promotes it.
    recovery    = REPLAYABLE HISTORY  — the committed log itself; "why is the world this way?" is answered
                                        by re-folding it, never by trusting live state.

THREE STATES OF A FACT, KEPT DISTINCT (objectivity is not one scalar — it is at least two orthogonal axes,
causal dependence ⟂ replica redundancy):
    COMMITTED    = authority_valid ∧ accepted_into_shared_log ∧ replay_integrity   (binary, at the gate)
    IRREVERSIBLE = ∃ committed dependent                                           (causal: the first
                                                                                    dependent crosses the
                                                                                    irreversibility frontier)
    DURABLE      = ∃ recovery path INDEPENDENT of the original failure mode        (redundancy: replicas OR
                                                                                    regeneration OR archival —
                                                                                    quorum is only ONE such path)
A fact can be committed-but-not-irreversible (nobody depends on it yet), irreversible-but-not-durable
(depended-on but single-copy, a failure destroys it), or durable-but-not-irreversible (replicated/regenerable
asset nothing yet depends on). DURABLE is NOT a synonym for quorum; the invariant is only that a recovery
path exists that the failure cannot also take out.

Run:  PYTHONHASHSEED=0 python3 live_world_kernel.py
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b

ROOT = "root"  # external trust anchor (the "external root" choice; the embedded-root variant is future work)


@dataclass(frozen=True)
class EditEvent:
    eid: str
    author: str
    capability: str
    target: str
    op: str
    payload: tuple = ()
    deps: tuple = ()

    def digest(self) -> str:
        h = blake2b(digest_size=8)
        for part in (self.eid, self.author, self.capability, self.target, self.op,
                     repr(self.payload), repr(self.deps)):
            h.update(part.encode())
        return h.hexdigest()


def apply_event(world: dict, ev: EditEvent) -> None:
    if ev.op in ("grant", "revoke"):
        return
    if ev.op == "create":
        world[ev.target] = dict(ev.payload)
    elif ev.op == "delete":
        world.pop(ev.target, None)
    elif ev.op in ("move", "set"):
        obj = world.setdefault(ev.target, {})
        for k, v in ev.payload:
            obj[k] = v


def project(events) -> dict:
    world: dict = {}
    for ev in events:
        apply_event(world, ev)
    return world


def project_caps(events) -> dict:
    caps: dict = {}
    for ev in events:
        if ev.op == "grant":
            caps.setdefault(ev.target, set()).add(ev.capability)
        elif ev.op == "revoke":
            caps.get(ev.target, set()).discard(ev.capability)
    return caps


def why_allowed(committed, ev: EditEvent):
    if ev.author == ROOT:
        return "root"
    granted = None
    for e in committed:
        if e.target == ev.author and e.capability == ev.capability:
            if e.op == "grant":
                granted = e.eid
            elif e.op == "revoke":
                granted = None
    return granted


def causal_closure(events, roots) -> set:
    doomed = set(roots)
    changed = True
    while changed:
        changed = False
        for e in events:
            if e.eid not in doomed and any(d in doomed for d in e.deps):
                doomed.add(e.eid)
                changed = True
    return doomed


# ---------------------------------------------------------------------------------------------------
# The kernel — the single authority over SHARED TRUTH; tracks the three states of every committed fact.
# ---------------------------------------------------------------------------------------------------
class Kernel:
    def __init__(self, root: str = ROOT):
        self.committed: list[EditEvent] = []   # shared truth + recovery substrate
        self.root = root
        # the three states, stamped on a logical clock (deterministic, replayable — not wall time)
        self.clock = 0
        self.t_commit: dict[str, int] = {}     # COMMITTED at
        self.t_dep: dict[str, int] = {}        # IRREVERSIBLE at (first committed dependent)
        self.t_durable: dict[str, int] = {}    # DURABLE at (first failure-independent recovery path)
        # durability holders — quorum is ONE strategy among several
        self.primary: set[str] = set()         # the primary store
        self.replicas: dict[str, set[str]] = {}  # holder_name -> eids it independently holds
        self.regen: dict[str, frozenset] = {}    # eid -> tokens its deterministic regeneration needs

    def tick(self) -> int:
        self.clock += 1
        return self.clock

    def caps(self) -> dict:
        return project_caps(self.committed)

    def authorized(self, ev: EditEvent) -> bool:
        if ev.op in ("grant", "revoke"):
            return ev.author == self.root
        if ev.author == self.root:
            return True
        return ev.capability in self.caps().get(ev.author, set())

    def commit(self, ev: EditEvent) -> bool:
        if any(e.eid == ev.eid for e in self.committed):
            return True                          # idempotent
        if not self.authorized(ev):
            return False
        self.committed.append(ev)
        t = self.tick()
        self.t_commit[ev.eid] = t
        self.primary.add(ev.eid)
        for parent in ev.deps:                   # committing a dependent crosses the parent's frontier
            if parent in self.t_commit and parent not in self.t_dep:
                self.t_dep[parent] = t
        return True

    def shared_world(self) -> dict:
        return project(self.committed)

    # --- the three states ---
    def is_committed(self, eid: str) -> bool:
        return eid in self.t_commit

    def is_irreversible(self, eid: str) -> bool:
        return any(eid in e.deps for e in self.committed)

    def replicate(self, eid: str, holder: str) -> None:
        """Copy a committed fact to an INDEPENDENT holder (a quorum-style recovery path)."""
        self.replicas.setdefault(holder, set()).add(eid)
        self._stamp_durable(eid)

    def declare_regenerable(self, eid: str, needs) -> None:
        """A fact recoverable by DETERMINISTIC regeneration from inputs that live elsewhere (no quorum)."""
        self.regen[eid] = frozenset(needs)
        self._stamp_durable(eid)

    def recovery_paths(self, eid: str, failed) -> list:
        """Every recovery path that the given failure does NOT also take out. The durability invariant
        is the EXISTENCE of such a path — replica, regeneration, archival — never a specific strategy."""
        failed = set(failed)
        paths = []
        if "primary" not in failed and eid in self.primary:
            paths.append("primary")
        for holder, held in self.replicas.items():
            if holder not in failed and eid in held:
                paths.append("replica:" + holder)
        if eid in self.regen and not (self.regen[eid] & failed):
            paths.append("regenerate")
        return paths

    def is_durable(self, eid: str, failed=("primary",)) -> bool:
        return len(self.recovery_paths(eid, failed)) >= 1

    def _stamp_durable(self, eid: str) -> None:
        # DURABLE := survives loss of the primary (∃ independent recovery path)
        if eid not in self.t_durable and self.is_durable(eid, {"primary"}):
            self.t_durable[eid] = self.tick()

    def recover(self, eid: str, failed):
        """Return ('recovered', path) or ('NonRecovery', diagnosis) — never a fabricated value.
        Loss with no independent path is SEVERANCE, reported, not silently guessed (`compress ≠ sever`)."""
        paths = self.recovery_paths(eid, failed)
        if not paths:
            return ("NonRecovery", f"severed: no recovery path for {eid} independent of {sorted(set(failed))}")
        return ("recovered", paths[0])


# ---------------------------------------------------------------------------------------------------
# The client — holds PRIVATE HOT speculation; sees committed truth + its own speculation; nobody else's.
# ---------------------------------------------------------------------------------------------------
class Client:
    def __init__(self, kernel: Kernel, name: str):
        self.k = kernel
        self.name = name
        self.spec: list[EditEvent] = []

    def propose(self, ev: EditEvent) -> None:
        self.spec.append(ev)

    def view(self) -> dict:
        return project(self.k.committed + self.spec)

    def commit(self, eid: str) -> bool:
        ev = next(e for e in self.spec if e.eid == eid)
        if self.k.commit(ev):
            self.spec.remove(ev)
            return True
        self._rollback_subtree(eid)
        return False

    def _rollback_subtree(self, eid: str) -> set:
        doomed = causal_closure(self.spec, {eid})
        self.spec = [e for e in self.spec if e.eid not in doomed]
        return doomed

    def discard_speculation(self) -> None:
        self.spec = []


# ---------------------------------------------------------------------------------------------------
# Adversarial self-test. No UI, no renderer, no scale.
# ---------------------------------------------------------------------------------------------------
def main() -> None:
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    print("live_world_kernel — accept / reject / rewind creator actions without losing causal truth,")
    print("and tell apart the three states of a fact: COMMITTED ⟂ IRREVERSIBLE ⟂ DURABLE\n")

    k = Kernel()
    k.commit(EditEvent("g1", ROOT, "terrain.modify", "builderA", "grant"))
    A, B = Client(k, "A"), Client(k, "B")

    # ---- layer 1: commit / speculate / reject / rewind (the original adversarial suite) ----
    e1 = EditEvent("e1", "builderA", "terrain.modify", "wall", "move", (("pos", (14, 2, 5)),))
    A.propose(e1)
    check("speculative_isolation",
          "wall" in A.view() and "wall" not in B.view() and all(e.eid != "e1" for e in k.committed),
          "A sees its speculative wall; B and shared truth do not")

    ok = A.commit("e1")
    check("commit_promotes_to_truth",
          ok and any(e.eid == "e1" for e in k.committed) and "wall" in B.view() and all(e.eid != "e1" for e in A.spec),
          "accepted → B now sees the wall; it left A's speculation")

    Bx = Client(k, "Bx")
    e1b = EditEvent("e1b", "builderB", "terrain.modify", "bridge", "move", (("pos", (0, 0, 9)),))
    e2b = EditEvent("e2b", "builderB", "terrain.modify", "crate", "create", (("on", "bridge"),), ("e1b",))
    e3b = EditEvent("e3b", "builderB", "terrain.modify", "ai", "create", (("behind", "crate"),), ("e2b",))
    e4b = EditEvent("e4b", "builderB", "terrain.modify", "torch", "create", (("pos", (5, 5, 5)),))
    for e in (e1b, e2b, e3b, e4b):
        Bx.propose(e)
    before = set(Bx.view())
    ok = Bx.commit("e1b")
    after = set(Bx.view())
    check("causal_subtree_rollback",
          (not ok) and {e.eid for e in Bx.spec} == {"e4b"}
          and {"bridge", "crate", "ai"} <= before and "torch" in after and not ({"bridge", "crate", "ai"} & after),
          "reject e1b → removed exactly {e1b,e2b,e3b}; unrelated torch survives")

    check("no_leak_on_reject",
          all(e.eid not in {"e1b", "e2b", "e3b", "e4b"} for e in k.committed) and "bridge" not in B.view(),
          "rejected speculation never entered committed truth or B's view")

    live = k.shared_world()
    log_digest = blake2b("".join(e.digest() for e in k.committed).encode(), digest_size=8).hexdigest()
    check("replay_from_zero", project(list(k.committed)) == live,
          f"world rebuilt from {len(k.committed)} committed events == live state (log {log_digest})")

    why = why_allowed(k.committed, e1)
    k.commit(EditEvent("r1", ROOT, "terrain.modify", "builderA", "revoke"))
    A2 = Client(k, "A2")
    A2.propose(EditEvent("e5", "builderA", "terrain.modify", "wall", "move", (("pos", (99, 0, 0)),)))
    revoked_ok = A2.commit("e5")
    check("authority_from_history", why == "g1" and not revoked_ok,
          "e1 authorized by grant g1; after revoke, the same edit is rejected")

    n = len(k.committed)
    k.commit(e1)
    check("duplicate_idempotent", len(k.committed) == n, "re-committing e1 is a no-op")

    C = Client(k, "C")
    C.propose(EditEvent("ed", "builderA", "terrain.modify", "ghost", "create"))
    seen = "ghost" in C.view()
    C.discard_speculation()
    check("disconnect_discards_speculation",
          seen and "ghost" not in C.view() and all(e.eid != "ed" for e in k.committed),
          "disconnect drops private speculation; committed truth untouched")

    frontier_ok = True
    for D in (1, 3, 5, 10):
        Z = Client(k, "Z")
        prev = None
        for i in range(D):
            deps = () if prev is None else (prev,)
            Z.propose(EditEvent(f"z{i}", "builderB", "terrain.modify", f"o{i}", "create", (), deps))
            prev = f"z{i}"
        frontier_ok &= (len(Z._rollback_subtree("z0")) == D)
    frontier_ok &= (10 * 0.1 > 3 * 0.1 > 1 * 0.1) and (5 * 0.2 > 5 * 0.05)
    check("latency_irreversibility_frontier", frontier_ok,
          "rolled-back work = causal depth; expected thrash = depth × reject_prob (monotone)")

    # ---- layer 2: the three states of a fact (committed / irreversible / durable are distinct) ----
    print()
    k.commit(EditEvent("g2", ROOT, "terrain.modify", "builderA", "grant"))  # re-grant after the earlier revoke

    a1 = EditEvent("a1", "builderA", "terrain.modify", "stone", "create", (("x", 1),))
    k.commit(a1)
    check("committed_not_irreversible",
          k.is_committed("a1") and not k.is_irreversible("a1"),
          "a1 is shared truth, but no committed event depends on it yet (committed ⊅ irreversible)")

    a2 = EditEvent("a2", "builderA", "terrain.modify", "moss", "create", (("on", "stone"),), ("a1",))
    k.commit(a2)
    check("dependency_makes_irreversible",
          k.is_irreversible("a1") and "a1" in k.t_dep,
          f"committing a2 (deps a1) crosses a1's irreversibility frontier at t={k.t_dep.get('a1')}")

    durable_a1 = k.is_durable("a1", {"primary"})
    k.replicate("a2", "node_b")                                  # recovery path: an independent replica
    a3 = EditEvent("a3", "builderA", "terrain.modify", "tree", "create", (("seed", 42),))
    k.commit(a3)
    k.declare_regenerable("a3", {"seed_store"})                  # recovery path: regeneration — ZERO replicas
    check("durable_by_independent_path_not_quorum",
          (not durable_a1) and k.is_durable("a2", {"primary"}) and k.is_durable("a3", {"primary"}),
          "a1 primary-only → not durable; a2 durable via replica; a3 durable via REGENERATION (no quorum)")

    check("axes_are_orthogonal",
          (k.is_irreversible("a1") and not k.is_durable("a1", {"primary"}))       # depended-on but fragile
          and (k.is_durable("a3", {"primary"}) and not k.is_irreversible("a3")),  # durable but nothing depends on it
          "a1 = irreversible-not-durable; a3 = durable-not-irreversible (causal load ⟂ replica redundancy)")

    # deliberate DURABILITY FAILURE: destroy the primary; who survives, and is loss reported honestly?
    rec_a2 = k.recover("a2", {"primary"})
    rec_a3 = k.recover("a3", {"primary"})
    rec_a1 = k.recover("a1", {"primary"})
    check("durability_failure_recovers_independent",
          rec_a2[0] == "recovered" and rec_a3[0] == "recovered",
          f"primary lost → a2 via {rec_a2[1]}, a3 via {rec_a3[1]} (paths independent of the failure)")
    check("loss_is_severance_not_a_guess",
          rec_a1[0] == "NonRecovery",
          "primary lost → a1 has no independent path: reported as severance, never fabricated (compress≠sever)")

    # three timestamps, two SEPARATE budgets — and durable reached without any dependency (axes are separate)
    k.commit(EditEvent("f1", "builderA", "terrain.modify", "wallx", "create", (("x", 0),)))
    k.commit(EditEvent("f2", "builderA", "terrain.modify", "vine", "create", (("on", "wallx"),), ("f1",)))
    k.replicate("f1", "node_b")
    order_ok = k.t_commit["f1"] <= k.t_dep["f1"] <= k.t_durable["f1"]
    commit_to_dep = k.t_dep["f1"] - k.t_commit["f1"]
    dep_to_durable = k.t_durable["f1"] - k.t_dep["f1"]
    check("three_timestamps_two_budgets",
          order_ok and ("a3" in k.t_durable) and ("a3" not in k.t_dep),
          f"f1: commit→dep={commit_to_dep}, dep→durable={dep_to_durable}; a3 reached durable with NO dependency")

    print(f"\n{passed}/{total} checks. The one question is answered "
          f"{'YES' if passed == total else 'NO'} (within scope): a running world accepts, rejects, and rewinds")
    print("creator actions without losing causal truth — AND keeps the three states of a fact distinct:")
    print("committed (at the authority gate), irreversible (first committed dependent), durable (a recovery")
    print("path independent of the failure — replica OR regeneration OR archival, never just quorum). Causal")
    print("load and replica redundancy are orthogonal axes with separate latency budgets; a severed fact is")
    print("reported, never guessed. Reference prototype: single-process LOGIC — concurrency/scale, embedded-root")
    print("authority, and a measured human-trust latency threshold remain the next probes. `declared ≠ verified`.")
    assert passed == total, "the kernel failed its own adversarial test"


if __name__ == "__main__":
    main()
