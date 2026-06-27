<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Does snowflake morphology encode a language? — a falsification-first audit

**Research-lead verdict (stated up front, per the brief):** On all evidence and experiments here, conventional
crystal-growth physics is **sufficient**. A snowflake admits a compositional *grammar*, but that grammar is a
**re-encoding** of known physics with no predictive gain. The single hypothesis-relevant quantity — information
between branches *beyond the shared environment* (conditional mutual information given the growth field) — is
**zero** under standard physics, and the suite shows it is **detectable when truly present**, so the language
hypothesis is *falsifiable* and *currently falsified for the null model*. The smallest claim that survives is
representational, not explanatory. `representation ≠ explanation`; `confounded-MI ≠ channel`; `integrity ≠ truth`.

This document is backed by executable artifacts in this folder; every claim below is classified
**Demonstrated** (passes a test here) / **Supported by literature** / **Plausible but unverified** /
**Speculative** / **Currently unfalsifiable**.

## 1. Established foundation (not re-litigated)

Molecular geometry → local ice structure; hydrogen-bond networks → hexagonal lattice; (T, humidity,
supersaturation, diffusion, attachment kinetics) → branching; nuclear quantum effects modify microscopic
bonding; classical instability (Mullins–Sekerka) amplifies microscopic differences into macroscopic
morphology. Everything beyond this must earn evidence. (Grounding + the molecular-quantum ledger:
`quantum_ledger.py`, `README.md` sources.)

## 2. A precise definition of a "snowflake language" (so it can be attacked)

- **Alphabet** Σ = {`F` facet, `B` branch, `T` tip} — the growth events emitted by the Nakaya map
  `morphology(T, supersaturation)` (`snow_grammar._mode`).
- **Grammar** G (context-free): nonterminal `A(r)` = "grow under regime r"; productions
  `A(r) → B A(r') A(r')` if `branch(r)` else `A(r) → F`. A derivation is a **parse tree** = the crystal.
- **Production rules** are listed in `RULE_TO_MECHANISM`; **semantics** = each rule's physical mechanism
  (faceting / tip-splitting instability / tip growth).
- **Information channel** (the testable core) = any statistical dependence between branches *not* explained by
  the shared growth field. Formal observable: `I(branch_i ; branch_j | field)`.
- **Decoding algorithm** = parse the tree back to the regime trajectory (`decode_levels`).
- **Prediction that would differ from physics** = `I(branch_i ; branch_j | field) > 0` (a real inter-branch
  channel). Standard physics predicts `= 0`.

## 3. The ten questions, answered and classified

| # | question | answer | class |
|---|----------|--------|-------|
| 1 | branching as a grammar, not only ODEs? | Yes — a CFG exists (`snow_grammar`), but each rule = a mechanism | **Demonstrated** (re-encoding) |
| 2 | repeated motifs as reusable "tokens"? | Yes — F/B/T recur; they are the Nakaya growth modes | **Demonstrated** (= physics) |
| 3 | hierarchical syntax in growth histories? | Trivially — branching is a tree; depth = growth time | **Demonstrated** (tautological) |
| 4 | symmetry as a communication constraint? | No — symmetry is shared-cause, not a channel (`snow_lattice`) | **Demonstrated against** |
| 5 | mutual information beyond diffusion between branches? | No — `I(·;·|field) ≈ 0` under H0 (`snow_infotheory`) | **Demonstrated against** |
| 6 | parse tree / probabilistic language model? | Yes as representation; a PCFG = the field-driven Markov law | **Demonstrated** (= physics) |
| 7 | compression finds latent symbolic structure? | Only the physical controls; gain beyond field = CMI = 0 (H0) | **Demonstrated** (= physics) |
| 8 | low-dimensional "semantic manifold"? | Yes — its dimension = the physical control count (Nakaya space) | **Demonstrated** (= physics) |
| 9 | generative models find reusable production rules? | They recover the physical branching/faceting rules | **Plausible but unverified** on real data |
| 10 | an experiment distinguishing language vs physics? | Yes — measure `I(branch_i;branch_j|field)` | **Demonstrated** (protocol valid) |

## 4. Multi-viewpoint reduction (each "symbol" reduced to physics before acceptance)

- **Statistical mechanics / dynamical systems:** branching = Mullins–Sekerka instability; the "grammar" is the
  symbolic dynamics of a field-driven growth map. No residual.
- **Information theory:** arm–arm MI is *confounded* by the shared field; the channel quantity is the
  conditional MI, which is 0 under H0. Compression gain beyond the field equals that conditional MI (proved by
  identity `H(Y|Z) − H(Y|X,Z) = I(X;Y|Z)`).
- **Computational / formal language theory:** the per-token law is **regular** (token = f(local field));
  branching adds context-free recursion but no context-sensitivity and no long-range agreement that the field
  does not already impose. No evidence for a grammar class richer than "physics + branching."
- **Graph theory / topology:** the crystal is a tree (then a planar graph); its topology is generated by the
  branching rule. A persistent-homology/topology signature would still be a function of the field.
- **Category theory:** the migration from "growth trajectory" to "parse tree" is a faithful functor
  (a re-labeling); it preserves, and creates, no information — the diagram commutes with the physical map.
- **Causal inference:** field = confounder; arms are colliders only if a channel exists; the do-operator test
  is the conditional-MI / shuffle-null protocol implemented here.
- **Machine learning:** a generative model will recover production rules **iff** they correspond to physical
  mechanisms; recovering a rule with no mechanism would be the (absent) novelty.

## 5. Competing hypotheses

- **H0 (null, conventional physics):** arms depend only on a shared field + independent local noise;
  `I(arm_i;arm_j|field)=0`. *Predicts:* confounded MI > 0, conditional MI = 0, compression gain beyond field
  = 0, manifold dim = #controls. **(All Demonstrated here.)**
- **H1 (representational):** snowflakes are usefully *described* by a CFG / PCFG / semantic manifold. *Predicts
  nothing new* — same distribution as H0; value is parsimony/visualization only. **(Demonstrated; not explanatory.)**
- **H2 (genuine channel — the real "language"):** branches share information beyond the field
  (`I(arm_i;arm_j|field) > 0`). *Predicts:* nonzero conditional MI surviving the within-field shuffle null;
  compression gain = that CMI. **(Detectable here when injected; Speculative for real snowflakes — no evidence.)**

## 6. Falsification protocols (executable)

1. **Conditional-MI channel test** (`snow_infotheory.channel_test`): estimate `I(X;Y)` and `I(X;Y|field)`;
   compare to a within-field shuffle null. *Falsifies the language hypothesis if `I(X;Y|field) ≈ null`.* Result
   on H0: ≈ null. On H2: ≫ null (so the test has power).
2. **Compression-gain test** (`compression_gain`): bits saved by a channel-aware model over a
   conditional-independence model = `I(X;Y|field)`. *Falsifies if gain ≈ 0.* Result on H0: ≈ 0.
3. **Manifold-dimension test** (`manifold_dimension`): effective dimension vs number of physical controls; a
   spurious parameter must add no dimension. *Falsifies a "semantic" reading if dim = #controls.*
4. **Orphan-symbol / MDL test** (`snow_grammar`): a symbol with no mechanism, or an MDL gain over the physical
   description, would be the novelty. *Result: none.*

## 7. Datasets required to run this on reality

- High-frame-rate, high-resolution *in-situ* growth video of single crystals under **measured** local
  (T, supersaturation) — e.g. a diffusion chamber (Libbrecht-style) with environmental telemetry, so the
  *field* is observed, not inferred. (Conditioning on the field is the whole point.)
- A large corpus of segmented crystals with per-arm branch-event sequences (to estimate arm–arm CMI).
- Isotopically controlled runs (H₂O vs D₂O) only to bound the molecular-quantum term (orthogonal to language).

## 8. Expected observations under each hypothesis (the decisive table)

| observable | H0 / H1 (physics) | H2 (true channel) |
|---|---|---|
| `I(arm_i; arm_j)` | **> 0** (shared field) | > 0 |
| `I(arm_i; arm_j | field)` | **≈ 0** | **> 0** |
| compression gain beyond field model | **≈ 0** | **= CMI > 0** |
| manifold dimension | **= #physical controls** | possibly higher |
| symbol with no mechanism | **none** | exists |

A single robust measurement of `I(arm_i;arm_j|field) > 0` (surviving the shuffle null and field
mis-specification checks) would move H2 from Speculative toward Supported. Absent that, H0 stands.

## 9. Conclusion, smallest defensible claim, minimal experiment

**Conclusion.** Conventional crystal-growth physics is sufficient. The "language" is a faithful
*representation* (a context-free re-encoding of a field-driven growth law plus branching recursion) that
produces **no new, testable prediction**. Symmetry is shared-cause, not communication. The semantic manifold is
the Nakaya control space. Compression recovers the physics, nothing more.

**Smallest claim that survives all attempted falsification (Demonstrated):** *snow-crystal growth histories are
exactly describable by a context-free grammar whose every production corresponds to a physical mechanism, and
whose description length does not beat the physical field encoding.* This is representational parsimony, not a
hidden language.

**The one claim that would make it a real language (Speculative / Currently unfalsifiable without the dataset):**
a measurable inter-branch channel, `I(branch_i ; branch_j | local field) > 0`.

**Minimal experiment to decide it:** grow single crystals in a diffusion chamber with *telemetered* local
(T, supersaturation); extract per-arm branch-event sequences; estimate `I(branch_i ; branch_j | field)` against
a within-field shuffle null and across deliberate field mis-specifications. **Standard physics predicts 0.** A
robust, mis-specification-stable positive value is the only thing that would distinguish a language-based
description from crystal-growth theory — and would be the smallest experiment capable of doing so.
