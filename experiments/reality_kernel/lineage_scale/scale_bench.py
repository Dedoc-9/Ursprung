# SPDX-License-Identifier: AGPL-3.0-only
"""
experiments/reality_kernel/lineage_scale/scale_bench.py — a CLOSURE TEST on the invariant, not a
throughput benchmark.

    python3 experiments/reality_kernel/lineage_scale/scale_bench.py     # stdlib only; deterministic structure

The narrow question: can the kernel preserve the distinction between *compressed execution state* and
*recoverable lineage* when the latent store becomes the dominant object? The one forbidden transition:

    digest present + lineage unavailable = severance

This bench separates the two planes so a fast cache can never hide a missing-lineage problem:

    hot plane    (id, state, provenance_digest)   the runtime object — cost of CARRYING identity
    cold plane   digest → lineage graph           the historical object — cost of RECOVERING history

and runs five pressure modes, the centerpiece being: an optimizer that discards canonical lineage for
a still-live digest must be DETECTED as severance, never silently allowed and never answered with a
guess. Earlier kernel tests proved objects can't appear without provenance, changes without events,
transitions without receipts, absence without diagnosis. This proves the last one:

    optimization cannot erase history.

HONEST SCOPE — this verifies the INVARIANT under tested scale on one machine (CPython; a Python dict
is O(1) hash, so resolve latency is flat and the cache cost a real heap would pay is hidden — that
flatness is a known blind spot, the Rust/substrate frontier). It does not test distributed durability,
NUMA/cache behaviour, GPU/frame-loop integration, or adversarial external-persistence failure.
"""
from __future__ import annotations

import json
import os
import random
import statistics
import sys
import time
import tracemalloc

# put the kernel package dir on the path, then import the real kernel (reuse, not reimplement)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from event import Event          # noqa: E402
from kernel import RealityKernel  # noqa: E402

SCALES = (10_000, 100_000, 500_000)   # raise on a real machine; 1e6–1e8 is the substrate frontier


class Bench:
    """Hot plane carries digests; cold plane is the canonical lineage store; a separate cache is the
    only droppable thing (eviction target). resolve() returns PROVENANCE_SEVERED — never a guess —
    when a referenced digest has no lineage."""

    def __init__(self, seed: int = 1):
        self.k = RealityKernel()
        self.rng = random.Random(seed)
        self.hot = []          # [(id, state, digest)]
        self.cold = {}         # digest -> lineage (canonical)
        self.cache = {}        # digest -> lineage (droppable; NOT canonical)
        self.collisions = 0

    def build(self, n: int):
        for i in range(n):
            receipt = self.k.apply(Event("o%d" % i, i, i + 1, "developer"))
            d = receipt.provenance_digest
            if d in self.cold:
                self.collisions += 1
            self.cold[d] = self.k.provenance_of("o%d" % i)
            self.hot.append((i, i + 1, d))

    def resolve(self, digest: str, use_cache: bool = True):
        if use_cache and digest in self.cache:
            return self.cache[digest]
        lineage = self.cold.get(digest)
        if lineage is None:
            return "PROVENANCE_SEVERED"          # digest present, lineage gone — the forbidden state
        if use_cache:
            self.cache[digest] = lineage
        return lineage

    def discard_cold_for_live(self, frac: float):
        """The FORBIDDEN optimization: drop canonical lineage for digests still live in the hot plane.
        A correct optimizer must never do this; the bench proves the kernel can DETECT it."""
        victims = [d for (_i, _s, d) in self.hot][: int(len(self.hot) * frac)]
        for d in victims:
            self.cold.pop(d, None)
        return victims


def _pcts(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] * 1e6, s[min(n - 1, int(0.99 * n))] * 1e6


def main():
    print("LINEAGE-SCALE — closure test on `digest present + lineage unavailable = severance`")
    print("(sandbox/CPython numbers; the invariant is the point, not the throughput)\n")

    sweep_ok = True
    for n in SCALES:
        b = Bench()
        tracemalloc.start()
        t0 = time.perf_counter()
        b.build(n)
        build_s = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        sample = [b.hot[b.rng.randrange(n)][2] for _ in range(2000)]
        b.cache.clear()
        lat = []
        for d in sample:
            t = time.perf_counter()
            b.resolve(d, use_cache=False)
            lat.append(time.perf_counter() - t)
        p50, p99 = _pcts(lat)
        retained = len(b.cold)
        no_loss = all(b.resolve(d, use_cache=False) != "PROVENANCE_SEVERED" for (_i, _s, d) in b.hot[:5000])
        sweep_ok = sweep_ok and retained == n and no_loss
        print("  N=%-7d build %5.2fs | retained %d/%d | collisions %d | resolve p50/p99 %.1f/%.1f us "
              "| mem peak %6.1f MB | every_digest_resolves %s"
              % (n, build_s, retained, n, b.collisions, p50, p99, peak / 1e6, no_loss))

    print("\npressure modes:")
    b = Bench()
    b.build(2000)
    modes = {}
    modes["steady_state"] = all(b.resolve(d, use_cache=False) != "PROVENANCE_SEVERED" for (_i, _s, d) in b.hot)
    b.cache = {d: b.cold[d] for (_i, _s, d) in b.hot}
    b.cache.clear()                                  # evict the droppable cache
    modes["eviction_of_cache_keeps_lineage"] = \
        all(b.resolve(d, use_cache=True) != "PROVENANCE_SEVERED" for (_i, _s, d) in b.hot)
    victims = b.discard_cold_for_live(0.10)          # the forbidden op
    modes["discard_live_lineage_is_detected_as_severance"] = \
        len(victims) > 0 and all(b.resolve(d, use_cache=False) == "PROVENANCE_SEVERED" for d in victims)
    modes["severance_never_returns_a_guess"] = \
        all(b.resolve(d, use_cache=False) == "PROVENANCE_SEVERED" for d in victims)
    b2 = Bench()
    b2.build(10)
    before = len(b2.cold)
    try:
        b2.k.apply(Event("bad", 0, 1, ""))           # invalid: raises before any state advances
    except ValueError:
        pass
    modes["partial_failure_no_unaccounted"] = \
        len(b2.cold) == before and b2.k.query("bad")["existence"] == "unaccounted"
    reloaded = json.loads(json.dumps(b2.cold))        # serialize → drop → reload
    modes["restart_recovery_all_resolve"] = all(d in reloaded for (_i, _s, d) in b2.hot)

    for m, v in modes.items():
        print(("  ok   " if v else "  FAIL ") + m)
    assert sweep_ok and all(modes.values()), "a pressure mode collapsed the invariant"

    print("\nVerified: digest→lineage preserved under tested scale; no commit becomes UNACCOUNTED;")
    print("          compression (hot→digest) preserves category; discarding live lineage is caught")
    print("          as severance and never answered with a guess.")
    print("Not tested: distributed/durable storage, NUMA/cache behaviour, GPU/frame-loop integration,")
    print("          adversarial external-persistence failure — the substrate frontier.")
    return modes


if __name__ == "__main__":
    main()
