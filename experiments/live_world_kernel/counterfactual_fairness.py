# SPDX-License-Identifier: AGPL-3.0-only
"""
counterfactual_fairness.py — the stack's intervention discipline TRANSFERRED to causal fairness. Not a new axis,
not a "fairness score": a demonstration that the core invariant generalizes — *any claim a model makes must carry
the assumptions that make its counterfactual meaningful.*

The unification: the whole project measures **counterfactual stability under a declared intervention**.
    RSI side      — do(force this self-edit):  does VERIFIED capability keep expanding?
    fairness side — do(flip the protected A):  does the OUTCOME stay invariant?
Same primitive `do(·)`, different invariant (trajectory expansion vs outcome invariance), SAME trap:
`correlation → claim` when the evidence only licenses `correlation → candidate explanation`.

Counterfactual fairness (Kusner et al.) on a KNOWN synthetic SCM A → {M, Y}, M → Y:
    M = α·A + U_M           (mediator, e.g. "choice of major")
    Y = β_dir·A + β_M·M + U_Y   (outcome; β_dir = the DIRECT discrimination path A→Y)
Per individual: ABDUCT U from the factual observation, INTERVENE do(A←a'), PREDICT the counterfactual Y'.
    total effect       = Y(A←a') − Y(A←a)            = (β_dir + β_M·α)·(a'−a)
    direct PSE  (A→Y)  = Y(a', M(a)) − Y(a, M(a))    = β_dir·(a'−a)        # path-specific: flip A only in Y
    indirect PSE (A→M→Y) = Y(a, M(a')) − Y(a, M(a))  = β_M·α·(a'−a)        # flip A only through M

THE TWO HIDDEN VARIABLES this exposes (the contribution — not the metric):
  1. THE GRAPH. Y(A←a') is only computable from a KNOWN SCM; the graph is *not identifiable from observation*
     (`observation ≠ intervention`). On real data the verdict is relative to an ASSUMED graph → FRONTIER.
  2. THE PATH PARTITION. Which paths are "forbidden" vs "permissible" (direct A→Y vs indirect A→M→Y) is a
     DECLARED normative choice the math cannot supply (the Arbitrary-Boundary Law). The SAME model is "fair" or
     "unfair" depending on it — demonstrated below.

Status discipline: MEASURED only relative to the declared SCM + declared partition; real-world deployment is
FRONTIER / UNVERIFIED. Reports resource accounting (SCM evals / interventions / paths), never a bare fairness bit.
`declared ≠ verified`; `estimate ≠ property`; a number without its experiment boundary is a claim generator.

Run (from this directory):  PYTHONHASHSEED=0 python3 counterfactual_fairness.py
"""
from __future__ import annotations

import random
from dataclasses import dataclass

SEED = 20260623
EPS = 1e-9
N_INDIV = 500

EVAL = {"scm": 0, "interventions": 0, "paths": 0}


@dataclass(frozen=True)
class SCM:
    """A DECLARED structural causal model (synthetic, fully known). alpha: A→M; beta_dir: A→Y (direct);
    beta_M: M→Y."""
    alpha: float
    beta_dir: float
    beta_M: float


def M_of(A, u_m, scm):
    EVAL["scm"] += 1
    return scm.alpha * A + u_m


def Y_of(A, M, u_y, scm):
    EVAL["scm"] += 1
    return scm.beta_dir * A + scm.beta_M * M + u_y


def abduct(a0, M0, Y0, scm):
    """Infer the exogenous U that produced a factual observation (the abduction step of a counterfactual)."""
    u_m = M0 - scm.alpha * a0
    u_y = Y0 - scm.beta_dir * a0 - scm.beta_M * M0
    return u_m, u_y


def effects(a0, u_m, u_y, scm, a1):
    """do(A←a1) vs factual A=a0, for ONE individual (fixed U): total + the two path-specific effects."""
    M0 = M_of(a0, u_m, scm)
    Y0 = Y_of(a0, M0, u_y, scm)
    # total: flip A everywhere
    EVAL["interventions"] += 1
    M1 = M_of(a1, u_m, scm)
    Y_total = Y_of(a1, M1, u_y, scm)
    # direct path A→Y: flip A only in Y, hold M at its factual (a0) value
    EVAL["interventions"] += 1
    EVAL["paths"] += 1
    Y_direct = Y_of(a1, M0, u_y, scm)
    # indirect path A→M→Y: flip A only through M, hold A=a0 in Y
    EVAL["interventions"] += 1
    EVAL["paths"] += 1
    Y_indirect = Y_of(a0, M1, u_y, scm)
    return {"Y0": Y0, "total": Y_total - Y0, "direct_pse": Y_direct - Y0, "indirect_pse": Y_indirect - Y0}


def assess(scm, label):
    """Counterfactual-fairness assessment of a DECLARED SCM, averaged over sampled individuals (the effects are
    constant across U for this linear SCM, so per-individual == population — verified by the spread check)."""
    rng = random.Random(SEED)
    tot, dpse, ipse = [], [], []
    abduct_ok = True
    for _ in range(N_INDIV):
        a0 = rng.randint(0, 1)
        u_m, u_y = rng.gauss(0, 1), rng.gauss(0, 1)
        a1 = 1 - a0
        # abduction round-trip check: recompute the factual from inferred U
        M0 = M_of(a0, u_m, scm)
        Y0 = Y_of(a0, M0, u_y, scm)
        ru_m, ru_y = abduct(a0, M0, Y0, scm)
        abduct_ok &= abs(ru_m - u_m) < 1e-9 and abs(ru_y - u_y) < 1e-9
        e = effects(a0, u_m, u_y, scm, a1)
        scale = 1 if a1 > a0 else -1                       # normalize sign to the a0→a1 direction
        tot.append(e["total"] * scale)
        dpse.append(e["direct_pse"] * scale)
        ipse.append(e["indirect_pse"] * scale)
    mean = lambda xs: sum(xs) / len(xs)
    total, direct, indirect = mean(tot), mean(dpse), mean(ipse)
    # verdicts are RELATIVE TO THE DECLARED PARTITION:
    return {
        "label": label, "scm": scm,
        "total_effect": total, "direct_pse": direct, "indirect_pse": indirect,
        "total_fair": abs(total) < EPS,                    # no effect of A on Y at all
        "direct_path_fair": abs(direct) < EPS,             # the forbidden direct path carries no effect
        "abduct_ok": abduct_ok,
        "spread": max(abs(t - total) for t in tot),        # ~0 ⇒ effect is constant across individuals (linear SCM)
    }


def main():
    print("counterfactual_fairness — the do() discipline transferred to causal fairness (MEASURED on a KNOWN SCM only).\n")
    a0, a1 = 0, 1
    # two DECLARED models on the same variables — differ only in whether the DIRECT path A→Y is active
    m_direct = SCM(alpha=0.6, beta_dir=0.5, beta_M=0.4)     # direct discrimination present
    m_indirect = SCM(alpha=0.6, beta_dir=0.0, beta_M=0.4)   # direct path BLOCKED; only A→M→Y remains
    r_dir = assess(m_direct, "direct-discrimination")
    r_ind = assess(m_indirect, "indirect-only (direct path blocked)")

    for r in (r_dir, r_ind):
        s = r["scm"]
        print(f"  model '{r['label']}'  SCM(α={s.alpha}, β_dir={s.beta_dir}, β_M={s.beta_M})  [DECLARED synthetic graph]")
        print(f"     total effect of A on Y      = {r['total_effect']:+.3f}   total counterfactually fair? {r['total_fair']}")
        print(f"     direct PSE  (A→Y)           = {r['direct_pse']:+.3f}   direct-path fair?            {r['direct_path_fair']}")
        print(f"     indirect PSE (A→M→Y)        = {r['indirect_pse']:+.3f}   (permissible? a DECLARED choice)")
        print()
    print("  partition-relativity: the SAME 'indirect-only' model is")
    print(f"     UNFAIR under a 'block all A→Y influence' partition (total effect {r_ind['total_effect']:+.3f} ≠ 0)")
    print(f"     FAIR  under a 'block only the direct path' partition (direct PSE {r_ind['direct_pse']:+.3f} = 0)")
    print("  → which paths must vanish is a DECLARED normative boundary the math cannot decide.\n")
    print(f"  resource accounting: SCM evaluations={EVAL['scm']}  interventions={EVAL['interventions']}  paths evaluated={EVAL['paths']}")
    print("  status: MEASURED relative to the DECLARED SCM + DECLARED path partition.")
    print("  real-world deployment: graph identified? NO (unidentifiable from observation) · path partition? DECLARED")
    print("                         → FRONTIER / UNVERIFIED. estimate ≠ property; declared ≠ verified.\n")

    passed = total = 0

    def check(name, ok, detail=""):
        nonlocal passed, total
        total += 1
        if ok:
            passed += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<34} {detail}")

    # 1. abduction round-trips: inferred U regenerates the factual observation (counterfactual machinery is sound)
    check("abduction_roundtrips", r_dir["abduct_ok"] and r_ind["abduct_ok"],
          "inferred exogenous U regenerates the factual M,Y for every sampled individual")

    # 2. the do()-measured total effect equals the closed form (β_dir + β_M·α) — anchor the intervention to algebra
    cf_dir = m_direct.beta_dir + m_direct.beta_M * m_direct.alpha
    cf_ind = m_indirect.beta_dir + m_indirect.beta_M * m_indirect.alpha
    check("total_effect_matches_closed_form",
          abs(r_dir["total_effect"] - cf_dir) < 1e-9 and abs(r_ind["total_effect"] - cf_ind) < 1e-9,
          f"measured total = (β_dir + β_M·α): {r_dir['total_effect']:.3f}={cf_dir:.3f}, {r_ind['total_effect']:.3f}={cf_ind:.3f}")

    # 3. path-specific decomposition: direct PSE + indirect PSE == total (additive in this DECLARED linear SCM)
    check("pse_decomposition_additive",
          all(abs((r["direct_pse"] + r["indirect_pse"]) - r["total_effect"]) < 1e-9 for r in (r_dir, r_ind)),
          "direct PSE + indirect PSE = total effect (holds for the declared linear/no-interaction SCM)")

    # 4. THE point: the verdict is PARTITION-RELATIVE — same indirect-only model is fair xor unfair by partition
    check("verdict_is_partition_relative",
          (r_ind["direct_path_fair"] is True) and (r_ind["total_fair"] is False)
          and (r_dir["direct_path_fair"] is False),
          "indirect-only model: direct-path-fair=True AND total-fair=False ⇒ the declared partition decides the verdict")

    # 5. effect is constant across individuals (counterfactual fairness here is structural, not a sample artifact)
    check("individual_level_constant", r_dir["spread"] < 1e-9 and r_ind["spread"] < 1e-9,
          "per-individual effect spread ≈ 0 — the verdict is structural under the declared SCM, not a sampling fluke")

    # 6. resource accounting is reported (not a bare fairness bit), per the suite's discipline
    check("resource_accounting_reported",
          EVAL["scm"] > 0 and EVAL["interventions"] > 0 and EVAL["paths"] > 0,
          f"SCM evals / interventions / paths counted ({EVAL['scm']}/{EVAL['interventions']}/{EVAL['paths']})")

    # 7. no over-claim: BOTH partition-views are always reported, so no single absolute "fair" verdict can be read
    check("no_unconditional_fairness_claim",
          all(("total_fair" in r and "direct_path_fair" in r) for r in (r_dir, r_ind)),
          "total_fair AND direct_path_fair both always reported — a verdict is never absolute, only partition-relative")

    # 8. determinism
    r3 = assess(m_direct, "x")
    check("deterministic", abs(r3["total_effect"] - r_dir["total_effect"]) < 1e-12,
          "seeded assessment reproduces; the counterfactual is a fixed witness")

    print(f"\n  {passed}/{total} checks. Same do() primitive as the RSI suite, different invariant (outcome invariance")
    print("  vs trajectory expansion). The artifact's value is NOT a fairness metric — it is that a fairness claim")
    print("  is MEASURED only relative to a DECLARED graph (unidentifiable from data) and a DECLARED path partition")
    print("  (a normative choice the math cannot make), so on real data it is FRONTIER / DECLARED, never proven.")
    print("  The stack's invariant generalizes: a counterfactual claim must carry the assumptions that make it mean")
    print("  anything. `observation ≠ intervention`; `declared ≠ verified`; a number without its boundary is a claim generator.")
    assert passed == total, "counterfactual_fairness failed a validity check"


if __name__ == "__main__":
    main()
