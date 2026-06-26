<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# weltwerk/verify — a verification kernel with interchangeable proof engines

This began as the first NASA-merge subsystem: an **explicit-state bounded model checker** *inspired by
techniques used in systems such as NASA's Java Pathfinder, adapted to `WorldSim`'s causal transition
system* (an inspiration, not an equivalence — no JPF source, no feature-parity claim; JPF checks Java
bytecode, this checks an authored causal world). It is now more than that: a **verification kernel** in
which the result *contract* is the architectural boundary and multiple engines plug in behind it.

> The line the project crossed (Phase A.2): from *"Weltwerk has a model checker"* to *"Weltwerk has a
> verification kernel with interchangeable proof engines producing auditable artifacts."* Symbolic BMC is
> one engine; abstract interpretation will be another; diagnosis/counterfactuals/repair consume the
> artifacts. `engine ≠ semantics`.

License + provenance: original AGPL-3.0 code, recorded in
[`../../docs/LICENSE_DECISIONS.md`](../../docs/LICENSE_DECISIONS.md) and
[`../../docs/PROVENANCE.md`](../../docs/PROVENANCE.md). Architecture contract: [`DESIGN.md`](DESIGN.md).

## Architecture

```
                         WorldModel
                             |
                             v
                     TransitionRelation        ← the proven semantics boundary (T(s,a,s'))
                             |
              +--------------+---------------+
              |                              |
              v                              v
     ExplicitStateBFSEngine          SymbolicBMCEngine (optional z3)
              |                              |
              +--------------+---------------+
                             |
                             v
                     VerificationResult        ← the only thing consumers depend on
                             |
            +----------------+-----------------+
            |                |                 |
          Trace        Certificate        Violations
            |
            v
   Diagnosis · Counterfactuals · Repair · Visualization (consumers)
```

The solver lives only inside `solver_adapter.py`. **The solver is an engine dependency, not an architecture
dependency** — nothing else in Weltwerk imports z3, and the core stays pure-stdlib.

### Vocabulary (kept precise, theme preserved)

- **ghost** — a *state* that violates an invariant.
- **ghost trace** — the *shortest, replayable* event sequence that reaches a ghost (the counterexample).
- **ghost report** — `diagnose`'s ranked *explanation* of a ghost trace (hypotheses + next observation).

## The idea, in Weltwerk's own terms

| Model checking | Weltwerk |
|---|---|
| all action sequences up to the depth bound | **Potential** — the combinatorial space `Potential(action sequences)` |
| the reachable states *induced by* those sequences | **Actual** — `Reachable(actual)`, what the world can actually become |
| a reachable state that violates an invariant | a **ghost** (with its shortest, replayable **ghost trace**) |
| exhaustive (frontier emptied) search | a **proof** of the invariants over the reachable state graph |

An engine does **not** enumerate `Potential` itself (it never visits impossible states): it explores
`Reachable(actual)` *inside* `Potential(action sequences)`. So `Actual ⊆ Potential` is both the law checked
on every transition (`actual ⊆ potential`) and the shape of the search — the reachable set is almost always
far smaller than the combinatorial bound, the project's sparsity thesis showing up in verification.

## Files

**Contract & semantics**

| File | Role | Grade |
|---|---|---|
| `interfaces.py` | the stable contract: frozen `ReachabilityResult` / `VerificationResult` (status, witness, trace, certificate, explored/frontier, engine, violations) + `verify()` | MEASURED — `test_interfaces` 8/8 |
| `transition.py` | the relation `T(s,a,s')`: frozen `Action` / `State` / `Transition` + `TransitionRelation` (successors/step/actions/materialize) | MEASURED — `test_transition` 8/8 |
| `artifacts.py` | durable outputs: `Trace`, `Invariant`, `Violation`, `ReachabilityCertificate` (with `verify()`) | MEASURED — `test_artifacts` 8/8 |

**Engines (behind the contract)**

| File | Role | Grade |
|---|---|---|
| `engine.py` | `VerificationEngine` protocol + `ExplicitStateBFSEngine` + `WorldModel` + `VerificationOptions` | MEASURED — `test_engine` 8/8 |
| `solver_adapter.py` | the ONLY module importing z3; bounded model checking over the extracted relation (**optional** — `pip install z3-solver`) | exercised via the symbolic suite |
| `symbolic_engine.py` | `SymbolicEngine` — second engine, SMT/BMC over the *extracted* relation (approach A); never imports z3 | MEASURED — `test_symbolic_engine` 8/8 (with z3) |
| `kernel_check.py` | compatibility layer: `check()` shim, `CheckResult`/`replay_path`, kernel helpers, `DEFAULT_INVARIANTS` — **no search algorithm remains here** | MEASURED — `test_kernel_check` 8/8 |

**Consumers & cross-engine**

| File | Role | Grade |
|---|---|---|
| `diagnose.py` | model-based diagnosis (the inverse): observed state → ranked fault hypotheses + a discriminating observation; consumes ghosts | MEASURED — `test_diagnose` 8/8 |
| `differential.py` | **first-class verification tool**: explicit vs symbolic equivalence over a model suite | MEASURED — `test_differential` 5/5 (with z3) |
| `conformance.py` | the **engine-conformance gate**: `check_conformance(engine)` — the universal contract every backend must satisfy (status set, replayable Trace on violation, determinism, label, frontier consistency) | MEASURED — `test_engine_conformance` |
| `counterfactual.py` | Phase C: **critical events in a ghost trace** by single-event ablation (trace-level; engine-agnostic; pure-stdlib) | MEASURED — `test_counterfactual` 8/8 |

## Engines and the differential harness

`ExplicitStateBFSEngine` is the reference. `SymbolicEngine` (approach A) reasons with SMT but **reuses the
same `TransitionRelation`** — it never re-encodes `apply_event`, so there is no second semantic definition.
It decodes the solver model to a concrete action sequence and **replays it through the relation** to build
the `Trace`: *symbolic proposes, semantics confirm*. Both engines share the exact same epistemic model
(CLOSED / BOUNDED / VIOLATED — there is no `UNSAT` status); `unsat-at-depth-k ≠ unreachable`.

`differential.py` is the proof that the contract hosts more than one engine: for every model both must reach
the same status; on VIOLATED, the same shortest witness *length* and a symbolic witness that replays to a
real violation (SMT models aren't canonical, so identical events are not required); otherwise the same
explored-state count. **Future engines should have to pass the differential harness before becoming a
supported backend.**

## Diagnosis (the inverse of the checker)

`kernel_check`/engines answer *"this invariant failed"* (forward). `diagnose` answers *"why?"* (inverse):
given an **observed** world state it returns **fault hypotheses** (entity losses) whose simulated cascade
reproduces the observation, ranked, each with the single **suggested observation** that best distinguishes
the surviving rivals. Pipeline: ghost trace → symptoms → candidate causes (consistency by simulation) →
ranking → ghost report.

**`confidence` is a ranking weight, not a probability.** No probabilistic model is assumed; scores are
ordinal allocation weights (parsimony of faults × parsimony of effects). `consistency ≠ causation`;
`minimal ≠ correct`; `weight ≠ P(true)`. Competing explanations are preserved (`underdetermined`).
Hypotheses are minimal **with respect to the implemented search** (minimum-cardinality entity-loss), not
globally minimal; consistency is judged over observed entities only, so partial observation yields honest
ambiguity. `unobserved ≠ ok`; `not-explained ≠ no-cause`.

## Honest grading of a result (the epistemic states)

- **CLOSED** — the frontier emptied before the depth bound: invariants are **PROVEN over the finite
  reachable state graph induced by the selected action alphabet and transition function** — and nothing
  beyond it. CLOSED carries a re-derivable `ReachabilityCertificate`. `state-space-closed = proof`.
- **BOUNDED** — the depth bound cut off real frontier: invariants hold on what was explored; the rest is
  **UNDERDETERMINED**. `depth-limited ≠ proof`.
- **VIOLATED** — an invariant fails; the shortest ghost trace is attached and is verified replayable.

## What it does NOT claim (Arbitrary-Boundary Law)

- Invariants are proven only over the **action alphabet** (default `{destroy, repair}`; `damage(amount)`
  excluded — unbounded amounts make the space infinite). `alphabet ≠ all-edits`.
- State identity excludes the event log, so `path ≠ state` (what makes closure finite).
- Passing the chosen invariants is `consistent-with-our-invariants`, not `correct`. `holds-here ≠ true`.
- The symbolic engine (approach A) extracts the relation by enumeration, so it is an **architectural** proof
  + witness extraction — **no scaling benefit yet**. `recompute ≠ cheaper-check`; `unsat-at-k ≠ unreachable`.
- It says nothing about gameplay, performance, or continuous dynamics. `event ≠ measured-dynamics`.

## Run (PowerShell, folder-directed)

Core (pure-stdlib, no dependencies):

```powershell
cd "weltwerk\verify"; python test_interfaces.py; python test_transition.py; python test_engine.py; python test_artifacts.py; python test_kernel_check.py; python test_diagnose.py; python test_engine_conformance.py; python test_counterfactual.py
```

Symbolic backend (optional — needs z3; the suites SKIP cleanly if it is absent):

```powershell
cd "weltwerk\verify"; pip install z3-solver; python test_symbolic_engine.py; python test_differential.py
```

Confirmed from local runs: core suites **8/8** each; with z3, `test_symbolic_engine` **8/8** and
`test_differential` **5/5**.

## Why this was the first NASA-merge chosen

(a) **Most novel use** — model-checking authored causal worlds is not a thing that exists; (b) **legally
cleanest** — reimplemented from the literature, own-copyright, dual-license-safe (no NOSA exposure, no
Java↔Python vendoring); (c) it **raises the central claim** — Weltwerk can now *prove* invariants it
previously only spot-tested. The differentiating IP is the mapping to `Potential ⊇ Actual`, not the
textbook search.

## Roadmap

The Phase A.2 **architecture spine is complete**: contract → semantics → engine → artifacts → second engine
→ differential harness (see [`DESIGN.md`](DESIGN.md)). The remaining work is capability, organized by the
*question* each stage answers — all over *the same transition system*.

**Phase A — Verification (exact reachability)**

1. ✅ Transition system (`../sim/world_sim.py` → `transition.py`)
2. ✅ Explicit-state model checker (`engine.ExplicitStateBFSEngine`) — ghosts + ghost traces
3. ✅ Symbolic checking (`symbolic_engine`, approach A: SMT/BMC over the extracted relation) + differential
   equivalence (`differential.py`). *Approach B* (SMT re-encoding of `apply_event` for real scale) is a
   later, separately-gated step — now safe, because the differential harness will catch encoding drift.

**Phase B — Analysis (sound approximation)**

4. ⏳ Abstract-interpretation pass — a *sound over-approximation* that scales past exact methods; feeds
   `world_lint`. A general framework from the literature (Patrick & Radhia Cousot), *not* NASA-specific;
   NASA's IKOS is one implementation — clean-room from the **published theory**, not IKOS source (treated as
   NOSA). `over-approx ≠ exact`.

**Phase C — Assistance (understand and respond to results)**

5. ✅ Diagnosis engine (`diagnose.py`) — ghost trace → ranked fault hypotheses + a probe to run next
6. ✅ Counterfactual explanations (`counterfactual.py`) — trace-level ablation: which events are critical to
   *this* ghost. Stronger forms (forbid an action from the alphabet + re-verify; symbolic `assert NOT(event_i)`)
   are documented follow-ups. `prevents-this-ghost ≠ makes-world-safe`.
7. ⏳ Automated repair suggestions — from a diagnosis, the minimal edit that restores invariants.

**Immediate next (recommended order):** (a) ✅ **engine-conformance harness** (`conformance.py` +
`test_engine_conformance.py`) — gates every engine (returns a `VerificationResult`, emits a replayable
`Trace` on violation, no new status, deterministic, frontier-consistent); future backends must pass it.
(b) ✅ **counterfactual explanations** (`counterfactual.py`, trace-level). Next: **automated repair**
(minimal edit that restores invariants) and the stronger counterfactual forms (alphabet-forbid re-verify;
symbolic `assert NOT`). (c) only later, symbolic **approach B** if scaling demands it.

(Build-order numbers and phase grouping are orthogonal: the numbers say what was built when; the phases say
what kind of question each stage answers.)
