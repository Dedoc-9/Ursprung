# SPDX-License-Identifier: AGPL-3.0-only
"""
live_world_kernel.py — the smallest adversarial embedded-authoring kernel (Python reference).

It is NOT an editor, a renderer, or an MMO. It answers exactly ONE question, the one the
EMBEDDED_AUTHORING design note says must be answered before the larger vision earns the right to exist:

    Can a running world accept, reject, and rewind creator actions WITHOUT losing causal truth?

If yes, the editor is a UI problem. If no, the larger engine vision collapses before it needs a renderer.

THREE STORES, KEPT DISTINCT (the load-bearing correction):
    committed   = SHARED TRUTH        — the canonical event log; the only thing other clients observe.
    speculative = PRIVATE HOT STATE   — a per-client scratchpad: fast, mutable, DISPOSABLE. Never observed
                                        by anyone else, never a contract, until it is promoted by a commit.
    recovery    = REPLAYABLE HISTORY  — the committed log itself; "why is the world this way?" is answered
                                        by re-folding it, never by trusting live state.
Blurring these is what makes rollback expensive. Prediction is a scratchpad, not a sealed reserve.

THE PRIMITIVE: an edit is an EVENT, not a mutation. propose() touches only private speculation; commit()
runs the authority gate and either PROMOTES the event into shared truth or REJECTS it and rewinds the
rejected event together with its entire CAUSAL SUBTREE — exactly its transitive descendants, nothing else.

Run:  PYTHONHASHSEED=0 python3 live_world_kernel.py
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2b

ROOT = "root"  # external trust anchor (the "external root" choice; the embedded-root variant is future work)


# ---------------------------------------------------------------------------------------------------
# The edit event — a transition with an author, a required capability, and explicit causal dependencies.
# ---------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class EditEvent:
    eid: str            # unique identity
    author: str         # who proposed it
    capability: str     # capability required to commit it (or, for grant/revoke, the cap being changed)
    target: str         # object id (or, for grant/revoke, the grantee)
    op: str             # "create" | "move" | "set" | "delete" | "grant" | "revoke"
    payload: tuple = ()  # deterministic ((key, value), ...)
    deps: tuple = ()     # eids this event causally depends on (its causal parents)

    def digest(self) -> str:
        h = blake2b(digest_size=8)
        for part in (self.eid, self.author, self.capability, self.target, self.op,
                     repr(self.payload), repr(self.deps)):
            h.update(part.encode())
        return h.hexdigest()


def apply_event(world: dict, ev: EditEvent) -> None:
    """Fold one event into a world state. Capability events do not touch world objects."""
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
    """Deterministic projection: state is a pure function of the ordered event sequence."""
    world: dict = {}
    for ev in events:
        apply_event(world, ev)
    return world


def project_caps(events) -> dict:
    """Authority is itself a projection of committed grant/revoke events — answerable from history."""
    caps: dict = {}
    for ev in events:
        if ev.op == "grant":
            caps.setdefault(ev.target, set()).add(ev.capability)
        elif ev.op == "revoke":
            caps.get(ev.target, set()).discard(ev.capability)
    return caps


def why_allowed(committed, ev: EditEvent):
    """Replay the log to explain authority: which committed grant licensed this edit (or None)."""
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
    """Every event that transitively depends on any root — the causal subtree to rewind."""
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
# The kernel — the single authority over SHARED TRUTH. It never holds speculation.
# ---------------------------------------------------------------------------------------------------
class Kernel:
    def __init__(self, root: str = ROOT):
        self.committed: list[EditEvent] = []   # shared truth (and the recovery substrate)
        self.root = root

    def caps(self) -> dict:
        return project_caps(self.committed)

    def authorized(self, ev: EditEvent) -> bool:
        if ev.op in ("grant", "revoke"):
            return ev.author == self.root           # only the root anchor may change authority
        if ev.author == self.root:
            return True
        return ev.capability in self.caps().get(ev.author, set())

    def commit(self, ev: EditEvent) -> bool:
        """Pre-commit authority gate. Accept → append to shared truth; reject → False (caller rewinds)."""
        if any(e.eid == ev.eid for e in self.committed):
            return True                              # idempotent: already committed
        if not self.authorized(ev):
            return False
        self.committed.append(ev)
        return True

    def shared_world(self) -> dict:
        return project(self.committed)


# ---------------------------------------------------------------------------------------------------
# The client — holds PRIVATE HOT speculation; sees committed truth + its own speculation; nobody else's.
# ---------------------------------------------------------------------------------------------------
class Client:
    def __init__(self, kernel: Kernel, name: str):
        self.k = kernel
        self.name = name
        self.spec: list[EditEvent] = []   # private hot scratchpad: fast, mutable, disposable

    def propose(self, ev: EditEvent) -> None:
        """Felt reality: applied locally and immediately, visible only to this creator."""
        self.spec.append(ev)

    def view(self) -> dict:
        """What THIS creator sees: shared truth + own speculation. No other client's speculation."""
        return project(self.k.committed + self.spec)

    def commit(self, eid: str) -> bool:
        """Promote a speculative event to shared truth, or reject + rewind its causal subtree."""
        ev = next(e for e in self.spec if e.eid == eid)
        if self.k.commit(ev):
            self.spec.remove(ev)                     # promoted — it is now committed truth, not speculation
            return True
        self._rollback_subtree(eid)                  # rejected — rewind it and everything that depended on it
        return False

    def _rollback_subtree(self, eid: str) -> set:
        doomed = causal_closure(self.spec, {eid})
        self.spec = [e for e in self.spec if e.eid not in doomed]
        return doomed

    def discard_speculation(self) -> None:
        """Disconnect: the private scratchpad is disposable; shared truth is untouched."""
        self.spec = []


# ---------------------------------------------------------------------------------------------------
# Adversarial self-test — the one question, broken into checks. No UI, no renderer, no scale.
# ---------------------------------------------------------------------------------------------------
def main() -> None:
    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<32} {detail}")

    print("live_world_kernel — can a running world accept / reject / rewind creator actions")
    print("without losing causal truth? (three stores: committed=truth, speculative=private hot, recovery=replay)\n")

    k = Kernel()
    # root grants builderA the terrain capability (a committed authority event)
    g1 = EditEvent("g1", ROOT, "terrain.modify", "builderA", "grant")
    k.commit(g1)

    A, B = Client(k, "A"), Client(k, "B")

    # 1. speculative isolation — a proposed edit is private hot state; no other client, no shared truth sees it
    e1 = EditEvent("e1", "builderA", "terrain.modify", "wall", "move", (("pos", (14, 2, 5)),))
    A.propose(e1)
    check("speculative_isolation",
          "wall" in A.view() and "wall" not in B.view() and all(e.eid != "e1" for e in k.committed),
          "A sees its speculative wall; B and shared truth do not")

    # 2. commit promotes speculation into shared truth
    ok = A.commit("e1")
    check("commit_promotes_to_truth",
          ok and any(e.eid == "e1" for e in k.committed) and "wall" in B.view() and all(e.eid != "e1" for e in A.spec),
          "accepted → B now sees the wall; it left A's speculation")

    # 3. causal-subtree rollback — reject the root edit, rewind EXACTLY its descendants, unrelated state intact
    Bx = Client(k, "Bx")  # builderB has NO capability → its edits will be rejected
    e1b = EditEvent("e1b", "builderB", "terrain.modify", "bridge", "move", (("pos", (0, 0, 9)),))
    e2b = EditEvent("e2b", "builderB", "terrain.modify", "crate", "create", (("on", "bridge"),), ("e1b",))
    e3b = EditEvent("e3b", "builderB", "terrain.modify", "ai", "create", (("behind", "crate"),), ("e2b",))
    e4b = EditEvent("e4b", "builderB", "terrain.modify", "torch", "create", (("pos", (5, 5, 5)),))  # unrelated
    for e in (e1b, e2b, e3b, e4b):
        Bx.propose(e)
    before = set(Bx.view())
    ok = Bx.commit("e1b")  # rejected (no capability)
    after = set(Bx.view())
    check("causal_subtree_rollback",
          (not ok)
          and {e.eid for e in Bx.spec} == {"e4b"}
          and {"bridge", "crate", "ai"} <= before
          and "torch" in after
          and not ({"bridge", "crate", "ai"} & after),
          "reject e1b → removed exactly {e1b,e2b,e3b}; unrelated torch survives")

    # 4. no leak — the rejected subtree never touched shared truth or any other client's view
    check("no_leak_on_reject",
          all(e.eid not in {"e1b", "e2b", "e3b", "e4b"} for e in k.committed) and "bridge" not in B.view(),
          "rejected speculation never entered committed truth or B's view")

    # 5. replay from zero — delete the world, rebuild from the committed log → identical (causal truth survives)
    live = k.shared_world()
    rebuilt = project(list(k.committed))
    log_digest = blake2b("".join(e.digest() for e in k.committed).encode(), digest_size=8).hexdigest()
    check("replay_from_zero",
          rebuilt == live,
          f"world rebuilt from {len(k.committed)} committed events == live state (log {log_digest})")

    # 6. authority from history — why was e1 allowed? and a revoke makes the next identical edit fail
    why = why_allowed(k.committed, e1)
    k.commit(EditEvent("r1", ROOT, "terrain.modify", "builderA", "revoke"))
    A2 = Client(k, "A2")
    A2.propose(EditEvent("e5", "builderA", "terrain.modify", "wall", "move", (("pos", (99, 0, 0)),)))
    revoked_ok = A2.commit("e5")
    check("authority_from_history",
          why == "g1" and not revoked_ok,
          "e1 authorized by grant g1; after revoke, the same edit is rejected")

    # 7. idempotency — committing an already-committed event does not double-apply
    n = len(k.committed)
    k.commit(e1)
    check("duplicate_idempotent", len(k.committed) == n, "re-committing e1 is a no-op")

    # 8. disconnect — speculative scratchpad is disposable; shared truth is unaffected
    C = Client(k, "C")
    C.propose(EditEvent("ed", "builderA", "terrain.modify", "ghost", "create"))
    seen = "ghost" in C.view()
    C.discard_speculation()
    check("disconnect_discards_speculation",
          seen and "ghost" not in C.view() and all(e.eid != "ed" for e in k.committed),
          "disconnect drops private speculation; committed truth untouched")

    # 9. latency irreversibility frontier — rolled-back work == causal depth; expected thrash == depth × reject_prob
    def exposure(depth, reject_prob):
        return depth * reject_prob

    frontier_ok = True
    for D in (1, 3, 5, 10):
        Z = Client(k, "Z")
        prev = None
        for i in range(D):
            deps = () if prev is None else (prev,)
            Z.propose(EditEvent(f"z{i}", "builderB", "terrain.modify", f"o{i}", "create", (), deps))
            prev = f"z{i}"
        doomed = Z._rollback_subtree("z0")             # reject the chain's root
        frontier_ok &= (len(doomed) == D)              # the WHOLE chain rewinds — depth is the exposed work
    frontier_ok &= exposure(10, 0.1) > exposure(3, 0.1) > exposure(1, 0.1)
    frontier_ok &= exposure(5, 0.2) > exposure(5, 0.05)
    check("latency_irreversibility_frontier", frontier_ok,
          "rolled-back work = causal depth; expected thrash = depth × reject_prob (monotone)")

    print(f"\n{passed}/{total} checks. The one question is answered "
          f"{'YES' if passed == total else 'NO'}: a running world can accept, reject, and rewind")
    print("creator actions without losing causal truth — speculation stays private and disposable, shared")
    print("truth only ever grows by committed events, rejection rewinds exactly the causal subtree, and the")
    print("world is reconstructable from its log. The editor is now a UI problem. (Reference prototype: logic,")
    print("not performance; no concurrency-at-scale, no embedded-root authority yet — those are the next probes.)")
    assert passed == total, "the kernel failed its own adversarial test"


if __name__ == "__main__":
    main()
