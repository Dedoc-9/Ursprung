<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Tool-value ledger — what is usable now, and at what maturity

The repo's own discipline turned on the question *"which parts have real tool value, and how much evidence
backs each?"* Graded by the two axes the stack uses everywhere: **maturity** (`BUILT` / `CONTRACT` / `ABSENT`)
× **evidence** (`MEASURED` / `DECLARED` / inspected), plus a plain **tool-value** call
(*usable-now* / *reference-pattern* / *frontier*).

> **Provenance of THIS ledger (declared, per the no-inflation rule).** It is a **static inspection** — a file/doc
> read, not a re-execution (the sandbox was unavailable, so nothing here was re-run this pass). By the stack's own
> rule that extraction *downgrades* strength (`repo_status`: a model of evidence is weaker than the evidence), the
> verification notes below are **inspected/`DECLARED`-to-this-audit**, not freshly `MEASURED`. Where an artifact
> independently corroborates a run (a compiled `target/` tree, committed test files), that is noted as stronger
> than a bare prose claim. Re-running the suites would upgrade these cells; until then, read them as a map, not a
> certificate. `declared ≠ verified` — including here.

## Tier 1 — usable now (highest evidence)

| Component | What it is / transplantable value | Maturity | Evidence (inspected) |
|---|---|---|---|
| `experiments/bench_gpu_real/` (Rust + Vulkan) | **The crown jewel.** A fair performance-comparison harness: equal *measured* GPU-tick budget (over-spenders refused), **sealed observer** (a policy can't read the ruler it's scored on), **ε-dominance** (difference must exceed the measured reproducibility floor), Pareto-vector error never a summed score. Transplants to any "policy A vs B" perf question. | BUILT | **`MEASURED` on real silicon** (ASUS ROG Ally X, RDNA 3.5, Vulkan): M1–M6c spatial + M6d/T1–T4 temporal. Corroborated in-repo by a compiled `target/` tree; verdicts consolidated in [`BOUNDARY_MAP.md`](BOUNDARY_MAP.md). |
| `experiments/reality_kernel/` + `core_rs/` (Rust) + `lineage_scale/` | Domain-agnostic **event-sourced provenance kernel**: Artifact / Event / CommitReceipt / Query; *absence is queryable* (`present/absent/unresolved/unaccounted`); every transition emits a receipt (record, never authorization). Usable as the spine of an editor, sim, or collaborative tool that must answer *why is the state this, who introduced it, what's missing*. | BUILT | Rust core with committed tests (`tests/differential.rs`, `tests/adversarial.rs`); README claims `cargo test` 10/10 under concurrency — **not re-run this audit**. |
| `experiments/live_world_kernel/` (the auditable-epistemology stack) | An **audit discipline + red-team phase-1 recon** tool, and the **RSI measurement framework** (capability / branching / generativity / orbit + the accounting layer). Plus the reflexive `claim_ledger` and the `no_inflation_latch`. | BUILT | Per-instrument self-tests (16/16, 7/7, 8/8, …) **run on the user's machine this session**, ledgered in [`EPISTEMIC_ACCOUNTING.md`](EPISTEMIC_ACCOUNTING.md) — not re-run by this static audit. The ledger *leads with its own recorded ghosts* (e.g. `runtime_witness` coverage over-count). |
| `research/` SHA-256 + Collatz instruments | **External-math auditors** that grade a claim and refuse to over-state: avalanche (no gradient), 2-adic carry survival (`BOUNDED_TO_REDUCED_ROUNDS`), Chapman–Kolmogorov mixing, exact carry ANF/degree. Transplantable pattern for "stress a structural claim, report the boundary." | BUILT | stdlib self-tests **run on the user's machine this session** (4/4, 6/6, 7/7), `PYTHONHASHSEED=0`; not re-run by this audit. |

## Tier 2 — reference-pattern (real code, validated *in its own envelope*; re-verify before relying)

| Component | Transplantable value | Maturity | Evidence (inspected) |
|---|---|---|---|
| `ursprung/` renderer core (`world_core`, `view_layer`, `raster`, `verify`, `registry`, `loop.py`, the **CORE/VIEW/ALLOCATOR/OBSERVER** layer law + cardinal invariant) | A **reference rasterizer + the layering discipline** (rendering may interpolate/approximate but never mutate committed state). The discipline transplants; the rasterizer is a reference, not a production engine. | BUILT | part of the **502-check stdlib suite** (single-process Python); not re-run this audit. |
| `ursprung/` information-firewall families (`causal_access`, `reconstruction`, `side_channel`, `accumulation`, `adversarial_dynamics`, `representation_privacy`, `execution_surface`, `convergence`, `reality_harness`, `behavioral_harness`, `adversary_*`, `channel_discovery`, `disclosure`, `perception/`) | **Transplantable, re-validatable references** for anti-cheat / multiplayer disclosure and side-channel neutralization (timing / reaction / absence / hysteresis / execution-cost / rollback). Patterns you re-verify in your context — **not** deployed security products. | BUILT | constructed-world self-tests, single-process; `reality_harness.NetworkChannel` etc. are intentionally-unbuilt seams. |
| `experiments/latent_phase1–6/` (the latent causal benchmark) | The **5-tier gate** (reconstruction → intervention → topology → model-robustness → gauge) — a real *procedure* for telling a generator from a confounder. The procedure transfers even where its toy numbers don't. | BUILT | self-tests on synthetic worlds with ground-truth `do()`; toy numbers explicitly non-transferable. |
| `experiments/live_latent_provenance/` + `provenance_runtime/` + `adversarial_runtime/` + `reality_authoring/` | "**Compression can't silently sever lineage**" guarantee (severance is caught, never silent) + a provenance/adversarial runtime pair. Transplantable to telemetry / model-artifact stores / event logs. | BUILT | self-tests; single-process. |

## Tier 3 — frontier / `ABSENT` (named, intentionally not faked)

The README and `BOUNDARY_MAP.md` already mark these honestly; they are **not** assets to rely on:
a production renderer; concurrency at **10⁶–10⁸** lineage scale; a real **estimator under intervention scarcity**
(unknown graph — IV / invariance / counterfactual); a real **external anchor** (verifiable delay function /
proof-of-sequential-work); the four boundary **contracts** (`SELF_MODIFICATION` / `AUTHORITY_ARBITRAGE` /
`ADJUDICATION_THROUGHPUT` / `FAILURE_MODE_MATRIX`) are **paper, not code**; a replay witness for the repo domain;
the "fidelity operating system" (direction, not built). The RSI/energy claims are `SCOPED` per their own benches.

## The honest one-paragraph answer

The repo is a **specification + reference implementation + measurement discipline** (its own framing), not a
turnkey product. Real tool value concentrates in three places: **metrology** (`bench_gpu_real` is the standout —
`MEASURED` on hardware, and the one piece most directly liftable into other projects), a **provenance kernel**
(`reality_kernel`/Rust core), and **transplantable reference patterns + the discipline itself** (the firewall and
causal families, the audit stack, the separators). What it is *not*: a shippable renderer, a deployed security
product, or an autonomous discovery/RSI engine. The strongest single asset is the **fair-comparison apparatus**,
because its credibility was earned by moving the project's own hypothesis *both* directions on the same sealed
ruler — the rarest property a benchmark can have.

*This ledger is itself a `repo_status`-class extraction. To upgrade any cell from inspected to `MEASURED`, re-run
its suite (`cargo test` for the Rust core; `PYTHONHASHSEED=0 python …` for the Python instruments; the GPU bench
on the Ally X) and record the result.*
