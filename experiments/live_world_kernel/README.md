<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# live_world_kernel — the smallest adversarial embedded-authoring kernel

Not an editor, a renderer, or an MMO. The smallest thing that can **kill or vindicate** the embedded-authoring
idea from [`docs/EMBEDDED_AUTHORING.md`](../../docs/EMBEDDED_AUTHORING.md). It answers exactly one question:

> **Can a running world accept, reject, and rewind creator actions without losing causal truth?**

If yes, the editor is a UI problem. If no, the larger engine vision collapses before it needs a renderer.

**Status — VERIFIED.** Ran 2026-06-22 (`PYTHONHASHSEED=0`, Python 3, Windows): **9/9 checks PASS**, answer
**YES — within the reference scope stated below**. `declared ≠ verified`: the YES is a property of the
single-process *logic*, not yet of a system under concurrency, latency, or scale.

```bash
PYTHONHASHSEED=0 python3 live_world_kernel.py
```

## Result — verified (9/9)

The reference passed its own adversarial self-test on the author's machine (the machine that runs it is the
verifier):

```
[PASS] speculative_isolation             A sees its speculative wall; B and shared truth do not
[PASS] commit_promotes_to_truth          accepted → B now sees the wall; it left A's speculation
[PASS] causal_subtree_rollback           reject e1b → removed exactly {e1b,e2b,e3b}; unrelated torch survives
[PASS] no_leak_on_reject                 rejected speculation never entered committed truth or B's view
[PASS] replay_from_zero                  world rebuilt from 2 committed events == live state (log 98a401876bd92998)
[PASS] authority_from_history            e1 authorized by grant g1; after revoke, the same edit is rejected
[PASS] duplicate_idempotent              re-committing e1 is a no-op
[PASS] disconnect_discards_speculation   disconnect drops private speculation; committed truth untouched
[PASS] latency_irreversibility_frontier  rolled-back work = causal depth; expected thrash = depth × reject_prob
9/9 checks — answer: YES (within scope)
```

**What it proves** (under the stated conditions): the causal-truth machinery is sound *in the small* —
speculation is private and disposable, shared truth grows only by committed events, **rejection rewinds exactly
the causal subtree and nothing else**, authority is replayable history (not an annotation), and the world
reconstructs from its log (digest `98a401876bd92998`). The load-bearing claim — *causal-subtree rollback
without corrupting unrelated state* — held against the adversarial case (`e1b → e2b → e3b` rejected while the
unrelated `e4b` survived). That is the provenance claim, made measurable and passed.

**What it does NOT prove** (`declared ≠ verified`): nothing about *scale*. This is single-process logic — no
concurrency-at-scale (the common lethal failure: many actors, one region), no networking or real latency
(check 9's frontier is a **surrogate**, not a measured human-trust threshold), external-root authority only
(the embedded-root / genesis case is open), and no performance claim. So "the editor is a UI problem" is true
*conditional on unscaled, single-process logic*; the boundary that actually decides the engine vision —
concurrency — is the next probe, not this one. The pass means the idea **earned the right to be scaled**, not
that it has been.

## What it changes — editor and runtime are one state of matter

Historically, engines treat **editing** and **playing** as two different states of matter, separated by a
*phase transition*: an authoring tool mutates an offline world (Unreal Editor, Maya, Blender) → build → export
→ deploy → a running game nobody can author without breaking it. The arrow runs one way. A runtime edit is a
hot-reload hack or simply impossible, because a live world has no honest way to accept an authored change while
preserving determinism, authority, and replay — so the two states are kept in separate phases, with a wall
between them.

**This kernel collapses the phase transition.** An editing action and a gameplay action are the *same
primitive* — an `EditEvent` committed to the one trajectory — differing only in (a) the capability the event
requires and (b) the source that emitted it. There is no offline state to build from and ship: the world never
leaves "running" in order to be edited. "Editing" is just a *privileged event stream into the live world*, and
because it is the identical primitive to a gameplay mutation, it inherits replay, provenance, authority, and
undo **for free** — as consequences of the substrate, not as bolted-on tooling. The build/deploy wall —
historically a change of *state* — becomes a **capability check**, not a phase change.

So editor and runtime are not two states of matter bridged by a pipeline; they are **one substrate**,
distinguished only by who is allowed to emit what. The prototype shows this directly: "move the wall" and any
in-world mutation travel the identical `propose → commit` path through the same kernel — there is no second
code path for "edit mode." (Scope, as above: demonstrated in single-process logic. The collapse is a property
of the substrate, shown in the small; whether it survives concurrency and scale is the next probe.
`declared ≠ verified`.)

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
