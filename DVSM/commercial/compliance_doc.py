# SPDX-License-Identifier: AGPL-3.0-only
# Commercial use beyond AGPL-3.0 requires a separate license — see LICENSE-COMMERCIAL.md.
"""
compliance_doc.py — generate an enterprise compliance document from the PROOF-GATED `COMMERCIAL_CLAIMS`.

The document is a DERIVED artifact of the gated ledger: `generate()` refuses to run unless
`audit_commercial_ledger` passes, so the doc can never contain a claim the gate would reject. Every warranted
capability is rendered with its grade, its discharged-obligation provenance, and the boundary it does NOT
establish; the boundary (non-warranty) claims are listed verbatim; and the warranty / liability /
indemnification sections are DISCLAIMER-FIRST and scoped to exactly those discharged claims.

NOT LEGAL ADVICE. This is a template for counsel to review and complete; dollar figures and terms are
`[PLACEHOLDER]`. The point is structural, not legal: a compliance doc that cannot exceed the proofs.
`claim ≠ proof`; `warranty ≠ proof`; `generated ≠ executed`.
"""
from __future__ import annotations

import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "..", "weltwerk", "verify"))
from commercial_obligations import (COMMERCIAL_CLAIMS, DISCHARGED, audit_commercial_ledger)  # noqa: E402
from claim_ledger import SUPPORTED                                                           # noqa: E402

CLAIM_TAG = re.compile(r"\[([A-Z]\d+)\]")
BANNER = "**NOT LEGAL ADVICE — a template for counsel to review and complete. Figures are `[PLACEHOLDER]`.**"


class LedgerNotHonest(Exception):
    """Refuse to generate a compliance doc from a ledger that fails the no-overclaim gate."""


def generate(claims=COMMERCIAL_CLAIMS) -> str:
    audit = audit_commercial_ledger(claims)
    if not audit["honest"]:
        raise LedgerNotHonest(
            f"refusing to generate: ledger not honest (exceeds={audit['exceeds_proof']}, hype={audit['hype']}, "
            f"unknown={audit['unknown_obligation']}, missing={audit['missing_boundary']})")

    supported = [c for c in claims if c.grade in SUPPORTED]
    boundary = [c for c in claims if c.grade not in SUPPORTED]

    L = []
    L.append("<!-- GENERATED from COMMERCIAL_CLAIMS by compliance_doc.py — do not edit by hand. -->")
    L.append("# Enterprise Compliance Summary — DVSM Commercial Edition\n")
    L.append(BANNER + "\n")
    L.append("Every statement below is derived from a proof-gated claim ledger. Generation aborts unless the "
             "ledger passes the no-overclaim gate, so this document cannot assert more than the evidence "
             "supports. Each warranted capability cites the discharged obligation (test) that backs it.\n")

    L.append("## 1. Warranted scope (capabilities backed by a discharged obligation)\n")
    for c in supported:
        L.append(f"- **[{c.id}]** ({c.grade}, tier: {c.tier}) — {c.statement}")
        L.append(f"  - backed by: `{c.rests_on}` — {DISCHARGED.get(c.rests_on, 'n/a')}")
        L.append(f"  - does NOT establish: {c.does_not_show}")
        L.append(f"  - falsifier: {c.falsifier}")
    L.append("")

    L.append("## 2. Explicit non-warranties (stated, in writing)\n")
    L.append("The following are deliberately NOT claimed and are excluded from any warranty below:\n")
    for c in boundary:
        L.append(f"- **[{c.id}]** ({c.grade}) — {c.statement}")
        L.append(f"  - reason: {c.does_not_show}")
    L.append("")

    L.append("## 3. Limited warranty (TEMPLATE — counsel to complete)\n")
    L.append("For the warranty period of `[PLACEHOLDER: e.g. 12 months]`, Licensor warrants solely that the "
             "Software performs the checks described in §1 (Warranted Scope) when run as documented on the "
             "supported configurations. This warranty is **limited to the discharged obligations in §1** and "
             "extends to nothing else. The Software is otherwise provided **\"AS IS\"**, and Licensor "
             "expressly disclaims all other warranties (including merchantability and fitness for a particular "
             "purpose) — in particular every item enumerated in §2. A breach is established only by the "
             "falsifier stated for the corresponding claim.\n")

    L.append("## 4. Limitation of liability (TEMPLATE — counsel to complete)\n")
    L.append("Licensor's aggregate liability shall not exceed `[PLACEHOLDER: e.g. fees paid in the prior 12 "
             "months]`. Licensor shall have **no liability** for any matter enumerated in §2 (Explicit "
             "non-warranties), nor for indirect, incidental, consequential, or punitive damages. Reliance on "
             "the Software beyond §1 is at the Licensee's sole risk. `bounded-by-clamp ≠ stable-dynamics`; "
             "`certificate ≠ proof-of-everything`.\n")

    L.append("## 5. Indemnification (TEMPLATE — counsel to complete)\n")
    L.append("Licensor shall indemnify Licensee solely against `[PLACEHOLDER: e.g. third-party IP "
             "infringement]` claims arising from the unmodified Software, capped per §4. Licensor provides "
             "**no indemnification** for use beyond §1, for reliance on any §2 item, or for results derived "
             "from Licensee-supplied inputs / schemas. `integrity ≠ truth`.\n")

    L.append("## 6. Provenance\n")
    L.append(f"Generated from `COMMERCIAL_CLAIMS` ({len(supported)} warranted, {len(boundary)} boundary) at "
             "gate-pass. Grades: " + ", ".join(sorted({c.grade for c in claims})) + ". "
             "Regenerate whenever the ledger changes; counsel must review before execution. "
             "`generated ≠ executed`; `claim ≠ proof`.")
    return "\n".join(L) + "\n"


def claim_tags(doc: str) -> set:
    """Every claim id referenced in a generated doc (for the no-drift check)."""
    return set(CLAIM_TAG.findall(doc))


def main():
    try:
        doc = generate()
    except LedgerNotHonest as e:
        print(f"compliance_doc: {e}")
        return
    out = os.path.join(_HERE, "COMPLIANCE_SUMMARY.generated.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"compliance_doc — wrote {out} ({len(doc)} bytes)")
    print(f"  claim tags in doc: {sorted(claim_tags(doc))}")
    print("  derived from the gated ledger; NOT legal advice; counsel must review.")


if __name__ == "__main__":
    main()
