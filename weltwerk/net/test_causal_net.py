# SPDX-License-Identifier: AGPL-3.0-only
"""
test_causal_net.py — Phase 4 proofs (validity-not-outcome) for the causal replication thesis.

The load-bearing check is equivalence: the causal derivation (client re-derives from one event) reproduces
naive full object-sync, byte-identical. Everything else (byte savings, scope honesty) is measured, not
assumed.

  1. causal_equals_naive    — causal client == naive client == server state (byte-identical)  ← the crux
  2. byte_saving_positive   — causal sends fewer bytes than naive (1 event vs N records)
  3. scope_honest           — for the destroy model actual == potential ⇒ scope compression 0 (no inflation)
  4. determinism            — same event stream ⇒ identical server state on two independent servers
  5. reconnect_recovery     — a fresh client + full snapshot == the server after a stream
  6. no_superluminal        — only entities reachable from the event are changed (others untouched)

Run:  PYTHONHASHSEED=0 python3 test_causal_net.py
"""
from __future__ import annotations

from causal_net import (DEMO, Server, reconnect_snapshot, replicate_event, run_stream, state_hash)

# a coupled world (a feedback loop) to exercise the honest "actual approaches potential" case
COUPLED = """
world "C"
entity a:
  depends_on b
entity b:
  depends_on c
entity c:
  depends_on a
entity d:
  protects a
"""


def check(name, ok, detail):
    return (name, ok, detail)


def test_causal_equals_naive():
    r = replicate_event(DEMO, "generator")
    hs, hn, hc = state_hash(r["server"]), state_hash(r["naive"]["client"]), state_hash(r["causal"]["client"])
    return check("causal_equals_naive", hs == hn == hc,
                 f"server==naive==causal client state: {hs == hn == hc}")


def test_byte_saving_positive():
    r = replicate_event(DEMO, "generator")
    rep = r["report"]
    ok = rep["bytes_causal"] < rep["bytes_naive"] and rep["byte_saving"] > 0
    return check("byte_saving_positive", ok,
                 f"causal {rep['bytes_causal']}B < naive {rep['bytes_naive']}B (saving {int(rep['byte_saving']*100)}%)")


def test_scope_honest():
    # destroy model: every reachable dependent diverges ⇒ actual == potential ⇒ scope compression 0
    r = replicate_event(DEMO, "generator")
    rep = r["report"]
    ok = rep["actual"] == rep["potential"] and rep["scope_compression"] == 0.0
    return check("scope_honest", ok,
                 f"actual({rep['actual']})==potential({rep['potential']}), scope compression {rep['scope_compression']} (no inflation)")


def test_determinism():
    a = run_stream(DEMO, ["generator", "tree"])
    b = run_stream(DEMO, ["generator", "tree"])
    return check("determinism", state_hash(a) == state_hash(b),
                 f"same event stream ⇒ identical state: {state_hash(a) == state_hash(b)}")


def test_reconnect_recovery():
    s = Server(DEMO)
    s.apply("generator")
    client = reconnect_snapshot(s)               # late client gets a full snapshot
    return check("reconnect_recovery", state_hash(client) == state_hash(s.runtime),
                 f"reconnected client == server: {state_hash(client) == state_hash(s.runtime)}")


def test_no_superluminal():
    # destroying 'tree' (a leaf, reaches nothing) must change only 'tree'
    r = replicate_event(DEMO, "tree")
    changed = [k for k in r["server"] if r["server"][k]["status"] != "ok"]
    ok = changed == ["tree"]
    return check("no_superluminal", ok, f"destroy leaf 'tree' changes only itself: {changed}")


def main():
    results = [
        test_causal_equals_naive(),
        test_byte_saving_positive(),
        test_scope_honest(),
        test_determinism(),
        test_reconnect_recovery(),
        test_no_superluminal(),
    ]
    print("test_causal_net — Phase 4 causal replication (validity-not-outcome)\n")
    passed = 0
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:22s} {detail}")
        passed += int(ok)
    total = len(results)
    print(f"\n  {passed}/{total} checks. Sound iff {total}/{total}: causal derivation reproduces naive object-sync"
          f"\n  byte-identically, sends fewer bytes, reports scope compression HONESTLY (0 when actual≈potential),"
          f"\n  is deterministic, recovers on reconnect, and never changes an entity outside the event's reach.")
    assert passed == total, f"{total - passed} check(s) failed — the causal replication prototype is not sound"


if __name__ == "__main__":
    main()
