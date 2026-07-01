# SPDX-License-Identifier: AGPL-3.0-only
"""phase10_airgap.py — RepE Phase 10: the air-gap layer (AetherPulse no-write-back + content-hash hardening).

Capstone hardening from the sealed core. `AetherPulse/snapshot.py`'s load-bearing invariant is NO WRITE-BACK:
the observe path reads a snapshot of the gated L1 state but cannot mutate it, and L1 tampering is caught because
the recomputed hash diverges. This layer applies that discipline to the whole RepE harness:

  * GATED state = the committed decision record (input digest, applied steers/alpha). Only a Grounded action
    (Phase 9) may commit to it, and every commit RE-SEALS the content hash.
  * OBSERVE = probe / monitor / audit / diagnostics. They get a DEEP-COPIED read-only snapshot; mutating it
    cannot reach the gated state. `observation != authority`.
  * TAMPER-EVIDENCE = any out-of-band mutation (external tampering, hardware bit-flip, nondeterministic drift)
    shifts the content hash; `verify()` fails closed (TAMPERED_FAIL_CLOSED).
  * REPLAY = the hash is content-addressed, so the same inputs + same grounded sequence reproduce the same hash.

Verified by `--selftest` (GPU-free, 6/6): observer mutation can't reach the gated state; only a Grounded action
commits (real weltwerk Grounded[T] via `.value` OR a Phase-9-style stub via `.get()`); an ungrounded commit is
refused; out-of-band tampering fails closed; replay is deterministic.

HONEST BOUND (the same one `AetherPulse/snapshot.py` states): this is tamper-EVIDENT and replay-verifiable, NOT
immutable. It detects tampering/drift and fails closed; it does not prevent an attacker who executes code that
recomputes the hash consistently. `borrow-checker-clean != air-gap-sound`; `detection != prevention`.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import copy


def state_hash(state):
    """Content-addressed hash of the gated state (the harness analogue of AetherPulse's l1_hash)."""
    return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()


class AirGap:
    """No-write-back gated state + content-addressed hash. Observers read a deep copy; only Grounded commits mutate."""

    def __init__(self, gated_state):
        self._state = copy.deepcopy(gated_state)
        self._hash = state_hash(self._state)

    def observe(self):
        """Read-only snapshot for observers: a deep copy + the gate hash. Mutating it cannot reach gated state."""
        return {"snapshot": copy.deepcopy(self._state), "hash": self._hash}

    def verify(self):
        """Fail-closed tamper/drift check: recompute the hash and compare to the sealed one."""
        ok = state_hash(self._state) == self._hash
        return {"ok": ok, "status": "OK" if ok else "TAMPERED_FAIL_CLOSED"}

    def commit(self, grounded, mutate_fn):
        """Only a Grounded action may mutate the gated state; re-seal after. Accepts a real weltwerk Grounded[T]
        (`.value`) OR a Phase-9-style stub (`.get()`) — so no per-call shim is needed. `observation != authority`."""
        if hasattr(grounded, "value"):
            payload = grounded.value
        elif hasattr(grounded, "get"):
            payload = grounded.get()
        else:
            raise PermissionError("commit requires a Grounded action (weltwerk Grounded[T] .value or Phase-9 .get()) "
                                  "— observation != authority")
        mutate_fn(self._state, payload)
        self._hash = state_hash(self._state)
        return self._hash

    def _tamper(self, mutate_fn):        # test hook: simulate out-of-band tampering (mutate WITHOUT re-hashing)
        mutate_fn(self._state)


class _G:                                # minimal Grounded stub (Phase 9 provides one via .get())
    def __init__(self, v): self._v = v
    def get(self): return self._v


class _GV:                               # weltwerk-style Grounded stub: exposes .value (not .get())
    def __init__(self, v): self.value = v


def selftest() -> int:
    init = {"input_digest": "abc123", "applied": []}
    ag = AirGap(init)

    obs = ag.observe()
    obs["snapshot"]["applied"].append({"alpha": 99.0}); obs["snapshot"]["input_digest"] = "HACKED"
    ok_nowrite = ag.verify()["ok"] and ag._state["applied"] == []

    h0 = ag._hash
    ag.commit(_G(0.5), lambda s, a: s["applied"].append({"alpha": a}))
    ok_commit = ag.verify()["ok"] and ag._state["applied"] == [{"alpha": 0.5}] and ag._hash != h0

    agv = AirGap(init)                    # real-weltwerk-style Grounded (.value) is accepted (widened commit)
    agv.commit(_GV(0.7), lambda s, a: s["applied"].append({"alpha": a}))
    ok_value = agv.verify()["ok"] and agv._state["applied"] == [{"alpha": 0.7}]

    try:
        ag.commit(0.9, lambda s, a: s["applied"].append(a)); ug = False
    except PermissionError:
        ug = True
    ok_ungrounded = ug

    ag._tamper(lambda s: s["applied"].append({"alpha": 7.7}))
    v = ag.verify(); ok_tamper = (v["ok"] is False and v["status"] == "TAMPERED_FAIL_CLOSED")

    a1 = AirGap(init); a2 = AirGap(init)
    for a in (a1, a2):
        a.commit(_G(0.5), lambda s, x: s["applied"].append({"alpha": x}))
    a3 = AirGap(init); a3.commit(_G(0.6), lambda s, x: s["applied"].append({"alpha": x}))
    ok_replay = (a1._hash == a2._hash) and (a1._hash != a3._hash)

    print(f"[selftest] no write-back: observer mutation cannot reach gated state  : {ok_nowrite}")
    print(f"[selftest] only a Grounded action commits + re-seals (.get stub)      : {ok_commit}")
    print(f"[selftest] real weltwerk Grounded (.value) also commits (seam closed) : {ok_value}")
    print(f"[selftest] ungrounded commit refused (observation != authority)       : {ok_ungrounded}")
    print(f"[selftest] tamper-evidence: out-of-band mutation -> fail closed       : {ok_tamper}  ({v['status']})")
    print(f"[selftest] deterministic content-addressed replay (same in->same hash): {ok_replay}")
    ok = ok_nowrite and ok_commit and ok_value and ok_ungrounded and ok_tamper and ok_replay
    print(f"[selftest] {'PASS 6/6 - air-gap layer valid (observe-only + tamper-evident + replayable)' if ok else 'FAIL'}")
    print("[frame]    AetherPulse no-write-back: observation != authority; only a Grounded steer crosses into")
    print("[frame]    gated state; tampering/drift shifts the hash and fails closed.")
    print("[bound]    HONEST: tamper-EVIDENT + replay-verifiable, NOT immutable — detects, does not prevent an")
    print("[bound]    attacker who recomputes the hash consistently (same bound AetherPulse/snapshot states).")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="RepE Phase 10 air-gap layer (no-write-back + content hash)")
    ap.add_argument("--selftest", action="store_true", help="verify observe-only + tamper-evidence + replay")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("wrap the gated decision record in AirGap; observers use observe(); only Grounded steers commit().")


if __name__ == "__main__":
    main()
