# SPDX-License-Identifier: AGPL-3.0-only
"""
snow_lattice.py — applying the Ursprung verify toolkit to snow-crystal MORPHOLOGY.

Question studied: what actually produces a snowflake's six-fold symmetry, and what does NOT? We model the
established physics and make the answer an EXECUTABLE, falsifiable invariant rather than a slogan.

ESTABLISHED PHYSICS (grounded, see snowflake/README.md sources):
  • A snow crystal's hexagonal habit comes from ice Ih's lattice, itself from water's tetrahedral hydrogen
    bonding (a molecular/quantum boundary condition — see quantum_ledger.py C1).
  • The six arms grow *independently* — they do NOT communicate. Their similarity comes from a SHARED growth
    environment: all six sit in the same tiny air pocket, so a shift in temperature/supersaturation reaches
    every arm at once and each responds by the SAME deterministic growth law (Libbrecht's "crowd reaching for
    umbrellas"). Perfect symmetry is the exception; most real snowflakes are irregular.

THE CLAIM, MADE FALSIFIABLE: six-fold symmetry = (shared field trajectory) ∘ (deterministic growth law).
It is NOT caused by inter-arm communication. We encode an arm as a 1-D growth profile driven only by its OWN
schedule (no sibling access — a structural no-communication channel), and check the `six_fold` invariant:

  • SHARED field  ⇒ six identical schedules ⇒ identical arms ⇒ six_fold holds (CLOSED).
  • PER-ARM field ⇒ schedules differ ⇒ arms diverge ⇒ six_fold VIOLATED, with a witness — even though the
    arms are physically identical and never communicate. So `correlation ≠ communication`; symmetry is a
    shared-cause signature, not a signal between arms.

MODEL BOUNDARY (Arbitrary-Boundary Law): an arm is abstracted to a sequence of growth *modes* under a shared
field; real growth is 2-D diffusion-limited. The claim proven here is about the LOGIC of the symmetry
(shared-cause vs communication), not a quantitative growth simulation. `holds-here ≠ true`.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from artifacts import Invariant                       # noqa: E402  (the verify primitive, reused)

# ---- Nakaya-style morphology map (deterministic: same (temp, supersaturation) ⇒ same growth mode) ----
# Temperature regimes (°C) after the classic Nakaya diagram; supersaturation: higher ⇒ more branched.
def morphology(temp_c: int, supersat: int) -> str:
    if temp_c > -4:        base = "plate"
    elif temp_c > -10:     base = "needle" if supersat >= 2 else "column"
    elif temp_c > -22:     base = "plate"
    else:                  base = "column"
    if base == "plate" and supersat >= 3:
        return "dendrite"
    if base == "plate" and supersat == 2:
        return "sector"
    return base


def grow(schedule: Tuple[int, ...], temp_c: int) -> Tuple[str, ...]:
    """An arm's growth profile = the morphology mode at each time step. Depends ONLY on this arm's own
    schedule and the (shared) temperature — there is NO parameter through which a sibling arm could be read.
    This is the structural no-communication channel."""
    return tuple(morphology(temp_c, s) for s in schedule)


# ---- the frozen invariant ------------------------------------------------------------------------
def _six_fold(arms) -> bool:
    return len(set(arms)) == 1


SIX_FOLD = Invariant("six_fold", _six_fold,
                     "all six arms have an identical growth profile (radial 6-fold symmetry)", "structural")


# ---- field models (the environment the arms share, or do not) ------------------------------------
def shared_field(schedule: Tuple[int, ...], temp_c: int) -> dict:
    """One tiny air pocket: all six arms get the SAME schedule (the physical reality for a tumbling flake)."""
    return {"temp": temp_c, "schedules": tuple(schedule for _ in range(6))}


def perarm_field(schedules6, temp_c: int) -> dict:
    """Counterfactual: each arm gets its OWN schedule (an environment that is not shared)."""
    assert len(schedules6) == 6
    return {"temp": temp_c, "schedules": tuple(tuple(s) for s in schedules6)}


@dataclass(frozen=True)
class SnowVerdict:
    status: str                          # CLOSED (symmetric) | VIOLATED (broken)
    arms: Tuple
    witness: Optional[Tuple]             # (arm_index, step, mode_here, mode_arm0) of the first divergence


def check_sixfold(field: dict) -> SnowVerdict:
    """Grow all six arms from the field, then check the six_fold invariant. CLOSED iff symmetric; otherwise
    VIOLATED with a replayable witness (which arm diverged from arm 0, at which step)."""
    temp = field["temp"]
    arms = tuple(grow(s, temp) for s in field["schedules"])
    if SIX_FOLD.predicate(arms):
        return SnowVerdict("CLOSED", arms, None)
    a0 = arms[0]
    for i in range(1, 6):
        if arms[i] != a0:
            step = next((t for t in range(min(len(a0), len(arms[i]))) if arms[i][t] != a0[t]), 0)
            return SnowVerdict("VIOLATED", arms, (i, step, arms[i][step] if step < len(arms[i]) else None,
                                                  a0[step] if step < len(a0) else None))
    return SnowVerdict("VIOLATED", arms, (1, 0, None, None))


# ---- independent oracle (different code path: pairwise comparison, not set-cardinality) -----------
def oracle_symmetric(field: dict) -> bool:
    temp = field["temp"]
    arms = [grow(s, temp) for s in field["schedules"]]
    return all(arms[i] == arms[0] for i in range(1, 6))


def main():
    print("snow_lattice.py — six-fold symmetry as shared-cause, not communication (verify toolkit)\n")
    sched = (0, 1, 3, 2, 3, 1)                          # a varying environmental history
    shared = check_sixfold(shared_field(sched, temp_c=-15))
    print(f"  SHARED field   → {shared.status}  arm0={shared.arms[0]}")
    per = check_sixfold(perarm_field([(0, 1, 3, 2, 3, 1), (0, 1, 3, 2, 3, 1), (0, 1, 3, 2, 3, 1),
                                      (0, 1, 3, 2, 3, 1), (0, 1, 3, 2, 0, 1),  # arm 4 saw a different humidity dip
                                      (0, 1, 3, 2, 3, 1)], temp_c=-15))
    print(f"  PER-ARM field  → {per.status}  witness(arm,step,here,arm0)={per.witness}")
    print("\n  the arms never read each other (grow() takes only its own schedule). Symmetry appears with a")
    print("  shared field and vanishes with a per-arm field — so it is a shared-cause signature, not a signal.")
    print("  correlation ≠ communication; shared-cause ≠ inter-arm coordination.")


if __name__ == "__main__":
    main()
