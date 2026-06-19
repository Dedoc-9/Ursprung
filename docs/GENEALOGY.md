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

- [x] **Milestone 3 — VIEW vertical slice + Causal Continuity Hypothesis (provisional).**
  - [x] Causal Continuity *Hypothesis* (NOT a law): allocate ∝ expected future causal loss `U×C×P`; encodes
    the PFAL⇄Reality-Debt duality; promotion gate — `causal_continuity.py`
  - [x] Deterministic reference rasterizer: projection → coverage → sampling → rasterization, each a declared
    convention with a named ghost; content-hashable framebuffer — `raster.py`
  - [x] Cardinal invariant holds under rendering: CORE byte-identical with the rasterizer running every tick.
  - [x] Equal-budget bench + promotion gate (uniform / distance / visibility / PFAL / causal + control) — `raster_bench.py`
  - [x] **Result (recorded, not rigged): the hypothesis is NOT promoted.** Proportional causal loses even to
    uniform — the failure, and its diagnosis, are the deliverable.

- [x] **Milestone 3.1 — the failure becomes a refinement (ranking ≠ allocation).**
  - [x] `representation.py` — RepresentationResistance (the hidden variable: how hard a region is to represent;
    perimeter proxy) and `DebtPressure = RealityDebt × RepresentationResistance`.
  - [x] `allocation.py` — the ranking/allocation split: `rank(priority)` then `waterfill(priority, resistance)`.
    **PFAL ranks · water-filling allocates · Reality Debt constrains.**
  - [x] Re-specified bench: on the future-causal residual metric, two-stage `ranked_waterfill` (756,247,772)
    **strictly beats** uniform (1,063,453,324), distance, visibility, proportional-causal (844,974,909), and the
    drifted control — a **supported** hypothesis on the constructed bench (pending real silicon).
  - Result statement: *importance metrics and allocation functions cannot be conflated; causal importance ranks,
    constrained optimization distributes.*

- [x] **Milestone 4 — stressors + the perceptual axis (extract weaknesses; harden).**
  - [x] `perceptual.py` — Perceptual Continuity Loss (reallocation churn × sensitivity): the measurable
    *success* axis (liability → priority → difficulty → allocation → **continuity**).
  - [x] `policy_arena.py` — dual-axis (causal residual × perceptual continuity) over drifting frames; Pareto
    front. **Mismatch confirmed:** min-causal (ranked_waterfill) ≠ min-perceptual (uniform). Hardening:
    `damped_waterfill` cuts perceptual loss ~5× (22,016→4,228) for ~9% more causal residual.
  - [x] `stress.py` — workbench-style weakness extraction: Goodhart mutation guard (4/4 noticed), WRONG
    adversary (raw consequence broke → expected value), GAMEABLE adversary (self-report captured 68% → repair:
    independent evidence). See [`STRESSORS.md`](STRESSORS.md).

### Milestone-3 finding (the failure is the result)

The Causal Continuity Hypothesis as *stated* (allocate ∝ U·C·P) **failed** the equal-budget bench. Diagnosis
(itself falsifiable, and verified by the diagnostic allocators in `raster_bench.py`):

1. The consequential edge-error metric (`Σ C·perimeter/samples`) is **convex** in samples, so *proportional*
   allocation over-concentrates and loses to uniform.
2. The optimal weight must include the **error's own structural term** (size/perimeter), which `U·C·P` (and
   PFAL's `U·C·P·S`) omit.

Measured (seed=1, budget=400): proportional causal **2,147,735** > uniform **1,684,339**; water-filling causal
`√(U·C·P)` **1,641,016** (marginal win); size-aware optimum `√(C·perimeter)` **1,427,556** (clear win). The
re-specification — *water-filling form + include the error's structural term* — is the next hypothesis to test
before any promotion. Failure kept as architectural information.

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

- [ ] **Re-specified Causal Continuity** — water-filling form (∝ √weight) + a weight that includes the error's
  structural term (size/perimeter); re-run the gate. Only then is promotion on the table.
- [ ] Real-silicon benchmark: PFAL/TCFF at equal GPU time, measuring temporal artifacts, input-to-photon
  latency, reconstruction error, and motion stability (the numbers above expire here).
- [ ] Native (C++/Rust) port validated against the Python reference via conformance vectors.
- [ ] Multi-lens presentations (cinematic / competitive / VR / handheld / debug) over one committed world.

## Verify locally

```bash
PYTHONHASHSEED=0 python3 tests/test_ursprung.py     # unit suite
PYTHONHASHSEED=0 python3 loop.py                    # live loop + milestone + benches
```
