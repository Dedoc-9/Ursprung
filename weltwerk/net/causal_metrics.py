# SPDX-License-Identifier: AGPL-3.0-only
"""
causal_metrics.py — Phase 4: competitive-readiness instrumentation (METRICS ONLY, no latency claim).

Adds deterministic cost accounting to the causal replication path so the economics are MEASURED, not
assumed. All costs are deterministic op-counts (graph traversals, entity mutations, bytes); wall-clock is
deliberately omitted as a verdict (it is nondeterministic). The project already proved the advantage is
regime-dependent — so this also emits the honest warning when a world is too coupled to compress.

Per causal event (e.g. destroy X):
  causal_eval_cost   — graph-traversal ops to compute the footprint reach(X)        (the derivation cost)
  event_cost         — entities mutated = |footprint|                               (runtime work)
  replication_naive  — bytes to send a full record for every changed entity         (|footprint|·RECORD)
  replication_causal — bytes to send ONE event (+ the client pays causal_eval_cost to re-derive)
  reconstruction_snapshot — bytes for a reconnecting client to full-resync          (N·RECORD)
  reconstruction_replay   — ops to rebuild by replaying the event(s)                (Σ causal_eval_cost)

WARNING (honest): when |footprint|/N ≥ 0.5 the world is coupled enough that Actual ≈ Potential and
"causal compression is unavailable" — sending an event saves transport bytes but the client still
re-derives most of the world. `bytes-saved ≠ scope-reduced`. NOT a latency claim.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from causal_net import EVENT_BYTES, RECORD_BYTES, Server   # noqa: E402

DENSE_THRESHOLD = 0.5   # footprint/N at/above which causal compression is unavailable (declared policy)


def reach_counted(edges: dict, start: str) -> tuple:
    """reach(start) with a deterministic traversal-op counter (node pops). ops = derivation cost."""
    seen, ops, st = set(), 0, list(edges.get(start, set()))
    while st:
        n = st.pop()
        ops += 1
        if n not in seen:
            seen.add(n)
            st.extend(edges.get(n, set()))
    return seen, ops


def instrument_event(world_text: str, target: str) -> dict:
    s = Server(world_text)
    cg = s.cg
    n = len(cg.nodes) or 1
    footprint, eval_ops = reach_counted(cg.edges, target) if target in cg.nodes else (set(), 0)
    fp = len(footprint) + (1 if target in cg.nodes else 0)     # +target itself
    metrics = {
        "world_entities": n,
        "footprint": fp,
        "causal_eval_cost": eval_ops,
        "event_cost": fp,
        "replication_naive_bytes": fp * RECORD_BYTES,
        "replication_causal_bytes": EVENT_BYTES,
        "client_rederive_cost": eval_ops,                       # the client pays this instead of receiving records
        "reconstruction_snapshot_bytes": n * RECORD_BYTES,
        "reconstruction_replay_ops": eval_ops,
        "footprint_fraction": round(fp / n, 2),
    }
    metrics["transport_saving"] = round(1 - metrics["replication_causal_bytes"] / metrics["replication_naive_bytes"], 2) \
        if metrics["replication_naive_bytes"] else 0.0
    metrics["warning"] = ("causal compression unavailable: Actual ≈ Potential"
                          if fp / n >= DENSE_THRESHOLD else None)
    return metrics


def report(world_text: str, target: str) -> str:
    m = instrument_event(world_text, target)
    L = ["CAUSAL COST METRICS (deterministic op-counts; MEASURED, no latency claim)",
         f"  world entities:        {m['world_entities']}",
         f"  event footprint:       {m['footprint']}  ({int(m['footprint_fraction']*100)}% of world)",
         f"  causal eval cost:      {m['causal_eval_cost']} traversal ops",
         f"  event (runtime) cost:  {m['event_cost']} entity mutations",
         f"  replication: naive {m['replication_naive_bytes']}B  vs  causal {m['replication_causal_bytes']}B"
         f"  (transport saving {int(m['transport_saving']*100)}%)",
         f"  reconstruction: snapshot {m['reconstruction_snapshot_bytes']}B  vs  replay {m['reconstruction_replay_ops']} ops"]
    if m["warning"]:
        L.append(f"  ⚠ {m['warning']}")
    else:
        L.append(f"  ✓ sparse footprint — causal compression available")
    return "\n".join(L)


if __name__ == "__main__":
    from causal_net import DENSE_WORLD, SPARSE_WORLD
    print("causal_metrics.py — Phase 4 instrumentation (metrics only)\n")
    print("DENSE world, destroy generator:")
    print(report(DENSE_WORLD, "generator"))
    print("\nSPARSE world, destroy generator:")
    print(report(SPARSE_WORLD, "generator"))
    print("\n  costs are op-counts (deterministic); wall-clock is intentionally not a verdict. No latency claim.")
