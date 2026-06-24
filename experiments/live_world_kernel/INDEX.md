<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# live_world_kernel — instrument index

The auditable-epistemology stack: small, self-testing, **observe-not-enforce** instruments that *earn* boundaries
rather than assert them. No scalar scores, no verdicts — every claim carries its own provenance. Narrative in
[`README.md`](README.md); the full ledger (maturity + verification strength) in
[`../../docs/EPISTEMIC_ACCOUNTING.md`](../../docs/EPISTEMIC_ACCOUNTING.md). All are single-process *logic* —
`declared ≠ verified`.

## Instruments

| File | Role | Maturity | Evidence |
|---|---|---|---|
| `live_world_kernel.py` | accept/reject/rewind edits to the world's own data state; three states (committed/irreversible/durable) | IMPLEMENTED | 16/16 |
| `frontier_probe.py` | where possibility becomes obligation (dependency frontier) | IMPLEMENTED | 7/7 |
| `concurrency_probe.py` | geometry proposes a partition, dependencies judge, convergence reveals | IMPLEMENTED | 7/7 |
| `klein_probe.py` | orientability — a local convention vs a false global claim | IMPLEMENTED | 7/7 |
| `topology_provenance_engine.py` | bundle the three probes as a vector (no scalar) | IMPLEMENTED | 7/7 |
| `module_graph.py` | turn a real source tree into a model; declare its blind spots | IMPLEMENTED | 7/7 |
| `fidelity_gap.py` | why an extraction came back blind; recoverable defect vs runtime frontier | IMPLEMENTED | 7/7 |
| `reality_status.py` | every boundary on one fact, each cell carrying its provenance | IMPLEMENTED | 7/7 |
| `repo_status.py` | provenance survives extraction by *downgrading* (never inheriting strength) | IMPLEMENTED | 7/7 |
| `reconcile_status.py` | disagreement → `CONTESTED`; strength only decreases on conflict | IMPLEMENTED | self-test present; exercised transitively by the two below |
| `runtime_witness.py` | earns evidence static can't (dynamic imports); orthogonal blind spots | IMPLEMENTED | 8/8 |
| `witness_panel.py` | one fact, many witnesses; partial order, no global winner | IMPLEMENTED | 7/7 |
| `discrimination_matrix.py` | rank experiments by uncertainty collapsed; `UNKNOWN` vs `UNDERCOMMITTED` gate; collapse-power | IMPLEMENTED | 12/12 |
| `claim_ledger.py` | reconcile statements about the kernel as claims with commitment levels; enforce *evidence ≤ maturity* | IMPLEMENTED | 6/6 |
| `self_improvement_witness.py` | prove the provable self-improvement *step* (guarded + self-modifying); mark where "recursive"/"proof" becomes inflation (`NON_ORIENTABLE`) | IMPLEMENTED | 7/7 |
| `recursion_witness.py` | the next rung — can the system improve its *ability to improve*? `d²/dt²` on held-out tasks, evaluator outside the loop. Result: **sustained, NOT recursive**; self-estimate diverges from reality | IMPLEMENTED | 7/7 |
| `limit_discriminator.py` | *why* the upper rungs fail — separates search (A) / task (B) / transfer (C) / evaluator (D), adds the TRANSFER rung. This run: **A refuted**, B/C/D supported. Self-tests check **validity**, not whether a hypothesis confirmed (`experiment-ran ≠ hypothesis-confirmed`) | IMPLEMENTED | 7/7 |
| `inflation_vs_search.py` | A↔D as a curve — inflation vs search strength K∈{1..32}. Finding: inflation **persistent (~+0.07) but not explosive**; flat across 31× budget (separator: `optimization-pressure ≠ search-budget`). Contests the endpoint coupling | IMPLEMENTED | 7/7 |
| `transfer_representation.py` | the transfer table — reset / raw_weights / support_set / basis_structure / learned_init × (acq cost, external, inflation). Win = lower cost AND higher external AND no worse inflation. Single-run winner is **regime-dependent** (3 of 5 mechanisms flip between noise regimes) — see `transfer_robustness` | IMPLEMENTED | 7/7 |
| `transfer_robustness.py` | replication gate — transfer table across a 3×3 noise×seed grid. Verdict **REGIME_DEPENDENT**: 6/9 regimes have *no* winner, all 3 wins cluster at one seed ⇒ **no robust transfer advantage** (apparent winners are sampling flukes). *A finding that doesn't replicate is not a finding* | IMPLEMENTED | 7/7 |
| `rsi_engine.py` | **the RSI engine (capstone)** — self-modify only through a reconciler gate: external gain ∧ replication (across seeds) ∧ calibration; naive proxy-runaway as control. Result: gated improves *reality* (ext +0.041, inflation **−0.090** = underconfident, safe) while naive self-deceives (proxy +0.072 but ext −0.024). Both promote **once in 60 rounds** ⇒ verified gains are rare: a single verified step, not a sequence. The gate invariant *is* the self-test | IMPLEMENTED | 7/7 |
| `no_inflation_latch.py` | **the hardware floor** — `evidence ≤ maturity` compiled to NAND gates feeding a flip-flop's load enable; an over-claim is a *forbidden state* (like SR `S=R=1`) the wiring won't latch. **Exhaustive proof** over all 16 (maturity,evidence) states: at the bottom of the stack as at the top, an over-claim is *unrepresentable*, not merely rejected | IMPLEMENTED | 7/7 |
| `verified_improvement_theorem.py` | **theorem + model, kept separate** — *classical theorem (true):* a Bienaymé–Galton–Watson process with offspring mean `m≤1` ⇒ a.s. extinction, `m>1` ⇒ survives w.p. `1−q`. *Modeling claim (not a theorem, empirical per domain):* verified self-improvement ≈ such a process with verified mean `m_verified`. *Conditional conclusion:* if so modeled, `m_verified` is critical. Contribution: `m_verified` as an operational scalar + the runaway `m̂>1≥m_verified`. MC-verifies the classical criterion; toy domain *consistent with* `m_verified<1` | IMPLEMENTED | 7/7 |
| `verified_branching_estimator.py` | **the domain estimator** — *estimates* `m_verified` (the theorem's empirical unknown): walks the verified-edit graph, counts each parent's neighbours that pass external∧replicated∧calibrated, reports `m_verified ≈ x ± SE`, a sub/near/super class, and `m(s)` shape (depletion / temporary-boom / critical / generativity-signal). Output is an *estimate under a regime*, never "has/lacks RSI" (enforced by a self-test) | IMPLEMENTED | 7/7 |

## The discipline these encode — the "green-check blindspot"

A green check certifies that code *executed*; it does **not** certify that a metric *means what its name claims*.
Compilers check syntax, test suites check behavior, neither checks **epistemic licensing** — whether a claim's
evidence strength is licensed by what was actually built and measured. That gap is where semantic inflation
hides: rhetoric (a name, a comment, a high-level assertion) borrows a strength the code never earned, and the
pipeline flashes green anyway. `claim_ledger.py` makes the rule executable: *evidence may not exceed maturity*,
and a claim that overstates its depth is rejected rather than trusted.

## Evidence it works — in this repository (`MEASURED`)

The strongest evidence is not borrowed; it is the slips this discipline caught *here, this session* — each one
structurally-sound code or a correct-looking derivation that was **mislabeled until interrogated**:

1. **`runtime_witness` over-counted coverage** — it counted `from x import f` *names* as modules, inflating the
   `requests` figures (240 edges / 118 "refinements"). The 8/8 self-test passed; *reading the output* caught it.
2. **`stopping_density` dipped** (`0.826 → 0.788`) — it computed "decreased at *exactly* step k" under a label
   claiming the Terras *stopping-time* density. The dip was the only symptom; fixed to the monotone `≤ k` quantity.
3. **`no_break_overclaim` check** looked for the substring `"reduced-round"` (hyphen) against an underscore
   regime string — a *correct* result tripped a *wrong* check, caught by a **loud assertion failure**.
4. **carry-degree off-by-one** — a derivation handed over "accepted without qualification" summarized
   `deg(C_{i+1}) = i+1`; recomputing the ANF showed `i+2` (its own examples `2,3,4` proved it).

The pattern: the errors were never in the grand structure — they were in a *label, a count, a check's own string,
an exponent*, the small quotable summaries that ride on correct work and don't get re-derived. `tested ≠
correct-label`; comb the output, not just the check.

## The failure class it speaks to (`DECLARED` analogy — *not* a solved problem)

The same *class* of failure — a correctly-executing system whose data or flags silently stopped meaning what the
code assumed — has caused real disasters:

- **Boeing Starliner OFT (Dec 2019).** The capsule pulled its Mission Elapsed Timer from the Atlas V booster but
  grabbed the value ~11 hours early/with the wrong coefficient; the software ran fine, but the clock value no
  longer *meant* mission time, so the burns fired wrong and it missed its orbit. [MIT Tech Review](https://www.technologyreview.com/2019/12/20/131454/boeings-starliner-wont-make-it-to-the-iss-now-after-its-internal-clock-went-wrong/) · [Boeing OFT (Wikipedia)](https://en.wikipedia.org/wiki/Boeing_Orbital_Flight_Test)
- **Knight Capital (Aug 2012).** A deploy reached 7 of 8 servers; the 8th still held dead "Power Peg" test code
  bound to a config flag that had been *repurposed* years earlier — the flag's meaning had silently warped. ~$440M
  lost in ~45 minutes. [Knight Capital (Wikipedia)](https://en.wikipedia.org/wiki/Knight_Capital_Group) · [case study](https://www.henricodolfing.ch/en/case-study-4-the-440-million-software-error-at-knight-capital/)

These illustrate *the class of problem the discipline addresses in principle*. They are **not** problems these
instruments solved: nothing here was run against flight software or a trading system; there is no integration,
no deployment, no measurement on a real high-stakes system. The link is `DECLARED` (analogy), not
`MEASURED_BY_INTERVENTION`.

## Dogfood — `claim_ledger` applied to this folder

To state the folder's own claims honestly, in its own format:

```
claim "the instruments behave as specified"        maturity=IMPLEMENTED  evidence=MEASURED   (N/N self-tests + the 4 caught slips above)
claim "this prevents real-world catastrophic        maturity=ABSENT       evidence=DECLARED   (analogy; no integration/deployment/measurement)
       failures (aerospace, finance, autonomy)"
```

By the ledger's own rule, asserting that second claim at `MEASURED` ("solves catastrophic failures never solved
before") is an **`INFLATION_ERROR`** — the exact semantic inflation this stack exists to reject, turned on
itself. So this index records it as `DECLARED`. The instruments *demonstrate* the discipline on small,
verified systems; they do not *deploy* it against the world's hard problems, and saying otherwise would fail the
check `claim_ledger.py` enforces.

## See also

[`SELF_MODIFICATION_BOUNDARY`](../../docs/SELF_MODIFICATION_BOUNDARY.md) · [`AUTHORITY_ARBITRAGE_BOUNDARY`](../../docs/AUTHORITY_ARBITRAGE_BOUNDARY.md) ·
[`ADJUDICATION_THROUGHPUT_BOUNDARY`](../../docs/ADJUDICATION_THROUGHPUT_BOUNDARY.md) · [`FAILURE_MODE_MATRIX`](../../docs/FAILURE_MODE_MATRIX.md) ·
[`EPISTEMIC_ACCOUNTING`](../../docs/EPISTEMIC_ACCOUNTING.md) — the boundary contracts (paper) and the capstone ledger.
