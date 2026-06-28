<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# halvorsen/ — the Halvorsen attractor through the Ursprung discipline

Applying the verify kernel's epistemic discipline to a chaotic flow. The Halvorsen attractor is a near-ideal
test domain because it has **exact, provable invariants** (the DEMONSTRATED floor), a place where the
verify-cheaper-than-simulate asymmetry is *real* (a trapping certificate), and the canonical
`determinism ≠ reproducibility` ghost (chaos + floating point). Everything is graded honestly:
`integrity ≠ truth`; `measure ≠ cite-authority`.

The flow (cyclically symmetric, `a ≈ 1.4`):

```
ẋ = -a·x - 4y - 4z - y²      ẏ = -a·y - 4z - 4x - z²      ż = -a·z - 4x - 4y - x²
```

## The mapping to the kernel

| Ursprung primitive | Halvorsen instance |
|---|---|
| authoritative world / Weltlinie | the flow `f`; the committed integrated trajectory |
| projection (rendering ≠ truth) | the integrator (RK4/Euler) — a numerical rendering of the flow |
| exact invariant | `∇·f = -3a` (dissipativity); C₃ cyclic equivariance `f(P·s)=P·f(s)` |
| `ConstraintCertificate` (inductive) | a **trapping region**: `dV/dt < 0` outside R ⇒ positively invariant (no integration) |
| `differential` / oracle (PO-4) | differential on **invariant measures** (λ-sign, dissipation, bbox) — *not* paths |
| ghost taxonomy | FP run-to-run divergence = sensitive-dependence (precision), rate ≈ λ_max |
| `claim_ledger` | `attractor_ledger.py` grades every claim |
| `frontier_gate` (m_novel) | box-coverage discovery rate depletes ⇒ gate reads SUBCRITICAL |

## What is exactly true (DEMONSTRATED floor)

- **Dissipativity** `∇·f = -3a = -4.2`, constant (differentiate the field). Phase volume → 0. `flow.divergence`.
- **C₃ cyclic equivariance** `f(P·s) = P·f(s)` (substitute the permutation). The symmetry is of the *law*, not
  of any finite orbit. `flow.equivariance_error`.

## The honest parts (where the discipline bites)

- **Boundedness is MEASURED, not certified.** The natural quadratic Lyapunov ball `V=‖s‖²` is **rejected** by
  `trapping_certificate.py` — its `dV/dt` has a non-sign-definite cubic term, so a witness with `‖s‖>R,
  dV/dt≥0` exists. The checker refuses to certify boundedness even though the orbit is empirically bounded. A
  valid certificate needs SOS/interval methods — **OPEN**. `empirical-boundedness ≠ certified-boundedness`.
- **Differential testing on measures, not paths.** Chaos forbids comparing two integrators' trajectories
  pointwise (they diverge). `invariant_audit.py` compares the **λ-sign, dissipation, and bounding box** instead;
  the paths *do* diverge, by design. `agreement-on-measure ≠ agreement-on-path`.
- **The canonical ghost.** Two ε-different integrations diverge exponentially at rate ≈ λ_max, integrator-
  independent ⇒ classified as **sensitive-dependence (precision)**, not a model/implementation defect.
  `determinism ≠ reproducibility`.

## Claim ladder (`attractor_ledger.py`)

`H1` dissipativity / `H2` symmetry — **ESTABLISHED**; `H3` bounded — **MEASURED** (certificate OPEN);
`H4` chaotic (λ_max>0) — **MEASURED**; `H5` FP divergence is precision — **MEASURED**; `H6` "encodes
information beyond the flow" — **SPECULATIVE**, routed to the `residual_channel` firewall (predicted 0).

## Files & run

`flow.py` · `trapping_certificate.py` · `invariant_audit.py` · `attractor_ledger.py` · `coverage_gate.py`
(+ a test per module). Reuses `../verify/claim_ledger.py` and `../verify/frontier_gate.py` unchanged.

```powershell
cd "weltwerk\halvorsen"; python flow.py; python trapping_certificate.py; python invariant_audit.py; python attractor_ledger.py; python coverage_gate.py
cd "weltwerk\halvorsen"; python test_flow.py; python test_trapping_certificate.py; python test_invariant_audit.py; python test_attractor_ledger.py; python test_coverage_gate.py
```

Pure-stdlib (no numpy/z3). `invariant_audit` and `coverage_gate` run integration loops (tens of seconds).
Numerical results are MEASURED with our own integrator and audited for integrator-robustness — never cited as
truth. `integrator ≠ flow`; `trajectory ≠ attractor`; `integrity ≠ truth`.

## Robust real-world adaptation patterns

These are **adaptation patterns**, not turnkey features: the repo supplies *verified primitives* (exact
invariants, the residual-channel firewall, the frontier gate, the epistemic gate, the trapping checker); wiring
them to a live domain is the integrator's work, and **each pattern ships with its boundary**. API names below
are exact. The Halvorsen world is the worked example; the recipe at the end generalizes to any flow `f`.

**1. Validation testbed for high-throughput solvers.** Use the exact invariants as an un-fakable anchor for a
new (GPU/ML) ODE/PDE integrator.
*Use:* `flow.divergence(a)` is the exact target `-3a`; `invariant_audit.dissipation_numeric()`,
`lyapunov_max()` (sign), and the bounding box are the candidate's **invariant measures** (never compare
trajectories — chaos forbids it). Gate the deploy with `epistemic_types.require_grounded`: build a `Grounding`
adapter that `is_grounded()` iff `|measured_dissipation − (−3a)| < tol` **and** the λ-sign matches; the deploy
function raises `UngroundedError` otherwise.
*Boundary:* **necessary, not sufficient** — a solver can match dissipation/symmetry and still distort the
attractor. `agreement-on-measure ≠ correctness`.

**2. Grounding generative-agent output.** Force a code/trajectory synthesizer through the epistemic gate so it
cannot emit an ungrounded path.
*Use:* `epistemic_types.Grounded.ground(trajectory, proof)` + `@require_grounded("trajectory")` on the applier;
the proof is a verifier output (e.g. an `EngineClosed`-style adapter, or a custom `InTrappingRegion` adapter
built on `trapping_certificate`). A blind guess never constructs `Grounded` → `UngroundedError` before runtime.
*Boundary:* the strong "inside a certified region" proof needs a **valid** certificate (see #5); absent one, the
honest proof is "inside the **measured** bounding box" (MEASURED, not certified). `grounded ≠ true`.

**3. Telemetry anomaly / hardware-degradation detection — the best-fit reuse.** Distinguish genuine component
wear from sensor noise.
*Use:* `residual_channel.audit(samples_xyz, misspec_fns=(coarsen_Z, …))` with sensor streams as `X,Y` and the
control/operating state as the confounder `Z`. `CONSISTENT_WITH_NULL` ⇒ healthy (dependence explained by the
control); `RESIDUAL_MISSPEC_STABLE` ⇒ a real unmodeled inter-coordinate channel (a candidate fault, because it
**survives Z-coarsening**); `RESIDUAL_MISSPEC_FRAGILE` ⇒ likely mis-specification/noise.
*Boundary:* `residual-CMI ≠ channel` until mis-spec-stable; requires the **complete modeled** `Z` (else
confounder leakage); discretization is a model choice (Arbitrary-Boundary Law).
*Built:* **`telemetry_audit.py`** — `diagnose(samples)` → `HEALTHY` / `SENSOR_MISSPEC` / `FAULT` by comparing
`I(X;Y|Z)` to `I(X;Y|Z,W)` against the shuffle null (a fault must survive conditioning on the candidate
confounder `W`; a missing confounder dissolves and is **not** called a fault). Tested in `test_telemetry_audit.py`.

**4. Chaos-RNG / entropy-pool degeneracy monitor.** Watch a chaotic bitstream generator for periodic windows or
precision collapse.
*Use:* `coverage_gate.coverage_windows()` + `frontier_gate` — a premature drop of the box-discovery multiplier
into `SUBCRITICAL` flags a collapse and emits a `PIVOT` (reseed/flush) signal.
*Boundary:* this detects **gross degeneracy only**, and is **necessary-not-sufficient** for entropy — it is not
a cryptographic guarantee and does not replace standard suites (e.g. NIST SP 800-22). Note also that chaotic-map
RNGs are generally not recommended for cryptographic use; treat this purely as a degeneracy/health monitor.

**5. Edge safety gate for nonlinear control.** A cheap boundary check instead of forward trajectory simulation.
*Use:* `trapping_certificate.certify_ball(field, a, R)` — if a Lyapunov `V` gives `dV/dt < 0` outside radius R,
membership is a single boundary evaluation (verify-cheaper-than-simulate), so an edge controller checks "am I
inside the certified region?" without running a 100-step look-ahead.
*Boundary (critical):* this guarantee holds **only with a sound certificate**. For Halvorsen the quadratic-V
ball is **REJECTED** (`certify_ball` returns `certified=False` with a witness) — so on this system you must
**first obtain a valid certificate** (higher-degree V via SOS / interval arithmetic — **OPEN**). A rejected or
unverified `V` gives **no** safety; never deploy on its strength. `unsound-certificate ≠ safety`.
*Built (two-part):* **`safety_gate.py`** — *Part A (the mechanism)*: `SafetyGate.permit(next_state)` commits a
move only if `Grounded` by `InsideCertifiedRegion` (O(1) membership, no simulation), via `require_grounded`;
with the **rejected** Halvorsen certificate it is **fail-closed** (permits nothing). *Part B (a sound Halvorsen
certificate)*: **OPEN**. Tested in `test_safety_gate.py` (incl. `unsound_refuses_all`).

### Wiring a new domain (the recipe)

1. Implement the field `f` (and integrators). 2. Establish the **exact** invariants (divergence, symmetries) —
the DEMONSTRATED floor. 3. Run `invariant_audit`-style measures (Lyapunov sign, dissipation, bbox) with
integrator-robustness + the FP-ghost classification. 4. *Attempt* a `trapping_certificate` — and accept its
rejection honestly. 5. Grade every claim with `claim_ledger`. 6. Gate any side-effecting applier with
`require_grounded`; route "hidden structure" suspicions to `residual_channel`. Each step states what it does
**not** show. `measure ≠ cite-authority`; `integrity ≠ truth`.
