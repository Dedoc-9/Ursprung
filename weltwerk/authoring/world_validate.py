# SPDX-License-Identifier: AGPL-3.0-only
"""
world_validate.py — Phase 6: the pre-play validation gate (BLOCK / WARN / INFO).

Before a developer plays a world, the studio validates its causal structure. Every verdict comes from
MEASURED structure (the verified graph/lint), never a guess:

  BLOCK — a feedback loop (SCC) with NO declared feedback relation. An undeclared cycle is almost always
          an authoring mistake; the designer must either declare intent (use a feedback-typed relation)
          or break it. This is the only thing that prevents play.
  WARN  — high blast radius / Actual approaching Potential (coupled world; causal compression unavailable).
  INFO  — declared feedback loops; causal compression available (sparse world).

`undeclared-cycle ≠ bug-proven` (it's a strong structural smell, hence BLOCK-with-override-by-declaration,
not a hard error); `WARN ≠ failure`. The gate reports; the designer decides.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world_design import regime                # noqa: E402
from world_lint import sccs                    # noqa: E402

# Relation types that DECLARE a cycle is intentional feedback (control loops, economies, ecologies).
DECLARED_FEEDBACK = {"feedback", "regulates", "balances", "stabilizes", "damps"}


def validate(cg) -> dict:
    out = []
    can_play = True
    loops = [c for c in sccs(cg) if len(c) > 1]
    for c in loops:
        members = set(c)
        declared = any(cg.labels.get((s, d)) in DECLARED_FEEDBACK
                       for s in c for d in cg.edges.get(s, ()) if d in members)
        if declared:
            out.append({"level": "INFO", "kind": "declared_feedback", "subject": sorted(c),
                        "detail": "declared feedback loop — intentional, allowed"})
        else:
            out.append({"level": "BLOCK", "kind": "undeclared_feedback", "subject": sorted(c),
                        "detail": "feedback loop with NO declared feedback relation — declare one "
                                  "(e.g. 'regulates'/'balances') or break the cycle before play"})
            can_play = False

    reg = regime(cg)
    if reg["peak_blast_pct"] >= 0.5:
        out.append({"level": "WARN", "kind": "high_blast", "subject": None,
                    "detail": f"high coupling (peak blast {int(reg['peak_blast_pct']*100)}%) — "
                              f"Actual approaches Potential; causal compression unavailable"})
    else:
        out.append({"level": "INFO", "kind": "compression_available", "subject": None,
                    "detail": f"sparse (peak blast {int(reg['peak_blast_pct']*100)}%) — causal compression available"})
    return {"validations": out, "can_play": can_play}


def render(cg) -> str:
    v = validate(cg)
    order = {"BLOCK": 0, "WARN": 1, "INFO": 2}
    lines = [f"WORLD VALIDATION  —  {'CAN PLAY' if v['can_play'] else 'BLOCKED (fix before play)'}"]
    for item in sorted(v["validations"], key=lambda x: order[x["level"]]):
        subj = (" " + ",".join(item["subject"])) if item["subject"] else ""
        tag = {"BLOCK": "⛔", "WARN": "⚠ ", "INFO": "· "}[item["level"]]
        lines.append(f"  {tag}[{item['level']}] {item['kind']}{subj}: {item['detail']}")
    return "\n".join(lines)


def main():
    from world_format import build_causal_graph, parse_world
    print("world_validate.py — Phase 6 pre-play gate\n")
    undeclared = """
world "Loop"
entity a:
  depends_on b
entity b:
  depends_on c
entity c:
  depends_on a
"""
    declared = undeclared + "entity reg:\n  regulates a\nentity a2:\n"  # add a declared feedback edge into the loop
    declared2 = """
world "Declared"
entity a:
  depends_on b
entity b:
  regulates a
"""
    print(render(build_causal_graph(parse_world(undeclared))))
    print()
    print(render(build_causal_graph(parse_world(declared2))))


if __name__ == "__main__":
    main()
