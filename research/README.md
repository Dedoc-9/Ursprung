<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# research/ — applications of the auditable-epistemology stack (NOT renderer code)

These are **applications** of the discipline built in [`../experiments/live_world_kernel/`](../experiments/live_world_kernel/)
(see [`../docs/EPISTEMIC_ACCOUNTING.md`](../docs/EPISTEMIC_ACCOUNTING.md)) to problem spaces *outside* the
renderer — domains where blurring observation, inference, and speculation is common. They are the analytical
bedrock that justifies *why the engineering stack treats these spaces the way it does*, and they are
deliberately **not** part of the renderer: the CORE/VIEW/ALLOCATOR/OBSERVER layering, the cardinal invariant,
and the `AGENTS.md` contract govern the renderer, not this folder. Each tool is standalone (stdlib-only,
self-testing); each doc carries its own provenance and sources.

## Index

| File | What it is | One-line result |
|---|---|---|
| `SONOLUMINESCENCE_AUDIT.md` | provenance audit of a physical phenomenon | interior is **OCCLUDED, not SEVERED**; *what the gas does* is intervention-grade, *what the core is* is model-grade |
| `SONOLUMINESCENCE_EXPERIMENT_ROADMAP.md` | discrimination matrix over hypotheses | `flash(t, λ)` is highest epistemic gain; the hypothesis set is not a clean partition |
| `SONOLUMINESCENCE_SIMULATION_PROGRAM.md` | simulations ranked by value/cost | a simulation is a `DECLARED` witness; **commitment-first** funding order (force `pred(H, do(x))` before measuring) |
| `SHA256_STRESS_AUDIT.md` | audit of a "3-in-1" cryptanalysis proposal | full SHA-256 **unbroken**; SAT/differential = reduced-round only; GA+Hamming **refuted by avalanche**; Collatz-counter `UNDERCOMMITTED` |
| `sha256_avalanche.py` | diffusion measurement (defensive) | measures the **absence** of gradient — `d_out ≈ 128` for every `d_in` (4/4) |
| `collatz_reconcile.py` | structural Collatz-like map auditor | exploits the **presence** of structure (2-adic bijection + drift); corners the residual; universal claim stays `OPEN` (7/7) |
| `sha256_2adic_branch.py` | falsification test for the carry-conditioned "2-adic reverse-Collatz" hypothesis | measures carry-branch survival; verdict regime *local gradient real, no compounding → `BOUNDED_TO_REDUCED_ROUNDS`*; never a break (the coinage, now committed & tested, not undercommitted) |

## The cross-domain pair (why both exist)

`sha256_avalanche` and `collatz_reconcile` are mirror images of one diffusion phenomenon:
- a cryptographic hash **engineers the absence** of algebraic structure — no parity-vector bijection, no drift,
  a flat Hamming landscape — which is what makes it secure and what defeats a Hamming/genetic search;
- a Collatz-like map **has** that structure — which is what makes density/almost-all convergence provable.

So a "reverse-Collatz counter" is a legitimate research instrument on Collatz and a non-starter on SHA-256 *for
the same reason* — one has the structure the other removes by design. Stated as two runnable measurements, not
intuition.

## The session's core realization (the discipline these tools encode)

> **Green checks certify code execution; only inspection of the output fields validates semantic meaning.**

Two bugs this session were *structurally sound code that passed their self-tests* and still output
mathematically mismatched reality until interrogated:
- `runtime_witness` **over-counted coverage** (counted `from x import f` names as modules) — caught by reading
  the `requests` numbers, not by the 8/8 check;
- `collatz_reconcile.stopping_density` **dipped non-monotonically** (`0.826 → 0.788`) because it computed
  "decreased at exactly step k" under a label claiming the Terras stopping-time density — caught by reading the
  output, then corrected to the monotone `≤ k` quantity.

The lesson is not that the tools are infallible — it is that errors surface as **honest signals** (an inflated
count, a dip) rather than hiding behind a passing test. `tested ≠ correct-label`; `declared ≠ verified`;
`green check ≠ semantic validity`. Comb the output, not just the check.
