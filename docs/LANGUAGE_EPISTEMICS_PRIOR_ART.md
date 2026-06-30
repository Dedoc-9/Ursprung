<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Language epistemics: prior art, the real niche, and the ceiling

**Status: research note + design specification — SCOPED / UNDERCOMMITTED. Nothing here is built.** This maps an
adjacent frontier honestly *before* any code, so the project cannot ship a novelty claim the field would reject.
The engine the spec would expose (claim → graded evidence binding over a manifest + build receipt) **already
exists** as Layer 4 (`commercial_obligations.rs` / `commercial_obligations.py` / `claim_ledger.py`); the
*language-level linter pass* described in §3 is **not built**. `engine-exists ≠ language-extension-shipped`;
`described ≠ built`; `claim ≠ code`.

> **The phrase "world's first Compiler-Enforced Honesty Stack" is struck.** It does not survive this repo's own
> HYPE gate, and §1 shows why: design-by-contract and verification are a mature, institutionalized field, and
> evidence-backed claim structures are old in safety engineering. What is narrow-but-real is documented in §2.

---

## 1. Prior-art matrix — the room is crowded (and the Rust team is in it now)

Two distinct bodies of prior art bound the novelty claim. Treat both as ESTABLISHED; do not reinvent either.

### 1a. Programming-language contracts & verification (asserts a *property of a value/state*)

| Tool / effort | Mechanism | What it asserts |
|---|---|---|
| **Eiffel** (Meyer, 1986) | `require` / `ensure` / `invariant` | the original design-by-contract: pre/post/invariants |
| **Rust `contracts` crate** | proc-macro `#[requires]` / `#[ensures]` / `#[invariant]` | runtime-checked value contracts |
| **Rust MCP-759 + `std-contracts` (2025)** | **official** `#[contracts::requires/ensures]` experimental attrs + type invariants | language-level contracts; ~200 std fns annotated in `verify-rust-std` |
| **Flux** | refinement/liquid types as a compiler plug-in | value refinements (`i32{v: v > 0}`) inferred via liquid typing |
| **Prusti / Creusot / Kani / Thrust** (Thrust = PLDI 2025) | deductive verification / model checking / refinement | the code provably meets a value/behavioral spec |
| **icontract / deal / dpcontracts** (Python) | call-time decorators | runtime pre/post/invariants |
| **CrossHair / SpecPylot** (Python) | symbolic execution / LLM spec-gen + refinement | whether contracts are *consistent with* the code |

The mechanisms the aspirational syntax reaches for — proc-macro attributes carrying conditions, call-time
decorators — are exactly these. A generic invariant/value checker would reinvent a standardized wheel.

### 1b. Evidence-backed claim structures (asserts the *justification of a claim*)

The *idea* of "a claim backed by graded evidence, with stated limits" is **not new outside PL** either:

- **Assurance cases — GSN (Goal Structuring Notation) / CAE (Claims–Arguments–Evidence)**: safety engineering's
  decades-old discipline of binding a claim to its supporting evidence and assumptions.
- **W3C PROV / provenance systems**: standardized records of *how* an artifact came to be.
- **ML model cards / datasheets**: structured disclosure of a model's intended use and limitations.

So the honest novelty is **not** "evidence-backed claims" (old) and **not** "language contracts" (old). It is the
*intersection*: §2.

---

## 2. The real niche — Epistemic Provenance Contracts (claim-evidence binding *as a toolchain contract*)

Every framework in §1a asserts a **property of a value**. The assurance disciplines in §1b assert claim
justification but live in *documents and review boards*, not in the compiler. Ursprung's Layer 4 occupies the
narrow intersection neither covers: **a claim-justification contract enforced by the build toolchain, that fails
the build when an assertion outruns its evidence.**

| | Value contracts (§1a) | **Epistemic provenance contracts (this niche)** |
|---|---|---|
| **Invariant** | state correctness, e.g. `x.len() > 0` | `evidence_grade ≤ maturity` AND the backing test PASSED this build |
| **Target defect** | runtime edge-case bugs, memory/logic faults | **unbacked-claim drift & semantic inflation** (human- or AI-authored) |
| **Failure mode** | panic / failed symbolic proof on a value | **build/commit rejected** when a claim strips its `does_not_show` or lacks a fresh passing receipt |
| **Plane** | the *value* flowing through the program | the *assertion a person/LLM makes about the program* |

This is **orthogonal to and composes with** §1a — it is not a competitor to Flux or `#[contracts::requires]`. A
function can carry *both* a value contract (its inputs are finite) *and* a provenance contract (the safety claim
in its doc rests on a discharged, currently-passing obligation). To my knowledge no mainstream PL contract tool
binds *grade + does_not_show + rests-on-a-discharged-test + receipt-freshness* as a first-class, build-failing
contract. That is the sliver this repo can honestly own — as a **methodology layer**, graded SCOPED.

---

## 3. Specification — the `GatedClaim` provenance-contract layer (aspirational; not built)

A thin layer *on top of* the existing contract ecosystem. The example syntax is illustrative only.

```rust
// ASPIRATIONAL — illustrates the provenance contract; composes with §1a value contracts, does not replace them.
#[derive(GatedClaim)]
#[claim_id("L2_CONTRACTION_BOUND")]
#[grade(Bounded)]                                  // a point on the ladder; evidence may not exceed it
#[rests_on("test_discrete_certificate")]           // must name a real, currently-PASSING obligation
#[does_not_show("global non-linear asymptotic stability outside σ_max")]
#[falsifier("sampled_trajectory_growth_exceeds_rho")]
pub fn execute_matrix_step(kappa: [[f64; 4]; 4]) {
    #[contracts::requires(kappa.iter().flatten().all(|x| x.is_finite()))]  // §1a value contract, unchanged
    let _result = evaluate_contraction(kappa);
}
```

**The linter verification routine (what a `cargo`/pre-commit pass would mechanically do):**

1. Extract `claim_id`, `grade`, `rests_on`, `does_not_show`, `falsifier` from the attribute.
2. Parse the single-source manifest (`ledger.tsv` + `obligations.tsv`) and verify cross-reference alignment:
   `claim_id` exists, `rests_on` names a registered obligation, `grade` is `≤` what that obligation's status
   licenses (the no-inflation rule), and `does_not_show` + `falsifier` are present and non-empty.
3. Open the build-local `.verify_receipt.tsv`. If the token for `test_discrete_certificate` is **missing,
   stale, or `FAIL`**, emit a compile-time / pre-commit error and **block** (`exit 1`).

The Python analogue is a `@gated_claim(...)` decorator running the same manifest + receipt check at import/call
time — exactly the `icontract`/`deal` decorator shape (§1a), carrying the provenance fields (§2) instead of a
value predicate. **Reuse, don't reinvent:** the value-predicate half should defer to the `contracts` crate /
`icontract`; this layer adds only the provenance half.

---

## 4. The ceiling — what this layer can and cannot guarantee (the load-bearing section)

A macro or decorator is a **syntactic/structural** check. It can enforce the *form* of a claim; it cannot
evaluate the *truth* of the prose inside it.

- **`form ≠ truth`.** The linter verifies that `#[does_not_show("…")]` is present, that `rests_on` names a real
  obligation, and that the obligation PASSED this build. It does **not** — and cannot — verify that the
  `does_not_show` string is mathematically true or complete. `#[does_not_show("global stability")]` is an opaque
  string to the compiler.
- **`present ≠ correct`.** It catches exactly one drift mode: a claim asserted **without a discharged backing**
  (over-claim, stripped limitation, stale/failed receipt, off-ladder grade). It does **not** catch a *wrong but
  well-formed* claim whose named test passes for the wrong reason.
- **`static-check ≠ live-execution` / `receipt ≠ proof`.** A green receipt attests the suite ran and passed this
  build — not that the suite is complete, correct, or omniscient. This is the same ceiling Layer 4 already lives
  under; the language layer inherits it unchanged.
- **`grounded ≠ true`.** A `Grounded<T>` token is only as strong as its proof oracle; it is a known
  pattern (typestate / sealed-constructor witness), not a new soundness result.

**Consequence matching (why this application is sound where the drone sidecar was not).** A failure of this
linter produces a **broken build or a rejected commit** — never a kinetic actuation failure. The strength of the
guarantee (structural, sufficient, form-only) is matched to a low-consequence error surface. That is the rule the
unmanned-systems framing violated and this one satisfies. `measured ≠ guaranteed`; `integrity ≠ truth`.

---

## 5. Honest status ledger

| Component | Status | Note |
|---|---|---|
| Claim→graded-evidence engine (manifest + live receipt) | **IMPLEMENTED / MEASURED** | Layer 4: `commercial_obligations.{rs,py}`, `claim_ledger.py`, `ledger.tsv`/`obligations.tsv`/`.verify_receipt.tsv`; tested (`commercial_gate.rs`, `verify.py` LIVE gate) |
| `GatedClaim` proc-macro + linter pass (Rust) | **SCOPED / UNDERCOMMITTED** | spec in §3; not written; would depend on `syn`/`proc-macro2` (a dependency — breaks the crate's zero-dep posture; a separate tool crate, not `ursprung` itself) |
| `@gated_claim` decorator (Python) | **SCOPED** | thin wrapper over the existing `claim_ledger` + receipt loader; the most reachable first step |
| "Verifies documentation matches code" | **REJECTED AS PROOF** | the ceiling (§4) forbids this claim; `form ≠ truth` |

**Defensible one-line:** *a claim-provenance contract layer that composes with established value-contracts
(`#[contracts::requires]`, `icontract`) and fails the build when an assertion's grade, limitations, or backing
test are missing, stale, or off-ladder — catching unbacked-claim drift, not certifying truth.*

A noted dependency tension to decide before building: a real Rust proc-macro needs `syn`/`proc-macro2`, which
breaks `ursprung`'s zero-dependency posture. The honest resolution is a **separate companion tool-crate** that
depends on those, leaving the audited core untouched — not vendoring proc-macro machinery into `ursprung`.

---

Sources: [Rust `contracts` crate](https://crates.io/crates/contracts) ·
[MCP-759 contract attributes](https://github.com/rust-lang/compiler-team/issues/759) ·
[std-contracts project goal](https://rust-lang.github.io/rust-project-goals/2025h1/std-contracts.html) ·
[Contracts & Automated Reasoning for Rust (lang-team #181)](https://github.com/rust-lang/lang-team/issues/181) ·
[Flux / Prusti / Creusot / Kani — awesome-rust-formalized-reasoning](https://github.com/newca12/awesome-rust-formalized-reasoning) ·
[Thrust, PLDI 2025](https://www.riec.tohoku.ac.jp/~unno/papers/pldi2025.pdf) ·
[icontract](https://github.com/Parquery/icontract) · [CrossHair](https://crosshair.readthedocs.io/en/latest/kinds_of_contracts.html) ·
[SpecPylot](https://arxiv.org/html/2604.16560v1)
