<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# live_world_kernel — the smallest adversarial embedded-authoring kernel

Not an editor, a renderer, or an MMO. The smallest thing that can **kill or vindicate** the embedded-authoring
idea from [`docs/EMBEDDED_AUTHORING.md`](../../docs/EMBEDDED_AUTHORING.md). It answers exactly one question:

> **Can a running world accept, reject, and rewind creator actions without losing causal truth?**

If yes, the editor is a UI problem. If no, the larger engine vision collapses before it needs a renderer.

```bash
PYTHONHASHSEED=0 python3 live_world_kernel.py
```

## Three stores, kept distinct

The load-bearing correction this prototype enforces — blurring these is what makes rollback expensive:

| Store | Role | Properties |
|---|---|---|
| **committed** | shared truth | the canonical event log; the only thing other clients observe; grows only by accepted events |
| **speculative** | private hot belief | a per-client scratchpad: fast, mutable, **disposable**; never observed by others or made a contract until a commit promotes it |
| **recovery** | replayable history | the committed log itself — "why is the world this way?" is answered by re-folding it, never by trusting live state |

Prediction is a *scratchpad*, not a sealed reserve. An edit is an **event**, never a direct mutation:
`propose()` touches only private speculation (felt reality, instant); `commit()` runs the authority gate and
either **promotes** the event into shared truth or **rejects** it and rewinds the rejected event with its
entire **causal subtree** — exactly its transitive descendants, nothing unrelated.

## What the self-test proves (9 checks)

1. **speculative_isolation** — a proposed edit is private; no other client and no committed truth sees it.
2. **commit_promotes_to_truth** — an accepted edit becomes shared truth; other clients now see it.
3. **causal_subtree_rollback** — rejecting `E1` (with `E2`→`E3` depending on it, plus an unrelated `E4`)
   removes *exactly* `{E1,E2,E3}` and leaves `E4` intact. The provenance claim, made measurable.
4. **no_leak_on_reject** — the rejected subtree never entered committed truth or any other client's view.
5. **replay_from_zero** — delete the world, rebuild from the committed log → identical state.
6. **authority_from_history** — "why was this edit allowed?" resolves to the committed grant that licensed it;
   a revoke makes the same edit fail afterward (authority is an event, not an annotation).
7. **duplicate_idempotent** — committing an already-committed event is a no-op.
8. **disconnect_discards_speculation** — the private scratchpad is disposable; shared truth is untouched.
9. **latency_irreversibility_frontier** — rolled-back work equals causal depth; expected thrash is
   `depth × reject_probability`. The *felt-reality* analogue of the irreversibility frontier — the quantity to
   measure next: how much speculative divergence a creator tolerates before trust collapses.

## Honest scope (what this is NOT)

A **logic reference**, not a performance system. No concurrency-at-scale, no networking, no UI, no renderer.
Authority uses an **external root** anchor (the embedded-root / genesis variant is left open). The latency
frontier is a *surrogate metric*, not a measured human-trust threshold. A Rust port (validated against this
reference via conformance vectors, the same method used for `reality_kernel/core_rs`) is the natural next
step. `declared ≠ verified`. This prototype exists to force the boundary to reveal itself — and if it fails,
the failure (concurrency, authority, provenance cost, contract leak) answers the theory directly.
