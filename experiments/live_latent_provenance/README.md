<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Live / Latent Provenance — provenance-preserving compression under runtime constraints

Not a new layer trying to explain reality — a **stress test of the existing invariant** at a new
pressure. The earlier phases asked whether a claim keeps its floor, a coordinate its status, an
edge its support, a latent its claim, an inference its price, an edit its source, ignorance its
diagnosis. This asks the same question under a frame budget:

> Can a runtime keep provenance when it is forced to **compress**?

The invariant, stated for the runtime:

```
Provenance identity survives representation change.
```

which is exactly the Phase-5 recursion at a different layer:

```
Phase 5:   latent coordinate can change      Runtime:   execution representation can change
           claim identity cannot                        provenance identity cannot
```

## The split (where "4.13 ms" actually lives — not in the renderer)

```
frame(t):     execute        — the hot path carries only {state, transform, provenance_digest}
background:   preserve why    — the latent store resolves a digest to the full lineage on demand
```

The hot loop never asks *"why is this object true?"*. It asks *"what is the **identity** of the
explanation attached to this object?"* — one digest, O(1) to carry, independent of lineage depth.
A high-performance reality stack does not need every frame to carry the universe of explanation; it
needs the frame to carry an address, and the background to keep the thing it addresses.

```
LiveObject { state, transform, provenance_digest }      # hot path
ProvenanceStore: digest ──► origin · edit lineage · assumptions
                                  · survival tests · failures · verification status   # latent
```

## Run

```bash
python3 experiments/live_latent_provenance/run.py     # stdlib only; deterministic; 9/9
```

## The severance test (the sharp one)

A real system **must** compress — so compression has to be allowed. The danger is not latency; it
is an optimization that silently converts `why this exists` into `it exists`. So nulling the digest
must **not** degrade to `unknown`. The structure remains (gravity is still `0.5`); the *history* was
destroyed. That is a different category, and the runtime names it:

```
resolve(a81f92…)  → developer edit → gameplay_constraint → world_v12     (resolved)
resolve(NULL)     → PROVENANCE_SEVERED      (not `unknown`; structure remains, history lost)
```

A missing digest is a **runtime failure mode, not a silent fallback.** It connects back to the
failure taxonomy as a fourth, runtime-level mode — kept crisply distinct from the other three:

```
UNACCOUNTED          never recorded                 (no digest ever assigned — the silent gap)
PROVENANCE_SEVERED   recorded identity lost          (digest nulled or dangling; structure remains)
resource_limit       observer insufficient
assumption_limit     admissibility insufficient
```

## Calibration — `PROVENANCE_SEVERED` is not the epistemic `severance`

The failure-taxonomy `severance` means a signal is **absent in the world** (`I(X;O)=0`),
observer-independent and absolute. Runtime `PROVENANCE_SEVERED` means the world still has the
structure but the **runtime threw away its record of why**. Same word, different objects: the
runtime mode is class-relative and repairable in principle (re-commit the lineage); the epistemic
one is not. The code keeps them separate on purpose; do not conflate them.

## What it earns (9 checks)

```
hot path carries only a digest                 (full provenance ≠ hot-path representation)
the digest resolves to the full provenance     (compression conserves the lineage)
representation change keeps provenance identity (re-encode state/transform → same provenance)
severance is a distinct failure, not `unknown`  (PROVENANCE_SEVERED; structure remains)
severed ≠ unaccounted                           (lost-after-recording ≠ never-recorded)
a dangling digest is severed too                (pointing nowhere is the same failure)
optimization may compress, not sever            (compress → traceable; sever → caught)
the frame admits the traceable, refuses the severed   (the contract boundary enforces it)
```

Earned separators: **`full provenance ≠ hot-path representation`** and **`compression ≠ severance`**.

## Bench record — first real-silicon contact (`probe.py`)

```bash
python3 experiments/live_latent_provenance/probe.py     # a MEASUREMENT, not a claim
```

The deterministic `run.py` proves the contract; `probe.py` puts it under a real monotonic clock to
find where the abstraction leaks into hardware. The point is not "4.13 ms achieved" — it is to record
exactly what the measurement did and did not license, so a later optimization pass cannot quietly
promote a scoped observation into a generalized claim.

```
Question
    Can provenance survive runtime COMPRESSION under a real clock?

Measured (the contract, under a fixed-Hz loop)
    hot path carries state + transform + provenance_digest, nothing more
    full lineage resolves from the digest, off the frame budget
    severed provenance is detected in-frame, never treated as `unknown`
    latent resolve requests may be dropped / deferred under backpressure (counted)
    commits may NOT be dropped

Results (this sandbox's Linux clock — NOT the user's Windows)
    provenance lookup overhead was small at the tested scale
        (~0.06 ms hot-path work for 200 objects; ~0.3 us/object — the digest carry is near-free here)
    timing jitter was dominated by scheduler / clock behaviour, not by provenance metadata
        (240 Hz target 4.167 ms; interval p50 ~4.29 ms; worst frame 5.02 ms on the locked-queue path)
    CPython ring-vs-queue differences are implementation observations only
        (ring jitter 0.040 vs queue 0.075 ms — real, but GIL-bound; not a lock-free silicon result)
    the contract held every frame: planted severed + unaccounted objects caught, zero drops

Not established (do not let the next pass assume these)
    lock-free behaviour            (GIL serializes; the ring is not a lock-free demonstration)
    cache-locality behaviour       (a Python dict hides it; resolve latency stayed flat under store growth)
    silicon-level frame guarantees
    GPU runtime viability

Frontier
    a native implementation where atomics, the cache hierarchy, and allocation behaviour are
    actually OBSERVABLE — the only place these four can be measured rather than assumed.
```

### The reversal (the strongest finding, because the data falsified the expectation)

The bench was built on the worry that *provenance might threaten performance*. The measurement says
the opposite: **provenance metadata is not the first-order threat to the frame budget — uncontrolled
time sources are.** The hot-path provenance carry was near-free at this scale; the timeline raggedness
came from `time.sleep` granularity (mild on Linux, expected ~15 ms and budget-breaking on Windows).
This is a project-consistent result precisely because it came from letting the measurement overturn
the prior, not confirm it. The ghosts, classified by origin:

```
cadence overshoot / jitter   timing origin        (time.sleep granularity; OS-dependent; the real variable)
flat resolve latency vs size measurement-limit     (Python dict O(1) hides the cache cost; Rust will expose it)
ring < queue jitter delta    implementation        (CPython machinery only; not generalizable to silicon)
```

### Separators this bench adds

```
provenance_digest in hot path  ≠  performance collapse   (measured: near-free carry at tested scale)
declared runtime constraint    ≠  silicon guarantee       (4.13 ms is a target until real hardware says so)
Python timing result           ≠  hardware architecture result   (GIL/sleep ⇒ CPython behaviour, not silicon)
```

The clean staircase this preserves, with no leap between steps: **Python** proves the contract
survives compression; **Rust** proves the mechanism survives real concurrency primitives;
**GPU/runtime** proves the world loop survives a real substrate.

### Iteration — first-class channels + deadline pacing (`channels.py`, `run_channels.py`)

Two follow-ups, each scoped by the boundary above. First, the policy *drop resolve requests, never
commits* was lifted from a runtime check into the **type boundary**: a `Commit` cannot be constructed
without provenance, state advances only through `CommitChannel.apply` (which has no drop surface and
refuses an untraceable commit), and `ResolveRing` (which may drop, counted) has no `apply`. So the
danger the probe named — *buffer full → drop event → world advances → UNACCOUNTED* — is now an
unreachable program state, not a discouraged one (7/7, `run_channels.py`).

Second, the probe's reversal said the real variable was clock discipline, so `probe.py` gained a
`sleep` vs spin-to-`deadline` pacing A/B. Measured (sandbox Linux):

```
240 Hz (budget 4.167 ms)   sleep:    interval p50 4.267, jitter 0.047, 234 frames
                           deadline: interval p50 4.167, jitter 0.004, 240 frames   (~12× tighter, on budget)
```

Deadline pacing hit the budget exactly and cut jitter ~12×, while commits flowed 1200/0 with zero
drops — confirming the runtime can hold its temporal contract without confusing scheduler behaviour
for simulation behaviour. **Non-transfer caveat (named, not measured):** this cheapness is
Linux-relative. Windows timer granularity (~15 ms) exceeds a 4.167 ms frame, so the coarse-sleep step
would overshoot every frame; a sub-granularity budget there requires spinning the whole frame (a full
core) or raising OS timer resolution. New separator: **`Linux scheduler result ≠ Windows scheduler
result`** — `deadline pacing is cheap` holds only where sleep granularity is below the budget.

## Honest bounds — the narrow claim

The claim is **provenance-preserving compression under runtime constraints**, *not*
"provenance-bearing reality at 4.13 ms" — the latter implies silicon validation this bench does not
have. There is no GPU, no real frame timing, no real-time rendering here; those remain the un-faked
frontier (every constructed millisecond expires on real silicon). What is shown is the architectural
property that *licenses* such a stack: execution can be compressed to a digest, the full lineage
stays recoverable, and an optimization that severs provenance is a caught failure rather than a
silent collapse. The contract this hands the future renderer/world-model/agent stack:

> The world may become faster, smaller, learned, generated, distributed, or optimized.
> It may **not** become untraceable.
