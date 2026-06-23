# SPDX-License-Identifier: AGPL-3.0-only
"""
claim_ledger.py — reconcile heterogeneous statements about the kernel WITHOUT category collapse, by treating
commitment as a property of CLAIMS, not of the kernel. The reflexive form of the whole stack's principle
(`reality_status`: provenance per cell; `EPISTEMIC_ACCOUNTING`: BUILT/CONTRACT/ABSENT) applied to the question
"what can this kernel honestly claim about editing itself?".

The reconciliation that preserves the distinction: model everything as a claim with TWO orthogonal fields —
    maturity  — does the thing EXIST?           IMPLEMENTED > SCOPED > UNDERCOMMITTED   (≈ BUILT / CONTRACT / ABSENT)
    evidence  — what does the claim REST on?     MEASURED_BY_INTERVENTION > MEASURED > DECLARED > N/A
— plus mechanism, implementation, falsifier. The load-bearing INVARIANT (the no-inflation rule this session kept
re-deriving): **evidence may not exceed what maturity licenses.** You cannot be MEASURED without being
IMPLEMENTED; a SCOPED claim tops out at DECLARED (a prediction); an UNDERCOMMITTED claim carries no mechanism, no
falsifier, no evidence. The ledger enforces this structurally — three statements at three maturities reconcile
into one object, and none can borrow a strength it has not earned. `declared ≠ verified`; commitment ≠ the thing.

Run (from this directory):  PYTHONHASHSEED=0 python3 claim_ledger.py
"""
from __future__ import annotations

from dataclasses import dataclass, replace

try:
    from reality_status import MEASURED, MEASURED_BY_INTERVENTION, DECLARED, NOT_APPLICABLE
except ImportError:                                   # standalone fallback — mirrors reality_status
    MEASURED, MEASURED_BY_INTERVENTION, DECLARED, NOT_APPLICABLE = "MEASURED", "MEASURED_BY_INTERVENTION", "DECLARED", "N/A"

IMPLEMENTED, SCOPED, UNDERCOMMITTED = "IMPLEMENTED", "SCOPED", "UNDERCOMMITTED"

EVIDENCE_RANK = {NOT_APPLICABLE: 0, DECLARED: 1, MEASURED: 2, MEASURED_BY_INTERVENTION: 3}
MATURITY_CEILING = {UNDERCOMMITTED: 0, SCOPED: 1, IMPLEMENTED: 3}   # max evidence rank a maturity licenses


@dataclass(frozen=True)
class Claim:
    id: str
    kind: str                       # capability / frontier / theory_import / ...
    maturity: str                   # IMPLEMENTED / SCOPED / UNDERCOMMITTED
    evidence: str                   # MEASURED... / DECLARED / N/A
    implementation: str | None = None
    mechanism: str | None = None    # what it DOES (a prediction, for SCOPED)
    falsifier: str | None = None    # what would prove it wrong


def valid(c: Claim) -> bool:
    """A claim is well-formed iff its evidence does not exceed its maturity, and its fields match its maturity."""
    if EVIDENCE_RANK[c.evidence] > MATURITY_CEILING[c.maturity]:
        return False                                              # the no-inflation guard
    if c.maturity == UNDERCOMMITTED:
        return c.mechanism is None and c.falsifier is None and c.implementation is None and c.evidence == NOT_APPLICABLE
    if c.maturity == SCOPED:
        return (c.mechanism is not None and c.falsifier is not None and c.implementation is None
                and c.evidence == DECLARED)                       # a scoped claim predicts; it does not measure
    if c.maturity == IMPLEMENTED:
        return (c.implementation is not None and c.falsifier is not None and EVIDENCE_RANK[c.evidence] >= 2)
    return False


def promote(c: Claim, **updates) -> Claim:
    """Raise a claim's maturity/evidence by SUPPLYING what the new level requires. Refuses to upgrade on thin
    air: a promotion whose result is not `valid` raises. (UNDERCOMMITTED→SCOPED needs mechanism+falsifier;
    SCOPED→IMPLEMENTED needs implementation + MEASURED evidence.)"""
    nc = replace(c, **updates)
    if not valid(nc):
        raise ValueError(f"promotion of {c.id} to {nc.maturity}/{nc.evidence} is unsupported — "
                         f"evidence exceeds maturity, or required mechanism/implementation/falsifier is missing")
    return nc


# --- the three statements about the kernel, reconciled into one ledger without collapsing their maturities ---
LEDGER = [
    Claim(id="data_editing", kind="capability", maturity=IMPLEMENTED, evidence=MEASURED,
          implementation="live_world_kernel.py (16/16)",
          mechanism="propose / commit / reject / causal-subtree rollback; three states (committed/irreversible/durable)",
          falsifier="a committed edit that loses causal truth — rollback corrupts unrelated state"),
    Claim(id="self_modification", kind="frontier", maturity=SCOPED, evidence=DECLARED,
          implementation=None,
          mechanism="SELF_MODIFICATION_BOUNDARY: edit the rule that decides edits; klein/frontier — prediction NON_ORIENTABLE (no global outside; bootstrap/genesis residual)",
          falsifier="a single self-validating layer that returns ORIENTABLE/recoverable across all three cases (refutes the layering necessity)"),
    Claim(id="M_theory_mapping", kind="theory_import", maturity=UNDERCOMMITTED, evidence=NOT_APPLICABLE,
          implementation=None, mechanism=None, falsifier=None),
]


def report(ledger: list) -> dict:
    """The reconciled object: claims kept at their own maturities; the ONLY rollup is a maturity histogram —
    never a single 'kernel status' scalar (a kernel is not one commitment level; its claims are)."""
    from collections import Counter
    return {
        "claims": ledger,
        "by_maturity": dict(Counter(c.maturity for c in ledger)),
        "note": "maturity & evidence are properties of CLAIMS, not of the kernel; no single kernel status exists",
    }


def main() -> None:
    print("claim_ledger — reconcile statements about the kernel as CLAIMS with commitment levels (no collapse).\n")
    for c in LEDGER:
        print(f"  {c.id:<18} maturity={c.maturity:<14} evidence={c.evidence:<24} impl={c.implementation}")
    rep = report(LEDGER)
    print(f"\n  by maturity: {rep['by_maturity']}   (no single 'kernel status' — there isn't one)\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<36} {detail}")

    # 1. three maturities coexist in one object — commitment is per-claim, not per-kernel
    check("maturities_coexist",
          {c.maturity for c in LEDGER} == {IMPLEMENTED, SCOPED, UNDERCOMMITTED},
          "data_editing IMPLEMENTED, self_modification SCOPED, M_theory UNDERCOMMITTED — together, undiluted")

    # 2. all three are well-formed at their stated maturity
    check("all_claims_valid", all(valid(c) for c in LEDGER),
          "each claim's evidence and fields match its maturity")

    # 3. THE guard: evidence may not exceed maturity (no borrowing strength you haven't earned)
    faked_measured_undercommitted = Claim("x", "theory_import", UNDERCOMMITTED, MEASURED, mechanism="hand-wave")
    faked_measured_scoped = Claim("y", "frontier", SCOPED, MEASURED, mechanism="m", falsifier="f")
    check("evidence_cannot_exceed_maturity",
          not valid(faked_measured_undercommitted) and not valid(faked_measured_scoped),
          "UNDERCOMMITTED/MEASURED and SCOPED/MEASURED are rejected — can't measure what isn't implemented")

    # 4. an UNDERCOMMITTED claim carries nothing; attaching a mechanism without promoting is invalid
    m = next(c for c in LEDGER if c.id == "M_theory_mapping")
    check("undercommitted_carries_nothing",
          m.mechanism is None and m.falsifier is None and m.evidence == NOT_APPLICABLE
          and not valid(replace(m, mechanism="branes-as-state")),
          "M_theory has no mechanism/falsifier/evidence; adding a mechanism alone is invalid — it must be promoted")

    # 5. promotion requires SUPPLYING the evidence — no free upgrade
    try:
        promote(m, maturity=SCOPED)                               # missing mechanism + falsifier
        free_upgrade = True
    except ValueError:
        free_upgrade = False
    promoted_ok = promote(m, maturity=SCOPED, evidence=DECLARED,
                          mechanism="a committed M-theory operation X", falsifier="X is reproduced without it")
    check("promotion_requires_evidence",
          not free_upgrade and promoted_ok.maturity == SCOPED and valid(promoted_ok),
          "UNDERCOMMITTED→SCOPED is refused on thin air; it succeeds only when mechanism + falsifier are supplied")

    # 6. NO scalar collapse: the report has no single kernel status, only per-claim + a maturity histogram
    check("no_kernel_scalar",
          not any(k in rep for k in ("kernel_status", "status", "committed")) and "by_maturity" in rep,
          "the object refuses a single 'the kernel is COMMITTED' — maturity is a property of claims, not the kernel")

    print(f"\n  {passed}/{total} checks. Three statements about the kernel — an IMPLEMENTED capability, a SCOPED")
    print("  frontier, an UNDERCOMMITTED import — reconcile into one object WITHOUT pretending they share a")
    print("  maturity, because commitment is modelled as a property of the CLAIM, not the kernel. The invariant")
    print("  is enforced structurally: evidence never exceeds maturity, and promotion demands the mechanism/")
    print("  falsifier/implementation it claims — no free upgrade. The same discipline as every cell of")
    print("  reality_status and every row of EPISTEMIC_ACCOUNTING, turned on the kernel's own self-description.")
    assert passed == total, "claim_ledger failed its own self-test"


if __name__ == "__main__":
    main()
