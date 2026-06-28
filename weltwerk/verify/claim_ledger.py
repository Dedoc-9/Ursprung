# SPDX-License-Identifier: AGPL-3.0-only
"""
claim_ledger.py — a domain-agnostic, honesty-enforced claim ledger (extracted from the snowflake study).

A reusable template for stating a set of claims about ANY modeled system such that each claim is forced to
carry its epistemic status. Every claim has a GRADE on the ladder, the MECHANISM it rests on, what it does NOT
show, and a FALSIFIER; and every claim projects into the shared `AnalysisResult` honesty contract (scope + ≥1
limitation). `audit_ledger` mechanizes the ledger-level invariants — so a ledger cannot silently ship an
ungraded, unfalsifiable, or boundary-free claim. `integrity ≠ truth`; `salience ≠ importance`.

GRADE LADDER (preserve epistemic states; never force a binary):
  ESTABLISHED     — settled theory/observation, broadly reproduced.
  MEASURED        — a measured effect exists; full mechanism may be open.
  UNDERDETERMINED — competing explanations survive the evidence.
  SPECULATIVE     — proposed, not supported by current evidence.
  NOT_MEASURED    — outside what has been observed (a scope note).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artifacts import AnalysisResult, Finding, Limitation        # noqa: E402  (honesty contract, reused)

GRADES = ("ESTABLISHED", "MEASURED", "UNDERDETERMINED", "SPECULATIVE", "NOT_MEASURED")
SUPPORTED = {"ESTABLISHED", "MEASURED"}      # grades that assert a claim is currently supported


@dataclass(frozen=True)
class Claim:
    id: str
    statement: str
    grade: str
    mechanism: str                # what the claim actually rests on
    does_not_show: str            # the boundary — what it does NOT establish
    falsifier: str                # the observation that would overturn it
    quantity: str = ""            # optional grounded number

    def as_analysis(self) -> AnalysisResult:
        """Project into the shared honesty contract (scope + ≥1 limitation)."""
        findings = (
            Finding("CLAIM", "claim-ledger", f"[{self.grade}] {self.statement}"),
            Finding("MECHANISM", "claim-ledger", self.mechanism),
        )
        limitations = (
            Limitation("claim-ledger", f"does not show: {self.does_not_show}"),
            Limitation("epistemic", f"grade={self.grade}; falsifier: {self.falsifier}"),
        )
        return AnalysisResult(source_trace=(self.id,), scope="claim-ledger",
                              findings=findings, limitations=limitations)


def grade_counts(ledger) -> dict:
    out = {g: 0 for g in GRADES}
    for c in ledger:
        out[c.grade] = out.get(c.grade, 0) + 1
    return out


def audit_ledger(ledger) -> dict:
    """Ledger-level honesty invariants. `honest` iff every grade is on the ladder and every claim carries both
    a non-empty falsifier and a non-empty 'does_not_show' boundary."""
    off_ladder = [c.id for c in ledger if c.grade not in GRADES]
    missing = [c.id for c in ledger if not (c.falsifier.strip() and c.does_not_show.strip())]
    return {"off_ladder": off_ladder, "missing_falsifier_or_boundary": missing,
            "honest": not off_ladder and not missing, "counts": grade_counts(ledger)}


def main():
    print("claim_ledger.py — a domain-agnostic, honesty-enforced claim ledger\n")
    demo = (
        Claim("D1", "Effect E is real and reproduced.", "ESTABLISHED",
              "mechanism M, reproduced across N studies.", "the magnitude under condition C.",
              "a pre-registered replication failing to find E."),
        Claim("D2", "Hypothesis H explains the residual.", "SPECULATIVE",
              "no established mechanism; consistent-with but not required-by the data.",
              "anything — listed to be graded, not endorsed.",
              "a controlled test isolating H from the known driver."),
    )
    a = audit_ledger(demo)
    print(f"  audit: honest={a['honest']}  counts={a['counts']}")
    for c in demo:
        print(f"    {c.id} [{c.grade}] falsifier? {'yes' if c.falsifier else 'NO'}")
    print("\n  every claim carries grade + mechanism + boundary + falsifier, and projects to AnalysisResult.")
    print("  a ledger cannot ship an ungraded, unfalsifiable, or boundary-free claim. integrity ≠ truth.")


if __name__ == "__main__":
    main()
