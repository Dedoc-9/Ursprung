<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# FAILURE_MODE_MATRIX — the cross-boundary diagnostic layer (connective tissue, not a new ontology)

> **This is not another boundary. It is the routing layer over the boundaries already earned — a table of
> interactions, not a theory.**

The boundary docs each ask *"can this happen?"* This asks the operational question that comes after enough of
them exist:

> **"If I observe X, which boundary am I probably hitting?"**

That is the difference between a research framework (define what is measurable) and a troubleshooting framework
(given a symptom, route to the cause). The project has accumulated enough independent probes that the bottleneck
is no longer *defining* boundaries — it is *classification*. `declared ≠ verified`: this matrix is a declared
mapping, a router toward a boundary, never a verdict.

## A word on "conservation laws" (graded down before building on it)

It is tempting to call the four boundaries *conservation laws*. They are not. Nothing is conserved here — the
project already demoted its own "Temporal Fidelity **Conservation** Law" to an **Accounting** Law for exactly
this reason. The accurate, weaker, load-bearing claim is: **four independent invariants / orthogonal failure
axes**, each violable without the others. "Independent" and "orthogonal" survive reduction; "conservation"
imports a physics authority the structure has not earned (imported terms must increase precision, not authority).

And **orthogonality is a hypothesis this matrix tests, not an assumption it rests on.** The inverse table below
*is* the test: where an observation collapses to one cause, the axes are separable there; where it stays
multi-candidate, two boundaries are not independently diagnosable from that observation alone.

## The four axes

| Boundary | Question | Characteristic failure | Root cause | Status |
|---|---|---|---|---|
| **Self-Modification** | Can the system define its own frontier? | `NON_ORIENTABLE` | recursion / no global outside | contract ([doc](SELF_MODIFICATION_BOUNDARY.md)) |
| **Authority Arbitrage** | Can advantage be independently adjudicated? | `SEVERED` | information loss | contract ([doc](AUTHORITY_ARBITRAGE_BOUNDARY.md)) |
| **Adjudication Throughput** | Can adjudication arrive before consequences are load-bearing? | `FLOODED` | verification / throughput deficit | contract ([doc](ADJUDICATION_THROUGHPUT_BOUNDARY.md)) |
| **Causal Identifiability** | Can observation alone determine causation? | `INTERVENTION_ONLY` | identifiability limit | **empirically established** (latent phases; `observation ≠ intervention`) |

The fourth is not a pending contract like the other three — it is already *measured* (the Phase-1 latent
benchmark and the project's pioneering result: a confounder that reconstructs, is gauge-invariant, and correlates
≈0.6 still fails the gate because `do(c)` does not move the outcome). The matrix therefore unifies **three
contracts-ahead-of-code plus one verified result** — stated so the matrix does not imply the four share an
epistemic status.

A system can survive one axis and fail another, which is the evidence the axes are orthogonal rather than one
defect rediscovered four times:

- perfect provenance, but `FLOODED`;
- fast verification, but `SEVERED`;
- complete logs, but `INTERVENTION_ONLY`;
- independent witnesses everywhere, but `NON_ORIENTABLE` when authority edits authority.

## Distinct at the root, overlapping at the surface

The four **root causes** are distinct (recursion · information loss · throughput deficit · identifiability
limit). The four **observable labels** are not a clean bijection with the boundaries — `SEVERED`, for instance,
is reachable both from authority-witness-destruction *and* from a throughput no-witness state. That overlap is
precisely why the inverse map must yield **candidate sets, not diagnoses** — the project's standing discipline
that a residual is a *candidate set, not a truth* (`ghost ≠ hidden truth`). Narrowing the set requires a
**discriminating observation** or, where observation underdetermines it, an **intervention**.

## Forward — primary failure → secondary consequence (and cascades)

| Primary failure | Secondary consequence |
|---|---|
| `FLOODED` | produces *temporary* arbitrage (advantage during the verification gap) |
| `SEVERED` | makes arbitrage *permanent* (no witness will ever adjudicate it) |
| `NON_ORIENTABLE` | makes frontier placement *observer-relative* (no single global cut) |
| `INTERVENTION_ONLY` | prevents *definitive* adjudication (observation cannot close it) |

**The cascade worth naming:** `FLOODED` is temporary *only until commitment forms*. A flooded claim that crosses
the irreversibility frontier (`t_dep < t_verified`) before it is verified **hardens into permanence** — a
throughput deficit becomes effectively information loss. So `FLOODED → SEVERED` across the irreversibility
frontier is a real interaction, not two unrelated rows: the timing failure *causes* the loss failure once a
dependent commits on the unverified.

## Inverse — observation → candidate causes → the discriminator

This is the operational layer: each symptom maps to a candidate set **and** the next observation that collapses
it. The discriminator is the value; the candidate set alone is just a lookup.

| Observation | Candidate causes | Discriminator (the test that collapses the set) |
|---|---|---|
| Hidden advantage persists | `SEVERED`, `FLOODED` | Does `t_verified` ever complete? Never → `SEVERED`; completes after `t_dep` → `FLOODED` |
| Verification disagreement | `INTERVENTION_ONLY`, `NON_ORIENTABLE` | Is the validators' cut orientable (`klein_probe`)? Frustrated → `NON_ORIENTABLE`; orientable yet still disagree → `INTERVENTION_ONLY` (needs `do(·)`) |
| Recovery impossible | `SEVERED` | (single candidate — directly diagnostic) |
| Recovery possible but late | `FLOODED` | (single candidate — directly diagnostic) |

The real output of the matrix is therefore `(candidate_set, discriminating_probe)` — it **routes toward a
boundary**, it never returns a diagnosis. `observation → candidate set, never cause`; same no-verdict stance as
every instrument in the project.

## What writing this *now* buys (before the probes exist)

Three of the four probes are contracts, not code, so the matrix is — honestly — a **paper diagnostic over
mostly-unbuilt probes**, two steps ahead of implementation. It is still worth writing now for one concrete
reason beyond connective tissue: **the discriminators are a design constraint, top-down.** For the inverse table
to work, each boundary probe must *emit an observable signature distinguishable from the others* — e.g.
Adjudication-Throughput must expose whether `t_verified` ever completes (to separate `FLOODED` from `SEVERED`),
and Self-Modification must expose the orientability of the validators' cut (to separate `NON_ORIENTABLE` from
`INTERVENTION_ONLY`). The matrix thus tightens the three open contracts from the top: it tells each probe what it
must *output* to remain diagnostically separable.

## Invariants · observables · assumptions · failure modes · ghosts · alternatives

**Invariants:** the matrix routes; it does not diagnose, enforce, or rank. Output is a candidate set + a
discriminator, never a verdict, never a scalar. The rollup across axes is the unweighted conjunction *(which
boundaries are clean?)* — a vector, never a "health score."

**Observables:** the categorical outputs of the four probes (orientability, advantage reconstructability, race
outcome / `t_verified` vs `t_dep`, intervention-required).

**Assumptions (declared):** the observation→candidate mapping is a *declared* model (`declared ≠ verified`); the
four probes emit distinguishable signatures (the design constraint above); a single symptom is being routed at a
time (composite symptoms decompose into rows).

**Failure modes:** (a) false single-candidacy — routing a symptom to one cause when two remain admissible
(over-confident triage); (b) a discriminator that itself requires an intervention being treated as a free
observation (it is not — that is the `INTERVENTION_ONLY` axis reappearing inside the router).

**Possible ghost signals (the most valuable):** an observed real failure whose symptom matches **no row** — that
is not noise, it is evidence of an **unmodeled fifth axis**, a boundary the project has not yet named. The matrix
is also a detector for its own incompleteness.

**Alternatives (rejected for v1):** a *learned* classifier over probe outputs — rejected, because it
reintroduces the black box and the scalar the whole project refuses; the matrix stays a declared lookup plus
explicit discriminators a human can audit.

## Honest scope

This is connective tissue, not a new ontology. It is only as good as the probes feeding it, three of which are
not built; it becomes operational as they are. It adds no claim about the world — only a declared route from a
symptom to a boundary, with the discriminating test that narrows it. `declared ≠ verified`; the matrix tells you
*where to look*, never *what is true*.

## The seam (the contract a router would satisfy, not yet built)

A future `experiments/live_world_kernel/failure_router.py` would take the categorical outputs of the four probes
and return `(candidate_set, discriminating_probe)` — never a diagnosis. Its self-test's first success is
*negative*: a symptom with a single known cause must route to exactly that one cause (no false multi-candidacy),
and a symptom matching no row must be reported as `UNMODELED` (a candidate fifth axis), never forced into the
nearest row.

> Boundary docs define what is measurable. Probes measure it. The matrix tells you where to look. When a real
> system fails, the first question is not *"is this a self-modification problem?"* — it is *"why did this occur?"*
> — and the answer should route you toward one boundary, as a candidate set with a test attached, never as a
> verdict.
