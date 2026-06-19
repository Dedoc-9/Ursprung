# Ursprung

A deterministic high-fidelity renderer that treats rendering as a **perception layer over an authoritative
world model**. Ursprung consumes the sealed `Reality_Engine` (Chronicle/Dentatus) workbench read-only as its
verification substrate; the workbench supplies the deterministic kernel and the integrity discipline, and
Ursprung is the renderer projected off the committed trajectory.

```
authoritative world state → deterministic snapshot → visual interpretation → GPU execution → presented frame
```

**Author:** Daniel J. Dillberg · **Contact:** [bigdilly95@gmail.com](mailto:bigdilly95@gmail.com)
**License:** [AGPL-3.0-only](LICENSE)

The renderer never discovers truth; it manages where its approximations fail. Its one-line philosophy:
**arbitrary boundaries require deterministic handling, and finite fidelity should be allocated by expected
future failure cost, not present visual complexity.**

## The five laws (the philosophy layer)

1. **Reality Debt Law** *(underneath)* — every approximation incurs debt: `Debt = Approximation ×
   Persistence × Consequence`. Fidelity is conserved, but debt is accumulated; allocation places debt where
   future consequence is lowest. (`reality_debt.py`)
2. **Arbitrary-Boundary Law** — representation choices (pixel coverage, float format, LOD threshold, tick
   rate, polygons) are deterministic *conventions*, never truth claims. (`conventions.py`)
3. **Predictive Fidelity Law (PFAL / TCFF)** — spend computation where future failure cost is highest:
   `R = U × C × P × S × τ`. (`prediction.py`, `temporal_membrane.py`, `pfal_bench.py`, `tcff.py`)
4. **Polygon Reconciliation Law** — keep polygons iff abandoning them costs more than their approximation
   error; rasterization is transport, allocation is strategy. (`polygon_reconciliation.py`)
5. **Temporal Fidelity Conservation Law** — fidelity is transferred, not created; the objective is *minimum
   consequential discontinuity under a fixed budget*, not maximum detail. (`fidelity_conservation.py`)

```
WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → DEBT MANAGEMENT → RASTERIZATION → IMAGE
```

A sixth idea — the **Causal Continuity Hypothesis** (allocate fidelity ∝ expected future causal loss) — is
deliberately held as a *provisional hypothesis*, not a law: it must survive implementation, replay, a negative
control, and equal-budget benchmarking before promotion. As stated, it *failed* the first test (the failure
and its diagnosis are recorded — see [`docs/GENEALOGY.md`](docs/GENEALOGY.md)).

See [`docs/GENEALOGY.md`](docs/GENEALOGY.md) for the full genealogy & checklist of what is built, verified,
and not yet built.

## Run it

```bash
PYTHONHASHSEED=0 python3 loop.py                  # live loop: milestone + prediction/membrane/PFAL/TCFF/PCJ
PYTHONHASHSEED=0 python3 tests/test_ursprung.py   # unit suite (stdlib asserts)
```

If the engine is not at `~/Desktop/Reality_Engine`, set `URSPRUNG_WORKBENCH=/path/to/Reality_Engine`.

## What Milestone 1 proves (and only this)

> *I can replay the same world and prove the renderer is only an observer.*

- **replay identity** — the same world run N times yields byte-identical committed trajectories.
- **view-perturbation invariance** — the CORE trajectory is byte-identical even with the VIEW layer active
  and *deliberately corrupted* every tick (the renderer cannot move the Weltlinie — no write-back).
- **ordering invariance** — permuting input body order does not change the trajectory (id-sorted evolution).

It does **not** prove the renderer is correct, fast, or pretty. `integrity ≠ truth`.

## Layout

| Path | Layer | Role |
|---|---|---|
| `ursprung/_workbench.py` | bridge | Sibling-Law read-only access to `Reality_Engine` |
| `ursprung/world_core.py` | **CORE** | authoritative trajectory (wraps the AetherPulse kernel): tick · hash · replay · compare |
| `ursprung/view_layer.py` | **VIEW** | read-only snapshot → camera → VisualFrame; no write-back |
| `ursprung/registry.py` | — | system-classification register; enforces "only CORE may mutate the trajectory" |
| `ursprung/ghost_report.py` | **OBSERVER** | ghost capture & classification (6 categories × origins) |
| `ursprung/verify.py` | **OBSERVER** | the milestone verification harness |
| `ursprung/render_record.py` | **OBSERVER** | emits a render Verification Record (features as experiments) |
| `ursprung/conventions.py` | **OBSERVER** | the Arbitrary-Boundary Law / Boundary Ledger (declared, hashed, never truth) |
| `ursprung/divergence.py` | **OBSERVER** | the 3 divergence classes (world / representation / observation) |
| `ursprung/prediction.py` | **OBSERVER** | Dini-style predict→observe→ghost (surprise → attention, never authority) |
| `ursprung/temporal_membrane.py` | **ALLOCATOR** | Temporal Prediction Membrane + Temporal Reality Budget (uncertainty × consequence) |
| `ursprung/pfal_bench.py` | **OBSERVER** | PFAL `R=U×C×P×S` + falsification bench (uniform / distance-vis / PFAL, negative control) |
| `ursprung/tcff.py` | **ALLOCATOR** | TCFF `F=U×C×P×S×τ` proactive pre-warming + Perceptual Continuity per Joule bench |
| `ursprung/polygon_reconciliation.py` | **OBSERVER** | Polygon Reconciliation Law: polygons as deterministic convention; `reconcile()` not replace |
| `ursprung/fidelity_conservation.py` | **OBSERVER** | Temporal Fidelity Conservation Law: fidelity is transferred, not created; minimize consequential discontinuity |
| `ursprung/reality_debt.py` | **OBSERVER** | Reality Debt Law: `Debt = Approximation × Persistence × Consequence`; place debt where consequence is lowest |
| `ursprung/causal_continuity.py` | **OBSERVER** | Causal Continuity *Hypothesis* (provisional): allocate ∝ expected future causal loss `U×C×P`; PFAL⇄Debt duality |
| `ursprung/raster.py` | **VIEW** | deterministic reference rasterizer: projection→coverage→sampling→raster, each a declared convention; hashable framebuffer |
| `ursprung/raster_bench.py` | **OBSERVER** | equal-budget allocation bench + promotion gate (the hypothesis *failed* as stated — recorded with diagnosis) |
| `loop.py` | — | smallest executable world loop, end to end |
| `AGENTS.md` | — | the renderer contract (the rules every change obeys) |

## Roadmap

1. **Milestone 1 — done.** Foundation + invariant harness (this).
2. VIEW vertical slice: camera · geometry · basic raster path · lighting · frame presentation.
3. ALLOCATOR experiments: LOD · visibility · adaptive quality · salience · compute budgets — each proven by
   *same trajectory, different allocation* under a baseline→benchmark→compare experiment.

See [`docs/LLM_ON_TRACK.md`](docs/LLM_ON_TRACK.md) for how the workbench mechanisms keep an LLM coding partner
on the renderer track (incl. the renderer application rules and the **Arbitrary-Boundary Law** —
*arbitrary boundaries require deterministic handling, not claims of truth*),
[`docs/RENDER_VERIFICATION_RECORD.md`](docs/RENDER_VERIFICATION_RECORD.md) for the per-feature record that
turns new capabilities into experiments, [`docs/PREDICTIVE_FIDELITY.md`](docs/PREDICTIVE_FIDELITY.md) for the
prediction → membrane → PFAL chain (spend compute where the approximation is weakest under the cost of being
wrong), and [`AGENTS.md`](AGENTS.md) for the contract every change obeys.

## License

Ursprung is licensed under the [GNU Affero General Public License v3.0 only](LICENSE) (AGPL-3.0-only).
Copyright (C) 2026 Daniel J. Dillberg. It consumes the sealed `Reality_Engine` workbench read-only (the
Sibling Law) and does not vendor or relicense any of it.
