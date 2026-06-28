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
