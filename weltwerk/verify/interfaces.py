# SPDX-License-Identifier: AGPL-3.0-only
"""
interfaces.py — Phase A.2, Step 1: the stable verification contract.

`ReachabilityResult` and `VerificationResult` are the ONLY objects later phases (diagnosis, abstract
interpretation, counterfactuals, repair) should consume. They are deliberately **minimal and backend-
agnostic**: they carry only what *every* engine — explicit-state BFS today, a symbolic engine later — can
reasonably provide. It is easier to extend a stable interface with optional capabilities than to remove or
redefine fields once consumers depend on them. `interface ≠ engine`; `stable-contract ≠ implementation`.

This step changes NO behavior. `kernel_check.py` (the reference engine) is left untouched: `verify()` uses
a deferred import and `from_check_result()` is duck-typed, so the 8/8 explicit-state checker cannot regress.

Design notes:
  • `certificate` is a PLACEHOLDER here (Step 4 fills it). A certificate is intended to be *independently
    checkable* by another component — for the explicit engine, the canonical closed reachable-state set;
    for a symbolic engine, a different artifact. Until Step 4 it is None. `placeholder ≠ proof`.
  • `frontier_exhausted` (not a fabricated frontier count) is the honest bit the explicit engine actually
    has: True ⇒ no residual frontier ⇒ exhaustive over the representation ⇒ CLOSED-eligible.
  • `witness` is a replayable action trace to a violating state, or None. `unbounded` claims are NOT made
    here — status carries the CLOSED (exhaustive) vs BOUNDED (depth-limited) distinction. `bounded ≠ proof`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple


@dataclass(frozen=True)
class ReachabilityResult:
    """Backend-agnostic answer to a reachability query. Minimal by design (extend, don't redefine)."""
    engine: str                                   # which backend produced this (e.g. "explicit-state-bfs")
    status: str                                   # CLOSED | BOUNDED | VIOLATED
    explored_states: int                          # states the engine materialized (metadata; may be 0 for symbolic)
    frontier_exhausted: bool                      # True ⇒ no residual frontier (exhaustive over the representation)
    witness: Optional[Tuple] = None               # replayable action trace to a violating state, else None
    certificate: Optional[Any] = None             # PLACEHOLDER (Step 4): independently-checkable proof artifact


@dataclass(frozen=True)
class VerificationResult:
    """The object every later phase consumes: a ReachabilityResult plus the property/invariant outcome.

    Consumers read `.status`, `.witness`, `.certificate`, `.explored_states`, `.frontier_exhausted`,
    `.engine`, and `.violations` — and must NOT reach past this object into a specific search algorithm.
    """
    reachability: ReachabilityResult
    violations: Tuple = ()                         # tuple of (invariant_name, kind) — minimal descriptors
    trace: Optional[Any] = None                    # Trace of the ghost on VIOLATED, else None (Step 4, additive)

    # delegated convenience accessors (keep consumers off the nested object) -----------------------
    @property
    def status(self) -> str:
        return self.reachability.status

    @property
    def witness(self) -> Optional[Tuple]:
        return self.reachability.witness

    @property
    def certificate(self) -> Optional[Any]:
        return self.reachability.certificate

    @property
    def explored_states(self) -> int:
        return self.reachability.explored_states

    @property
    def frontier_exhausted(self) -> bool:
        return self.reachability.frontier_exhausted

    @property
    def engine(self) -> str:
        return self.reachability.engine


def from_check_result(r) -> VerificationResult:
    """Adapt the explicit-state engine's `CheckResult` (duck-typed) into the stable contract.

    Reads only the public attributes of a kernel_check.CheckResult; imports nothing from kernel_check, so
    there is no coupling and no risk to the reference engine. `adapter ≠ engine`.
    """
    ghost = getattr(r, "ghost", None)
    witness = tuple(ghost.path) if ghost is not None else None
    rr = ReachabilityResult(
        engine="explicit-state-bfs",
        status=r.status,
        explored_states=r.states_explored,
        frontier_exhausted=not r.truncated,
        witness=witness,
        certificate=getattr(r, "certificate", None),   # Step 4: filled with a ReachabilityCertificate on CLOSED
    )
    violations = tuple((v.invariant, v.kind) for v in r.violations)
    return VerificationResult(reachability=rr, violations=violations, trace=getattr(r, "trace", None))


def verify(world_text: str, **kwargs) -> VerificationResult:
    """Run the (current, explicit-state) reference engine and return the stable contract object.

    A deferred import keeps `kernel_check.py` entirely untouched and avoids any import cycle. When other
    engines exist they will expose the same `verify`-shaped entry point returning a VerificationResult, and
    consumers will not change. `engine-swap ⇒ no consumer change`.
    """
    from kernel_check import check                # deferred on purpose (see docstring)
    return from_check_result(check(world_text, **kwargs))


def main():
    from kernel_check import DEMO_WORLD
    print("interfaces.py — Phase A.2 Step 1: stable VerificationResult contract over the reference engine\n")
    vr = verify(DEMO_WORLD, max_depth=3)
    print(f"  engine={vr.engine!r}  status={vr.status}  explored_states={vr.explored_states}  "
          f"frontier_exhausted={vr.frontier_exhausted}")
    print(f"  witness={vr.witness}  certificate={vr.certificate}  violations={vr.violations}")
    print("\n  consumers depend on THIS object, not on BFS. A symbolic engine will return the same shape.")
    print("  certificate is a placeholder until Step 4; bounded vs exhaustive lives in `status`.")


if __name__ == "__main__":
    main()
