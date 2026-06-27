<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# snowflake/ — snow-crystal "quantum design" studied with the Ursprung verify toolkit

A study, not an endorsement: it applies the repository's verification discipline (a frozen invariant +
`CLOSED/VIOLATED` grading + an independent oracle + a built-in falsifier; the epistemic ladder + the
`AnalysisResult` honesty contract) to the question *"what does quantum structure actually design in a
snowflake, and what is overclaim?"* `integrity ≠ truth`; `possibility ≠ actuality`.

## The two parts

**`snow_lattice.py` — six-fold symmetry as shared-cause, not communication.** A snow crystal's hexagonal habit
comes from ice Ih's lattice (water's tetrahedral hydrogen bonding — a molecular/quantum boundary condition).
The *similarity of the six arms* is a separate question, and the established answer (Libbrecht) is that the arms
do **not** communicate — they share one tiny air pocket, so a shared (temperature, supersaturation) trajectory
plus a deterministic growth law makes them match. We encode an arm as a 1-D growth profile driven **only** by
its own schedule (a structural no-communication channel) and check the `six_fold` invariant:

- shared field ⇒ identical arms ⇒ `CLOSED` (symmetric);
- per-arm field ⇒ arms diverge ⇒ `VIOLATED` with a witness — even though arms are identical and never read each
  other. So symmetry is a **shared-cause signature, not a signal**. `correlation ≠ communication`.

A Nakaya-style `morphology(T, supersaturation)` map supplies the deterministic growth law (plates/columns/
needles/dendrites by regime). Model boundary (Arbitrary-Boundary Law): this proves the *logic* of the symmetry
on an abstracted 1-D model; it is not a 2-D diffusion-limited growth simulation. `holds-here ≠ true`.

**`quantum_ledger.py` — quantum→design claims, graded with falsifiers.** Each claim carries a grade on the
ladder (ESTABLISHED / MEASURED / UNDERDETERMINED / SPECULATIVE / NOT_MEASURED), the mechanism it rests on, what
it does **not** show, and a falsifier; each projects into the honesty contract (scope + ≥1 limitation).

| id | claim | grade |
|----|-------|-------|
| C1 | hexagonal habit ← water's tetrahedral H-bonding (ice Ih) | ESTABLISHED |
| C2 | six arms similar via shared environment, not communication | ESTABLISHED |
| C3 | nuclear quantum effects tune H-bonds (D₂O ice melts ≈ +3.8 K) | MEASURED (mechanism subtle) |
| C4 | proton disorder ⇒ residual entropy S ≈ R·ln(3/2) ≈ 3.37 J·mol⁻¹·K⁻¹ | ESTABLISHED |
| C5 | macroscopic quantum **coherence** designs snowflake morphology | **SPECULATIVE** (no support) |
| C6 | ice XI is the proton-ordered phase (≈ 72 K, KOH-doped) | ESTABLISHED (lab; not atmospheric) |

The legitimate quantum link is **molecular and bounded** (C1/C3/C4/C6). The popular "snowflakes are quantum
designs" reading (C5) is graded SPECULATIVE — and a test asserts the ledger never launders it into "settled".

## The language-hypothesis audit (does morphology encode information beyond physics?)

A separate, falsification-first investigation — full write-up in [`LANGUAGE_AUDIT.md`](LANGUAGE_AUDIT.md):

- `snow_grammar.py` — defines a snowflake **context-free grammar** (alphabet F/B/T, production rules, parse
  tree, decoder) and then **reduces every symbol to a physical mechanism** + shows **no MDL gain** over the
  physical field encoding. The grammar is a re-encoding, not a new theory. `representation ≠ explanation`.
- `snow_infotheory.py` — the decisive tests: **conditional** mutual information between branches *given the
  shared field* (the only quantity that could be a "language channel"); compression-gain `== I(X;Y|field)`;
  and the **semantic-manifold dimension == number of physical controls**. Under standard physics the channel
  is ≈ 0; an injected channel is detected — so the hypothesis is falsifiable, and falsified for the null model.

### Verdict (hardened)

Snowflake morphology admits multiple information-theoretic representations — a grammar, a graph language, a
low-dimensional manifold, compressible symbolic descriptions — but **every one reduces to the established
field-driven crystal-growth dynamics**. They improve description and compression; they do **not**, by
themselves, yield predictions beyond conventional physics. Within the evidence here, every proposed "hidden
language" collapses to an alternative representation of known dynamics. `representation ≠ explanation`.

The single hypothesis that would be genuinely new physics is an **inter-branch information channel** unexplained
by the local growth field:

> `I(branch_i ; branch_j | local field) > 0`

i.e. statistical dependence between branches *after conditioning on the complete local physical environment*.
The repository does **not** establish that such a channel exists. It establishes something narrower and
stronger: an **executable falsification framework** that distinguishes the null (all dependence explained by
the local field) from the alternative (residual inter-branch information) — demonstrated, on its modeled
systems, to be **detectable if present** (`H2` CMI ≫ null) and **absent under the null** (`H0` CMI ≈ null ≈ 0),
with a concrete diffusion-chamber experiment that would discriminate the two on real crystals.

Three caveats this framework keeps explicit, because they are load-bearing:

1. **"Complete local field" is never fully measurable.** Empirically you condition on the *best-observed*
   field, so a positive `I(branch_i;branch_j | field_observed)` is evidence of *residual dependence* — either a
   genuine channel **or** unobserved-confounder leakage (field mis-specification). That is exactly why the
   protocol pairs the conditional-MI estimate with a **within-field shuffle null** *and* deliberate **field
   mis-specification** stress: a real channel is mis-specification-stable; leakage is not.
   `residual-CMI ≠ channel` until it survives those checks. `integrity ≠ truth`.
2. **"Absent under the null" is a statement about the modeled system, not a measurement of nature.** No real
   snowflakes were analyzed here; the contribution is the *discriminator and its demonstrated power /
   specificity*, not a physical result. The negative must not be over-read as "proven no channel in nature."
3. **Stronger because narrower, and reusable.** The confounder-conditioned-MI + shuffle-null +
   mis-specification protocol generalizes to any "hidden coordination" claim where a shared driver masquerades
   as communication (biological patterning, market co-movement, neural assemblies). The snowflake case is the
   clean worked example. `shared-cause ≠ signal`.

**Smallest surviving claim (Demonstrated):** growth histories are exactly a context-free grammar whose every
production corresponds to a physical mechanism, with no description-length gain over the field encoding —
representational parsimony, not a hidden language. **Only remaining route to a stronger claim is empirical:**
detect a statistically significant residual inter-branch channel in real crystal-growth experiments that
survives conditioning on the complete local field. `confounded-MI ≠ channel`.

## Run

```powershell
cd "weltwerk\verify\snowflake"; python snow_lattice.py; python quantum_ledger.py; python snow_grammar.py; python snow_infotheory.py; python test_snow_lattice.py; python test_quantum_ledger.py; python test_snow_grammar.py; python test_snow_infotheory.py
```

Pure-stdlib; reuses `artifacts.Invariant` and `artifacts.AnalysisResult/Finding/Limitation` from the verify
kernel. Each test suite is validity-not-outcome: it asserts the apparatus is honest, not that a physical result
is "good".

## Sources (grounding for the ledger quantities)

- Six-fold similarity via shared environment (Libbrecht): ScienceABC, *Why Do Snowflakes Have Such Fascinating Shapes?*; Wikipedia, *Snowflake*.
- Pauling residual entropy S ≈ R·ln(3/2) ≈ 3.37 J·mol⁻¹·K⁻¹: SklogWiki, *Entropy of ice phases*; *Residual Entropy of Ice: A Study Based on Transfer Matrices* (arXiv:2404.13897).
- Nuclear quantum effects / D₂O–H₂O isotope effect (≈ 3.8 K): *Opposing Electronic and Nuclear Quantum Effects on Hydrogen Bonds in H₂O and D₂O* (PMC6790677); *Zero-point energy effects on the stability of water clusters* (AIP Advances 2024).
