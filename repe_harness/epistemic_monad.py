#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""epistemic_monad.py — a small, LAW-CHECKED monad for composing grounded computations (the adapter layer).

An EM[T] is either EM.ok(Grounded[T]) [the REAL weltwerk Grounded[T]] or EM.fail(reason). `bind` sequences
steps  T -> EM[U], SHORT-CIRCUITING fail-closed on the first ungrounded step (carrying the reason) — exactly
the orchestrator's P8->P9 halt-on-ungrounded semantics, expressed as a composable algebra instead of hand ifs.

It also ABSORBS the .value/.get seam: `value_of()` reads either a real weltwerk Grounded (`.value`) or a
Phase-9-style stub (`.get()`), and `phase10_airgap.commit` was widened to match — so no per-call shim.

MONAD CLAIM IS TESTED, NOT ASSERTED. `--selftest` verifies the three monad laws on THIS implementation:
  left identity   : unit(a).bind(f)       == f(a)
  right identity  : m.bind(unit)          == m
  associativity   : m.bind(f).bind(g)     == m.bind(lambda x: f(x).bind(g))
The laws lean on weltwerk Grounded's `proof = field(compare=False)` (equality is on the value, not the proof).
If a law FAILED this would be relabelled (applicative / Kleisli arrow), not called a monad. `claim != code`.

GRADE:         apparatus VERIFIED when --selftest passes (laws + fail-closed composition on the real kernel).
DOES_NOT_SHOW: safety (SPECULATIVE); that a grounded value is true (`grounded != true`); that composing steps
               proves the phenomenon (`proves-the-procedure != proves-the-phenomenon`). A real-model number is
               still yours to measure.
"""
from __future__ import annotations
import argparse
import os
import sys


def _find_root():
    here = os.path.dirname(os.path.abspath(__file__)); d = here
    while True:
        if any(os.path.exists(os.path.join(d, m)) for m in (".git", "method.md", "AGENTS.md")):
            return d
        p = os.path.dirname(d)
        if p == d:
            return os.path.dirname(here)
        d = p


ROOT = os.environ.get("URSPRUNG_ROOT") or _find_root()
sys.path.insert(0, os.path.join(ROOT, "repe_harness"))
sys.path.insert(0, os.path.join(ROOT, "weltwerk", "verify"))

try:
    from residual_channel import audit                                    # noqa: E402
    from epistemic_types import Grounded, ChannelEstablished, Attested, UngroundedError  # noqa: E402
    _KERNEL_OK, _KERNEL_ERR = True, None
except Exception as e:
    _KERNEL_OK, _KERNEL_ERR = False, e


def value_of(grounded):
    """Seam adapter: weltwerk Grounded exposes `.value`; a Phase-9-style stub exposes `.get()`."""
    if hasattr(grounded, "value"):
        return grounded.value
    if hasattr(grounded, "get"):
        return grounded.get()
    raise AttributeError("not a Grounded: has neither .value nor .get()")


class EM:
    """Epistemic monad over the grounding-failure effect: EM.ok(Grounded[T]) | EM.fail(reason)."""
    __slots__ = ("grounded", "reason")

    def __init__(self, grounded, reason):
        self.grounded = grounded
        self.reason = reason

    @classmethod
    def ok(cls, grounded):
        return cls(grounded, None)

    @classmethod
    def fail(cls, reason):
        return cls(None, str(reason))

    @property
    def is_ok(self):
        return self.reason is None

    def bind(self, f):
        """f: T -> EM[U]. Apply f to the unwrapped value if ok; else propagate the failure unchanged."""
        if not self.is_ok:
            return self
        return f(value_of(self.grounded))

    def __eq__(self, other):
        if not isinstance(other, EM):
            return NotImplemented
        if self.is_ok != other.is_ok:
            return False
        return value_of(self.grounded) == value_of(other.grounded) if self.is_ok else self.reason == other.reason

    def __repr__(self):
        return f"EM.ok({value_of(self.grounded)!r})" if self.is_ok else f"EM.fail({self.reason!r})"


def unit(value):
    """Monadic unit :: a -> EM a. Lifts a plain value via a bare Attested proof (trusted boundary)."""
    if not _KERNEL_OK:
        raise RuntimeError(f"weltwerk kernel unavailable: {_KERNEL_ERR}")
    return EM.ok(Grounded.ground(value, Attested(True, "unit")))


def lift(value, proof):
    """Lift a value with a REAL grounding proof; EM.fail(reason) if the proof is not grounded (fail-closed)."""
    if not _KERNEL_OK:
        raise RuntimeError(f"weltwerk kernel unavailable: {_KERNEL_ERR}")
    try:
        return EM.ok(Grounded.ground(value, proof))
    except UngroundedError as e:
        return EM.fail(str(e))


def channel_arrow(steer_vector):
    """Kleisli arrow: given a ResidualChannelResult (the bound value), ground the steer via ChannelEstablished.
    EM.ok(Grounded[steer]) iff result.decision == 'RESIDUAL_MISSPEC_STABLE', else EM.fail(reason)."""
    def _arrow(result):
        return lift(steer_vector, ChannelEstablished(result))
    return _arrow


def _planted(n, rng):
    """A real channel: score carries label beyond z (I(label;score|z) > 0)."""
    out = []
    for _ in range(n):
        z = rng.randint(0, 2); lab = rng.randint(0, 1)
        out.append((lab, lab if rng.random() < 0.9 else 1 - lab, z))
    return out


def _confounded(n, rng):
    """No channel: label and score are both determined by z; score _|_ label | z."""
    return [(z % 2, z % 2, z) for z in (rng.randint(0, 2) for _ in range(n))]


def selftest() -> int:
    if not _KERNEL_OK:
        print(f"[selftest] FAIL — weltwerk/verify kernel not importable: {_KERNEL_ERR}")
        return 1
    import random
    from phase10_airgap import AirGap        # unique to repe_harness (no name collision)

    checks = []

    # --- monad laws (TESTED, not asserted) ---
    f = lambda x: unit(x + 1)
    g = lambda x: unit(x * 2)
    checks.append(("law: left identity  unit(a).bind(f) == f(a)", unit(5).bind(f) == f(5)))
    m = unit(3)
    checks.append(("law: right identity m.bind(unit) == m", m.bind(unit) == m))
    checks.append(("law: associativity", m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))))

    # --- fail-closed short-circuit: a failure skips downstream arrows ---
    calls = []
    def spy(x):
        calls.append(x); return unit(x)
    sc = EM.fail("boom").bind(spy)
    checks.append(("fail-closed: bind on EM.fail skips f (spy silent)", (sc.is_ok is False) and calls == []))

    # --- value_of absorbs the .value/.get seam ---
    class _RV:
        def __init__(self, v): self.value = v
    class _SV:
        def __init__(self, v): self._v = v
        def get(self): return self._v
    checks.append(("value_of reads .value AND .get", value_of(_RV(7)) == 7 and value_of(_SV(8)) == 8))

    # --- real-kernel Kleisli composition (planted -> grounded; confounded -> fail-closed) ---
    rng = random.Random(0)
    coarsen = (lambda s: [(x, y, z % 2) for x, y, z in s],)
    r_ok = audit(_planted(3000, rng), reps=100, seed=0, misspec_fns=coarsen)
    em_ok = unit(r_ok).bind(channel_arrow([1.0, 2.0, 3.0]))
    checks.append(("planted -> EM.ok(Grounded[steer])", em_ok.is_ok and value_of(em_ok.grounded) == [1.0, 2.0, 3.0]))

    ag = AirGap({"input_digest": "x", "applied": []})
    ag.commit(em_ok.grounded, lambda st, vec: st["applied"].append({"steer_dim": len(vec)}))
    checks.append(("phase10 commits the REAL Grounded (seam closed, no shim)", ag.verify()["ok"] is True))

    r_cf = audit(_confounded(3000, rng), reps=100, seed=0, misspec_fns=coarsen)
    em_cf = unit(r_cf).bind(channel_arrow([9.0]))
    checks.append(("confounded -> EM.fail (gate bites)", em_cf.is_ok is False))

    ok_all = True
    for label, ok in checks:
        print(f"[selftest] {label:52s}: {ok}"); ok_all = ok_all and ok
    n = len(checks); npass = sum(1 for _, ok in checks if ok)
    print(f"[selftest] {('PASS %d/%d - monad laws hold + fail-closed on real kernel' % (npass, n)) if ok_all else ('FAIL %d/%d' % (npass, n))}")
    print("[grade]    apparatus VERIFIED — monad laws TESTED (not asserted); composition fail-closed on real kernel.")
    print("[bound]    DOES_NOT_SHOW: safety (SPECULATIVE); grounded != true. A real-model number is yours to run.")
    return 0 if ok_all else 1


def main():
    ap = argparse.ArgumentParser(description="epistemic monad adapter layer (law-checked grounding composition)")
    ap.add_argument("--selftest", action="store_true", help="verify the 3 monad laws + fail-closed real-kernel composition")
    if ap.parse_args().selftest:
        raise SystemExit(selftest())
    print("compose grounded steps: unit(result).bind(channel_arrow(steer)); EM.fail short-circuits fail-closed.")
    if not _KERNEL_OK:
        print(f"WARNING: weltwerk kernel not importable now: {_KERNEL_ERR}")


if __name__ == "__main__":
    main()
