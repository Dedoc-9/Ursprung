# Extracting weaknesses with the workbench tools (and hardening them)

At this stage the project gains more from **stressors** than from new laws — Ursprung's best results came from
failure (PFAL → Causal Continuity → bench failure → Representation Resistance → ranking ≠ allocation). This
doc records *how* the sealed `Reality_Engine` workbench's weakness-extraction tools map onto Ursprung, and the
weaknesses they surfaced.

## The workbench tools, and their Ursprung analogues

| Workbench tool | What it does | Ursprung analogue |
|---|---|---|
| `toolkit/mutate.py` | Goodhart guard: degrade the policy, confirm the suite *notices* (`test_quality ≠ test_count`) | `stress.mutation_guard` — degrade the allocator; the causal-residual metric must worsen |
| `causal_runtime/adversary.py` | find where a field stops being valid: **LATE / WRONG / GAMEABLE**, each with a recorded repair | `stress.adversary_wrong`, `stress.adversary_gameable` |
| `glitch/explorer.py` | bounded fuzz → first invariant violation → **shrink** to minimal counterexample → seal for replay | the divergence classes + render record (counterexamples are replayable by construction) |
| `crucible` | forge deterministic **hard seeds** (a difficulty landscape) | seeded adversarial scenes in `stress` / `policy_arena` |
| `assay` / `monitor` | recomputable quality judgments; runtime drift CERTIFIED→DEGRADED→QUARANTINED | the dual-axis Pareto evaluation (a policy can be DEGRADED on one axis) |

The discipline they share, inherited here: **a benchmark that can no longer fail a policy is decoration**;
every weakness is recorded as a *boundary with its repair*, not hidden.

## The dual-axis arena (the most dangerous missing benchmark)

`policy_arena.py` evaluates every allocation policy on two axes over a drifting frame sequence at equal budget:

```
causal residual        Σ (U·C·P)·aliasing_error(size, samples)          (lower better)
perceptual continuity  Σ sensitivity·|alloc_t − alloc_{t-1}|  (PCL)      (lower better)
```

Measured (constructed world, seed 1, 24 frames):

```
policy                       causal_residual   perceptual_loss
ranked_waterfill                 15.37e9            22,016     ← min causal
damped_waterfill (hardened)      16.83e9             4,228     ← the hardening
proportional_causal              18.65e9            40,411     ← dominated (loses both)
uniform                          19.33e9                 0     ← min perceptual
Pareto front: {damped_waterfill, ranked_waterfill, uniform}
```

**Result: min-causal ≠ min-perceptual.** Minimizing the causal residual (ranked_waterfill) is *not* the same
as maximizing perceptual continuity (uniform). This is the hidden variable the user predicted — the same
shape of mismatch that produced ranking ≠ allocation. `perceptual.py` makes Perceptual Continuity a
first-class **success** axis (liability → priority → difficulty → allocation → **continuity**).

## Hardening the weak result

The churny optimum (`ranked_waterfill`) wins causal residual but reallocates every frame → high perceptual
loss. The hardening, `damped_waterfill`, water-fills a slowly-moving (EMA) weight: it **cuts perceptual loss
~5× (22,016 → 4,228) for ~9% more causal residual** — a Pareto improvement on the perceptual axis. Hardening
here means *adding temporal hysteresis to the allocation*, discovered by the arena rather than assumed.

## Weaknesses extracted (and their repairs, recorded as boundaries)

```
Goodhart mutation guard : 4/4 degraded allocators NOTICED (metric is not decoration; 0 blind)
WRONG (improbable)      : raw-consequence allocator BROKE (5.42e9 vs 2.32e9) → repair: expected value C×probability
GAMEABLE (self-report)  : a self-inflating region captured 68% of budget vs 0% → repair: impact × independent evidence
```

Honest bound: constructed-world results on declared aliasing / PCL proxies; the *shapes* (a two-axis Pareto
trade-off; the named failure boundaries) are the findings, not the exact numbers — they `expire_if` measured
on real silicon with real perceptual error. `integrity ≠ truth`.

## Open (bench-defined)

- A **Resistance Tensor** (geometry / motion / shading / occlusion / reconstruction / perceptual) instead of
  the scalar perimeter proxy — *which resistance dimension dominates error on real hardware?* is measurable.
- **Multi-horizon** allocation (16 ms / 100 ms / 1 s / 5 s votes) and **fidelity derivatives** (`d(FailureCost)/dt`)
  for anticipatory rather than reactive allocation.
- Re-run all of the above on **real silicon**, where every number here expires.
