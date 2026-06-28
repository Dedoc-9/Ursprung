# SPDX-License-Identifier: AGPL-3.0-only
"""
epistemic_types.py — the judge → COMPILER step: types that carry epistemic status, so an ungrounded value
cannot be constructed and an ungrounded action cannot trigger a state transition.

Standard type checking guards data safety ("this function wants an int"). Here a type guards EPISTEMIC safety:
a `Grounded[T]` value can exist ONLY if it is accompanied by a proof object that the frozen verification layer
issued. A generator/synthesizer therefore cannot simply emit an action sequence — to reach an applier whose
signature demands `Grounded[Action]`, it must pass a verification certificate alongside it. If it cannot ground
the value, construction raises `UngroundedError` *before* any state transition — the "compile error" the leap asks for.

This is the same discipline the repo already enforces, lifted into the type:
  • `AnalysisResult` refuses to construct without scope + ≥1 limitation;
  • a swap succeeds only on the frozen `CLOSED ∧ migrated` verdict;
  • `repair.restores_world` is enum-typed evidence, never a bare bool.
`Grounded[T]` makes that refusal structural and composable. `improved_map ≠ changed_criterion`;
`grounded ≠ true` (grounding is relative to the proof's scope and bound); `proves-the-procedure ≠ proves-the-phenomenon`.

A `Grounding` is any proof object exposing `is_grounded() -> bool` + `label() -> str`. Adapters wrap the
existing artifacts as proofs — the verifier issues the certificate; the type system only refuses to proceed
without one. The type system creates NO authority; it only forbids ungrounded synthesis.
"""
from __future__ import annotations

import functools
import inspect
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Protocol, Tuple, TypeVar, runtime_checkable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artifacts import AnalysisResult, Finding, Limitation        # noqa: E402  (honesty contract, reused)
from claim_ledger import SUPPORTED                               # noqa: E402

T = TypeVar("T")


class UngroundedError(Exception):
    """Raised when a value would be used (or constructed) without a valid grounding proof — BEFORE any
    state transition. This is the epistemic 'compile error'."""


@runtime_checkable
class Grounding(Protocol):
    def is_grounded(self) -> bool: ...
    def label(self) -> str: ...


# ---- adapters: wrap a verifier-issued artifact as a Grounding proof ------------------------------
@dataclass(frozen=True)
class EngineClosed:
    """Grounded iff the frozen engine returned CLOSED for the action's resulting world (no reachable
    violation over the alphabet + bound). The canonical proof for a synthesized action."""
    certificate: Any                       # a ReachabilityCertificate (or any object with .status)
    def is_grounded(self) -> bool:
        return self.certificate is not None and getattr(self.certificate, "status", None) == "CLOSED"
    def label(self) -> str:
        return f"engine={getattr(self.certificate, 'status', None)} (CLOSED over alphabet+bound)"


@dataclass(frozen=True)
class SupportedClaim:
    """Grounded iff a claim is graded ESTABLISHED/MEASURED on the epistemic ladder (claim_ledger)."""
    claim: Any                             # a claim_ledger.Claim (object with .grade)
    def is_grounded(self) -> bool:
        return getattr(self.claim, "grade", None) in SUPPORTED
    def label(self) -> str:
        return f"claim-grade={getattr(self.claim, 'grade', None)}"


@dataclass(frozen=True)
class ChannelEstablished:
    """Grounded iff a residual_channel audit found a mis-specification-stable channel (RESIDUAL_MISSPEC_STABLE)."""
    result: Any                            # a residual_channel.ResidualChannelResult (object with .decision)
    def is_grounded(self) -> bool:
        return getattr(self.result, "decision", None) == "RESIDUAL_MISSPEC_STABLE"
    def label(self) -> str:
        return f"channel-decision={getattr(self.result, 'decision', None)}"


@dataclass(frozen=True)
class NoHiddenChannel:
    """Grounded iff a residual_channel audit is CONSISTENT_WITH_NULL (no residual dependence beyond Z)."""
    result: Any
    def is_grounded(self) -> bool:
        return getattr(self.result, "decision", None) == "CONSISTENT_WITH_NULL"
    def label(self) -> str:
        return f"channel-decision={getattr(self.result, 'decision', None)}"


@dataclass(frozen=True)
class Attested:
    """A bare attestation (for tests / trusted boundaries). `ok` must be supplied explicitly — no default-True."""
    ok: bool
    why: str = "attested"
    def is_grounded(self) -> bool:
        return bool(self.ok)
    def label(self) -> str:
        return self.why


# ---- the epistemic type: a value that cannot exist without a valid proof -------------------------
@dataclass(frozen=True)
class Grounded(Generic[T]):
    """A value tagged with the proof that grounds it. Construction (any path) raises UngroundedError unless the
    proof.is_grounded(). The raw value is reachable only AFTER grounding succeeded — so holding a Grounded[T]
    IS the witness that T was verified. `grounded ≠ true`: it is grounded relative to the proof's scope."""
    value: T
    proof: Grounding = field(compare=False)

    def __post_init__(self):
        if not isinstance(self.proof, Grounding) or not self.proof.is_grounded():
            raise UngroundedError(f"refusing to construct Grounded[...] for {self.value!r}: "
                                  f"proof not grounded ({_safe_label(self.proof)})")

    @classmethod
    def ground(cls, value: T, proof: Grounding) -> "Grounded[T]":
        return cls(value, proof)

    def as_analysis(self) -> AnalysisResult:
        findings = (
            Finding("GROUNDED_VALUE", "grounded-value", f"{self.value!r}"),
            Finding("PROOF", "grounded-value", self.proof.label()),
        )
        limitations = (
            Limitation("grounded-value", "grounded relative to the proof's scope and bound; grounded ≠ true"),
            Limitation("epistemic", f"the proof attests '{self.proof.label()}', not global correctness"),
        )
        return AnalysisResult(source_trace=(), scope="grounded-value",
                              findings=findings, limitations=limitations)


def _safe_label(p) -> str:
    try:
        return p.label()
    except Exception:
        return f"{type(p).__name__} (not a Grounding)"


# ---- the gate: a transition cannot run on a raw/ungrounded value ---------------------------------
def require_grounded(*param_names: str) -> Callable:
    """Decorator: the named parameters MUST be `Grounded` instances with a still-valid proof, or the call
    raises UngroundedError *before* the function body runs. This is the epistemic compile-gate that sits in
    front of any state-transition / side-effecting applier."""
    def deco(fn: Callable) -> Callable:
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name in param_names:
                if name not in bound.arguments:
                    raise UngroundedError(f"{fn.__name__}: required grounded parameter '{name}' missing")
                v = bound.arguments[name]
                if not isinstance(v, Grounded):
                    raise UngroundedError(f"{fn.__name__}: parameter '{name}' must be Grounded[...] "
                                          f"with a verifier-issued proof; refusing before any state transition")
                if not v.proof.is_grounded():               # defense-in-depth (proof can't normally go stale here)
                    raise UngroundedError(f"{fn.__name__}: parameter '{name}' carries an ungrounded proof")
            return fn(*args, **kwargs)
        wrapper.__wrapped_requires__ = param_names
        return wrapper
    return deco


# ---- the compiler loop: synthesis gated by grounding --------------------------------------------
def synthesize_gate(candidates, to_proof: Callable[[Any], Grounding]):
    """The generative loop as a compiler: each candidate is (value, evidence); evidence is turned into a proof
    and the value is grounded. Ungrounded candidates are REJECTED here and never become Grounded — so they can
    never reach an applier that requires Grounded[...]. Returns (accepted: list[Grounded], rejected: list)."""
    accepted, rejected = [], []
    for value, evidence in candidates:
        proof = to_proof(evidence)
        try:
            accepted.append(Grounded.ground(value, proof))
        except UngroundedError:
            rejected.append((value, _safe_label(proof)))
    return accepted, rejected


def main():
    print("epistemic_types.py — Grounded[T]: ungrounded synthesis cannot compile\n")

    @require_grounded("action")
    def apply_action(action: "Grounded", log: list):
        log.append(action.value)            # the 'state transition' — only reached for grounded actions
        return action.value

    class _Cert:                            # stand-in for a ReachabilityCertificate
        def __init__(self, status): self.status = status

    # a generator proposes (action, engine-verdict); only CLOSED-verified actions ground
    candidates = [("destroy_then_repair", _Cert("CLOSED")),
                  ("destroy_only", _Cert("VIOLATED")),
                  ("noop", _Cert("CLOSED"))]
    accepted, rejected = synthesize_gate(candidates, EngineClosed)
    print(f"  synthesized {len(candidates)} candidates → accepted {len(accepted)}, rejected {len(rejected)}")
    for v, why in rejected:
        print(f"    REJECTED at compile: {v!r}  ({why})")

    log = []
    for g in accepted:
        apply_action(action=g, log=log)
    print(f"  applied (state transitions): {log}")
    try:
        apply_action(action="raw_ungrounded_action", log=log)   # bypass attempt
    except UngroundedError as e:
        print(f"  bypass blocked before transition: {type(e).__name__}")
    print("\n  an ungrounded value cannot be constructed or applied; the proof must accompany the action.")
    print("  grounded ≠ true; the type forbids ungrounded synthesis, it creates no authority.")


if __name__ == "__main__":
    main()
