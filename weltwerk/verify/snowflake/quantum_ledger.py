# SPDX-License-Identifier: AGPL-3.0-only
"""
quantum_ledger.py — the snowflake instance of the domain-agnostic `claim_ledger.py`. The `Claim` type, the
grade ladder, and the honesty/ledger audit live there now; this module just supplies the snow-crystal claims.

The phrase "snowflake quantum design" spans real physics and overclaim. Each claim carries a GRADE, the
MECHANISM it rests on, what it does NOT show, and a FALSIFIER; each projects into the `AnalysisResult` honesty
contract. The legitimate quantum→design link is MOLECULAR (tetrahedral H-bonding sets the hexagonal lattice;
nuclear quantum effects tune the H-bond). Macroscopic quantum COHERENCE shaping morphology is NOT established
and is graded SPECULATIVE. `integrity ≠ truth`; `possibility ≠ actuality`.

Quantities grounded (see README sources): Pauling residual entropy S ≈ R·ln(3/2) ≈ 3.37 J·mol⁻¹·K⁻¹;
D₂O ice melts ≈ 3.8 K above H₂O ice (a nuclear-quantum isotope effect).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from claim_ledger import Claim, GRADES, SUPPORTED, grade_counts as _grade_counts, audit_ledger  # noqa: E402,F401

_SUPPORTED = SUPPORTED          # back-compat alias for existing tests

LEDGER = (
    Claim("C1", "The hexagonal (six-fold) habit of snow crystals originates in water's tetrahedral hydrogen "
                "bonding (ice Ih).", "ESTABLISHED",
          "Bent H₂O molecular geometry (a quantum/molecular-orbital fact) ⇒ tetrahedral hydrogen bonding ⇒ "
          "hexagonal ice Ih lattice ⇒ six-fold crystal habit.",
          "the diversity of macro-morphology (plates/columns/dendrites) — that is set by classical "
          "diffusion-limited growth and the Nakaya (T, supersaturation) map, not by the lattice alone.",
          "a counterfactual non-tetrahedral H-bond geometry that still yielded hexagonal habit."),

    Claim("C2", "A snowflake's six arms are similar because they share one growth environment, NOT because "
                "they communicate.", "ESTABLISHED",
          "all six arms occupy the same micro-pocket of air; a shared (T, supersaturation) trajectory + a "
          "deterministic growth law ⇒ matching arms. (Libbrecht.)",
          "that snowflakes are generally symmetric — most are irregular; perfect symmetry is the exception.",
          "an arm whose growth depends on a sibling arm's state (a real inter-arm channel). Demonstrated "
          "false-by-construction in snow_lattice.py: per-arm fields break symmetry; arms never read siblings."),

    Claim("C3", "Nuclear quantum effects (zero-point energy) measurably tune ice hydrogen bonds — e.g. D₂O ice "
                "melts ≈ 3.8 K above H₂O ice.", "MEASURED",
          "isotope substitution changes proton zero-point motion ⇒ changed H-bond strength/length and "
          "thermodynamics (a nuclear quantum effect).",
          "that NQE dictate snowflake MORPHOLOGY; the effect is on bond thermodynamics, not arm shape.",
          "no measurable thermodynamic isotope effect between H₂O and D₂O ice.",
          "ΔT_melt(D₂O−H₂O) ≈ +3.8 K"),

    Claim("C4", "Proton disorder gives ice a residual configurational entropy S ≈ R·ln(3/2) ≈ 3.37 J·mol⁻¹·K⁻¹ "
                "(Pauling).", "ESTABLISHED",
          "Bernal–Fowler 'ice rules' on proton placement ⇒ many equivalent configurations ⇒ residual entropy; "
          "confirmed to ~0.1%.",
          "anything about macroscopic shape; residual entropy is a proton-configuration count.",
          "a measured ice residual entropy materially different from R·ln(3/2).",
          "S ≈ R·ln(3/2) ≈ 3.37 J·mol⁻¹·K⁻¹"),

    Claim("C5", "Macroscopic quantum coherence determines snowflake morphology / snowflakes are coherent "
                "'quantum designs'.", "SPECULATIVE",
          "no established mechanism; environmental decoherence at the relevant temperatures and length/time "
          "scales is extremely fast, and growth is well-described classically.",
          "anything — there is no supporting evidence; it is listed to be graded honestly, not endorsed.",
          "an observed coherence signature controlling growth-scale morphology (none reported)."),

    Claim("C6", "Ice XI is a proton-ORDERED (ferroelectric) phase reachable from ice Ih (≈ 72 K, KOH-doped) "
                "— a quantum-ordering ground state.", "ESTABLISHED",
          "low-temperature ordering of the proton-disordered Ih lattice into ferroelectric ice XI.",
          "relevance to atmospheric snowflakes — those are ice Ih; ice XI is a lab/cryogenic phase. A scope "
          "note, not a snowflake mechanism.",
          "failure to observe the Ih→XI ordering transition under the stated conditions.",
          "T ≈ 72 K (KOH-doped)"),
)


def grade_counts() -> dict:
    return _grade_counts(LEDGER)


def main():
    print("quantum_ledger.py — quantum→snow-crystal design claims (via claim_ledger.py), graded with falsifiers\n")
    for c in LEDGER:
        q = f"  [{c.quantity}]" if c.quantity else ""
        print(f"  {c.id} [{c.grade:14s}] {c.statement}{q}")
        print(f"       mechanism : {c.mechanism}")
        print(f"       NOT shown : {c.does_not_show}")
        print(f"       falsifier : {c.falsifier}\n")
    a = audit_ledger(LEDGER)
    print(f"  ledger audit: honest={a['honest']}  counts={a['counts']}")
    print("  the molecular quantum link (C1/C3/C4/C6) is real and bounded; macroscopic 'quantum design' (C5)")
    print("  is SPECULATIVE and graded as such. possibility ≠ actuality; salience ≠ importance.")


if __name__ == "__main__":
    main()
