<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SONOLUMINESCENCE — ranked experimental roadmap (Simulation Test Lead, Ursprung framework)

> **Mission:** not "what causes sonoluminescence?" but *"what experiment forces the surviving explanations to
> make incompatible predictions?"* and *"which intervention converts the most `DECLARED` claims to
> `MEASURED_BY_INTERVENTION`?"* Companion to [`SONOLUMINESCENCE_AUDIT.md`](SONOLUMINESCENCE_AUDIT.md); ranking
> logic = [`../experiments/live_world_kernel/discrimination_matrix.py`](../experiments/live_world_kernel/discrimination_matrix.py).
>
> **Provenance of this document:** every prediction cell below is `DECLARED` — *my* model-output guess of what
> each hypothesis would predict. They are not the field's committed predictions, and the realized epistemic
> value of any experiment depends on the hypotheses publishing their own `pred(H, do(x))`. Where I cannot
> responsibly assign a *divergent* prediction, the cell is `UNKNOWN`, and **`UNKNOWN` never counts as
> discrimination** (no fabricated divergence to inflate a score). Sandbox down → the matrix logic was applied by
> hand, not re-run.

## 0. Red-team finding that reframes everything: the hypothesis set is not a clean partition

Before ranking, the sharpest epistemic bottleneck is in the *question*, not the experiments. The five hypotheses
do not all answer the same question:

```
EMISSION MICRO-MECHANISM (mutually exclusive on one axis):  H1 bremsstrahlung · H2 recombination · H3 opacity/blackbody
ENERGY-CONCENTRATION DYNAMICS (a different axis):           H4 shock-wave focusing  — COMPATIBLE with any of H1–H3
NON-THERMAL OUTLIER (under-committed placeholder):          H5 "residual non-thermal" — predicts almost nothing specific
```

Consequences, recorded honestly:
- **H4 is not a peer of H1/H2/H3.** Shock focusing is a claim about *how the energy gets concentrated*, and is
  compatible with thermal bremsstrahlung/recombination/blackbody *emission*. So most "H4 vs H1/H2/H3" cells are
  `UNKNOWN` by **category mismatch**, not by measurement difficulty. An experiment that "fails to separate H4
  from H1" may be asking an ill-posed question.
- **H5 is under-committed to the point of near-unfalsifiability as stated.** "Residual non-thermal" predicts
  little; I treat it as `UNKNOWN` everywhere *unless* instantiated (e.g., as the vacuum/dynamical-Casimir model,
  which *does* commit: emission at max |dV/dt| / no atomic-species dependence — and on those commitments it has
  already largely lost, §audit 2.5). **Force H5 to instantiate or it contributes zero discrimination.**

**Recommendation #0 (free, must precede ranking realization):** split the program into two orthogonal
discrimination problems — (i) emission micro-mechanism {H1,H2,H3}, (ii) energy-concentration dynamics
{smooth-adiabatic vs H4 shock} — and require H5 to instantiate a committed model. Most `UNKNOWN` cells below are
this category/commitment gap, not the experiments' fault.

## 1. Per-experiment evaluation

Pairs are counted out of C(5,2)=10. `sep` = predicted-divergent (`DECLARED`); `UNK` = under-committed;
`same` = predicted identical (no discrimination).

### A. Time-resolved spectroscopy — `flash(t, λ)` (sub-ps, spectrally resolved)
- **do(x):** resolve the emission across time *and* wavelength through the collapse, instead of the
  time-integrated spectrum.
- **Predictions (DECLARED):** H1 continuum whose shape tracks T(t), peaking at compression; H2 recombination
  features timed to the cooling phase (lagging peak); H3 graybody whose effective-area×temperature evolves with
  optical depth; H4 `UNKNOWN` distinct *spectral* signature (dynamics, not emission) — at most predicts a
  shorter/more-centralized pulse; H5(vacuum) emission at max |dV/dt| (≠ collapse), no T-evolution.
- **Separates:** H1–H2, H1–H3, H2–H3 (3, the live dispute) + H5 vs H1/H2/H3/H4 (4) = **7 sep**, 3 UNK (H4 vs
  H1/H2/H3).
- **Epistemic value: HIGH (~7/10).** Also **reduces occlusion** — a less-compressed projection of the core.
- **Major uncertainties:** the H1/H2/H3 spectra may diverge only *subtly*; needs the three to commit to
  distinct t-λ curves first; sub-ps + spectral resolution at ~10⁴–10⁵ photons/flash is hard.
- **Failure modes:** too few photons per time-λ bin; instrument response convolving the ps structure (a mild
  `FLOODED` — detector bandwidth vs event clock).
- **Falsifies:** H1 if no continuum tracks T(t); H2 if no cooling-phase features; H3 if area-temperature
  relation is absent; the **dominant thermal model entirely** if the t-λ evolution matches no ~10⁴ K thermal
  source; H5 confirmed-lost if emission is at collapse (already strongly indicated).

### B. Noble-gas sweep He → Ne → Ar → Kr → Xe
- **do(x):** vary trapped-gas species (ionization potential ↓, thermal conductivity varies across the series).
- **Predictions (DECLARED):** H1/H2/H3 all predict the *same* qualitative trend (brighter/hotter toward Xe:
  lower ionization potential, lower conductivity → hotter core) → `same` among the thermal family; H4 `UNKNOWN`;
  H5(vacuum) ~no dependence on atomic species → `sep` from all thermal.
- **Separates:** H5 vs H1/H2/H3/H4 (4) = **4 sep**; 0 within thermal family.
- **Epistemic value: nominal 4, MARGINAL LOW.** The strong *observed* gas dependence already argues against
  H5; this mostly re-spends evidence. Cheap, though.
- **Uncertainties:** confounds (gas solubility, diffusion, chemistry differ across the series).
- **Failure modes:** changing gas also changes bubble stability/size — not a clean single-variable do(x).
- **Falsifies:** an instantiated H5 if brightness depends sharply on atomic species (it does → H5-vacuum already
  on the ropes); thermal family barely touched.

### C. Isotope substitution H₂O vs D₂O
- **do(x):** change the liquid's density, sound speed, viscosity, vapor pressure, and (slightly) dielectric.
- **Predictions:** H1/H2/H3 `UNKNOWN` divergence — they emit from whatever collapse the liquid produces, with no
  *published* per-mechanism divergent prediction; H4 *might* predict sound-speed sensitivity of shock formation
  (`UNKNOWN`-leaning); H5(vacuum) *might* predict a dielectric-constant dependence (`DECLARED`, weak).
- **Separates:** ~**0–1**, almost all `UNKNOWN`.
- **Epistemic value: LOW / CONDITIONAL.** This is a pure **theory-under-commitment bottleneck**: the experiment
  is cheap and clean, but no hypothesis has committed to a divergent D₂O prediction. Value is unlocked *only if*
  Recommendation #0 is done first.
- **Falsifies:** little, as currently specified — its worth is contingent on prior commitment.

### D. Drive-frequency sweep
- **do(x):** vary acoustic frequency (~20–40 kHz and beyond).
- **Predictions:** all hypotheses' emission follows the collapse; frequency mainly reshapes drive/stability →
  `same`/`UNKNOWN` on mechanism.
- **Separates:** ~**0**. Maps the operating envelope; does not discriminate emission mechanism.
- **Epistemic value: LOW.** Useful for stability/parameter mapping, not for collapsing mechanism uncertainty.

### E. Pressure / drive-amplitude sweep
- **do(x):** vary acoustic drive amplitude / static ambient pressure → vary collapse intensity, T, P.
- **Predictions (DECLARED, confounded):** the *intensity-vs-drive scaling law* may diverge —
  H1 bremsstrahlung ∝ (specific T-power × ionization), H3 blackbody ∝ T⁴·area, H2 recombination a different
  scaling. So H1/H2/H3 *might* separate via scaling exponents.
- **Separates:** up to **3** (H1/H2/H3 via scaling) — but **heavily confounded** (T, P, ionization, size all
  move together), so realistically `UNKNOWN`-degraded to ~1–2.
- **Epistemic value: MODERATE-CONDITIONAL.** A real but confounded discriminator; weaker and messier than A.
- **Failure modes:** the scaling confound is severe; without an independent T measurement (occluded), the
  exponent is not cleanly attributable.

### F. Liquid substitution — water vs concentrated H₂SO₄ vs other media
- **do(x):** change the medium; conc. H₂SO₄ yields far brighter SBSL **with resolvable emission lines**
  (Ar/SO/O₂⁺; Flannigan–Suslick) and inferred core opacity.
- **Predictions:** lines present ⇒ a real partially-ionized plasma ⇒ strongly `sep` H5 from H1/H2/H3/H4; line
  self-absorption + temperature bear on **H3 (opacity)** vs H1/H2 (`sep`, partial).
- **Separates:** ~**4–5** (H5 vs thermal strongly; H3-relevant evidence).
- **Epistemic value: MODERATE-HIGH, and the strongest OCCLUSION-REDUCER available** — it makes the featureless
  spectrum reveal lines, partially de-occluding the emitting region.
- **Major caveat (red-team):** acid SBSL may not be the *same phenomenon* as water SBSL; transferring its
  conclusions to water is a `CONTESTED` inference, not a measurement. Largely *already done* (Suslick) → marginal
  new value is in **time-resolved** acid spectroscopy (= A applied in the line-rich medium).
- **Falsifies:** H5(vacuum) if lines scale with gas/medium chemistry (they do); supports H3 if self-absorption
  shows an optically thick core.

### G. Bubble-radius control
- **do(x):** control ambient/maximum radius (via gas concentration, drive shaping).
- **Predictions:** emission-vs-(Rmax/Rmin/compression-ratio) scaling could differ by mechanism (`UNKNOWN`-leaning,
  like E); mostly maps the dynamics→emission relation.
- **Separates:** ~**0–2**, mostly `UNKNOWN`. **LOW-MODERATE.**

### H. Multi-bubble (MBSL) vs single-bubble (SBSL)
- **do(x):** compare regimes; MBSL gives stronger, line-rich spectra.
- **Predictions:** lines in MBSL `sep` H5 from thermal; tests universality/transfer more than micro-mechanism.
- **Separates:** ~**2–3**, **mostly already exploited.** MODERATE, low marginal value.
- **Caveat:** SBSL≠MBSL transfer is itself `CONTESTED`.

### J. (added) Hard-UV / X-ray photon detection (or calibrated null)
- **do(x):** look for the high-energy photon tail that escapes (or fails to escape) the core.
- **Predictions (DECLARED):** H1 bremsstrahlung → a power-law high-energy tail; H3 blackbody → an exponential
  cutoff (no hard tail); H2 recombination → edges, intermediate. So **H1 vs H3 `sep`** on the hard-photon
  signature; bounds core T regardless.
- **Separates:** ~**1–2 strong** (H1 vs H3, the hardest sub-mechanism pair) **and reduces occlusion** (hard
  photons probe the core more directly than the visible continuum).
- **Epistemic value: MODERATE-HIGH *if feasible*.** **Feasibility risk is the headline failure mode:** the
  predicted hard-photon flux may be far too low to detect, and may be absorbed by an optically thick core — in
  which case the **null is ambiguous** (no photons ≠ no hard source; an `OCCLUSION` not a refutation). Design
  must pre-register what a null means.

## 2. Discrimination matrix (pairs forced into mutually-exclusive predictions; `DECLARED` predictions)

| Experiment | H1·H2 | H1·H3 | H2·H3 | thermal·H4 | thermal·H5 | H4·H5 | **sep / 10** | Occlusion ↓ |
|---|---|---|---|---|---|---|---|---|
| **A** time-resolved flash(t,λ) | sep | sep | sep | UNK | sep | sep | **~7** | **HIGH** |
| **F** liquid (acid lines) | UNK | sep | UNK | UNK | sep | sep | **~4–5** | **HIGH** |
| **J** hard-UV/X-ray | UNK | **sep** | UNK | UNK | UNK | UNK | **~1–2** | MED–HIGH (if feasible) |
| **B** noble-gas sweep | same | same | same | UNK | sep | sep | **~4** (marginal LOW) | none |
| **E** pressure/drive scaling | sep? | sep? | sep? | UNK | UNK | UNK | **~1–3** (confounded) | none |
| **H** MBSL vs SBSL | UNK | UNK | UNK | UNK | sep | sep | **~2–3** (already done) | MED (lines) |
| **G** radius control | UNK | UNK | UNK | UNK | UNK | UNK | **~0–2** | none |
| **C** isotope H₂O/D₂O | UNK | UNK | UNK | UNK | (weak) | UNK | **~0–1** | none |
| **D** frequency sweep | same | same | same | UNK | UNK | UNK | **~0** | none |

(The dense band of `UNK` in the H4 and H5 columns is the §0 finding made visual: it is category mismatch +
under-commitment, not measurement weakness.)

## 3. Ranked experimental roadmap

Ranked by **(1) expected epistemic gain**, then **(2) cost**, **(3) feasibility**, **(4) occlusion reduction.**

| Rank | Experiment | Gain | Cost | Feasibility | Occlusion ↓ | Verdict |
|---|---|---|---|---|---|---|
| **1** | **A — time-resolved flash(t, λ)** | HIGH (~7) | High | Hard but demonstrated | **HIGH** | **the next experiment** — separates the live H1/H2/H3 dispute *and* de-occludes |
| **2** | **F′ — time-resolved spectroscopy in conc. H₂SO₄ / line-rich media** | MOD-HIGH | Medium | **Demonstrated** (Suslick static; time-resolve it) | HIGH | A applied where lines already exist — fastest realizable path |
| **3** | **J — hard-UV / X-ray tail (or pre-registered null)** | MOD-HIGH* | Medium | **Risky** (flux/escape) | MED-HIGH | unique H1 vs H3 separator; *null must be pre-defined* |
| 4 | B — adversarial noble-gas sweep | LOW marginal | Low | Easy | none | cheap; mostly re-confirms H5 loses |
| 5 | E — pressure/drive scaling | MOD-confounded | Low | Easy | none | needs independent T to deconfound |
| 6 | H — MBSL vs SBSL | LOW marginal | Low | Easy | MED | largely done; transfer caveat |
| 7 | G — radius control | LOW | Low | Easy | none | dynamics mapping |
| 8 | C — isotope H₂O/D₂O | CONDITIONAL | Low | Easy | none | **blocked on Recommendation #0** |
| 9 | D — frequency sweep | LOW | Low | Easy | none | envelope mapping, not discrimination |

**Recommendation #0 (free, ranks above all of them):** force H1/H2/H3 (and an instantiated H5) to publish
`pred(H, do(A))` and `pred(H, do(E))`. Until they commit, A's value is *potential* ~7; commitment is what
realizes it, and it costs nothing.

## 4. Highest-value next experiment

**A — sub-ps, spectrally-resolved `flash(t, λ)`**, run *first in a line-rich medium* (F′) where photon counts and
spectral features are highest. It is the only candidate that (a) separates the genuinely live dispute
(bremsstrahlung vs recombination vs opacity), (b) re-confirms or finally retires H5 on timing, and (c) **reduces
the occlusion** by delivering a less-compressed projection of the core. Precondition: Recommendation #0.

## 5. The single observation most likely to change the field

**A measured `flash(t, λ)` (or a hard-photon tail, J) that is incompatible with thermal emission from a ~10⁴ K
partially-ionized gas.** Not a new confirmation of plasma — a *spectral-temporal signature no thermal model
reproduces*. That single result would falsify the **dominant** model (not just one sub-mechanism), which is the
highest-impact outcome available; any result that merely matches a thermal continuum leaves the field where it
is. (Symmetrically: a hard-photon tail matching bremsstrahlung *and* excluding a blackbody cutoff would, for the
first time, settle H1-vs-H3 by intervention rather than by fit.)

## 6. What would be NEW evidence vs additional confirmation

**New evidence (converts `DECLARED`/`CONTESTED` → `MEASURED_BY_INTERVENTION`):**
- a time-resolved `flash(t, λ)` that uniquely matches *one* of {bremsstrahlung, recombination, blackbody};
- a hard-UV/X-ray photon tail, or a *pre-registered* calibrated null bounding it;
- a within-thermal-family divergence under a committed prediction (e.g., a scaling exponent that excludes one
  emission model);
- any measurement that constrains the **core T/P directly** (reduces the `OCCLUSION`);
- a calibrated single-bubble nuclear-signature result (positive or null) bounding the extreme-T tail.

**Confirmation only (does not move provenance — do not fund as discrimination):**
- more brightness / photon-count measurements;
- more time-*integrated*, featureless water spectra;
- re-confirming the noble-gas dependence or that the flash occurs at collapse;
- more Mie `R(t)` curves matching hydrodynamics;
- more MBSL line spectra that re-establish "a plasma exists."

## 7. Epistemic bottlenecks (red-team summary)

1. **Hypothesis set is not a partition** (§0): H4 is a different axis from H1/H2/H3; H5 is under-committed.
   Many `UNKNOWN` cells are this, not measurement difficulty. *Fix the question before funding the experiments.*
2. **Theory under-commitment:** the `UNKNOWN`-heavy columns (C, E, H4 everywhere, H5) mean hypotheses have not
   stated divergent predictions. Closing this is **free** and must precede ranking realization.
3. **Interior `OCCLUSION`:** core T/P/ionization are reconstructed indirectly (not `SEVERED` — instrument-limited;
   see audit §7). A and J reduce it; none eliminate it.
4. **Same-observable-multiple-generators = `INTERVENTION_ONLY`:** the time-*integrated* featureless spectrum fits
   H1/H2/H3 equally — which is *why* the less-compressed `flash(t, λ)` is #1.
5. **Transfer assumption:** acid/MBSL evidence (F, H) may not transfer to water SBSL — a `CONTESTED` inference
   wearing a measurement's clothing; do not silently generalize it.

## Honest scope

I am the test-design lead, not the physics oracle. Every prediction here is `DECLARED` (mine); the matrix is a
*plan over predictions*, an allocation of investigation, **never a verdict**. Its realized value depends on the
hypotheses committing to their own `pred(H, do(x))` — the cheapest and highest-leverage action on the board.
`observation ≠ intervention`; `absence of evidence ≠ evidence of absence`; `UNKNOWN ≠ discrimination`;
`declared ≠ verified`. The goal was never to solve sonoluminescence — it was to maximize the rate at which its
uncertainty is eliminated, and the answer is: **commit the predictions (free), then run `flash(t, λ)`.**
