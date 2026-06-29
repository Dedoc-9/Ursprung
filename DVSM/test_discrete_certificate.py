# SPDX-License-Identifier: AGPL-3.0-only
"""
test_discrete_certificate.py — the discrete contraction certificate is SOUND (its analytic ρ upper-bounds the
measured worst-case growth), the condition BITES (large σ / large dt ⇒ not certified), and the κ fix is the
precondition (the corrected κ certifies where the broken κ does not). Validity-not-outcome.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "weltwerk", "verify"))

from dvsm_reference import kappa_matrix, R
from kappa_remediation import kappa_skew
from discrete_certificate import certify, sigma_max, as_obligation, frob

LAM, DT = 0.5, 0.1


def chk(name, ok, detail):
    return (name, ok, detail)


def test_fix_widens_margin():
    sm_sin = sigma_max(kappa_matrix(R), LAM)
    sm_skew = sigma_max(kappa_skew(R), LAM)
    return chk("fix_widens_margin", sm_skew > sm_sin, f"σ_max skew={sm_skew:.4f} > sin={sm_sin:.4f}")


def test_skew_certifies_where_sin_does_not():
    sm_sin = sigma_max(kappa_matrix(R), LAM)
    sm_skew = sigma_max(kappa_skew(R), LAM)
    sigma = (sm_sin + sm_skew) / 2.0
    rs = certify(kappa_skew(R), LAM, DT, sigma)
    rn = certify(kappa_matrix(R), LAM, DT, sigma)
    ok = rs["decision"] == "CONTRACTIVE_CERT" and rn["decision"] == "NOT_CERTIFIED"
    return chk("skew_certifies_sin_not", ok, f"skew={rs['decision']} sin={rn['decision']} σ={sigma:.4f}")


def test_bound_is_sound():
    # when certified, the analytic ρ must upper-bound the sampled worst-case growth
    sigma = sigma_max(kappa_skew(R), LAM) * 0.5
    r = certify(kappa_skew(R), LAM, DT, sigma, samples=4000)
    ok = r["decision"] == "CONTRACTIVE_CERT" and r["max_ratio"] <= r["rho"] + 1e-6
    return chk("bound_is_sound", ok, f"measured={r['max_ratio']:.4f} <= ρ={r['rho']:.4f}")


def test_large_sigma_not_certified():
    r = certify(kappa_skew(R), LAM, DT, sigma=10.0)
    return chk("large_sigma_not_certified", r["decision"] == "NOT_CERTIFIED", f"decision={r['decision']}")


def test_dt_too_large_not_certified():
    r = certify(kappa_skew(R), LAM, dt=3.0, sigma=0.01)  # dt*λ = 1.5 > 1
    return chk("dt_too_large_not_certified", r["decision"] == "NOT_CERTIFIED", f"decision={r['decision']}")


def test_obligation_honest():
    sigma = sigma_max(kappa_skew(R), LAM) * 0.5
    o = as_obligation(certify(kappa_skew(R), LAM, DT, sigma))
    ok = o.status == "CLOSED" and bool(o.does_not_show) and bool(o.falsifier)
    return chk("obligation_honest", ok, f"status={o.status}")


def main():
    results = [
        test_fix_widens_margin(),
        test_skew_certifies_where_sin_does_not(),
        test_bound_is_sound(),
        test_large_sigma_not_certified(),
        test_dt_too_large_not_certified(),
        test_obligation_honest(),
    ]
    print("test_discrete_certificate — sound narrow contraction certificate; κ fix is the precondition\n")
    passed = sum(int(ok) for _n, ok, _d in results)
    for name, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:28s} {detail}")
    total = len(results)
    print(f"\n  {passed}/{total} checks. SUFFICIENT condition, not a global proof; certificate ≠ proof-of-everything.")
    assert passed == total, f"{total - passed} check(s) failed"


if __name__ == "__main__":
    main()
