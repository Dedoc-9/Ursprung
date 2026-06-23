<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# SONOLUMINESCENCE — an auditable causal phenomenon (Ursprung epistemic framework)

> A research application of the auditable-epistemology stack to a physical phenomenon, not renderer code.
> **Core question:** how much of sonoluminescence is directly *measured*, how much is *inferred*, and where do
> explanations exceed evidence? Rules held throughout: observation ≠ intervention · preserve competing
> hypotheses · absence of evidence ≠ evidence of absence · do not average away disagreement · measured ≠
> inferred · every conclusion carries its provenance · **strength is never upgraded.**

This note audits *single-bubble* sonoluminescence (SBSL) primarily, with multi-bubble (MBSL) where it carries
evidence. It is written by a non-specialist applying a discipline; the physics claims are web-grounded (see
**Sources**) but the audit's value is the *provenance structure*, not new physics. `declared ≠ verified`.

## 0. Provenance legend (the only rollup; never upgraded)

```
MEASURED                 directly observed with an instrument (a number read off a detector)
MEASURED_BY_INTERVENTION a manipulation (do(x)) changed the outcome — a causal, not merely correlational, result
DECLARED                 a model inference / leading explanation consistent with data, but no probe establishes it
CONTESTED                conflicting evidence or competing models that data does not resolve (kept apart, not averaged)
N/A                      the axis does not apply
```
A *measured spectrum* is `MEASURED`; a *temperature extracted from it by a model* is at most `DECLARED` (or
`MEASURED` only of the emitting region, model-dependent). The interior core state is, for water SBSL, never
directly measured — it is a **hidden variable** (§6).

---

## 1. Observation layer — what is actually measured vs derived

| Observable | What is directly measured | Provenance | What is *inferred* from it (do not conflate) |
|---|---|---|---|
| **Existence of the flash** | photons detected, periodic, phase-locked to the drive (Gaitan 1990, stable SBSL) | MEASURED | — |
| **Bubble radius R(t)** | Mie/laser light-scattering off the bubble surface → R(t) curve: R₀≈3–5 µm, R_max≈30–50 µm, R_min≈0.5 µm | MEASURED (surface only) | collapse wall-velocity (supersonic), compression ratio — derived from R(t) + model |
| **Acoustic drive** | transducer/hydrophone: f≈20–40 kHz, drive pressure ≈1.2–1.5 atm | MEASURED (in the bulk liquid) | pressure *at/inside* the bubble — inferred (§6) |
| **Flash duration** | streak camera / time-correlated single-photon counting → ~tens–hundreds of ps | MEASURED | the *internal* collapse timescale (sub-ps) — not resolved |
| **Emitted spectrum (water SBSL)** | broadband continuum rising toward UV, *featureless*, cut off by water UV absorption | MEASURED | a fitted "temperature" / mechanism — underdetermined by a featureless continuum |
| **Emitted spectrum (conc. H₂SO₄ SBSL, dopants, MBSL)** | discrete **emission lines/bands**: Ar atomic lines, SO molecular, O₂⁺ ionic progressions (Flannigan–Suslick 2005) | MEASURED | excitation temperature, ionization, opacity — model-extracted |
| **Emitting-region temperature** | line-ratio / band-fit spectroscopy on the *measured* lines → ≈6,000–~15,000 K (medium-dependent) | MEASURED *of the emitting region*, model-dependent (LTE/opacity assumed) | the *core peak* temperature — separate, inferred, higher |
| **Gas-content dependence** | vary dissolved/noble-gas content → intensity changes (see §3) | MEASURED_BY_INTERVENTION | argon "rectification" mechanism — inferred (§2) |
| **Bubble interior (T, P, ρ, ionization, geometry at peak)** | *nothing directly* — the core is sub-µm, sub-ns, possibly optically thick; we receive only integrated emitted light | **not measured** → hidden variable (§6) | essentially all "extreme conditions" claims |

The cardinal split: **R(t), flash timing, spectra, and gas/parameter dependences are measured. The interior
state at peak collapse is not** — it is a projection (the escaping light), and recovering the generator (core
conditions) requires additional structure (a model). `observable ≠ generator`.

---

## 2. Mechanism layer — explanatory models, each with evidence / assumptions / falsifiers / dependencies

### 2.1 Adiabatic heating → partial ionization → thermal emission (bremsstrahlung + recombination) — the dominant model
*(Hilgenfeldt–Grossmann–Lohse 1999; Brenner–Hilgenfeldt–Lohse, Rev. Mod. Phys. 2002.)*
- **Evidence:** R(t) from Mie scattering matches Rayleigh–Plesset/Keller–Miksis hydrodynamics with violent
  near-adiabatic collapse (strong); plasma emission lines in acid/MBSL confirm a partially-ionized hot gas
  (strong, but in special media); intensity rises with noble-gas content and falling liquid temperature
  (intervention, strong).
- **Assumptions:** near-adiabatic, near-spherical compression; the gas reaches ionization; emission is thermal
  (bremsstrahlung/recombination) from a ~10⁴ K plasma; local thermodynamic equilibrium for temperature
  extraction.
- **Falsifiers:** a spectrum/timing that no ~10⁴ K thermal plasma can reproduce; absence of the noble-gas /
  temperature / pressure dependences; line emission requiring non-thermal excitation.
- **Unresolved dependencies:** the *core* peak T and P (hidden, §6); whether emission is bremsstrahlung-,
  recombination-, or opacity/blackbody-dominated is **not** settled (§2.2).

### 2.2 Sub-mechanism dispute *inside* the thermal picture: bremsstrahlung vs recombination vs finite-opacity "blackbody"
- **Evidence:** all fit the *featureless* water continuum about equally — which is the problem.
- **Falsifier / separator:** a sub-ps time-resolved spectrum, or isotope/gas scaling that the three predict
  differently. **Not yet done decisively.**
- **Status:** `CONTESTED` — a featureless continuum **underdetermines** the microscopic emission process.
  The 2010 "inertially confined plasma" work (Flannigan–Suslick) infers an **optically thick** core from line
  self-absorption, pushing toward a high-opacity picture — a refinement, still model-dependent.

### 2.3 Argon rectification (why air bubbles glow at all)
*(Lohse et al.; Storey–Szeri, PRL 2002.)*
- **Evidence:** **intervention** — pure-N₂ bubbles barely emit; brightness peaks near ~1% argon (air's argon
  fraction); doping with noble gas raises intensity. Reactive gases (N₂, O₂) chemically burn off, leaving argon.
- **Assumptions:** dissociation + dissolution of reactive species; partial-pressure stability argument; supported
  by simulation (which gives ~7000 K — notably *too low* for bremsstrahlung-dominated emission, an internal
  tension).
- **Falsifier:** show brightness independent of noble-gas fraction, or that reactive gases persist.
- **Status:** the *dependence* is `MEASURED_BY_INTERVENTION`; the *rectification mechanism* is `DECLARED`
  (inference consistent with the intervention + simulation).

### 2.4 Shock-wave focusing inside the bubble
- **Evidence:** some hydrodynamic models produce an inward-converging shock that concentrates energy at the
  center; consistent with extreme central conditions.
- **Assumptions:** near-perfect spherical convergence at sub-µm scale; shock formation.
- **Falsifier:** imaging/measurement showing no shock or that emission timing/extent is incompatible with a
  focused shock; models reproducing all data *without* a shock (these exist).
- **Status:** `DECLARED` / debated — neither required by nor excluded by the measured data; depends on the
  unobserved **collapse geometry** (§6).

### 2.5 Quantum-vacuum / dynamical Casimir (Schwinger; Eberlein variant)
- **Evidence:** none uniquely supporting; motivated by the speed of the moving dielectric boundary.
- **Assumptions:** photon production from vacuum fluctuations under the collapsing dielectric interface.
- **Falsifier (applied):** quantitative tests (Liberati–Visser et al., "Sonoluminescence as a QED vacuum
  effect") find the predicted photon number / spectrum / timing **inconsistent** with observation (e.g.,
  Schwinger-type estimates peak emission at maximum radius, not at collapse).
- **Status:** `CONTESTED` → effectively **refuted as the primary mechanism** on quantitative grounds. *Preserved*
  as a minority hypothesis (rule: absence of a role is not proven), but it loses the quantitative tests; do not
  average it with the thermal model.

### 2.6 Alternative / fringe: chemiluminescence, electrical microdischarge, "sonofusion"
- **Chemiluminescence / electrical breakdown:** minor contributors at most; consistent with some line emission
  in MBSL; not the dominant continuum. `DECLARED` (partial role) / `CONTESTED`.
- **Sonofusion (Taleyarkhan 2002):** claimed neutron/tritium signatures of D-D fusion in cavitating deuterated
  acetone. **Independent replication failed** (Putterman–Suslick reconstruction found no fusion; Oak Ridge
  replication failed); misconduct findings attached at Purdue. `CONTESTED` → **not accepted**; treat as
  unsupported (not disproven-in-principle, but the positive claim does not survive replication).

---

## 3. Causal audit — observation ≠ intervention

**Supported by manipulation (`MEASURED_BY_INTERVENTION`) — do(x) moved the outcome:**
- do(gas composition): noble-gas doping ↑ intensity; N₂-only ≈ dark; ~1% Ar optimum. *Strongest causal lever;
  load-bearing for argon rectification and for "the emitter is the trapped gas."*
- do(dissolved gas / ambient pressure): changes stability and photon count.
- do(liquid): water → concentrated H₂SO₄ dramatically ↑ brightness and *reveals emission lines* (Suslick) — the
  manipulation that turned an inferred plasma into a measured one.
- do(liquid temperature): lowering it sharply ↑ intensity.
- do(dopant atoms): seeding emitter species produces their spectral lines (MBSL spectroscopy).

**Consistent with observation only (correlational / model-fit — NOT intervention):**
- The *microscopic emission mechanism* (bremsstrahlung vs recombination vs opaque-blackbody): all fit the
  spectrum; no intervention cleanly separates them → `CONTESTED` (§2.2).
- The *core peak temperature and pressure*: extracted from models fit to R(t) and spectra; **no manipulation
  reaches the interior to test them** (§6).
- Shock-wave focusing: model-consistent, not intervened.
- Quantum-vacuum: not even consistent quantitatively (§2.5).

> The decisive epistemic fact: **interventions act on the *inputs* (gas, liquid, drive) and read the *outputs*
> (light); none act on the *interior at peak*.** So conclusions about what the gas *does* are intervention-grade;
> conclusions about *how hot/dense the core gets and why it radiates* are model-grade.

---

## 4. Multi-witness analysis (agreements · refinements · genuine conflicts)

| Witness | Says | Relation to others |
|---|---|---|
| **Acoustics** | drive f, P_drive, bubble trapping & stability (Bjerknes/shape) | sets boundary conditions; agrees with hydrodynamics |
| **Fluid dynamics** | Rayleigh–Plesset/Keller–Miksis R(t), violent collapse | **agrees** with the measured Mie R(t) — a strong corroboration |
| **Experimental measurement** | R(t), ps flash, spectra, gas dependence | the ground truth the others are scored against |
| **Plasma physics** | emission lines ⇒ partially-ionized hot gas; opacity (2010) | **agrees** in acid/MBSL (measured lines); **refines** the bare adiabatic picture toward an optically-thick core |
| **Thermodynamics** | adiabatic compression → ~10⁴ K | agrees in order of magnitude; **conflicts numerically** across methods |
| **Quantum theory** | dynamical-Casimir photon production | **conflicts** quantitatively → loses |

- **Agreements (high confidence):** hydrodynamics ↔ measured R(t); gas-doping intervention ↔ "the trapped gas is
  the emitter" ↔ argon rectification; emission lines ↔ a real plasma (in the media where lines appear).
- **Refinements (stronger witness corrects weaker):** measured plasma lines + inferred opacity (Suslick 2005/2010)
  *refine* the early simple "adiabatic hot gas / variable-blackbody" picture — without overturning it.
- **Genuine conflicts (preserved, not averaged):**
  - *temperature values* differ by method — argon-rectification simulation ~7000 K vs spectroscopic ~15,000 K vs
    higher core-model estimates. **Do not average to ~11,000 K** — they measure different things (bulk-gas model
    vs emitting-region spectrum vs inferred core) and the gap is information.
  - *thermal-plasma vs quantum-vacuum*: a real conflict, resolved against the vacuum model on quantitative
    grounds, but recorded as a conflict, not erased.
  - *bremsstrahlung vs recombination vs opaque-blackbody*: unresolved sub-conflict inside the winning camp.

---

## 5. Epistemic provenance of major conclusions (never upgraded)

| Conclusion | Provenance | Note |
|---|---|---|
| Acoustically-driven bubbles collapse and emit short, phase-locked light flashes | **MEASURED** | the phenomenon itself |
| R(t) follows violent near-adiabatic collapse dynamics | **MEASURED** (surface) | Mie scattering; interior not seen |
| Flash duration ~tens–hundreds of ps | **MEASURED** | streak/TCSPC |
| Bright SL **requires** a noble (especially inert) gas; ~1% Ar optimal in air | **MEASURED_BY_INTERVENTION** | gas doping |
| Brightness rises with falling liquid T / changed ambient pressure | **MEASURED_BY_INTERVENTION** | parameter sweeps |
| The emitter is the trapped gas, and air bubbles "rectify" to argon | **DECLARED** (mechanism) over MEASURED_BY_INTERVENTION (dependence) | inference consistent with doping + sim |
| The collapsed bubble contains a hot, partially-ionized **plasma** | **MEASURED** in conc. acid/MBSL (lines); **DECLARED** in water SBSL (no lines) | split by medium — do not generalize the measured case to water |
| Emitting-region temperature ≈ 10⁴–~15,000 K | **MEASURED** of the emitting region, **model-dependent** | not the core peak |
| The **core** reaches ≫15,000 K and ~GPa-scale pressures at peak | **DECLARED / CONTESTED** | hidden variables; values disagree (§6) |
| Primary emission = thermal bremsstrahlung + recombination | **DECLARED** | leading; underdetermined vs opaque-blackbody |
| Shock-wave focusing concentrates the energy | **DECLARED** | model-dependent on collapse geometry |
| Sonoluminescence is a quantum-vacuum (dynamical Casimir) effect | **CONTESTED** (loses quantitatively) | preserved as minority, not averaged in |
| Sonoluminescence produces thermonuclear fusion (sonofusion) | **CONTESTED** → not replicated | unsupported positive claim |

---

## 6. Hidden-arbitrage search — dependence on quantities that cannot be directly measured

The "extreme conditions" narrative is **arbitraged** on interior variables no instrument reaches in water SBSL:

| Hidden variable | Directly measurable? | Conclusions that depend on it | Arbitrage exposure |
|---|---|---|---|
| **Core peak temperature** | No (water SBSL); only emitting-region T in special media | "star-in-a-jar," any fusion-adjacent claim, bremsstrahlung dominance | **High** — the headline-grabbing claims live here |
| **Pressure peaks (~GPa/kbar)** | No — purely model-inferred from R(t) + EoS | shock focusing, extreme-state chemistry | **High** |
| **Plasma state (ionization fraction, opacity)** | Partially (lines/self-absorption in acid; inferred in water) | emission mechanism, the 2010 opacity refinement | **Medium** |
| **Collapse geometry (sphericity, shock)** | No, at the relevant sub-µm/sub-ns scale | shock-wave-focusing models | **Medium–High** |

**Estimated dependence:** the robust, low-arbitrage core — *"a noble-gas plasma forms at collapse and radiates
thermally"* — rests on measured spectra (in acid/MBSL) + intervention (doping). The high-arbitrage shell —
*specific core T/P values, shock focusing, fusion-adjacent energy densities* — depends almost entirely on
unmeasured interior quantities supplied by models. A reader should treat the *existence and rough nature* of the
hot plasma as well-founded and any *specific extreme number for the core* as a model output wearing a
measurement's clothing. `compress ≠ sever`: the measured spectrum is a compressed projection of the core;
reconstructing the core from it without an independent witness is the severance to flag.

---

## 7. Failure-mode matrix (assigned only where justified)

| Claim / target | Failure mode | Justification | Not-assigned where |
|---|---|---|---|
| **Microscopic emission mechanism** (bremsstrahlung vs recombination vs opaque-blackbody) | **INTERVENTION_ONLY** | observation (featureless continuum) underdetermines it; separating the sub-mechanisms needs a manipulation that resolves the emitting plasma directly — not yet possible | — |
| **Core interior state at peak** | **OCCLUDED** (instrument-relative — *not* structural `SEVERED`) | presently reconstructed only *indirectly* from projections (sub-µm, sub-ns, possibly optically thick); we receive integrated escaped light. **Self-correction:** an earlier draft of this audit labeled this `SEVERED` (= *no recovery path exists*). That is the absence-of-evidence→evidence-of-absence upgrade this framework forbids — new probes have opened apparently-inaccessible interiors before (stellar interiors, neutrinos, gravitational waves). The honest label is *instrument-limited*: a strong epistemic warning **without** a claim of impossibility | the *inputs→light* chain (`MEASURED_BY_INTERVENTION`) — fully accessible |
| **Temperature ↔ emission-mechanism inference loop** | **NON_ORIENTABLE** (mild) | the temperature is extracted using a model that assumes the emission mechanism, whose validity depends on the temperature — a co-dependence with no fully independent anchor (a circular gate, cf. M6b). Lines in acid partly break it; water SBSL does not | — |
| **Instrument vs event timescale** | **FLOODED** (weak/declared) | the internal collapse dynamics (sub-ps) outrun detector bandwidth, so verification cannot keep pace with the phenomenon's internal clock — assigned cautiously; this is an instrument-throughput limit, not a system overload | the *flash envelope* itself (that **is** resolved → not FLOODED) |
| Existence / R(t) / gas dependence | **none** | these are `MEASURED` / `MEASURED_BY_INTERVENTION` — no failure axis applies | — |

(The four axes are the Ursprung `FAILURE_MODE_MATRIX` set; `NON_ORIENTABLE` and `FLOODED` are assigned as mild
/ declared, not asserted — the discipline is to assign only when justified and to say when it's a stretch.)

---

## 8. Deliverables

### 8.1 Claim graph (claim ← evidence; provenance in brackets)

```
[Light is emitted at bubble collapse]             MEASURED
   ├── photon detection, phase-locked             MEASURED
   └── ps flash width                             MEASURED
        │
[The emitter is the trapped gas]                 MEASURED_BY_INTERVENTION
   ├── noble-gas doping ↑ intensity               MEASURED_BY_INTERVENTION
   ├── N2-only ≈ dark; ~1% Ar optimum             MEASURED_BY_INTERVENTION
   └──> [Air bubbles rectify to argon]            DECLARED (mechanism)  ← consistent w/ doping + simulation
        │
[A hot, partially-ionized plasma forms]          MEASURED (acid/MBSL lines) | DECLARED (water SBSL)
   ├── Ar/SO/O2+ emission lines (Suslick 2005)    MEASURED
   ├── inferred optical thickness (2010)          DECLARED (refinement)
   └──> [Emitting-region T ≈ 10^4–15,000 K]       MEASURED (model-dependent, of emitting region)
        │
[The CORE reaches ≫15,000 K and ~GPa]            DECLARED / CONTESTED   ← HIDDEN VARIABLES (§6)
   ├── R(t) + EoS hydrodynamic models             DECLARED
   ├── shock-wave focusing                        DECLARED (geometry-dependent)
   └── value conflict: ~7000 K (sim) vs ~15,000 K (spectro) vs higher (core models)   CONTESTED
        │
[Primary emission = thermal bremsstrahlung+recombination]   DECLARED  (vs opaque-blackbody: CONTESTED)
[Quantum-vacuum / dynamical Casimir is the cause]           CONTESTED → refuted quantitatively
[Sonoluminescence drives fusion]                            CONTESTED → not replicated
```

### 8.2 Evidence-strength table (ranked)

| Rank | Claim | Strength |
|---|---|---|
| 1 | Flashes exist, ps-scale, phase-locked; R(t) measured | MEASURED |
| 2 | Noble gas is required / rectification dependence | MEASURED_BY_INTERVENTION |
| 3 | A partially-ionized plasma exists (in acid/MBSL) | MEASURED (medium-specific) |
| 4 | Emitting-region T ~10⁴ K | MEASURED (model-dependent) |
| 5 | Thermal bremsstrahlung/recombination is the mechanism | DECLARED |
| 6 | Specific core T/P extremes; shock focusing | DECLARED / CONTESTED |
| 7 | Quantum-vacuum cause | CONTESTED (loses) |
| 8 | Sonofusion | CONTESTED (unsupported) |

### 8.3 Mechanism comparison matrix

| Mechanism | Evidence | Intervention-tested? | Key hidden dependency | Status |
|---|---|---|---|---|
| Adiabatic heating → ionization → thermal emission | strong (R(t), lines, doping) | partly (inputs only) | core T/P | **dominant / DECLARED+** |
| Argon rectification | strong (doping) | **yes** | — | well-supported (mechanism DECLARED) |
| Opaque-blackbody (finite opacity) | line self-absorption (2010) | no | opacity/geometry | refinement, CONTESTED vs bremsstrahlung |
| Shock-wave focusing | model-consistent | no | collapse geometry | DECLARED / debated |
| Quantum vacuum (Casimir) | none unique; quant. fails | no | — | CONTESTED → refuted |
| Sonofusion | not replicated | attempted, failed | — | CONTESTED → unsupported |

### 8.4 Highest-confidence findings
1. Acoustically-trapped bubbles emit ps-scale, phase-locked light at collapse (MEASURED).
2. Bright SL **requires a noble gas**; intensity is governed by inert-gas content (MEASURED_BY_INTERVENTION).
3. In the right medium (conc. H₂SO₄, dopants, MBSL) the collapsed bubble's emission shows **plasma lines** —
   a real, partially-ionized hot gas (MEASURED).

### 8.5 Most speculative claims
1. Specific **core** peak temperature/pressure values (DECLARED; hidden-variable arbitrage).
2. Shock-wave focusing as a *required* energy concentrator (DECLARED, geometry-dependent).
3. Quantum-vacuum origin (CONTESTED, quantitatively refuted) and sonofusion (CONTESTED, unreplicated).

### 8.6 Unresolved contradictions (preserved, not averaged)
- **Temperature by method:** ~7000 K (argon-rectification simulation) vs ~15,000 K (spectroscopy) vs higher
  (core models) — different referents; the gap is real information, not noise to average.
- **Emission micro-mechanism:** bremsstrahlung vs recombination vs finite-opacity blackbody — a featureless
  continuum cannot decide; the 2010 opacity result leans one way without closing it.
- **7000 K "too low for bremsstrahlung":** the rectification model's own temperature is in tension with the
  emission model it is meant to feed — an internal contradiction worth flagging, not smoothing.

### 8.7 Critical experiments that would collapse uncertainty
1. **Sub-ps, spectrally-resolved flash measurement** of water SBSL — would separate bremsstrahlung from
   recombination from opaque-blackbody (resolves §2.2 / the INTERVENTION_ONLY item).
2. **A direct interior probe** (e.g., escaping hard-UV/X-ray, or a tracer whose line shape reports core T/ρ
   independent of the emission-mechanism assumption) — would de-arbitrage the core T/P (resolves §6, partly
   breaks the NON_ORIENTABLE loop).
3. **Calibrated single-bubble nuclear-signature search** (neutrons/fusion products) with pre-registered nulls —
   would bound the extreme-T tail and settle the sonofusion question.
4. **Isotope/gas scaling sweeps** predicted differently by competing emission models — intervention to separate
   sub-mechanisms.
5. **Time-resolved imaging of collapse asphericity** at the relevant scale — would test shock-wave focusing.

### 8.8 What would falsify the dominant model (thermal noble-gas plasma)
- A measured **spectrum or flash-timing** that no ~10⁴ K partially-ionized thermal source can reproduce (e.g.,
  emission requiring non-thermal excitation, or scaling laws no thermal model fits).
- Demonstrating the **noble-gas / liquid-temperature / pressure dependences are absent or reversed** vs thermal
  predictions.
- A **quantitatively complete** alternative (e.g., a vacuum or electrical model) matching photon number,
  spectrum, **and** timing simultaneously — which would reopen the §2.5 conflict the thermal model currently wins.

---

## 9. Hypothesis-discrimination matrix — *the red-team move*

The audit above asks "which parts of each model are earned?". The discrimination matrix asks the sharper
question: **what manipulation would make the surviving hypotheses predict *different* observables?** Same
observable → multiple generators → `INTERVENTION_ONLY`; the only way out is an intervention whose predictions
*diverge*. Surviving hypothesis families (the vacuum and sonofusion families having already lost, §2.5/§2.6):

```
H1 thermal bremsstrahlung      H2 recombination-dominated      H3 finite-opacity / blackbody-like
H4 shock-wave focusing         (H5 vacuum-Casimir — retained only as the already-falsified control)
```

Each cell is **`DECLARED`** (a *predicted* divergence, a model output — not a measurement); `UNKNOWN` means the
published hypothesis has not committed to a divergent prediction for that intervention (an honest gap, **not** a
zero). Running the experiment is what would convert a separated pair from `DECLARED` to `MEASURED_BY_INTERVENTION`.

| Intervention `do(x)` | H1 vs H2 vs H3 (thermal sub-mechanisms) | thermal-family vs H5 (vacuum) | What it would separate |
|---|---|---|---|
| **time-resolved flash(t, λ)** (sub-ps, spectrally resolved) | **DIVERGE** — H1 continuum tracks T(t); H2 recombination features timed to cooling; H3 spectral shape evolves with optical depth | DIVERGE — emission at peak collapse (thermal) vs at max \|dV/dt\| (vacuum) | **the live dispute** (micro-mechanism, opacity, temperature evolution) |
| **noble-gas sweep He→Ne→Ar→Kr→Xe** (adversarial: each H's predicted trend) | weak — all thermal-family predict a trend with ionization potential / thermal conductivity (UNKNOWN which *differs* between H1/H2/H3) | DIVERGE — thermal-family predicts strong species dependence; vacuum predicts ~none (gas-independent) | thermal-family **from** vacuum (largely already spent — data shows strong gas dependence) |
| **isotope H₂O → D₂O** | UNKNOWN — no published per-sub-mechanism divergent prediction; liquid properties change collapse dynamics for *all* | UNKNOWN | currently **non-discriminating until the hypotheses commit** |
| **liquid-temperature sweep** | weak/UNKNOWN among survivors | (already shows dependence) | low among survivors |
| **better brightness / photon-count measurement** | NONE — all predict the same | NONE | **nothing** (the null experiment) |

**Meta-finding (a result, not a footnote):** most cells are `UNKNOWN` *not because the experiments are weak but
because the surviving hypotheses have not been forced to state `pred(H, do(x))`.* The bottleneck on
sonoluminescence is therefore **two** bottlenecks — (a) the interior is `OCCLUDED` (measurement), and (b) the
hypotheses are *under-committed* to divergent predictions (theory). Closing (b) is free and must precede ranking.

## 10. Experiment epistemic-value ranking — `value = # of DECLARED→MEASURED_BY_INTERVENTION conversions`

An experiment's worth here is not its cost or precision — it is **how many competing explanations it forces into
mutually-exclusive predictions** (how many `DECLARED` claims it would convert to `MEASURED_BY_INTERVENTION`). The
general ranking instrument is `experiments/live_world_kernel/discrimination_matrix.py` (verified, synthetic
self-test); applied by hand to the table above:

| Rank | Experiment | Pairs it separates | Converts | Expected epistemic gain |
|---|---|---|---|---|
| 1 | **time-resolved flash(t, λ)** | H1/H2/H3 *and* thermal/vacuum | emission micro-mechanism · opacity dispute · temperature-evolution | **HIGH** — reduces the `INTERVENTION_ONLY` core and partly de-`OCCLUDES` (a less-compressed projection) |
| 2 | **adversarial noble-gas sweep** | thermal-family / vacuum (mostly already done); weak within thermal-family | re-confirms vacuum loses; bounds ionization-driven vs not | **MEDIUM** (mostly already spent) |
| 3 | **isotope H₂O/D₂O** | UNKNOWN until hypotheses commit | — | **CONDITIONAL** — high *iff* (b) above is closed first |
| 4 | **liquid-T sweep** | weak among survivors | — | **LOW** |
| 5 | **better brightness measurement** | none | none | **ZERO** (the null) |

The one-line red-team prescription: **the next experiment is not "measure more light" — it is `time-resolved
flash(t, λ)`, the manipulation that makes the most surviving explanations predict different futures.** It is the
shortest path from "the micro-mechanism is `INTERVENTION_ONLY`" to "only one survives." (And the cheap
precondition: make each hypothesis publish its `pred(H, do(x))` so the matrix stops being sparse.)

## Honest scope

This is a *non-specialist provenance audit*, not a physics review; it is current to web sources cited below and
will age. The discipline applied — separate measured from inferred, mark intervention vs correlation, preserve
competing hypotheses, do not average disagreement, and never upgrade an evidence strength — is the deliverable.
The single most important takeaway in the framework's own terms: the bubble interior at peak collapse is
**OCCLUDED, not `SEVERED`** — *presently reconstructed indirectly from projections rather than directly
measured.* So every claim about *what the core is* is a model reconstruction of an incompletely-observed
projection, while the claims about *what the gas does* (inputs→light) are genuine intervention-grade results.
(The earlier `SEVERED` label, corrected in §7, is logged as a caught instance of the framework's own forbidden
move — upgrading "not yet observed" to "cannot be observed.") `observation ≠ intervention`; `observable ≠
generator`; `stable ≠ causal`; `declared ≠ verified`; **absence of evidence ≠ evidence of absence.**

## Sources

- Flannigan & Suslick, *Plasma formation and temperature measurement during single-bubble cavitation*, Nature 434, 52–55 (2005) — [nature.com](https://www.nature.com/articles/nature03361) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/15744295/)
- Flannigan & Suslick, *Inertially confined plasma in an imploding bubble*, Nature Physics 6, 598 (2010) — [nature.com](https://www.nature.com/articles/nphys1701)
- Brenner, Hilgenfeldt & Lohse, *Single-bubble sonoluminescence*, Rev. Mod. Phys. 74, 425 (2002) — [aps.org](https://link.aps.org/doi/10.1103/RevModPhys.74.425)
- Hilgenfeldt, Grossmann & Lohse, *Mechanism of single-bubble sonoluminescence*, Phys. Rev. E 60, 1754 (1999) — [aps.org](https://journals.aps.org/pre/abstract/10.1103/PhysRevE.60.1754)
- Storey & Szeri, *Argon rectification and the cause of light emission in single-bubble sonoluminescence*, PRL 88, 074301 (2002) — [aps.org](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.88.074301) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/11863899/)
- *Sonoluminescence* and *Mechanism of sonoluminescence* — [Wikipedia](https://en.wikipedia.org/wiki/Sonoluminescence) · [Wikipedia](https://en.wikipedia.org/wiki/Mechanism_of_sonoluminescence)
- Liberati, Visser et al., *Sonoluminescence as a QED vacuum effect: Probing Schwinger's proposal* — [arXiv quant-ph/9805031](https://arxiv.org/abs/quant-ph/9805031)
- *Bubble fusion* (Taleyarkhan controversy) — [Wikipedia](https://en.wikipedia.org/wiki/Bubble_fusion) · [Scientific American](https://www.scientificamerican.com/article/taleyarkhan-bubble-fusion-misconduct/)
