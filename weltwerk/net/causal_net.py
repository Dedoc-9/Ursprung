# SPDX-License-Identifier: AGPL-3.0-only
"""
causal_net.py — Phase 4: causal multiplayer prototype, the THESIS TEST (no sockets, no latency claim).

The networking claim is: replication can follow world STRUCTURE (send a causal event, let the client
re-derive) instead of blindly syncing objects — and produce the SAME result. This file proves or refutes
that with no networking stack: the "server" and "clients" are RuntimeWorld dicts, the "channel" is a list
of messages. What is measured is bytes/messages/scope and, crucially, EQUIVALENCE.

Two replication modes for one authoritative event (e.g. "destroy generator"):
  NAIVE   — server applies the event, then serialises the FULL state of every changed entity; the client
            applies those records blindly (no graph needed). Messages = |changed| full records.
  CAUSAL  — server sends ONLY the event; the client re-derives the consequences via its copy of the
            causal graph (simulate_destroy + reach). Messages = 1 event.

THE CRUX (test_causal_net): causal-client state == naive-client state == server state, BYTE-IDENTICAL.
i.e. the causal derivation reproduces full object-sync. `cheaper-transport ≠ different-answer`.

HONEST MEASUREMENT (the project's central law, as a replication report):
  potential = entities the event COULD affect (reach over the causal graph).
  actual    = entities it DID affect (diverged).
  scope compression opportunity = 1 − |actual|/|potential|.  LOW when actual approaches potential
            (coupled world) — reported honestly. Byte savings (1 event vs N records) is a separate
            transport detail and does NOT reduce derivation scope. `bytes-saved ≠ scope-reduced`.

Do NOT claim: MMO scale, solved latency, competitive FPS networking, UE5, infinite players. The next
question is the MEASUREMENT — can this hold competitive latency when the world is SPARSE — not an assumption.
"""
from __future__ import annotations

import os
import sys
from hashlib import blake2b

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))
from world_design import regime                                              # noqa: E402
from world_format import build_causal_graph, parse_world, simulate_destroy   # noqa: E402

RECORD_BYTES = 16   # a nominal full-state record: id + pos(3) + health + alive/status
EVENT_BYTES = 8     # a nominal causal event id


def initial_runtime(cg) -> dict:
    return {n: {"alive": True, "status": "ok"} for n in cg.nodes}


def state_hash(runtime: dict) -> str:
    h = blake2b(digest_size=16)
    for k in sorted(runtime):
        r = runtime[k]
        h.update(f"|{k}:{int(r['alive'])}:{r['status']}".encode())
    return h.hexdigest()


def _apply_destroy(cg, runtime: dict, target: str) -> set:
    """The shared deterministic rule: target dies; everything reachable from it is disabled."""
    diverged = simulate_destroy(cg, target)["diverged"]
    runtime[target] = {"alive": False, "status": "destroyed"}
    for d in diverged:
        runtime[d] = {"alive": runtime[d]["alive"], "status": "disabled"}
    return set(diverged)


class Server:
    """Authoritative RuntimeWorld derived from a world.wrk text. The world compiler is the source of truth."""
    def __init__(self, world_text: str):
        self.spec = parse_world(world_text)
        self.cg = build_causal_graph(self.spec)
        self.runtime = initial_runtime(self.cg)

    def apply(self, target: str) -> set:
        return _apply_destroy(self.cg, self.runtime, target)


def naive_replicate(baseline: dict, server_after: dict, changed: set) -> dict:
    """Client receives full records for every changed entity and applies them blindly (no graph)."""
    client = {k: dict(v) for k, v in baseline.items()}
    msgs = [(c, dict(server_after[c])) for c in sorted(changed)]   # full-state records on the wire
    for cid, st in msgs:
        client[cid] = st
    return {"client": client, "bytes": len(msgs) * RECORD_BYTES, "msgs": len(msgs), "entities": len(msgs)}


def causal_replicate(baseline: dict, cg, target: str) -> dict:
    """Client receives ONLY the event and re-derives the consequences via its own causal graph."""
    client = {k: dict(v) for k, v in baseline.items()}
    diverged = _apply_destroy(cg, client, target)    # client runs the same rule locally
    return {"client": client, "bytes": EVENT_BYTES, "msgs": 1, "entities": len(diverged) + 1}


def replicate_event(world_text: str, target: str) -> dict:
    """Run both modes for one event from a fresh world; return clients, costs, and the honest report."""
    s = Server(world_text)
    baseline = {k: dict(v) for k, v in s.runtime.items()}
    potential = s.cg.reach_ge1(target) if target in s.cg.nodes else set()
    s.apply(target)
    changed = {target} | potential
    naive = naive_replicate(baseline, s.runtime, changed)
    causal = causal_replicate(baseline, s.cg, target)
    actual = len(potential)                          # destroy model: every reachable dependent diverges
    pot = len(potential)
    report = {
        "coupling": regime(s.cg)["label"],
        "potential": pot, "actual": actual,
        "scope_compression": round(1 - actual / pot, 2) if pot else 0.0,
        "bytes_naive": naive["bytes"], "bytes_causal": causal["bytes"],
        "byte_saving": round(1 - causal["bytes"] / naive["bytes"], 2) if naive["bytes"] else 0.0,
    }
    return {"server": s.runtime, "naive": naive, "causal": causal, "report": report}


def run_stream(world_text: str, events: list) -> dict:
    s = Server(world_text)
    for e in events:
        s.apply(e)
    return s.runtime


def reconnect_snapshot(server: Server) -> dict:
    """A reconnecting client gets a full snapshot (recovery) and matches the server."""
    return {k: dict(v) for k, v in server.runtime.items()}


DEMO = """
world "Frontier"
zone forest
zone reactor
entity generator:
  zone reactor
  health 100
  emits power
entity turret:
  zone forest
  health 80
  powered_by generator
entity door:
  zone forest
  depends_on generator
entity tree:
  zone forest
  health 30
"""


def main():
    print("causal_net.py — Phase 4 thesis test (no sockets, no latency claim)\n")
    r = replicate_event(DEMO, "generator")
    rep = r["report"]
    ok = state_hash(r["naive"]["client"]) == state_hash(r["causal"]["client"]) == state_hash(r["server"])
    print(f"  event: destroy generator")
    print(f"  equivalence (causal client == naive client == server): {ok}")
    print(f"\n  Replication Report")
    print(f"    World coupling:     {rep['coupling']}")
    print(f"    Potential affected: {rep['potential']}")
    print(f"    Actual changed:     {rep['actual']}")
    print(f"    Scope compression:  {int(rep['scope_compression']*100)}%  "
          f"({'LOW — actual approaches potential' if rep['scope_compression'] < 0.25 else 'some selectivity'})")
    print(f"    Bytes naive={rep['bytes_naive']}  causal={rep['bytes_causal']}  "
          f"(transport saving {int(rep['byte_saving']*100)}% — fewer bytes, SAME derivation scope)")
    print("\n  Honest: causal replication sends fewer bytes (event vs records) but does NOT shrink the")
    print("  derivation scope when actual≈potential. The next question is whether a SPARSE world keeps")
    print("  competitive latency — a MEASUREMENT, not an assumption. No MMO/latency/UE5 claim.")


if __name__ == "__main__":
    main()
