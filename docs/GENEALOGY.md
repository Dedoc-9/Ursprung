# Ursprung — genealogy & checklist (thus far)

The engineering lineage of Ursprung: what was built, in what order, which law it established, how it was
verified, and its honest bound. Modeled on the workbench's `GENEALOGY.md`. `integrity ≠ truth` throughout.

## The five laws (the philosophy layer)

```
Reality Debt Law          (underneath)  every approximation incurs debt = approx × persistence × consequence
   └─ Arbitrary-Boundary Law            representation choices are deterministic conventions, not truth
   └─ Predictive Fidelity Law (PFAL/TCFF) spend where future failure cost is highest (U·C·P·S·τ)
   └─ Polygon Reconciliation Law        keep polygons iff abandonment cost ≥ approximation error
   └─ Temporal Fidelity Conservation    fidelity is transferred, not created; minimize consequential discontinuity
```

One line: **arbitrary boundaries require deterministic handling, and finite fidelity should be allocated by
expected future failure cost, not present visual complexity.**

The hierarchy these produce:

```
WORLD → SNAPSHOT → PREDICTION → FIDELITY ALLOCATION → DEBT MANAGEMENT → RASTERIZATION → IMAGE
```

## Layer map (the cardinal rule: only CORE may move committed state)

- **CORE** — `world_core` (authoritative trajectory, wraps the sealed AetherPulse kernel).
- **VIEW** — `view_layer` (read-only snapshot → VisualFrame; no write-back).
- **ALLOCATOR** — `temporal_membrane`, `tcff` (decide where/when effort goes; never truth).
- **OBSERVER** — `ghost_report`, `verify`, `render_record`, `conventions`, `divergence`, `prediction`,
  `pfal_bench`, `polygon_reconciliation`, `fidelity_conservation`, `reality_debt`.

## Checklist — built & verified

- [x] **Milestone 1 — foundation + invariant harness.** Renderer proven observer-only.
  - [x] CORE world loop (tick · hash · replay · divergence locator) — `world_core.py`
  - [x] VIEW boundary (read-only snapshot → frame, no write-back) — `view_layer.py`
  - [x] System-classification register; only CORE may mutate — `registry.py`
  - [x] Ghost reporter (6 categories × origins) — `ghost_report.py`
  - [x] Verification harness: replay identity · view-perturbation invariance · ordering invariance — `verify.py`
  - [x] Cardinal invariant holds: committed trajectory byte-identical with VIEW active + corrupted.
- [x] **Milestone 2 — predictive-fidelity architecture + the five laws.**
  - [x] Render Verification Record — features are experiments (TYPE/EFFECT/NON-EFFECT/EVIDENCE) — `render_record.py`
  - [x] Arbitrary-Boundary Law / Boundary Ledger (declared, hashed, `truth_claim=false`) — `conventions.py`
  - [x] Three divergence classes (world / representation / observation) — `divergence.py`
  - [x] Dini-style prediction observer; ghost = max(0, observed − predicted) — `prediction.py`
  - [x] Temporal Prediction Membrane + Temporal Reality Budget (U × C) — `temporal_membrane.py`
  - [x] PFAL R = U×C×P×S + falsification bench w/ negative control — `pfal_bench.py`
  - [x] TCFF F = U×C×P×S×τ proactive + Perceptual Continuity per Joule — `tcff.py`
  - [x] Polygon Reconciliation Law; `reconcile()` not replace — `polygon_reconciliation.py`
  - [x] Temporal Fidelity Conservation Law; transfer is zero-sum — `fidelity_conservation.py`
  - [x] Reality Debt Law; Debt = approx × persistence × consequence — `reality_debt.py`
  - [x] Live loop wiring (prediction → membrane budget → PFAL → TCFF/PCJ → render record) — `loop.py`
  - [x] Docs: `LLM_ON_TRACK.md`, `PREDICTIVE_FIDELITY.md`, `RENDER_VERIFICATION_RECORD.md`, this file.

## Measured (constructed-world; honest bounds)

| Result | Number | Status |
|---|---|---|
| Milestone-1 invariants (replay / view-perturbation / ordering) | all pass | proven on the AetherPulse kernel |
| PFAL vs distance/visibility (failure-cost covered, equal budget) | 0.897 vs 0.046 | constructed-world hypothesis |
| PFAL negative control vs uniform floor | 0.501 < 0.587 | bench can falsify (Goodhart guard) |
| TCFF vs PFAL vs reactive (Perceptual Continuity per Joule) | 0.287 / 0.245 / 0.105 | constructed-world hypothesis |
| Conservation objective swap (consequential discontinuity, equal budget) | 7 vs 30 | declared-budget accounting |
| Reality-debt placement (consequential debt, same approximation) | 72 vs 456 | declared accounting |

**Every bench number above is a constructed-world result and `expires_if` measured on real GPU silicon.** A
benchmark measures the benchmark's world; it does not prove universal superiority.

## Not yet built (honest)

- [ ] **VIEW vertical slice** — projection → coverage → sampling → rasterization, each step a declared
  convention (hash + rejected alternatives + known ghosts). The first test of whether the five laws survive
  contact with an actual rasterizer.
- [ ] Real-silicon benchmark: PFAL/TCFF at equal GPU time, measuring temporal artifacts, input-to-photon
  latency, reconstruction error, and motion stability (the numbers above expire here).
- [ ] Native (C++/Rust) port validated against the Python reference via conformance vectors.
- [ ] Multi-lens presentations (cinematic / competitive / VR / handheld / debug) over one committed world.

## Verify locally

```bash
PYTHONHASHSEED=0 python3 tests/test_ursprung.py     # unit suite
PYTHONHASHSEED=0 python3 loop.py                    # live loop + milestone + benches
```
