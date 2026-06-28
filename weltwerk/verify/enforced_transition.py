# SPDX-License-Identifier: AGPL-3.0-only
"""
enforced_transition.py — wiring the epistemic gate IN FRONT of real state mutation (discharges the
"`require_grounded` is a standalone decorator, not yet wired into a transition system" caveat).

`EnforcedTransitionSystem` holds mutable state and a step function, but its `apply` method is guarded by
`require_grounded("action")`: the only way to mutate the state is to hand it a `Grounded[Action]` carrying a
verifier-issued proof. A raw primitive, or a value whose proof is not grounded, is rejected by the gate
**before the body runs** — so the mutation never happens and the state + `transition_count` are unchanged. This
is atomicity-by-construction: the check strictly precedes the effect, so there is nothing to roll back.
`improved_map ≠ changed_criterion`; only the committed trajectory records what occurred.

The proof is produced by the existing verifier, unchanged — e.g. `EngineClosed(certificate)` where the
certificate is a frozen-engine `ReachabilityCertificate` (status CLOSED) or a `certificate_compiler`
`ConstraintCertificate` that passed its inductive check. The enforced system adds no authority; it only refuses
to mutate without a proof. `grounded ≠ true`.

Demo (`main`): a running system is asked to hot-swap (Alpha→Beta). A swap PLAN is verified by the frozen swap
checker; a CLOSED plan yields a grounded proof and the system migrates; a VIOLATED plan's proof is not grounded
so the swap is rejected and the running state stays pristine — an unsafe hot-swap physically cannot fire.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from epistemic_types import Grounded, Grounding, UngroundedError, require_grounded   # noqa: E402


@dataclass
class EnforcedTransitionSystem:
    """A stateful system whose ONLY mutation path (`apply`) is gated by `require_grounded`. Raw/ungrounded
    actions are refused before any effect; `transition_count` and `state` are unchanged on refusal (atomic).
    `commit_log` is the committed trajectory — the sole record of what actually occurred."""
    state: Any
    step_fn: Callable[[Any, Any], Any]          # (state, action_value) -> new_state
    transition_count: int = 0
    rejected_count: int = 0
    commit_log: List = field(default_factory=list)

    @require_grounded("action")
    def apply(self, action: "Grounded") -> Any:
        """Mutate the state under a grounded action. Reached ONLY for Grounded[...] with a valid proof — the
        decorator raises UngroundedError before this body for anything else, so mutation is all-or-nothing."""
        self.state = self.step_fn(self.state, action.value)
        self.transition_count += 1
        self.commit_log.append((action.value, action.proof.label()))
        return self.state

    def propose(self, action_value: Any, proof: "Grounding") -> Tuple[bool, str]:
        """Synthesis → enforcement pipe: try to ground the action, then apply. An ungrounded proposal is
        rejected here and never mutates the state. Returns (applied, why)."""
        try:
            g = Grounded.ground(action_value, proof)
        except UngroundedError as e:
            self.rejected_count += 1
            return False, f"rejected (ungrounded): {e}"
        self.apply(action=g)
        return True, "applied (grounded)"


def main():
    print("enforced_transition.py — the epistemic gate wired in front of real state mutation\n")
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hotswap"))
    from swap_relation import SwapModelChecker                  # noqa: E402  (the frozen swap checker)
    from epistemic_types import EngineClosed

    chk = SwapModelChecker()
    system = EnforcedTransitionSystem(state="running:alpha", step_fn=lambda _s, _plan: "migrated:beta")

    for label, plan, bound in [("greedy {ALIGN} (unsafe)", {"ALIGN"}, 4),
                               ("safe {MBB,ALIGN}", {"MBB", "ALIGN"}, 8)]:
        verdict = chk.run(plan, bound)                          # frozen verifier issues the proof material
        proof = EngineClosed(verdict.certificate)               # grounded iff status == CLOSED
        applied, why = system.propose(plan, proof)
        print(f"  swap {label:24s} verdict={verdict.status:8s} → {why}")
        print(f"      state now: {system.state}   transitions={system.transition_count}")

    print(f"\n  committed trajectory: {system.commit_log}")
    print(f"  rejected (no proof):  {system.rejected_count}")
    print("\n  an unsafe hot-swap could not mutate the running system — the gate refused it before any effect.")
    print("  only the committed trajectory records what occurred. grounded ≠ true; the gate grants no authority.")


if __name__ == "__main__":
    main()
