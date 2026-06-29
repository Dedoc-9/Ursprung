# SPDX-License-Identifier: AGPL-3.0-only
# Commercial use beyond AGPL-3.0 requires a separate license — see LICENSE-COMMERCIAL.md.
"""
commercial_obligations.py — the buyer-facing claims ledger, PROOF-GATED. A sales claim is honest only if a
discharged technical obligation backs it.

`consider those proofs`: every `CommercialClaim` names the obligation it `rests_on`. The STATIC audit is honest
iff (a) every claim is on the grade ladder with a `does_not_show` and a `falsifier`; (b) no SUPPORTED claim
rests on an UNDISCHARGED/REJECTED obligation; (c) no SUPPORTED claim contains hype; (d) every `rests_on` names
a known obligation. `claim ≠ proof`; `grade ≠ truth`.

SINGLE SOURCE OF TRUTH: claims + obligation registries load from the manifests `ledger.tsv` / `obligations.tsv`
(the same files the Rust `shipped_ledger()` reads). Edit the manifest, not the code. `mirror ≠ source` → one source.

LIVE EXECUTION BINDING (Obligation B, opt-in): pass `live_receipts=` to `audit_commercial_ledger` to ADD a
gate — a SUPPORTED claim's backing test suite (the `suite` column in obligations.tsv) must read `PASS` in a
fresh build receipt; otherwise it is `unverified_live` and the ledger is not honest. This lifts the gate from
"a test is NAMED" to "a test RAN AND PASSED in this build". HONEST CEILING, recorded not papered over:
`receipt ≠ proof` — it does NOT show the test is correct or complete (`tested ≠ safe`); the receipt is a
trusted build-environment artifact (freshness-bounded but forgeable), so the regress terminates at the build
root, not at truth. Default (`live_receipts=None`) keeps the pure STATIC audit — no behavior change.

Grades reuse the ladder (`claim_ledger.GRADES`): ESTABLISHED, MEASURED, UNDERDETERMINED, SPECULATIVE,
NOT_MEASURED. SUPPORTED = {ESTABLISHED, MEASURED}.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "weltwerk", "verify"))
from claim_ledger import Claim, audit_ledger, GRADES, SUPPORTED                 # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
# verify.py drops the build receipt one level up (next to DVSM/verify.py).
RECEIPT_FILE = os.path.join(_HERE, "..", ".verify_receipt.tsv")
MAX_RECEIPT_AGE_SECONDS = 600  # freshness backstop for a STANDALONE audit; the integrated verify.py run is fresh by construction


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


def _load_obligations() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Returns (discharged: key→evidence, open_or_rejected: key→evidence, suite_of: key→backing-suite-stem)."""
    discharged: Dict[str, str] = {}
    open_rej: Dict[str, str] = {}
    suite_of: Dict[str, str] = {}
    for row in _read_tsv("obligations.tsv"):
        key, status = row[0], row[1]
        suite = row[2] if len(row) > 2 else "-"
        evidence = row[3] if len(row) > 3 else ""
        if status == "DISCHARGED":
            discharged[key] = evidence
        elif status == "OPEN_OR_REJECTED":
            open_rej[key] = evidence
        else:
            raise ValueError("unknown obligation status %r for key %r" % (status, key))
        if suite and suite != "-":
            suite_of[key] = suite
    return discharged, open_rej, suite_of


# Loaded from the single-source manifest (obligations.tsv).
DISCHARGED, OPEN_OR_REJECTED, OBLIGATION_SUITE = _load_obligations()

# Hype lexicon — banned from any SUPPORTED claim.
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


# Loaded from the single-source manifest (ledger.tsv).
COMMERCIAL_CLAIMS: Tuple[CommercialClaim, ...] = _load_claims()


def load_live_receipts(path: str = RECEIPT_FILE, max_age_seconds: int = MAX_RECEIPT_AGE_SECONDS) -> Dict[str, str]:
    """Load a build receipt (`suite → status`) IF it exists and is fresh. A missing or stale receipt returns
    {} — treated as 'nothing verified live', so the gate fails closed. `receipt ≠ proof`."""
    if not os.path.exists(path):
        return {}
    if (time.time() - os.path.getmtime(path)) > max_age_seconds:
        return {}  # stale ⇒ treat as no live evidence
    out: Dict[str, str] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) >= 2:
                out[fields[0]] = fields[1]
    return out


def audit_commercial_ledger(claims: Tuple[CommercialClaim, ...],
                            live_receipts: Optional[Dict[str, str]] = None) -> dict:
    """STATIC audit (always): on-ladder + boundary fields present (claim_ledger); no SUPPORTED claim exceeds its
    proof or uses hype; every `rests_on` is known. LIVE audit (opt-in, when `live_receipts` is given): each
    SUPPORTED claim's backing suite must read PASS in the receipt, else it is `unverified_live`.
    `receipt ≠ proof`; default `live_receipts=None` ⇒ pure static audit (no behavior change)."""
    base = audit_ledger([c.to_claim() for c in claims])
    exceeds = [c.id for c in claims if c.grade in SUPPORTED and c.rests_on not in DISCHARGED]
    hype = [c.id for c in claims if c.grade in SUPPORTED and any(w in c.statement.lower() for w in HYPE)]
    unknown_ref = [c.id for c in claims if c.rests_on not in DISCHARGED and c.rests_on not in OPEN_OR_REJECTED]
    missing = [c.id for c in claims if not c.does_not_show or not c.falsifier]

    unverified_live: List[str] = []
    if live_receipts is not None:
        for c in claims:
            if c.grade in SUPPORTED:
                suite = OBLIGATION_SUITE.get(c.rests_on)
                if not suite or live_receipts.get(suite) != "PASS":
                    unverified_live.append(c.id)

    honest = (base["honest"] and not exceeds and not hype and not unknown_ref and not missing
              and not unverified_live)
    return {"honest": honest, "exceeds_proof": exceeds, "hype": hype,
            "unknown_obligation": unknown_ref, "missing_boundary": missing,
            "unverified_live": unverified_live, "base": base}


def main():
    print("commercial_obligations.py — proof-gated buyer claims (consider those proofs)\n")
    a = audit_commercial_ledger(COMMERCIAL_CLAIMS)
    for c in COMMERCIAL_CLAIMS:
        kind = "value" if c.grade in SUPPORTED else "boundary"
        print(f"  [{c.grade:15s}] {c.id} ({c.tier}, {kind}) ← {c.rests_on}")
    print(f"\n  STATIC ledger honest: {a['honest']}  exceeds={a['exceeds_proof']}  hype={a['hype']}  "
          f"unknown={a['unknown_obligation']}")
    live = load_live_receipts()
    if live:
        la = audit_commercial_ledger(COMMERCIAL_CLAIMS, live_receipts=live)
        print(f"  LIVE (fresh receipt found): honest={la['honest']}  unverified_live={la['unverified_live']}")
    else:
        print("  LIVE: no fresh build receipt — run via DVSM/verify.py to bind the gate to live execution.")
    print(f"  loaded {len(COMMERCIAL_CLAIMS)} claims + {len(DISCHARGED)} discharged / {len(OPEN_OR_REJECTED)} "
          f"open obligations from the manifest. receipt ≠ proof; tested ≠ safe; claim ≠ proof.")


if __name__ == "__main__":
    main()
