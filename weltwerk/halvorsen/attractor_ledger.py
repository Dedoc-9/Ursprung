# SPDX-License-Identifier: AGPL-3.0-only
"""
attractor_ledger.py — the Halvorsen claims, graded on the epistemic ladder via the reusable
`weltwerk/verify/claim_ledger.py`. Each claim carries grade + mechanism + does-not-show + falsifier.

The DEMONSTRATED floor is algebraic (dissipativity, C₃ symmetry); the statistical claims are MEASURED with our
own integrator; the "hidden structure" claim is SPECULATIVE and routed to the residual_channel firewall.
`integrity ≠ truth`; `measure ≠ cite-authority`; `empirical-boundedness ≠ certified-boundedness`.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "verify"))
from claim_ledger import Claim, GRADES, SUPPORTED, grade_counts, audit_ledger   # noqa: E402,F401

LEDGER = (
    Claim("H1", "The Halvorsen flow is dissipative: ∇·f = -3a (constant), so phase volume contracts to a "
                "zero-volume attractor.", "ESTABLISHED",
          "the Jacobian trace is -a-a-a = -3a everywhere (differentiate the field); volume ~ e^{-3a·t}.",
          "anything about the attractor's shape, dimension, or dynamics — only that volume contracts.",
          "a measured phase-volume contraction rate different from -3a.",
          "∇·f = -3a = -4.2"),

    Claim("H2", "The flow is C₃-cyclically symmetric: f(P·s) = P·f(s) under (x,y,z)→(y,z,x).", "ESTABLISHED",
          "substitute the cyclic permutation into the field; each equation maps to the next exactly.",
          "that any single trajectory is symmetric (it is not); the symmetry is of the LAW and the invariant "
          "measure, not of a finite orbit. symmetry = shared law ≠ signal.",
          "an algebraic asymmetry term in f(P·s) − P·f(s) beyond floating-point round-off."),

    Claim("H3", "The attractor is bounded (trajectories stay in a finite region after the transient).", "MEASURED",
          "long RK4 integration remains within a finite bounding box; the cubic nonlinearity does not blow up "
          "on the attractor.",
          "a PROOF of boundedness — the natural quadratic Lyapunov ball is REJECTED (cubic term breaks dV/dt<0); "
          "a valid trapping certificate is OPEN. empirical-boundedness ≠ certified-boundedness.",
          "a trajectory escaping the measured bounding box under a converged integrator."),

    Claim("H4", "The system is chaotic: the largest Lyapunov exponent is positive.", "MEASURED",
          "Benettin two-trajectory estimate yields λ_max > 0, integrator-robust in sign.",
          "the exact value (integrator/length dependent) or the full spectrum; only the positive SIGN is robust.",
          "λ_max ≤ 0 under a converged integrator, or a sign that flips with the integrator."),

    Claim("H5", "Run-to-run divergence of integrations is sensitive-dependence (precision), not a model or "
                "implementation defect.", "MEASURED",
          "two integrations from ε-different inputs diverge exponentially at a rate ≈ λ_max, independent of the "
          "integrator. determinism ≠ reproducibility.",
          "that the integrator is wrong; the divergence is the dynamics amplifying precision, not a bug.",
          "a divergence rate unrelated to λ_max, or divergence that vanishes under a different integrator "
          "(⇒ an implementation ghost instead)."),

    Claim("H6", "The attractor 'encodes information' / has structure beyond the deterministic flow.", "SPECULATIVE",
          "no mechanism; the flow is deterministic, so any apparent inter-coordinate information beyond the "
          "state is confounded by the shared dynamics.",
          "anything — listed to be graded honestly, not endorsed.",
          "I(x_i;x_j | flow-state) > 0 surviving the residual_channel shuffle-null + integrator "
          "mis-specification (predicted 0)."),
)


def main():
    print("attractor_ledger.py — Halvorsen claims graded on the epistemic ladder\n")
    for c in LEDGER:
        q = f"  [{c.quantity}]" if c.quantity else ""
        print(f"  {c.id} [{c.grade:11s}] {c.statement}{q}")
        print(f"       NOT shown : {c.does_not_show}")
        print(f"       falsifier : {c.falsifier}\n")
    a = audit_ledger(LEDGER)
    print(f"  ledger audit: honest={a['honest']}  counts={a['counts']}")
    print("  DEMONSTRATED floor is algebraic (H1/H2); statistics are MEASURED (H3/H4/H5); 'hidden structure'")
    print("  (H6) is SPECULATIVE → residual_channel firewall. measure ≠ cite-authority; integrity ≠ truth.")


if __name__ == "__main__":
    main()
