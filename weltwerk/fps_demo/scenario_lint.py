# SPDX-License-Identifier: AGPL-3.0-only
"""
scenario_lint.py — the VERIFIED causal backbone for the FPS demo (Phase 5).

The playable demo (weltwerk_fps.html) mirrors the Potential/Actual primitives in JS so it can run in a
browser at interactive rates. THIS file is the authoritative reference: it runs the demo's fortress
scenario DSL through the already-verified authoring layer (world_spec + world_lint, both tested) so the
causal analysis the demo shows — reachability, SCC / feedback detection, load-bearing, bottlenecks — is
backed by code that is checked, not hand-asserted in JavaScript.

Run:  PYTHONHASHSEED=0 python3 scenario_lint.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "authoring"))

from world_lint import report                  # noqa: E402
from world_spec import parse_spec              # noqa: E402

# The fortress FPS scenario as causal topology (Phase 8). Directed edge = "editing/destroying src can
# affect dst". A feedback cluster is left in deliberately (supply economy + the gate/courtyard loop) so
# the linter demonstrates its value by flagging structure the level designer may not have intended.
FORTRESS_FPS = """
# defensive structure (acyclic — collapse propagates downhill)
keep        supports      wall_north
keep        supports      wall_east
wall_north  collapses_into courtyard
wall_east   collapses_into courtyard
tower       supports      wall_north
gate        blocks        courtyard

# supply / garrison economy (the systems layer — where feedback lives)
courtyard   feeds         market
market      supplies      garrison
garrison    defends       gate
garrison    consumes      supply_crate
supply_crate sustains     garrison

# destructibles and resource nodes a player can act on
barrel      explodes_into wall_east
barrel      explodes_into courtyard
resource_node feeds       market
guard_patrol defends      courtyard
"""


def main():
    g = parse_spec(FORTRESS_FPS)
    print("scenario_lint.py — verified causal analysis of the FPS fortress scenario (Phase 5 backbone)\n")
    print(report(g))
    print("\n  This analysis is produced by the tested authoring layer (world_spec + world_lint). The")
    print("  HTML demo mirrors these Potential-side primitives in JS for interactive play; this is the")
    print("  verified reference they mirror.  structural-cycle ≠ measured-amplification.")


if __name__ == "__main__":
    main()
