# SPDX-License-Identifier: AGPL-3.0-only
# Commercial use beyond AGPL-3.0 requires a separate license — see LICENSE-COMMERCIAL.md.
"""
commercial_obligations.py — the buyer-facing claims ledger, PROOF-GATED. This is the commercial expression of
the project's core discipline: a sales claim is honest only if a discharged technical obligation backs it.

`consider those proofs`: every `CommercialClaim` names the obligation it `rests_on`. The ledger is honest iff
  (a) every claim is on the grade ladder with a `does_not_show` and a `falsifier`;
  (b) no SUPPORTED (ESTABLISHED/MEASURED) claim rests on an UNDISCHARGED or REJECTED obligation;
  (c) no SUPPORTED claim contains hype-lexicon language;
  (d) every `rests_on` names a known obligation.
So marketing cannot exceed evidence — the same vulnerability the whole project treats as a defect, enforced at
the contract layer. `claim ≠ proof`; `grade ≠ truth`.

SINGLE SOURCE OF TRUTH: the claims and the obligation registries are loaded from the manifests `ledger.tsv`
and `obligations.tsv` (same files the Rust `shipped_ledger()` reads via `include_str!`), so the two
language ports cannot drift. Edit the manifest, not the code. `mirror ≠ source` → resolved to one source.

Grades reuse the open-core epistemic ladder (`claim_ledger.GRADES`): ESTABLISHED, MEASURED, UNDERDETERMINED,
SPECULATIVE, NOT_MEASURED. SUPPORTED = {ESTABLISHED, MEASURED}.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "weltwerk", "verify"))
from claim_ledger import Claim, audit_ledger, GRADES, SUPPORTED                 # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))


def _read_tsv(name: str) -> List[List[str]]:
    """Read a tab-separated manifest (skipping blank / '#' lines). UTF-8 so κ / ‖ / σ survive on any platform
    (do NOT rely on the locale default — Windows cp1252 would corrupt them)."""
    rows: List[List[str]] = []
    with open(os.path.join(_HERE, name), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def _load_obligations() -> Tuple[Dict[str, str], Dict[str, str]]:
    discharged: Dict[str, str] = {}
    open_rej: Dict[str, str] = {}
    for row in _read_tsv("obligations.tsv"):
        key, status = row[0], row[1]
        evidence = row[2] if len(row) > 2 else ""
        if status == "DISCHARGED":
            discharged[key] = evidence
        elif status == "OPEN_OR_REJECTED":
            open_rej[key] = evidence
        else:
            raise ValueError("unknown obligation status %r for key %r" % (status, key))
    return discharged, open_rej


# Technical obligations + their status, loaded from the single-source manifest (obligations.tsv).
DISCHARGED, OPEN_OR_REJECTED = _load_obligations()

# Hype lexicon — banned from any SUPPORTED claim (semantic inflation the product treats as a defect).
HYPE: Tuple[str, ...] = (
    "guarantee", "guaranteed", "100%", "unhackable", "proves your", "certified safe", "bug-free",
    "prevents all", "eliminates all", "fully secure", "provably safe", "zero risk")


@dataclass(frozen=True)
class CommercialClaim:
    """A buyer-facing claim. `rests_on` MUST name an obligation key; a SUPPORTED grade is honest only when that
    key is DISCHARGED. Boundary claims (what we do NOT sell) rest on OPEN_OR_REJECTED at a non-supported grade."""
    id: str
    statement: str
    grade: str
    rests_on: str
    does_not_show: str
    falsifier: str
    tier: str = "open-core"          # open-core (AGPL-3.0) | commercial (paid license)

    def to_claim(self) -> Claim:
        return Claim(self.id, self.statement, self.grade, f"rests_on={self.rests_on}",
                     self.does_not_show, self.falsifier)


def _load_claims() -> Tuple[CommercialClaim, ...]:
    out: List[CommercialClaim] = []
    for row in _read_tsv("ledger.tsv"):
        if len(row) != 7:
            raise ValueError("ledger.tsv row needs 7 tab-separated fields, got %d: %r" % (len(row), row))
        cid, grade, tier, rests_on, statement, does_not_show, falsifier = row
        out.append(CommercialClaim(cid, statement, grade, rests_on, does_not_show, falsifier, tier))
    return tuple(out)


# The SHIPPED commercial ledger, loaded from the single-source manifest (ledger.tsv). Supported value-props
# rest on discharged obligations; boundary rows are explicitly downgraded and rest on OPEN_OR_REJECTED.
COMMERCIAL_CLAIMS: Tuple[CommercialClaim, ...] = _load_claims()


def audit_commercial_ledger(claims: Tuple[CommercialClaim, ...]) -> dict:
    """Honest iff: on-ladder + boundary fields present (claim_ledger); no SUPPORTED claim rests on an
    undischarged/rejected obligation; no SUPPORTED claim contains hype; every `rests_on` is a known key."""
    base = audit_ledger([c.to_claim() for c in claims])
    exceeds = [c.id for c in claims if c.grade in SUPPORTED and c.rests_on not in DISCHARGED]
    hype = [c.id for c in claims if c.grade in SUPPORTED and any(w in c.statement.lower() for w in HYPE)]
    unknown_ref = [c.id for c in claims if c.rests_on not in DISCHARGED and c.rests_on not in OPEN_OR_REJECTED]
    missing = [c.id for c in claims if not c.does_not_show or not c.falsifier]
    honest = base["honest"] and not exceeds and not hype and not unknown_ref and not missing
    return {"honest": honest, "exceeds_proof": exceeds, "hype": hype,
            "unknown_obligation": unknown_ref, "missing_boundary": missing, "base": base}


def main():
    print("commercial_obligations.py — proof-gated buyer claims (consider those proofs)\n")
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS)
    for c in COMMERCIAL_CLAIMS:
        kind = "value" if c.grade in SUPPORTED else "boundary"
        print(f"  [{c.grade:15s}] {c.id} ({c.tier}, {kind}) ← {c.rests_on}")
    print(f"\n  ledger honest: {a['honest']}  exceeds_proof={a['exceeds_proof']}  hype={a['hype']}  "
          f"unknown={a['unknown_obligation']}")
    print(f"  loaded {len(COMMERCIAL_CLAIMS)} claims + {len(DISCHARGED)} discharged / {len(OPEN_OR_REJECTED)} "
          f"open obligations from the single-source manifest. marketing cannot exceed evidence; claim ≠ proof.")


if __name__ == "__main__":
    main()
