<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Weltwerk — Phase 10: the operating envelope

Phase 9 answered *can a causal world host gameplay?* (yes). Phase 10 attacks the question most likely to
change the roadmap:

> **How large can a causal world become before Actual approaches Potential and the economics collapse?**

`sim/causal_scale_bench.py` measures it from the **real authority** (`world_format` reach + `world_ai`
pathing). It is a **deterministic op-count** bench — it counts structural work (entities reached, graph
edges, LOS cells, A* path nodes). It reports **no** wall-clock, bandwidth, latency, or networking.
`op-count ≠ latency`.

## The law under test

```
cheap iff Actual ≪ Potential

per event:  footprint = |{target} ∪ reach(target)|
            naive_ops = N            (broadcast: touch everything)
            causal_ops = footprint   (re-derive only the reachable set)
            headroom  = 1 − avg_footprint / N
```

Worlds are generated as dependency **chains** whose length scales with a `coupling` knob (0 → isolated
entities; 1 → one chain of length N). This is a *model* of coupling, stated, not a claim about real game
topologies.

## Run

```powershell
cd "C:\Users\dillb_lzxy763\Claude\Projects\Ursprung\weltwerk\sim"; $env:PYTHONHASHSEED="0"; python test_causal_scale_bench.py; python causal_scale_bench.py
```

## MEASURED

- **The envelope exists and points the predicted way.** As coupling rises, average footprint rises and
  compression headroom falls **monotonically** — causal replication is cheap when the world is sparse and
  degrades toward broadcast as it densifies. (`test_causal_scale_bench`: `headroom_monotonic`,
  `envelope_direction`, `causal_le_naive`.)
- **The bench measures the real authority.** Reach is `world_format`'s reach, not a re-implementation.
  (`anchor_reach_authority`.)
- **AI work is ~linear in bot count.** Bots are independent; per-bot work (LOS cells + A* path nodes) is
  bounded by **grid geometry, not by world entity count**. (`ai_work_linear`.)
- **Deterministic.** Same seed ⇒ identical envelope and identical AI scaling. (`determinism`.)

## The honest finding (a stated boundary, not a hidden one)

A **linear** dependency chain bottoms out at ~**50% headroom** — on average half the chain is downstream of
any node, so even maximal chain coupling leaves ~half the world untouched. Driving headroom toward 0 (true
collapse, where causal ≈ naive for most events) requires **shared / hub coupling** (one node reaching most
of the world), which this chain model does not include. So this phase establishes the *direction and shape*
of the envelope and the sparse-world win; it does **not** yet exhibit the dense-collapse regime. That regime
— hub/feedback-dense topologies, and the real-game topologies in between — is the next measurement.

## Topology sweep — where headroom actually collapses (and under which metric)

The chain model can't reach the dense regime, so the bench also sweeps fixed topologies (N=400) and reports
**both** average headroom (cost of a *typical* event) and worst-case headroom (cost of the single
most-coupled event). The result refines the naive expectation:

| Topology | avg headroom | worst headroom | reading |
|---|---|---|---|
| chain | ~0.50 | ~0.00 | half downstream on average; the head reaches all |
| tree (binary) | ~0.97 | ~0.00 | most nodes shallow; the root reaches all |
| modular clusters | ~0.99 | ~0.98 | bounded by cluster size — **both** stay high |
| **hub-and-spoke** | **~0.99** | **~0.00** | only the hub event is costly |
| scc (one cycle) | ~0.00 | ~0.00 | mutual reachability ⇒ **collapse** |
| clique (complete) | ~0.00 | ~0.00 | everyone reaches everyone ⇒ **collapse** |

The sharp finding: **hub-and-spoke does NOT collapse *average* headroom.** A hub has one expensive event
(destroy the hub) among N−1 cheap ones, so the *typical* event stays cheap while the *worst* event costs the
world. This is the "metric is missing something" outcome made concrete — average headroom is blind to a
single high-reach node. The **average** event collapses only under **mutual reachability** (SCC / clique),
where most nodes reach most of the world. So the operating envelope has two axes, not one:

```
worst-case headroom collapses when ANY node reaches the world  (chain head, tree root, hub, scc, clique)
average    headroom collapses only when MOST nodes reach the world  (scc, clique)
```

A causal runtime that replicates *per event* lives or dies on the **average** (and tail) of this
distribution, not on the worst case alone — which is why "one node reaches everything" is not by itself a
collapse. (`test_causal_scale_bench`: `topo_hub_distinction`, `topo_scc_collapses`, `topo_worst_le_avg`.)

## NOT CLAIMED

- No latency, bandwidth, throughput, networking, MMO, or player-count claims. Structural op-counts only.
- The coupling model is chains, not measured game topologies; the numbers describe the *model's* envelope.
- This does not prove worlds stay sparse in practice — it provides the **ruler** for deciding, per world,
  whether `Actual ≪ Potential` holds. `has-a-ruler ≠ world-is-sparse`.

## Where this leaves the roadmap

The thesis is now an **engineering operating envelope**, not just an architecture: causal replication wins
in the sparse regime, degrades with coupling (not size), and collapses on the *average* event only under
mutual reachability (SCC / clique) — a hub collapses only the worst case. The bench tells you which regime a
given world is in. Next measurements, in order: (1) ~~dense-topology collapse point~~ **done (topology
sweep above)**; (2) live-edit (continuous `world_diff` + re-derive); (3) the runtime "why" layer, which
becomes valuable once worlds are too large to inspect by eye.

**The distinctions this phase pins down (easy to collapse together later):**
`world size ≠ coupling` · `entity count ≠ reachability` · `scale ≠ density` · and
`one node reaches everything ≠ the average event is expensive`.
