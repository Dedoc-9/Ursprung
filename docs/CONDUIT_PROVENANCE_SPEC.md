<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Conduit — tuple-level data provenance via semirings (spec note)

**Status: design specification — SCOPED / UNDERCOMMITTED. Nothing here is built.** This is an exploratory spec
for a *separate* product (data-lineage / compliance), recorded with the same discipline as the rest of `docs/`:
prior art first, the genuine niche named narrowly, the static/runtime boundary drawn honestly, and the one open
problem stated as open. The mathematics is **established** (Green–Karvounarakis–Tannen, 2007) and has **working
implementations** (GProM, Perm); Conduit's novelty is *not* the semiring propagation. `claim ≠ code`;
`described ≠ built`; `integrity ≠ truth`.

> **Why this one, of the candidates considered.** Consequence-matching: a wrong or missing provenance annotation
> is an **auditable, recoverable, measurable** compliance gap — not a silent privacy breach (the DP-mechanism
> route) and not a kinetic failure (the unmanned-systems route). The risk here is *performance/scale*, which you
> can see fail; not *silent incorrectness*, which you can't. That is the honest reason to pick it.

---

## 1. Prior art — the theory is settled and partly implemented

### 1a. The theorem
**Green, Karvounarakis & Tannen, "Provenance Semirings," PODS 2007.** Provenance for the **positive relational
algebra** (select, project, join, union — "SPJU") propagates over a commutative semiring `(K, +, ×, 0, 1)`:
**join → ×** (provenance combines), **union / projection → +** (provenance alternatives merge), selection keeps
or zeroes a tuple. Annotate each input tuple with a token from `K`; the provenance of any output tuple is the
semiring expression you get by propagating tokens through the query plan — **compositional, deterministic,
complete** for positive RA. The *same* propagation, instantiated at different semirings, yields different
provenance at different cost (see §2).

**Honest scope of the theorem.** It is clean for **positive** RA. Relational **difference / negation** needs
semirings with monus (m-semirings); **aggregation** needs a separate extension (Amsterdamer–Deutch–Tannen,
"Provenance for Aggregate Queries," PODS 2011). "Every relational operation propagates by semiring arithmetic"
is therefore *almost* right — true for SPJU, an active research frontier for difference and aggregation. Conduit
must state which fragment it covers.

### 1b. The implementations (this is the part the earlier pitch understated)
- **Perm** (Glavic & Alonso, ICDE 2009): computes provenance via **query rewriting** on a stock RDBMS.
- **GProM** (Arab, Glavic et al., TaPP 2014; "Swiss Army Knife," IEEE Data Eng. Bull. 2018): a **DB-independent
  provenance middleware** that rewrites queries over an algebra-graph model, implements **how- / why- / why-not-
  provenance**, and runs on existing engines (Postgres, Oracle). Semiring how-provenance is *already shipped here.*

So semiring provenance is **not unbuilt**. Conduit may not claim to invent it.

### 1c. The commercial lineage tools (what they do and don't do)
**OpenLineage / Marquez, Collibra, Alation, dbt, Spark lineage** track **operational lineage** — *which job ran
which transformation, table- and column-level*. They do **not** propagate **tuple-level** semiring provenance
(*which input rows produced this output row, combined how*). They catalog pipelines; they don't carry
annotations through query semantics.

| Layer | Granularity | Carries semiring how-provenance? | Examples |
|---|---|---|---|
| Operational lineage | job / table / column | no | OpenLineage, Collibra, Alation, dbt |
| Tuple-level provenance, SQL-over-DBMS | row, positive RA | **yes** | GProM, Perm |
| **Tuple-level provenance, dataframe/UDF pipelines** | row, across Spark/pandas/UDFs | **no existing product** | ← Conduit's niche |

---

## 2. The genuine sliver

Not "semiring propagation" (Green–Tannen + GProM own it). Conduit's three honest claims:

1. **Dataframe / pipeline target, not SQL-over-a-DBMS.** GProM/Perm rewrite SQL against a relational engine.
   Modern data work is **Spark / pandas / dbt** pipelines mixing declarative ops with arbitrary user code.
   Carrying tuple-level semiring provenance through *that* substrate is not served.
2. **Compliance framing as the product.** GDPR Art. 15 (right of access — *where did this datum come from?*),
   Art. 17 (erasure — *what derived from this person's record and must also be deleted?*), Art. 25 (data
   protection by design); CCPA right-to-know / deletion. Tuple-level provenance answers these *mechanically*;
   today compliance teams reconstruct lineage by hand from catalogs and interviews — incomplete and unverifiable.
3. **The UDF boundary, handled honestly** (§3) — the thing the academic systems sidestep by staying in SQL.

`niche ≠ invention`: the contribution is productization + the dataframe/UDF substrate + compaction (§4), on top
of a settled theorem.

---

## 3. The static / runtime boundary (the load-bearing honesty)

Conduit's pipeline splits into two regimes, and the guarantee differs across them:

- **Declarative / relational operators (map / filter / join / groupBy / union on typed columns) — STATIC.**
  These lower to positive RA, so the semiring propagation rule is known at plan time and can be **type-checked**
  on the query plan (a `ProvenanceRing` trait, §5). This is the part where "provenance is complete by
  construction" honestly holds.
- **Arbitrary UDFs (a Python/Scala lambda, a black-box `.apply(f)`) — RUNTIME or OPAQUE.** Tracking provenance
  through Turing-complete user code is the general information-flow problem — **undecidable**, exactly the
  `proves-the-procedure ≠ proves-the-phenomenon` wall. Conduit must not pretend otherwise. Two honest options
  per UDF: **(a) runtime instrumentation** (taint-wrap the inputs, observe which contributed — sound only for
  the observed execution, `runtime-trace ≠ all-inputs`), or **(b) declare the UDF an opaque provenance barrier**
  (record "rows X..Y entered this UDF; output attributed to all of them" — an over-approximation, flagged as
  such — mirroring this repo's `non-liftable` declaration). `relational ≠ Turing-complete`.

The defensible claim: *"≈90% of real transformations are relational and get complete, statically-checked
provenance; UDFs are runtime-instrumented or declared opaque, never silently dropped."* Not *"we solve
information flow through arbitrary code."* That second claim is **REJECTED AS PROOF**.

---

## 4. The open problem (stated as open): provenance-polynomial blowup

The free semiring `ℕ[X]` (full how-provenance) gives complete audit trails — but nested joins produce **products
of provenance terms**, so the polynomial can grow **exponentially** in query depth. This is the real engineering
frontier, and it is the reason this is a *hard* project rather than a weekend one.

Compaction strategies, each with a **stated guarantee-loss** (an instrument must report its blind spot):

- **Semiring homomorphism to a cheaper backend** — project the free polynomial down to Boolean ("which sources?")
  or bag-`ℕ` ("how many times?") when the full expression isn't needed. `cheaper-semiring ≠ full-how-provenance`.
- **Factorized / circuit representations** — provenance *circuits* (Deutch–Milo–Roy–Tannen, ICDT 2014) share
  subterms instead of expanding them; polynomial size becomes circuit size. The most promising lead.
- **Truncation / fingerprinting / sampling** — bound size by dropping or hashing terms; a bounded answer, not
  the complete one. `compacted ≠ complete`.

Crucially this risk is **measurable** (provenance size vs completeness, a Pareto curve) — not a soundness
landmine. A too-large polynomial *slows down or is approximated*; it does not silently mis-attribute. That is the
consequence-match that makes Conduit the right pick.

---

## 5. Architecture & build path

```
┌──────────────────────────────────────────────┐
│  Analyst (Python) — standard dataframe / SQL   │
│  provenance is transparent; no API change      │
├──────────────────────────────────────────────┤
│  Plan rewriter (Rust) — parse → algebra graph; │
│  insert a provenance-propagation node at each  │
│  RELATIONAL operator; mark each UDF a barrier   │
├──────────────────────────────────────────────┤
│  Provenance runtime (Rust)                     │
│    trait ProvenanceRing { zero; one;           │
│        add(&self,&Self)->Self;  // union/proj   │
│        mul(&self,&Self)->Self } // join         │
│    • tuple-level tokens; #[must_use] (no drop)  │
│    • pluggable backend = cost/completeness:     │
│      Boolean | bag-ℕ | free-poly | circuit      │
│    • UDF: runtime taint-wrap OR opaque barrier  │
├──────────────────────────────────────────────┤
│  Storage — provenance-annotated rows + circuit │
│  store; compaction policy per §4               │
└──────────────────────────────────────────────┘
```

**Build path (honest order — compose, don't reinvent):**

1. **Don't reimplement the relational provenance core blind — study GProM/Perm first** and decide
   interop-vs-reimplement (their rewrite rules are the reference; `quantity ≠ coherence`).
2. **Smallest real artifact:** a Rust `ProvenanceRing` trait + the four standard backends (Boolean / bag-`ℕ` /
   free-poly / circuit), with a **differential test** that the four agree where they must (homomorphisms commute
   with propagation) — the `to_bits`/decision-parity discipline, applied to provenance.
3. **One declarative operator set** (map/filter/join/groupBy/union) over a typed plan; provenance propagation
   type-checked at the plan layer. Defer aggregation/difference (the semiring-extension frontier, §1a).
4. **The UDF boundary** (§3): ship taint-wrapping for the common cases + the opaque-barrier declaration for the
   rest. Declare blind spots; never drop a token silently.
5. **Compaction** (§4) as the headline research deliverable: implement circuits, measure the size/completeness
   Pareto curve on real pipelines, grade it `MEASURED` only after running. Until then: `UNMEASURED`.

---

## 6. Honest status ledger

| Component | Status | Note |
|---|---|---|
| Semiring propagation over positive RA | **ESTABLISHED + IMPLEMENTED** | Green–Tannen (2007); GProM, Perm — *not* Conduit's novelty |
| Tuple-level provenance through dataframe/UDF pipelines | **SCOPED** | the genuine niche; UDF boundary is the hard part (§3) |
| Compliance product (GDPR 15/17/25, CCPA) framing | **SCOPED** | real driver; commercial tools do operational, not tuple-level provenance |
| Polynomial compaction at industrial scale | **OPEN (research frontier)** | circuits are the lead; size/completeness is a measurable Pareto, not a soundness risk |
| Provenance through arbitrary UDFs, statically | **REJECTED AS PROOF** | undecidable; `relational ≠ Turing-complete` |
| "Provenance correctness ⇒ data correctness" | **REJECTED** | provenance tracks *origin*, not *truth*; `lineage ≠ validity` |

**Defensible one-line:** *tuple-level semiring provenance carried through dataframe pipelines — statically
complete for relational operators, runtime-instrumented or explicitly-opaque through UDFs — productized for
GDPR/CCPA traceability, with provenance-circuit compaction as the stated open problem.*

---

Sources: Green, Karvounarakis & Tannen, "Provenance Semirings," **PODS 2007** · Glavic & Alonso, "Perm," **ICDE
2009** · [GProM — generic provenance middleware (TaPP 2014)](https://www.usenix.org/system/files/conference/tapp2014/tapp14_paper_arab.pdf) ·
[GProM — "Swiss Army Knife" (IEEE Data Eng. Bull. 2018)](http://sites.computer.org/debull/A18mar/p51.pdf) ·
[Provenance in Databases: Why, How, and Where (survey)](https://www.academia.edu/19708582/Provenance_in_Databases_Why_How_and_Where) ·
Deutch, Milo, Roy & Tannen, "Circuits for Datalog Provenance," **ICDT 2014** · Amsterdamer, Deutch & Tannen,
"Provenance for Aggregate Queries," **PODS 2011** · OpenLineage / Marquez, Collibra, Alation (operational lineage).
