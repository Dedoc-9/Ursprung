<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SONOLUMINESCENCE — simulation program, ranked by epistemic value / cost (Simulation Lead, Ursprung framework)

> Companion to [`SONOLUMINESCENCE_AUDIT.md`](SONOLUMINESCENCE_AUDIT.md) and
> [`SONOLUMINESCENCE_EXPERIMENT_ROADMAP.md`](SONOLUMINESCENCE_EXPERIMENT_ROADMAP.md); ranking logic =
> [`../experiments/live_world_kernel/discrimination_matrix.py`](../experiments/live_world_kernel/discrimination_matrix.py).
>
> **Rule 5, load-bearing:** a simulation is a *witness*, not evidence. Its output is `pred(H, do(x))`, which stays
> **`DECLARED`** until experimentally observed. **No simulation in this program upgrades any hypothesis to
> `MEASURED`.** What a simulation buys, cheaply, is three things: (1) convert `UNKNOWN`→`DECLARED` (force a
> hypothesis to commit a prediction), (2) reveal where the committed predictions *diverge* vs *overlap*, (3) tell
> the consortium **which experiment is worth the hardware dollars** — including the right to *cancel* an
> experiment a simulation shows would not discriminate. Compute is cheap; the experiment it gates is not — that
> ratio is the entire value proposition.

## Hypotheses (tracked independently; the set is not a clean partition — see audit §0/roadmap §0)

`H1` thermal plasma · `H2` recombination-dominated · `H3` opaque-core/blackbody · `H4` shock-focusing
(*a dynamics axis, compatible with H1–H3*) · `H5` nonthermal/unknown (*under-committed; contributes nothing until
instantiated — here read as the vacuum/dynamical-Casimir instantiation, which commits to "emission at max
|dV/dt|, no atomic-species dependence"*).

## 0. The pre-simulation gate — `UNKNOWN` vs `UNDERCOMMITTED` (the real bottleneck)

The program's sharpest finding is upstream of any simulation: **the bottleneck is prediction scarcity, not data
scarcity.** Several sonoluminescence explanations are vague enough to survive almost any outcome — so before
ranking simulations, separate the two reasons a matrix cell is empty (now encoded in
`discrimination_matrix.py`):

| State | Meaning | Whose problem | Action | Cost |
|---|---|---|---|---|
| `UNKNOWN` | we have not worked out this hypothesis's prediction yet | **ours** | run the cheap simulation to fill it | low |
| `UNDERCOMMITTED` | the hypothesis **refuses/fails** to specify a prediction | **the theory's** | demand a committed forecast — or set the theory aside | ~zero (a workshop) |

The distinction is decisive because **no future observation can discriminate a theory that will not commit.** An
`UNDERCOMMITTED` theory is therefore a *larger* obstacle than an `OCCLUDED` measurement — and the cure is cheap
(force a prediction), not expensive (build a probe). **Honest guard:** `UNDERCOMMITTED` ≠ false. A theory that
makes no falsifiable forecast is *set aside as non-discriminable*, never refuted (`absence of evidence ≠ evidence
of absence`); it can re-enter the moment it commits.

This splits the consortium's work into **two programs with opposite cost profiles**:

```
COMMITMENT PROGRAM (cheap)            MEASUREMENT PROGRAM (expensive)
  force H1–H5 to publish pred(H,do(x))  better temporal resolution
  complete the discrimination matrix    better spectral resolution
  set aside theories that won't commit   better collapse diagnostics
```

The **pre-simulation gate**: every hypothesis must answer, for `do(noble_gas, drive_pressure, frequency,
liquid_T, asymmetry)`, a prediction for `{flash(t,λ), brightness, flash_width, spectral_shape, scaling_law}`
*with a confidence per cell*. No prediction ⇒ `UNDERCOMMITTED` (not `UNKNOWN`). The matrix is not fundable as a
ranking until this gate is run.

## 1. Discrimination matrix — `pred(H, do(x))`, all cells `DECLARED`, `UNKNOWN`, or `UNDERCOMMITTED`

`UNKNOWN` = the hypothesis has not committed (and **never counts as discrimination** — no invented commitments).

| do(x) | H1 thermal | H2 recombination | H3 opaque/blackbody | H4 shock-focusing | H5 nonthermal |
|---|---|---|---|---|---|
| **flash(t, λ)** | continuum shape tracks T(t), peak at compression `[DECL]` | recomb features timed to cooling phase `[DECL]` | graybody; area×T evolves with opacity `[DECL]` | **UNKNOWN** (dynamics, no committed spectral signature) | emission at max \|dV/dt\| ≠ collapse; no T-evolution `[DECL]` |
| **noble-gas sweep** | brighter/hotter toward Xe (↓ ionization pot.) `[DECL]` | same trend `[DECL]` | same trend `[DECL]` | **UNKNOWN** | ~no atomic-species dependence `[DECL]` |
| **pressure / drive sweep** | intensity ∝ bremsstrahlung scaling `[DECL, confounded]` | different scaling exponent `[DECL, confounded]` | ∝ T⁴·area scaling `[DECL, confounded]` | **UNKNOWN** | **UNKNOWN** |
| **collapse-asymmetry sweep** | emission falls with asymmetry only via reduced T `[DECL, weak]` | weak `[DECL]` | weak `[DECL]` | **strong suppression** if asymmetry prevents shock convergence `[DECL]` | **UNKNOWN** |

The visual fact: the `H4` and `H5` columns are empty-dominated. **Reading those cells with the §0 distinction
sharpens the diagnosis** — they are not all the same kind of empty:
- **H5** (`nonthermal/unknown`) is `UNDERCOMMITTED` everywhere by construction — it is a *placeholder* that
  refuses to predict. It is set aside as non-discriminable (not refuted) until instantiated; the table's H5
  entries are courtesy of the vacuum instantiation, which *does* commit and on those commitments loses.
- **H4** (`shock-focusing`) is `UNDERCOMMITTED` on the *emission* rows (flash, gas, pressure) — a **category
  mismatch**, not our gap: it is a dynamics hypothesis and does not specify an emission spectrum — but it is
  `COMMITTED` on the **collapse-asymmetry** row (its own axis), the unique lever on shock-focusing.
- The only genuinely `UNKNOWN` (our-gap) cells are the **emission trio under asymmetry** — we simply have not
  computed them; cheap to fill.

So the empty band is mostly a *theory-commitment* problem (`UNDERCOMMITTED`), not a measurement problem — exactly
the bottleneck §0 names.

## 2. Simulation program (each sim: do(x) · who separates · gain · what it reduces · failure modes · red-team)

### S1 — Time-resolved flash spectrum `flash(t, λ)` (Tier 1)
1. **do(x):** simulate the emitted spectrum *resolved in time* through collapse, for each emission hypothesis.
2. **Separates:** H1≠H2≠H3 (the live dispute, 3 pairs) + H5≠{thermal} on timing. `H4` UNKNOWN (orthogonal axis).
3. **Expected information gain: HIGH.**
4. **Reduces:** emission-mechanism ambiguity ✅ · model under-commitment ✅ (forces H1/H2/H3 to commit t-λ) ·
   OCCLUDED interior ⚠ partial (a less-compressed projection) · shock-focusing uncertainty ❌.
5. **Failure modes:** `NONE` (it is *checkable against existing data* — the simulated integrated spectrum must
   match the measured featureless water continuum and the measured ps flash width; any hypothesis whose sim
   fails that is filtered out before any experiment). Mild `FLOODED` only as a numerical-resolution concern.
6. **Red-team — what would prove this simulation wrong?** Its simulated *integrated* spectrum or flash width
   disagreeing with the already-`MEASURED` continuum/width. ✅ Falsifiable against existing observation →
   recommendation **stands**.

### S4 — Collapse-asymmetry / shock-formation sweep (Tier 4) — *promoted to second because it is the only `H4` lever*
1. **do(x):** impose non-spherical perturbations; simulate whether/where converging shocks form and **what
   observable consequence** follows (emission intensity, flash width).
2. **Separates:** `H4` vs {H1,H2,H3} — *only if it commits to an observable*. It addresses the all-`UNKNOWN`
   shock column.
3. **Expected information gain: MEDIUM-HIGH** (highest marginal `UNKNOWN`→`DECLARED` conversion — an entire
   column) **— conditional on the red-team gate below.**
4. **Reduces:** shock-focusing uncertainty ✅ (the unique one) · model under-commitment ✅ (forces `H4`) ·
   emission ambiguity ❌ · OCCLUDED interior ⚠ only if mapped to an observable.
5. **Failure modes:** **`OCCLUDED`** — the central risk: if the sim predicts only *interior shock structure*
   with no observable consequence, it is unfalsifiable and worthless as a witness. `INTERVENTION_ONLY` if the
   only discriminator is interior geometry.
6. **Red-team — what would prove this simulation wrong?** *Only* if it commits to an observable —
   emission/flash-width **vs imposed asymmetry** — can experiment (deliberate sphericity perturbation) refute
   it. **Gate: if S4 predicts only interior shocks → DOWNGRADE to LOW** (predicts the `OCCLUDED` interior, no
   observable). Funded *only* in the observable-committed form.

### S3 — Pressure / drive-amplitude sweep (Tier 3)
1. **do(x):** vary drive amplitude/frequency/ambient pressure; simulate intensity-vs-drive scaling per emission
   hypothesis.
2. **Separates:** H1/H2/H3 via scaling exponents — *if deconfoundable*.
3. **Expected information gain: MEDIUM, confounded.**
4. **Reduces:** emission ambiguity ⚠ partial · under-commitment ✅ (forces scaling commitment) · OCCLUDED ❌
   (scaling depends on the unmeasured core T).
5. **Failure modes:** `OCCLUDED` — the scaling exponent is confounded by co-varying core T, which is itself
   occluded; you cannot cleanly attribute the exponent without an independent T.
6. **Red-team:** falsifiable against measured intensity-vs-drive curves, but the *mechanism attribution* is not
   (confound). Recommendation **downgraded** from its nominal gain for that reason.

### S2 — Noble-gas fraction sweep (Tier 2)
1. **do(x):** sweep He→Ne→Ar→Kr→Xe; simulate intensity/temperature trend.
2. **Separates:** only H5 vs {thermal}; H1/H2/H3 predict the *same* trend (0 within-family).
3. **Expected information gain: LOW (marginal).** The strong *measured* gas dependence already argues against
   H5 — this mostly re-derives known evidence.
4. **Reduces:** under-commitment ✅ (commits the gas trend) · emission ambiguity ❌ · OCCLUDED ❌ · shock ❌.
5. **Failure modes:** `NONE` (checkable against the measured ~1% Ar optimum).
6. **Red-team:** falsifiable (must reproduce the measured dependence), but low *marginal* value. **Stands as
   cheap validation, not as discrimination.**

## 3. Ranking — epistemic value / cost (consortium with finite funding)

Simulation cost is compute (low, ≈ uniform). The real economy is *experimental dollars de-risked per compute
dollar*. Value = (`UNKNOWN`→`DECLARED` conversion) × (divergence revealed) × (expensive experiment gated),
**capped at `DECLARED`** (Rule 5).

| Rank | Simulation | Info gain | Falsifiable (red-team)? | What it gates / de-risks | Value / cost |
|---|---|---|---|---|---|
| **1** | **S1 flash(t, λ) suite** | HIGH | ✅ vs measured continuum + ps width | the #1 (most expensive) experiment — could *justify or cancel* it | **HIGHEST** |
| **2** | **S4 asymmetry (observable-committed only)** | MED-HIGH | ✅ *iff* it predicts emission-vs-asymmetry | the only `H4` lever; converts an entire `UNKNOWN` column | **HIGH (gated)** |
| 3 | S3 pressure/drive scaling | MEDIUM | partial (confound) | a confounded discriminator | MEDIUM |
| 4 | S2 noble-gas sweep | LOW | ✅ but marginal | re-derives known dependence | LOW |

## 4. Master funding order (commitment before measurement) and the single highest-value next step

With the §0 gate in front, the cheapest steps move ahead of the expensive ones, and two of the top three are
near-zero cost:

```
1. Prediction-commitment workshop        cheap     force H1–H5 to publish pred(H, do(x)) + confidence;
                                                    UNDERCOMMITTED ⇒ set aside (not refuted)
2. Discrimination-matrix completion       cheap     fill the UNKNOWN (our-gap) cells; finalize divergence map
3. S1 flash(t, λ) simulation suite        cheap     validate vs measured continuum/width; reveal divergence;
                                                    JUSTIFY or CANCEL step 4
4. Time-resolved spectroscopy experiment  expensive run only if step 3 shows the survivors diverge
5. Collapse-asymmetry campaign            v. expensive only if H4 commits (step 1) AND survives
```

**The single highest-value next step is step 1 — the prediction-commitment workshop.** It is the cheapest action
on the board and it unblocks the largest block of empty cells (the `UNDERCOMMITTED` H4/H5 columns); no
measurement can substitute for it, because *no observation discriminates a theory that will not commit.* The S1
`flash(t, λ)` simulation runs **in parallel** for the already-committed emission trio (H1/H2/H3): simulate each
time-resolved spectrum, **discard any whose *integrated* prediction already fails the measured featureless
continuum / ps width**, and report whether the survivors *diverge* — which **justifies** the expensive
time-resolved experiment (with a known target signature) or **cancels** it before a hardware dollar is spent.
Both outcomes are high value; neither upgrades past `DECLARED` (Rule 5).

## 5. Red-team summary (where recommendations were downgraded)

- **S4 downgraded unless observable-committed** — a shock-focusing simulation that predicts only the `OCCLUDED`
  interior is unfalsifiable and contributes nothing as a witness. Funded only in the emission-vs-asymmetry form.
- **S3 downgraded** — its mechanism attribution is confounded by the occluded core temperature; the scaling
  curve is checkable, the *cause* of the exponent is not.
- **S2 reclassified** from discrimination to *cheap validation* — it re-derives the already-measured gas
  dependence and separates only an already-losing H5.
- **Whole-program ceiling:** every output is `DECLARED`. No simulation here moves any hypothesis toward
  `MEASURED`; the program's deliverable is a committed, divergence-mapped matrix and a funding decision, **not a
  cause.** `simulation ≠ evidence`; `pred(H, do(x))` stays `DECLARED`; `observation ≠ intervention`;
  `UNKNOWN ≠ discrimination`; `absence of evidence ≠ evidence of absence`; **strength is never upgraded.**

## Honest scope

I am the simulation lead, not the physics oracle: every prediction cell is *my* `DECLARED` guess of what each
hypothesis would commit to, and the program's realized value depends on the hypotheses publishing their own
`pred(H, do(x))`. The discipline — simulations are witnesses capped at `DECLARED`, `UNKNOWN` is a result,
disagreement is preserved not averaged, and a recommendation with no falsifier is downgraded — is the
deliverable. **Maximum epistemic gain per dollar = simulate `flash(t, λ)` first; let it justify or kill the
expensive experiment before the hardware budget is touched.**
