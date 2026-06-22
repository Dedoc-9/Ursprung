<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Lineage Scale — the closure test: optimization cannot erase history

Not a throughput benchmark. A **closure test on the one forbidden transition**, run when the latent
store becomes the dominant object:

```
digest present + lineage unavailable = severance
```

Earlier kernel checks proved objects can't appear without provenance, changes without events,
transitions without receipts, absence without diagnosis. This proves the last one — **optimization
cannot erase history** — which is the thing that would otherwise silently collapse the whole stack.

## Run

```bash
python3 experiments/reality_kernel/lineage_scale/scale_bench.py     # stdlib only; reuses the kernel
```

## Two planes, measured separately (so a fast cache cannot hide a missing lineage)

```
hot plane    (id, state, provenance_digest)   the runtime object   — cost of CARRYING identity
cold plane   digest → lineage graph           the historical object — cost of RECOVERING history
cache        digest → lineage (droppable)     the ONLY evictable thing; never canonical
```

## What it measures and asserts

The scale sweep reports build time, **retained lineage count**, digest collisions, resolve-latency
distribution (p50/p99), and peak memory — and asserts the invariant, not a speed:

```
N=10000    retained 10000/10000   collisions 0   resolve p50/p99 0.4/1.0 us   mem  12.8 MB   every_digest_resolves ✓
N=100000   retained 100000/100000 collisions 0   resolve p50/p99 0.5/1.4 us   mem 132.4 MB   every_digest_resolves ✓
N=500000   retained 500000/500000 collisions 0   resolve p50/p99 0.5/2.0 us   mem 653.0 MB   every_digest_resolves ✓
```

Five pressure modes, the centerpiece being the forbidden optimization:

```
steady_state                                  every committed digest resolves
eviction_of_cache_keeps_lineage               drop the droppable cache → canonical lineage still resolves
discard_live_lineage_is_detected_as_severance the FORBIDDEN op (drop canonical lineage for a live digest)
                                               is caught as PROVENANCE_SEVERED, not silently allowed
severance_never_returns_a_guess               a severed digest yields severance, never a fabricated lineage
partial_failure_no_unaccounted                a commit that raises mid-way leaves no half-state, no UNACCOUNTED
restart_recovery_all_resolve                  serialize → drop → reload: every hot digest still resolves
```

The distinction the bench defends operationally: dropping the *full hot representation* (keeping the
digest, with the lineage in the cold plane) is **compression** — category preserved. Dropping the
*canonical lineage* for a digest still referenced by the hot plane is **severance** — and the runtime
catches it rather than answering with a stale or guessed value. That is `compress ≠ sever`, measured
rather than asserted.

## Honest scope — every layer earns its own claim

```
Verified:   digest → lineage preserved under tested scale (to 5e5 here); no commit becomes UNACCOUNTED;
            compression preserves category; discarding live lineage is detected as severance.
Not tested: distributed / durable storage, NUMA / cache behaviour, GPU / frame-loop integration,
            adversarial external-persistence failure.
```

CPython caveat: a Python dict is O(1) hash, so resolve latency is flat and the cache-miss cost a real
expanded heap would pay is **hidden** — that flatness is the known blind spot, the substrate frontier
where the Rust CORE and a real store take over. The footprint here (~1.3 KB/artifact) is Python's
worst case, not the kernel's floor. The claim is the invariant, not the bytes.
